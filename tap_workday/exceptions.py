"""
Centralized exception definitions for Workday SOAP API operations.
"""


class WorkdaySOAPError(Exception):
    """Base exception for all Workday SOAP errors."""


class WorkdaySOAPFaultError(WorkdaySOAPError):
    """Raised when a SOAP Fault is returned by the server."""


class WorkdaySOAPTransportError(WorkdaySOAPError):
    """Raised for HTTP/transport-level issues."""


class WorkdaySOAPXMLSyntaxError(WorkdaySOAPError):
    """Raised when the SOAP response XML is invalid."""


class WorkdaySOAPUnexpectedError(WorkdaySOAPError):
    """Raised for unexpected/unhandled exceptions."""


class WorkdayBackoffError(WorkdaySOAPError):
    """Raised for retryable/backoff conditions."""
