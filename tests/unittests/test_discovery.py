"""
Unit tests for discovery behavior.

Covers:
  1. Credential validation (check_credentials)
  2. Per-stream authorization exclusion
  3. Empty catalog (no exception) when all streams are unauthorized
  4. Authorized streams produce an INFO log and appear in the catalog
"""

import unittest
from unittest.mock import Mock, patch

from tap_workday.client import Client, check_credentials
from tap_workday.exceptions import WorkdayAuthenticationError, WorkdaySOAPFaultError, WorkdaySOAPTransportError
from tap_workday.schema import get_schemas
from tap_workday.streams import STREAMS

CONFIG = {
    'hostname': 'test.workday.com',
    'username': 'test_user',
    'password': 'test_pass',
    'tenant': 'test_tenant',
}

_EXCLUDED = 'financial_management_cost_centers'
_PRESENT = 'financial_management_ledgers'


# ---------------------------------------------------------------------------
# check_credentials
# ---------------------------------------------------------------------------

class TestCheckCredentials(unittest.TestCase):
    """Credential probe called before discovery/sync."""

    def setUp(self):
        self.config = dict(CONFIG)

    def test_no_config_skips_the_network_call(self):
        """No config skips the network call without raising."""
        check_credentials(None)  # Should not raise

    @patch('tap_workday.client.Client')
    def test_does_not_raise_on_successful_probe(self, mock_client_class):
        """Successful SOAP call confirms credentials are valid; no exception raised."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client

        check_credentials(self.config)  # Should not raise

        mock_client_class.assert_called_once_with(self.config, service="Human_Resources")
        mock_client.check_access.assert_called_once_with("Get_Workers")

    @patch('tap_workday.client.Client')
    def test_raises_on_transport_401_by_status_code(self, mock_client_class):
        """HTTP 401 (via status_code) raises WorkdayAuthenticationError."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client
        mock_client.check_access.side_effect = WorkdaySOAPTransportError(
            "Transport error: Server returned HTTP status 401 (Unauthorized)",
            status_code=401,
        )

        with self.assertRaises(WorkdayAuthenticationError):
            check_credentials(self.config)

    @patch('tap_workday.client.Client')
    def test_raises_on_transport_401_by_message(self, mock_client_class):
        """HTTP 401 embedded in message (SOAPErrorHandler path, status_code=0) raises."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client
        mock_client.check_access.side_effect = WorkdaySOAPTransportError(
            "Transport error: Server returned HTTP status 401 (Unauthorized)",
            status_code=0,
        )

        with self.assertRaises(WorkdayAuthenticationError):
            check_credentials(self.config)

    @patch('tap_workday.client.Client')
    def test_does_not_raise_on_authorization_soap_fault(self, mock_client_class):
        """SOAP authorization fault = valid credentials; probe operation just not permitted."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client
        mock_client.check_access.side_effect = WorkdaySOAPFaultError(
            "Processing error occurred. The task submitted is not authorized."
        )

        check_credentials(self.config)  # Should not raise

    @patch('tap_workday.client.Client')
    def test_raises_on_authentication_soap_fault(self, mock_client_class):
        """SOAP fault with 'invalid username or password' raises WorkdayAuthenticationError."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client
        mock_client.check_access.side_effect = WorkdaySOAPFaultError(
            "SOAP Fault in 'Get_Workers': invalid username or password"
        )

        with self.assertRaises(WorkdayAuthenticationError):
            check_credentials(self.config)

    @patch('tap_workday.client.Client')
    def test_does_not_raise_on_non_401_transport_error(self, mock_client_class):
        """Non-401 transport errors (503, timeout) do not block discovery."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client
        mock_client.check_access.side_effect = WorkdaySOAPTransportError(
            "Transport error: Connection timed out", status_code=503
        )

        check_credentials(self.config)  # Should not raise

    @patch('tap_workday.client.Client')
    def test_does_not_raise_on_unexpected_exception(self, mock_client_class):
        """Unexpected probe errors do not block discovery."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client
        mock_client.check_access.side_effect = RuntimeError("Unexpected!")

        check_credentials(self.config)  # Should not raise


# ---------------------------------------------------------------------------
# get_schemas — authorization (per-stream)
# ---------------------------------------------------------------------------

class TestGetSchemasAuthorization(unittest.TestCase):
    """get_schemas excludes unauthorized streams and continues with the rest."""

    @patch('tap_workday.schema.check_stream_authorization')
    def test_unauthorized_stream_excluded_from_catalog(self, mock_check):
        """A stream that fails the access check is absent from schemas and field_metadata."""
        mock_check.side_effect = lambda cfg, name, obj: (True, None, None) if name != _EXCLUDED else (False, "authorization", "credentials lack the required permissions")

        schemas, field_metadata = get_schemas(config=CONFIG)

        self.assertNotIn(_EXCLUDED, schemas)
        self.assertNotIn(_EXCLUDED, field_metadata)

    @patch('tap_workday.schema.check_stream_authorization')
    def test_authorized_streams_remain_in_catalog(self, mock_check):
        """Streams that pass the access check appear in the catalog."""
        mock_check.side_effect = lambda cfg, name, obj: (True, None, None) if name != _EXCLUDED else (False, "authorization", "credentials lack the required permissions")

        schemas, field_metadata = get_schemas(config=CONFIG)

        self.assertIn(_PRESENT, schemas)
        self.assertIn(_PRESENT, field_metadata)

    @patch('tap_workday.schema.check_stream_authorization')
    def test_multiple_unauthorized_streams_all_excluded(self, mock_check):
        """All streams that fail the access check are absent from the catalog."""
        excluded = {
            'financial_management_cost_centers',
            'human_resources_locations',
            'performance_management_degrees',
        }
        mock_check.side_effect = lambda cfg, name, obj: (True, None, None) if name not in excluded else (False, "authorization", "credentials lack the required permissions")

        schemas, field_metadata = get_schemas(config=CONFIG)

        for name in excluded:
            self.assertNotIn(name, schemas, f"'{name}' should be excluded")
            self.assertNotIn(name, field_metadata, f"'{name}' metadata should be excluded")
        self.assertIn(_PRESENT, schemas)

    @patch('tap_workday.schema.check_stream_authorization')
    def test_only_passing_stream_in_catalog(self, mock_check):
        """Only the single passing stream appears in the catalog."""
        mock_check.side_effect = lambda cfg, name, obj: (True, None, None) if name == _PRESENT else (False, "authorization", "credentials lack the required permissions")

        schemas, _ = get_schemas(config=CONFIG)

        self.assertEqual(list(schemas.keys()), [_PRESENT])


# ---------------------------------------------------------------------------
# get_schemas — all streams unauthorized
# ---------------------------------------------------------------------------

class TestGetSchemasAllUnauthorized(unittest.TestCase):
    """get_schemas returns an empty catalog (no exception) when no streams are authorized."""

    @patch('tap_workday.schema.check_stream_authorization', return_value=(False, "authorization", "credentials lack the required permissions"))
    def test_returns_empty_catalog_no_exception(self, mock_check):
        """Empty dicts are returned; no exception is raised."""
        schemas, field_metadata = get_schemas(config=CONFIG)

        self.assertEqual(schemas, {})
        self.assertEqual(field_metadata, {})

    @patch('tap_workday.schema.check_stream_authorization', return_value=(False, "authorization", "credentials lack the required permissions"))
    def test_logs_no_authorized_streams_warning(self, mock_check):
        """A warning is logged when the catalog ends up empty after authorization checks."""
        with self.assertLogs(level='WARNING') as cm:
            get_schemas(config=CONFIG)

        self.assertTrue(
            any('no authorized streams' in msg.lower() for msg in cm.output),
            "Expected 'no authorized streams' in log output",
        )

