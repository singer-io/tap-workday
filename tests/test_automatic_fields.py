import unittest

from base import WorkdayBaseTest, WorkdayBaseTestFinancial
from tap_tester.base_suite_tests.automatic_fields_test import MinimumSelectionTest


class WorkdayAutomaticFieldsStandard(MinimumSelectionTest, WorkdayBaseTest):
    """Test automatic fields for HR/Staffing/Absence/Performance streams."""

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test_standard"

    def streams_to_test(self):
        return set(self.testable_streams)


@unittest.skip("Skipped: Financial credentials failing with authentication errors")
class WorkdayAutomaticFieldsFinancial(MinimumSelectionTest, WorkdayBaseTestFinancial):
    """Test automatic fields for Financial streams. Heavy streams excluded for performance."""

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test_financial"

    def streams_to_test(self):
        streams_to_exclude = {
            "financial_management_journals",
            "financial_management_ledgers",
        }
        return set(self.testable_streams).difference(streams_to_exclude)
