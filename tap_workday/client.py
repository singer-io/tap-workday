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
    WorkdaySOAPError,
    WorkdaySOAPFaultError,
    WorkdaySOAPTransportError,
    WorkdaySOAPUnexpectedError,
    WorkdaySOAPXMLSyntaxError,
)

LOGGER = get_logger()
REQUEST_TIMEOUT = 300


class SOAPErrorHandler:
    """Centralized SOAP error handler."""

    @staticmethod
    def handle_error(operation_name: str, exc: Exception) -> None:
        """
        Log SOAP errors and raise unified WorkdaySOAPError exceptions.
        """
        if isinstance(exc, Fault):
            LOGGER.error(
                f"[SOAP Fault] Operation='{operation_name}', "
                f"faultcode='{exc.code}', faultstring='{exc.message}', detail='{exc.detail}'"
            )
            raise WorkdaySOAPFaultError(
                f"SOAP Fault in '{operation_name}': {exc.message}"
            ) from exc

        elif isinstance(exc, TransportError):
            LOGGER.error(
                f"[Transport Error] Operation='{operation_name}', "
                f"status_code={getattr(exc, 'status_code', 'N/A')}, message='{str(exc)}'"
            )
            raise WorkdaySOAPTransportError(
                f"Transport error in '{operation_name}': {str(exc)}"
            ) from exc

        elif isinstance(exc, XMLSyntaxError):
            LOGGER.error(
                f"[XML Error] Operation='{operation_name}', Invalid SOAP XML response: {exc}"
            )
            raise WorkdaySOAPXMLSyntaxError(
                f"Invalid SOAP XML in '{operation_name}': {exc}"
            ) from exc

        else:
            LOGGER.exception(
                f"[Unexpected Error] Operation='{operation_name}', Exception={exc}"
            )
            raise WorkdaySOAPUnexpectedError(
                f"Unexpected error in '{operation_name}': {exc}"
            ) from exc


class Client:
    """Centralized SOAP client for Workday API calls."""

    def __init__(
        self,
        config: Mapping[str, Any],
        service: str = "Human_Resources",
        version: str = "v44.2",
    ) -> None:
        self.config = config
        self.service = service
        self.version = config.get("version", version)
        self.request_timeout = float(config.get("request_timeout", REQUEST_TIMEOUT))
        self._client = self._create_client()

    def _create_client(self) -> ZeepClient:
        session = requests.Session()
        session.verify = True
        transport = Transport(session=session, timeout=self.request_timeout)
        wsdl = (
            f"https://{self.config['hostname']}/ccx/service/"
            f"{self.config['tenant']}/{self.service}/{self.version}?wsdl"
        )
        return ZeepClient(
            wsdl=wsdl,
            wsse=UsernameToken(self.config["username"], self.config["password"]),
            transport=transport,
        )

    @backoff.on_exception(
        wait_gen=backoff.expo,
        exception=(
            ConnectionResetError,
            ConnectionError,
            ChunkedEncodingError,
            Timeout,
            WorkdayBackoffError,
            Fault,
            TransportError,
            XMLSyntaxError,
        ),
        max_tries=5,
        factor=2,
    )
    def call(self, operation_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Call a SOAP operation with retry, timeout, and centralized error handling.
        """
        try:
            result = getattr(self._client.service, operation_name)(*args, **kwargs)
            return result
        except Exception as exc:
            SOAPErrorHandler.handle_error(operation_name, exc)
