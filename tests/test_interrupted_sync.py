from tap_tester.base_suite_tests.interrupted_sync_test import \
    InterruptedSyncTest

from base import WorkdayBaseTest


class WorkdayInterruptedSyncTest(InterruptedSyncTest, WorkdayBaseTest):
    """Test tap sets a bookmark and respects it for the next sync of a
    stream."""

    @staticmethod
    def name():
        return "tap_tester_workday_interrupted_sync_test"

    def get_properties(self, original: bool = True):
        properties = super().get_properties(original)
        properties["start_date"] = "2019-01-01T00:00:00Z"
        return properties

    def streams_to_test(self):
        streams_to_exclude = {
            # full table 
            "absence_management_absence_inputs",
            "absence_management_override_balances",
            "financial_management_customer_categories",
            "financial_management_fund_hierarchies",
            "financial_management_fund_types",
            "financial_management_funding_sources",
            "financial_management_funds",
            "financial_management_journal_sources",
            "financial_management_ledger_account_summaries",
            "financial_management_ledgers",
            "financial_management_position_budgets",
            "financial_management_program_hierarchies",
            "financial_management_programs",
            "financial_management_revenue_category_hierarchies",
            "financial_management_spend_category_hierarchies",
            "financial_management_supplier_categories",
            "human_resources_job_categories",
            "human_resources_job_family_groups",
            "human_resources_locations",
            "performance_management_certification_issuers",
            "performance_management_competencies",
            "performance_management_competency_categories",
            "performance_management_degrees"
            # No data available for streams
            "financial_management_cost_centers",
            "financial_management_revenue_categories"
        }
        return self.expected_stream_names().difference(streams_to_exclude)


    def manipulate_state(self):
        bookmark_value = "2020-01-01T00:00:00Z"
        return {
        "currently_syncing": "staffing_organizations",
        "bookmarks":{
            "human_resources_job_profiles": {
                "updated_through": bookmark_value
            },
            "human_resources_organizations": {
                "updated_through": bookmark_value
            },
            "financial_management_journals": {
                "updated_through": bookmark_value
            },
            "financial_management_organizations": {
                "updated_through": bookmark_value
            },
            "staffing_organizations": {
                "updated_through": bookmark_value
            }
        }
        }
