"""Test that with no fields selected for a stream automatic fields are still
replicated."""
from base import WorkdayBaseTest
from tap_tester import connections
from tap_tester.base_suite_tests.automatic_fields_test import \
    MinimumSelectionTest
from tap_tester.logger import LOGGER


class WorkdayAutomaticFields(MinimumSelectionTest, WorkdayBaseTest):
    """Test that with no fields selected for a stream automatic fields are
    still replicated."""
    
    # Class variable to store which credential set is active
    active_cred_set = None

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test"

    def streams_to_test(self):
        streams_to_exclude = {
            # Financial Management
            "financial_management_journals",
            "financial_management_ledgers",
            "financial_management_fund_hierarchies",
            "financial_management_fund_types",
            "financial_management_funding_sources",
            "financial_management_funds",
            "financial_management_position_budgets",
            "financial_management_program_hierarchies",
            "financial_management_programs",

            # Absence Management - require different credentials / no data
            "absence_management_override_balances",
            "absence_management_absence_inputs",
            # Performance Management - require different credentials / no data
            "performance_management_certification_issuers",
            "performance_management_competencies",
            "performance_management_competency_categories",
            "performance_management_degrees"           
        }
        return self.expected_stream_names().difference(streams_to_exclude)
    
    @staticmethod
    def get_credentials():
        """Override to use the active credential set."""
        cred_set = WorkdayAutomaticFields.active_cred_set or "first"
        return WorkdayBaseTest.get_credentials(cred_set)

    def setUp(self):
        """Override setUp to use credential fallback logic."""
        cached_variables = all([
            MinimumSelectionTest.record_count,
            MinimumSelectionTest.actual_field,
            MinimumSelectionTest.synced_messages])

        if not cached_variables:
            # Try first credentials, fallback to second
            conn_id = self._ensure_connection_with_fallback()

            # run check mode
            found_catalogs = self.run_and_verify_check_mode(conn_id)

            # table and field selection
            test_catalogs = [catalog for catalog in found_catalogs
                             if catalog.get('stream_name') in self.streams_to_test()]

            # make non_selected_fields be all fields
            self.perform_and_verify_table_and_field_selection(conn_id, test_catalogs)

            # Run a sync job using orchestrator and save the results
            from tap_tester import runner
            MinimumSelectionTest.record_count = self.run_and_verify_sync_mode(conn_id)
            MinimumSelectionTest.actual_field = runner.examine_target_output_for_fields()
            MinimumSelectionTest.synced_messages = runner.get_records_from_target_output()

    def _ensure_connection_with_fallback(self):
        """Create connection with automatic fallback from first to second credentials."""
        # Try first credentials
        try:
            WorkdayAutomaticFields.active_cred_set = "first"
            conn_id = connections.ensure_connection(self)
            LOGGER.info("Connected using first credential set")
            return conn_id
        except Exception as e:
            LOGGER.warning(f"First credentials failed: {e}")
            
            # Try second credentials
            try:
                WorkdayAutomaticFields.active_cred_set = "second"
                conn_id = connections.ensure_connection(self)
                LOGGER.info("Connected using second credential set")
                return conn_id
            except Exception as e2:
                LOGGER.error(f"Second credentials failed: {e2}")
                raise Exception(f"Both credential sets failed. First: {e}, Second: {e2}")
