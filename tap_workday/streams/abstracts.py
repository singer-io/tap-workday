import json
from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterator, List, Tuple

from singer import (
    Transformer,
    get_bookmark,
    get_logger,
    metadata,
    metrics,
    write_bookmark,
    write_record,
    write_schema,
    write_state,
)

from tap_workday.client import Client, DefaultValues
from tap_workday.streams.helpers import call_workday_operation, emit_full_table

LOGGER = get_logger()


class BaseStream(ABC):
    """
    A Base Class providing structure and boilerplate for generic streams
    and required attributes for any kind of stream
    ~~~
    Provides:
     - Basic Attributes (stream_name,replication_method,key_properties)
     - Helper methods for catalog generation
     - `sync` and `get_records` method for performing sync
    """

    url_endpoint = ""
    path = ""
    page_size = 100
    next_page_key = ""
    headers = {}
    children = []
    parent = ""
    data_key = ""
    parent_bookmark_key = ""
    http_method = "POST"

    def __init__(self, client=None, catalog=None) -> None:
        self.client = client
        self.catalog = catalog
        self.schema = catalog.schema.to_dict()
        self.metadata = metadata.to_map(catalog.metadata)
        self.child_to_sync = []
        self.params = {}
        self.data_payload = {}

    @property
    @abstractmethod
    def tap_stream_id(self) -> str:
        """Unique identifier for the stream.

        This is allowed to be different from the name of the stream, in
        order to allow for sources that have duplicate stream names.
        """

    @property
    @abstractmethod
    def replication_method(self) -> str:
        """Defines the sync mode of a stream."""

    @property
    @abstractmethod
    def replication_keys(self) -> List:
        """Defines the replication key for incremental sync mode of a
        stream."""

    @property
    @abstractmethod
    def key_properties(self):
        """Key properties for stream."""

    def is_selected(self):
        """Check if the stream is selected in the catalog."""
        return metadata.get(self.metadata, (), "selected")

    @abstractmethod
    def sync(
        self,
        state: Dict,
        transformer: Transformer,
        parent_obj: Dict = None,
    ) -> Dict:
        """
        Performs a replication sync for the stream.
        ~~~
        Args:
         - state (dict): represents the state file for the tap.
         - transformer (object): A Object of the singer.transformer class.
         - parent_obj (dict): The parent object for the stream.

        Returns:
         - bool: The return value. True for success, False otherwise.

        Docs:
         - https://github.com/singer-io/getting-started/blob/master/docs/SYNC_MODE.md
        """

    def get_records(self) -> Iterator:
        """Interacts with api client interaction and pagination."""
        self.params["page"] = self.page_size
        next_page = 1
        while next_page:
            response = self.client.make_request(
                self.http_method,
                self.url_endpoint,
                self.params,
                self.headers,
                body=json.dumps(self.data_payload),
                path=self.path,
            )
            raw_records = response.get(self.data_key, [])
            next_page = response.get(self.next_page_key)

            self.params[self.next_page_key] = next_page
            yield from raw_records

    def write_schema(self) -> None:
        """
        Write a schema message.
        """
        try:
            write_schema(self.tap_stream_id, self.schema, self.key_properties)
        except OSError as err:
            LOGGER.error("OS Error while writing schema for: %s", self.tap_stream_id)
            raise err

    def update_params(self, **kwargs) -> None:
        """
        Update params for the stream
        """
        self.params.update(kwargs)

    def update_data_payload(self, **kwargs) -> None:
        """
        Update JSON body for the stream
        """
        self.data_payload.update(kwargs)

    def modify_object(self, record: Dict, parent_record: Dict = None) -> Dict:
        """
        Modify the record before writing to the stream

        The `parent_obj` parameter is included for interface compatibility with
        subclasses that may require it, even though it is unused in this base implementation.
        """
        return record

    def get_url_endpoint(self, parent_obj: Dict = None) -> str:
        """
        Get the URL endpoint for the stream

        The `parent_obj` parameter is included for interface compatibility with
        subclasses that may require it, even though it is unused in this base implementation.
        """
        return self.url_endpoint or f"{self.client.base_url}/{self.path}"


