from zeep.helpers import serialize_object

from tap_workday.streams.abstracts import FullTableStream
from tap_workday.streams.common import get_workday_client, emit_full_table


class Organizations(FullTableStream):
    tap_stream_id = "get_organizations"
    replication_method = "FULL_TABLE"
    key_properties = ["Organization_ID.value"]
    data_key = "Organization"

    def get_client(self):
        cfg = self.client.config
        # Keeping original version v42.0 to match the source file; change if needed
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Human_Resources",
            version="v42.0",
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Organizations()
        serialized = serialize_object(response)
        records = serialized.get("Response_Data", {}).get(self.data_key, [])
        return emit_full_table(self, records)


class JobCategories(FullTableStream):
    tap_stream_id = "job_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Job_Category_ID.value"]
    data_key = "Job_Category"

    def get_client(self):
        cfg = self.client.config
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Human_Resources",
            version="v44.2",
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Job_Categories()
        serialized = serialize_object(response)
        records = serialized.get("Response_Data", {}).get(self.data_key, [])
        return emit_full_table(self, records)
