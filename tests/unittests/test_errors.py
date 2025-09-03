import unittest

from zeep.exceptions import Fault, TransportError, XMLSyntaxError
from tap_workday.client import SOAPErrorHandler
from tap_workday.exceptions import (
    WorkdaySOAPUnexpectedError,
    WorkdaySOAPFaultError,
    WorkdaySOAPTransportError,
    WorkdaySOAPXMLSyntaxError,
)


class TestSOAPErrorHandler(unittest.TestCase):
    """Unit tests for the SOAPErrorHandler static error handler."""

    def test_handle_fault(self):
        """Should raise WorkdaySOAPFaultError for Fault exception."""
        with self.assertRaises(WorkdaySOAPFaultError):
            SOAPErrorHandler.handle_error("op", Fault("msg", code="c", detail="d"))

    def test_handle_transport_error(self):
        """Should raise WorkdaySOAPTransportError for TransportError exception."""
        with self.assertRaises(WorkdaySOAPTransportError):
            SOAPErrorHandler.handle_error("op", TransportError(500, "fail"))

    def test_handle_xml_error(self):
        """Should raise WorkdaySOAPXMLSyntaxError for XMLSyntaxError exception."""
        with self.assertRaises(WorkdaySOAPXMLSyntaxError):
            SOAPErrorHandler.handle_error("op", XMLSyntaxError("fail"))

    def test_handle_unexpected_error(self):
        """Should raise WorkdaySOAPUnexpectedError for unknown exception."""
        with self.assertRaises(WorkdaySOAPUnexpectedError):
            SOAPErrorHandler.handle_error("op", RuntimeError("fail"))
