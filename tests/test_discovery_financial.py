"""
Test discovery for Financial Management streams.

NOTE: Separate file required because DiscoveryTest uses class-level caching. Multiple test
classes in one file would share cached variables, causing the second class to incorrectly
reuse the first class's data (wrong streams/credentials). Separate files ensure isolated execution.
"""
from base import WorkdayBaseTestFinancial
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest


class WorkdayDiscoveryTestFinancial(DiscoveryTest, WorkdayBaseTestFinancial):
    """Test discovery for Financial streams."""
    
    @staticmethod
    def name():
        return "tap_tester_workday_discovery_test_financial"

    def streams_to_test(self):
        return set(self.testable_streams)
