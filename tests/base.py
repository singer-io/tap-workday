import glob
import os

from tap_tester.base_suite_tests.base_case import BaseCase


_SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tap_workday", "schemas")
ALL_STREAMS = sorted(
    os.path.splitext(os.path.basename(f))[0]
    for f in glob.glob(os.path.join(_SCHEMA_DIR, "*.json"))
)


class WorkdayBaseTest(BaseCase):
    """Base test for Workday using standard credentials (TAP_WORKDAY_*)."""

    start_date = "2025-01-01T00:00:00Z"
    stream_group = ALL_STREAMS
    testable_streams = ALL_STREAMS

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
    
        incremental_streams = {
            "human_resources_job_profiles",
            "human_resources_organizations",
            "financial_management_organizations",
            "staffing_organizations",
            "financial_management_journals",
            "financial_management_cost_centers",
            "financial_management_revenue_categories",
        }
    
        expected_metadata = {
            stream: stream_metadata.copy()
            for stream in cls.stream_group
        }

        for stream in incremental_streams:
            if stream in expected_metadata:
                expected_metadata[stream].update({
                    cls.REPLICATION_METHOD: cls.INCREMENTAL,
                    cls.REPLICATION_KEYS: {"updated_through"},
                    cls.OBEYS_START_DATE: True,
                })

        return expected_metadata

    @staticmethod
    def get_credentials():
        """Authentication information for the test account (OAuth 2.0)."""
        creds = {
            "client_id": "TAP_WORKDAY_CLIENT_ID",
            "client_secret": "TAP_WORKDAY_CLIENT_SECRET",
            "refresh_token": "TAP_WORKDAY_REFRESH_TOKEN",
            "tenant": "TAP_WORKDAY_TENANT",
            "hostname": "TAP_WORKDAY_HOSTNAME",
        }
        return {key: os.getenv(env_var) for key, env_var in creds.items()}

    def get_properties(self, original: bool = True):
        """Configuration of properties required for the tap."""
        return {
            "start_date": self.start_date
        }
