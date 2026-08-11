from tap_tester.base_suite_tests.start_date_test import StartDateTest

from base import WorkdayBaseTest


class WorkdayStartDateTest(StartDateTest, WorkdayBaseTest):
    """Instantiate start date according to the desired data set and run the
    test."""

    @staticmethod
    def name():
        return "tap_tester_workday_start_date_test"

    def streams_to_test(self):
        streams_to_include = {
            "financial_management_journals",
            "financial_management_organizations",
            "human_resources_job_profiles",
            "human_resources_organizations",
            "staffing_organizations",
        }
        return self.expected_stream_names().intersection(streams_to_include)

    @property
    def start_date_1(self):
        return "2020-01-01T00:00:00Z"

    @property
    def start_date_2(self):
        return "2021-01-01T00:00:00Z"
