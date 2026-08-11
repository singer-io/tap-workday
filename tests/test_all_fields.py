"""
Test all fields for HR/Staffing/Absence/Performance streams.

NOTE: Separate file required because AllFieldsTest uses class-level caching. Multiple test
classes in one file would share cached variables, causing the second class to incorrectly
reuse the first class's data (wrong streams/credentials). Separate files ensure isolated execution.
"""
from base import WorkdayBaseTest
from tap_tester.base_suite_tests.all_fields_test import AllFieldsTest


class WorkdayAllFieldsStandard(AllFieldsTest, WorkdayBaseTest):
    """Test all fields for HR/Staffing/Absence/Performance streams."""

    @staticmethod
    def name():
        return "tap_tester_workday_all_fields_test_standard"

    def streams_to_test(self):
        streams_to_exclude = {
            "human_resources_job_profiles"
        }
        return set(self.testable_streams).difference(streams_to_exclude)
