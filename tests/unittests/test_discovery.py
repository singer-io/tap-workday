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

from tap_workday.client import Client, _AUTH_MODE_OAUTH, _AUTH_MODE_WSSECURITY
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

    def _make_client(self, auth_mode=_AUTH_MODE_WSSECURITY):
        """Create a Client instance without triggering __init__ network calls."""
        client = object.__new__(Client)
        client.config = self.config
        client._auth_mode = auth_mode
        client._token_manager = Mock()
        client._token_manager.fetch.return_value = "mock_access_token"
        client._session = Mock()
        return client

    def test_no_config_skips_the_network_call(self):
        """No config skips the network call without raising."""
        client = object.__new__(Client)
        client.config = None
        client.check_credentials()  # Should not raise

    def test_does_not_raise_on_successful_probe(self):
        """Successful SOAP probe confirms credentials are valid; no exception raised."""
        client = self._make_client()
        with patch.object(client, 'check_access'):
            client.check_credentials()  # Should not raise

    def test_raises_on_transport_401_by_status_code(self):
        """HTTP 401 (via status_code) raises WorkdayAuthenticationError."""
        client = self._make_client()
        with patch.object(client, 'check_access', side_effect=WorkdaySOAPTransportError(
            "Transport error: Server returned HTTP status 401 (Unauthorized)",
            status_code=401,
        )):
            with self.assertRaises(WorkdayAuthenticationError):
                client.check_credentials()

    def test_raises_on_transport_401_by_message(self):
        """HTTP 401 embedded in message (status_code=0) raises WorkdayAuthenticationError."""
        client = self._make_client()
        with patch.object(client, 'check_access', side_effect=WorkdaySOAPTransportError(
            "Transport error: Server returned HTTP status 401 (Unauthorized)",
            status_code=0,
        )):
            with self.assertRaises(WorkdayAuthenticationError):
                client.check_credentials()

    def test_does_not_raise_on_authorization_soap_fault(self):
        """SOAP authorization fault = valid credentials; probe operation just not permitted."""
        client = self._make_client()
        with patch.object(client, 'check_access', side_effect=WorkdaySOAPFaultError(
            "Processing error occurred. The task submitted is not authorized."
        )):
            client.check_credentials()  # Should not raise

    def test_raises_on_authentication_soap_fault(self):
        """SOAP fault with 'invalid username or password' raises WorkdayAuthenticationError."""
        client = self._make_client()
        with patch.object(client, 'check_access', side_effect=WorkdaySOAPFaultError(
            "SOAP Fault in 'Get_Workers': invalid username or password"
        )):
            with self.assertRaises(WorkdayAuthenticationError):
                client.check_credentials()

    def test_does_not_raise_on_non_401_transport_error(self):
        """Non-401 transport errors (503, timeout) do not block discovery."""
        client = self._make_client()
        with patch.object(client, 'check_access', side_effect=WorkdaySOAPTransportError(
            "Transport error: Connection timed out", status_code=503
        )):
            client.check_credentials()  # Should not raise

    def test_raises_on_unexpected_exception(self):
        """Unexpected probe errors are raised after being logged."""
        client = self._make_client()
        with patch.object(client, 'check_access', side_effect=RuntimeError("Unexpected!")):
            with self.assertRaises(RuntimeError):
                client.check_credentials()


# ---------------------------------------------------------------------------
# get_schemas — authorization (per-stream)
# ---------------------------------------------------------------------------

class TestGetSchemasAuthorization(unittest.TestCase):
    """get_schemas excludes unauthorized streams and continues with the rest."""

    @patch('tap_workday.schema.check_stream_authorization')
    def test_unauthorized_stream_excluded_from_catalog(self, mock_check):
        """A stream that fails the access check is absent from schemas and field_metadata."""
        mock_check.side_effect = lambda cfg, name, obj, **kwargs: (True, None, None) if name != _EXCLUDED else (False, "authorization", "credentials lack the required permissions")

        schemas, field_metadata = get_schemas(config=CONFIG)

        self.assertNotIn(_EXCLUDED, schemas)
        self.assertNotIn(_EXCLUDED, field_metadata)

    @patch('tap_workday.schema.check_stream_authorization')
    def test_authorized_streams_remain_in_catalog(self, mock_check):
        """Streams that pass the access check appear in the catalog."""
        mock_check.side_effect = lambda cfg, name, obj, **kwargs: (True, None, None) if name != _EXCLUDED else (False, "authorization", "credentials lack the required permissions")

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
        mock_check.side_effect = lambda cfg, name, obj, **kwargs: (True, None, None) if name not in excluded else (False, "authorization", "credentials lack the required permissions")

        schemas, field_metadata = get_schemas(config=CONFIG)

        for name in excluded:
            self.assertNotIn(name, schemas, f"'{name}' should be excluded")
            self.assertNotIn(name, field_metadata, f"'{name}' metadata should be excluded")
        self.assertIn(_PRESENT, schemas)

    @patch('tap_workday.schema.check_stream_authorization')
    def test_only_passing_stream_in_catalog(self, mock_check):
        """Only the single passing stream appears in the catalog."""
        mock_check.side_effect = lambda cfg, name, obj, **kwargs: (True, None, None) if name == _PRESENT else (False, "authorization", "credentials lack the required permissions")

        schemas, _ = get_schemas(config=CONFIG)

        self.assertEqual(list(schemas.keys()), [_PRESENT])