class IncrementalStream(BaseStream):
    """Base Class for Incremental Stream."""

    def get_bookmark(self, state: dict, stream: str, key: Any = None) -> int:
        """A wrapper for singer.get_bookmark to deal with compatibility for
        bookmark values or start values."""
        start_date = self.client.config.get("start_date")
        return get_bookmark(
            state,
            stream,
            key or self.replication_keys[0],
            start_date,
        )

    def write_bookmark(
        self, state: dict, stream: str, key: Any = None, value: Any = None
    ) -> Dict:
        """A wrapper for singer.get_bookmark to deal with compatibility for
        bookmark values or start values."""
        if not (key or self.replication_keys):
            return state

        start_date = self.client.config.get("start_date")
        current_bookmark = get_bookmark(
            state,
            stream,
            key or self.replication_keys[0],
            start_date,
        )
        value = max(current_bookmark, value)
        return write_bookmark(state, stream, key or self.replication_keys[0], value)

    def sync(
        self,
        state: Dict,
        transformer: Transformer,
        parent_obj: Dict = None,
    ) -> Dict:
        """Implementation for `type: Incremental` stream."""
        bookmark_date = self.get_bookmark(state, self.tap_stream_id)
        current_max_bookmark_date = bookmark_date
        self.update_params(updated_since=bookmark_date)
        self.update_data_payload(parent_obj=parent_obj)
        self.url_endpoint = self.get_url_endpoint(parent_obj)

        with metrics.record_counter(self.tap_stream_id) as counter:
            for record in self.get_records():
                record = self.modify_object(record, parent_obj)
                transformed_record = transformer.transform(
                    record, self.schema, self.metadata
                )

                record_bookmark = transformed_record[self.replication_keys[0]]
                if record_bookmark >= bookmark_date:
                    if self.is_selected():
                        write_record(self.tap_stream_id, transformed_record)
                        counter.increment()

                    current_max_bookmark_date = max(
                        current_max_bookmark_date, record_bookmark
                    )

                    for child in self.child_to_sync:
                        child.sync(
                            state=state, transformer=transformer, parent_obj=record
                        )

            state = self.write_bookmark(
                state, self.tap_stream_id, value=current_max_bookmark_date
            )

            write_state(state)
            return counter.value


class FullTableStream(BaseStream):
    """Base class for streams that replicate updates."""

    replication_keys = []

    def sync(
        self,
        state: Dict,
        transformer: Transformer,
        parent_obj: Dict = None,
    ) -> Dict:
        """Abstract implementation for `type: Fulltable` stream."""
        self.url_endpoint = self.get_url_endpoint(parent_obj)
        self.update_data_payload(parent_obj=parent_obj)
        with metrics.record_counter(self.tap_stream_id) as counter:
            for record in self.get_records():
                transformed_record = transformer.transform(
                    record, self.schema, self.metadata
                )
                if self.is_selected():
                    write_record(self.tap_stream_id, transformed_record)
                    counter.increment()

                for child in self.child_to_sync:
                    child.sync(state=state, transformer=transformer, parent_obj=record)

            return counter.value


class ParentBaseStream(IncrementalStream):
    """Base Class for Parent Stream."""

    def get_bookmark(self, state: Dict, stream: str, key: Any = None) -> int:
        """A wrapper for singer.get_bookmark to deal with compatibility for
        bookmark values or start values."""

        min_parent_bookmark = (
            super().get_bookmark(state, stream) if self.is_selected() else None
        )
        for child in self.child_to_sync:
            bookmark_key = f"{self.tap_stream_id}_{self.replication_keys[0]}"
            child_bookmark = super().get_bookmark(
                state, child.tap_stream_id, key=bookmark_key
            )
            min_parent_bookmark = (
                min(min_parent_bookmark, child_bookmark)
                if min_parent_bookmark
                else child_bookmark
            )

        return min_parent_bookmark

    def write_bookmark(
        self, state: Dict, stream: str, key: Any = None, value: Any = None
    ) -> Dict:
        """A wrapper for singer.get_bookmark to deal with compatibility for
        bookmark values or start values."""
        if self.is_selected():
            super().write_bookmark(state=state, stream=stream, value=value)

        for child in self.child_to_sync:
            bookmark_key = f"{self.tap_stream_id}_{self.replication_keys[0]}"
            super().write_bookmark(
                state, child.tap_stream_id, key=bookmark_key, value=value
            )

        return state


