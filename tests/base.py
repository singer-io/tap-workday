import copy
import os
import unittest
from datetime import datetime as dt
from datetime import timedelta

import dateutil.parser
import pytz
from tap_tester import connections, menagerie, runner
from tap_tester.base_suite_tests.base_case import BaseCase
from tap_tester.logger import LOGGER


# Stream groups for different test configurations
ABSENCE_PERFORMANCE_STREAMS = [
    # Absence Management
    "absence_management_override_balances",
    "absence_management_absence_inputs",
    # Performance Management
    "performance_management_certification_issuers",
    "performance_management_competencies",
    "performance_management_competency_categories",
    "performance_management_degrees",
]

FINANCIAL_HR_STAFFING_STREAMS = [
    # Human Resources
    "human_resources_job_categories",
    "human_resources_job_family_groups",
    "human_resources_job_profiles",
    "human_resources_locations",
    "human_resources_organizations",
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
    # Staffing
    "staffing_organizations",
]


class WorkdayBaseTest(BaseCase):
    """Base test class for Workday tap integration tests.
    
    Supports different stream groups via the stream_group class attribute.
    Override stream_group in subclasses to use different sets of streams.
    """

    start_date = "2019-01-01T00:00:00Z"
    stream_group = ABSENCE_PERFORMANCE_STREAMS  # Default stream group

    @staticmethod
    def tap_name():
        """The name of the tap."""
        return "tap-workday"

    @staticmethod
    def get_type():
        """The name of the tap."""
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
        return {
            "username": os.getenv("TAP_WORKDAY_USERNAME"),
            "password": os.getenv("TAP_WORKDAY_PASSWORD"),
            "tenant": os.getenv("TAP_WORKDAY_TENANT"),
            "hostname": os.getenv("TAP_WORKDAY_HOSTNAME"),
        }

    def get_properties(self, original: bool = True):
        """Configuration of properties required for the tap."""
        return_value = {"start_date": "2022-07-01T00:00:00Z"}
        if original:
            return return_value

        return_value["start_date"] = self.start_date
        return return_value


class WorkdayBaseTestFinancialManagement(WorkdayBaseTest):
    """Base test class for financial management, HR, and staffing streams."""
    stream_group = FINANCIAL_HR_STAFFING_STREAMS

    @staticmethod
    def get_credentials():
        """Authentication information for the financial management test account."""
        return {
            "username": os.getenv("TAP_WORKDAY_FINANCIAL_MANAGEMENT_USERNAME"),
            "password": os.getenv("TAP_WORKDAY_FINANCIAL_MANAGEMENT_PASSWORD"),
            "tenant": os.getenv("TAP_WORKDAY_FINANCIAL_MANAGEMENT_TENANT"),
            "hostname": os.getenv("TAP_WORKDAY_FINANCIAL_MANAGEMENT_HOSTNAME"),
        }
