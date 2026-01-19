"""Test tap discovery mode and metadata."""
from base import WorkdayBaseTest, WorkdayBaseTestFinancialManagement
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest


class WorkdayDiscoveryBase(DiscoveryTest):
    """Test tap discovery mode and metadata conforms to standards."""

    @staticmethod
    def name():
        return "tap_tester_workday_discovery_test"

    def streams_to_test(self):
        return self.expected_stream_names()


# Test classes for different stream groups
class WorkdayDiscoveryTest(WorkdayDiscoveryBase, WorkdayBaseTest):
    """Discovery test for absence/performance streams."""
    pass


class WorkdayDiscoveryTestFinancialManagement(WorkdayDiscoveryBase, WorkdayBaseTestFinancialManagement):
    """Discovery test for financial/HR/staffing streams."""
    pass
