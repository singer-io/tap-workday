"""
Centralized exception definitions for Workday SOAP API operations.
"""

from zeep.exceptions import Fault, TransportError, XMLSyntaxError

# Patterns that indicate a SOAP-level authorization failure (credentials valid but lack permissions)
WORKDAY_AUTH_ERROR_PATTERNS = [
    'Processing error occurred. The task submitted is not authorized.',
    'not authorized',
    'authorization failed',
    'insufficient permissions',
]

# Patterns that indicate an HTTP-level authentication failure (invalid/expired credentials)
WORKDAY_AUTHN_ERROR_PATTERNS = [
    'http status 401',
    'authentication failed',
    'invalid credentials',
    'invalid username',
    'invalid password',
]


class WorkdaySOAPError(Exception):
    """Base exception for all Workday SOAP errors."""


class WorkdaySOAPFaultError(Fault, WorkdaySOAPError):
    """Raised when a SOAP Fault is returned by the server."""

    pass


class WorkdaySOAPTransportError(TransportError, WorkdaySOAPError):
    """Raised for HTTP/transport-level issues."""

    pass


class WorkdaySOAPXMLSyntaxError(XMLSyntaxError, WorkdaySOAPError):
    """Raised when the SOAP response XML is invalid."""

    pass


class WorkdaySOAPUnexpectedError(WorkdaySOAPError):
    """Raised for unexpected/unhandled exceptions."""

    pass


class WorkdayBackoffError(WorkdaySOAPError):
    """Raised for retryable/backoff conditions."""

    pass


class WorkdayForbiddenError(WorkdaySOAPError):
    """Raised when credentials lack access to all discoverable streams."""

    pass