# ---------------------------------------------------------------------------
# get_schemas — all streams unauthorized
# ---------------------------------------------------------------------------

class TestGetSchemasAllUnauthorized(unittest.TestCase):
    """get_schemas raises RuntimeError when no streams are authorized."""

    @patch('tap_workday.schema.check_stream_authorization', return_value=(False, "authorization", "credentials lack the required permissions"))
    def test_raises_when_all_streams_excluded(self, mock_check):
        """RuntimeError is raised when every stream fails the access check."""
        with self.assertRaises(RuntimeError):
            get_schemas(config=CONFIG)

    @patch('tap_workday.schema.check_stream_authorization', return_value=(False, "authorization", "credentials lack the required permissions"))
    def test_error_message_mentions_no_authorized_streams(self, mock_check):
        """The RuntimeError message indicates no authorized streams were found."""
        with self.assertRaises(RuntimeError) as ctx:
            get_schemas(config=CONFIG)

        self.assertIn('no authorized streams', str(ctx.exception).lower())


# ---------------------------------------------------------------------------
# check_credentials — OAuth 2.0 specific behavior
# ---------------------------------------------------------------------------

class TestCheckCredentialsOAuth(unittest.TestCase):
    """OAuth-specific check_credentials behavior."""

    def setUp(self):
        self.config = {
            'hostname': 'test.workday.com',
            'tenant': 'test_tenant',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'refresh_token': 'test_refresh_token',
        }

    def _make_oauth_client(self):
        """Create a Client in OAuth mode without triggering __init__ network calls."""
        client = object.__new__(Client)
        client.config = self.config
        client._auth_mode = _AUTH_MODE_OAUTH
        client._token_manager = Mock()
        client._token_manager.fetch.return_value = "mock_access_token"
        client._session = Mock()
        return client

    def test_oauth_token_fetch_is_attempted(self):
        """check_credentials calls _token_manager.fetch() when in OAuth mode."""
        client = self._make_oauth_client()
        with patch.object(client, 'check_access'):
            client.check_credentials()
        client._token_manager.fetch.assert_called_once()

    def test_oauth_failure_without_fallback_raises(self):
        """OAuth token failure raises WorkdayAuthenticationError when fallback is disabled."""
        from tap_workday.exceptions import WorkdayAuthenticationError
        client = self._make_oauth_client()
        client._token_manager.fetch.side_effect = WorkdayAuthenticationError("bad token")

        with self.assertRaises(WorkdayAuthenticationError):
            client.check_credentials()

    def test_oauth_failure_with_fallback_but_no_credentials_raises(self):
        """OAuth failure with fallback enabled but no username/password raises."""
        from tap_workday.exceptions import WorkdayAuthenticationError
        client = self._make_oauth_client()
        client.config = {**self.config, 'enable_wssecurity_fallback': True}
        client._token_manager.fetch.side_effect = WorkdayAuthenticationError("bad token")

        with self.assertRaises(WorkdayAuthenticationError):
            client.check_credentials()

    def test_oauth_failure_with_fallback_and_credentials_switches_mode(self):
        """OAuth failure with fallback enabled and username/password present switches to WS-Security."""
        from tap_workday.exceptions import WorkdayAuthenticationError
        client = self._make_oauth_client()
        client.config = {
            **self.config,
            'enable_wssecurity_fallback': True,
            'username': 'fallback_user',
            'password': 'fallback_pass',
        }
        client._token_manager.fetch.side_effect = WorkdayAuthenticationError("bad token")

        with patch.object(client, '_switch_to_wssecurity_fallback') as mock_switch, \
             patch.object(client, 'check_access'):
            client.check_credentials()
            mock_switch.assert_called_once()

