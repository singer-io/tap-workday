"""
Unit tests for Ledgers stream custom check_access method.
"""

import unittest
from unittest.mock import Mock, patch
from tap_workday.streams.financial_management import Ledgers, Journals
from tap_workday.client import Client


class TestLedgersCheckAccess(unittest.TestCase):
    """Test the Ledgers stream custom check_access functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=Client)

    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_check_access_calls_client_with_correct_params(self, mock_extract_ledger_ids):
        """Test that check_access calls client.check_access with expected parameters."""
        # Mock the ledger ID extraction to return a test ID set
        mock_extract_ledger_ids.return_value = {"REAL_LEDGER_ID"}
        
        # Mock the client.check_access to return a successful response
        self.mock_client.check_access.return_value = {"success": True}
        
        # Call the custom check_access class method
        result = Ledgers.check_access(self.mock_client)
        
        # Verify the ledger ID extraction was called with max_pages=1
        mock_extract_ledger_ids.assert_called_once_with(
            self.mock_client, max_pages=1, updated_since=None, updated_through=None
        )
        
        # Verify the client.check_access was called once for ledgers
        self.mock_client.check_access.assert_called_once()
        call_args = self.mock_client.check_access.call_args
        
        # Verify operation name is correct
        self.assertEqual(call_args[0][0], "Get_Ledgers")
        
        # Verify Request_Reference structure uses the real ledger ID
        expected_request_ref = {
            'Request_Reference': {
                'Actuals_Ledger_Reference': {
                    'ID': [{'_value_1': 'REAL_LEDGER_ID', 'type': 'Ledger_Reference_ID'}]
                }
            },
            'Response_Filter': {'Page': 1, 'Count': 1}
        }
        
        # Check that the call was made with the expected parameters
        for key, value in expected_request_ref.items():
            self.assertEqual(call_args[1][key], value)
        
        # Verify return value
        self.assertEqual(result, {"success": True})

    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_check_access_fallback_when_no_ledger_id_found(self, mock_extract_ledger_ids):
        """Test that check_access falls back to TEST_LEDGER when no real ledger ID is found."""
        # Mock the ledger ID extraction to return empty set
        mock_extract_ledger_ids.return_value = set()
        
        # Mock the client.check_access to return a successful response
        self.mock_client.check_access.return_value = {"success": True}
        
        # Call the custom check_access class method
        result = Ledgers.check_access(self.mock_client)
        
        # Verify the ledger ID extraction was called with max_pages=1
        mock_extract_ledger_ids.assert_called_once_with(
            self.mock_client, max_pages=1, updated_since=None, updated_through=None
        )
        
        # Get the ledgers call args
        call_args = self.mock_client.check_access.call_args
        
        # Verify it falls back to TEST_LEDGER
        expected_ledger_id = 'TEST_LEDGER'
        actual_ledger_id = call_args[1]['Request_Reference']['Actuals_Ledger_Reference']['ID'][0]['_value_1']
        self.assertEqual(actual_ledger_id, expected_ledger_id)

    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_check_access_fallback_when_exception_occurs(self, mock_extract_ledger_ids):
        """Test that check_access falls back to TEST_LEDGER when an exception occurs."""
        # Mock the ledger ID extraction to raise an exception
        mock_extract_ledger_ids.side_effect = Exception("Journal API error")
        
        # Mock the client.check_access to return a successful response
        self.mock_client.check_access.return_value = {"success": True}
        
        # Call the custom check_access class method
        result = Ledgers.check_access(self.mock_client)
        
        # Get the ledgers call args
        call_args = self.mock_client.check_access.call_args
        
        # Verify it falls back to TEST_LEDGER
        expected_ledger_id = 'TEST_LEDGER'
        actual_ledger_id = call_args[1]['Request_Reference']['Actuals_Ledger_Reference']['ID'][0]['_value_1']
        self.assertEqual(actual_ledger_id, expected_ledger_id)

    def test_check_access_reraises_exceptions(self):
        """Test that check_access properly re-raises exceptions from client."""
        # Mock the client to raise an exception  
        test_exception = Exception("Test API error")
        self.mock_client.check_access.side_effect = test_exception
        
        # Verify the exception is re-raised
        with self.assertRaises(Exception) as context:
            Ledgers.check_access(self.mock_client)
        
        self.assertEqual(str(context.exception), "Test API error")

    def test_ledgers_stream_has_check_access_method(self):
        """Test that Ledgers class has the check_access method."""
        self.assertTrue(hasattr(Ledgers, 'check_access'))
        self.assertTrue(callable(getattr(Ledgers, 'check_access')))

    def test_stream_attributes(self):
        """Test that Ledgers stream has the expected attributes."""
        self.assertEqual(Ledgers.tap_stream_id, "financial_management_ledgers")
        self.assertEqual(Ledgers.operation_name, "Get_Ledgers")
        self.assertEqual(Ledgers.data_key, "Ledger")
        self.assertEqual(Ledgers.wid_key, "Actuals_Ledger_Reference")
