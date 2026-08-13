"""
Unit tests to verify Ledgers stream registration and module integration.
"""

import unittest
from tap_workday.streams import STREAMS
from tap_workday.streams.financial_management import Ledgers


class TestLedgersStreamRegistration(unittest.TestCase):
    """Test that Ledgers stream is properly registered and integrated."""

    def test_ledgers_stream_in_streams_registry(self):
        """Test that Ledgers stream is registered in STREAMS dictionary."""
        self.assertIn("financial_management_ledgers", STREAMS)
        self.assertEqual(STREAMS["financial_management_ledgers"], Ledgers)

    def test_ledgers_stream_import_succeeds(self):
        """Test that Ledgers stream can be imported from financial_management module."""
        from tap_workday.streams.financial_management import Ledgers as ImportedLedgers
        
        # Verify it's the same class
        self.assertEqual(ImportedLedgers, Ledgers)
        
        # Verify basic attributes
        self.assertEqual(ImportedLedgers.tap_stream_id, "financial_management_ledgers")
        self.assertEqual(ImportedLedgers.operation_name, "Get_Ledgers")
        self.assertEqual(ImportedLedgers.data_key, "Ledger")
        self.assertEqual(ImportedLedgers.wid_key, "Actuals_Ledger_Reference")

    def test_ledgers_stream_has_required_methods(self):
        """Test that Ledgers stream has all required methods."""
        # Check that the class has the expected methods
        self.assertTrue(hasattr(Ledgers, 'check_access'))
        self.assertTrue(callable(getattr(Ledgers, 'check_access')))
        
        self.assertTrue(hasattr(Ledgers, 'sync'))
        self.assertTrue(callable(getattr(Ledgers, 'sync')))
        
        self.assertTrue(hasattr(Ledgers, '_call_get_ledgers_with_reference_id'))
        self.assertTrue(callable(getattr(Ledgers, '_call_get_ledgers_with_reference_id')))

    def test_ledgers_stream_inherits_from_correct_base_class(self):
        """Test that Ledgers stream inherits from FinancialManagementStream."""
        from tap_workday.streams.financial_management import FinancialManagementStream
        
        # Check inheritance chain
        self.assertTrue(issubclass(Ledgers, FinancialManagementStream))
        
        # Verify inherited attributes at class level (no instantiation needed)
        self.assertEqual(Ledgers.replication_method, "FULL_TABLE")
        self.assertEqual(Ledgers.key_properties, ["key_value"])
        self.assertEqual(Ledgers.service_name, "Financial_Management")

    def test_all_financial_management_streams_registered(self):
        """Test that all Financial Management streams including Ledgers are registered."""
        expected_fm_streams = {
            "financial_management_cost_centers",
            "financial_management_customer_categories", 
            "financial_management_fund_hierarchies",
            "financial_management_fund_types",
            "financial_management_funding_sources",
            "financial_management_funds",
            "financial_management_journal_sources",
            "financial_management_journals",
            "financial_management_ledger_account_summaries",
            "financial_management_ledgers",  # This is the new stream
            "financial_management_organizations",
            "financial_management_position_budgets",
            "financial_management_program_hierarchies",
            "financial_management_programs",
            "financial_management_revenue_categories",
            "financial_management_revenue_category_hierarchies",
            "financial_management_spend_category_hierarchies",
            "financial_management_supplier_categories",
        }
        
        # Check that all expected FM streams are in STREAMS
        registered_fm_streams = {k for k in STREAMS.keys() if k.startswith("financial_management_")}
        
        self.assertEqual(registered_fm_streams, expected_fm_streams)
        
        # Specifically verify ledgers stream
        self.assertIn("financial_management_ledgers", registered_fm_streams)

    def test_streams_registry_has_correct_structure(self):
        """Test that STREAMS registry has the expected structure."""
        # Verify STREAMS is a dictionary
        self.assertIsInstance(STREAMS, dict)
        
        # Verify all values are classes
        for stream_name, stream_class in STREAMS.items():
            self.assertIsInstance(stream_name, str, f"Stream name {stream_name} should be string")
            self.assertTrue(hasattr(stream_class, 'tap_stream_id'), 
                          f"Stream {stream_name} should have tap_stream_id attribute")
        
        # Verify ledgers stream specifically
        ledgers_class = STREAMS.get("financial_management_ledgers")
        self.assertIsNotNone(ledgers_class)
        self.assertEqual(ledgers_class.tap_stream_id, "financial_management_ledgers")

    def test_ledgers_stream_unique_in_registry(self):
        """Test that ledgers stream is uniquely registered (no duplicates)."""
        ledgers_entries = [k for k, v in STREAMS.items() if v == Ledgers]
        
        # Should only be registered once
        self.assertEqual(len(ledgers_entries), 1)
        self.assertEqual(ledgers_entries[0], "financial_management_ledgers")

    def test_stream_registry_imports_work(self):
        """Test that all stream imports in __init__.py work correctly."""
        # This test ensures the imports in __init__.py are correct
        from tap_workday.streams import (
            Ledgers as ImportedLedgers,
            STREAMS as ImportedStreams
        )
        
        # Verify the import worked
        self.assertEqual(ImportedLedgers, Ledgers)
        self.assertIs(ImportedStreams, STREAMS)
        
        # Verify ledgers is accessible through imported STREAMS
        self.assertEqual(ImportedStreams["financial_management_ledgers"], ImportedLedgers)
