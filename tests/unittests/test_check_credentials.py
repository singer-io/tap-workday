"""Unit tests for the check_credentials function in tap_workday.client."""

import unittest
from unittest.mock import Mock, patch
from requests.exceptions import ConnectionError, Timeout

from tap_workday.client import check_credentials
from tap_workday.exceptions import WorkdayAuthenticationError


CONFIG = {
    "hostname": "wd2-impl-services1.workday.com",
    "tenant": "test_tenant",
    "username": "test_user",
    "password": "test_pass",
}

SOAP_SUCCESS_BODY = "<SOAP-ENV:Envelope><SOAP-ENV:Body><workers/></SOAP-ENV:Body></SOAP-ENV:Envelope>"
SOAP_AUTH_FAULT_BODY = "<faultcode>SOAP-ENV:Client.authenticationError</faultcode><faultstring>Invalid credentials</faultstring>"
SOAP_AUTHZ_FAULT_BODY = "<faultcode>SOAP-ENV:Client</faultcode><faultstring>Processing error occurred. The task submitted is not authorized.</faultstring>"


def _mock_response(status_code, text=""):
    response = Mock()
    response.status_code = status_code
    response.text = text
    return response


class TestCheckCredentials(unittest.TestCase):

    @patch("tap_workday.client.requests.post")
    def test_valid_credentials_http_200(self, mock_post):
        """HTTP 200 success → credentials accepted, no exception."""
        mock_post.return_value = _mock_response(200, SOAP_SUCCESS_BODY)
        check_credentials(CONFIG)  # must not raise

    @patch("tap_workday.client.requests.post")
    def test_valid_credentials_authz_fault_http_500(self, mock_post):
        """HTTP 500 with stream-level authorization fault → credentials still valid."""
        mock_post.return_value = _mock_response(500, SOAP_AUTHZ_FAULT_BODY)
        check_credentials(CONFIG)  # must not raise

    @patch("tap_workday.client.requests.post")
    def test_invalid_credentials_http_401(self, mock_post):
        """HTTP 401 → WorkdayAuthenticationError raised."""
        mock_post.return_value = _mock_response(401, "Unauthorized")
        with self.assertRaises(WorkdayAuthenticationError):
            check_credentials(CONFIG)

    @patch("tap_workday.client.requests.post")
    def test_invalid_credentials_auth_fault_in_body(self, mock_post):
        """SOAP authentication fault in response body → WorkdayAuthenticationError raised."""
        mock_post.return_value = _mock_response(500, SOAP_AUTH_FAULT_BODY)
        with self.assertRaises(WorkdayAuthenticationError):
            check_credentials(CONFIG)

    @patch("tap_workday.client.requests.post", side_effect=ConnectionError("timeout"))
    def test_connection_error_is_propagated(self, _mock_post):
        """Network-level ConnectionError is re-raised unchanged."""
        with self.assertRaises(ConnectionError):
            check_credentials(CONFIG)

    @patch("tap_workday.client.requests.post", side_effect=Timeout("timed out"))
    def test_timeout_is_propagated(self, _mock_post):
        """Timeout is re-raised unchanged."""
        with self.assertRaises(Timeout):
            check_credentials(CONFIG)

    @patch("tap_workday.client.requests.post")
    def test_request_targets_correct_url(self, mock_post):
        """POST is sent to the expected Human_Resources SOAP endpoint."""
        mock_post.return_value = _mock_response(200, SOAP_SUCCESS_BODY)
        check_credentials(CONFIG)
        call_url = mock_post.call_args[0][0]
        self.assertIn("Human_Resources", call_url)
        self.assertIn(CONFIG["tenant"], call_url)
        self.assertIn(CONFIG["hostname"], call_url)
