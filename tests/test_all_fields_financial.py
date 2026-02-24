"""
Test all fields for Financial Management streams.

NOTE: Separate file required because AllFieldsTest uses class-level caching. Multiple test
classes in one file would share cached variables, causing the second class to incorrectly
reuse the first class's data (wrong streams/credentials). Separate files ensure isolated execution.
"""
from base import WorkdayBaseTestFinancial
from tap_tester.base_suite_tests.all_fields_test import AllFieldsTest


class WorkdayAllFieldsFinancial(AllFieldsTest, WorkdayBaseTestFinancial):
    """Test all fields for Financial streams. Heavy streams excluded for performance."""

    @staticmethod
    def name():
        return "tap_tester_workday_all_fields_test_financial"

    def streams_to_test(self):
        streams_to_exclude = {
            # Heavy streams excluded - cause CircleCI timeouts (context deadline exceeded >10m) due to large data volumes
            "financial_management_journals",
            "financial_management_ledgers",
            # Streams with no data in test account
            "financial_management_fund_hierarchies",
            "financial_management_fund_types",
            "financial_management_funding_sources",
            "financial_management_funds",
            "financial_management_position_budgets",
            "financial_management_program_hierarchies",
            "financial_management_programs"
        }
        return set(self.testable_streams).difference(streams_to_exclude)
