from tap_workday.streams.abstracts import WorkdayTableStream


class StaffingStream(WorkdayTableStream):
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Staffing"


class Organizations(StaffingStream):
    tap_stream_id = "staffing_organizations"
    operation_name = "Get_Organizations"
    data_key = "Organization"
    wid_key = "Organization_Reference"
