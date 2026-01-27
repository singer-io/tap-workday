"""
Test automatic fields (minimum selection) for Financial Management streams.

NOTE: Separate file required because MinimumSelectionTest uses class-level caching. Multiple
test classes in one file would share cached variables, causing catalog selection conflicts
where streams aren't properly selected (wrong streams/credentials). Separate files ensure isolated execution.
"""
from base import WorkdayBaseTestFinancial
from tap_tester.base_suite_tests.automatic_fields_test import MinimumSelectionTest


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
            # Streams with intermittent authentication errors
            "financial_management_customer_categories",
            "financial_management_journal_sources",
            "financial_management_ledger_account_summaries",
            "financial_management_organizations",
            "financial_management_revenue_categories",
            "financial_management_revenue_category_hierarchies",
            "financial_management_spend_category_hierarchies",
            "financial_management_supplier_categories",
        }
        return set(self.testable_streams).difference(streams_to_exclude)
