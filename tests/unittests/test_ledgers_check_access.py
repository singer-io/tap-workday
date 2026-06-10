"""
Unit tests for Ledgers stream custom check_access method.
"""

import unittest
from unittest.mock import Mock, patch
from tap_workday.streams.financial_management import Ledgers, Journals
from tap_workday.client import Client
from tap_workday.exceptions import WorkdayForbiddenError, WorkdaySOAPFaultError


class TestLedgersCheckAccess(unittest.TestCase):
    """Test the Ledgers stream custom check_access instance method."""

    def _make_ledgers(self, mock_check_access_client):
        """Create a Ledgers instance with get_client() mocked."""
        mock_tap_client = Mock(spec=Client)
        mock_tap_client.config = {
            'hostname': 'test.workday.com',
            'username': 'user',
            'password': 'pass',
            'tenant': 'tenant',
        }
        ledgers = Ledgers(client=mock_tap_client)
        ledgers.get_client = Mock(return_value=mock_check_access_client)
        return ledgers

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=Client)

    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_check_access_calls_client_with_correct_params(self, mock_extract_ledger_ids):
        """Test that check_access calls client.check_access with expected parameters."""
        mock_extract_ledger_ids.return_value = {"REAL_LEDGER_ID"}
        self.mock_client.check_access.return_value = {"success": True}

        ledgers = self._make_ledgers(self.mock_client)
        result = ledgers.check_access()

        # Verify the ledger ID extraction was called with max_pages=1
        mock_extract_ledger_ids.assert_called_once_with(self.mock_client, max_pages=1)

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
        for key, value in expected_request_ref.items():
            self.assertEqual(call_args[1][key], value)

        self.assertTrue(result)

    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_check_access_fallback_when_no_ledger_id_found(self, mock_extract_ledger_ids):
        """Test that check_access falls back to TEST_LEDGER when no real ledger ID is found."""
        mock_extract_ledger_ids.return_value = set()
        self.mock_client.check_access.return_value = {"success": True}

        ledgers = self._make_ledgers(self.mock_client)
        ledgers.check_access()

        mock_extract_ledger_ids.assert_called_once_with(self.mock_client, max_pages=1)
        call_args = self.mock_client.check_access.call_args
        actual_ledger_id = call_args[1]['Request_Reference']['Actuals_Ledger_Reference']['ID'][0]['_value_1']
        self.assertEqual(actual_ledger_id, 'TEST_LEDGER')

    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_check_access_fallback_when_exception_occurs(self, mock_extract_ledger_ids):
        """Test that check_access falls back to TEST_LEDGER when extraction raises."""
        mock_extract_ledger_ids.side_effect = Exception("Journal API error")
        self.mock_client.check_access.return_value = {"success": True}

        ledgers = self._make_ledgers(self.mock_client)
        ledgers.check_access()

        call_args = self.mock_client.check_access.call_args
        actual_ledger_id = call_args[1]['Request_Reference']['Actuals_Ledger_Reference']['ID'][0]['_value_1']
        self.assertEqual(actual_ledger_id, 'TEST_LEDGER')

    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_check_access_reraises_exceptions(self, mock_extract_ledger_ids):
        """Test that check_access properly re-raises non-auth exceptions from client."""
        mock_extract_ledger_ids.return_value = set()
        test_exception = Exception("Test API error")
        self.mock_client.check_access.side_effect = test_exception

        ledgers = self._make_ledgers(self.mock_client)
        with self.assertRaises(Exception) as ctx:
            ledgers.check_access()

        self.assertEqual(str(ctx.exception), "Test API error")

    @patch.object(Journals, 'extract_ledger_ids_from_journals_api')
    def test_check_access_raises_forbidden_on_auth_fault(self, mock_extract_ledger_ids):
        """Test that check_access converts auth SOAP faults to WorkdayForbiddenError."""
        mock_extract_ledger_ids.return_value = set()
        self.mock_client.check_access.side_effect = WorkdaySOAPFaultError(
            "Processing error occurred. The task submitted is not authorized."
        )

        ledgers = self._make_ledgers(self.mock_client)
        with self.assertRaises(WorkdayForbiddenError):
            ledgers.check_access()

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

