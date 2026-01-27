import unittest

from base import WorkdayBaseTest
from tap_tester.base_suite_tests.pagination_test import PaginationTest


@unittest.skip("Skipped")
class WorkdayPaginationTest(PaginationTest, WorkdayBaseTest):
    """Test pagination functionality."""

    @staticmethod
    def name():
        return "tap_tester_workday_pagination_test"

    def streams_to_test(self):
        return self.expected_stream_names()
