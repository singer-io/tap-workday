from enum import Enum
from typing import Any, Dict, Mapping

import backoff
import requests
from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout
from singer import get_logger
from zeep import Client as ZeepClient
from zeep.exceptions import Fault, TransportError, XMLSyntaxError
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken
from zeep import Settings

from tap_workday.exceptions import (
    WorkdayAuthenticationError,
    WorkdayBackoffError,
    WorkdaySOAPFaultError,
    WorkdaySOAPTransportError,
    WorkdaySOAPUnexpectedError,
    WorkdaySOAPXMLSyntaxError,
    WORKDAY_AUTHN_ERROR_PATTERNS,
)

LOGGER = get_logger()


class DefaultValues(Enum):
    """Configuration defaults and constants"""

    REQUEST_TIMEOUT = 300
    SERVICE = "Human_Resources"
    VERSION = "v45.0"
    MAX_RETRIES = 5
    BACKOFF_FACTOR = 2


class SOAPErrorHandler:
    """Centralized SOAP error handler with unified message formatting"""

    # Exception mapping as class attribute - more cohesive than separate class
    EXCEPTION_MAPPINGS = {
        Fault: (WorkdaySOAPFaultError, "SOAP Fault"),
        TransportError: (WorkdaySOAPTransportError, "Transport Error"),
        XMLSyntaxError: (WorkdaySOAPXMLSyntaxError, "XML Error"),
    }

    @classmethod
    def _get_exception_details(cls, exc: Exception) -> str:
        """Extract specific details from different exception types"""
        if isinstance(exc, Fault):
            return f"faultcode='{exc.code}', faultstring='{exc.message}', detail='{exc.detail}'"
        elif isinstance(exc, TransportError):
            return f"status_code={getattr(exc, 'status_code', 'N/A')}, message='{str(exc)}'"
        elif isinstance(exc, XMLSyntaxError):
            return f"Invalid SOAP XML response: {exc}"
        else:
            return f"Exception={exc}"

    @classmethod
    def _get_error_message(cls, operation_name: str, exc: Exception) -> str:
        """Generate unified error message for different exception types"""
        if isinstance(exc, Fault):
            return f"SOAP Fault in '{operation_name}': {exc.message}"
        elif isinstance(exc, TransportError):
            return f"Transport error in '{operation_name}': {str(exc)}"
        elif isinstance(exc, XMLSyntaxError):
            return f"Invalid SOAP XML in '{operation_name}': {exc}"
        else:
            return f"Unexpected error in '{operation_name}': {exc}"

    @classmethod
    def handle_error(cls, operation_name: str, exc: Exception) -> None:
        """Log SOAP errors with unified format and raise appropriate WorkdaySOAPError exceptions"""
        exc_type = type(exc)
        workday_exc_class, error_type = cls.EXCEPTION_MAPPINGS.get(
            exc_type, (WorkdaySOAPUnexpectedError, "Unexpected Error")
        )

        # Unified logging format for all exception types
        exception_details = cls._get_exception_details(exc)
        LOGGER.error(
            f"[{error_type}] Operation='{operation_name}', {exception_details}"
        )

        # Generate appropriate error message and raise exception
        error_msg = cls._get_error_message(operation_name, exc)
        raise workday_exc_class(error_msg) from exc


