from tap_workday.streams.abstracts import WorkdayTableStream


class Organizations(WorkdayTableStream):
    tap_stream_id = "human_resources_organizations"
    replication_method = "FULL_TABLE"
    key_properties = ["Organization_Reference__ID__0___value_1"]
    service_name = "Human_Resources"
    operation_name = "Get_Organizations"
    data_key = "Organization"


class JobCategories(WorkdayTableStream):
    tap_stream_id = "human_resources_job_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Job_Category_Reference__ID__0___value_1"]
    service_name = "Human_Resources"
    operation_name = "Get_Job_Categories"
    data_key = "Job_Category"


class JobFamilyGroups(WorkdayTableStream):
    tap_stream_id = "human_resources_job_family_groups"
    replication_method = "FULL_TABLE"
    key_properties = ["Job_Family_Group_Reference__ID__0___value_1"]
    service_name = "Human_Resources"
    operation_name = "Get_Job_Family_Groups"
    data_key = "Job_Family_Group"


class JobProfiles(WorkdayTableStream):
    tap_stream_id = "human_resources_job_profiles"
    replication_method = "FULL_TABLE"
    key_properties = ["Job_Profile_Reference__ID__0___value_1"]
    service_name = "Human_Resources"
    operation_name = "Get_Job_Profiles"
    data_key = "Job_Profile"


class Locations(WorkdayTableStream):
    tap_stream_id = "human_resources_locations"
    replication_method = "FULL_TABLE"
    key_properties = ["Location_Reference__ID__0___value_1"]
    service_name = "Human_Resources"
    operation_name = "Get_Locations"
    data_key = "Location"
