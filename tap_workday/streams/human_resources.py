from tap_workday.streams.common import WorkdayFullTableStream


class Organizations(WorkdayFullTableStream):
    tap_stream_id = "get_organizations"
    replication_method = "FULL_TABLE"
    key_properties = ["Organization_ID.value"]
    service_name = "Human_Resources"
    operation_name = "Get_Organizations"
    data_key = "Organization"


class JobCategories(WorkdayFullTableStream):
    tap_stream_id = "job_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Job_Category_ID.value"]
    service_name = "Human_Resources"
    operation_name = "Get_Job_Categories"
    data_key = "Job_Category"


class JobFamilyGroups(WorkdayFullTableStream):
    tap_stream_id = "job_family_groups"
    replication_method = "FULL_TABLE"
    key_properties = ["Job_Family_Group_Data.ID"]
    service_name = "Human_Resources"
    operation_name = "Get_Job_Family_Groups"
    data_key = "Job_Family_Group"


class JobProfiles(WorkdayFullTableStream):
    tap_stream_id = "job_profiles"
    replication_method = "FULL_TABLE"
    key_properties = ["Job_Profile_Data.Job_Code"]
    service_name = "Human_Resources"
    operation_name = "Get_Job_Profiles"
    data_key = "Job_Profile"


class Locations(WorkdayFullTableStream):
    tap_stream_id = "locations"
    replication_method = "FULL_TABLE"
    key_properties = ["Location_Data.Location_ID"]
    service_name = "Human_Resources"
    operation_name = "Get_Locations"
    data_key = "Location"
