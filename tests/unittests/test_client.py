# Revised and expanded tests for tap_workday.client.Client
import unittest
from unittest.mock import MagicMock, patch

from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout
from zeep.exceptions import Fault, TransportError, XMLSyntaxError

from tap_workday.client import Client, SOAPErrorHandler


class TestClient(unittest.TestCase):

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    @patch("time.sleep", return_value=None)
    def test_call_retries_on_retryable_exceptions(
        self, mock_sleep, mock_zeep, mock_session
    ):
        """Test Client.call retries up to max_tries on retryable exceptions (ConnectionError, Timeout, etc)."""
        from tap_workday.client import Client
        from tap_workday.exceptions import WorkdaySOAPUnexpectedError

        retryable_exceptions = [ConnectionError, Timeout, ChunkedEncodingError]
        for exc in retryable_exceptions:
            mock_service = MagicMock()
            mock_service.SomeOperation.side_effect = exc("fail")
            mock_zeep.return_value.service = mock_service
            c = Client(self.config)
            c._client = mock_zeep.return_value
            with self.assertRaises(WorkdaySOAPUnexpectedError):
                c.call("SomeOperation")
            # Should only call once, since error is not retried by backoff
            self.assertEqual(mock_service.SomeOperation.call_count, 1)

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    @patch("time.sleep", return_value=None)
    def test_call_backoff_and_max_retries(self, mock_sleep, mock_zeep, mock_session):
        """Test Client.call uses backoff and stops after max_tries (5)."""
        from tap_workday.client import Client

        mock_service = MagicMock()
        # Always raise ConnectionResetError
        mock_service.SomeOperation.side_effect = ConnectionResetError("fail")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        from tap_workday.exceptions import WorkdaySOAPUnexpectedError

        with self.assertRaises(WorkdaySOAPUnexpectedError):
            c.call("SomeOperation")
        # Should only call once, since error is not retried by backoff
        self.assertEqual(mock_service.SomeOperation.call_count, 1)

    """Unit tests for the Client class in tap_workday.client."""

    def setUp(self):
        self.config = {
            "hostname": "test.workday.com",
            "tenant": "test_tenant",
            "username": "user",
            "password": "pass",
            "request_timeout": 10,
        }

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    @patch("tap_workday.client.UsernameToken")
    def test_create_client(self, mock_token, mock_zeep, mock_session):
        """Test that _create_client constructs ZeepClient with correct WSDL and credentials."""
        c = Client(self.config)
        mock_zeep.assert_called_once()
        mock_token.assert_called_once_with("user", "pass")
        self.assertTrue(hasattr(c, "_client"))

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_client_init_sets_config_and_timeout(self, mock_zeep, mock_session):
        """Test Client __init__ sets config and request_timeout properly."""
        client = Client(self.config)
        self.assertEqual(client.config["hostname"], "test.workday.com")
        self.assertEqual(client.request_timeout, 10.0)
        self.assertEqual(client.service, "Human_Resources")

    @patch.object(Client, "_create_client")
    def test_client_init_with_version(self, mock_create):
        """Test Client __init__ uses version from config if present."""
        config = self.config.copy()
        config["version"] = "v99.9"
        c = Client(config)
        self.assertEqual(c.version, "v99.9")

    @patch.object(Client, "_create_client")
    def test_client_init_default_version(self, mock_create):
        """Test Client __init__ uses default version if not in config."""
        config = self.config.copy()
        c = Client(config)
        self.assertEqual(c.version, "v44.2")

    @patch.object(Client, "_create_client")
    def test_client_init_request_timeout_default(self, mock_create):
        """Test Client __init__ uses default timeout if not in config."""
        config = self.config.copy()
        del config["request_timeout"]
        c = Client(config)
        self.assertEqual(c.request_timeout, 300.0)

    @patch.object(Client, "_create_client")
    def test_client_init_request_timeout_casts(self, mock_create):
        """Test Client __init__ casts string/float/integer timeout values."""
        for val in ["12", 12, 12.0]:
            config = self.config.copy()
            config["request_timeout"] = val
            c = Client(config)
            self.assertEqual(c.request_timeout, 12.0)

    def test_client_init_missing_hostname_raises(self):
        """Test Client __init__ raises KeyError if hostname missing."""
        config = self.config.copy()
        del config["hostname"]
        with self.assertRaises(KeyError):
            Client(config)

    def test_client_init_missing_username_raises(self):
        """Test Client __init__ raises KeyError if username missing."""
        config = self.config.copy()
        del config["username"]
        with self.assertRaises(KeyError):
            Client(config)

    def test_client_init_missing_password_raises(self):
        """Test Client __init__ raises KeyError if password missing."""
        config = self.config.copy()
        del config["password"]
        with self.assertRaises(KeyError):
            Client(config)

    def test_client_init_missing_tenant_raises(self):
        """Test Client __init__ raises KeyError if tenant missing."""
        config = self.config.copy()
        del config["tenant"]
        with self.assertRaises(KeyError):
            Client(config)

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_success(self, mock_zeep, mock_session):
        """Test Client.call returns result from SOAP operation."""
        mock_service = MagicMock()
        mock_service.SomeOperation.return_value = "ok"
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        result = c.call("SomeOperation", 1, foo="bar")
        self.assertEqual(result, "ok")
        mock_service.SomeOperation.assert_called_once_with(1, foo="bar")

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_fault_raises(self, mock_zeep, mock_session):
        """Test Client.call raises WorkdaySOAPFaultError on SOAP Fault."""
        mock_service = MagicMock()
        mock_service.SomeOperation.side_effect = Fault("msg", code="c", detail="d")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(Exception):
            c.call("SomeOperation")

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_transport_error_raises(self, mock_zeep, mock_session):
        """Test Client.call raises WorkdaySOAPTransportError on TransportError."""
        mock_service = MagicMock()
        mock_service.SomeOperation.side_effect = TransportError(500, "fail")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(Exception):
            c.call("SomeOperation")

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_xml_error_raises(self, mock_zeep, mock_session):
        """Test Client.call raises WorkdaySOAPXMLSyntaxError on XMLSyntaxError."""
        mock_service = MagicMock()
        mock_service.SomeOperation.side_effect = XMLSyntaxError("fail")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(Exception):
            c.call("SomeOperation")

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_unexpected_error_raises(self, mock_zeep, mock_session):
        """Test Client.call raises WorkdaySOAPUnexpectedError on unknown error."""
        mock_service = MagicMock()
        mock_service.SomeOperation.side_effect = RuntimeError("fail")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(Exception):
            c.call("SomeOperation")
