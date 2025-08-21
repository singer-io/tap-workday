from tap_workday.streams.abstracts import FullTableStream


class GetOrganizations(FullTableStream):
    tap_stream_id = "get_organizations"
    key_properties = ["Organization_ID.value"]
    replication_method = "FULL_TABLE"
