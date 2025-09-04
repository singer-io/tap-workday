"""
Unit tests for tap_workday.client.Client and SOAPErrorHandler.
Covers initialization, error handling, retry logic, and edge cases.
"""

import unittest
from unittest.mock import MagicMock, patch


from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout
from zeep.exceptions import Fault, TransportError, XMLSyntaxError
from parameterized import parameterized

from tap_workday.client import Client
from tap_workday.exceptions import WorkdaySOAPUnexpectedError


# Patch backoff.expo and time.sleep globally for all tests
def _instant_expo(*args, **kwargs):
    # Always yield 0 (no sleep)
    while True:
        yield 0


patcher_expo = patch("backoff.expo", _instant_expo)
patcher_sleep = patch("time.sleep", lambda x: None)
patcher_expo.start()
patcher_sleep.start()


class TestClient(unittest.TestCase):
    """Unit tests for the Workday SOAP Client abstraction."""

    def setUp(self):
        """Set up a valid config for each test."""
        self.config = {
            "hostname": "test.workday.com",
            "tenant": "test_tenant",
            "username": "user",
            "password": "pass",
            "request_timeout": 10,
        }

    @parameterized.expand([
        (ConnectionError,),
        (Timeout,),
        (ChunkedEncodingError,),
        (Fault,),
        (TransportError,),
        (XMLSyntaxError,),
        (ConnectionResetError,),
    ])
    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_retries_on_retryable_exceptions(self, exc_type, mock_zeep, mock_session):
        """
        Test that Client.call retries up to max_tries on retryable exceptions and raises the original exception.
        Covers all retryable exceptions including SOAP and requests errors.
        """
        mock_service = MagicMock()
        # Fault and TransportError require special args
        if exc_type is Fault:
            mock_service.SomeOperation.side_effect = Fault("msg", code="c", detail="d")
        elif exc_type is TransportError:
            mock_service.SomeOperation.side_effect = TransportError(500, "fail")
        elif exc_type is XMLSyntaxError:
            mock_service.SomeOperation.side_effect = XMLSyntaxError("fail")
        else:
            mock_service.SomeOperation.side_effect = exc_type("fail")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(exc_type):
            c.call("SomeOperation")
        self.assertEqual(mock_service.SomeOperation.call_count, 5)

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_backoff_and_max_retries(self, mock_zeep, mock_session):
        """
        Test that Client.call uses backoff and stops after max_tries (5) for ConnectionResetError, raising the original exception.
        """
        mock_service = MagicMock()
        mock_service.SomeOperation.side_effect = ConnectionResetError("fail")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(ConnectionResetError):
            c.call("SomeOperation")
        self.assertEqual(mock_service.SomeOperation.call_count, 5)


    @parameterized.expand([
        ("operation_not_found", AttributeError, "SomeOperation"),
        ("service_not_found", AttributeError, "service"),
        ("unexpected_runtime_error", RuntimeError, None),
    ])
    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_unexpected_errors(self, case, exc_type, missing_attr, mock_zeep, mock_session):
        """
        Test that Client.call raises WorkdaySOAPUnexpectedError on non-retryable/unexpected errors.
        Covers missing operation, missing service, and unknown runtime error.
        """
        mock_service = MagicMock()
        if case == "operation_not_found":
            delattr(mock_service, "SomeOperation")
            mock_zeep.return_value.service = mock_service
        elif case == "service_not_found":
            mock_zeep.return_value = MagicMock()
            delattr(mock_zeep.return_value, "service")
        elif case == "unexpected_runtime_error":
            mock_service.SomeOperation.side_effect = RuntimeError("fail")
            mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(WorkdaySOAPUnexpectedError):
            c.call("SomeOperation")

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_service_not_found(self, mock_zeep, mock_session):
        """
        Test that calling with a ZeepClient missing 'service' raises WorkdaySOAPUnexpectedError.
        """
        mock_zeep.return_value = MagicMock()
        delattr(mock_zeep.return_value, "service")
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(WorkdaySOAPUnexpectedError):
            c.call("SomeOperation")

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    @patch("tap_workday.client.UsernameToken", side_effect=Exception("token fail"))
    def test_create_client_token_failure(self, mock_token, mock_zeep, mock_session):
        """
        Test that _create_client raises if UsernameToken fails.
        """
        with self.assertRaises(Exception):
            Client(self.config)

    @patch("tap_workday.client.requests.Session", side_effect=Exception("session fail"))
    def test_create_client_session_failure(self, mock_session):
        """
        Test that _create_client raises if requests.Session fails.
        """
        with self.assertRaises(Exception):
            Client(self.config)

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient", side_effect=Exception("wsdl fail"))
    def test_create_client_wsdl_failure(self, mock_zeep, mock_session):
        """
        Test that _create_client raises if ZeepClient fails (e.g., invalid WSDL).
        """
        with self.assertRaises(Exception):
            Client(self.config)

    def test_client_init_invalid_timeout(self):
        """
        Test that Client __init__ raises ValueError if request_timeout is not castable to float.
        """
        config = self.config.copy()
        config["request_timeout"] = "not_a_number"
        with self.assertRaises(ValueError):
            Client(config)

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    @patch("tap_workday.client.UsernameToken")
    def test_create_client(self, mock_token, mock_zeep, mock_session):
        """
        Test that _create_client constructs ZeepClient with correct WSDL and credentials.
        """
        c = Client(self.config)
        mock_zeep.assert_called_once()
        mock_token.assert_called_once_with("user", "pass")
        self.assertTrue(hasattr(c, "_client"))

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_client_init_sets_config_and_timeout(self, mock_zeep, mock_session):
        """
        Test Client __init__ sets config and request_timeout properly.
        """
        client = Client(self.config)
        self.assertEqual(client.config["hostname"], "test.workday.com")
        self.assertEqual(client.request_timeout, 10.0)
        self.assertEqual(client.service, "Human_Resources")

    @patch.object(Client, "_create_client")
    def test_client_init_with_version(self, mock_create):
        """
        Test Client __init__ uses version from config if present.
        """
        config = self.config.copy()
        config["version"] = "v99.9"
        c = Client(config)
        self.assertEqual(c.version, "v99.9")

    @patch.object(Client, "_create_client")
    def test_client_init_default_version(self, mock_create):
        """
        Test Client __init__ uses default version if not in config.
        """
        config = self.config.copy()
        c = Client(config)
        self.assertEqual(c.version, "v44.2")

    @patch.object(Client, "_create_client")
    def test_client_init_request_timeout_default(self, mock_create):
        """
        Test Client __init__ uses default timeout if not in config.
        """
        config = self.config.copy()
        del config["request_timeout"]
        c = Client(config)
        self.assertEqual(c.request_timeout, 300.0)

    @patch.object(Client, "_create_client")
    def test_client_init_request_timeout_casts(self, mock_create):
        """
        Test Client __init__ casts string/float/integer timeout values.
        """
        for val in ["12", 12, 12.0]:
            config = self.config.copy()
            config["request_timeout"] = val
            c = Client(config)
            self.assertEqual(c.request_timeout, 12.0)

    def test_client_init_missing_hostname_raises(self):
        """
        Test Client __init__ raises KeyError if hostname missing.
        """
        config = self.config.copy()
        del config["hostname"]
        with self.assertRaises(KeyError):
            Client(config)

    def test_client_init_missing_username_raises(self):
        """
        Test Client __init__ raises KeyError if username missing.
        """
        config = self.config.copy()
        del config["username"]
        with self.assertRaises(KeyError):
            Client(config)

    def test_client_init_missing_password_raises(self):
        """
        Test Client __init__ raises KeyError if password missing.
        """
        config = self.config.copy()
        del config["password"]
        with self.assertRaises(KeyError):
            Client(config)

    def test_client_init_missing_tenant_raises(self):
        """
        Test Client __init__ raises KeyError if tenant missing.
        """
        config = self.config.copy()
        del config["tenant"]
        with self.assertRaises(KeyError):
            Client(config)

    @parameterized.expand([
        ("ok", "ok"),
        ("empty", None),
        ("dict", {"foo": "bar"}),
        ("list", [1, 2, 3]),
    ])
    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_success(self, return_case, return_value, mock_zeep, mock_session):
        """
        Test Client.call returns result from SOAP operation for various return types.
        """
        mock_service = MagicMock()
        mock_service.SomeOperation.return_value = return_value
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        result = c.call("SomeOperation", 1, foo="bar")
        self.assertEqual(result, return_value)
        mock_service.SomeOperation.assert_called_once_with(1, foo="bar")

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_fault_raises(self, mock_zeep, mock_session):
        """
        Test Client.call raises Fault after retries on SOAP Fault (retryable).
        """
        mock_service = MagicMock()
        mock_service.SomeOperation.side_effect = Fault("msg", code="c", detail="d")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(Fault):
            c.call("SomeOperation")

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_transport_error_raises(self, mock_zeep, mock_session):
        """
        Test Client.call raises TransportError after retries (retryable).
        """
        mock_service = MagicMock()
        mock_service.SomeOperation.side_effect = TransportError(500, "fail")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(TransportError):
            c.call("SomeOperation")

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_xml_error_raises(self, mock_zeep, mock_session):
        """
        Test Client.call raises XMLSyntaxError after retries (retryable).
        """
        mock_service = MagicMock()
        mock_service.SomeOperation.side_effect = XMLSyntaxError("fail")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(XMLSyntaxError):
            c.call("SomeOperation")

    @patch("tap_workday.client.requests.Session")
    @patch("tap_workday.client.ZeepClient")
    def test_call_unexpected_error_raises(self, mock_zeep, mock_session):
        """
        Test Client.call raises WorkdaySOAPUnexpectedError on unknown error.
        """
        mock_service = MagicMock()
        mock_service.SomeOperation.side_effect = RuntimeError("fail")
        mock_zeep.return_value.service = mock_service
        c = Client(self.config)
        c._client = mock_zeep.return_value
        with self.assertRaises(WorkdaySOAPUnexpectedError):
            c.call("SomeOperation")
