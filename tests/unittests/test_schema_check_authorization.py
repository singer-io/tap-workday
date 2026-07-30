"""
Unit tests for schema.py check_stream_authorization function.
"""

import unittest
from unittest.mock import Mock, patch
from tap_workday.schema import check_stream_authorization
from tap_workday.client import Client
from tap_workday.exceptions import WorkdaySOAPFaultError, WorkdaySOAPTransportError
from tap_workday.streams.financial_management import Ledgers


class TestSchemaCheckStreamAuthorization(unittest.TestCase):
    """Test the check_stream_authorization function with custom check_access methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'hostname': 'test.workday.com',
            'username': 'test_user',
            'password': 'test_pass',
            'tenant': 'test_tenant'
        }
        self.stream_name = "financial_management_ledgers"

    @patch('tap_workday.schema.Client')
    @patch.object(Ledgers, 'check_access')
    def test_uses_stream_custom_check_access_method(self, mock_ledgers_check_access, mock_client_class):
        """Test that check_stream_authorization uses stream's custom check_access method when available."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client

        result = check_stream_authorization(self.config, self.stream_name, Ledgers)

        mock_client_class.assert_called_once_with(self.config, service=Ledgers.service_name)
        mock_ledgers_check_access.assert_called_once_with(mock_client)
        mock_client.check_access.assert_not_called()
        self.assertTrue(result)

    @patch('tap_workday.schema.Client')
    def test_uses_client_check_access_for_streams_without_custom_method(self, mock_client_class):
        """Test that check_stream_authorization uses client.check_access for streams without custom method."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client

        class MockStream:
            service_name = "Financial_Management"
            operation_name = "Get_Cost_Centers"

        result = check_stream_authorization(self.config, "test_stream", MockStream)

        mock_client_class.assert_called_once_with(self.config, service=MockStream.service_name)
        mock_client.check_access.assert_called_once_with(MockStream.operation_name)
        self.assertTrue(result)

    @patch('tap_workday.schema.Client')
    def test_handles_missing_config(self, mock_client_class):
        """Test that check_stream_authorization handles missing config gracefully."""
        class MockStream:
            service_name = "Financial_Management"
            operation_name = "Get_Cost_Centers"

        result = check_stream_authorization(None, "test_stream", MockStream)

        mock_client_class.assert_not_called()
        self.assertTrue(result)

    @patch('tap_workday.schema.Client')
    def test_handles_stream_without_required_attributes(self, mock_client_class):
        """Test that check_stream_authorization handles streams without required attributes."""
        class MockStream:
            pass  # No service_name or operation_name

        result = check_stream_authorization(self.config, "test_stream", MockStream)

        mock_client_class.assert_not_called()
        self.assertTrue(result)

    @patch('tap_workday.schema.Client')
    def test_returns_false_on_auth_fault(self, mock_client_class):
        """Test that check_stream_authorization returns False when auth error pattern matches."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client

        class MockStream:
            service_name = "Financial_Management"
            operation_name = "Get_Cost_Centers"

        mock_client.check_access.side_effect = WorkdaySOAPFaultError(
            'Processing error occurred. The task submitted is not authorized.'
        )

        with self.assertLogs(level='WARNING') as cm:
            result = check_stream_authorization(self.config, "test_stream", MockStream)

        self.assertFalse(result)
        self.assertTrue(
            any('authorization' in msg.lower() for msg in cm.output),
            "Expected 'authorization' in log output",
        )
        self.assertFalse(
            any('authentication' in msg.lower() for msg in cm.output),
            "Authorization log should not mention 'authentication'",
        )

    @patch('tap_workday.schema.Client')
    def test_returns_true_on_non_auth_fault(self, mock_client_class):
        """Test that check_stream_authorization returns True for non-auth SOAP faults."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client

        class MockStream:
            service_name = "Financial_Management"
            operation_name = "Get_Cost_Centers"

        mock_client.check_access.side_effect = WorkdaySOAPFaultError('Some other SOAP error')

        result = check_stream_authorization(self.config, "test_stream", MockStream)

        self.assertTrue(result)

    @patch('tap_workday.schema.Client')
    def test_returns_false_on_transport_authentication_failure_by_status_code(self, mock_client_class):
        """A WorkdaySOAPTransportError with status_code=401 returns False with an authentication warning."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client

        class MockStream:
            service_name = "Financial_Management"
            operation_name = "Get_Cost_Centers"

        mock_client.check_access.side_effect = WorkdaySOAPTransportError(
            "Transport error in 'Get_Cost_Centers': Server returned HTTP status 401 (Unauthorized)",
            status_code=401,
        )

        with self.assertLogs(level='WARNING') as cm:
            result = check_stream_authorization(self.config, "test_stream", MockStream)

        self.assertFalse(result)
        self.assertTrue(
            any('authentication' in msg.lower() for msg in cm.output),
            "Expected 'authentication' in log output",
        )
        self.assertFalse(
            any('authorization' in msg.lower() for msg in cm.output),
            "Authentication log should not mention 'authorization'",
        )

    @patch('tap_workday.schema.Client')
    def test_returns_false_on_transport_authentication_failure_by_message(self, mock_client_class):
        """A transport error whose message contains an authn pattern returns False.
        This covers the production path where SOAPErrorHandler re-raises with status_code=0."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client

        class MockStream:
            service_name = "Financial_Management"
            operation_name = "Get_Cost_Centers"

        # Simulate what SOAPErrorHandler produces: status_code defaults to 0, message contains '401'
        mock_client.check_access.side_effect = WorkdaySOAPTransportError(
            "Transport error in 'Get_Cost_Centers': Server returned HTTP status 401 (Unauthorized)",
            status_code=0,
        )

        with self.assertLogs(level='WARNING') as cm:
            result = check_stream_authorization(self.config, "test_stream", MockStream)

        self.assertFalse(result)
        self.assertTrue(any('authentication' in msg.lower() for msg in cm.output))

    @patch('tap_workday.schema.Client')
    def test_returns_true_on_non_auth_transport_error(self, mock_client_class):
        """A transport error unrelated to authentication returns True (stream is included)."""
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client

        class MockStream:
            service_name = "Financial_Management"
            operation_name = "Get_Cost_Centers"

        mock_client.check_access.side_effect = WorkdaySOAPTransportError(
            "Transport error in 'Get_Cost_Centers': Connection timed out",
            status_code=503,
        )

        result = check_stream_authorization(self.config, "test_stream", MockStream)

        self.assertTrue(result)
