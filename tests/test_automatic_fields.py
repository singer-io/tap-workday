"""Test that with no fields selected for a stream automatic fields are still
replicated."""
from base import WorkdayBaseTest, WorkdayBaseTestFinancialManagement
from tap_tester import connections, runner
from tap_tester.base_suite_tests.automatic_fields_test import MinimumSelectionTest


class WorkdayAutomaticFieldsStandard(MinimumSelectionTest, WorkdayBaseTest):
    """Test automatic fields for Absence/Performance streams (standard credentials).
    
    Only tests streams accessible with standard credentials to avoid authorization errors.
    """

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test_standard"

    def streams_to_test(self):
        # Only test streams accessible with standard credentials
        streams_to_exclude = set()
        return set(self.testable_streams).difference(streams_to_exclude)

    def setUp(self):
        """Override setUp to cache test results."""
        cached_variables = all([
            MinimumSelectionTest.record_count,
            MinimumSelectionTest.actual_field,
            MinimumSelectionTest.synced_messages])

        if not cached_variables:
            # Establish connection
            conn_id = connections.ensure_connection(self)

            # run check mode
            found_catalogs = self.run_and_verify_check_mode(conn_id)

            # table and field selection - only select testable streams
            test_catalogs = [catalog for catalog in found_catalogs
                             if catalog.get('stream_name') in self.streams_to_test()]

            # make non_selected_fields be all fields
            self.perform_and_verify_table_and_field_selection(conn_id, test_catalogs)

            # Run a sync job using orchestrator and save the results
            MinimumSelectionTest.record_count = self.run_and_verify_sync_mode(conn_id)
            MinimumSelectionTest.actual_field = runner.examine_target_output_for_fields()
            MinimumSelectionTest.synced_messages = runner.get_records_from_target_output()


class WorkdayAutomaticFieldsFinancial(MinimumSelectionTest, WorkdayBaseTestFinancialManagement):
    """Test automatic fields for Financial/HR/Staffing streams (financial management credentials).
    
    Only tests streams accessible with financial management credentials to avoid authorization errors.
    """

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test_financial"

    def streams_to_test(self):
        # Only test streams accessible with financial management credentials
        streams_to_exclude = set()
        return set(self.testable_streams).difference(streams_to_exclude)

    def setUp(self):
        """Override setUp to cache test results."""
        cached_variables = all([
            MinimumSelectionTest.record_count,
            MinimumSelectionTest.actual_field,
            MinimumSelectionTest.synced_messages])

        if not cached_variables:
            # Establish connection
            conn_id = connections.ensure_connection(self)

            # run check mode
            found_catalogs = self.run_and_verify_check_mode(conn_id)

            # table and field selection - only select testable streams
            test_catalogs = [catalog for catalog in found_catalogs
                             if catalog.get('stream_name') in self.streams_to_test()]

            # make non_selected_fields be all fields
            self.perform_and_verify_table_and_field_selection(conn_id, test_catalogs)

            # Run a sync job using orchestrator and save the results
            MinimumSelectionTest.record_count = self.run_and_verify_sync_mode(conn_id)
            MinimumSelectionTest.actual_field = runner.examine_target_output_for_fields()
            MinimumSelectionTest.synced_messages = runner.get_records_from_target_output()

