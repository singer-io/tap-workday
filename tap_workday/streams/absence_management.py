from tap_workday.streams.abstracts import WorkdayTableStream


class OverrideBalances(WorkdayTableStream):
    tap_stream_id = "absence_management_override_balances"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Absence_Management"
    operation_name = "Get_Override_Balances"
    data_key = "Override_Balance"
    wid_key = "Override_Balance_Reference"


class AbsenceInputs(WorkdayTableStream):
    tap_stream_id = "absence_management_absence_inputs"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Absence_Management"
    operation_name = "Get_Absence_Inputs"
    data_key = "Absence_Input"
    wid_key = "Absence_Input_Reference"
