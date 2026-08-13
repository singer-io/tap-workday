import unittest
from unittest.mock import MagicMock, patch

from tap_workday.streams.abstracts import IncrementalStream, _extract_max_date
from tap_workday.streams.human_resources import (
    Organizations as HROrgs, JobProfiles,
)
from tap_workday.streams.financial_management import (
    Organizations as FMOrgs, Journals, CostCenters, RevenueCategories,
)
from tap_workday.streams.staffing import Organizations as StaffingOrgs


class ConcreteParentBaseStream(IncrementalStream):
    @property
    def key_properties(self):
        return ["id"]

    @property
    def replication_keys(self):
        return ["updated_at"]

    @property
    def replication_method(self):
        return "INCREMENTAL"

    @property
    def tap_stream_id(self):
        return "stream_1"


class TestSync(unittest.TestCase):
    @patch("tap_workday.streams.abstracts.metadata.to_map")
    def setUp(self, mock_to_map):

        mock_catalog = MagicMock()
        mock_catalog.schema.to_dict.return_value = {"key": "value"}
        mock_catalog.metadata = "mock_metadata"
        mock_to_map.return_value = {"metadata_key": "metadata_value"}

        self.stream = ConcreteParentBaseStream(catalog=mock_catalog)
        self.stream.client = MagicMock()
        self.stream.child_to_sync = []

    @patch("tap_workday.streams.abstracts.get_bookmark", return_value=100)
    def test_write_bookmark_with_state(self, mock_get_bookmark):

        state = {"bookmarks": {"stream_1": {"updated_at": 100}}}
        result = self.stream.write_bookmark(state, "stream_1", "updated_at", 200)
        self.assertEqual(result, {"bookmarks": {"stream_1": {"updated_at": 200}}})

    @patch("tap_workday.streams.abstracts.get_bookmark", return_value=100)
    def test_write_bookmark_without_state(self, mock_get_bookmark):

        state = {}
        result = self.stream.write_bookmark(state, "stream_1", "updated_at", 200)
        self.assertEqual(result, {"bookmarks": {"stream_1": {"updated_at": 200}}})

    @patch("tap_workday.streams.abstracts.get_bookmark", return_value=300)
    def test_write_bookmark_with_old_value(self, mock_get_bookmark):

        state = {"bookmarks": {"stream_1": {"updated_at": 300}}}
        result = self.stream.write_bookmark(state, "stream_1", "updated_at", 200)
        self.assertEqual(result, {"bookmarks": {"stream_1": {"updated_at": 300}}})


# ── helpers ──────────────────────────────────────────────────────────────────

def _stream(cls):
    mock_catalog = MagicMock()
    mock_catalog.schema.to_dict.return_value = {}
    mock_catalog.metadata = []
    inst = cls(catalog=mock_catalog)
    inst.client = MagicMock()
    inst.client.config = {"start_date": "2019-01-01T00:00:00Z"}
    return inst


# ── WorkdayTableStream — bookmark priority and state writes ───────────────────

class TestWorkdayTableStreamSync(unittest.TestCase):
    """Tests for the incremental WorkdayTableStream.sync() implementation."""

    def setUp(self):
        self.stream = _stream(HROrgs)
        self.stream.get_client = MagicMock(return_value=MagicMock())
        self.stream._get_sync_start_time = MagicMock(return_value="2026-08-10T08:00:00Z")

    @patch("tap_workday.streams.abstracts.write_state")
    @patch("tap_workday.streams.abstracts.write_bookmark")
    @patch("tap_workday.streams.abstracts.emit_full_table", return_value=41)
    @patch("tap_workday.streams.abstracts.call_workday_operation", return_value=[])
    @patch("tap_workday.streams.abstracts.get_bookmark", return_value="2019-01-01T00:00:00Z")
    def test_first_run_uses_start_date_writes_bookmark(
        self, mock_gbm, mock_cwo, mock_eft, mock_wb, mock_ws
    ):
        """Run 1: empty state → get_bookmark returns start_date; bookmark is written."""
        self.stream.sync({}, MagicMock())
        mock_gbm.assert_called_once_with(
            {}, "human_resources_organizations", "updated_through", "2019-01-01T00:00:00Z"
        )
        mock_wb.assert_called_once()
        mock_ws.assert_called_once()

    @patch("tap_workday.streams.abstracts.write_state")
    @patch("tap_workday.streams.abstracts.write_bookmark")
    @patch("tap_workday.streams.abstracts.emit_full_table", return_value=0)
    @patch("tap_workday.streams.abstracts.call_workday_operation", return_value=[])
    @patch("tap_workday.streams.abstracts.get_bookmark", return_value="2026-08-10T08:12:11Z")
    def test_second_run_uses_bookmark_not_start_date(
        self, mock_gbm, mock_cwo, mock_eft, mock_wb, mock_ws
    ):
        """Run 2+: bookmark in state overrides start_date. 0 records = nothing changed — correct."""
        state = {"bookmarks": {"human_resources_organizations": {"updated_through": "2026-08-10T08:12:11Z"}}}
        count = self.stream.sync(state, MagicMock())
        # start_date is only the *fallback*; bookmark was returned by get_bookmark
        mock_gbm.assert_called_once_with(
            state, "human_resources_organizations", "updated_through", "2019-01-01T00:00:00Z"
        )
        self.assertEqual(count, 0)       # nothing changed in Workday — correct
        mock_wb.assert_called_once()     # bookmark still advances
        mock_ws.assert_called_once()

    @patch("tap_workday.streams.abstracts.write_state")
    @patch("tap_workday.streams.abstracts.write_bookmark")
    @patch("tap_workday.streams.abstracts.emit_full_table", return_value=0)
    @patch("tap_workday.streams.abstracts.call_workday_operation", return_value=[])
    def test_full_table_stream_does_not_write_bookmark(self, _cwo, _eft, mock_wb, mock_ws):
        """FULL_TABLE streams (replication_keys=[]) must not touch state at all."""
        from tap_workday.streams.financial_management import JournalSources
        ft = _stream(JournalSources)
        ft.get_client = MagicMock(return_value=MagicMock())
        ft.sync({}, MagicMock())
        mock_wb.assert_not_called()
        mock_ws.assert_not_called()


