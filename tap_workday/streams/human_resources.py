from tap_workday.streams.abstracts import WorkdayTableStream


class HumanResourcesStream(WorkdayTableStream):
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Human_Resources"


class Organizations(HumanResourcesStream):
    tap_stream_id = "human_resources_organizations"
    operation_name = "Get_Organizations"
    data_key = "Organization"
    wid_key = "Organization_Reference"
    replication_method = "INCREMENTAL"
    replication_keys = ["updated_through"]
    # NOTE: Organization_Data.Last_Updated_DateTime is the EFFECTIVE date of
    # the most recent change — it can be future-dated (a HR user enters a
    # change today that takes effect next month).  Workday's
    # Transaction_Log_Criteria.Updated_From filter operates on the internal
    # TRANSACTION LOG timestamp (when the change was entered/approved), which
    # is NOT exposed in the response payload and may precede
    # Last_Updated_DateTime by weeks or months.
    # Using Last_Updated_DateTime as Updated_From therefore misses records
    # that were entered well before their effective date.
    # sync_start_time is the correct bookmark: every record whose transaction
    # log entry falls in [Updated_From, sync_start_time] is captured, and the
    # next run picks up from sync_start_time onward with no gaps.
    bookmark_field_path = None

    def build_filter_params(self, updated_since, updated_through=None):
        # updated_since = bookmark from state (or start_date on first run).
        # Run 2+ returns 0 records when nothing changed since the last sync —
        # that is correct; it does NOT mean data was missed.
        if not updated_since:
            return {}
        return {
            "Request_Criteria": {
                "Transaction_Log_Criteria": {
                    "Transaction_Date_Range_Data": {
                        "Updated_From": updated_since,    # bookmark / start_date
                        "Updated_Through": updated_through,  # sync_start_time
                    }
                }
            }
        }


class JobCategories(HumanResourcesStream):
    tap_stream_id = "human_resources_job_categories"
    operation_name = "Get_Job_Categories"
    data_key = "Job_Category"
    wid_key = "Job_Category_Reference"


class JobFamilyGroups(HumanResourcesStream):
    tap_stream_id = "human_resources_job_family_groups"
    operation_name = "Get_Job_Family_Groups"
    data_key = "Job_Family_Group"
    wid_key = "Job_Family_Group_Reference"


class JobProfiles(HumanResourcesStream):
    tap_stream_id = "human_resources_job_profiles"
    operation_name = "Get_Job_Profiles"
    data_key = "Job_Profile"
    wid_key = "Job_Profile_Reference"
    replication_method = "INCREMENTAL"
    replication_keys = ["updated_through"]
    # NOTE: Get_Job_Profiles responses contain no last-modified timestamp.
    # Job_Profile_Data.Effective_Date is the date the profile became effective
    # (e.g. 2015-01-01), not when it was last transacted/modified.  The API
    # is filtered via Transaction_Log_Criteria_Data which tracks internal
    # transaction log entries not exposed in the response payload.
    # bookmark_field_path = None -> bookmark falls back to sync_start_time
    # (no guaranteed record overlap across sync windows).
    bookmark_field_path = None

    def build_filter_params(self, updated_since, updated_through=None):
        # Same incremental filter logic — see Organizations.build_filter_params.
        if not updated_since:
            return {}
        return {
            "Request_Criteria": {
                "Transaction_Log_Criteria_Data": {
                    "Transaction_Date_Range_Data": {
                        "Updated_From": updated_since,
                        "Updated_Through": updated_through,
                    }
                }
            }
        }


class Locations(HumanResourcesStream):
    tap_stream_id = "human_resources_locations"
    operation_name = "Get_Locations"
    data_key = "Location"
    wid_key = "Location_Reference"
