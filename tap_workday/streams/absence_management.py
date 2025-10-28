from tap_workday.streams.abstracts import WorkdayTableStream


class OverrideBalances(WorkdayTableStream):
    tap_stream_id = "absence_management_override_balances"
    replication_method = "FULL_TABLE"
    key_properties = ["Override_Balance_Reference__ID__0___value_1"]
    service_name = "Absence_Management"
    operation_name = "Get_Override_Balances"
    data_key = "Override_Balance"


class AbsenceInputs(WorkdayTableStream):
    tap_stream_id = "absence_management_absence_inputs"
    replication_method = "FULL_TABLE"
    key_properties = ["Absence_Input_Reference__ID__0___value_1"]
    service_name = "Absence_Management"
    operation_name = "Get_Absence_Inputs"
    data_key = "Absence_Input"
