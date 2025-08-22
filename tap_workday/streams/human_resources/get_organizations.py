from singer import write_record, write_schema, Transformer, metrics, UNIX_SECONDS_INTEGER_DATETIME_PARSING
from zeep import Client
from zeep.wsse.username import UsernameToken
from zeep.helpers import serialize_object
from decimal import Decimal
from datetime import datetime, date
import json

from tap_workday.streams.abstracts import FullTableStream


# -- Normalization for single reference object fields --
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


# -- Normalization for lists of reference objects (used in Leadership, etc.) --
def normalize_ref_array(value):
    if not isinstance(value, list):
        return []

    return [normalize_ref_object(item) for item in value if isinstance(item, dict)]


# -- Pre-transform hook that normalizes known fields --
def my_pre_hook(data, typ, schema):
    if isinstance(data, datetime) and schema.get("format") == "date-time":
        return data.isoformat()

    if isinstance(data, Decimal):
        return float(data)

    if isinstance(data, dict):
        # Fields that are singular reference objects
        singular_refs = [
            "External_URL_Reference",
            "Organization_Owner_Reference",
            "Organization_Type_Reference",
            "Organization_Subtype_Reference",
            "Organization_Visibility_Reference",
            "Manager_Reference",
            "Top-Level_Organization_Reference",
            "Superior_Organization_Reference",
        ]

        # Fields that are arrays of reference objects
        array_refs = [
            "Leadership_Reference",
            "Subordinate_Organization_Reference",
            "Included_Organization_Reference",
            "Included_In_Organization_Reference",
        ]

        for key in singular_refs:
            if key in data:
                data[key] = normalize_ref_object(data.get(key))

        for key in array_refs:
            if key in data:
                data[key] = normalize_ref_array(data.get(key))

    return data


# -- Main Tap Stream --
class GetOrganizations(FullTableStream):
    tap_stream_id = "get_organizations"
    replication_method = "FULL_TABLE"
    key_properties = ["Organization_ID.value"]
    data_key = "Organization_Data"  # top-level key in response if applicable

    def get_client(self):
        tenant = self.client.config["tenant"]
        username = self.client.config["username"]
        password = self.client.config["password"]
        wsdl = f"https://wd2-impl-services1.workday.com/ccx/service/{tenant}/Human_Resources/v42.0?wsdl"
        return Client(wsdl=wsdl, wsse=UsernameToken(username, password))

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Organizations()
        serialized = serialize_object(response)
        records = serialized.get("Response_Data", {}).get("Organization", [])

        write_schema(self.tap_stream_id, self.schema, self.key_properties)

        transformer = Transformer(
            integer_datetime_fmt=UNIX_SECONDS_INTEGER_DATETIME_PARSING,
            pre_hook=my_pre_hook
        )

        with metrics.record_counter(self.tap_stream_id) as counter:
            for record in records:
                try:
                    transformed = transformer.transform(record, self.schema, self.metadata)
                    write_record(self.tap_stream_id, transformed)
                    counter.increment()
                except Exception as e:
                    import pprint
                    print(f" Failed to transform record in stream '{self.tap_stream_id}'")
                    pprint.pprint(record)
                    raise e

            return counter.value
