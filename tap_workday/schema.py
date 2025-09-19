import json
import os
from typing import Dict, Tuple

import singer
from singer import metadata

from tap_workday.client import Client
from tap_workday.exceptions import WorkdaySOAPFaultError
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


def get_schemas(config: Dict = None) -> Tuple[Dict, Dict]:
    """
    Load the schema references, prepare metadata for each streams and return schema and metadata for the catalog.
    """
    schemas = {}
    field_metadata = {}

    refs = load_schema_references()
    for stream_name, stream_obj in STREAMS.items():
        schema_path = get_abs_path("schemas/{}.json".format(stream_name))
        with open(schema_path) as file:
            schema = json.load(file)

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

        # Check if stream is authorized by making a test API call
        if config and hasattr(stream_obj, 'service_name') and hasattr(stream_obj, 'operation_name'):
            try:
                client = Client(config, service=stream_obj.service_name)
                # Make a minimal test call to check authorization
                client.call(stream_obj.operation_name)
                LOGGER.info(f"Stream {stream_name} is authorized")
            except WorkdaySOAPFaultError as e:
                # Check for specific authorization error message
                if 'Processing error occurred. The task submitted is not authorized.' in str(e):
                    LOGGER.warning(f"Stream {stream_name} is not authorized, marking as unsupported")
                    mdata[()]['inclusion'] = "unsupported"
                else:
                    # Re-raise other SOAP faults as they may indicate other issues
                    LOGGER.warning(f"SOAP fault for stream {stream_name}: {e}")
            except Exception as e:
                # Log other exceptions but don't mark as unsupported
                # as they might be temporary network issues
                LOGGER.warning(f"Error testing authorization for stream {stream_name}: {e}")

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

    return schemas, field_metadata
