from base import WorkdayBaseTest, WorkdayBaseTestFinancial
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest


class WorkdayDiscoveryTestStandard(DiscoveryTest, WorkdayBaseTest):
    """Test discovery for HR/Staffing/Absence/Performance streams."""
    
    @staticmethod
    def name():
        return "tap_tester_workday_discovery_test_standard"

    def streams_to_test(self):
        return set(self.testable_streams)


class WorkdayDiscoveryTestFinancial(DiscoveryTest, WorkdayBaseTestFinancial):
    """Test discovery for Financial streams."""
    
    @staticmethod
    def name():
        return "tap_tester_workday_discovery_test_financial"

    def streams_to_test(self):
        return set(self.testable_streams)

