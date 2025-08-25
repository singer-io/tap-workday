from datetime import datetime, date
from decimal import Decimal

from singer import (
    Transformer,
    metrics,
    UNIX_SECONDS_INTEGER_DATETIME_PARSING,
    write_record,
    write_schema,
)
from zeep import Client
from zeep.wsse.username import UsernameToken


# ---- Reference normalization helpers ----
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


# ---- Transformer pre-hook (generic across Workday responses) ----
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


# ---- Zeep client factory ----
def get_workday_client(
    tenant: str, username: str, password: str, service: str, version: str
):
    """Create a Zeep SOAP client for a given Workday service & version."""
    wsdl = f"https://wd2-impl-services1.workday.com/ccx/service/{tenant}/{service}/{version}?wsdl"
    return Client(wsdl=wsdl, wsse=UsernameToken(username, password))


# ---- Emit helper for FULL_TABLE streams ----
def emit_full_table(stream, records):
    """Write schema, transform with shared hook, and emit records."""
    # write_schema(stream.tap_stream_id, stream.schema, stream.key_properties)

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
