from typing import Dict

import singer

from tap_workday.client import Client
from tap_workday.streams import STREAMS

LOGGER = singer.get_logger()


def update_currently_syncing(state: Dict, stream_name: str) -> None:
    """
    Update currently_syncing in state and write it
    """
    if not stream_name and singer.get_currently_syncing(state):
        # Clear in-memory marker without emitting another STATE message.
        # This keeps output to a single STATE record containing currently_syncing.
        del state["currently_syncing"]
        return

    singer.set_currently_syncing(state, stream_name)
    singer.write_state(state)


def write_schema(stream, client, streams_to_sync, catalog) -> None:
    """
    Write schema for stream and its children
    """
    if stream.is_selected():
        stream.write_schema()

    for child in stream.children:
        child_obj = STREAMS[child](client, catalog.get_stream(child))
        write_schema(child_obj, client, streams_to_sync, catalog)
        if child in streams_to_sync:
            stream.child_to_sync.append(child_obj)


def _apply_interrupted_sync_resume(streams_to_sync, state):
    """If currently_syncing exists in state, resume from that stream onward."""
    current_stream = singer.get_currently_syncing(state)
    if not current_stream:
        return streams_to_sync

    if current_stream not in streams_to_sync:
        LOGGER.warning(
            "currently_syncing stream '%s' is not selected; starting from first selected stream",
            current_stream,
        )
        return streams_to_sync

    resume_index = streams_to_sync.index(current_stream)
    resumed_streams = streams_to_sync[resume_index:]
    LOGGER.info(
        "Resuming interrupted sync from stream '%s' (remaining_streams=%s)",
        current_stream,
        resumed_streams,
    )
    return resumed_streams


def sync(client: Client, config: Dict, catalog: singer.Catalog, state) -> None:
    """
    Sync selected streams from catalog
    """

    streams_to_sync = []
    for stream in catalog.get_selected_streams(state):
        streams_to_sync.append(stream.stream)
    streams_to_sync = _apply_interrupted_sync_resume(streams_to_sync, state)
    LOGGER.info("selected_streams: {}".format(streams_to_sync))

    with singer.Transformer() as transformer:
        for stream_name in streams_to_sync:

            stream = STREAMS[stream_name](client, catalog.get_stream(stream_name))
            if stream.parent:
                if stream.parent not in streams_to_sync:
                    streams_to_sync.append(stream.parent)
                continue

            write_schema(stream, client, streams_to_sync, catalog)
            LOGGER.info("START Syncing: {}".format(stream_name))
            update_currently_syncing(state, stream_name)
            total_records = stream.sync(state=state, transformer=transformer)

            update_currently_syncing(state, None)
            LOGGER.info(
                "FINISHED Syncing: {}, total_records: {}".format(
                    stream_name, total_records
                )
            )
