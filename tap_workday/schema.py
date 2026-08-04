import json
import os
from typing import Dict, Optional, Tuple

import singer
from singer import metadata

from tap_workday.client import Client
from tap_workday.exceptions import (
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


def check_stream_authorization(
    config: Dict, stream_name: str, stream_obj, shared_client=None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if stream is authorized by making a test API call.

    Returns a tuple (authorized, failure_category, failure_detail):
    - authorized (bool): True if the stream should be included in the catalog.
    - failure_category (str | None): Short category key for grouping log messages —
        'authentication', 'authorization', 'soap_fault', 'transport_error',
        'unexpected_error', or None when authorized.
    - failure_detail (str | None): Human-readable error detail, or None when authorized.

    Streams with unexpected errors (soap_fault, transport_error, unexpected_error) are
    still included in the catalog (authorized=True) but surfaced for grouped error logging.
    """
    if not config or not hasattr(stream_obj, 'service_name') or not hasattr(stream_obj, 'operation_name'):
        return True, None, None

    try:
        client = Client(config, service=stream_obj.service_name)
        # Reuse the token manager from the main client so every stream shares the
        # same cached access token instead of fetching a fresh one each time.
        if shared_client is not None and shared_client._token_manager is not None:
            client._token_manager = shared_client._token_manager

        # Use stream's custom check_access method if present, else fall back to client
        if hasattr(stream_obj, 'check_access') and callable(getattr(stream_obj, 'check_access')):
            stream_obj.check_access(client)
        else:
            client.check_access(stream_obj.operation_name)
        return True, None, None
    except WorkdaySOAPFaultError as e:
        err_lower = str(e).lower()
        if any(p.lower() in err_lower for p in WORKDAY_AUTHN_ERROR_PATTERNS):
            return False, "authentication", "invalid or expired credentials"
        matched_pattern = next(
            (p for p in WORKDAY_AUTH_ERROR_PATTERNS if p.lower() in err_lower), None
        )
        if matched_pattern:
            return False, "authorization", "credentials lack the required permissions"
        return True, "soap_fault", str(e)
    except WorkdaySOAPTransportError as e:
        err_lower = str(e).lower()
        status_code = getattr(e, 'status_code', 0)
        is_authn_failure = (
            status_code == 401
            or any(p.lower() in err_lower for p in WORKDAY_AUTHN_ERROR_PATTERNS)
        )
        if is_authn_failure:
            return False, "authentication", "invalid or expired credentials"
        return True, "transport_error", str(e)
    except Exception as e:
        return True, "unexpected_error", str(e)


def get_schemas(config: Dict, client=None):
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

    refs = load_schema_references()

    excluded_groups: Dict[Tuple[str, str], list] = {}
    error_groups: Dict[Tuple[str, str], list] = {}

    for stream_name, stream_obj in STREAMS.items():
        schema_path = get_abs_path("schemas/{}.json".format(stream_name))
        with open(schema_path) as file:
            schema = json.load(file)

        authorized, category, detail = check_stream_authorization(config, stream_name, stream_obj, shared_client=client)

        if not authorized:
            excluded_groups.setdefault((category, detail), []).append(stream_name)
            continue

        if category is not None:
            error_groups.setdefault((category, detail), []).append(stream_name)

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

    for (category, detail), stream_names in excluded_groups.items():
        streams_str = ", ".join(stream_names)
        if category == "authentication":
            LOGGER.warning(
                "%d stream(s) excluded from catalog — authentication failure: %s.\n"
                "Affected streams: [%s].\n"
                "Verify the username and password in the tap config.",
                len(stream_names), detail, streams_str,
            )
        elif category == "authorization":
            LOGGER.warning(
                "%d stream(s) excluded from catalog — authorization failure: %s.\n"
                "Affected streams: [%s].\n"
                "Grant access via the Workday domain/security group settings and re-run discovery.",
                len(stream_names), detail, streams_str,
            )

    for (category, detail), stream_names in error_groups.items():
        streams_str = ", ".join(stream_names)
        LOGGER.error(
            "Access check error (%s) for %d stream(s) — %s. Affected streams: [%s]",
            category.replace("_", " "), len(stream_names), detail, streams_str,
        )

    if config and not schemas:
        raise RuntimeError(
            "No authorized streams found — discovery cannot complete. \n"
            "Verify that the tap credentials have 'read' access to at least one stream."
        )

    return schemas, field_metadata
