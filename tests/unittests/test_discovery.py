"""
Unit tests for discovery logic: access checks, stream exclusion, and catalog building.
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

from tap_workday.discover import _apply_access_checks, _prune_inaccessible_children, discover
from tap_workday.exceptions import WorkdayForbiddenError, WorkdaySOAPFaultError
from tap_workday.streams import STREAMS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(config=None):
    """Return a lightweight mock Client."""
    client = Mock()
    client.config = config or {
        "hostname": "test.workday.com",
        "username": "user",
        "password": "pass",
        "tenant": "tenant",
        "start_date": "2024-01-01T00:00:00Z",
    }
    return client


def _minimal_schemas():
    """Return a tiny schemas dict with two independent (parent-less) streams."""
    return {
        "financial_management_cost_centers": {"type": "object", "properties": {}},
        "financial_management_journals": {"type": "object", "properties": {}},
    }


def _minimal_field_metadata():
    return {
        "financial_management_cost_centers": [],
        "financial_management_journals": [],
    }


# ---------------------------------------------------------------------------
# _apply_access_checks
# ---------------------------------------------------------------------------

class TestApplyAccessChecks(unittest.TestCase):
    """Tests for _apply_access_checks()."""

    def test_all_streams_accessible_leaves_schemas_unchanged(self):
        schemas = _minimal_schemas()
        field_metadata = _minimal_field_metadata()
        client = _make_client()

        with patch("tap_workday.discover.STREAMS", {
            "financial_management_cost_centers": _make_accessible_stream_class(),
            "financial_management_journals": _make_accessible_stream_class(),
        }):
            _apply_access_checks(client, schemas, field_metadata)

        self.assertIn("financial_management_cost_centers", schemas)
        self.assertIn("financial_management_journals", schemas)

    def test_forbidden_stream_is_removed(self):
        schemas = _minimal_schemas()
        field_metadata = _minimal_field_metadata()
        client = _make_client()

        forbidden_cls = _make_forbidden_stream_class()
        accessible_cls = _make_accessible_stream_class()

        with patch("tap_workday.discover.STREAMS", {
            "financial_management_cost_centers": forbidden_cls,
            "financial_management_journals": accessible_cls,
        }):
            _apply_access_checks(client, schemas, field_metadata)

        self.assertNotIn("financial_management_cost_centers", schemas)
        self.assertNotIn("financial_management_cost_centers", field_metadata)
        self.assertIn("financial_management_journals", schemas)

    def test_soap_auth_fault_removes_stream(self):
        schemas = _minimal_schemas()
        field_metadata = _minimal_field_metadata()
        client = _make_client()

        soap_auth_cls = _make_soap_auth_fault_stream_class()
        accessible_cls = _make_accessible_stream_class()

        with patch("tap_workday.discover.STREAMS", {
            "financial_management_cost_centers": soap_auth_cls,
            "financial_management_journals": accessible_cls,
        }):
            _apply_access_checks(client, schemas, field_metadata)

        self.assertNotIn("financial_management_cost_centers", schemas)
        self.assertIn("financial_management_journals", schemas)

    def test_non_auth_soap_fault_is_reraised(self):
        schemas = _minimal_schemas()
        field_metadata = _minimal_field_metadata()
        client = _make_client()

        non_auth_cls = _make_soap_non_auth_fault_stream_class()
        accessible_cls = _make_accessible_stream_class()

        with patch("tap_workday.discover.STREAMS", {
            "financial_management_cost_centers": non_auth_cls,
            "financial_management_journals": accessible_cls,
        }):
            with self.assertRaises(WorkdaySOAPFaultError):
                _apply_access_checks(client, schemas, field_metadata)

    def test_all_streams_inaccessible_raises_exception(self):
        schemas = _minimal_schemas()
        field_metadata = _minimal_field_metadata()
        client = _make_client()

        with patch("tap_workday.discover.STREAMS", {
            "financial_management_cost_centers": _make_forbidden_stream_class(),
            "financial_management_journals": _make_forbidden_stream_class(),
        }):
            with self.assertRaises(Exception, msg="all streams inaccessible"):
                _apply_access_checks(client, schemas, field_metadata)

    def test_child_streams_are_skipped_during_access_check(self):
        """Child streams should never be checked for access directly."""
        schemas = {
            "financial_management_journals": {"type": "object", "properties": {}},
            "financial_management_ledgers": {"type": "object", "properties": {}},
        }
        field_metadata = {
            "financial_management_journals": [],
            "financial_management_ledgers": [],
        }
        client = _make_client()

        # journals is a parent, ledgers is treated as a child here
        child_checked = []

        class ChildStreamCls:
            parent = "financial_management_journals"  # non-empty → child

            def __init__(self, client=None):
                pass

            def check_access(self):
                child_checked.append(True)
                return True

        accessible_cls = _make_accessible_stream_class()

        with patch("tap_workday.discover.STREAMS", {
            "financial_management_journals": accessible_cls,
            "financial_management_ledgers": ChildStreamCls,
        }):
            _apply_access_checks(client, schemas, field_metadata)

        self.assertEqual(child_checked, [], "Child stream check_access should not be called")
        self.assertIn("financial_management_ledgers", schemas)


# ---------------------------------------------------------------------------
# _prune_inaccessible_children
# ---------------------------------------------------------------------------

class TestPruneInaccessibleChildren(unittest.TestCase):
    """Tests for _prune_inaccessible_children()."""

    def test_child_removed_when_parent_absent(self):
        schemas = {
            # parent stream is NOT present
            "child_stream": {"type": "object"},
        }
        field_metadata = {"child_stream": []}

        class ChildCls:
            parent = "missing_parent"

        with patch("tap_workday.discover.STREAMS", {"child_stream": ChildCls}):
            _prune_inaccessible_children(schemas, field_metadata)

        self.assertNotIn("child_stream", schemas)
        self.assertNotIn("child_stream", field_metadata)

    def test_child_retained_when_parent_present(self):
        schemas = {
            "parent_stream": {"type": "object"},
            "child_stream": {"type": "object"},
        }
        field_metadata = {"parent_stream": [], "child_stream": []}

        class ParentCls:
            parent = ""

        class ChildCls:
            parent = "parent_stream"

        with patch("tap_workday.discover.STREAMS", {
            "parent_stream": ParentCls,
            "child_stream": ChildCls,
        }):
            _prune_inaccessible_children(schemas, field_metadata)

        self.assertIn("parent_stream", schemas)
        self.assertIn("child_stream", schemas)

    def test_grandchild_removed_when_parent_removed(self):
        """Cascading removal: grandchild is removed after parent is removed."""
        schemas = {
            # grandparent is NOT present
            "child_stream": {"type": "object"},
            "grandchild_stream": {"type": "object"},
        }
        field_metadata = {"child_stream": [], "grandchild_stream": []}

        class ChildCls:
            parent = "missing_grandparent"

        class GrandchildCls:
            parent = "child_stream"

        with patch("tap_workday.discover.STREAMS", {
            "child_stream": ChildCls,
            "grandchild_stream": GrandchildCls,
        }):
            _prune_inaccessible_children(schemas, field_metadata)

        self.assertNotIn("child_stream", schemas)
        self.assertNotIn("grandchild_stream", schemas)

    def test_no_pruning_when_all_parents_present(self):
        schemas = {
            "stream_a": {"type": "object"},
            "stream_b": {"type": "object"},
        }
        field_metadata = {"stream_a": [], "stream_b": []}

        class ClsA:
            parent = ""

        class ClsB:
            parent = ""

        with patch("tap_workday.discover.STREAMS", {"stream_a": ClsA, "stream_b": ClsB}):
            _prune_inaccessible_children(schemas, field_metadata)

        self.assertEqual(set(schemas.keys()), {"stream_a", "stream_b"})


# ---------------------------------------------------------------------------
# discover()
# ---------------------------------------------------------------------------

class TestDiscover(unittest.TestCase):
    """Integration-style tests for discover()."""

    @patch("tap_workday.discover._prune_inaccessible_children")
    @patch("tap_workday.discover._apply_access_checks")
    @patch("tap_workday.discover.get_schemas")
    def test_discover_builds_catalog_from_accessible_streams(
        self, mock_get_schemas, mock_apply, mock_prune
    ):
        """discover() should build a Catalog with one entry per accessible stream."""
        mock_get_schemas.return_value = (
            {"stream_a": {"type": "object", "properties": {"id": {"type": "string"}}}},
            {
                "stream_a": [
                    {
                        "metadata": {
                            "inclusion": "automatic",
                            "table-key-properties": ["id"],
                            "valid-replication-keys": [],
                            "forced-replication-method": "FULL_TABLE",
                        },
                        "breadcrumb": [],
                    }
                ]
            },
        )
        client = _make_client()

        catalog = discover(client)

        mock_get_schemas.assert_called_once_with(config=client.config)
        mock_apply.assert_called_once()
        mock_prune.assert_called_once()

        self.assertEqual(len(catalog.streams), 1)
        self.assertEqual(catalog.streams[0].tap_stream_id, "stream_a")

    @patch("tap_workday.discover._prune_inaccessible_children")
    @patch("tap_workday.discover._apply_access_checks")
    @patch("tap_workday.discover.get_schemas")
    def test_discover_passes_client_config_to_get_schemas(
        self, mock_get_schemas, mock_apply, mock_prune
    ):
        mock_get_schemas.return_value = ({}, {})
        client = _make_client({"start_date": "2024-01-01T00:00:00Z", "hostname": "h"})

        catalog = discover(client)

        mock_get_schemas.assert_called_once_with(config=client.config)
        # With empty schemas, an empty catalog is produced
        self.assertEqual(len(catalog.streams), 0)


# ---------------------------------------------------------------------------
# STREAMS catalog: metadata & schema validation
# ---------------------------------------------------------------------------

class TestStreamsCatalogMetadata(unittest.TestCase):
    """Validate that all registered streams have required attributes."""

    def test_all_streams_have_tap_stream_id(self):
        for name, cls in STREAMS.items():
            with self.subTest(stream=name):
                self.assertTrue(
                    hasattr(cls, "tap_stream_id"),
                    f"{name} missing tap_stream_id",
                )

    def test_all_streams_have_key_properties(self):
        for name, cls in STREAMS.items():
            with self.subTest(stream=name):
                self.assertTrue(
                    hasattr(cls, "key_properties"),
                    f"{name} missing key_properties",
                )

    def test_all_streams_have_replication_method(self):
        for name, cls in STREAMS.items():
            with self.subTest(stream=name):
                self.assertTrue(
                    hasattr(cls, "replication_method"),
                    f"{name} missing replication_method",
                )
                self.assertIn(
                    cls.replication_method,
                    ("FULL_TABLE", "INCREMENTAL"),
                    f"{name} has invalid replication_method",
                )

    def test_all_streams_have_check_access_method(self):
        for name, cls in STREAMS.items():
            with self.subTest(stream=name):
                self.assertTrue(
                    hasattr(cls, "check_access") and callable(cls.check_access),
                    f"{name} missing callable check_access",
                )


# ---------------------------------------------------------------------------
# Private helpers for building mock stream classes
# ---------------------------------------------------------------------------

def _make_accessible_stream_class():
    """Stream class whose check_access() always succeeds."""

    class AccessibleStream:
        parent = ""
        service_name = "Test_Service"
        operation_name = "Test_Op"

        def __init__(self, client=None):
            pass

        def check_access(self):
            return True

    return AccessibleStream


def _make_forbidden_stream_class():
    """Stream class whose check_access() raises WorkdayForbiddenError."""

    class ForbiddenStream:
        parent = ""
        service_name = "Test_Service"
        operation_name = "Test_Op"

        def __init__(self, client=None):
            pass

        def check_access(self):
            raise WorkdayForbiddenError("not authorized")

    return ForbiddenStream


def _make_soap_auth_fault_stream_class():
    """Stream class whose check_access() raises a WorkdaySOAPFaultError with auth pattern."""

    class SoapAuthFaultStream:
        parent = ""
        service_name = "Test_Service"
        operation_name = "Test_Op"

        def __init__(self, client=None):
            pass

        def check_access(self):
            raise WorkdaySOAPFaultError(
                "Processing error occurred. The task submitted is not authorized."
            )

    return SoapAuthFaultStream


def _make_soap_non_auth_fault_stream_class():
    """Stream class whose check_access() raises a non-auth WorkdaySOAPFaultError."""

    class SoapNonAuthStream:
        parent = ""
        service_name = "Test_Service"
        operation_name = "Test_Op"

        def __init__(self, client=None):
            pass

        def check_access(self):
            raise WorkdaySOAPFaultError("Some unexpected SOAP error")

    return SoapNonAuthStream


if __name__ == "__main__":
    unittest.main()
