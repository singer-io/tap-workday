from tap_workday.streams.common import WorkdayFullTableStream


class CostCenters(WorkdayFullTableStream):
    tap_stream_id = "cost_centers"
    replication_method = "FULL_TABLE"
    key_properties = ["Cost_Center_Data.Organization_Data.ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Cost_Centers"
    data_key = "Cost_Center"


class Organizations(WorkdayFullTableStream):
    tap_stream_id = "fm_organizations"
    replication_method = "FULL_TABLE"
    key_properties = ["Organization_Data.Reference_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Organizations"
    data_key = "Organization"


class PositionBudgets(WorkdayFullTableStream):
    tap_stream_id = "position_budgets"
    replication_method = "FULL_TABLE"
    key_properties = ["Position_Budget_Data.Position_Reference.Descriptor"]
    service_name = "Financial_Management"
    operation_name = "Get_Position_Budgets"
    data_key = "Position_Budget"


class CustomerCategories(WorkdayFullTableStream):
    tap_stream_id = "customer_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Customer_Category_Data.Customer_Category_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Customer_Categories"
    data_key = "Customer_Category"


class FundHierarchies(WorkdayFullTableStream):
    tap_stream_id = "fund_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["Fund_Hierarchy_Data.Fund_Hierarchy_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Fund_Hierarchies"
    data_key = "Fund_Hierarchy"


class FundTypes(WorkdayFullTableStream):
    tap_stream_id = "fund_types"
    replication_method = "FULL_TABLE"
    key_properties = ["Fund_Type_Data.Fund_Type_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Fund_Types"
    data_key = "Fund_Type"


class FundingSources(WorkdayFullTableStream):
    tap_stream_id = "funding_sources"
    replication_method = "FULL_TABLE"
    key_properties = ["Funding_Source_Data.Funding_Source_Name"]
    service_name = "Financial_Management"
    operation_name = "Get_Funding_Sources"
    data_key = "Funding_Source"


class Funds(WorkdayFullTableStream):
    tap_stream_id = "funds"
    replication_method = "FULL_TABLE"
    key_properties = ["Fund_Data.Fund_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Funds"
    data_key = "Fund"


class JournalSources(WorkdayFullTableStream):
    tap_stream_id = "journal_sources"
    replication_method = "FULL_TABLE"
    key_properties = ["Journal_Source_Data.Journal_Source_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Journal_Sources"
    data_key = "Journal_Source"


class Journals(WorkdayFullTableStream):
    tap_stream_id = "journals"
    replication_method = "FULL_TABLE"
    key_properties = ["Journal_Entry_Data.Journal_Number"]
    service_name = "Financial_Management"
    operation_name = "Get_Journals"
    data_key = "Journal_Entry"


class LedgerAccountSummaries(WorkdayFullTableStream):
    tap_stream_id = "ledger_account_summaries"
    replication_method = "FULL_TABLE"
    key_properties = ["Ledger_Account_Summary_Data.Ledger_Account_Summary_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Ledger_Account_Summaries"
    data_key = "Ledger_Account_Summary"


class Ledgers(WorkdayFullTableStream):
    tap_stream_id = "ledgers"
    replication_method = "FULL_TABLE"
    key_properties = ["Ledger_Data.Actuals_Ledger_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Ledgers"
    data_key = "Actuals_Ledger"


class ProgramHierarchies(WorkdayFullTableStream):
    tap_stream_id = "program_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["Program_Hierarchy_Data.Program_Hierarchy_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Program_Hierarchies"
    data_key = "Program_Hierarchy"


class Programs(WorkdayFullTableStream):
    tap_stream_id = "programs"
    replication_method = "FULL_TABLE"
    key_properties = ["Program_Data.Program_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Programs"
    data_key = "Program"


class RevenueCategories(WorkdayFullTableStream):
    tap_stream_id = "revenue_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Revenue_Category_Data.Revenue_Category_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Revenue_Categories"
    data_key = "Revenue_Category"


class RevenueCategoryHierarchies(WorkdayFullTableStream):
    tap_stream_id = "revenue_category_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["Revenue_Category_Hierarchy_Data.ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Revenue_Category_Hierarchies"
    data_key = "Revenue_Category_Hierarchy"


class SpendCategoryHierarchies(WorkdayFullTableStream):
    tap_stream_id = "spend_category_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["Spend_Category_Hierarchy_Data.Spend_Category_Hierarchy_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Spend_Category_Hierarchies"
    data_key = "Spend_Category_Hierarchy"


class SupplierCategories(WorkdayFullTableStream):
    tap_stream_id = "supplier_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Supplier_Category_Data.Supplier_Category_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Supplier_Categories"
    data_key = "Supplier_Category"
