from zeep.helpers import serialize_object

from tap_workday.streams.abstracts import FullTableStream
from tap_workday.streams.common import get_workday_client, emit_full_table, safe_get_records


class CostCenters(FullTableStream):
    tap_stream_id = "cost_centers"
    replication_method = "FULL_TABLE"
    key_properties = []
    data_key = "Cost_Center"

    def get_client(self):
        cfg = self.client.config
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Financial_Management",
            version="v44.2",
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Cost_Centers()
        serialized = serialize_object(response)
        records = safe_get_records(serialized, self.data_key)
        return emit_full_table(self, records)


class Organizations(FullTableStream):
    tap_stream_id = "fm_organizations"
    replication_method = "FULL_TABLE"
    key_properties = []
    data_key = "Organization"

    def get_client(self):
        cfg = self.client.config
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Financial_Management",
            version="v44.2",
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Organizations()
        serialized = serialize_object(response)
        records = safe_get_records(serialized, self.data_key)
        return emit_full_table(self, records)
