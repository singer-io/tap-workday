from enum import Enum
from typing import Any, Mapping

import backoff
import requests
from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout
from singer import get_logger
from zeep import Client as ZeepClient
from zeep.exceptions import Fault, TransportError, XMLSyntaxError
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken

from tap_workday.exceptions import (
    WorkdayBackoffError,
    WorkdaySOAPFaultError,
    WorkdaySOAPTransportError,
    WorkdaySOAPUnexpectedError,
    WorkdaySOAPXMLSyntaxError,
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
        self.version = 'v45.0'
        self.request_timeout = float(
            config.get("request_timeout", DefaultValues.REQUEST_TIMEOUT.value)
        )
        self._client = self._create_client()

    def _create_client(self) -> ZeepClient:
        session = requests.Session()
        session.verify = True
        transport = Transport(session=session, timeout=self.request_timeout)
        wsdl = self._build_wsdl_url()
        return ZeepClient(
            wsdl=wsdl,
            wsse=UsernameToken(self.config["username"], self.config["password"]),
            transport=transport,
        )

    def _build_wsdl_url(self) -> str:
        return (
            f"https://{self.config['hostname']}/ccx/service/"
            f"{self.config['tenant']}/{self.service}/{self.version}?wsdl"
        )

    @backoff.on_exception(
        wait_gen=backoff.expo,
        exception=RETRYABLE_EXCEPTIONS,
        max_tries=DefaultValues.MAX_RETRIES.value,
        factor=DefaultValues.BACKOFF_FACTOR.value,
    )
    def call(self, operation_name: str, *args: Any, **kwargs: Any) -> Any:
        try:
            return getattr(self._client.service, operation_name)(*args, **kwargs)
        except Exception as exc:
            SOAPErrorHandler.handle_error(operation_name, exc)
