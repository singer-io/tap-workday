import glob
import os

from tap_tester.base_suite_tests.base_case import BaseCase


_SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tap_workday", "schemas")
ALL_STREAMS = sorted(
    os.path.splitext(os.path.basename(f))[0]
    for f in glob.glob(os.path.join(_SCHEMA_DIR, "*.json"))
)
FINANCIAL_STREAMS = [s for s in ALL_STREAMS if s.startswith("financial_management_")]
HR_STAFFING_ABSENCE_PERFORMANCE_STREAMS = [s for s in ALL_STREAMS if s not in FINANCIAL_STREAMS]


# Stream groups for different test configurations
# CRITICAL: These streams require DIFFERENT credentials due to Workday permissions
# Standard credentials (TAP_WORKDAY_*) can access Absence/Performance streams
# Financial Management credentials (TAP_WORKDAY_FINANCIAL_MANAGEMENT_*) can access Financial/HR/Staffing streams

ABSENCE_PERFORMANCE_STREAMS = [
    # Absence Management - requires standard credentials
    "absence_management_override_balances",
    "absence_management_absence_inputs",
    # Performance Management - requires standard credentials
    "performance_management_certification_issuers",
    "performance_management_competencies",
    "performance_management_competency_categories",
    "performance_management_degrees",
]

FINANCIAL_HR_STAFFING_STREAMS = [
    # Human Resources - requires financial management credentials
    "human_resources_job_categories",
    "human_resources_job_family_groups",
    "human_resources_job_profiles",
    "human_resources_locations",
    "human_resources_organizations",
    # Financial Management - requires financial management credentials
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
    # Staffing - requires financial management credentials
    "staffing_organizations",
]

# All streams available
ALL_STREAMS = ABSENCE_PERFORMANCE_STREAMS + FINANCIAL_HR_STAFFING_STREAMS


class WorkdayBaseTest(BaseCase):
    """Base test class for Workday tap integration tests using STANDARD credentials.
    
    This class uses standard Workday credentials (TAP_WORKDAY_*).
    During discovery, ALL streams are returned by the tap.
    However, only Absence/Performance streams are selected for syncing
    because standard credentials lack permissions for Financial/HR/Staffing streams.
    """

    start_date = "2019-01-01T00:00:00Z"
    stream_group = ALL_STREAMS  # Discovery returns all streams
    testable_streams = ABSENCE_PERFORMANCE_STREAMS  # But only these can be synced with standard creds

    @staticmethod
    def tap_name():
        """The name of the tap."""
        return "tap-workday"

    @staticmethod
    def get_type():
        return "platform.workday"

    @classmethod
    def expected_metadata(cls):
        """The expected streams and metadata about the streams."""
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
        """Authentication information for the test account."""
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
        """Configuration of properties required for the tap."""
        return_value = {"start_date": "2022-07-01T00:00:00Z"}
        if original:
            return return_value
        return_value["start_date"] = self.start_date
        return return_value


class WorkdayBaseTestFinancialManagement(WorkdayBaseTest):
    """Base test class using FINANCIAL MANAGEMENT credentials.
    
    This class uses Financial Management credentials (TAP_WORKDAY_FINANCIAL_MANAGEMENT_*).
    During discovery, ALL streams are returned by the tap.
    However, only Financial/HR/Staffing streams are selected for syncing
    because these are the streams this credential set can access.
    """

    stream_group = ALL_STREAMS  # Discovery returns all streams
    testable_streams = FINANCIAL_HR_STAFFING_STREAMS  # But only these can be synced with financial creds

    @staticmethod
    def get_credentials():
        """Authentication information for the financial management test account."""
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
