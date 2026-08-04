"""
Unit tests for Journals.extract_ledger_ids_from_journals_api method.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from tap_workday.streams.financial_management import Journals
from tap_workday.client import Client


class TestJournalsExtractLedgerIds(unittest.TestCase):
    """Test the Journals stream extract_ledger_ids_from_journals_api functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=Client)

    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_extract_ledger_ids_successful(self, mock_paginator_class):
        """Test successful extraction of ledger IDs from journal entries."""
        # Mock paginator instance and records
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        
        # Sample journal entry with ledger reference
        journal_records = [
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {
                        "ID": [
                            {
                                "type": "Ledger_Reference_ID",
                                "_value_1": "LEDGER_001"
                            }
                        ]
                    }
                }
            },
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {
                        "ID": [
                            {
                                "type": "Ledger_Reference_ID", 
                                "_value_1": "LEDGER_002"
                            }
                        ]
                    }
                }
            }
        ]
        mock_paginator.paginate_operation.return_value = journal_records

        # Call the method
        result = Journals.extract_ledger_ids_from_journals_api(self.mock_client)

        # Verify paginator was created and called correctly
        mock_paginator_class.assert_called_once_with(self.mock_client, "Get_Journals")
        mock_paginator.paginate_operation.assert_called_once_with("Journal_Entry", max_pages=None)

        # Verify extracted ledger IDs
        expected_ids = {"LEDGER_001", "LEDGER_002"}
        self.assertEqual(result, expected_ids)

    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_extract_ledger_ids_with_max_pages(self, mock_paginator_class):
        """Test extraction with max_pages parameter."""
        # Mock paginator instance and records
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        mock_paginator.paginate_operation.return_value = []

        # Call with max_pages
        result = Journals.extract_ledger_ids_from_journals_api(self.mock_client, max_pages=5)

        # Verify max_pages was passed correctly
        mock_paginator.paginate_operation.assert_called_once_with("Journal_Entry", max_pages=5)
        self.assertEqual(result, set())

    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_extract_ledger_ids_array_journal_entry_data(self, mock_paginator_class):
        """Test extraction when Journal_Entry_Data is an array."""
        # Mock paginator instance
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        
        # Journal entry with array Journal_Entry_Data
        journal_records = [
            {
                "Journal_Entry_Data": [
                    {
                        "Ledger_Reference": {
                            "ID": [
                                {
                                    "type": "Ledger_Reference_ID",
                                    "_value_1": "LEDGER_ARRAY_001"
                                }
                            ]
                        }
                    },
                    {
                        "Ledger_Reference": {
                            "ID": [
                                {
                                    "type": "Ledger_Reference_ID",
                                    "_value_1": "LEDGER_ARRAY_002"
                                }
                            ]
                        }
                    }
                ]
            }
        ]
        mock_paginator.paginate_operation.return_value = journal_records

        # Call the method
        result = Journals.extract_ledger_ids_from_journals_api(self.mock_client)

        # Verify extracted ledger IDs from array
        expected_ids = {"LEDGER_ARRAY_001", "LEDGER_ARRAY_002"}
        self.assertEqual(result, expected_ids)

    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_extract_ledger_ids_duplicate_handling(self, mock_paginator_class):
        """Test that duplicate ledger IDs are handled correctly (set behavior)."""
        # Mock paginator instance
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        
        # Records with duplicate ledger IDs
        journal_records = [
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {
                        "ID": [
                            {
                                "type": "Ledger_Reference_ID",
                                "_value_1": "LEDGER_001"
                            }
                        ]
                    }
                }
            },
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {
                        "ID": [
                            {
                                "type": "Ledger_Reference_ID",
                                "_value_1": "LEDGER_001"  # Duplicate
                            }
                        ]
                    }
                }
            },
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {
                        "ID": [
                            {
                                "type": "Ledger_Reference_ID",
                                "_value_1": "LEDGER_002"
                            }
                        ]
                    }
                }
            }
        ]
        mock_paginator.paginate_operation.return_value = journal_records

        # Call the method
        result = Journals.extract_ledger_ids_from_journals_api(self.mock_client)

        # Verify duplicates are removed (set behavior)
        expected_ids = {"LEDGER_001", "LEDGER_002"}
        self.assertEqual(result, expected_ids)
        self.assertEqual(len(result), 2)  # Ensure no duplicates

    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_extract_ledger_ids_invalid_data_structures(self, mock_paginator_class):
        """Test extraction handles invalid or missing data structures gracefully."""
        # Mock paginator instance
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        
        # Records with various invalid structures
        journal_records = [
            # Missing Journal_Entry_Data
            {},
            # Journal_Entry_Data is not dict or list
            {"Journal_Entry_Data": "invalid"},
            # Missing Ledger_Reference
            {"Journal_Entry_Data": {}},
            # Ledger_Reference missing ID
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {}
                }
            },
            # ID is not a list
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {
                        "ID": "not_a_list"
                    }
                }
            },
            # ID entry missing required fields
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {
                        "ID": [
                            {
                                "type": "Wrong_Type",
                                "_value_1": "LEDGER_003"
                            }
                        ]
                    }
                }
            },
            # ID entry missing _value_1
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {
                        "ID": [
                            {
                                "type": "Ledger_Reference_ID"
                                # Missing _value_1
                            }
                        ]
                    }
                }
            },
            # Valid entry for comparison
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {
                        "ID": [
                            {
                                "type": "Ledger_Reference_ID",
                                "_value_1": "LEDGER_VALID"
                            }
                        ]
                    }
                }
            }
        ]
        mock_paginator.paginate_operation.return_value = journal_records

        # Call the method
        result = Journals.extract_ledger_ids_from_journals_api(self.mock_client)

        # Verify only the valid entry is extracted
        expected_ids = {"LEDGER_VALID"}
        self.assertEqual(result, expected_ids)

    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_extract_ledger_ids_empty_response(self, mock_paginator_class):
        """Test extraction with empty journal response."""
        # Mock paginator instance
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        mock_paginator.paginate_operation.return_value = []

        # Call the method
        result = Journals.extract_ledger_ids_from_journals_api(self.mock_client)

        # Verify empty set is returned
        self.assertEqual(result, set())

    @patch('tap_workday.streams.helpers.WorkdayPaginator')
    def test_extract_ledger_ids_multiple_id_entries(self, mock_paginator_class):
        """Test extraction when Ledger_Reference has multiple ID entries."""
        # Mock paginator instance
        mock_paginator = Mock()
        mock_paginator_class.return_value = mock_paginator
        
        # Record with multiple ID entries in same Ledger_Reference
        journal_records = [
            {
                "Journal_Entry_Data": {
                    "Ledger_Reference": {
                        "ID": [
                            {
                                "type": "Ledger_Reference_ID",
                                "_value_1": "LEDGER_MULTI_001"
                            },
                            {
                                "type": "Some_Other_Type",  # Should be ignored
                                "_value_1": "SHOULD_BE_IGNORED"
                            },
                            {
                                "type": "Ledger_Reference_ID",
                                "_value_1": "LEDGER_MULTI_002"
                            }
                        ]
                    }
                }
            }
        ]
        mock_paginator.paginate_operation.return_value = journal_records

        # Call the method
        result = Journals.extract_ledger_ids_from_journals_api(self.mock_client)

        # Verify only Ledger_Reference_ID types are extracted
        expected_ids = {"LEDGER_MULTI_001", "LEDGER_MULTI_002"}
        self.assertEqual(result, expected_ids)
