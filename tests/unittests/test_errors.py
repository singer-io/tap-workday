import unittest
from tap_workday.client import SOAPErrorHandler
from tap_workday.exceptions import WorkdaySOAPUnexpectedError

class TestSOAPErrorHandler(unittest.TestCase):
    """Unit tests for the SOAPErrorHandler static error handler."""

    def test_handle_unexpected_error(self):
        """Should raise WorkdaySOAPUnexpectedError for any exception."""
        with self.assertRaises(WorkdaySOAPUnexpectedError) as ctx:
            SOAPErrorHandler.handle_error("op", RuntimeError("fail"))
        self.assertIn("Unexpected error in 'op'", str(ctx.exception))

    def test_error_message_and_chaining(self):
        """Should preserve error message and exception chaining."""
        try:
            SOAPErrorHandler.handle_error("op", ValueError("bad value"))
        except WorkdaySOAPUnexpectedError as exc:
            self.assertIn("bad value", str(exc))
            self.assertIsInstance(exc.__cause__, ValueError)
