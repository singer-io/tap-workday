from typing import Any, Dict, Mapping, Optional, Tuple

import backoff
import requests
from requests import session
from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout
from singer import get_logger, metrics
from zeep import Client as ZeepClient
from zeep.wsse.username import UsernameToken

from tap_workday.exceptions import (
    ERROR_CODE_EXCEPTION_MAPPING,
    workdayBackoffError,
    workdayError,
)

LOGGER = get_logger()
REQUEST_TIMEOUT = 300


def raise_for_error(response: requests.Response) -> None:
    """Raises the associated response exception. Takes in a response object,
    checks the status code, and throws the associated exception based on the
    status code.

    :param resp: requests.Response object
    """
    try:
        response_json = response.json()
    except Exception:
        response_json = {}
    if response.status_code not in [200, 201, 204]:
        if response_json.get("error"):
            message = f"HTTP-error-code: {response.status_code}, Error: {response_json.get('error')}"
        else:
            error_message = ERROR_CODE_EXCEPTION_MAPPING.get(
                response.status_code, {}
            ).get("message", "Unknown Error")
            message = f"HTTP-error-code: {response.status_code}, Error: {response_json.get('message', error_message)}"
        exc = ERROR_CODE_EXCEPTION_MAPPING.get(response.status_code, {}).get(
            "raise_exception", workdayError
        )
        raise exc(message, response) from None


class Client:
    """
    A Wrapper class.
    ~~~
    Performs:
     - Authentication
     - Response parsing
     - HTTP Error handling and retry
    """

    def __init__(self, config: Mapping[str, Any]) -> None:
        self.config = config
        self._session = session()
        self.base_url = ""
        config_request_timeout = config.get("request_timeout")
        self.request_timeout = (
            float(config_request_timeout) if config_request_timeout else REQUEST_TIMEOUT
        )

    def __enter__(self):
        self.check_api_credentials()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._session.close()

    def check_api_credentials(self) -> None:
        pass

    def authenticate(self, headers: Dict, params: Dict) -> Tuple[Dict, Dict]:
        """Authenticates the request with the token"""
        headers[""] = self.config[""]
        return headers, params

    def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        path: Optional[str] = None,
    ) -> Any:
        """
        Sends an HTTP request to the specified API endpoint.
        """
        params = params or {}
        headers = headers or {}
        body = body or {}
        endpoint = endpoint or f"{self.base_url}/{path}"
        headers, params = self.authenticate(headers, params)
        return self.__make_request(
            method,
            endpoint,
            headers=headers,
            params=params,
            data=body,
            timeout=self.request_timeout,
        )

    @backoff.on_exception(
        wait_gen=backoff.expo,
        exception=(
            ConnectionResetError,
            ConnectionError,
            ChunkedEncodingError,
            Timeout,
            workdayBackoffError,
        ),
        max_tries=5,
        factor=2,
    )
    def __make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[Mapping[Any, Any]]:
        """Performs HTTP Operations."""
        method = method.upper()
        with metrics.http_request_timer(endpoint):
            if method in ("GET", "POST"):
                if method == "GET":
                    kwargs.pop("data", None)
                response = self._session.request(method, endpoint, **kwargs)
                raise_for_error(response)
            else:
                raise ValueError(f"Unsupported method: {method}")

        return response.json()


class SOAPClient:
    """
    Wrapper for Workday SOAP API.
    Handles:
     - WSDL construction
     - Zeep client creation
     - Authentication with UsernameToken
     - Request retries with backoff
    """

    def __init__(
        self, config: Mapping[str, Any], service: str, version: str = "v44.2"
    ) -> None:
        self.config = config
        self.tenant = config["tenant"]
        self.hostname = config["hostname"]
        self.username = config["username"]
        self.password = config["password"]
        self.service = service
        self.version = version
        config_request_timeout = config.get("request_timeout")
        self.request_timeout = (
            float(config_request_timeout) if config_request_timeout else REQUEST_TIMEOUT
        )
        self._client = self._create_client()

    def _create_client(self):
        wsdl = f"https://{self.hostname}/ccx/service/{self.tenant}/{self.service}/{self.version}?wsdl"
        return ZeepClient(wsdl=wsdl, wsse=UsernameToken(self.username, self.password))

    @property
    def service_proxy(self):
        """Expose the Zeep service proxy for operations."""
        return self._client.service

    @backoff.on_exception(
        wait_gen=backoff.expo,
        exception=(ConnectionError, Timeout, workdayBackoffError),
        max_tries=5,
        factor=2,
    )
    def call(self, operation_name: str, *args, **kwargs):
        """Call a SOAP operation with retry and timeout."""
        operation = getattr(self._client.service, operation_name)
        return operation(*args, **kwargs)
