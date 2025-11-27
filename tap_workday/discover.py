import singer
from singer import metadata
from singer.catalog import Catalog, CatalogEntry, Schema

from tap_workday.schema import get_schemas
from tap_workday.streams import STREAMS
from typing import Dict

LOGGER = singer.get_logger()


def discover(config: Dict) -> Catalog:
    """
    Run the discovery mode, prepare the catalog file and return the catalog.
    """
    schemas, field_metadata = get_schemas(config=config)
    catalog = Catalog([])

    for stream_name, schema_dict in schemas.items():
        try:
            schema = Schema.from_dict(schema_dict)
            mdata = field_metadata[stream_name]
        except Exception as err:
            LOGGER.error(err)
            LOGGER.error("stream_name: {}".format(stream_name))
            LOGGER.error("type schema_dict: {}".format(type(schema_dict)))
            raise err

        key_properties = metadata.to_map(mdata).get((), {}).get("table-key-properties")

        stream_obj = STREAMS.get(stream_name)
        stream_id = getattr(stream_obj, "stream_id", None) if stream_obj else None

        catalog.streams.append(
            CatalogEntry(
                stream=stream_id,
                tap_stream_id=stream_name,
                key_properties=key_properties,
                schema=schema,
                metadata=mdata,
            )
        )

    return catalog
