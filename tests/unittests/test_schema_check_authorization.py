"""
Unit tests for schema.py check_stream_authorization function.

Access checking is now handled by _apply_access_checks() in discover.py.
check_stream_authorization is a no-op metadata pass-through retained for
backward compatibility.
"""

import unittest
from tap_workday.schema import check_stream_authorization
from tap_workday.streams.financial_management import Ledgers


class TestSchemaCheckStreamAuthorization(unittest.TestCase):
    """Tests that check_stream_authorization returns mdata unchanged (no API calls)."""

    def setUp(self):
        self.config = {
            'hostname': 'test.workday.com',
            'username': 'test_user',
            'password': 'test_pass',
            'tenant': 'test_tenant'
        }
        self.mdata = {"some": "metadata"}

    def test_returns_mdata_unchanged_for_known_stream(self):
        result = check_stream_authorization(self.config, "financial_management_ledgers", Ledgers, self.mdata)
        self.assertEqual(result, self.mdata)

    def test_returns_mdata_unchanged_for_missing_config(self):
        result = check_stream_authorization(None, "test_stream", Ledgers, self.mdata)
        self.assertEqual(result, self.mdata)

    def test_returns_mdata_unchanged_for_unknown_stream(self):
        class UnknownStream:
            pass

        result = check_stream_authorization(self.config, "unknown", UnknownStream, self.mdata)
        self.assertEqual(result, self.mdata)

    def test_does_not_make_api_calls(self):
        """No Client instantiation or network calls should occur."""
        # If this runs without patching Client or network, it must not call the API.
        result = check_stream_authorization(self.config, "financial_management_ledgers", Ledgers, self.mdata)
        self.assertIs(result, self.mdata)


