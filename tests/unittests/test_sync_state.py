import unittest
import importlib
from unittest.mock import Mock, call, patch

sync_module = importlib.import_module("tap_workday.sync")


class _SelectedStream:
    def __init__(self, stream):
        self.stream = stream


class _DummyStream:
    parent = None
    children = []

    def __init__(self, _client, _catalog_stream):
        self.child_to_sync = []

    def is_selected(self):
        return True

    def write_schema(self):
        return None

    def sync(self, state=None, transformer=None):
        return 1


class _NoopTransformer:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestInterruptedSyncResume(unittest.TestCase):
    def test_apply_resume_without_currently_syncing(self):
        state = {"bookmarks": {}}
        streams = ["a", "b", "c"]

        result = sync_module._apply_interrupted_sync_resume(streams, state)

        self.assertEqual(result, streams)

    def test_apply_resume_with_currently_syncing_present(self):
        state = {"currently_syncing": "b", "bookmarks": {}}
        streams = ["a", "b", "c"]

        result = sync_module._apply_interrupted_sync_resume(streams, state)

        self.assertEqual(result, ["b", "c"])

    def test_apply_resume_with_currently_syncing_missing_from_selection(self):
        state = {"currently_syncing": "x", "bookmarks": {}}
        streams = ["a", "b", "c"]

        result = sync_module._apply_interrupted_sync_resume(streams, state)

        self.assertEqual(result, streams)


class TestSyncUsesCurrentlySyncing(unittest.TestCase):
    @patch("tap_workday.sync.singer.Transformer", return_value=_NoopTransformer())
    @patch("tap_workday.sync.write_schema")
    @patch("tap_workday.sync.update_currently_syncing")
    @patch.dict("tap_workday.sync.STREAMS", {"a": _DummyStream, "b": _DummyStream}, clear=False)
    def test_sync_starts_from_currently_syncing_stream(
        self, mock_update_currently_syncing, _mock_write_schema, _mock_transformer
    ):
        catalog = Mock()
        catalog.get_selected_streams.return_value = [
            _SelectedStream("a"),
            _SelectedStream("b"),
        ]
        catalog.get_stream.return_value = Mock()
        state = {"currently_syncing": "b", "bookmarks": {}}

        sync_module.sync(client=Mock(), config={}, catalog=catalog, state=state)

        self.assertEqual(
            mock_update_currently_syncing.call_args_list,
            [
                call(state, "b"),
                call(state, None),
            ],
        )


class TestUpdateCurrentlySyncingWriteBehavior(unittest.TestCase):
    @patch("tap_workday.sync.singer.write_state")
    @patch("tap_workday.sync.singer.set_currently_syncing")
    @patch("tap_workday.sync.singer.get_currently_syncing", return_value="staffing_organizations")
    def test_clear_does_not_write_state(
        self, _mock_get_currently_syncing, mock_set_currently_syncing, mock_write_state
    ):
        state = {"currently_syncing": "staffing_organizations", "bookmarks": {}}

        sync_module.update_currently_syncing(state, None)

        self.assertNotIn("currently_syncing", state)
        mock_set_currently_syncing.assert_not_called()
        mock_write_state.assert_not_called()

    @patch("tap_workday.sync.singer.write_state")
    @patch("tap_workday.sync.singer.set_currently_syncing")
    def test_set_writes_state(self, mock_set_currently_syncing, mock_write_state):
        state = {"bookmarks": {}}

        sync_module.update_currently_syncing(state, "staffing_organizations")

        mock_set_currently_syncing.assert_called_once_with(state, "staffing_organizations")
        mock_write_state.assert_called_once_with(state)
