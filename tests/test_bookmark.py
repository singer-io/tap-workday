from tap_tester.base_suite_tests.bookmark_test import BookmarkTest

from base import WorkdayBaseTest


class WorkdayBookMarkTest(BookmarkTest, WorkdayBaseTest):
    """Test tap sets a bookmark and respects it for the next sync of a
    stream."""

    bookmark_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    initial_bookmarks = {
        "bookmarks": {
            "human_resources_job_profiles": {
                "updated_through": "2025-01-01T00:00:00Z"
            },
            "human_resources_organizations": {
                "updated_through": "2025-01-01T00:00:00Z"
            },
            "financial_management_journals": {
                "updated_through": "2025-01-01T00:00:00Z"
            },
            "financial_management_organizations": {
                "updated_through": "2025-01-01T00:00:00Z"
            },
            "staffing_organizations": {
                "updated_through": "2025-01-01T00:00:00Z"
            }
        }
    }


    @staticmethod
    def name():
        return "tap_tester_workday_bookmark_test"

    def streams_to_test(self):
        streams_to_include = {
            "human_resources_job_profiles",
            "human_resources_organizations",
            "financial_management_journals",
            "financial_management_organizations",
            "staffing_organizations",
        }
        return self.expected_stream_names().intersection(streams_to_include)
