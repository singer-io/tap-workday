"""Test tap discovery mode and metadata."""
from base import WorkdayBaseTest, WorkdayBaseTestFinancialManagement
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest


class WorkdayDiscoveryTestStandard(DiscoveryTest, WorkdayBaseTest):
    """Test tap discovery for Absence/Performance streams (standard credentials).
    
    Discovery returns all streams, but we only test metadata for streams accessible
    with standard credentials.
    """
    
    @staticmethod
    def name():
        return "tap_tester_workday_discovery_test_standard"

    def streams_to_test(self):
        # Only test streams accessible with standard credentials
        return set(self.testable_streams)


class WorkdayDiscoveryTestFinancial(DiscoveryTest, WorkdayBaseTestFinancialManagement):
    """Test tap discovery for Financial/HR/Staffing streams (financial management credentials).
    
    Discovery returns all streams, but we only test metadata for streams accessible
    with financial management credentials.
    """
    
    @staticmethod
    def name():
        return "tap_tester_workday_discovery_test_financial"

    def streams_to_test(self):
        # Only test streams accessible with financial management credentials
        return set(self.testable_streams)

