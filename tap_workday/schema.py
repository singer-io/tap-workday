import json
import os
from typing import Dict, Tuple

import singer
from singer import metadata

from tap_workday.client import Client
from tap_workday.exceptions import (
    WorkdayForbiddenError,
    WorkdaySOAPFaultError,
    WorkdaySOAPTransportError,
    WORKDAY_AUTH_ERROR_PATTERNS,
    WORKDAY_AUTHN_ERROR_PATTERNS,
)
from tap_workday.streams import STREAMS

LOGGER = singer.get_logger()


def get_abs_path(path: str) -> str:
    """
    Get the absolute path for the schema files.
    """
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schema_references() -> Dict:
    """
    Load the schema files from the schema folder and return the schema references.
    """
    shared_schema_path = get_abs_path("schemas/shared")

    shared_file_names = []
    if os.path.exists(shared_schema_path):
        shared_file_names = [
            f
            for f in os.listdir(shared_schema_path)
            if os.path.isfile(os.path.join(shared_schema_path, f))
        ]

    refs = {}
    for shared_schema_file in shared_file_names:
        with open(os.path.join(shared_schema_path, shared_schema_file)) as data_file:
            refs["shared/" + shared_schema_file] = json.load(data_file)

    return refs


def check_stream_authorization(config: Dict, stream_name: str, stream_obj) -> bool:
    """
    Check if stream is authorized by making a test API call.
    Returns True if accessible, False if the stream should be excluded from the catalog.

    Distinguishes two failure types:
    - Authentication failure: invalid/expired credentials (HTTP 401). Logged as 'authentication'.
    - Authorization failure: valid credentials but insufficient permissions (SOAP auth fault).
      Logged as 'authorization'.
    """
    if not config or not hasattr(stream_obj, 'service_name') or not hasattr(stream_obj, 'operation_name'):
        return True

    try:
        client = Client(config, service=stream_obj.service_name)

        # Use stream's custom check_access method if present, else fall back to client
        if hasattr(stream_obj, 'check_access') and callable(getattr(stream_obj, 'check_access')):
            stream_obj.check_access(client)
        else:
            client.check_access(stream_obj.operation_name)
        return True
    except WorkdaySOAPFaultError as e:
        err_lower = str(e).lower()
        # Authentication failure (invalid credentials) delivered as a SOAP fault
        if any(p.lower() in err_lower for p in WORKDAY_AUTHN_ERROR_PATTERNS):
            LOGGER.warning(
                "Stream '%s' excluded from catalog \u2014 authentication failure "
                "(service=%s, operation=%s): invalid or expired credentials. "
                "Verify the username and password in the tap config.",
                stream_name,
                getattr(stream_obj, 'service_name', 'unknown'),
                getattr(stream_obj, 'operation_name', 'unknown'),
            )
            return False
        # Authorization failure (valid credentials, insufficient permissions)
        matched_pattern = next(
            (p for p in WORKDAY_AUTH_ERROR_PATTERNS if p.lower() in err_lower),
            None
        )
        if matched_pattern:
            LOGGER.warning(
                "Stream '%s' excluded from catalog — authorization failure "
                "(service=%s, operation=%s): credentials lack the required permissions. "
                "Grant access via the Workday domain/security group settings and re-run discovery.",
                stream_name,
                getattr(stream_obj, 'service_name', 'unknown'),
                getattr(stream_obj, 'operation_name', 'unknown'),
            )
            return False
        LOGGER.error("SOAP fault for stream '%s': %s", stream_name, e)
        return True
    except WorkdaySOAPTransportError as e:
        err_lower = str(e).lower()
        # status_code may be 0 when raised via SOAPErrorHandler; rely on the message string.
        status_code = getattr(e, 'status_code', 0)
        is_authn_failure = (
            status_code == 401
            or any(p.lower() in err_lower for p in WORKDAY_AUTHN_ERROR_PATTERNS)
        )
        if is_authn_failure:
            LOGGER.warning(
                "Stream '%s' excluded from catalog — authentication failure "
                "(service=%s, operation=%s): invalid or expired credentials. "
                "Verify the username and password in the tap config.",
                stream_name,
                getattr(stream_obj, 'service_name', 'unknown'),
                getattr(stream_obj, 'operation_name', 'unknown'),
            )
            return False
        LOGGER.error("Transport error for stream '%s': %s", stream_name, e)
        return True
    except Exception as e:
        LOGGER.error("Unexpected error testing access for stream '%s': %s", stream_name, e)
        return True


