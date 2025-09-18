from tap_workday.streams.abstracts import WorkdayTableStream


class CostCenters(WorkdayTableStream):
    tap_stream_id = "cost_centers"
    replication_method = "FULL_TABLE"
    key_properties = ["Cost_Center_Data.Organization_Data.ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Cost_Centers"
    data_key = "Cost_Center"


class Organizations(WorkdayTableStream):
    tap_stream_id = "fm_organizations"
    replication_method = "FULL_TABLE"
    key_properties = ["Organization_Data.Reference_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Organizations"
    data_key = "Organization"


class PositionBudgets(WorkdayTableStream):
    tap_stream_id = "position_budgets"
    replication_method = "FULL_TABLE"
    key_properties = ["Position_Budget_Data.Position_Reference.Descriptor"]
    service_name = "Financial_Management"
    operation_name = "Get_Position_Budgets"
    data_key = "Position_Budget"
