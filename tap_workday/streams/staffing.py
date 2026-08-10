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
    replication_method = "INCREMENTAL"
    BOOKMARK_KEY = "updated_through"

    def build_filter_params(self, updated_since, updated_through=None):
        if not updated_since:
            return {}
        return {
            "Request_Criteria": {
                "Transaction_Log_Criteria": {
                    "Transaction_Date_Range_Data": {
                        "Updated_From": updated_since,
                        "Updated_Through": updated_through,
                    }
                }
            }
        }
