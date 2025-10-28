from tap_workday.streams.abstracts import WorkdayTableStream


class CostCenters(WorkdayTableStream):
    tap_stream_id = "financial_management_cost_centers"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Cost_Centers"
    data_key = "Cost_Center"
    wid_key = "Cost_Center_Reference"


class Organizations(WorkdayTableStream):
    tap_stream_id = "financial_management_organizations"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Organizations"
    data_key = "Organization"
    wid_key = "Organization_Reference"


class PositionBudgets(WorkdayTableStream):
    tap_stream_id = "financial_management_position_budgets"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Position_Budgets"
    data_key = "Position_Budget"
    wid_key = "Position_Budget_Reference"


class CustomerCategories(WorkdayTableStream):
    tap_stream_id = "financial_management_customer_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Customer_Categories"
    data_key = "Customer_Category"
    wid_key = "Customer_Category_Reference"


class FundHierarchies(WorkdayTableStream):
    tap_stream_id = "financial_management_fund_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Fund_Hierarchies"
    data_key = "Fund_Hierarchy"
    wid_key = "Fund_Hierarchy_Reference"


class FundTypes(WorkdayTableStream):
    tap_stream_id = "financial_management_fund_types"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Fund_Types"
    data_key = "Fund_Type"
    wid_key = "Fund_Type_Reference"


class FundingSources(WorkdayTableStream):
    tap_stream_id = "financial_management_funding_sources"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Funding_Sources"
    data_key = "Funding_Source"
    wid_key = "Funding_Source_Reference"


class Funds(WorkdayTableStream):
    tap_stream_id = "financial_management_funds"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Funds"
    data_key = "Fund"
    wid_key = "Fund_Reference"


class JournalSources(WorkdayTableStream):
    tap_stream_id = "financial_management_journal_sources"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Journal_Sources"
    data_key = "Journal_Source"
    wid_key = "Journal_Source_Reference"


class Journals(WorkdayTableStream):
    tap_stream_id = "financial_management_journals"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Journals"
    data_key = "Journal_Entry"
    wid_key = "Journal_Entry_Reference"


class LedgerAccountSummaries(WorkdayTableStream):
    tap_stream_id = "financial_management_ledger_account_summaries"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Ledger_Account_Summaries"
    data_key = "Ledger_Account_Summary"
    wid_key = "Ledger_Account_Summary_Reference"


class Ledgers(WorkdayTableStream):
    tap_stream_id = "financial_management_ledgers"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Ledgers"
    data_key = "Actuals_Ledger"
    wid_key = "Actuals_Ledger_Reference"


class ProgramHierarchies(WorkdayTableStream):
    tap_stream_id = "financial_management_program_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Program_Hierarchies"
    data_key = "Program_Hierarchy"
    wid_key = "Program_Hierarchy_Reference"


class Programs(WorkdayTableStream):
    tap_stream_id = "financial_management_programs"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Programs"
    data_key = "Program"
    wid_key = "Program_Reference"


class RevenueCategories(WorkdayTableStream):
    tap_stream_id = "financial_management_revenue_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Revenue_Categories"
    data_key = "Revenue_Category"
    wid_key = "Revenue_Category_Reference"


class RevenueCategoryHierarchies(WorkdayTableStream):
    tap_stream_id = "financial_management_revenue_category_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Revenue_Category_Hierarchies"
    data_key = "Revenue_Category_Hierarchy"
    wid_key = "Revenue_Category_Hierarchy_Reference"


class SpendCategoryHierarchies(WorkdayTableStream):
    tap_stream_id = "financial_management_spend_category_hierarchies"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Spend_Category_Hierarchies"
    data_key = "Spend_Category_Hierarchy"
    wid_key = "Spend_Category_Hierarchy_Reference"


class SupplierCategories(WorkdayTableStream):
    tap_stream_id = "financial_management_supplier_categories"
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"
    operation_name = "Get_Supplier_Categories"
    data_key = "Supplier_Category"
    wid_key = "Supplier_Category_Reference"
