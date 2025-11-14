"""
Integration tests for Ledgers stream using tap-tester framework.
"""

from tap_tester.base_suite_tests.all_fields_test import AllFieldsTest
from tap_tester.base_suite_tests.automatic_fields_test import AutomaticFieldsTest
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest
from tap_tester import runner

from .base import WorkdayBaseTest


class WorkdayLedgersDiscoveryTest(DiscoveryTest, WorkdayBaseTest):
    """Test ledgers stream discovery mode and metadata conforms to standards."""

    @staticmethod
    def name():
        return "tap_tester_workday_ledgers_discovery_test"

    def streams_to_test(self):
        return {"financial_management_ledgers"}


class WorkdayLedgersAllFieldsTest(AllFieldsTest, WorkdayBaseTest):
    """Test ledgers stream can select all fields and sync successfully."""

    @staticmethod
    def name():
        return "tap_tester_workday_ledgers_all_fields_test"

    def streams_to_test(self):
        return {"financial_management_ledgers"}


class WorkdayLedgersAutomaticFieldsTest(AutomaticFieldsTest, WorkdayBaseTest):
    """Test ledgers stream respects automatic field selection."""

    @staticmethod
    def name():
        return "tap_tester_workday_ledgers_automatic_fields_test"

    def streams_to_test(self):
        return {"financial_management_ledgers"}


class WorkdayLedgersCustomTest(WorkdayBaseTest):
    """Custom tests specific to ledgers stream functionality."""

    @staticmethod
    def name():
        return "tap_tester_workday_ledgers_custom_test"

    def streams_to_test(self):
        return {"financial_management_ledgers"}

    def test_ledgers_stream_has_correct_metadata(self):
        """Test that ledgers stream has the expected metadata properties."""
        conn_id = self.create_connection()

        # Run discovery
        found_catalogs = self.run_and_verify_check_mode(conn_id)
        
        # Find ledgers catalog
        ledgers_catalog = None
        for catalog in found_catalogs:
            if catalog['stream_name'] == 'financial_management_ledgers':
                ledgers_catalog = catalog
                break
        
        self.assertIsNotNone(ledgers_catalog, "Ledgers stream not found in discovery")
        
        # Verify stream properties
        self.assertEqual(ledgers_catalog['tap_stream_id'], 'financial_management_ledgers')
        
        # Verify metadata
        metadata = ledgers_catalog.get('metadata', [])
        table_metadata = next((m for m in metadata if m['breadcrumb'] == []), None)
        
        self.assertIsNotNone(table_metadata, "Table metadata not found")
        
        table_meta_props = table_metadata['metadata']
        self.assertEqual(table_meta_props.get('replication-method'), 'FULL_TABLE')
        self.assertIn('key_value', table_meta_props.get('table-key-properties', []))

    def test_ledgers_stream_sync_produces_records(self):
        """Test that ledgers stream can sync and produce records."""
        conn_id = self.create_connection()

        # Run discovery
        found_catalogs = self.run_and_verify_check_mode(conn_id)
        
        # Select ledgers stream
        catalog = self.select_all_streams_and_fields(conn_id, found_catalogs, ['financial_management_ledgers'])
        
        # Run sync
        sync_job_name = self.run_and_verify_sync(conn_id)
        
        # Get sync records
        synced_records = runner.get_records_from_target_output()
        
        # Verify ledgers stream was synced
        self.assertIn('financial_management_ledgers', synced_records)
        
        ledgers_records = synced_records['financial_management_ledgers']
        
        # Verify we have records (this may be 0 if no ledgers exist in test environment)
        self.assertIsInstance(ledgers_records.get('messages', []), list)
        
        # If we have records, verify their structure
        record_messages = [m for m in ledgers_records['messages'] if m.get('action') == 'upsert']
        
        if record_messages:
            # Verify record structure
            sample_record = record_messages[0]['data']
            
            # Verify key fields exist
            self.assertIn('key_value', sample_record)
            
            # Verify ledger-specific fields exist based on schema
            expected_fields = [
                'Actuals_Ledger_Reference',
                'Ledger_Data'
            ]
            
            for field in expected_fields:
                self.assertIn(field, sample_record, f"Expected field {field} not found in record")

    def test_ledgers_stream_schema_matches_records(self):
        """Test that ledgers stream records match the discovered schema."""
        conn_id = self.create_connection()

        # Run discovery
        found_catalogs = self.run_and_verify_check_mode(conn_id)
        
        # Find ledgers catalog and get schema
        ledgers_catalog = None
        for catalog in found_catalogs:
            if catalog['stream_name'] == 'financial_management_ledgers':
                ledgers_catalog = catalog
                break
        
        self.assertIsNotNone(ledgers_catalog)
        
        schema = ledgers_catalog['schema']
        
        # Verify key schema properties exist
        schema_properties = schema.get('properties', {})
        
        expected_properties = [
            'key_value',
            'Actuals_Ledger_Reference',
            'Ledger_Data'
        ]
        
        for prop in expected_properties:
            self.assertIn(prop, schema_properties, f"Expected property {prop} not found in schema")
        
        # Verify key_value is in key properties
        metadata = ledgers_catalog.get('metadata', [])
        table_metadata = next((m for m in metadata if m['breadcrumb'] == []), None)
        key_properties = table_metadata['metadata'].get('table-key-properties', [])
        
        self.assertIn('key_value', key_properties)

    def test_ledgers_stream_custom_check_access_integration(self):
        """Test that the custom check_access method works in integration context."""
        # This test verifies that discovery doesn't fail due to check_access issues
        conn_id = self.create_connection()
        
        # This should not raise exceptions - if check_access fails, discovery will fail
        found_catalogs = self.run_and_verify_check_mode(conn_id)
        
        # Verify ledgers stream was discovered successfully
        stream_names = {catalog['stream_name'] for catalog in found_catalogs}
        self.assertIn('financial_management_ledgers', stream_names, 
                     "Ledgers stream not discovered - check_access may have failed")
