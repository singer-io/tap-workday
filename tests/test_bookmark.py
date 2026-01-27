import unittest

from base import WorkdayBaseTest
from tap_tester.base_suite_tests.bookmark_test import BookmarkTest


@unittest.skip("Skipped")
class WorkdayBookMarkTest(BookmarkTest, WorkdayBaseTest):
    """Test bookmark functionality."""

    bookmark_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    initial_bookmarks = {"bookmarks": {}}

    @staticmethod
    def name():
        return "tap_tester_workday_bookmark_test"

    def streams_to_test(self):
        return self.expected_stream_names()
