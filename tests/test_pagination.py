from base import WorkdayBaseTest, WorkdayBaseTestFinancialManagement
from tap_tester.base_suite_tests.pagination_test import PaginationTest


class WorkdayPaginationBase(PaginationTest):
    """Ensure tap can replicate multiple pages of data for streams that use pagination."""

    @staticmethod
    def name():
        return "tap_tester_workday_pagination_test"

    def streams_to_test(self):
        streams_to_exclude = {}
        return self.expected_stream_names().difference(streams_to_exclude)


# Test classes for different stream groups
class WorkdayPaginationTest(WorkdayPaginationBase, WorkdayBaseTest):
    """Pagination test for absence/performance streams."""
    pass


class WorkdayPaginationTestFinancialManagement(WorkdayPaginationBase, WorkdayBaseTestFinancialManagement):
    """Pagination test for financial/HR/staffing streams."""
    pass
