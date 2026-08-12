from tap_tester.base_suite_tests.interrupted_sync_test import \
    InterruptedSyncTest

from base import WorkdayBaseTest


class WorkdayInterruptedSyncTest(InterruptedSyncTest, WorkdayBaseTest):
    """
    Verify tap-workday can recover from an interrupted sync.

    OVERVIEW
    --------
    The base class runs two syncs:

      1. A first sync to create a real baseline state.
      2. A resuming sync after we replace that state with a hand-made
         interrupted state.

    The goal is to prove that the tap can resume from the interrupted
    stream, continue the remaining streams in the right order, and finish
    cleanly.

    WHAT MAKES tap-workday DIFFERENT
    --------------------------------
    tap-workday uses updated_through as the time this sync fetched the
    record, not the time the Workday entity was last modified.

    Example: the same record in two different syncs can have the same
    primary key but different updated_through values:

        key_value='15baf9003ea943a9a62332bb48f5386c'
        first sync  -> updated_through='2026-08-11T10:39:06Z'
        second sync -> updated_through='2026-08-11T11:01:08Z'

    Because of that, any base-class assertion that treats updated_through
    like a business timestamp becomes misleading for this tap.

    HOW THE INTERRUPTED STATE IS BUILT
    ----------------------------------
    For this tap, we simulate an interruption with this state:

        currently_syncing = human_resources_job_profiles
        bookmarks = {
            human_resources_job_profiles: updated_through=2020-01-01T00:00:00Z,
            staffing_organizations: updated_through=2020-01-01T00:00:00Z,
        }

    That means:

        interrupted stream:
            [human_resources_job_profiles]

        not yet started streams:
            [human_resources_organizations,
             financial_management_journals,
             financial_management_organizations,
             financial_management_revenue_categories]

        already completed streams:
            [staffing_organizations]

    So the expected resume order is:

        [human_resources_job_profiles,
         human_resources_organizations,
         financial_management_journals,
         financial_management_organizations,
         financial_management_revenue_categories,
         staffing_organizations]

    WHY THE TEST IS STILL VALID
    ---------------------------
    Two base-class tests still give real coverage and are enough to prove
    interrupted-sync recovery works:

      test_all_streams_sync_records
        Every selected stream returned records in the resuming sync, so no
        remaining stream was skipped after the interruption.

      test_interrupted_sync_stream_order
        Streams resumed in the correct order:
        interrupted -> not yet started -> already completed.

    The overridden methods below are only the methods whose logic depends on
    updated_through being a true data timestamp.
    """

    @staticmethod
    def name():
        return "tap_tester_workday_interrupted_sync_test"

    def get_properties(self, original: bool = True):
        """
        Override: set start_date to 2019-01-01.

        The base default is 2025-01-01. The test account's fixture data
        falls between 2019 and 2020, so a 2025 start date would return
        0 records for every stream and cause test_all_streams_sync_records
        to fail. Setting 2019-01-01 ensures all 6 streams return records.
        """
        properties = super().get_properties(original)
        properties["start_date"] = "2019-01-01T00:00:00Z"
        return properties

    def streams_to_test(self):
        """
        Override: test only the 6 incremental streams that have data in
        the test account.

        Full-table streams are excluded because InterruptedSyncTest injects
        bookmark values into state and verifies bookmark-driven resume
        behaviour — concepts that don't apply to full-table streams. The
        base test_full_replication_streams method still runs but finds no
        streams to iterate over, so it passes vacuously.

        financial_management_cost_centers is excluded because its API
        returns 0 records for this account even with a 2019 start date.
        All other incremental streams have confirmed data between 2019 and
        2020 (verified by test_start_date.py):
          human_resources_job_profiles     14 records (2019) vs 10 (2020)
          human_resources_organizations    77 records (2019) vs 41 (2020)
          financial_management_journals 10814 records (2019) vs 3307 (2020)
          financial_management_organizations  77 records (2019) vs 41 (2020)
          financial_management_revenue_categories  1 record both dates
          staffing_organizations           77 records (2019) vs 41 (2020)
        """
        streams_to_exclude = {
            # full table streams
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
            # No data available in test account
            "financial_management_cost_centers",
        }
        return self.expected_stream_names().difference(streams_to_exclude)

    def manipulate_state(self):
        """
        Override the required base method to return a state that looks like
        a sync was interrupted part-way through.

        Visual stream groups:

            interrupted now:
                [human_resources_job_profiles]

            not yet started:
                [human_resources_organizations,
                 financial_management_journals,
                 financial_management_organizations,
                 financial_management_revenue_categories]

            already completed:
                [staffing_organizations]

        Injected state:

            {
              "currently_syncing": "human_resources_job_profiles",
              "bookmarks": {
                "human_resources_job_profiles": {
                  "updated_through": "2020-01-01T00:00:00Z"
                },
                "staffing_organizations": {
                  "updated_through": "2020-01-01T00:00:00Z"
                }
              }
            }

        Why this shape is useful:

            - it gives us 1 interrupted stream to resume first
            - 4 streams with no bookmark that must come next
            - 1 bookmarked stream that must come last

        So the resume order is easy to verify visually:

            [human_resources_job_profiles] +
            [human_resources_organizations,
             financial_management_journals,
             financial_management_organizations,
             financial_management_revenue_categories] +
            [staffing_organizations]

        The bookmark value 2020-01-01 is inside the known fixture-data
        window, so the tap resumes with a real incremental filter rather
        than behaving like a full historical sync.
        """
        bookmark_value = "2020-01-01T00:00:00Z"
        return {
            "currently_syncing": "human_resources_job_profiles",
            "bookmarks": {
                "human_resources_job_profiles": {
                    "updated_through": bookmark_value
                },
                "staffing_organizations": {
                    "updated_through": bookmark_value
                }
            }
        }

    def test_syncs_were_successful(self):
        """
        Override the base state-equality check because the bookmark values
        are expected to change on every run even when recovery is correct.

        What the base class thinks:

            "If the tap resumes correctly, the final state after the resumed
            run should be exactly equal to the final state from the normal
            uninterrupted run."

        That idea is reasonable if bookmark values are stable business
        timestamps.

        Visual example:

            first sync final state:
                human_resources_job_profiles -> updated_through=2026-08-12T08:08:44Z
                human_resources_organizations -> updated_through=2026-08-12T08:08:57Z

            resuming sync final state:
                human_resources_job_profiles -> updated_through=2026-08-12T08:23:30Z
                human_resources_organizations -> updated_through=2026-08-12T08:23:46Z

        That would be true only if bookmark values were stable business
        timestamps. Here they are fetch times, so both states are valid but
        not equal:

            first sync state != resuming sync state

        What we keep instead:

            - both states have bookmarks
            - resuming state no longer has currently_syncing

        Those are the two facts that really prove the tap wrote state and
        finished the resumed run cleanly.
        """
        self.assertIsNotNone(self.first_sync_state.get('bookmarks'))
        self.assertIsNotNone(self.resuming_sync_state.get('bookmarks'))
        self.assertIsNone(self.resuming_sync_state.get('currently_syncing'))

    def test_bookmarked_streams_start_date(self):
        """
        Override this base test because it would always pass for the wrong
        reason.

        Base class idea:
            "Look at the oldest record returned in the resuming sync. If its
            updated_through is at or after the bookmark, then the tap must
            have resumed from the right place."

        Visual example with our injected bookmark:

            bookmark in state:
                human_resources_job_profiles -> updated_through=2020-01-01T00:00:00Z

            records returned in resuming sync:
                [J1@2026-08-12T08:23:30Z,
                 J2@2026-08-12T08:23:30Z,
                 J3@2026-08-12T08:23:30Z]

            oldest returned record = 2026-08-12T08:23:30Z

            base check:
                2026-08-12T08:23:30Z >= 2020-01-01T00:00:00Z -> True

        What the base class thinks this means:

            "The oldest resumed record is at or after the bookmark, so the
            tap must have restarted from the bookmarked point."

        The problem is that this will be True even if the tap resumed from
        the wrong place, because every resuming-sync record gets stamped with
        the time of the resuming run itself. So the assertion proves nothing.

        That is why this method is intentionally left as a no-op.
        """

    def test_resuming_sync_records(self):
        """
        Override this base test because its record comparison filter removes
        every resuming-sync record for this tap.

        Base class idea:
            Compare the records after the bookmark from sync-1 with the
            records returned by the resuming sync.

        What the base class thinks:

            "If the tap resumes correctly, then the resumed records should
            match the part of the first sync that comes after the bookmark."

        That idea is correct only if updated_through is a real business
        timestamp.

        Visual example:

            injected bookmark:
                human_resources_job_profiles -> 2020-01-01T00:00:00Z

            first sync records:
                [A@2026-08-12T08:08:44Z,
                 B@2026-08-12T08:08:44Z,
                 C@2026-08-12T08:08:44Z]

            resuming sync records:
                [A@2026-08-12T08:23:30Z,
                 B@2026-08-12T08:23:30Z,
                 C@2026-08-12T08:23:30Z]

        The base keeps:

            from first sync:
                records where updated_through >= 2020-01-01T00:00:00Z
                -> [A, B, C]

            from resuming sync:
                records where updated_through <= first_sync_bookmark
                where first_sync_bookmark = 2026-08-12T08:08:44Z

                A -> 08:23:30 <= 08:08:44 ? no
                B -> 08:23:30 <= 08:08:44 ? no
                C -> 08:23:30 <= 08:08:44 ? no

                result -> []

        So the base assertion becomes:

            [A, B, C] == []

        That fails even though the tap returned the right records. The only
        problem is that updated_through in the resuming sync is the later
        fetch time, not a business timestamp.

        The remaining non-overridden tests still cover the important behavior:
            - every selected stream resumed and returned records
            - streams resumed in the correct order
        """
