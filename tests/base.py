import os
import sys

# Ensure tap_workday is importable even when not installed as a package
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from tap_tester.base_suite_tests.base_case import BaseCase

from tap_workday.streams import STREAMS

ALL_STREAMS = sorted(STREAMS.keys())
FINANCIAL_STREAMS = [s for s in ALL_STREAMS if s.startswith("financial_management_")]
HR_STAFFING_ABSENCE_PERFORMANCE_STREAMS = [s for s in ALL_STREAMS if s not in FINANCIAL_STREAMS]


class WorkdayBaseTest(BaseCase):
    """Base test for Workday using standard credentials (TAP_WORKDAY_*)."""

    start_date = "2020-01-01T00:00:00Z"
    stream_group = ALL_STREAMS
    testable_streams = HR_STAFFING_ABSENCE_PERFORMANCE_STREAMS

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


class WorkdayBaseTestFinancial(WorkdayBaseTest):
    """Base test using financial credentials (TAP_WORKDAY_FINANCIAL_MANAGEMENT_*)."""

    stream_group = ALL_STREAMS
    testable_streams = FINANCIAL_STREAMS

    @staticmethod
    def get_credentials():
        """Authentication information for the test account."""
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
