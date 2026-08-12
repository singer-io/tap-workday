from tap_tester.base_suite_tests.start_date_test import StartDateTest

from base import WorkdayBaseTest


class WorkdayStartDateTest(StartDateTest, WorkdayBaseTest):
    """Instantiate start date according to the desired data set and run the
    test."""

    @staticmethod
    def name():
        return "tap_tester_workday_start_date_test"

    def streams_to_test(self):
        streams_to_exclude = {
            # full_tables
            "absence_management_absence_inputs",
            "absence_management_override_balances",
            "financial_management_customer_categories",
            "financial_management_fund_hierarchies",
            "financial_management_fund_types",
            "financial_management_funding_sources",
            "financial_management_funds",
            "financial_management_journal_sources",
            "financial_management_ledger_account_summaries",
            "financial_management_ledgers",
            "financial_management_position_budgets",
            "financial_management_program_hierarchies",
            "financial_management_programs",
            "financial_management_revenue_category_hierarchies",
            "financial_management_spend_category_hierarchies",
            "financial_management_supplier_categories",
            "human_resources_job_categories",
            "human_resources_job_family_groups",
            "human_resources_locations",
            "performance_management_certification_issuers",
            "performance_management_competencies",
            "performance_management_competency_categories",
            "performance_management_degrees",
            # Streams with no data in test account
            "financial_management_cost_centers",
            "financial_management_revenue_categories",
        }
        return set(self.testable_streams).difference(streams_to_exclude)

    @property
    def start_date_1(self):
        return "2019-01-01T00:00:00Z"

    @property
    def start_date_2(self):
        return "2020-01-01T00:00:00Z"

    def test_replicated_records(self):
        """
        Override the base test because tap-workday uses updated_through as
        the time this sync fetched the record, not the time the Workday
        record was last modified.

        Example: the same job profile can appear in two runs with the same
        primary key but different updated_through values:

            key_value='15baf9003ea943a9a62332bb48f5386c'
            sync-1 -> updated_through='2026-08-11T10:39:06Z'
            sync-2 -> updated_through='2026-08-11T11:01:08Z'

        The base test assumes updated_through is a real last_modified field
        and tries to remove records that may have appeared after sync-1.

        Visual example of what the base test expects:

            sync-1 finishes at 11:01
            sync-2 finishes at 11:20

            Ideal records if updated_through were last_modified:
                sync-1: [A@2020-02-10, B@2020-05-01, C@2020-09-15, D@2021-01-10]
                sync-2: [B@2020-05-01, C@2020-09-15, D@2021-01-10, E@2026-08-11T11:15]

            Base filter:
                keep sync-2 records where updated_through <= sync-1 finish boundary

            Result in that ideal world:
                keep [B, C, D]
                drop [E]

        That logic is fine only if updated_through means "when the business
        record changed".

        What tap-workday really outputs:

            sync-1 records fetched around 11:01:
                [A@11:01:08, B@11:01:08, C@11:01:08, D@11:01:08]

            sync-2 records fetched around 11:20:
                [B@11:20:15, C@11:20:15, D@11:20:15]

            Base filter still says:
                keep records where updated_through <= 11:01:08

            Actual result:
                B -> drop
                C -> drop
                D -> drop
                filtered sync-2 = []

            So the base comparison becomes:
                expected from sync-1: [B, C, D]
                filtered sync-2: []

        The test fails even though the tap returned the correct records.
        The failure comes from the wrong assumption about what
        updated_through means.

        This override avoids that bad filter. Instead it checks the real
        behavior directly:

            - sync-1 has at least as many records as sync-2
            - every primary key from sync-2 is also present in sync-1

        Example:
            sync-1 keys = [A, B, C, D]
            sync-2 keys = [B, C, D]

        That is the correct start-date behavior for this tap.
        """
        for stream in self.streams_to_test():
            with self.subTest(stream=stream):

                expected_primary_keys = self.expected_primary_keys(stream)
                stream_obeys_start_date = self.expected_start_date_behavior(stream)

                record_count_sync_1 = self.record_count_by_stream_1.get(stream, 0)
                record_count_sync_2 = self.record_count_by_stream_2.get(stream, 0)

                primary_keys_sync_1 = {
                    tuple(message['data'][expected_pk] for expected_pk in expected_primary_keys)
                    for message in self.synced_messages_by_stream_1.get(
                        stream, {}).get('messages', [])
                    if message.get('action') == 'upsert'}

                primary_keys_sync_2 = {
                    tuple(message['data'][expected_pk] for expected_pk in expected_primary_keys)
                    for message in self.synced_messages_by_stream_2.get(
                        stream, {}).get('messages', [])
                    if message.get('action') == 'upsert'}

                if stream_obeys_start_date:
                    # Verify sync 1 (earlier start date) replicated at least as many
                    # records as sync 2 (later start date).
                    self.assertGreaterEqual(record_count_sync_1, record_count_sync_2)

                    # Verify every record replicated in sync 2 was also replicated
                    # in sync 1 (sync 1 has a strictly earlier or equal start date,
                    # so it is a superset).
                    self.assertTrue(
                        primary_keys_sync_2.issubset(primary_keys_sync_1),
                        msg=f"Stream {stream}: records in sync 2 were not all "
                            f"present in sync 1.\n"
                            f"Missing: {primary_keys_sync_2 - primary_keys_sync_1}")
                else:
                    # Verify by primary key the same records are replicated in
                    # the 1st and 2nd syncs.
                    self.assertSetEqual(primary_keys_sync_1, primary_keys_sync_2)