class Client:
    """Centralized SOAP client for Workday API calls"""

    # These are the base zeep/requests exceptions that should trigger retries
    # We keep these separate because they represent different error categories:
    # 1. Network/connection issues (ConnectionResetError, ConnectionError, etc.)
    # 2. SOAP-specific issues (Fault, TransportError, XMLSyntaxError)
    # 3. Application-specific backoff signals (WorkdayBackoffError)
    RETRYABLE_EXCEPTIONS = (
        # Network/HTTP level exceptions
        ConnectionResetError,
        ConnectionError,
        ChunkedEncodingError,
        Timeout,
        # Application level retry signal
        WorkdayBackoffError,
        # SOAP level exceptions that should be retried
        Fault,
        TransportError,
        XMLSyntaxError,
    )

    def __init__(
        self,
        config: Mapping[str, Any],
        service: str = DefaultValues.SERVICE.value,
        version: str = DefaultValues.VERSION.value,
    ) -> None:
        self.config = config
        self.service = service
        self.version = version
        self.request_timeout = float(
            config.get("request_timeout", DefaultValues.REQUEST_TIMEOUT.value)
        )
        self._client = self._create_client()

    def _create_client(self) -> ZeepClient:
        session = requests.Session()
        session.verify = True
        transport = Transport(session=session, timeout=self.request_timeout)
        wsdl = self._build_wsdl_url()

        # Configure ZEEP settings for more flexible XML parsing
        # This helps handle cases where element order differs from schema
        settings = Settings(strict=False, xml_huge_tree=True)

        return ZeepClient(
            wsdl=wsdl,
            wsse=UsernameToken(self.config["username"], self.config["password"]),
            transport=transport,
            settings=settings,
        )

    def _build_wsdl_url(self) -> str:
        return (
            f"https://{self.config['hostname']}/ccx/service/"
            f"{self.config['tenant']}/{self.service}/{self.version}?wsdl"
        )

    def _execute_operation(self, operation_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a SOAP operation with error handling.
        """
        try:
            return getattr(self._client.service, operation_name)(*args, **kwargs)
        except Exception as exc:
            SOAPErrorHandler.handle_error(operation_name, exc)

    def check_access(self, operation_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Check access permissions for a Workday service operation without retry logic.
        Uses direct execution without backoff retries for discovery/access validation.
        """
        return self._execute_operation(operation_name, *args, **kwargs)

    def check_credentials(self) -> None:
        """
        Validate credentials with a lightweight SOAP call before discovery or sync.

        Raises WorkdayAuthenticationError (with CRITICAL log) on invalid/expired credentials.
        Non-authentication errors (authorization faults, non-401 transport issues) are
        silently ignored so they do not block discovery.
        """
        if not self.config:
            return

        try:
            probe = Client(self.config, service="Human_Resources")
            probe.check_access("Get_Workers")
        except WorkdaySOAPTransportError as e:
            err_lower = str(e).lower()
            status_code = getattr(e, 'status_code', 0)
            if status_code == 401 or any(p.lower() in err_lower for p in WORKDAY_AUTHN_ERROR_PATTERNS):
                raise WorkdayAuthenticationError(
                    "Authentication failure: invalid or expired credentials. "
                    "Verify the username and password in the tap config."
                ) from e
        except WorkdaySOAPFaultError as e:
            err_lower = str(e).lower()
            if any(p.lower() in err_lower for p in WORKDAY_AUTHN_ERROR_PATTERNS):
                raise WorkdayAuthenticationError(
                    "Authentication failure: invalid or expired credentials. "
                    "Verify the username and password in the tap config."
                ) from e
            # Authorization fault only — credentials are valid, do not block discovery
        except Exception as e:
            LOGGER.error("Unexpected error during credential check: %s", str(e))
            raise

    @backoff.on_exception(
        wait_gen=backoff.expo,
        exception=RETRYABLE_EXCEPTIONS,
        max_tries=DefaultValues.MAX_RETRIES.value,
        factor=DefaultValues.BACKOFF_FACTOR.value,
    )
    def call(self, operation_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a SOAP operation with retry logic for production data operations.
        Uses the same core logic as check_access but with exponential backoff on failures.
        """
        return self._execute_operation(operation_name, *args, **kwargs)

    def call_with_raw_response(self, operation_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Alternative method to call SOAP operations with raw XML response handling.
        Useful when strict schema validation causes issues with element ordering.
        """
        try:
            binding = self._client.service._binding._operations[operation_name]

            envelope, http_headers = binding.create(
                *args, 
                _soapheaders=self._client.wsse.create_header() if self._client.wsse else None,
                **kwargs
            )

            response = self._client.transport.post_xml(
                binding.location,
                envelope,
                http_headers
            )

            return binding.process_reply(self._client, operation_name, response.content)
        except Exception as exc:
            try:
                # Fallback to standard call - the raw XML approach has WSSE complications too
                return getattr(self._client.service, operation_name)(*args, **kwargs)
            except Exception as fallback_exc:
                SOAPErrorHandler.handle_error(operation_name, fallback_exc)
