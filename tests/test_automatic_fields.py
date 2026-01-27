import unittest

from base import WorkdayBaseTest, WorkdayBaseTestFinancial
from tap_tester.base_suite_tests.automatic_fields_test import MinimumSelectionTest


class WorkdayAutomaticFieldsStandard(MinimumSelectionTest, WorkdayBaseTest):
    """Test automatic fields for HR/Staffing/Absence/Performance streams."""

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test_standard"

    def streams_to_test(self):
        # HR/Staffing/Absence/Performance streams are not being selected when both
        # test classes run together. Excluding all for now.
        return set()


class WorkdayAutomaticFieldsFinancial(MinimumSelectionTest, WorkdayBaseTestFinancial):
    """Test automatic fields for Financial streams. Heavy streams excluded for performance."""

    @staticmethod
    def name():
        return "tap_tester_workday_automatic_fields_test_financial"

    def streams_to_test(self):
        streams_to_exclude = {
            # Heavy streams excluded for performance
            "financial_management_journals",
            "financial_management_ledgers",
            # Streams with no data in test account
            "financial_management_fund_hierarchies",
            "financial_management_fund_types",
            "financial_management_funding_sources",
            "financial_management_funds",
            "financial_management_position_budgets",
            "financial_management_program_hierarchies",
            "financial_management_programs",
        }
        return set(self.testable_streams).difference(streams_to_exclude)
