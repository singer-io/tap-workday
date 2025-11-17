"""
Unit tests for Ledgers stream sync method and associated functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from tap_workday.streams.financial_management import Ledgers, Journals
from tap_workday.client import Client


class TestLedgersSync(unittest.TestCase):
    """Test the Ledgers stream sync functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=Client)
        
        # Create a properly mocked catalog
        mock_catalog = Mock()
        mock_catalog.schema.to_dict.return_value = {}
        mock_catalog.metadata = []
        
        self.ledgers_stream = Ledgers(catalog=mock_catalog)
        self.ledgers_stream.client = Mock()
        self.ledgers_stream.client.config = {}
        
        # Mock state and transformer
        self.state = {}
        self.transformer = Mock()

    @patch('tap_workday.streams.helpers.emit_full_table')
    @patch.object(Ledgers, '_call_get_ledgers_with_reference_id')
    @patch.object(Ledgers, 'get_client')
    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_sync_successful_with_discovered_ledgers(self, mock_extract_ledgers, mock_get_client, 
                                                   mock_call_get_ledgers, mock_emit_full_table):
        """Test successful sync with discovered ledger IDs."""
        # Setup mocks
        mock_get_client.return_value = self.mock_client
        mock_extract_ledgers.return_value = {"LEDGER_001", "LEDGER_002"}
        
        # Mock ledger data for each ID
        ledger_001_records = [{"key_value": "L001", "Ledger_Data": {"Actuals_Ledger_ID": "LEDGER_001"}}]
        ledger_002_records = [{"key_value": "L002", "Ledger_Data": {"Actuals_Ledger_ID": "LEDGER_002"}}]
        
        # Use a function to return the correct data based on ledger ID
        def mock_get_ledgers_data(client, ledger_id, updated_since):
            if ledger_id == "LEDGER_001":
                return ledger_001_records
            elif ledger_id == "LEDGER_002":
                return ledger_002_records
            else:
                return []
        
        mock_call_get_ledgers.side_effect = mock_get_ledgers_data
        
        mock_emit_full_table.return_value = {"success": True}

        # Call sync
        result = self.ledgers_stream.sync(self.state, self.transformer)

        # Verify ledger discovery was called
        mock_extract_ledgers.assert_called_once_with(self.mock_client)
        
        # Verify get_ledgers was called for each discovered ledger ID
        self.assertEqual(mock_call_get_ledgers.call_count, 2)
        calls = mock_call_get_ledgers.call_args_list
        
        # Extract the ledger IDs from the calls (order may vary due to set behavior)
        called_ledger_ids = {call[0][1] for call in calls}
        expected_ledger_ids = {"LEDGER_001", "LEDGER_002"}
        self.assertEqual(called_ledger_ids, expected_ledger_ids)
        
        # Verify all calls used the correct client and None for updated_since
        for call in calls:
            self.assertEqual(call[0][0], self.mock_client)  # client
            self.assertEqual(call[0][2], None)  # updated_since
        
        # Verify emit_full_table was called with all records (order may vary)
        mock_emit_full_table.assert_called_once()
        call_args = mock_emit_full_table.call_args[0]
        self.assertEqual(call_args[0], self.ledgers_stream)  # First arg should be the stream
        
        # Check that all expected records are present (regardless of order)
        actual_records = call_args[1]
        expected_records = ledger_001_records + ledger_002_records
        self.assertEqual(len(actual_records), len(expected_records))
        
        # Convert to sets of key_values for order-independent comparison
        actual_key_values = {record["key_value"] for record in actual_records}
        expected_key_values = {record["key_value"] for record in expected_records}
        self.assertEqual(actual_key_values, expected_key_values)
        
        # Verify result
        self.assertEqual(result, {"success": True})

    @patch('tap_workday.streams.helpers.emit_full_table')
    @patch.object(Ledgers, 'get_client')
    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_sync_no_ledgers_discovered(self, mock_extract_ledgers, mock_get_client, mock_emit_full_table):
        """Test sync when no ledger IDs are discovered from journals."""
        # Setup mocks
        mock_get_client.return_value = self.mock_client
        mock_extract_ledgers.return_value = set()  # Empty set
        mock_emit_full_table.return_value = {"success": True, "records": 0}

        # Call sync
        result = self.ledgers_stream.sync(self.state, self.transformer)

        # Verify ledger discovery was called
        mock_extract_ledgers.assert_called_once_with(self.mock_client)
        
        # Verify emit_full_table was called with empty records
        mock_emit_full_table.assert_called_once_with(self.ledgers_stream, [])
        
        # Verify result
        self.assertEqual(result, {"success": True, "records": 0})

    @patch('tap_workday.streams.helpers.emit_full_table')
    @patch.object(Ledgers, 'get_client')
    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_sync_journal_discovery_fails(self, mock_extract_ledgers, mock_get_client, mock_emit_full_table):
        """Test sync when journal ledger ID discovery fails."""
        # Setup mocks
        mock_get_client.return_value = self.mock_client
        mock_extract_ledgers.side_effect = Exception("Journal API failure")
        mock_emit_full_table.return_value = {"success": True, "records": 0}

        # Call sync
        result = self.ledgers_stream.sync(self.state, self.transformer)

        # Verify ledger discovery was called
        mock_extract_ledgers.assert_called_once_with(self.mock_client)
        
        # Verify emit_full_table was called with empty records due to discovery failure
        mock_emit_full_table.assert_called_once_with(self.ledgers_stream, [])
        
        # Verify result
        self.assertEqual(result, {"success": True, "records": 0})

    @patch('tap_workday.streams.helpers.emit_full_table')
    @patch.object(Ledgers, '_call_get_ledgers_with_reference_id')
    @patch.object(Ledgers, 'get_client')
    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_sync_partial_ledger_failure(self, mock_extract_ledgers, mock_get_client, 
                                        mock_call_get_ledgers, mock_emit_full_table):
        """Test sync when some ledger retrievals fail but others succeed."""
        # Setup mocks
        mock_get_client.return_value = self.mock_client
        mock_extract_ledgers.return_value = {"LEDGER_001", "LEDGER_002", "LEDGER_003"}
        
        # Mock success for first and third ledgers, failure for second
        ledger_001_records = [{"key_value": "L001", "Ledger_Data": {"Actuals_Ledger_ID": "LEDGER_001"}}]
        ledger_003_records = [{"key_value": "L003", "Ledger_Data": {"Actuals_Ledger_ID": "LEDGER_003"}}]
        
        # Use a function to return the correct data/exception based on ledger ID
        def mock_partial_failure(client, ledger_id, updated_since):
            if ledger_id == "LEDGER_001":
                return ledger_001_records
            elif ledger_id == "LEDGER_002":
                raise Exception("Ledger API failure for LEDGER_002")
            elif ledger_id == "LEDGER_003":
                return ledger_003_records
            else:
                return []
        
        mock_call_get_ledgers.side_effect = mock_partial_failure
        
        mock_emit_full_table.return_value = {"success": True}

        # Call sync
        result = self.ledgers_stream.sync(self.state, self.transformer)

        # Verify all ledger calls were attempted
        self.assertEqual(mock_call_get_ledgers.call_count, 3)
        
        # Verify emit_full_table was called with successful records only (order may vary)
        mock_emit_full_table.assert_called_once()
        call_args = mock_emit_full_table.call_args[0]
        self.assertEqual(call_args[0], self.ledgers_stream)  # First arg should be the stream
        
        # Check that only successful records are present (LEDGER_001 and LEDGER_003)
        actual_records = call_args[1]
        expected_records = ledger_001_records + ledger_003_records
        self.assertEqual(len(actual_records), len(expected_records))
        
        # Convert to sets of key_values for order-independent comparison
        actual_key_values = {record["key_value"] for record in actual_records}
        expected_key_values = {"L001", "L003"}  # Only successful ledgers
        self.assertEqual(actual_key_values, expected_key_values)
        
        # Verify result
        self.assertEqual(result, {"success": True})

    @patch('tap_workday.streams.helpers.emit_full_table')
    @patch.object(Ledgers, '_call_get_ledgers_with_reference_id')
    @patch.object(Ledgers, 'get_client')
    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_sync_with_bookmark_incremental(self, mock_extract_ledgers,
                                          mock_get_client, mock_call_get_ledgers, mock_emit_full_table):
        """Test sync uses bookmark for incremental syncs when available."""
        # Setup mocks
        mock_get_client.return_value = self.mock_client
        mock_extract_ledgers.return_value = {"LEDGER_001"}
        
        ledger_records = [{"key_value": "L001", "Ledger_Data": {"Actuals_Ledger_ID": "LEDGER_001"}}]
        mock_call_get_ledgers.return_value = ledger_records
        mock_emit_full_table.return_value = {"success": True}

        # Add get_bookmark method to the instance for this test
        mock_get_bookmark = Mock(return_value="2023-01-01T00:00:00Z")
        self.ledgers_stream.get_bookmark = mock_get_bookmark

        # Call sync
        result = self.ledgers_stream.sync(self.state, self.transformer)

        # Verify bookmark was retrieved
        mock_get_bookmark.assert_called_once_with(self.state, self.ledgers_stream.tap_stream_id)
        
        # Verify get_ledgers was called with updated_since
        mock_call_get_ledgers.assert_called_once_with(
            self.mock_client, "LEDGER_001", "2023-01-01T00:00:00Z"
        )
        
        # Verify result
        self.assertEqual(result, {"success": True})

    @patch('tap_workday.streams.helpers.emit_full_table')
    @patch.object(Ledgers, '_call_get_ledgers_with_reference_id')
    @patch.object(Ledgers, 'get_client')
    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_sync_bookmark_exception_handled(self, mock_extract_ledgers,
                                           mock_get_client, mock_call_get_ledgers, mock_emit_full_table):
        """Test sync handles bookmark retrieval exceptions gracefully."""
        # Setup mocks
        mock_get_client.return_value = self.mock_client
        mock_extract_ledgers.return_value = {"LEDGER_001"}
        
        ledger_records = [{"key_value": "L001", "Ledger_Data": {"Actuals_Ledger_ID": "LEDGER_001"}}]
        mock_call_get_ledgers.return_value = ledger_records
        mock_emit_full_table.return_value = {"success": True}

        # Mock get_bookmark method to raise an exception
        mock_get_bookmark = Mock(side_effect=Exception("Bookmark error"))
        self.ledgers_stream.get_bookmark = mock_get_bookmark

        # Call sync
        result = self.ledgers_stream.sync(self.state, self.transformer)

        # Verify get_ledgers was called with None for updated_since
        mock_call_get_ledgers.assert_called_once_with(self.mock_client, "LEDGER_001", None)
        
        # Verify result
        self.assertEqual(result, {"success": True})

    def test_ledgers_stream_attributes(self):
        """Test that Ledgers stream has the expected attributes."""
        self.assertEqual(Ledgers.tap_stream_id, "financial_management_ledgers")
        self.assertEqual(Ledgers.operation_name, "Get_Ledgers")
        self.assertEqual(Ledgers.data_key, "Ledger")
        self.assertEqual(Ledgers.wid_key, "Actuals_Ledger_Reference")
        self.assertEqual(Ledgers.replication_method, "FULL_TABLE")
