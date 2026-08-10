from tap_tester.base_suite_tests.pagination_test import PaginationTest

from base import WorkdayBaseTest


class WorkdayPaginationTest(PaginationTest, WorkdayBaseTest):
    """
    Ensure tap can replicate multiple pages of data for streams that use pagination.
    """

    @staticmethod
    def name():
        return "tap_tester_workday_pagination_test"

    def streams_to_test(self):        
        streams_to_exclude = {
            'financial_management_journals',
            'financial_management_ledgers',
            # streams with fewer than 100 records
            'absence_management_absence_inputs',
            'absence_management_override_balances',
            'financial_management_cost_centers',
            'financial_management_customer_categories',
            'financial_management_fund_hierarchies',
            'financial_management_fund_types',
            'financial_management_funding_sources',
            'financial_management_funds',
            'financial_management_position_budgets',
            'financial_management_program_hierarchies',
            'financial_management_programs',
            'financial_management_revenue_categories',
            'financial_management_revenue_category_hierarchies',
            'financial_management_spend_category_hierarchies',
            'financial_management_supplier_categories',
            'human_resources_job_categories',
            'human_resources_job_family_groups',
            'performance_management_certification_issuers',
            'performance_management_competencies',
            'performance_management_competency_categories',
            'performance_management_degrees',
        }
        return self.expected_stream_names().difference(streams_to_exclude)
