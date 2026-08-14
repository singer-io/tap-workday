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
    replication_keys = ["updated_through"]
    # NOTE: Get_Cost_Centers responses contain no last-modified timestamp.
    # Cost_Center_Data.Effective_Date is the organizational effective date
    # (when the cost center version became active), not when the record was
    # last modified.  The API is filtered via
    # Cost_Center_Request_CriteriaType.Updated_From_Date (internal update
    # tracking) which is not surfaced in the response payload.
    # bookmark_field_path = None -> bookmark falls back to sync_start_time
    # (no guaranteed record overlap across sync windows).
    bookmark_field_path = None

    def build_filter_params(self, updated_since, updated_through=None):
        # updated_since = bookmark from state (or start_date on first run).
        # Run 2+ returns 0 records when nothing changed since the last sync —
        # that is correct; it does NOT mean data was missed.
        if not updated_since:
            return {}
        return {
            "Request_Criteria": {
                "Updated_From_Date": updated_since,    # bookmark / start_date
                "Updated_To_Date": updated_through,    # sync_start_time
            }
        }


class Organizations(FinancialManagementStream):
    tap_stream_id = "financial_management_organizations"
    operation_name = "Get_Organizations"
    data_key = "Organization"
    wid_key = "Organization_Reference"
    replication_method = "INCREMENTAL"
    replication_keys = ["updated_through"]
    # NOTE: Organization_Data.Last_Updated_DateTime is the EFFECTIVE date of
    # the most recent change and may be future-dated.  Workday's
    # Transaction_Log_Criteria.Updated_From operates on the internal
    # transaction log timestamp, which is not in the response and can precede
    # Last_Updated_DateTime significantly.  sync_start_time is the correct
    # bookmark; see human_resources.Organizations for full explanation.
    bookmark_field_path = None

    def build_filter_params(self, updated_since, updated_through=None):
        # Same incremental filter logic — see CostCenters.build_filter_params.
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
    replication_keys = ["updated_through"]

    def build_filter_params(self, updated_since, updated_through=None):
        # Same incremental filter logic — see CostCenters.build_filter_params.
        if not updated_since:
            return {}
        return {
            "Request_Criteria": {
                "Updated_From_Date": updated_since,
                "Updated_To_Date": updated_through,
            }
        }

    @staticmethod
    def extract_ledger_ids_from_journals_api(client, max_pages=None, updated_since=None, updated_through=None):
        """Extract unique ledger IDs from journal entries using minimal API calls.
        
        Args:
            client: Workday client instance
            max_pages: Maximum pages to fetch (None = all pages)
            updated_since: Start date for incremental filtering (None = all journals)
            updated_through: End date for incremental filtering
        """
        from tap_workday.streams.helpers import WorkdayPaginator
        
        page_info = f"(max {max_pages} pages)" if max_pages else "(all pages)"
        date_info = f" since {updated_since}" if updated_since else " (all time)"
        LOGGER.info(f"Extracting Ledger_Reference_IDs from journal entries {page_info}{date_info}...")
        ledger_ids = set()
        
        # Build incremental filter params if date range provided
        custom_params = None
        if updated_since:
            custom_params = {
                "Request_Criteria": {
                    "Updated_From_Date": updated_since,
                    "Updated_To_Date": updated_through,
                }
            }
        
        paginator = WorkdayPaginator(client, "Get_Journals")
        records = paginator.paginate_operation("Journal_Entry", custom_params=custom_params, max_pages=max_pages)
        
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

        LOGGER.info(f"Extracted {len(ledger_ids)} unique Ledger_Reference_IDs")
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
    # FULL_TABLE: Get_Ledgers has no Request_Criteria for date filtering.
    # Optimization: discover ledger IDs from journals since start_date to reduce API calls.

    @classmethod
    def check_access(cls, client):
        """
        Custom check_access for Get_Ledgers operation that requires Request_Reference.
        Uses a real ledger ID extracted from journals (1 page only) to verify API accessibility without retry logic.
        """
        # Get a real ledger ID from journals for access testing (limit to 1 page, no date filtering)
        try:
            ledger_ids = Journals.extract_ledger_ids_from_journals_api(
                client, max_pages=1, updated_since=None, updated_through=None
            )
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
        """Synchronize records for Ledgers with automatic ledger ID discovery from Journals.

        FULL_TABLE stream with optimization: discovers ledger IDs from journals since
        start_date (not bookmark) to reduce API calls. Always returns complete snapshot
        of discovered ledgers.
        
        Note: Ledgers that exist but have no journal activity since start_date will not
        be discovered. This is acceptable as such ledgers are likely inactive.
        """
        from datetime import datetime, timezone
        from tap_workday.streams.helpers import emit_full_table

        client = self.get_client()
        
        # Use start_date to filter journals (optimization, not incremental sync)
        # Access config from client.config (set during Client initialization)
        start_date = client.config.get("start_date")
        
        if not start_date:
            LOGGER.warning("No start_date in config. Using None (will fetch all journals).")
        
        # Workday API requires both Update From and To dates
        # Use current time as end date to capture all journals from start_date to now
        updated_through = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        LOGGER.info(f"Discovering ledger IDs from journal entries since {start_date}...")
        try:
            discovered_ledger_ids = Journals.extract_ledger_ids_from_journals_api(
                client, 
                updated_since=start_date,
                updated_through=updated_through
            )
        except Exception as e:
            LOGGER.warning(f"Failed to discover ledger IDs from journals: {e}")
            return emit_full_table(self, [])
        
        if not discovered_ledger_ids:
            LOGGER.info("No Ledger_Reference_IDs found in journals. Syncing 0 ledgers.")
            return emit_full_table(self, [])

        LOGGER.info(f"Discovered {len(discovered_ledger_ids)} unique ledgers from journals")
        
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
    replication_keys = ["updated_through"]
    # NOTE: Get_Revenue_Categories responses contain no date/time fields
    # whatsoever.  Revenue_Category_Data has only identifier, name, and
    # classification fields.  The API is filtered via
    # Revenue_Category_Request_CriteriaType.Updated_From_Date (internal
    # update tracking) which is not exposed in the response payload.
    # bookmark_field_path = None -> bookmark falls back to sync_start_time
    # (no guaranteed record overlap across sync windows).
    bookmark_field_path = None

    def build_filter_params(self, updated_since, updated_through=None):
        # Same incremental filter logic — see CostCenters.build_filter_params.
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
