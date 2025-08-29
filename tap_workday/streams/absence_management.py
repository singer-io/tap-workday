from tap_workday.streams.common import WorkdayFullTableStream


class OverrideBalances(WorkdayFullTableStream):
    tap_stream_id = "override_balances"
    replication_method = "FULL_TABLE"
    key_properties = ["Override_Balance_Reference.ID"]
    service_name = "Absence_Management"
    operation_name = "Get_Override_Balances"
    data_key = "Override_Balance"


class AbsenceInputs(WorkdayFullTableStream):
    tap_stream_id = "absence_inputs"
    replication_method = "FULL_TABLE"
    key_properties = ["Absence_Input_Reference.ID"]
    service_name = "Absence_Management"
    operation_name = "Get_Absence_Inputs"
    data_key = "Absence_Input"
