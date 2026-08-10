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
    replication_keys = ["updated_through"]
    # NOTE: Organization_Data.Last_Updated_DateTime is the EFFECTIVE date of
    # the most recent change and may be future-dated.  Workday's
    # Transaction_Log_Criteria.Updated_From operates on the internal
    # transaction log timestamp, which is not in the response and can precede
    # Last_Updated_DateTime significantly.  sync_start_time is the correct
    # bookmark; see human_resources.Organizations for full explanation.
    bookmark_field_path = None

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
