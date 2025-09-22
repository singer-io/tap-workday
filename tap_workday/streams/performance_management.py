from tap_workday.streams.abstracts import WorkdayTableStream


class CertificationIssuers(WorkdayTableStream):
    tap_stream_id = "performance_management_certification_issuers"
    replication_method = "FULL_TABLE"
    key_properties = ["ID"]
    service_name = "Performance_Management"
    operation_name = "Get_Certification_Issuers"
    data_key = "Certification_Issuer"


class Competencies(WorkdayTableStream):
    tap_stream_id = "performance_management_competencies"
    replication_method = "FULL_TABLE"
    key_properties = ["Competency_ID"]
    service_name = "Performance_Management"
    operation_name = "Get_Competencies"
    data_key = "Competency"


class CompetencyCategories(WorkdayTableStream):
    tap_stream_id = "performance_management_competency_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Code"]
    service_name = "Performance_Management"
    operation_name = "Get_Competency_Categories"
    data_key = "Competency_Category"


class Degrees(WorkdayTableStream):
    tap_stream_id = "performance_management_degrees"
    replication_method = "FULL_TABLE"
    key_properties = ["ID"]
    service_name = "Performance_Management"
    operation_name = "Get_Degrees"
    data_key = "Degree"
