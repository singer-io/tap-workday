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
        Override the base test_replicated_records.

        REASONING:
        The base implementation filters sync 2 records down to those with
        a replication key value <= max(replication_dates_1), in order to
        exclude records that were newly created/modified between sync 1 and
        sync 2 before comparing primary keys across syncs.

        For tap-workday, the replication key (`updated_through`) is NOT the
        actual last-modified timestamp of the underlying Workday entity.
        Instead, it is stamped by the tap with (approximately) the
        wall-clock time at which that sync run executed. This means every
        record emitted during sync 1 gets `updated_through` ~= sync 1's run
        time, and every record emitted during sync 2 gets `updated_through`
        ~= sync 2's run time (which is always later, since sync 2 runs
        after sync 1 completes).

        As a result, comparing `updated_through` from sync 2 against
        `max(replication_dates_1)` always evaluates to False for every
        sync 2 record (since sync 2's timestamps are inherently larger),
        producing an empty `primary_keys_sync_2` set regardless of whether
        the same records were actually replicated in both syncs. This
        causes spurious test failures for streams that behave correctly.

        FIX:
        Since the replication key cannot be used to distinguish "record
        already present as of sync 1" from "record added after sync 1"
        for this tap, we instead compare primary keys directly, without
        filtering by replication key. This mirrors the approach already
        used in the base class for streams that don't obey start date,
        but we still enforce the record-count assertion for streams that
        do obey start date.
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
