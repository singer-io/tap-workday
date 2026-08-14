"""Test all fields for Workday streams."""
from base import WorkdayBaseTest
from tap_tester.base_suite_tests.all_fields_test import AllFieldsTest


class WorkdayAllFields(AllFieldsTest, WorkdayBaseTest):
    """Test all fields for supported streams, excluding known heavy/empty streams."""

    @staticmethod
    def name():
        return "tap_tester_workday_all_fields_test"

    def get_properties(self, original: bool = True):
        properties = super().get_properties(original)
        properties["start_date"] = "2020-01-01T00:00:00Z"
        return properties

    def streams_to_test(self):
        streams_to_exclude = {
            # Streams with no data in test account
            "financial_management_fund_hierarchies",
            "financial_management_fund_types",
            "financial_management_funding_sources",
            "financial_management_funds",
            "financial_management_position_budgets",
            "financial_management_program_hierarchies",
            "financial_management_programs",
            "financial_management_cost_centers",
            "financial_management_revenue_categories",
        }
        return set(self.testable_streams).difference(streams_to_exclude)
