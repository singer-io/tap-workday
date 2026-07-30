"""
Unit tests for get_schemas discovery behavior.

Verifies that inaccessible streams (unauthorized or invalid credentials)
are excluded from the catalog while accessible streams remain.
"""

import unittest
from unittest.mock import patch

from tap_workday.exceptions import WorkdayForbiddenError
from tap_workday.schema import get_schemas


CONFIG = {
    'hostname': 'test.workday.com',
    'username': 'test_user',
    'password': 'test_pass',
    'tenant': 'test_tenant',
}

# Stable names to use as fixtures across tests
_EXCLUDED = 'financial_management_cost_centers'
_PRESENT = 'financial_management_ledgers'


class TestGetSchemasDiscoveryExclusion(unittest.TestCase):
    """get_schemas excludes streams whose access check fails and continues for the rest."""

    @patch('tap_workday.schema.check_stream_authorization')
    def test_unauthorized_stream_excluded_from_catalog(self, mock_check):
        """A stream that fails the access check is absent from both schemas and field_metadata."""
        mock_check.side_effect = lambda cfg, name, obj: name != _EXCLUDED

        schemas, field_metadata = get_schemas(config=CONFIG)

        self.assertNotIn(_EXCLUDED, schemas)
        self.assertNotIn(_EXCLUDED, field_metadata)

    @patch('tap_workday.schema.check_stream_authorization')
    def test_accessible_streams_remain_in_catalog(self, mock_check):
        """Streams that pass the access check are still present in the catalog."""
        mock_check.side_effect = lambda cfg, name, obj: name != _EXCLUDED

        schemas, field_metadata = get_schemas(config=CONFIG)

        self.assertIn(_PRESENT, schemas)
        self.assertIn(_PRESENT, field_metadata)

    @patch('tap_workday.schema.check_stream_authorization')
    def test_multiple_excluded_streams_all_absent(self, mock_check):
        """All streams that fail the access check are removed from the catalog."""
        excluded = {
            'financial_management_cost_centers',
            'human_resources_locations',
            'performance_management_degrees',
        }
        mock_check.side_effect = lambda cfg, name, obj: name not in excluded

        schemas, field_metadata = get_schemas(config=CONFIG)

        for name in excluded:
            self.assertNotIn(name, schemas, f"'{name}' should be excluded")
            self.assertNotIn(name, field_metadata, f"'{name}' should be excluded from metadata")

        # At least one accessible stream must survive
        self.assertIn(_PRESENT, schemas)

    @patch('tap_workday.schema.check_stream_authorization')
    def test_raises_forbidden_error_when_all_streams_excluded(self, mock_check):
        """WorkdayForbiddenError is raised when every stream fails the access check."""
        mock_check.return_value = False

        with self.assertRaises(WorkdayForbiddenError):
            get_schemas(config=CONFIG)

    @patch('tap_workday.schema.check_stream_authorization')
    def test_no_forbidden_error_when_at_least_one_stream_accessible(self, mock_check):
        """No error is raised as long as at least one stream passes the access check."""
        mock_check.side_effect = lambda cfg, name, obj: name == _PRESENT

        # Should not raise
        schemas, _ = get_schemas(config=CONFIG)

        self.assertEqual(list(schemas.keys()), [_PRESENT])

    def test_no_config_returns_all_streams_without_access_checks(self):
        """When config is None, no access checks are made and all streams are returned."""
        schemas, field_metadata = get_schemas(config=None)

        # All STREAMS entries must be present
        from tap_workday.streams import STREAMS
        self.assertEqual(set(schemas.keys()), set(STREAMS.keys()))
        self.assertEqual(set(field_metadata.keys()), set(STREAMS.keys()))

    @patch('tap_workday.schema.check_stream_authorization')
    def test_no_forbidden_error_raised_when_no_config(self, mock_check):
        """The all-excluded guard is gated on config being truthy.

        Even when the mock excludes every stream, no WorkdayForbiddenError is raised
        because the guard is ``if config and not schemas`` — falsy config skips it.
        """
        mock_check.return_value = False

        # No error raised; schemas is empty because mock excluded everything
        schemas, field_metadata = get_schemas(config=None)

        self.assertEqual(schemas, {})
        self.assertEqual(field_metadata, {})