# ── build_filter_params — SOAP structure per stream type ─────────────────────

class TestBuildFilterParams(unittest.TestCase):
    """Verify each incremental stream produces the correct Workday SOAP filter."""

    FROM = "2020-01-01T00:00:00Z"
    THROUGH = "2026-08-10T08:00:00Z"

    def _params(self, cls):
        return _stream(cls).build_filter_params(self.FROM, self.THROUGH)

    def test_no_filter_when_updated_since_is_none(self):
        for cls in (HROrgs, JobProfiles, FMOrgs, Journals, CostCenters, RevenueCategories, StaffingOrgs):
            with self.subTest(cls=cls.__name__):
                self.assertEqual(_stream(cls).build_filter_params(None), {})

    def test_transaction_log_criteria_streams(self):
        """HR+FM+Staffing Organizations use Transaction_Log_Criteria (no _Data suffix)."""
        for cls in (HROrgs, FMOrgs, StaffingOrgs):
            with self.subTest(cls=cls.__name__):
                dr = self._params(cls)["Request_Criteria"]["Transaction_Log_Criteria"]["Transaction_Date_Range_Data"]
                self.assertEqual(dr["Updated_From"], self.FROM)
                self.assertEqual(dr["Updated_Through"], self.THROUGH)

    def test_job_profiles_uses_transaction_log_criteria_data(self):
        """Get_Job_Profiles uses Transaction_Log_Criteria_Data (with _Data suffix)."""
        dr = self._params(JobProfiles)["Request_Criteria"]["Transaction_Log_Criteria_Data"]["Transaction_Date_Range_Data"]
        self.assertEqual(dr["Updated_From"], self.FROM)

    def test_updated_from_date_streams(self):
        """Journals, CostCenters, RevenueCategories use Updated_From_Date / Updated_To_Date."""
        for cls in (Journals, CostCenters, RevenueCategories):
            with self.subTest(cls=cls.__name__):
                rc = self._params(cls)["Request_Criteria"]
                self.assertEqual(rc["Updated_From_Date"], self.FROM)
                self.assertEqual(rc["Updated_To_Date"], self.THROUGH)


# ── stream attributes ─────────────────────────────────────────────────────────

class TestStreamAttributes(unittest.TestCase):

    INCREMENTAL = [HROrgs, JobProfiles, FMOrgs, Journals, CostCenters, RevenueCategories, StaffingOrgs]

    def test_seven_incremental_streams(self):
        from tap_workday.streams import STREAMS
        inc = [k for k, v in STREAMS.items() if getattr(v, "replication_method", "") == "INCREMENTAL"]
        self.assertEqual(len(inc), 7)

    def test_all_incremental_have_updated_through_key(self):
        for cls in self.INCREMENTAL:
            with self.subTest(cls=cls.__name__):
                self.assertEqual(cls.replication_keys, ["updated_through"])

    def test_bookmark_field_path_none_for_all(self):
        """None = bookmark falls back to sync_start_time.

        Last_Updated_DateTime is Workday's *effective* date and can be
        future-dated — it does not match the internal transaction log
        timestamp the API actually filters on.
        """
        for cls in self.INCREMENTAL:
            with self.subTest(cls=cls.__name__):
                self.assertIsNone(cls.bookmark_field_path)


# ── _extract_max_date ─────────────────────────────────────────────────────────

class TestExtractMaxDate(unittest.TestCase):

    PATH = ["Organization_Data", "Last_Updated_DateTime"]

    def test_returns_none_for_empty_list(self):
        self.assertIsNone(_extract_max_date([], self.PATH))

    def test_returns_maximum_string(self):
        records = [
            {"Organization_Data": {"Last_Updated_DateTime": "2020-01-30T00:29:21Z"}},
            {"Organization_Data": {"Last_Updated_DateTime": "2025-10-20T03:33:45Z"}},
            {"Organization_Data": {"Last_Updated_DateTime": "2022-09-10T08:45:41Z"}},
        ]
        self.assertEqual(_extract_max_date(records, self.PATH), "2025-10-20T03:33:45Z")

    def test_skips_null_and_missing_fields(self):
        records = [
            {"Organization_Data": {"Last_Updated_DateTime": None}},
            {"Organization_Data": {}},
            {"Organization_Data": {"Last_Updated_DateTime": "2021-06-15T00:00:00Z"}},
        ]
        self.assertEqual(_extract_max_date(records, self.PATH), "2021-06-15T00:00:00Z")

    def test_datetime_object_converted(self):
        from datetime import datetime, timezone
        records = [{"Organization_Data": {"Last_Updated_DateTime":
                    datetime(2025, 6, 24, 7, 27, 14, tzinfo=timezone.utc)}}]
        self.assertEqual(_extract_max_date(records, self.PATH), "2025-06-24T07:27:14Z")
