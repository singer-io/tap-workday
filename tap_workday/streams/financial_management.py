from tap_workday.streams.abstracts import WorkdayTableStream
from singer import get_logger

LOGGER = get_logger()


class FinancialManagementStream(WorkdayTableStream):
    replication_method = "FULL_TABLE"
    key_properties = ["key_value"]
    service_name = "Financial_Management"


class CostCenters(FinancialManagementStream):
    tap_stream_id = "financial_management_cost_centers"
    operation_name = "Get_Cost_Centers"
    data_key = "Cost_Center"
    wid_key = "Cost_Center_Reference"
    replication_method = "INCREMENTAL"
    BOOKMARK_KEY = "updated_through"

    def build_filter_params(self, updated_since, updated_through=None):
        if not updated_since:
            return {}
        return {
            "Request_Criteria": {
                "Updated_From_Date": updated_since,
                "Updated_To_Date": updated_through,
            }
        }


class Organizations(FinancialManagementStream):
    tap_stream_id = "financial_management_organizations"
    operation_name = "Get_Organizations"
    data_key = "Organization"
    wid_key = "Organization_Reference"
    replication_method = "INCREMENTAL"
    BOOKMARK_KEY = "updated_through"

    def build_filter_params(self, updated_since, updated_through=None):
        if not updated_since:
            return {}
        return {
            "Request_Criteria": {
                "Transaction_Log_Criteria": {
                    "Transaction_Date_Range_Data": {
                        "Updated_From": updated_since,
                        "Updated_Through": updated_through,
                    }
                }
            }
        }


class PositionBudgets(FinancialManagementStream):
    tap_stream_id = "financial_management_position_budgets"
    operation_name = "Get_Position_Budgets"
    data_key = "Position_Budget"
    wid_key = "Position_Budget_Reference"


class CustomerCategories(FinancialManagementStream):
    tap_stream_id = "financial_management_customer_categories"
    operation_name = "Get_Customer_Categories"
    data_key = "Customer_Category"
    wid_key = "Customer_Category_Reference"


class FundHierarchies(FinancialManagementStream):
    tap_stream_id = "financial_management_fund_hierarchies"
    operation_name = "Get_Fund_Hierarchies"
    data_key = "Fund_Hierarchy"
    wid_key = "Fund_Hierarchy_Reference"


class FundTypes(FinancialManagementStream):
    tap_stream_id = "financial_management_fund_types"
    operation_name = "Get_Fund_Types"
    data_key = "Fund_Type"
    wid_key = "Fund_Type_Reference"


class FundingSources(FinancialManagementStream):
    tap_stream_id = "financial_management_funding_sources"
    operation_name = "Get_Funding_Sources"
    data_key = "Funding_Source"
    wid_key = "Funding_Source_Reference"


class Funds(FinancialManagementStream):
    tap_stream_id = "financial_management_funds"
    operation_name = "Get_Funds"
    data_key = "Fund"
    wid_key = "Fund_Reference"


class JournalSources(FinancialManagementStream):
    tap_stream_id = "financial_management_journal_sources"
    operation_name = "Get_Journal_Sources"
    data_key = "Journal_Source"
    wid_key = "Journal_Source_Reference"


class Journals(FinancialManagementStream):
    tap_stream_id = "financial_management_journals"
    operation_name = "Get_Journals"
    data_key = "Journal_Entry"
    wid_key = "Journal_Entry_Reference"
    replication_method = "INCREMENTAL"
    BOOKMARK_KEY = "updated_through"

    def build_filter_params(self, updated_since, updated_through=None):
        if not updated_since:
            return {}
        return {
            "Request_Criteria": {
                "Updated_From_Date": updated_since,
                "Updated_To_Date": updated_through,
            }
        }

    @staticmethod
    def extract_ledger_ids_from_journals_api(client, max_pages=None):
        """Extract unique ledger IDs from journal entries using minimal API calls."""
        from tap_workday.streams.helpers import WorkdayPaginator
        
        page_info = f"(max {max_pages} pages)" if max_pages else ""
        LOGGER.debug(f"Extracting Ledger_Reference_IDs from journal entries {page_info}...")
        ledger_ids = set()
        
        paginator = WorkdayPaginator(client, "Get_Journals")
        records = paginator.paginate_operation("Journal_Entry", max_pages=max_pages)
        
        # Extract ledger IDs from records
        for record in records:
            journal_entry_data = record.get("Journal_Entry_Data", [])
            if isinstance(journal_entry_data, dict):
                journal_entry_data = [journal_entry_data]
            elif not isinstance(journal_entry_data, list):
                continue
                
            for entry_data in journal_entry_data:
                ledger_ref = entry_data.get("Ledger_Reference")
                if ledger_ref and isinstance(ledger_ref.get("ID"), list):
                    for id_entry in ledger_ref["ID"]:
                        if (isinstance(id_entry, dict) and 
                            id_entry.get("type") == "Ledger_Reference_ID" and
                            id_entry.get("_value_1")):
                            ledger_ids.add(id_entry["_value_1"])

        LOGGER.debug(f"Extracted {len(ledger_ids)} unique Ledger_Reference_IDs")
        return ledger_ids


class LedgerAccountSummaries(FinancialManagementStream):
    tap_stream_id = "financial_management_ledger_account_summaries"
    operation_name = "Get_Ledger_Account_Summaries"
    data_key = "Ledger_Account_Summary"
    wid_key = "Ledger_Account_Summary_Reference"


