"""
Test discovery for HR/Staffing/Absence/Performance streams.

NOTE: Separate file required because DiscoveryTest uses class-level caching. Multiple test
classes in one file would share cached variables, causing the second class to incorrectly
reuse the first class's data (wrong streams/credentials). Separate files ensure isolated execution.
"""
from base import WorkdayBaseTest
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest


class WorkdayDiscoveryTestStandard(DiscoveryTest, WorkdayBaseTest):
    """Test discovery for HR/Staffing/Absence/Performance streams."""
    
    @staticmethod
    def name():
        return "tap_tester_workday_discovery_test_standard"

    def streams_to_test(self):
        return set(self.testable_streams)
