from tap_tester.base_suite_tests.start_date_test import StartDateTest

from base import WorkdayBaseTest


class WorkdayStartDateTest(StartDateTest, WorkdayBaseTest):
    """Instantiate start date according to the desired data set and run the
    test."""

    @staticmethod
    def name():
        return "tap_tester_workday_start_date_test"

    def streams_to_test(self):
        streams_to_exclude = {
            "financial_management_ledgers",
        }
        return self.expected_stream_names().difference(streams_to_exclude)

    @property
    def start_date_1(self):
        return "2025-01-01T00:00:00Z"

    @property
    def start_date_2(self):
        return "2026-01-01T00:00:00Z"
