from zeep.helpers import serialize_object

from tap_workday.streams.abstracts import FullTableStream
from tap_workday.streams.common import get_workday_client, emit_full_table


class OverrideBalances(FullTableStream):
    tap_stream_id = "override_balances"
    replication_method = "FULL_TABLE"
    key_properties = ["Override_Balance_Reference.ID"]
    data_key = "Override_Balance"

    def get_client(self):
        cfg = self.client.config
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Absence_Management",
            version="v44.2",
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Override_Balances()
        serialized = serialize_object(response)
        records = serialized.get("Response_Data", {}).get(self.data_key, [])
        return emit_full_table(self, records)


class AbsenceInputs(FullTableStream):
    tap_stream_id = "absence_inputs"
    replication_method = "FULL_TABLE"
    key_properties = ["Absence_Input_Reference.ID"]
    data_key = "Absence_Input"

    def get_client(self):
        cfg = self.client.config
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Absence_Management",
            version="v44.2",
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Absence_Inputs()
        serialized = serialize_object(response)
        records = serialized.get("Response_Data", {}).get(self.data_key, [])
        return emit_full_table(self, records)
