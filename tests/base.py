import os
from tap_tester.base_suite_tests.base_case import BaseCase


# Standard credentials: HR/Staffing/Absence/Performance streams
# Financial credentials: Financial streams only

HR_STAFFING_ABSENCE_PERFORMANCE_STREAMS = [
    # Human Resources
    "human_resources_job_categories",
    "human_resources_job_family_groups",
    "human_resources_job_profiles",
    "human_resources_locations",
    "human_resources_organizations",
    # Staffing
    "staffing_organizations",
    # Absence Management
    "absence_management_override_balances",
    "absence_management_absence_inputs",
    # Performance Management
    "performance_management_certification_issuers",
    "performance_management_competencies",
    "performance_management_competency_categories",
    "performance_management_degrees",
]

FINANCIAL_STREAMS = [
    # Financial Management
    "financial_management_cost_centers",
    "financial_management_customer_categories",
    "financial_management_fund_hierarchies",
    "financial_management_fund_types",
    "financial_management_funding_sources",
    "financial_management_funds",
    "financial_management_journal_sources",
    "financial_management_journals",
    "financial_management_ledger_account_summaries",
    "financial_management_ledgers",
    "financial_management_organizations",
    "financial_management_position_budgets",
    "financial_management_program_hierarchies",
    "financial_management_programs",
    "financial_management_revenue_categories",
    "financial_management_revenue_category_hierarchies",
    "financial_management_spend_category_hierarchies",
    "financial_management_supplier_categories",
]

ALL_STREAMS = HR_STAFFING_ABSENCE_PERFORMANCE_STREAMS + FINANCIAL_STREAMS


class WorkdayBaseTest(BaseCase):
    """Base test for Workday using standard credentials (TAP_WORKDAY_*)."""

    start_date = "2020-01-01T00:00:00Z"
    stream_group = ALL_STREAMS
    testable_streams = HR_STAFFING_ABSENCE_PERFORMANCE_STREAMS

    @staticmethod
    def tap_name():
        return "tap-workday"

    @staticmethod
    def get_type():
        return "platform.workday"

    @classmethod
    def expected_metadata(cls):
        stream_metadata = {
            cls.PRIMARY_KEYS: {"key_value"},
            cls.REPLICATION_METHOD: cls.FULL_TABLE,
            cls.REPLICATION_KEYS: set(),
            cls.OBEYS_START_DATE: False,
            cls.API_LIMIT: 100,
        }
        return {stream: stream_metadata.copy() for stream in cls.stream_group}

    @staticmethod
    def get_credentials():
        credentials_dict = {}
        creds = {
            "username": "TAP_WORKDAY_USERNAME",
            "password": "TAP_WORKDAY_PASSWORD",
            "tenant": "TAP_WORKDAY_TENANT",
            "hostname": "TAP_WORKDAY_HOSTNAME",
        }
        for cred in creds:
            credentials_dict[cred] = os.getenv(creds[cred])
        return credentials_dict

    def get_properties(self, original: bool = True):
        return_value = {"start_date": "2022-07-01T00:00:00Z"}
        if original:
            return return_value
        return_value["start_date"] = self.start_date
        return return_value


class WorkdayBaseTestFinancial(WorkdayBaseTest):
    """Base test using financial credentials (TAP_WORKDAY_FINANCIAL_MANAGEMENT_*)."""

    stream_group = ALL_STREAMS
    testable_streams = FINANCIAL_STREAMS

    @staticmethod
    def get_credentials():
        credentials_dict = {}
        creds = {
            "username": "TAP_WORKDAY_FINANCIAL_MANAGEMENT_USERNAME",
            "password": "TAP_WORKDAY_FINANCIAL_MANAGEMENT_PASSWORD",
            "tenant": "TAP_WORKDAY_FINANCIAL_MANAGEMENT_TENANT",
            "hostname": "TAP_WORKDAY_FINANCIAL_MANAGEMENT_HOSTNAME",
        }
        for cred in creds:
            credentials_dict[cred] = os.getenv(creds[cred])
        return credentials_dict
