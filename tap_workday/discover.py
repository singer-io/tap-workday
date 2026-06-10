import singer
from singer import metadata
from singer.catalog import Catalog, CatalogEntry, Schema

from tap_workday.exceptions import WORKDAY_AUTH_ERROR_PATTERNS, WorkdayForbiddenError, WorkdaySOAPFaultError
from tap_workday.schema import get_schemas
from tap_workday.streams import STREAMS
from typing import Dict

LOGGER = singer.get_logger()


def _apply_access_checks(client, schemas: dict, field_metadata: dict) -> None:
    """Check each parent stream for API access and remove inaccessible ones.

    Child streams are skipped here since their accessibility is determined by
    their parent. Call _prune_inaccessible_children() after this to remove
    orphaned child streams.

    Raises an exception if all parent streams are inaccessible.
    """
    inaccessible = []

    for stream_name in list(schemas.keys()):
        stream_class = STREAMS.get(stream_name)
        if stream_class is None:
            continue

        # Child streams are checked via parent — skip here
        if getattr(stream_class, "parent", None):
            continue

        stream_instance = stream_class(client=client)
        try:
            stream_instance.check_access()
        except WorkdayForbiddenError as exc:
            LOGGER.warning(
                "Stream '%s' is not accessible (authorization failure). "
                "Excluding from catalog. Error: %s",
                stream_name,
                exc,
            )
            inaccessible.append(stream_name)
        except WorkdaySOAPFaultError as exc:
            err_lower = str(exc).lower()
            if any(p.lower() in err_lower for p in WORKDAY_AUTH_ERROR_PATTERNS):
                LOGGER.warning(
                    "Stream '%s' is not accessible (SOAP authorization error). "
                    "Excluding from catalog. Error: %s",
                    stream_name,
                    exc,
                )
                inaccessible.append(stream_name)
            else:
                raise

    for stream_name in inaccessible:
        schemas.pop(stream_name, None)
        field_metadata.pop(stream_name, None)

    remaining_parents = [
        name for name in schemas
        if not getattr(STREAMS.get(name), "parent", None)
    ]
    if not remaining_parents:
        raise Exception(
            "All streams are inaccessible with the provided credentials. "
            "Cannot produce a usable catalog."
        )


def _prune_inaccessible_children(schemas: dict, field_metadata: dict) -> None:
    """Remove child streams whose parent streams are no longer in the catalog.

    Iterates until no more children are pruned to handle multi-level
    parent-child relationships (e.g. grandchildren).
    """
    accessible = set(schemas.keys())

    to_remove = [
        name for name in list(schemas.keys())
        if getattr(STREAMS.get(name), "parent", None)
        and getattr(STREAMS.get(name), "parent") not in accessible
    ]

    while to_remove:
        for stream_name in to_remove:
            LOGGER.warning(
                "Excluding child stream '%s' because its parent '%s' is not in the catalog.",
                stream_name,
                getattr(STREAMS.get(stream_name), "parent"),
            )
            schemas.pop(stream_name, None)
            field_metadata.pop(stream_name, None)
            accessible.discard(stream_name)

        to_remove = [
            name for name in list(schemas.keys())
            if getattr(STREAMS.get(name), "parent", None)
            and getattr(STREAMS.get(name), "parent") not in accessible
        ]


def discover(client) -> Catalog:
    """Run the discovery mode, prepare the catalog file and return the catalog."""
    schemas, field_metadata = get_schemas(config=client.config)

    _apply_access_checks(client, schemas, field_metadata)
    _prune_inaccessible_children(schemas, field_metadata)

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

        catalog.streams.append(
            CatalogEntry(
                stream=stream_name,
                tap_stream_id=stream_name,
                key_properties=key_properties,
                schema=schema,
                metadata=mdata,
            )
        )

    return catalog
