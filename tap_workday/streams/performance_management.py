from zeep.helpers import serialize_object

from tap_workday.streams.abstracts import FullTableStream
from tap_workday.streams.common import get_workday_client, emit_full_table


class CertificationIssuers(FullTableStream):
    tap_stream_id = "certification_issuers"
    replication_method = "FULL_TABLE"
    key_properties = ["ID"]
    data_key = "Certification_Issuer"

    def get_client(self):
        cfg = self.client.config
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Performance_Management",
            version="v44.2",
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Certification_Issuers()
        serialized = serialize_object(response)
        records = serialized.get("Response_Data", {}).get(self.data_key, [])
        return emit_full_table(self, records)


class Competencies(FullTableStream):
    tap_stream_id = "competencies"
    replication_method = "FULL_TABLE"
    key_properties = ["Competency_ID"]
    data_key = "Competency"

    def get_client(self):
        cfg = self.client.config
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Performance_Management",
            version="v44.2",
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Competencies()
        serialized = serialize_object(response)
        records = serialized.get("Response_Data", {}).get(self.data_key, [])
        return emit_full_table(self, records)


class CompetencyCategories(FullTableStream):
    tap_stream_id = "competency_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Code"]
    data_key = "Competency_Category"

    def get_client(self):
        cfg = self.client.config
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Performance_Management",
            version="v44.2",
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Competency_Categories()
        serialized = serialize_object(response)
        records = serialized.get("Response_Data", {}).get(self.data_key, [])
        return emit_full_table(self, records)


class Degrees(FullTableStream):
    tap_stream_id = "degrees"
    replication_method = "FULL_TABLE"
    key_properties = ["ID"]
    data_key = "Degree"

    def get_client(self):
        cfg = self.client.config
        return get_workday_client(
            tenant=cfg["tenant"],
            username=cfg["username"],
            password=cfg["password"],
            service="Performance_Management",
            version="v44.2",
        )

    def sync(self, state, transformer, parent_obj=None):
        client = self.get_client()
        response = client.service.Get_Degrees()
        serialized = serialize_object(response)
        records = serialized.get("Response_Data", {}).get(self.data_key, [])
        return emit_full_table(self, records)
