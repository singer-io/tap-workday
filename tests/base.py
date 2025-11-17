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


class WorkdayBaseTest(BaseCase):
    """Setup expectations for test sub classes.

    Metadata describing streams. A bunch of shared methods that are used
    in tap-tester tests. Shared tap-specific methods (as needed).
    """

    start_date = "2019-01-01T00:00:00Z"

    @staticmethod
    def tap_name():
        """The name of the tap."""
        return "tap-workday"

    @staticmethod
    def get_type():
        """The name of the tap."""
        return "platform.workday"

    @classmethod
    def expected_stream_names(cls):
        """The expected stream names for the tap."""
        # Import here to avoid circular imports
        from tap_workday.streams import STREAMS
        return set(STREAMS.keys())

    @classmethod
    def expected_metadata(cls):
        """The expected streams and metadata about the streams."""
        return {
            "financial_management_ledgers": {
                cls.PRIMARY_KEYS: {"key_value"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "get_organizations": {
                cls.PRIMARY_KEYS: {"Organization_ID.value"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            }
        }

    @staticmethod
    def get_credentials():
        """Authentication information for the test account."""
        credentials_dict = {}
        creds = {
            "client_id": "TAP_WORKDAY_CLIENT_ID",
            "client_secret": "TAP_WORKDAY_CLIENT_SECRET",
            "refresh_token": "TAP_WORKDAY_REFRESH_TOKEN",
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
