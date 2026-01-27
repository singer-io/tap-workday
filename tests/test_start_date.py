import unittest

from base import WorkdayBaseTest
from tap_tester.base_suite_tests.start_date_test import StartDateTest


@unittest.skip("Skipped")
class WorkdayStartDateTest(StartDateTest, WorkdayBaseTest):
    """Test start date functionality."""

    @staticmethod
    def name():
        return "tap_tester_workday_start_date_test"

    def streams_to_test(self):
        return self.expected_stream_names()

    @property
    def start_date_1(self):
        return "2015-03-25T00:00:00Z"

    @property
    def start_date_2(self):
        return "2017-01-25T00:00:00Z"
