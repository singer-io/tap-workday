from tap_workday.streams.abstracts import WorkdayTableStream


class CostCenters(WorkdayTableStream):
    tap_stream_id = "financial_management_cost_centers"
    replication_method = "FULL_TABLE"
    key_properties = ["Cost_Center_Data.Organization_Data.ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Cost_Centers"
    data_key = "Cost_Center"


class Organizations(WorkdayTableStream):
    tap_stream_id = "financial_management_organizations"
    replication_method = "FULL_TABLE"
    key_properties = ["Organization_Data.Reference_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Organizations"
    data_key = "Organization"


class PositionBudgets(WorkdayTableStream):
    tap_stream_id = "financial_management_position_budgets"
    replication_method = "FULL_TABLE"
    key_properties = ["Position_Budget_Data.Position_Reference.Descriptor"]
    service_name = "Financial_Management"
    operation_name = "Get_Position_Budgets"
    data_key = "Position_Budget"


class CustomerCategories(WorkdayTableStream):
    tap_stream_id = "financial_management_customer_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Customer_Category_Data.Customer_Category_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Customer_Categories"
    data_key = "Customer_Category"


class FundHierarchies(WorkdayTableStream):
    tap_stream_id = "financial_management_fund_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["Fund_Hierarchy_Data.Fund_Hierarchy_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Fund_Hierarchies"
    data_key = "Fund_Hierarchy"


class FundTypes(WorkdayTableStream):
    tap_stream_id = "financial_management_fund_types"
    replication_method = "FULL_TABLE"
    key_properties = ["Fund_Type_Data.Fund_Type_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Fund_Types"
    data_key = "Fund_Type"


class FundingSources(WorkdayTableStream):
    tap_stream_id = "financial_management_funding_sources"
    replication_method = "FULL_TABLE"
    key_properties = ["Funding_Source_Data.Funding_Source_Name"]
    service_name = "Financial_Management"
    operation_name = "Get_Funding_Sources"
    data_key = "Funding_Source"


class Funds(WorkdayTableStream):
    tap_stream_id = "financial_management_funds"
    replication_method = "FULL_TABLE"
    key_properties = ["Fund_Data.Fund_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Funds"
    data_key = "Fund"


class JournalSources(WorkdayTableStream):
    tap_stream_id = "financial_management_journal_sources"
    replication_method = "FULL_TABLE"
    key_properties = ["Journal_Source_Data.Journal_Source_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Journal_Sources"
    data_key = "Journal_Source"


class Journals(WorkdayTableStream):
    tap_stream_id = "financial_management_journals"
    replication_method = "FULL_TABLE"
    key_properties = ["Journal_Entry_Data.Journal_Number"]
    service_name = "Financial_Management"
    operation_name = "Get_Journals"
    data_key = "Journal_Entry"


class LedgerAccountSummaries(WorkdayTableStream):
    tap_stream_id = "financial_management_ledger_account_summaries"
    replication_method = "FULL_TABLE"
    key_properties = ["Ledger_Account_Summary_Data.Ledger_Account_Summary_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Ledger_Account_Summaries"
    data_key = "Ledger_Account_Summary"


class ProgramHierarchies(WorkdayTableStream):
    tap_stream_id = "financial_management_program_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["Program_Hierarchy_Data.Program_Hierarchy_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Program_Hierarchies"
    data_key = "Program_Hierarchy"


class Programs(WorkdayTableStream):
    tap_stream_id = "financial_management_programs"
    replication_method = "FULL_TABLE"
    key_properties = ["Program_Data.Program_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Programs"
    data_key = "Program"


class RevenueCategories(WorkdayTableStream):
    tap_stream_id = "financial_management_revenue_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Revenue_Category_Data.Revenue_Category_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Revenue_Categories"
    data_key = "Revenue_Category"


class RevenueCategoryHierarchies(WorkdayTableStream):
    tap_stream_id = "financial_management_revenue_category_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["Revenue_Category_Hierarchy_Data.ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Revenue_Category_Hierarchies"
    data_key = "Revenue_Category_Hierarchy"


class SpendCategoryHierarchies(WorkdayTableStream):
    tap_stream_id = "financial_management_spend_category_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["Spend_Category_Hierarchy_Data.Spend_Category_Hierarchy_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Spend_Category_Hierarchies"
    data_key = "Spend_Category_Hierarchy"


class SupplierCategories(WorkdayTableStream):
    tap_stream_id = "financial_management_supplier_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["Supplier_Category_Data.Supplier_Category_ID"]
    service_name = "Financial_Management"
    operation_name = "Get_Supplier_Categories"
    data_key = "Supplier_Category"
