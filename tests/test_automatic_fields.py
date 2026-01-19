"""Test that with no fields selected for a stream automatic fields are still
replicated."""
from base import WorkdayBaseTest, WorkdayBaseTestFinancialManagement
from tap_tester import runner
from tap_tester.base_suite_tests.automatic_fields_test import MinimumSelectionTest


class WorkdayAutomaticFieldsBase(MinimumSelectionTest):
    """Base class for automatic fields tests."""

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test"

    def streams_to_test(self):
        streams_to_exclude = {}
        return self.expected_stream_names().difference(streams_to_exclude)

    def setUp(self):
        """Override setUp to cache test results."""
        cached_variables = all([
            MinimumSelectionTest.record_count,
            MinimumSelectionTest.actual_field,
            MinimumSelectionTest.synced_messages])

        if not cached_variables:
            # Establish connection
            conn_id = self.create_connection()

            # run check mode
            found_catalogs = self.run_and_verify_check_mode(conn_id)

            # table and field selection
            test_catalogs = [catalog for catalog in found_catalogs
                             if catalog.get('stream_name') in self.streams_to_test()]

            # make non_selected_fields be all fields
            self.perform_and_verify_table_and_field_selection(conn_id, test_catalogs)

            # Run a sync job using orchestrator and save the results
            MinimumSelectionTest.record_count = self.run_and_verify_sync_mode(conn_id)
            MinimumSelectionTest.actual_field = runner.examine_target_output_for_fields()
            MinimumSelectionTest.synced_messages = runner.get_records_from_target_output()


# Test classes for different stream groups
class WorkdayAutomaticFields(WorkdayAutomaticFieldsBase, WorkdayBaseTest):
    """Automatic fields test for absence/performance streams."""
    pass


class WorkdayAutomaticFieldsFinancialManagement(WorkdayAutomaticFieldsBase, WorkdayBaseTestFinancialManagement):
    """Automatic fields test for financial/HR/staffing streams."""
    pass
