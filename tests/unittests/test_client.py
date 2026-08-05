"""
Comprehensive unit tests for tap_workday.client module.

Tests all classes and methods in client.py including DefaultValues enum,
SOAPErrorHandler error handling, and Client SOAP operations with backoff logic.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from parameterized import parameterized

import requests
from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout
from zeep import Client as ZeepClient
from zeep.exceptions import Fault, TransportError, XMLSyntaxError
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken

from tap_workday.client import DefaultValues, SOAPErrorHandler, Client, WorkdayOAuthTokenManager
from tap_workday.exceptions import (
    WorkdayAuthenticationError,
    WorkdayBackoffError,
    WorkdaySOAPFaultError,
    WorkdaySOAPTransportError,
    WorkdaySOAPUnexpectedError,
    WorkdaySOAPXMLSyntaxError,
)


class TestDefaultValues(unittest.TestCase):
    """Test the DefaultValues enum constants."""

    def test_default_values_constants(self):
        """Test that all default values are set correctly."""
        self.assertEqual(DefaultValues.REQUEST_TIMEOUT.value, 300)
        self.assertEqual(DefaultValues.SERVICE.value, "Human_Resources")
        self.assertEqual(DefaultValues.VERSION.value, "v45.0")
        self.assertEqual(DefaultValues.MAX_RETRIES.value, 5)
        self.assertEqual(DefaultValues.BACKOFF_FACTOR.value, 2)

    def test_default_values_are_enum_members(self):
        """Test that DefaultValues items are proper enum members."""
        self.assertIsInstance(DefaultValues.REQUEST_TIMEOUT, DefaultValues)
        self.assertIsInstance(DefaultValues.SERVICE, DefaultValues)
        self.assertIsInstance(DefaultValues.VERSION, DefaultValues)
        self.assertIsInstance(DefaultValues.MAX_RETRIES, DefaultValues)
        self.assertIsInstance(DefaultValues.BACKOFF_FACTOR, DefaultValues)


class TestSOAPErrorHandler(unittest.TestCase):
    """Test the SOAPErrorHandler static error handling methods."""

    def setUp(self):
        """Set up common test data."""
        self.operation_name = "test_operation"

    @parameterized.expand([
        # (exception_type, exception_instance, expected_details_fragment)
        ("fault", Fault("Server Error", "SOAP-ENV:Server", None), "faultcode='SOAP-ENV:Server'"),
        ("transport", TransportError("HTTP 500 Error"), "status_code=0"),
        ("xml", XMLSyntaxError("Invalid XML"), "Invalid SOAP XML response: Invalid XML"),
        ("generic", ValueError("Generic error"), "Exception=Generic error"),
    ])
    def test_get_exception_details(self, exception_type, exception, expected_fragment):
        """Test _get_exception_details returns proper formatted details."""
        result = SOAPErrorHandler._get_exception_details(exception)
        self.assertIn(expected_fragment, result)

    @parameterized.expand([
        # (exception_type, exception_instance, expected_message)
        ("fault", Fault("Server Error", "SOAP-ENV:Server", None), "SOAP Fault in 'test_operation': Server Error"),
        ("transport", TransportError("HTTP 500 Error"), "Transport error in 'test_operation': HTTP 500 Error"),
        ("xml", XMLSyntaxError("Invalid XML"), "Invalid SOAP XML in 'test_operation': Invalid XML"),
        ("generic", ValueError("Generic error"), "Unexpected error in 'test_operation': Generic error"),
    ])
    def test_get_error_message(self, exception_type, exception, expected_message):
        """Test _get_error_message generates correct formatted messages."""
        result = SOAPErrorHandler._get_error_message(self.operation_name, exception)
        self.assertEqual(result, expected_message)

    @parameterized.expand([
        # (exception_type, exception_instance, expected_workday_exception_class)
        ("fault", Fault("code", "message", None), WorkdaySOAPFaultError),
        ("transport", TransportError("transport error"), WorkdaySOAPTransportError),
        ("xml", XMLSyntaxError("xml error"), WorkdaySOAPXMLSyntaxError),
        ("value", ValueError("unexpected error"), WorkdaySOAPUnexpectedError),
        ("runtime", RuntimeError("runtime error"), WorkdaySOAPUnexpectedError),
    ])
    @patch('tap_workday.client.LOGGER')
    def test_handle_error_exception_mapping(self, exception_type, exception, expected_exception_class, mock_logger):
        """Test handle_error raises correct Workday exception types."""
        with self.assertRaises(expected_exception_class) as context:
            SOAPErrorHandler.handle_error(self.operation_name, exception)
        self.assertIs(context.exception.__cause__, exception)
        mock_logger.error.assert_called_once()

    @patch('tap_workday.client.LOGGER')
    def test_handle_error_logging_format(self, mock_logger):
        """Test handle_error logs with proper format."""
        test_exception = Fault("Test message", "TEST_CODE", "Test detail")
        
        with self.assertRaises(WorkdaySOAPFaultError):
            SOAPErrorHandler.handle_error(self.operation_name, test_exception)
        
        # Check log format
        logged_message = mock_logger.error.call_args[0][0]
        self.assertIn("[SOAP Fault]", logged_message)
        self.assertIn(f"Operation='{self.operation_name}'", logged_message)
        self.assertIn("faultcode='TEST_CODE'", logged_message)

    def test_exception_mappings_class_attribute(self):
        """Test that EXCEPTION_MAPPINGS contains expected mappings."""
        expected_mappings = {
            Fault: (WorkdaySOAPFaultError, "SOAP Fault"),
            TransportError: (WorkdaySOAPTransportError, "Transport Error"),
            XMLSyntaxError: (WorkdaySOAPXMLSyntaxError, "XML Error"),
        }
        self.assertEqual(SOAPErrorHandler.EXCEPTION_MAPPINGS, expected_mappings)


class TestClient(unittest.TestCase):
    """Test the Client SOAP client class."""

    def setUp(self):
        """Set up common test data and mocks."""
        self.base_config = {
            "hostname": "test.workday.com",
            "tenant": "test_tenant",
            "username": "test_user",
            "password": "test_pass",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "refresh_token": "test_refresh_token",
        }
        self.mock_zeep_client = Mock(spec=ZeepClient)
        self.mock_zeep_client.service = Mock()

        # Prevent real HTTP calls during OAuth token acquisition
        self._token_manager_patcher = patch('tap_workday.client.WorkdayOAuthTokenManager')
        self.mock_token_manager_class = self._token_manager_patcher.start()
        self.mock_token_manager = Mock()
        self.mock_token_manager.get.return_value = "mock_access_token"
        self.mock_token_manager_class.return_value = self.mock_token_manager

    def tearDown(self):
        self._token_manager_patcher.stop()

    @parameterized.expand([
        # (config_override, service, version, expected_service, expected_version, expected_timeout)
        ({}, None, None, "Human_Resources", "v45.0", 300.0),
        ({}, "Custom_Service", None, "Custom_Service", "v45.0", 300.0),
        ({}, None, "v50.0", "Human_Resources", "v50.0", 300.0),
        ({"request_timeout": 600}, None, None, "Human_Resources", "v45.0", 600.0),
        ({"request_timeout": "120"}, None, None, "Human_Resources", "v45.0", 120.0),
    ])
    @patch('tap_workday.client.Client._create_client')
    def test_client_initialization(self, config_override, service, version, 
                                 expected_service, expected_version, expected_timeout, mock_create_client):
        """Test Client initialization with various configurations."""
        config = {**self.base_config, **(config_override or {})}
        
        kwargs = {}
        if service is not None:
            kwargs['service'] = service
        if version is not None:
            kwargs['version'] = version
            
        client = Client(config, **kwargs)
        
        self.assertEqual(client.config, config)
        self.assertEqual(client.service, expected_service)
        self.assertEqual(client.version, expected_version)
        self.assertEqual(client.request_timeout, expected_timeout)
        mock_create_client.assert_called_once()

    @patch('tap_workday.client.ZeepClient')
    @patch('tap_workday.client.Transport')
    @patch('tap_workday.client.requests.Session')
    @patch('tap_workday.client.Settings')
    def test_create_client_oauth_mode(self, mock_settings, mock_session, mock_transport, mock_zeep_client):
        """Test _create_client in OAuth mode: Bearer token auth, no UsernameToken wsse."""
        mock_session_instance = Mock()
        mock_session_instance.headers = {}
        mock_session.return_value = mock_session_instance
        mock_transport_instance = Mock()
        mock_transport.return_value = mock_transport_instance
        mock_settings_instance = Mock()
        mock_settings.return_value = mock_settings_instance
        mock_zeep_client_instance = Mock(spec=ZeepClient)
        mock_zeep_client.return_value = mock_zeep_client_instance

        with patch.object(Client, '_build_wsdl_url', return_value='test_wsdl_url'):
            client = Client(self.base_config)

        # Verify session setup
        mock_session.assert_called_once()
        self.assertTrue(mock_session_instance.verify)

        # Verify transport setup
        mock_transport.assert_called_once_with(
            session=mock_session_instance,
            timeout=300.0
        )

        # Verify settings setup
        mock_settings.assert_called_once_with(strict=False, xml_huge_tree=True)

        # OAuth mode: wsse=None (no UsernameToken)
        mock_zeep_client.assert_called_once_with(
            wsdl='test_wsdl_url',
            wsse=None,
            transport=mock_transport_instance,
            settings=mock_settings_instance
        )

        self.assertEqual(client._client, mock_zeep_client_instance)

    @parameterized.expand([
        # (hostname, tenant, service, version, expected_url)
        ("test.workday.com", "test_tenant", "Human_Resources", "v45.0", 
         "https://test.workday.com/ccx/service/test_tenant/Human_Resources/v45.0?wsdl"),
        ("prod.workday.com", "prod_tenant", "Financial_Management", "v50.0", 
         "https://prod.workday.com/ccx/service/prod_tenant/Financial_Management/v50.0?wsdl"),
        ("impl.workday.com", "impl_tenant", "Staffing", "v44.0", 
         "https://impl.workday.com/ccx/service/impl_tenant/Staffing/v44.0?wsdl"),
    ])
    @patch('tap_workday.client.Client._create_client')
    def test_build_wsdl_url(self, hostname, tenant, service, version, expected_url, mock_create_client):
        """Test _build_wsdl_url generates correct WSDL URLs."""
        config = {**self.base_config, "hostname": hostname, "tenant": tenant}
        client = Client(config, service=service, version=version)
        result = client._build_wsdl_url()
        self.assertEqual(result, expected_url)

    def test_retryable_exceptions_constant(self):
        """Test that RETRYABLE_EXCEPTIONS contains expected exception types."""
        expected_exceptions = (
            ConnectionResetError,
            ConnectionError,
            ChunkedEncodingError,
            Timeout,
            WorkdayBackoffError,
            Fault,
            TransportError,
            XMLSyntaxError,
        )
        self.assertEqual(Client.RETRYABLE_EXCEPTIONS, expected_exceptions)

    @patch('tap_workday.client.Client._update_bearer_header')
    @patch('tap_workday.client.Client._create_client')
    def test_call_successful_operation(self, mock_create_client, mock_update_bearer_header):
        """Test successful SOAP operation call."""
        # Setup
        mock_create_client.return_value = self.mock_zeep_client
        expected_result = {"test": "result"}
        self.mock_zeep_client.service.test_operation.return_value = expected_result

        client = Client(self.base_config)

        # Execute
        result = client.call("test_operation", "arg1", "arg2", kwarg1="value1")

        # Verify
        self.assertEqual(result, expected_result)
        self.mock_zeep_client.service.test_operation.assert_called_once_with(
            "arg1", "arg2", kwarg1="value1"
        )

    @parameterized.expand([
        # (exception_type, exception_instance, expected_workday_exception, is_retryable)
        ("fault", Fault("code", "message", None), WorkdaySOAPFaultError, True),
        ("transport", TransportError("transport error"), WorkdaySOAPTransportError, True),
        ("xml", XMLSyntaxError("xml error"), WorkdaySOAPXMLSyntaxError, True),
        ("value", ValueError("unexpected"), WorkdaySOAPUnexpectedError, False),
    ])
    @patch('tap_workday.client.Client._update_bearer_header')
    @patch('tap_workday.client.Client._create_client')
    @patch('tap_workday.client.SOAPErrorHandler.handle_error')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_call_error_handling(self, exception_type, exception_to_raise, expected_workday_exception, is_retryable,
                               mock_sleep, mock_handle_error, mock_create_client, mock_update_bearer_header):
        """Test that call method properly delegates error handling to SOAPErrorHandler."""
        mock_create_client.return_value = self.mock_zeep_client
        self.mock_zeep_client.service.test_operation.side_effect = exception_to_raise
        mock_handle_error.side_effect = expected_workday_exception("Mocked error")
        
        client = Client(self.base_config)
        
        with self.assertRaises(expected_workday_exception):
            client.call("test_operation")
        
        if is_retryable:
            # Should be called MAX_RETRIES times due to backoff
            self.assertEqual(mock_handle_error.call_count, DefaultValues.MAX_RETRIES.value)
        else:
            # Should be called only once (not retryable)
            mock_handle_error.assert_called_once()
        
        mock_handle_error.assert_called_with("test_operation", exception_to_raise)

    @patch('tap_workday.client.Client._create_client')
    def test_call_backoff_decorator_configuration(self, mock_create_client):
        """Test that call method has proper backoff configuration."""
        mock_create_client.return_value = self.mock_zeep_client
        
        # Create a client to check that the decorator exists
        client = Client(self.base_config)
        
        # Check that the call method has the backoff decorator applied
        # We can verify this by checking if the method has the appropriate attributes
        # that backoff adds to decorated functions
        self.assertTrue(hasattr(client.call, '__wrapped__'), 
                       "call method should have backoff decorator applied")

    @patch('tap_workday.client.Client._update_bearer_header')
    @patch('tap_workday.client.Client._create_client')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_call_backoff_retry_logic(self, mock_sleep, mock_create_client, mock_update_bearer_header):
        """Test that retryable exceptions trigger backoff retries."""
        # Setup
        mock_create_client.return_value = self.mock_zeep_client
        
        # Configure mock to fail twice with retryable SOAP exceptions, then succeed
        # Using a list that will be consumed as side_effects
        call_results = [
            Fault("Server Error", "SOAP-ENV:Server", None),  # First call fails
            TransportError("Transport failed"),               # Second call fails  
            {"success": True}                                # Third call succeeds
        ]
        self.mock_zeep_client.service.test_operation.side_effect = call_results
        
        client = Client(self.base_config)
        
        # Execute - should succeed after 2 retries
        result = client.call("test_operation")
        
        # Verify success after retries
        self.assertEqual(result, {"success": True})
        self.assertEqual(self.mock_zeep_client.service.test_operation.call_count, 3)

    @parameterized.expand([
        # (test_case_name, should_exhaust_retries)
        ("max_retries_exhausted", True),
        ("non_retryable_no_retry", False),
    ])
    @patch('tap_workday.client.Client._update_bearer_header')
    @patch('tap_workday.client.Client._create_client')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_call_retry_scenarios(self, test_case_name, should_exhaust_retries, mock_sleep, mock_create_client, mock_update_bearer_header):
        """Test retry scenarios: max retries exhausted vs non-retryable exceptions."""
        # Setup
        mock_create_client.return_value = self.mock_zeep_client
        client = Client(self.base_config)
        
        if should_exhaust_retries:
            # Configure mock to always fail with retryable SOAP exception
            persistent_error = Fault("Persistent Error", "SOAP-ENV:Server", None)
            self.mock_zeep_client.service.test_operation.side_effect = persistent_error
            
            # Execute and verify max retries exceeded
            with self.assertRaises(WorkdaySOAPFaultError):
                client.call("test_operation")
            
            # Should be called MAX_RETRIES times (5)
            self.assertEqual(self.mock_zeep_client.service.test_operation.call_count, 
                            DefaultValues.MAX_RETRIES.value)
        else:
            # Configure mock to raise non-retryable exception
            non_retryable_error = KeyError("Non-retryable error")
            self.mock_zeep_client.service.test_operation.side_effect = non_retryable_error
            
            with patch('tap_workday.client.SOAPErrorHandler.handle_error') as mock_handle_error:
                mock_handle_error.side_effect = WorkdaySOAPUnexpectedError("Handled error")
                
                # Execute and verify no retries
                with self.assertRaises(WorkdaySOAPUnexpectedError):
                    client.call("test_operation")
                
                # Should only be called once (no retries)
                self.assertEqual(self.mock_zeep_client.service.test_operation.call_count, 1)


class TestWorkdayOAuthTokenManager(unittest.TestCase):
    """Tests for WorkdayOAuthTokenManager OAuth 2.0 token handling."""

    def setUp(self):
        self.config = {
            'hostname': 'test.workday.com',
            'tenant': 'test_tenant',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'refresh_token': 'test_refresh_token',
        }

    def test_init_derives_token_endpoint(self):
        """Token endpoint is derived from hostname and tenant when not explicitly set."""
        manager = WorkdayOAuthTokenManager(self.config)
        self.assertEqual(
            manager._token_endpoint,
            'https://test.workday.com/ccx/oauth2/test_tenant/token'
        )

    def test_init_uses_explicit_token_endpoint(self):
        """An explicit token_endpoint in config overrides the derived URL."""
        config = {**self.config, 'token_endpoint': 'https://custom.example.com/token'}
        manager = WorkdayOAuthTokenManager(config)
        self.assertEqual(manager._token_endpoint, 'https://custom.example.com/token')

    def test_is_valid_initially_false(self):
        """Token is not valid before any fetch."""
        manager = WorkdayOAuthTokenManager(self.config)
        self.assertFalse(manager.is_valid)

    @patch('tap_workday.client.requests.post')
    def test_fetch_success(self, mock_post):
        """Successful fetch stores access_token and marks it valid."""
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'access_token': 'new_token', 'expires_in': 3600}
        mock_post.return_value = mock_resp

        manager = WorkdayOAuthTokenManager(self.config)
        token = manager.fetch()

        self.assertEqual(token, 'new_token')
        mock_post.assert_called_once_with(
            'https://test.workday.com/ccx/oauth2/test_tenant/token',
            auth=('test_client_id', 'test_client_secret'),
            data={'grant_type': 'refresh_token', 'refresh_token': 'test_refresh_token'},
            timeout=30,
            verify=True,
        )

    @patch('tap_workday.client.requests.post')
    def test_fetch_401_raises_authentication_error(self, mock_post):
        """HTTP 401 from token endpoint raises WorkdayAuthenticationError."""
        mock_resp = Mock()
        mock_resp.status_code = 401
        mock_post.return_value = mock_resp

        manager = WorkdayOAuthTokenManager(self.config)
        with self.assertRaises(WorkdayAuthenticationError):
            manager.fetch()

    @patch('tap_workday.client.requests.post')
    def test_fetch_non_ok_response_raises_authentication_error(self, mock_post):
        """Non-OK HTTP responses from the token endpoint raise WorkdayAuthenticationError."""
        mock_resp = Mock()
        mock_resp.ok = False
        mock_resp.status_code = 500
        mock_resp.text = 'Internal server error'
        mock_post.return_value = mock_resp

        manager = WorkdayOAuthTokenManager(self.config)
        with self.assertRaises(WorkdayAuthenticationError):
            manager.fetch()

    @patch('tap_workday.client.requests.post')
    def test_fetch_network_error_raises_authentication_error(self, mock_post):
        """Network errors during token request raise WorkdayAuthenticationError."""
        mock_post.side_effect = requests.RequestException("Connection failed")

        manager = WorkdayOAuthTokenManager(self.config)
        with self.assertRaises(WorkdayAuthenticationError):
            manager.fetch()

    @patch('tap_workday.client.requests.post')
    def test_get_fetches_token_when_cache_is_empty(self, mock_post):
        """get() fetches a new token when none is cached."""
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'access_token': 'new_token', 'expires_in': 3600}
        mock_post.return_value = mock_resp

        manager = WorkdayOAuthTokenManager(self.config)
        token = manager.get()

        self.assertEqual(token, 'new_token')
        mock_post.assert_called_once()

    @patch('tap_workday.client.requests.post')
    def test_get_returns_cached_token_when_valid(self, mock_post):
        """get() returns the cached token without a network call when still valid."""
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'access_token': 'cached_token', 'expires_in': 3600}
        mock_post.return_value = mock_resp

        manager = WorkdayOAuthTokenManager(self.config)
        manager.fetch()        # populate the cache
        token = manager.get()  # should return cached value

        self.assertEqual(token, 'cached_token')
        mock_post.assert_called_once()  # no second network call

    @patch('tap_workday.client.requests.post')
    def test_get_refreshes_expired_token(self, mock_post):
        """get() fetches a fresh token when the cached one has expired."""
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'access_token': 'refreshed_token', 'expires_in': 3600}
        mock_post.return_value = mock_resp

        manager = WorkdayOAuthTokenManager(self.config)
        manager._access_token = 'old_token'
        manager._expires_at = 0.0  # already expired

        token = manager.get()
        self.assertEqual(token, 'refreshed_token')
        mock_post.assert_called_once()
