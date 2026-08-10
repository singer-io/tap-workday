"""
Test automatic fields (minimum selection) for HR/Staffing/Absence/Performance streams.

NOTE: Separate file required because MinimumSelectionTest uses class-level caching. Multiple
test classes in one file would share cached variables, causing catalog selection conflicts
where streams aren't properly selected (wrong streams/credentials). Separate files ensure isolated execution.
"""
from base import WorkdayBaseTest
from tap_tester.base_suite_tests.automatic_fields_test import MinimumSelectionTest


class WorkdayAutomaticFieldsStandard(MinimumSelectionTest, WorkdayBaseTest):
    """Test automatic fields for HR/Staffing/Absence/Performance streams."""

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test_standard"

    def streams_to_test(self):
        streams_to_exclude = {
            "human_resources_job_profiles"
        }
        return set(self.testable_streams).difference(streams_to_exclude)
