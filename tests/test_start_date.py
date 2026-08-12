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
        Override the base test_replicated_records because tap-workday's
        replication key (updated_through) is the sync clock time, not a
        Workday entity timestamp, which breaks the base class filter.

        WHAT updated_through ACTUALLY IS
        ----------------------------------
        The tap stamps every emitted record with the wall-clock time of the
        API request, not when the Workday entity was last modified.

        Example — the same job profile in two different sync runs:
          key_value = '15baf9003ea943a9a62332bb48f5386c'
          sync run at 10:39 AM → updated_through = '2026-08-11T10:39:06Z'
          sync run at 11:01 AM → updated_through = '2026-08-11T11:01:08Z'
        Same Workday record, different updated_through every run.

        WHY THE BASE CLASS FAILS
        -------------------------
        The base class assumes updated_through is a data timestamp and
        filters sync-2 records to those where:
            updated_through <= max(sync-1 updated_through values)
        to exclude records created between the two syncs.

        With tap-workday that filter always produces an empty set:
          sync-1 (start=2019) runs at T1 → all records get updated_through ≈ T1
          sync-2 (start=2020) runs at T2 → all records get updated_through ≈ T2
          T2 > T1 (sync-2 runs after sync-1 finishes)
          filter: T2 <= T1 → False for every record → primary_keys_sync_2 = {}

        The base then asserts:
            assertSetEqual({sync-1 keys filtered by >= 2020-01-01}, {})
        sync-1 keys pass the filter because their updated_through (T1, e.g.
        '2026-08-11T10:00Z') is greater than '2020-01-01', so
        primary_keys_sync_1 = all 14 keys. The assertion becomes:
            assertSetEqual({14 keys}, {}) → FAILS spuriously.

        WHAT THIS OVERRIDE DOES INSTEAD
        ---------------------------------
        Compare primary keys without filtering by updated_through:
          - assertGreaterEqual(count_sync_1, count_sync_2)
            e.g. 14 (start=2019) >= 10 (start=2020) ✓
          - assert all sync-2 keys are a subset of sync-1 keys
            e.g. the 10 records from the 2020 sync are all present in
            the 14 records from the 2019 sync ✓
        This correctly verifies that the earlier start date returns more
        data, without relying on updated_through as a data timestamp.
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
