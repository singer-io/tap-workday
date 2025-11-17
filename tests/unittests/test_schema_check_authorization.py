"""
Unit tests for schema.py check_stream_authorization function.
"""

import unittest
from unittest.mock import Mock, patch
from tap_workday.schema import check_stream_authorization
from tap_workday.client import Client
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
        self.mdata = {}

    @patch('tap_workday.schema.Client')
    @patch.object(Ledgers, 'check_access')
    def test_uses_stream_custom_check_access_method(self, mock_ledgers_check_access, mock_client_class):
        """Test that check_stream_authorization uses stream's custom check_access method when available."""
        # Create mock client instance
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client
        
        # Call check_stream_authorization with Ledgers class (not instance)
        result = check_stream_authorization(self.config, self.stream_name, Ledgers, self.mdata)
        
        # Verify Client was created with correct parameters
        mock_client_class.assert_called_once_with(self.config, service=Ledgers.service_name)
        
        # Verify stream's custom check_access class method was called
        mock_ledgers_check_access.assert_called_once_with(mock_client)
        
        # Verify client's check_access was NOT called
        mock_client.check_access.assert_not_called()
        
        # Verify metadata is returned unchanged
        self.assertEqual(result, self.mdata)

    @patch('tap_workday.schema.Client')
    def test_uses_client_check_access_for_streams_without_custom_method(self, mock_client_class):
        """Test that check_stream_authorization uses client.check_access for streams without custom method."""
        # Create mock client instance
        mock_client = Mock(spec=Client)
        mock_client_class.return_value = mock_client
        
        # Create a mock stream class without check_access method
        class MockStream:
            service_name = "Financial_Management"
            operation_name = "Get_Cost_Centers"
        
        # Call check_stream_authorization
        result = check_stream_authorization(self.config, "test_stream", MockStream, self.mdata)
        
        # Verify Client was created with correct parameters
        mock_client_class.assert_called_once_with(self.config, service=MockStream.service_name)
        
        # Verify client's check_access method was called
        mock_client.check_access.assert_called_once_with(MockStream.operation_name)
        
        # Verify metadata is returned unchanged
        self.assertEqual(result, self.mdata)

    @patch('tap_workday.schema.Client')
    def test_handles_missing_config(self, mock_client_class):
        """Test that check_stream_authorization handles missing config gracefully."""
        class MockStream:
            service_name = "Financial_Management"
            operation_name = "Get_Cost_Centers"
        
        result = check_stream_authorization(None, "test_stream", MockStream, self.mdata)
        
        # Verify Client was not created
        mock_client_class.assert_not_called()
        
        # Verify metadata is returned unchanged
        self.assertEqual(result, self.mdata)

    @patch('tap_workday.schema.Client')
    def test_handles_stream_without_required_attributes(self, mock_client_class):
        """Test that check_stream_authorization handles streams without required attributes."""
        class MockStream:
            pass  # No service_name or operation_name
        
        result = check_stream_authorization(self.config, "test_stream", MockStream, self.mdata)
        
        # Verify Client was not created
        mock_client_class.assert_not_called()
        
        # Verify metadata is returned unchanged
        self.assertEqual(result, self.mdata)
