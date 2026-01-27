import unittest

from base import WorkdayBaseTest
from tap_tester.base_suite_tests.interrupted_sync_test import InterruptedSyncTest


@unittest.skip("Skipped")
class WorkdayInterruptedSyncTest(InterruptedSyncTest, WorkdayBaseTest):
    """Test interrupted sync functionality."""

    @staticmethod
    def name():
        return "tap_tester_workday_interrupted_sync_test"

    def streams_to_test(self):
        return self.expected_stream_names()

    def manipulate_state(self):
        return {"currently_syncing": "prospects", "bookmarks": {}}
