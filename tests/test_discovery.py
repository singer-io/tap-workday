"""Test tap discovery mode and metadata."""

from base import workdayBaseTest
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest


class workdayDiscoveryTest(DiscoveryTest, workdayBaseTest):
    """Test tap discovery mode and metadata conforms to standards."""

    @staticmethod
    def name():
        return "tap_tester_workday_discovery_test"

    def streams_to_test(self):
        return self.expected_stream_names()