class ChildBaseStream(IncrementalStream):
    """Base Class for Child Stream."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # bookmark_value is used to cache the bookmark for this child stream.
        # It is initialized as None and set on first call to get_bookmark.
        # After being set, it should remain unchanged for the stream's lifecycle.
        self.bookmark_value = None

    def get_url_endpoint(self, parent_obj=None):
        """Prepare URL endpoint for child streams."""
        if not parent_obj or "id" not in parent_obj:
            LOGGER.critical("parent_obj must contain an 'id' key for get_url_endpoint construction.")
            raise KeyError("parent_obj must contain an 'id' key for get_url_endpoint construction.")
        return f"{self.client.base_url}/{self.path.format(parent_obj['id'])}"

    def get_bookmark(self, state: Dict, stream: str, key: Any = None) -> int:
        """
        Get or cache the bookmark value for this child stream.

        bookmark_value is initialized to None in __init__, and is set the first time
        this method is called. After that, the cached value is returned for the lifetime
        of the stream instance. This avoids repeated lookups for the same bookmark.

        Returns:
            int: The bookmark value for the stream.
        """
        if self.bookmark_value is None:
            self.bookmark_value = super().get_bookmark(state, stream)
        return self.bookmark_value


def _extract_max_date(records, field_path):
    """Return the maximum date value found in *records* by following *field_path*.

    Traverses each record dict using the sequence of keys in *field_path*
    (e.g. ``["Organization_Data", "Last_Updated_DateTime"]``) and returns the
    lexicographically greatest ISO-8601 string found.  Handles both Python
    ``datetime``/``date`` objects (returned by zeep before transformation) and
    plain strings (already formatted by Singer's pre_hook).

    Returns ``None`` when no usable date value is found in any record —
    callers should fall back to ``sync_start_time`` in that case.
    """
    max_date = None
    for record in records:
        val = record
        for key in field_path:
            if not isinstance(val, dict):
                val = None
                break
            val = val.get(key)
        if val is None:
            continue
        if isinstance(val, datetime):
            val_str = val.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif isinstance(val, date):
            # plain date, no time component
            val_str = val.strftime("%Y-%m-%dT00:00:00Z")
        elif isinstance(val, str) and val:
            val_str = val
        else:
            continue
        if max_date is None or val_str > max_date:
            max_date = val_str
    return max_date


class WorkdayTableStream(FullTableStream):
    """Base for simple Workday SOAP streams.

    Child classes should set:
    - service_name: Workday service string (e.g., "Human_Resources")
    - operation_name: SOAP operation to call (e.g., "Get_Organizations")
    - data_key: leaf key inside Response_Data (e.g., "Organization")
    - wid_key: reference field key for extracting key_value (e.g., "Absence_Input_Reference")
    - version (optional): default "v45.0"

    To enable incremental replication for a stream:
    - Set ``replication_method = "INCREMENTAL"``
    - Set ``replication_keys = ["updated_through"]`` (or another bookmark key name).
      This value appears as ``valid-replication-keys`` in the Singer catalog and is
      also used as the Singer state bookmark key.
    - Override ``build_filter_params`` to return the correct ``Request_Criteria`` dict.
    - Set ``bookmark_field_path`` to a list of dict keys that navigate to a
      "last modified" timestamp in the returned records (e.g.
      ``["Organization_Data", "Last_Updated_DateTime"]``).  The max of that
      field across all records in the sync window is saved as the bookmark,
      guaranteeing the boundary record is re-fetched on the next run
      (≥1 record overlap).  Leave as ``None`` when no reliable last-modified
      field exists in the response — the bookmark falls back to sync_start_time.
    """

    service_name: str = ""
    operation_name: str = ""
    data_key: str = ""
    wid_key: str = ""
    version: str = DefaultValues.VERSION.value
    # Override with the key path to a "last modified" timestamp in response
    # records (see class docstring).  None means fall back to sync_start_time.
    bookmark_field_path: list = None

    def get_client(self):
        """Client for WorkdayTableStream."""
        cfg = self.client.config
        return Client(cfg, service=self.service_name, version=self.version)

    def build_filter_params(self, updated_since, updated_through=None):
        """Return stream-specific incremental filter params for the SOAP call.

        Override in subclasses that support server-side date filtering.
        The returned dict is merged into the SOAP call parameters.
        """
        return {}

    def _get_sync_start_time(self):
        """Return the current UTC time as an RFC 3339 string.

        Isolated into its own method so unit tests can patch it without
        replacing the entire datetime class (which would break isinstance
        checks in _extract_max_date).
        """
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def sync(self, state, transformer, parent_obj=None):
        """Synchronize records for WorkdayTableStream.

        INCREMENTAL BEHAVIOUR — why a run can correctly return 0 records
        ─────────────────────────────────────────────────────────────────
        Workday's date-range filter returns records whose *internal transaction
        log entry* falls in the window [Updated_From, Updated_Through].

          Run 1 (empty state):
            updated_since  = start_date from config (e.g. 2019-01-01)
            Updated_From   = 2019-01-01  →  returns all records since 2019
            bookmark saved = sync_start_time (e.g. 2026-08-10T08:12Z)

          Run 2 (state from Run 1):
            updated_since  = 2026-08-10T08:12Z  ← bookmark, NOT start_date
            Updated_From   = 2026-08-10T08:12Z  →  returns only records
                             whose Workday transaction date ≥ 08:12Z
            If no one edited Workday data since 08:12Z → 0 records is CORRECT.
            bookmark saved = new sync_start_time (e.g. 2026-08-10T08:32Z)

        0 records on Run 2 means "nothing changed in Workday since the last
        sync" — it is not a bug or a missed-data situation.  The bookmark
        advances each run so any future change is captured exactly once.

        NO DATA IS EVER LOST:
          • Records with transaction_date < Run-N bookmark  → already in Run N
          • Records with transaction_date ≥ Run-N bookmark  → captured in Run N+1
          • A record at the exact boundary timestamp        → appears in both
                                                              (inclusive filter)
        """
        client = self.get_client()
        updated_since = None
        sync_start_time = None
        if self.replication_keys:
            bookmark_key = self.replication_keys[0]
            start_date = self.client.config.get("start_date")
            # get_bookmark returns the stored bookmark if one exists, otherwise
            # falls back to start_date.  start_date is ONLY used on the very
            # first run when state is empty — it is ignored on all subsequent runs.
            updated_since = get_bookmark(
                state, self.tap_stream_id, bookmark_key, start_date
            )
            sync_start_time = self._get_sync_start_time()
        custom_params = self.build_filter_params(updated_since, sync_start_time) or None
        records = call_workday_operation(
            client, self.operation_name, self.data_key,
            custom_params=custom_params, wid_key=self.wid_key
        )
        if self.replication_keys and sync_start_time:
            for record in records:
                record["updated_through"] = sync_start_time
        count = emit_full_table(self, records)
        if self.replication_keys and sync_start_time:
            bookmark_key = self.replication_keys[0]
            # bookmark_field_path allows using a record-level date field as the
            # bookmark instead of sync_start_time.  Currently None for all
            # streams because Last_Updated_DateTime is the *effective* date of
            # a change (can be future-dated) and does not match the internal
            # Workday transaction log timestamp the API filters on.
            if self.bookmark_field_path and records:
                new_bookmark = (
                    _extract_max_date(records, self.bookmark_field_path)
                    or sync_start_time
                )
            else:
                new_bookmark = sync_start_time
            state = write_bookmark(state, self.tap_stream_id, bookmark_key, new_bookmark)
            write_state(state)
        return count
