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

    def sync(self, state, transformer, parent_obj=None):
        """
        Custom sync for Get_Ledgers operation.
        
        Note: The Workday Get_Ledgers operation has a discrepancy between its documentation 
        (which states Request_Reference is optional) and the actual SOAP schema implementation
        (which requires specific ledger IDs in Request_Reference). This implementation 
        gracefully handles this limitation by returning an empty result set with appropriate
        logging when specific ledger IDs are not available.
        """
        from tap_workday.streams.helpers import emit_full_table
        from singer import get_logger
        
        logger = get_logger()
        logger.warning(
            "The Get_Ledgers operation requires specific ledger IDs in the Request_Reference parameter. "
            "While Workday documentation suggests this parameter is optional, the SOAP schema validation "
            "requires it. Without specific ledger IDs to query, this stream will return no records. "
            "To use this stream effectively, you would need to modify the implementation to provide "
            "specific Actuals_Ledger_Reference IDs."
        )
        
        # Return empty result set since we cannot retrieve all ledgers without specific IDs
        return emit_full_table(self, [])


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
