from tap_workday.streams.common import WorkdayFullTableStream


class CertificationIssuers(WorkdayFullTableStream):
    tap_stream_id = "certification_issuers"
    replication_method = "FULL_TABLE"
    key_properties = ["ID"]
    service_name = "Performance_Management"
    operation_name = "Get_Certification_Issuers"
    data_key = "Certification_Issuer"


class Competencies(WorkdayFullTableStream):
    tap_stream_id = "competencies"
    replication_method = "FULL_TABLE"
    key_properties = ["Competency_ID"]
    service_name = "Performance_Management"
    operation_name = "Get_Competencies"
    data_key = "Competency"


class CompetencyCategories(WorkdayFullTableStream):
    tap_stream_id = "competency_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Code"]
    service_name = "Performance_Management"
    operation_name = "Get_Competency_Categories"
    data_key = "Competency_Category"


class Degrees(WorkdayFullTableStream):
    tap_stream_id = "degrees"
    replication_method = "FULL_TABLE"
    key_properties = ["ID"]
    service_name = "Performance_Management"
    operation_name = "Get_Degrees"
    data_key = "Degree"