class Ledgers(FinancialManagementStream):
    tap_stream_id = "financial_management_ledgers"
    operation_name = "Get_Ledgers"
    data_key = "Ledger"
    wid_key = "Actuals_Ledger_Reference"

    @classmethod
    def check_access(cls, client):
        """
        Custom check_access for Get_Ledgers operation that requires Request_Reference.
        Uses a real ledger ID extracted from journals (1 page only) to verify API accessibility without retry logic.
        """
        # Get a real ledger ID from journals for access testing (limit to 1 page)
        try:
            ledger_ids = Journals.extract_ledger_ids_from_journals_api(client, max_pages=1)
            ledger_id = next(iter(ledger_ids)) if ledger_ids else "TEST_LEDGER"
        except Exception as exc:
            LOGGER.warning(f"Failed to extract ledger ID for access check: {exc}")
            ledger_id = "TEST_LEDGER"
        
        dummy_params = {
            'Request_Reference': {
                'Actuals_Ledger_Reference': {
                    'ID': [{'_value_1': ledger_id, 'type': 'Ledger_Reference_ID'}]
                }
            },
            'Response_Filter': {'Page': 1, 'Count': 1}  # Minimal page size for testing
        }
        
        try:
            result = client.check_access(cls.operation_name, **dummy_params)
            return result
        except Exception as exc:
            LOGGER.info(f"Access check for {cls.operation_name}: {exc}")
            raise

    def sync(self, state, transformer, parent_obj=None):
        """Synchronize records for Ledgers with automatic ledger ID discovery from Journals."""
        from tap_workday.streams.helpers import emit_full_table

        client = self.get_client()
        
        try:
            discovered_ledger_ids = Journals.extract_ledger_ids_from_journals_api(client)
            if not discovered_ledger_ids:
                LOGGER.warning("No Ledger_Reference_IDs found in Journals. No ledgers to sync.")
                return emit_full_table(self, [])

            LOGGER.info(f"Discovered {len(discovered_ledger_ids)} unique ledgers")
        except Exception as exc:
            LOGGER.error(f"Failed to discover ledger IDs from Journals: {exc}")
            return emit_full_table(self, [])
        
        # Retrieve data for each ledger ID
        all_records = []
        for ledger_ref_id in discovered_ledger_ids:
            try:
                records = self._call_get_ledgers_with_reference_id(client, ledger_ref_id)
                all_records.extend(records)
                LOGGER.info(f"Retrieved {len(records)} records for ledger: {ledger_ref_id}")
            except Exception as exc:
                LOGGER.warning(f"Failed to retrieve data for ledger {ledger_ref_id}: {exc}")
        
        LOGGER.info(f"Total records retrieved: {len(all_records)}")
        return emit_full_table(self, all_records)
    
    def _call_get_ledgers_with_reference_id(self, client, ledger_reference_id):
        """Call Get_Ledgers operation using Ledger_Reference_ID.

        Get_Ledgers_RequestType has no Request_Criteria member, so incremental
        date filtering is not supported for this operation.
        """
        from tap_workday.streams.helpers import WorkdayPaginator, _extract_key_value

        custom_params = {
            'Request_Reference': {
                'Actuals_Ledger_Reference': {
                    'ID': [{'_value_1': ledger_reference_id, 'type': 'Ledger_Reference_ID'}]
                }
            }
        }
        
        paginator = WorkdayPaginator(client, self.operation_name)
        records = paginator.paginate_operation(self.data_key, custom_params=custom_params)
        
        # Add key_value to records
        for record in records:
            key_value = _extract_key_value(record, self.wid_key)
            if key_value:
                record["key_value"] = key_value

        return records


class ProgramHierarchies(FinancialManagementStream):
    tap_stream_id = "financial_management_program_hierarchies"
    operation_name = "Get_Program_Hierarchies"
    data_key = "Program_Hierarchy"
    wid_key = "Program_Hierarchy_Reference"


class Programs(FinancialManagementStream):
    tap_stream_id = "financial_management_programs"
    operation_name = "Get_Programs"
    data_key = "Program"
    wid_key = "Program_Reference"


class RevenueCategories(FinancialManagementStream):
    tap_stream_id = "financial_management_revenue_categories"
    operation_name = "Get_Revenue_Categories"
    data_key = "Revenue_Category"
    wid_key = "Revenue_Category_Reference"
    replication_method = "INCREMENTAL"
    BOOKMARK_KEY = "updated_through"

    def build_filter_params(self, updated_since, updated_through=None):
        if not updated_since:
            return {}
        return {
            "Request_Criteria": {
                "Updated_From_Date": updated_since,
                "Updated_To_Date": updated_through,
            }
        }


class RevenueCategoryHierarchies(FinancialManagementStream):
    tap_stream_id = "financial_management_revenue_category_hierarchies"
    operation_name = "Get_Revenue_Category_Hierarchies"
    data_key = "Revenue_Category_Hierarchy"
    wid_key = "Revenue_Category_Hierarchy_Reference"


class SpendCategoryHierarchies(FinancialManagementStream):
    tap_stream_id = "financial_management_spend_category_hierarchies"
    operation_name = "Get_Spend_Category_Hierarchies"
    data_key = "Spend_Category_Hierarchy"
    wid_key = "Spend_Category_Hierarchy_Reference"


class SupplierCategories(FinancialManagementStream):
    tap_stream_id = "financial_management_supplier_categories"
    operation_name = "Get_Supplier_Categories"
    data_key = "Supplier_Category"
    wid_key = "Supplier_Category_Reference"
