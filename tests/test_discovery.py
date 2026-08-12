"""Test discovery for Workday streams."""
from base import WorkdayBaseTest
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest


class WorkdayDiscoveryTest(DiscoveryTest, WorkdayBaseTest):
    """Test discovery for all configured streams."""

    @staticmethod
    def name():
        return "tap_tester_workday_discovery_test"

    def streams_to_test(self):
        return set(self.testable_streams)
