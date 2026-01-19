from base import WorkdayBaseTest, WorkdayBaseTestFinancialManagement
from tap_tester.base_suite_tests.all_fields_test import AllFieldsTest

KNOWN_MISSING_FIELDS = {}


class WorkdayAllFieldsBase(AllFieldsTest):
    """Ensure running the tap with all streams and fields selected results in
    the replication of all fields."""

    @staticmethod
    def name():
        return "tap_tester_workday_all_fields_test"

    def streams_to_test(self):
        streams_to_exclude = {}
        return self.expected_stream_names().difference(streams_to_exclude)


# Test classes for different stream groups
class WorkdayAllFields(WorkdayAllFieldsBase, WorkdayBaseTest):
    """All fields test for absence/performance streams."""
    pass


class WorkdayAllFieldsFinancialManagement(WorkdayAllFieldsBase, WorkdayBaseTestFinancialManagement):
    """All fields test for financial/HR/staffing streams."""
    pass
