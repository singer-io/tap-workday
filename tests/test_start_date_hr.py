from tap_tester.base_suite_tests.start_date_test import StartDateTest

from base import WorkdayBaseTest


class WorkdayStartDateTest(StartDateTest, WorkdayBaseTest):
    """Instantiate start date according to the desired data set and run the
    test."""

    @staticmethod
    def name():
        return "tap_tester_workday_start_date_test"

    def streams_to_test(self):
        # Exclude heavy streams and streams with 0 records in the test environment.
        # 0-record streams cannot satisfy test_both_syncs_got_data (>0 records required).
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

    @property
    def start_date_1(self):
        return "2026-05-01T00:00:00Z"

    @property
    def start_date_2(self):
        return "2026-06-01T00:00:00Z"

    def test_replication_key_values(self):
        """
        N/A for Workday: all streams use FULL_TABLE replication with REPLICATION_KEYS: set().
        The base class asserts len(replication_key) == 1 and checks date ordering, which
        is inapplicable when there is no replication key.
        """

    def test_replicated_records(self):
        """
        Verify FULL_TABLE streams return the same records regardless of start date.
        Overrides the base class because Workday streams have REPLICATION_KEYS: set(),
        making the base assertion `assert len(replication_keys) == 1` invalid.
        Since all streams are FULL_TABLE and OBEYS_START_DATE=False, both syncs should
        return identical record sets.
        """
        for stream in self.streams_to_test():
            with self.subTest(stream=stream):
                expected_primary_keys = self.expected_primary_keys(stream)

                primary_keys_sync_1 = {
                    tuple(message['data'][pk] for pk in expected_primary_keys)
                    for message in StartDateTest.synced_messages_by_stream_1.get(
                        stream, {}).get('messages', [])
                    if message.get('action') == 'upsert'}

                primary_keys_sync_2 = {
                    tuple(message['data'][pk] for pk in expected_primary_keys)
                    for message in StartDateTest.synced_messages_by_stream_2.get(
                        stream, {}).get('messages', [])
                    if message.get('action') == 'upsert'}

                # FULL_TABLE streams return all records regardless of start date
                self.assertSetEqual(
                    primary_keys_sync_1, primary_keys_sync_2,
                    msg="FULL_TABLE stream '{}' returned different records for "
                        "different start dates".format(stream))
