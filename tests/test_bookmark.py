from tap_tester.base_suite_tests.bookmark_test import BookmarkTest

from base import WorkdayBaseTest
from datetime import datetime, timezone


class WorkdayBookMarkTest(BookmarkTest, WorkdayBaseTest):
    """Test tap sets a bookmark and respects it for the next sync of a
    stream."""

    @classmethod
    @property
    def bookmark_format(cls):
        return "%Y-%m-%dT%H:%M:%SZ"

    @staticmethod
    def parse_date(date_value):
        """
        Override base parse_date to avoid the local-timezone conversion bug
        in BaseCase.parse_date (astimezone() on naive datetimes assumes
        local system time, causing an incorrect offset). Workday timestamps
        are always UTC ('Z' suffix), so we attach UTC directly.
        """
        date_formats = (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
        )
        for date_format in date_formats:
            try:
                date_stripped = datetime.strptime(date_value, date_format)
                if date_stripped.tzinfo is None:
                    date_stripped = date_stripped.replace(tzinfo=timezone.utc)
                return date_stripped
            except ValueError:
                continue
        raise NotImplementedError(
            f"Tests do not account for dates of this format: {date_value}"
        )

    @staticmethod
    def convert_to_utc(date_str):
        """Override to fix broken `self` reference and use the correct parse_date."""
        date_object = WorkdayBookMarkTest.parse_date(date_str)
        date_object_utc = date_object.astimezone(tz=timezone.utc)
        return datetime.strftime(date_object_utc, "%Y-%m-%dT%H:%M:%SZ")

    initial_bookmark_value = "2019-01-01T00:00:00Z"
    initial_bookmarks = {
        "bookmarks": {
            "human_resources_job_profiles": {
                "updated_through": initial_bookmark_value
            },
            "human_resources_organizations": {
                "updated_through": initial_bookmark_value
            },
            "financial_management_journals": {
                "updated_through": initial_bookmark_value
            },
            "financial_management_organizations": {
                "updated_through": initial_bookmark_value
            },
            "staffing_organizations": {
                "updated_through": initial_bookmark_value
            }
        }
    }


    @staticmethod
    def name():
        return "tap_tester_workday_bookmark_test"

    def streams_to_test(self):
        streams_to_include = {
            "financial_management_organizations",
            "human_resources_job_profiles",
            "human_resources_organizations",
            "staffing_organizations",
        }
        return self.expected_stream_names().intersection(streams_to_include)

    def calculate_new_bookmarks(self):
        """Calculates new bookmarks by looking through sync 1 data to determine
        a bookmark that will sync 2 records in sync 2 (plus any necessary look
        back data)"""
        new_bookmark_value = "2020-01-01T00:00:00Z"
        new_bookmarks = {
            "human_resources_job_profiles": {
                "updated_through": new_bookmark_value
            },
            "human_resources_organizations": {
                "updated_through": new_bookmark_value
            },
            "financial_management_journals": {
                "updated_through": new_bookmark_value
            },
            "financial_management_organizations": {
                "updated_through": new_bookmark_value
            },
            "staffing_organizations": {
                "updated_through": new_bookmark_value
            }
        }
        return new_bookmarks
