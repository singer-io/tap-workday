from singer import write_record, write_schema, Transformer, metrics, UNIX_SECONDS_INTEGER_DATETIME_PARSING
from zeep import Client
from zeep.wsse.username import UsernameToken
from zeep.helpers import serialize_object
from decimal import Decimal
from datetime import datetime, date

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


# -- Normalization for lists of reference objects --
def normalize_ref_array(value):
    if not isinstance(value, list):
        return []
    return [normalize_ref_object(item) for item in value if isinstance(item, dict)]


# -- Pre-transform hook: normalize datetimes, decimals, and any "*_Reference" fields --
def my_pre_hook(data, typ, schema):
    # Normalize datetime -> isoformat when target is date-time
    if isinstance(data, datetime) and schema.get("format") == "date-time":
        return data.isoformat()

    # Normalize Decimal -> float
    if isinstance(data, Decimal):
        return float(data)

    # Generic normalization for Workday reference shapes
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if key.endswith("_Reference"):
                # If it's a dict, treat as a singular reference object
                if isinstance(value, dict):
                    data[key] = normalize_ref_object(value)
                # If it's a list, treat as an array of reference objects
                elif isinstance(value, list):
                    data[key] = normalize_ref_array(value)
                # Otherwise coerce to an empty normalized reference
                else:
                    data[key] = {"ID": [], "Descriptor": None}

    return data


class GetJobCategories(FullTableStream):
    tap_stream_id = "get_job_categories"
    replication_method = "FULL_TABLE"
    # Typical Workday ID path is "<Entity>_ID.value" (mirrors your organizations stream)
    key_properties = ["Job_Category_ID.value"]
    data_key = "Job_Category"  # Expected list key under Response_Data

    def get_client(self):
        tenant = self.client.config["tenant"]
        username = self.client.config["username"]
        password = self.client.config["password"]
        # Use the WSDL version you referenced (v44.2)
        wsdl = f"https://wd2-impl-services1.workday.com/ccx/service/{tenant}/Human_Resources/v44.2?wsdl"
        return Client(wsdl=wsdl, wsse=UsernameToken(username, password))

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()

        # Invoke the Workday API
        response = client.service.Get_Job_Categories()
        serialized = serialize_object(response)

        # Extract records (mirror of get_organizations approach)
        records = serialized.get("Response_Data", {}).get(self.data_key, [])

        # Emit schema first
        write_schema(self.tap_stream_id, self.schema, self.key_properties)

        # Prepare transformer with our pre-hook
        transformer = Transformer(
            integer_datetime_fmt=UNIX_SECONDS_INTEGER_DATETIME_PARSING,
            pre_hook=my_pre_hook
        )

        # Stream out records
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
