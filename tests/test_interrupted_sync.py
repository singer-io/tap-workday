from base import WorkdayBaseTest, WorkdayBaseTestFinancialManagement
from tap_tester.base_suite_tests.interrupted_sync_test import InterruptedSyncTest


class WorkdayInterruptedSyncBase(InterruptedSyncTest):
    """Test tap sets a bookmark and respects it for the next sync of a stream."""

    @staticmethod
    def name():
        return "tap_tester_workday_interrupted_sync_test"

    def streams_to_test(self):
        return self.expected_stream_names()

    def manipulate_state(self):
        return {"currently_syncing": "prospects", "bookmarks": {}}


# Test classes for different stream groups
class WorkdayInterruptedSyncTest(WorkdayInterruptedSyncBase, WorkdayBaseTest):
    """Interrupted sync test for absence/performance streams."""
    pass


class WorkdayInterruptedSyncTestFinancialManagement(WorkdayInterruptedSyncBase, WorkdayBaseTestFinancialManagement):
    """Interrupted sync test for financial/HR/staffing streams."""
    pass
