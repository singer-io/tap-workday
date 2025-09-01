from tap_workday.streams.abstracts import WorkdayFullTableStream


class Organizations(WorkdayFullTableStream):
    """Staffing.Get_Organizations stream."""

    tap_stream_id = "staffing_organizations"
    replication_method = "FULL_TABLE"
    key_properties = ["Organization_Reference.ID"]
    service_name = "Staffing"
    operation_name = "Get_Organizations"
    data_key = "Organization"
