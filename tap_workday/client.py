import json
import time
from enum import Enum
from typing import Any, Dict, Mapping, Optional

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

# Auth mode sentinels
_AUTH_MODE_OAUTH = "oauth"
_AUTH_MODE_WSSECURITY = "wssecurity"


def _has_wssecurity_config(config: Mapping[str, Any]) -> bool:
    """Return True when the config contains username/password for WS-Security fallback."""
    return all(config.get(f) for f in ("username", "password"))


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


class WorkdayOAuthTokenManager:
    """
    Manages OAuth 2.0 access tokens for Workday SOAP requests.

    Uses the refresh_token grant: exchanges client_id + client_secret + refresh_token
    for a short-lived access_token that is sent as an HTTP ``Authorization: Bearer``
    header on every SOAP request instead of a WS-Security UsernameToken.

    Workday tenant pre-requisites (configured by a Workday administrator):
      - An OAuth 2.0 API client registered in the Workday tenant.
      - The client associated with an Integration System User (ISU) that has
        the required security-domain permissions.
      - A refresh token obtained via the Authorization Code flow and stored in
        the tap config under the ``refresh_token`` key.
    """

    EXPIRY_BUFFER_SECS = 60  # refresh proactively 60 s before actual expiry

    def __init__(self, config: Mapping[str, Any], config_path: Optional[str] = None) -> None:
        self._token_endpoint: str = config.get("token_endpoint") or (
            f"https://{config['hostname']}/ccx/oauth2/{config['tenant']}/token"
        )
        self._client_id: str = config["client_id"]
        self._client_secret: str = config["client_secret"]
        self._refresh_token: str = config["refresh_token"]
        # Workday uses rotating single-use refresh tokens.  We keep a mutable
        # reference to the config dict and its file path so that when Workday
        # returns a new refresh_token we can persist it for the next tap process.
        self._config = config
        self._config_path: Optional[str] = config_path
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0

    @property
    def is_valid(self) -> bool:
        """True when we hold a token that will not expire within the buffer window."""
        return (
            bool(self._access_token)
            and time.monotonic() < self._expires_at - self.EXPIRY_BUFFER_SECS
        )

    def fetch(self) -> str:
        """Force-fetch a new access token from the Workday token endpoint."""
        LOGGER.debug("Requesting OAuth 2.0 access token from Workday token endpoint")
        try:
            resp = requests.post(
                self._token_endpoint,
                auth=(self._client_id, self._client_secret),
                data={"grant_type": "refresh_token", "refresh_token": self._refresh_token},
                timeout=30,
                verify=True,
            )
        except requests.RequestException as exc:
            raise WorkdayAuthenticationError(
                f"OAuth token request failed (network error): {exc}"
            ) from exc

        if resp.status_code == 401:
            raise WorkdayAuthenticationError(
                "OAuth token request rejected (HTTP 401): "
                "verify client_id, client_secret, and refresh_token in the tap config."
            )
        if not resp.ok:
            raise WorkdayAuthenticationError(
                f"OAuth token request failed (HTTP {resp.status_code}): {resp.text[:300]}"
            )

        data = resp.json()
        self._access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._expires_at = time.monotonic() + expires_in

        # Workday rotates refresh tokens: each token response may contain a new
        # refresh_token that invalidates the previous one.  Persist it immediately
        # so the next tap process (which re-reads the config file) uses the valid token.
        # If no new refresh_token is returned (or it's empty), keep the existing one.
        new_refresh_token = data.get("refresh_token")
        if new_refresh_token:
            self._refresh_token = new_refresh_token
            self._config["refresh_token"] = new_refresh_token
            self._persist_config()

        LOGGER.debug("OAuth access token acquired (expires_in=%ds)", expires_in)
        return self._access_token

    def _persist_config(self) -> None:
        """Write the current config (including rotated refresh_token) back to disk."""
        if not self._config_path:
            LOGGER.debug("No config_path set; skipping refresh token persistence to disk")
            return
        try:
            with open(self._config_path, "w") as f:
                json.dump(self._config, f, indent=2)
            LOGGER.debug("Persisted rotated refresh token to %s", self._config_path)
        except OSError as exc:
            LOGGER.warning("Failed to persist rotated refresh token: %s", exc)

    def get(self) -> str:
        """Return a valid access token, fetching a fresh one if expired or absent."""
        if not self.is_valid:
            return self.fetch()
        return self._access_token  # type: ignore[return-value]


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

    _FALLBACK_HINT = "set 'enable_wssecurity_fallback: true' in config to enable it"

    def __init__(
        self,
        config: Mapping[str, Any],
        service: str = DefaultValues.SERVICE.value,
        version: str = DefaultValues.VERSION.value,
        config_path: Optional[str] = None,
    ) -> None:
        self.config = config
        self.service = service
        self.version = version
        self.request_timeout = float(
            config.get("request_timeout", DefaultValues.REQUEST_TIMEOUT.value)
        )
        # OAuth 2.0 is always the primary auth mode (client_id, client_secret,
        # refresh_token are required config keys).  WS-Security username/password
        # is an optional fallback used only when OAuth authentication fails.
        self._auth_mode: str = _AUTH_MODE_OAUTH
        # config_path is forwarded so rotated refresh tokens can be persisted to disk
        self._token_manager: Optional[WorkdayOAuthTokenManager] = WorkdayOAuthTokenManager(config, config_path=config_path)
        self._session: Optional[requests.Session] = None
        self._client = self._create_client()

    def _create_client(self) -> ZeepClient:
        session = requests.Session()
        session.verify = True
        self._session = session  # stored so _update_bearer_header can mutate it later
        transport = Transport(session=session, timeout=self.request_timeout)
        wsdl = self._build_wsdl_url()
        settings = Settings(strict=False, xml_huge_tree=True)

        if self._auth_mode == _AUTH_MODE_OAUTH:
            # OAuth 2.0 Bearer token mode: do NOT fetch a token here.
            # The token is acquired lazily on the first SOAP operation via
            # _update_bearer_header(), or explicitly and up-front in
            # check_credentials().  This allows check_credentials to own the
            # error-handling / fallback logic without _create_client raising.
            wsse = None
            LOGGER.debug("SOAP client created in OAuth 2.0 Bearer token mode")
        else:
            # WS-Security UsernameToken mode: credentials embedded in every SOAP envelope.
            wsse = UsernameToken(self.config["username"], self.config["password"])
            LOGGER.debug("SOAP client created in WS-Security UsernameToken mode")

        return ZeepClient(
            wsdl=wsdl,
            wsse=wsse,
            transport=transport,
            settings=settings,
        )

    @property
    def _wssecurity_fallback_enabled(self) -> bool:
        """True when the config opts in to WS-Security username/password fallback."""
        return bool(self.config.get("enable_wssecurity_fallback", False))

    def _build_wsdl_url(self) -> str:
        return (
            f"https://{self.config['hostname']}/ccx/service/"
            f"{self.config['tenant']}/{self.service}/{self.version}?wsdl"
        )

    def _update_bearer_header(self) -> None:
        """Ensure the session Authorization header holds a non-expired Bearer token."""
        token = self._token_manager.get()  # type: ignore[union-attr]
        self._session.headers["Authorization"] = f"Bearer {token}"  # type: ignore[union-attr]

    def _switch_to_wssecurity_fallback(self) -> None:
        """
        Tear down OAuth mode and rebuild the SOAP client in WS-Security UsernameToken mode.

        Called when OAuth token acquisition or refresh fails and username/password
        credentials are present in the config as a fallback.

        Raises WorkdayAuthenticationError if the required username/password fields
        are absent from the config (no fallback available).
        """
        if not _has_wssecurity_config(self.config):
            raise WorkdayAuthenticationError(
                "OAuth authentication failed and no username/password fallback credentials "
                "are present in the tap config. Authentication cannot continue."
            )
        LOGGER.debug("Switching authentication mode to WS-Security UsernameToken fallback")
        self._auth_mode = _AUTH_MODE_WSSECURITY
        self._token_manager = None
        self._client = self._create_client()  # rebuild without Bearer token

    def _execute_operation(self, operation_name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a SOAP operation with error handling and automatic auth fallback."""
        if self._auth_mode == _AUTH_MODE_OAUTH:
            try:
                self._update_bearer_header()
            except WorkdayAuthenticationError as auth_exc:
                if not self._wssecurity_fallback_enabled:
                    raise WorkdayAuthenticationError(
                        f"OAuth token refresh failed for '{operation_name}' and "
                        f"WS-Security fallback is disabled ({self._FALLBACK_HINT})."
                    ) from auth_exc
                LOGGER.warning(
                    "OAuth token update failed for '%s': %s. Attempting WS-Security fallback.",
                    operation_name, auth_exc,
                )
                self._switch_to_wssecurity_fallback()
        try:
            return getattr(self._client.service, operation_name)(*args, **kwargs)
        except TransportError as exc:
            # In OAuth mode a 401 usually means the access token expired mid-run.
            # Attempt one token refresh, then fall back to WS-Security if that also fails.
            if self._auth_mode == _AUTH_MODE_OAUTH and getattr(exc, "status_code", None) == 401:
                LOGGER.debug(
                    "Bearer token rejected (HTTP 401) for '%s'; attempting token refresh",
                    operation_name,
                )
                try:
                    self._token_manager.fetch()  # force-fetch, bypass is_valid
                    self._update_bearer_header()
                    LOGGER.debug("Token refreshed; retrying '%s'", operation_name)
                    return getattr(self._client.service, operation_name)(*args, **kwargs)
                except WorkdayAuthenticationError as auth_exc:
                    LOGGER.warning(
                        "OAuth token refresh failed for '%s': %s.",
                        operation_name, auth_exc,
                    )
                    if not self._wssecurity_fallback_enabled:
                        raise WorkdayAuthenticationError(
                            f"OAuth token refresh failed for '{operation_name}' and "
                            f"WS-Security fallback is disabled ({self._FALLBACK_HINT})."
                        ) from auth_exc
                    LOGGER.warning("Attempting WS-Security fallback for '%s'.", operation_name)
                    self._switch_to_wssecurity_fallback()  # raises if no u/p in config
                    try:
                        return getattr(self._client.service, operation_name)(*args, **kwargs)
                    except Exception as fallback_exc:
                        SOAPErrorHandler.handle_error(operation_name, fallback_exc)
                except Exception as retry_exc:
                    SOAPErrorHandler.handle_error(operation_name, retry_exc)
            SOAPErrorHandler.handle_error(operation_name, exc)
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
        Validate authentication before discovery or sync.

        Flow:
          1. If OAuth fields are present, attempt OAuth token acquisition first.
             - Success  → continue in OAuth mode.
             - Failure  → if username/password are present, log a warning and switch
               to WS-Security UsernameToken fallback mode.
             - Failure + no username/password → raise WorkdayAuthenticationError and stop.
          2. Run a lightweight SOAP probe (Get_Workers) in whatever mode is now active
             to confirm Workday accepts the credentials.

        Raises WorkdayAuthenticationError when all available authentication paths fail.
        Non-authentication SOAP errors (e.g. domain authorisation faults) are silently
        ignored so they do not block discovery.
        """
        if not self.config:
            return

        # ── Step 1: OAuth primary path ───────────────────────────────────────────────
        if self._auth_mode == _AUTH_MODE_OAUTH:
            try:
                LOGGER.debug("Attempting OAuth 2.0 authentication")
                self._token_manager.fetch()  # type: ignore[union-attr]
                LOGGER.debug("OAuth 2.0 token acquired successfully; continuing in OAuth mode")
            except Exception as oauth_exc:
                LOGGER.warning("OAuth authentication failed: %s", oauth_exc)
                if not self._wssecurity_fallback_enabled:
                    raise WorkdayAuthenticationError(
                        f"OAuth authentication failed. WS-Security fallback is disabled "
                        f"({self._FALLBACK_HINT})."
                    ) from oauth_exc
                if not _has_wssecurity_config(self.config):
                    raise WorkdayAuthenticationError(
                        "OAuth authentication failed and no username/password fallback "
                        "credentials are configured. Discovery/sync cannot continue."
                    ) from oauth_exc
                LOGGER.debug(
                    "username/password credentials found; attempting WS-Security fallback"
                )
                self._switch_to_wssecurity_fallback()

        # ── Step 2: SOAP probe (runs in whichever mode is now active) ────────────────
        auth_label = (
            "OAuth 2.0 Bearer token"
            if self._auth_mode == _AUTH_MODE_OAUTH
            else "username/password (WS-Security)"
        )
        LOGGER.debug("Validating %s with a lightweight SOAP probe", auth_label)

        try:
            self.check_access("Get_Workers")
            LOGGER.debug("Authentication validated successfully using %s", auth_label)
        except WorkdaySOAPTransportError as e:
            status_code = getattr(e, "status_code", 0)
            err_lower = str(e).lower()
            if status_code == 401 or any(p.lower() in err_lower for p in WORKDAY_AUTHN_ERROR_PATTERNS):
                raise WorkdayAuthenticationError(
                    f"Authentication failure: {auth_label} rejected by Workday. "
                    "Verify the credentials in the tap config."
                ) from e
        except WorkdaySOAPFaultError as e:
            err_lower = str(e).lower()
            if any(p.lower() in err_lower for p in WORKDAY_AUTHN_ERROR_PATTERNS):
                raise WorkdayAuthenticationError(
                    f"Authentication failure: {auth_label} rejected by Workday. "
                    "Verify the credentials in the tap config."
                ) from e
        except WorkdayAuthenticationError:
            raise
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