def check_authentication(config: Dict) -> bool:
    """
    Validate credentials with a single lightweight SOAP call before stream discovery.

    Returns True if credentials are valid (or config is absent).
    Returns False only on authentication failure (HTTP 401 / invalid credentials).
    SOAP authorization faults are treated as valid credentials — the probe operation
    may simply be unauthorized for this user.
    """
    if not config:
        return True

    try:
        client = Client(config, service="Human_Resources")
        client.check_access("Get_Workers")
        return True
    except WorkdaySOAPTransportError as e:
        err_lower = str(e).lower()
        status_code = getattr(e, 'status_code', 0)
        if status_code == 401 or any(p.lower() in err_lower for p in WORKDAY_AUTHN_ERROR_PATTERNS):
            return False
        return True  # non-401 transport error, don't block discovery
    except WorkdaySOAPFaultError as e:
        err_lower = str(e).lower()
        if any(p.lower() in err_lower for p in WORKDAY_AUTHN_ERROR_PATTERNS):
            return False  # authentication failure expressed as a SOAP fault
        return True  # authorization failure only; credentials are valid
    except Exception:
        return True  # unexpected error, don't block discovery


def get_schemas(config: Dict):
    """
    Load the schema references, prepare metadata for each stream and return schema and
    metadata for the catalog.

    Steps:
      1. Validate credentials upfront (authentication check).
      2. For each stream, verify authorization individually.
      3. Include only streams that pass both checks.
      4. Return empty dicts (no exception) when auth fails or no streams are authorized.
    """
    schemas = {}
    field_metadata = {}

    if config and not check_authentication(config):
        LOGGER.warning(
            "Authentication failure: invalid or expired credentials. "
            "Catalog generation skipped - verify the username and password in the tap config."
        )
        return schemas, field_metadata

    refs = load_schema_references()
    for stream_name, stream_obj in STREAMS.items():
        schema_path = get_abs_path("schemas/{}.json".format(stream_name))
        with open(schema_path) as file:
            schema = json.load(file)

        if not check_stream_authorization(config, stream_name, stream_obj):
            continue

        schemas[stream_name] = schema
        schema = singer.resolve_schema_references(schema, refs)

        mdata = metadata.new()
        mdata = metadata.get_standard_metadata(
            schema=schema,
            key_properties=getattr(stream_obj, "key_properties"),
            valid_replication_keys=(getattr(stream_obj, "replication_keys") or []),
            replication_method=getattr(stream_obj, "replication_method"),
        )
        mdata = metadata.to_map(mdata)

        automatic_keys = getattr(stream_obj, "replication_keys") or []
        for field_name in schema.get("properties", {}).keys():
            if field_name in automatic_keys:
                mdata = metadata.write(
                    mdata, ("properties", field_name), "inclusion", "automatic"
                )

        parent_tap_stream_id = getattr(stream_obj, "parent", None)
        if parent_tap_stream_id:
            mdata = metadata.write(mdata, (), 'parent-tap-stream-id', parent_tap_stream_id)

        mdata = metadata.to_list(mdata)
        field_metadata[stream_name] = mdata

    if config and not schemas:
        LOGGER.warning(
            "No authorized streams found. The catalog will be empty. "
            "Verify that the tap credentials have 'read' access to at least one stream."
        )

    return schemas, field_metadata
