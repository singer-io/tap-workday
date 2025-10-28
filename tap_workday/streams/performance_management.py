from tap_workday.streams.abstracts import WorkdayTableStream


class CertificationIssuers(WorkdayTableStream):
    tap_stream_id = "performance_management_certification_issuers"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Performance_Management"
    operation_name = "Get_Certification_Issuers"
    data_key = "Certification_Issuer"
    wid_key = "Certification_Issuer_Reference"


class Competencies(WorkdayTableStream):
    tap_stream_id = "performance_management_competencies"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Performance_Management"
    operation_name = "Get_Competencies"
    data_key = "Competency"
    wid_key = "Competency_Reference"


class CompetencyCategories(WorkdayTableStream):
    tap_stream_id = "performance_management_competency_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Performance_Management"
    operation_name = "Get_Competency_Categories"
    data_key = "Competency_Category"
    wid_key = "Competency_Category_Reference"


class Degrees(WorkdayTableStream):
    tap_stream_id = "performance_management_degrees"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Performance_Management"
    operation_name = "Get_Degrees"
    data_key = "Degree"
    wid_key = "Degree_Reference"
