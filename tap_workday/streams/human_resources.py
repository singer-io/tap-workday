from tap_workday.streams.abstracts import WorkdayTableStream


class Organizations(WorkdayTableStream):
    tap_stream_id = "human_resources_organizations"
    replication_method = "FULL_TABLE"
    key_properties = ["Organization_ID.value"]
    service_name = "Human_Resources"
    operation_name = "Get_Organizations"
    data_key = "Organization"


class JobCategories(WorkdayTableStream):
    tap_stream_id = "human_resources_job_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Job_Category_ID.value"]
    service_name = "Human_Resources"
    operation_name = "Get_Job_Categories"
    data_key = "Job_Category"


class JobFamilyGroups(WorkdayTableStream):
    tap_stream_id = "human_resources_job_family_groups"
    replication_method = "FULL_TABLE"
    key_properties = ["Job_Family_Group_Data.ID"]
    service_name = "Human_Resources"
    operation_name = "Get_Job_Family_Groups"
    data_key = "Job_Family_Group"


class JobProfiles(WorkdayTableStream):
    tap_stream_id = "human_resources_job_profiles"
    replication_method = "FULL_TABLE"
    key_properties = ["Job_Profile_Data.Job_Code"]
    service_name = "Human_Resources"
    operation_name = "Get_Job_Profiles"
    data_key = "Job_Profile"


class Locations(WorkdayTableStream):
    tap_stream_id = "human_resources_locations"
    replication_method = "FULL_TABLE"
    key_properties = ["Location_Data.Location_ID"]
    service_name = "Human_Resources"
    operation_name = "Get_Locations"
    data_key = "Location"
