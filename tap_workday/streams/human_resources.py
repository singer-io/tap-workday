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
    BOOKMARK_KEY = "updated_through"

    def build_filter_params(self, updated_since, updated_through=None):
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
