from tap_tester.base_suite_tests.interrupted_sync_test import \
    InterruptedSyncTest

from base import WorkdayBaseTest


class WorkdayInterruptedSyncTest(InterruptedSyncTest, WorkdayBaseTest):
    """Test tap handles an interrupted sync correctly for FULL_TABLE streams."""

    @staticmethod
    def name():
        return "tap_tester_workday_interrupted_sync_test"

    def streams_to_test(self):
        # Exclude heavy streams and streams with 0 records in the test environment.
        # 0-record streams cannot satisfy test_all_streams_sync_records (>0 records required).
        streams_to_exclude = {
            'financial_management_journals',
            'financial_management_ledgers',
            # streams with 0 records in test environment
            'financial_management_fund_hierarchies',
            'financial_management_fund_types',
            'financial_management_funding_sources',
            'financial_management_funds',
            'financial_management_position_budgets',
            'financial_management_program_hierarchies',
            'financial_management_programs',
        }
        return self.expected_stream_names().difference(streams_to_exclude)

    def manipulate_state(self):
        # Simulate an interrupted sync using a real stream name as currently_syncing.
        # All Workday streams are FULL_TABLE so no bookmarks are written to state.
        return {"currently_syncing": "financial_management_journal_sources", "bookmarks": {}}

    def test_full_replication_streams(self):
        """
        Verify full replication streams have no bookmarks and replicate matching record counts.
        Overrides the base class implementation because Workday FULL_TABLE streams have no
        replication key (REPLICATION_KEYS: set()), making the base assertion
        `assert len(expected_replication_key) == 1` invalid.
        """
        full_streams = {s for s, m in self.expected_replication_method().items()
                        if m == self.FULL_TABLE}
        for stream in self.streams_to_test().intersection(full_streams):
            with self.subTest(stream=stream):
                first_sync_records = [
                    record['data'] for record in
                    self.first_sync_records.get(stream, {}).get('messages', [])
                    if record.get('action') == 'upsert']
                resuming_sync_records = [
                    record['data'] for record in
                    self.resuming_sync_records.get(stream, {}).get('messages', [])
                    if record.get('action') == 'upsert']

                # Verify full table streams do not save bookmarked values
                self.assertNotIn(stream, self.first_sync_state.get('bookmarks', {}).keys())
                self.assertNotIn(stream, self.resuming_sync_state.get('bookmarks', {}).keys())

                # Verify record counts match between first and resuming sync
                self.assertEqual(len(first_sync_records), len(resuming_sync_records),
                                 msg="Record count mismatch between syncs for stream: {}".format(stream))

    def test_interrupted_sync_stream_order(self):
        """
        Verify the interrupted stream syncs first and all streams_to_test are synced.
        Overrides the base class because Workday is FULL_TABLE-only with empty bookmarks,
        so the base class logic (interrupted → yet_to_sync → already_synced slicing) is
        not applicable: with empty bookmarks every stream is "yet_to_be_synced" including
        the interrupted stream, causing an off-by-one in the slice assertion.
        """
        expected_interrupted_sync = self.manipulate_state()['currently_syncing']

        # Verify the interrupted stream was resumed first
        self.assertEqual(self.resuming_sync_order[0], expected_interrupted_sync)

        # Verify all streams under test were synced in the resuming sync
        self.assertSetEqual(set(self.resuming_sync_order), self.streams_to_test())
