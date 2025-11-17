"""
Unit tests for Ledgers._call_get_ledgers_with_reference_id method.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from tap_workday.streams.financial_management import Ledgers
from tap_workday.client import Client


class TestLedgersCallGetLedgersWithReferenceId(unittest.TestCase):
    """Test the Ledgers._call_get_ledgers_with_reference_id method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=Client)
        
        # Create a properly mocked catalog
        mock_catalog = Mock()
        mock_catalog.schema.to_dict.return_value = {}
        mock_catalog.metadata = []
        
        self.ledgers_stream = Ledgers(catalog=mock_catalog)
        self.test_ledger_id = "TEST_LEDGER_001"

    @patch('tap_workday.streams.helpers._extract_key_value')
    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_call_get_ledgers_without_updated_since(self, mock_paginator_class, mock_extract_key_value):
        """Test calling Get_Ledgers without updated_since parameter."""
        # Mock paginator and records
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        
        mock_records = [
            {
                "Ledger_Data": {
                    "Actuals_Ledger_ID": "TEST_LEDGER_001"
                }
            }
        ]
        mock_paginator.paginate_operation.return_value = mock_records
        mock_extract_key_value.return_value = "extracted_key_001"

        # Call the method
        result = self.ledgers_stream._call_get_ledgers_with_reference_id(
            self.mock_client, self.test_ledger_id
        )

        # Verify paginator was created correctly
        mock_paginator_class.assert_called_once_with(self.mock_client, "Get_Ledgers")
        
        # Verify paginate_operation was called with correct parameters
        call_args = mock_paginator.paginate_operation.call_args
        self.assertEqual(call_args[0][0], "Ledger")  # data_key
        self.assertEqual(call_args[0][1], None)     # updated_since
        
        # Verify custom_params structure (third positional argument)
        custom_params = call_args[0][2]
        expected_request_reference = {
            'Actuals_Ledger_Reference': {
                'ID': [{'_value_1': self.test_ledger_id, 'type': 'Ledger_Reference_ID'}]
            }
        }
        self.assertEqual(custom_params['Request_Reference'], expected_request_reference)
        self.assertNotIn('Request_Criteria', custom_params)
        
        # Verify key_value was extracted and added to records
        mock_extract_key_value.assert_called_once_with(mock_records[0], "Actuals_Ledger_Reference")
        self.assertEqual(result[0]["key_value"], "extracted_key_001")

    @patch('tap_workday.streams.helpers._extract_key_value')
    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_call_get_ledgers_with_updated_since(self, mock_paginator_class, mock_extract_key_value):
        """Test calling Get_Ledgers with updated_since parameter."""
        # Mock paginator and records
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        
        mock_records = [
            {
                "Ledger_Data": {
                    "Actuals_Ledger_ID": "TEST_LEDGER_001"
                }
            }
        ]
        mock_paginator.paginate_operation.return_value = mock_records
        mock_extract_key_value.return_value = "extracted_key_001"

        updated_since = "2023-01-01T00:00:00Z"
        
        # Call the method
        result = self.ledgers_stream._call_get_ledgers_with_reference_id(
            self.mock_client, self.test_ledger_id, updated_since
        )

        # Verify paginate_operation was called with updated_since
        call_args = mock_paginator.paginate_operation.call_args
        self.assertEqual(call_args[0][1], updated_since)  # updated_since
        
        # Verify custom_params includes Request_Criteria (third positional argument)
        custom_params = call_args[0][2]
        self.assertIn('Request_Criteria', custom_params)
        self.assertEqual(custom_params['Request_Criteria'], {'Updated_From': updated_since})
        
        # Verify result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["key_value"], "extracted_key_001")

    @patch('tap_workday.streams.helpers._extract_key_value')
    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_call_get_ledgers_multiple_records(self, mock_paginator_class, mock_extract_key_value):
        """Test calling Get_Ledgers with multiple records returned."""
        # Mock paginator and records
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        
        mock_records = [
            {
                "Ledger_Data": {
                    "Actuals_Ledger_ID": "TEST_LEDGER_001"
                }
            },
            {
                "Ledger_Data": {
                    "Actuals_Ledger_ID": "TEST_LEDGER_002"
                }
            }
        ]
        mock_paginator.paginate_operation.return_value = mock_records
        
        # Mock different key values for each record
        mock_extract_key_value.side_effect = ["key_001", "key_002"]

        # Call the method
        result = self.ledgers_stream._call_get_ledgers_with_reference_id(
            self.mock_client, self.test_ledger_id
        )

        # Verify extract_key_value was called for each record
        self.assertEqual(mock_extract_key_value.call_count, 2)
        
        # Verify both records have key_value added
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["key_value"], "key_001")
        self.assertEqual(result[1]["key_value"], "key_002")

    @patch('tap_workday.streams.helpers._extract_key_value')
    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_call_get_ledgers_key_value_extraction_fails(self, mock_paginator_class, mock_extract_key_value):
        """Test behavior when key_value extraction fails (returns None)."""
        # Mock paginator and records
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        
        mock_records = [
            {
                "Ledger_Data": {
                    "Actuals_Ledger_ID": "TEST_LEDGER_001"
                }
            }
        ]
        mock_paginator.paginate_operation.return_value = mock_records
        mock_extract_key_value.return_value = None  # Simulate extraction failure

        # Call the method
        result = self.ledgers_stream._call_get_ledgers_with_reference_id(
            self.mock_client, self.test_ledger_id
        )

        # Verify record is returned without key_value when extraction fails
        self.assertEqual(len(result), 1)
        self.assertNotIn("key_value", result[0])

    @patch('tap_workday.streams.helpers._extract_key_value')
    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_call_get_ledgers_empty_response(self, mock_paginator_class, mock_extract_key_value):
        """Test calling Get_Ledgers with empty response."""
        # Mock paginator with empty records
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        mock_paginator.paginate_operation.return_value = []

        # Call the method
        result = self.ledgers_stream._call_get_ledgers_with_reference_id(
            self.mock_client, self.test_ledger_id
        )

        # Verify empty list is returned
        self.assertEqual(result, [])
        
        # Verify extract_key_value was not called
        mock_extract_key_value.assert_not_called()

    @patch('tap_workday.streams.helpers._extract_key_value')
    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_call_get_ledgers_custom_params_structure(self, mock_paginator_class, mock_extract_key_value):
        """Test that custom_params structure is correctly formed."""
        # Mock paginator
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        mock_paginator.paginate_operation.return_value = []

        ledger_id = "SPECIFIC_LEDGER_ID"
        updated_since = "2023-06-15T12:30:00Z"
        
        # Call the method
        self.ledgers_stream._call_get_ledgers_with_reference_id(
            self.mock_client, ledger_id, updated_since
        )

        # Get the custom_params that were passed (third positional argument)
        call_args = mock_paginator.paginate_operation.call_args
        custom_params = call_args[0][2]
        
        # Verify Request_Reference structure
        request_ref = custom_params['Request_Reference']
        self.assertIn('Actuals_Ledger_Reference', request_ref)
        
        actuals_ledger_ref = request_ref['Actuals_Ledger_Reference']
        self.assertIn('ID', actuals_ledger_ref)
        self.assertIsInstance(actuals_ledger_ref['ID'], list)
        self.assertEqual(len(actuals_ledger_ref['ID']), 1)
        
        id_entry = actuals_ledger_ref['ID'][0]
        self.assertEqual(id_entry['_value_1'], ledger_id)
        self.assertEqual(id_entry['type'], 'Ledger_Reference_ID')
        
        # Verify Request_Criteria structure
        self.assertIn('Request_Criteria', custom_params)
        self.assertEqual(custom_params['Request_Criteria'], {'Updated_From': updated_since})

    @patch('tap_workday.streams.helpers._extract_key_value')
    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_call_get_ledgers_wid_key_used_for_extraction(self, mock_paginator_class, mock_extract_key_value):
        """Test that the correct wid_key is used for key value extraction."""
        # Mock paginator and records
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        
        mock_records = [{"test": "data"}]
        mock_paginator.paginate_operation.return_value = mock_records
        mock_extract_key_value.return_value = "test_key"

        # Call the method
        self.ledgers_stream._call_get_ledgers_with_reference_id(
            self.mock_client, self.test_ledger_id
        )

        # Verify _extract_key_value was called with the correct wid_key
        mock_extract_key_value.assert_called_once_with(mock_records[0], "Actuals_Ledger_Reference")
