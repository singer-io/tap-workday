from datetime import datetime, date
from decimal import Decimal

from singer import (
    Transformer,
    metrics,
    UNIX_SECONDS_INTEGER_DATETIME_PARSING,
    write_record,
    write_schema,
)
from tap_workday.streams.abstracts import FullTableStream
from zeep import Client
from zeep.helpers import serialize_object
from zeep.wsse.username import UsernameToken


def normalize_ref_object(value):
    if value is None or not isinstance(value, dict):
        return {"ID": [], "Descriptor": None}

    id_field = value.get("ID")

    if isinstance(id_field, dict):
        value["ID"] = [id_field]
    elif isinstance(id_field, list):
        value["ID"] = [item for item in id_field if isinstance(item, dict)]
    else:
        value["ID"] = []

    descriptor = value.get("Descriptor")
    value["Descriptor"] = descriptor if isinstance(descriptor, str) else None

    return value


def normalize_ref_array(value):
    if not isinstance(value, list):
        return []
    return [normalize_ref_object(item) for item in value if isinstance(item, dict)]


def my_pre_hook(data, typ, schema):
    # Dates & datetimes -> ISO strings when the schema says so
    if isinstance(data, datetime) and schema.get("format") == "date-time":
        return data.isoformat()
    if isinstance(data, date) and schema.get("format") == "date":
        return data.isoformat()

    # Decimal -> float
    if isinstance(data, Decimal):
        return float(data)

    # Normalize any "*_Reference" shapes (singular or array)
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if key.endswith("_Reference"):
                if isinstance(value, dict):
                    data[key] = normalize_ref_object(value)
                elif isinstance(value, list):
                    data[key] = normalize_ref_array(value)
                else:
                    data[key] = {"ID": [], "Descriptor": None}

    return data


def safe_get_records(serialized: dict, data_key: str):
    """Return a list of records from a Workday SOAP response.

    Handles cases where `Response_Data` is None or missing, and when the
    leaf at `data_key` is a single object instead of a list.
    """
    if not isinstance(serialized, dict):
        return []
    resp = serialized.get("Response_Data")
    if not isinstance(resp, dict):
        return []
    records = resp.get(data_key)
    if records is None:
        return []
    if isinstance(records, list):
        return records
    if isinstance(records, dict):
        return [records]
    return []


def get_workday_client(
    tenant: str, hostname: str, username: str, password: str, service: str, version: str
):
    """Create a Zeep SOAP client for a given Workday service & version."""
    wsdl = f"https://{hostname}/ccx/service/{tenant}/{service}/{version}?wsdl"
    return Client(wsdl=wsdl, wsse=UsernameToken(username, password))


def emit_full_table(stream, records):
    """Write schema, transform with shared hook, and emit records."""
    write_schema(stream.tap_stream_id, stream.schema, stream.key_properties)

    transformer = Transformer(
        integer_datetime_fmt=UNIX_SECONDS_INTEGER_DATETIME_PARSING,
        pre_hook=my_pre_hook,
    )

    with metrics.record_counter(stream.tap_stream_id) as counter:
        for record in records:
            transformed = transformer.transform(record, stream.schema, stream.metadata)
            write_record(stream.tap_stream_id, transformed)
            counter.increment()

        return counter.value


class WorkdayFullTableStream(FullTableStream):
    """Base for simple Workday FULL_TABLE SOAP streams.

    Child classes should set:
    - service_name: Workday service string (e.g., "Human_Resources")
    - operation_name: SOAP operation to call (e.g., "Get_Organizations")
    - data_key: leaf key inside Response_Data (e.g., "Organization")
    - wsdl_version (optional): default "v44.2"
    """

    service_name: str = ""
    operation_name: str = ""
    data_key: str = ""
    wsdl_version: str = "v44.2"

    def get_client(self):
        cfg = self.client.config
        # Allow per-service override via config, e.g. human_resources_version
        override_key = f"{self.service_name.lower()}_version"
        version = cfg.get(override_key, cfg.get("wsdl_version", self.wsdl_version))
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            hostname=cfg["hostname"],
            service=self.service_name,
            version=version,
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        operation = getattr(client.service, self.operation_name)
        response = operation()
        serialized = serialize_object(response)
        records = safe_get_records(serialized, self.data_key)
        return emit_full_table(self, records)
