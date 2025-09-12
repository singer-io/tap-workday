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

from tap_workday.client import DefaultValues, SOAPErrorHandler, Client
from tap_workday.exceptions import (
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

    def test_get_exception_details_fault_error(self):
        """Test _get_exception_details for Fault exception."""
        exception = Fault("Server Error", "SOAP-ENV:Server", None)
        result = SOAPErrorHandler._get_exception_details(exception)
        self.assertIn("faultcode='SOAP-ENV:Server'", result)
        self.assertIn("faultstring='Server Error'", result)

    def test_get_exception_details_transport_error(self):
        """Test _get_exception_details for TransportError exception."""
        exception = TransportError("HTTP 500 Error")
        result = SOAPErrorHandler._get_exception_details(exception)
        self.assertIn("status_code=0", result)
        self.assertIn("message='HTTP 500 Error'", result)

    def test_get_exception_details_xml_error(self):
        """Test _get_exception_details for XMLSyntaxError exception."""
        exception = XMLSyntaxError("Invalid XML")
        result = SOAPErrorHandler._get_exception_details(exception)
        self.assertIn("Invalid SOAP XML response: Invalid XML", result)

    def test_get_exception_details_generic_error(self):
        """Test _get_exception_details for generic exception."""
        exception = ValueError("Generic error")
        result = SOAPErrorHandler._get_exception_details(exception)
        self.assertIn("Exception=Generic error", result)

    def test_get_error_message_fault_error(self):
        """Test _get_error_message for Fault exception."""
        exception = Fault("Server Error", "SOAP-ENV:Server", None)
        result = SOAPErrorHandler._get_error_message(self.operation_name, exception)
        expected = "SOAP Fault in 'test_operation': Server Error"
        self.assertEqual(result, expected)

    def test_get_error_message_transport_error(self):
        """Test _get_error_message for TransportError exception."""
        exception = TransportError("HTTP 500 Error")
        result = SOAPErrorHandler._get_error_message(self.operation_name, exception)
        expected = "Transport error in 'test_operation': HTTP 500 Error"
        self.assertEqual(result, expected)

    def test_get_error_message_xml_error(self):
        """Test _get_error_message for XMLSyntaxError exception."""
        exception = XMLSyntaxError("Invalid XML")
        result = SOAPErrorHandler._get_error_message(self.operation_name, exception)
        expected = "Invalid SOAP XML in 'test_operation': Invalid XML"
        self.assertEqual(result, expected)

    def test_get_error_message_generic_error(self):
        """Test _get_error_message for generic exception."""
        exception = ValueError("Generic error")
        result = SOAPErrorHandler._get_error_message(self.operation_name, exception)
        expected = "Unexpected error in 'test_operation': Generic error"
        self.assertEqual(result, expected)

    @patch('tap_workday.client.LOGGER')
    def test_handle_error_fault_error(self, mock_logger):
        """Test handle_error with Fault exception."""
        exception = Fault("code", "message", None)
        with self.assertRaises(WorkdaySOAPFaultError) as context:
            SOAPErrorHandler.handle_error(self.operation_name, exception)
        self.assertIs(context.exception.__cause__, exception)
        mock_logger.error.assert_called_once()

    @patch('tap_workday.client.LOGGER')
    def test_handle_error_transport_error(self, mock_logger):
        """Test handle_error with TransportError exception."""
        exception = TransportError("transport error")
        with self.assertRaises(WorkdaySOAPTransportError) as context:
            SOAPErrorHandler.handle_error(self.operation_name, exception)
        self.assertIs(context.exception.__cause__, exception)
        mock_logger.error.assert_called_once()

    @patch('tap_workday.client.LOGGER')
    def test_handle_error_xml_error(self, mock_logger):
        """Test handle_error with XMLSyntaxError exception."""
        exception = XMLSyntaxError("xml error")
        with self.assertRaises(WorkdaySOAPXMLSyntaxError) as context:
            SOAPErrorHandler.handle_error(self.operation_name, exception)
        self.assertIs(context.exception.__cause__, exception)
        mock_logger.error.assert_called_once()

    @patch('tap_workday.client.LOGGER')
    def test_handle_error_unexpected_error(self, mock_logger):
        """Test handle_error with unexpected exception."""
        exception = ValueError("unexpected error")
        with self.assertRaises(WorkdaySOAPUnexpectedError) as context:
            SOAPErrorHandler.handle_error(self.operation_name, exception)
        self.assertIs(context.exception.__cause__, exception)
        mock_logger.error.assert_called_once()

    @patch('tap_workday.client.LOGGER')
    def test_handle_error_runtime_error(self, mock_logger):
        """Test handle_error with runtime exception."""
        exception = RuntimeError("runtime error")
        with self.assertRaises(WorkdaySOAPUnexpectedError) as context:
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
        }
        self.mock_zeep_client = Mock(spec=ZeepClient)
        self.mock_zeep_client.service = Mock()

    def test_client_initialization_defaults(self):
        """Test Client initialization with default parameters."""
        with patch('tap_workday.client.Client._create_client'):
            client = Client(self.base_config)
            self.assertEqual(client.config, self.base_config)
            self.assertEqual(client.service, "Human_Resources")
            self.assertEqual(client.version, "v45.0")
            self.assertEqual(client.request_timeout, 300.0)

    def test_client_initialization_custom_service(self):
        """Test Client initialization with custom service."""
        with patch('tap_workday.client.Client._create_client'):
            client = Client(self.base_config, service="Custom_Service")
            self.assertEqual(client.service, "Custom_Service")
            self.assertEqual(client.version, "v45.0")

    def test_client_initialization_custom_version(self):
        """Test Client initialization with custom version."""
        with patch('tap_workday.client.Client._create_client'):
            client = Client(self.base_config, version="v50.0")
            self.assertEqual(client.service, "Human_Resources")
            self.assertEqual(client.version, "v50.0")

    def test_client_initialization_custom_timeout(self):
        """Test Client initialization with custom timeout."""
        config = {**self.base_config, "request_timeout": 600}
        with patch('tap_workday.client.Client._create_client'):
            client = Client(config)
            self.assertEqual(client.request_timeout, 600.0)

    def test_client_initialization_string_timeout(self):
        """Test Client initialization with string timeout."""
        config = {**self.base_config, "request_timeout": "120"}
        with patch('tap_workday.client.Client._create_client'):
            client = Client(config)
            self.assertEqual(client.request_timeout, 120.0)

    @patch('tap_workday.client.ZeepClient')
    @patch('tap_workday.client.Transport')
    @patch('tap_workday.client.requests.Session')
    @patch('tap_workday.client.UsernameToken')
    def test_create_client(self, mock_username_token, mock_session, mock_transport, mock_zeep_client):
        """Test _create_client method creates proper ZeepClient instance."""
        # Setup mocks
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_transport_instance = Mock()
        mock_transport.return_value = mock_transport_instance
        mock_username_token_instance = Mock()
        mock_username_token.return_value = mock_username_token_instance
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
        
        # Verify username token setup
        mock_username_token.assert_called_once_with("test_user", "test_pass")
        
        # Verify ZeepClient setup
        mock_zeep_client.assert_called_once_with(
            wsdl='test_wsdl_url',
            wsse=mock_username_token_instance,
            transport=mock_transport_instance
        )
        
        self.assertEqual(client._client, mock_zeep_client_instance)

    @patch('tap_workday.client.Client._create_client')
    def test_build_wsdl_url(self, mock_create_client):
        """Test _build_wsdl_url generates correct WSDL URLs."""
        test_cases = [
            ("test.workday.com", "test_tenant", "Human_Resources", "v45.0",
             "https://test.workday.com/ccx/service/test_tenant/Human_Resources/v45.0?wsdl"),
            ("prod.workday.com", "prod_tenant", "Financial_Management", "v50.0",
             "https://prod.workday.com/ccx/service/prod_tenant/Financial_Management/v50.0?wsdl"),
            ("impl.workday.com", "impl_tenant", "Staffing", "v44.0",
             "https://impl.workday.com/ccx/service/impl_tenant/Staffing/v44.0?wsdl"),
        ]
        
        for hostname, tenant, service, version, expected_url in test_cases:
            with self.subTest(hostname=hostname, tenant=tenant, service=service, version=version):
                config = {
                    **self.base_config,
                    "hostname": hostname,
                    "tenant": tenant,
                }
                
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

    @patch('tap_workday.client.Client._create_client')
    def test_call_successful_operation(self, mock_create_client):
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

    def test_call_error_handling_fault_error(self):
        """Test that call method properly delegates Fault error handling to SOAPErrorHandler."""
        with patch('tap_workday.client.Client._create_client') as mock_create_client:
            with patch('tap_workday.client.SOAPErrorHandler.handle_error') as mock_handle_error:
                mock_create_client.return_value = self.mock_zeep_client
                exception_to_raise = Fault("code", "message", None)
                self.mock_zeep_client.service.test_operation.side_effect = exception_to_raise
                mock_handle_error.side_effect = WorkdaySOAPFaultError("Mocked error")
                
                client = Client(self.base_config)
                
                with self.assertRaises(WorkdaySOAPFaultError):
                    client.call("test_operation")
                
                # Should be called MAX_RETRIES times due to backoff (Fault is retryable)
                self.assertEqual(mock_handle_error.call_count, DefaultValues.MAX_RETRIES.value)
                mock_handle_error.assert_called_with("test_operation", exception_to_raise)

    def test_call_error_handling_transport_error(self):
        """Test that call method properly delegates TransportError error handling to SOAPErrorHandler."""
        with patch('tap_workday.client.Client._create_client') as mock_create_client:
            with patch('tap_workday.client.SOAPErrorHandler.handle_error') as mock_handle_error:
                mock_create_client.return_value = self.mock_zeep_client
                exception_to_raise = TransportError("transport error")
                self.mock_zeep_client.service.test_operation.side_effect = exception_to_raise
                mock_handle_error.side_effect = WorkdaySOAPTransportError("Mocked error")
                
                client = Client(self.base_config)
                
                with self.assertRaises(WorkdaySOAPTransportError):
                    client.call("test_operation")
                
                # Should be called MAX_RETRIES times due to backoff (TransportError is retryable)
                self.assertEqual(mock_handle_error.call_count, DefaultValues.MAX_RETRIES.value)
                mock_handle_error.assert_called_with("test_operation", exception_to_raise)

    def test_call_error_handling_xml_error(self):
        """Test that call method properly delegates XMLSyntaxError error handling to SOAPErrorHandler."""
        with patch('tap_workday.client.Client._create_client') as mock_create_client:
            with patch('tap_workday.client.SOAPErrorHandler.handle_error') as mock_handle_error:
                mock_create_client.return_value = self.mock_zeep_client
                exception_to_raise = XMLSyntaxError("xml error")
                self.mock_zeep_client.service.test_operation.side_effect = exception_to_raise
                mock_handle_error.side_effect = WorkdaySOAPXMLSyntaxError("Mocked error")
                
                client = Client(self.base_config)
                
                with self.assertRaises(WorkdaySOAPXMLSyntaxError):
                    client.call("test_operation")
                
                # Should be called MAX_RETRIES times due to backoff (XMLSyntaxError is retryable)
                self.assertEqual(mock_handle_error.call_count, DefaultValues.MAX_RETRIES.value)
                mock_handle_error.assert_called_with("test_operation", exception_to_raise)

    def test_call_error_handling_unexpected_error(self):
        """Test that call method properly delegates unexpected error handling to SOAPErrorHandler."""
        with patch('tap_workday.client.Client._create_client') as mock_create_client:
            with patch('tap_workday.client.SOAPErrorHandler.handle_error') as mock_handle_error:
                mock_create_client.return_value = self.mock_zeep_client
                exception_to_raise = ValueError("unexpected")
                self.mock_zeep_client.service.test_operation.side_effect = exception_to_raise
                mock_handle_error.side_effect = WorkdaySOAPUnexpectedError("Mocked error")
                
                client = Client(self.base_config)
                
                with self.assertRaises(WorkdaySOAPUnexpectedError):
                    client.call("test_operation")
                
                # Should be called only once (ValueError is not retryable)
                mock_handle_error.assert_called_once_with("test_operation", exception_to_raise)

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

    @patch('tap_workday.client.Client._create_client')
    def test_call_backoff_retry_logic(self, mock_create_client):
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

    @patch('tap_workday.client.Client._create_client')
    def test_call_max_retries_exceeded(self, mock_create_client):
        """Test that max retries are respected and final exception is raised."""
        # Setup
        mock_create_client.return_value = self.mock_zeep_client
        
        # Configure mock to always fail with retryable SOAP exception
        persistent_error = Fault("Persistent Error", "SOAP-ENV:Server", None)
        self.mock_zeep_client.service.test_operation.side_effect = persistent_error
        
        client = Client(self.base_config)
        
        # Execute and verify max retries exceeded
        # Since Fault is retryable, backoff will convert it to WorkdaySOAPFaultError after max tries
        with self.assertRaises(WorkdaySOAPFaultError):
            client.call("test_operation")
        
        # Should be called MAX_RETRIES times (5)
        self.assertEqual(self.mock_zeep_client.service.test_operation.call_count, 
                        DefaultValues.MAX_RETRIES.value)

    @patch('tap_workday.client.Client._create_client')
    def test_call_non_retryable_exception_no_retry(self, mock_create_client):
        """Test that non-retryable exceptions are not retried."""
        # Setup
        mock_create_client.return_value = self.mock_zeep_client
        
        # Configure mock to raise non-retryable exception
        non_retryable_error = KeyError("Non-retryable error")
        self.mock_zeep_client.service.test_operation.side_effect = non_retryable_error
        
        with patch('tap_workday.client.SOAPErrorHandler.handle_error') as mock_handle_error:
            mock_handle_error.side_effect = WorkdaySOAPUnexpectedError("Handled error")
            
            client = Client(self.base_config)
            
            # Execute and verify no retries
            with self.assertRaises(WorkdaySOAPUnexpectedError):
                client.call("test_operation")
            
            # Should only be called once (no retries)
            self.assertEqual(self.mock_zeep_client.service.test_operation.call_count, 1)


if __name__ == '__main__':
    unittest.main()
