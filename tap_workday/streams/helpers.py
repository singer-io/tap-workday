from datetime import date, datetime
from decimal import Decimal

from singer import (
    UNIX_SECONDS_INTEGER_DATETIME_PARSING,
    Transformer,
    metrics,
    write_record,
    write_schema,
)
from zeep import Client as Client
from zeep.helpers import serialize_object
from zeep.wsse.username import UsernameToken


def normalize_ref_object(value):
    """Normalize a Workday reference object to a standard dict format.

    Args:
        value: The object to normalize.

    Returns:
        dict: Normalized reference object with 'ID' and 'Descriptor'.
    """
    if value is None or not isinstance(value, dict):
        return {"ID": [], "Descriptor": None}

    id_field = value.get("ID")

    if isinstance(id_field, dict):
        value["ID"] = [id_field]
    elif isinstance(id_field, list):
        value["ID"] = [item for item in id_field if isinstance(item, dict)]
    else:
        value["ID"] = []

    descriptor = value.get("Descriptor")
    value["Descriptor"] = descriptor if isinstance(descriptor, str) else None

    return value


def normalize_ref_array(value):
    """Normalize a list of Workday reference objects.

    Args:
        value: The list to normalize.

    Returns:
        list: List of normalized reference objects.
    """
    if not isinstance(value, list):
        return []
    return [normalize_ref_object(item) for item in value if isinstance(item, dict)]


def pre_hook(data, typ, schema):
    """Pre-processing hook for Singer Transformer.

    Converts dates and decimals, and normalizes Workday reference objects.

    Args:
        data: The data value to process.
        typ: The type (unused).
        schema: The schema dict.

    Returns:
        The processed value.
    """
    # Dates & datetimes -> ISO strings when the schema says so
    if isinstance(data, datetime) and schema.get("format") == "date-time":
        return data.isoformat()
    if isinstance(data, date) and schema.get("format") == "date":
        return data.isoformat()

    # Decimal -> float
    if isinstance(data, Decimal):
        return float(data)

    # Normalize any "*_Reference" shapes (singular or array)
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if key.endswith("_Reference"):
                if isinstance(value, dict):
                    data[key] = normalize_ref_object(value)
                elif isinstance(value, list):
                    data[key] = normalize_ref_array(value)
                else:
                    data[key] = {"ID": [], "Descriptor": None}

    return data


def safe_get_records(serialized: dict, data_key: str):
    """Return a list of records from a Workday SOAP response.

    Handles cases where `Response_Data` is None or missing, and when the
    leaf at `data_key` is a single object instead of a list.

    Args:
        serialized (dict): The serialized SOAP response.
        data_key (str): The key for the data leaf.

    Returns:
        list: List of records (dicts).
    """
    if not isinstance(serialized, dict):
        return []
    resp = serialized.get("Response_Data")
    if not isinstance(resp, dict):
        return []
    records = resp.get(data_key)
    if records is None:
        return []
    if isinstance(records, list):
        return records
    if isinstance(records, dict):
        return [records]
    return []


def call_workday_operation(client, operation_name: str, data_key: str, updated_since=None):
    """
    Call a Workday SOAP operation and return all paginated records.
    If updated_since is provided, it will be used to filter records (for incremental syncs).
    The filter is passed as 'Updated_Since' in Request_Criteria or Response_Filter, depending on the API.
    """
    all_records = []
    page = 1
    total_pages = 1  # Will be updated after first call

    while page <= total_pages:
        # Build filter dicts
        response_filter = {"Page": page}
        if updated_since:
            # Many Workday APIs use 'Updated_Since' or similar in Request_Criteria or Response_Filter
            response_filter["Updated_Since"] = updated_since

        try:
            # Try passing filter in Response_Filter
            response = client.call(
                operation_name,
                Response_Filter=response_filter
            )
        except TypeError:
            # Fallback: try passing filter in Request_Criteria
            try:
                criteria = {"Page": page}
                if updated_since:
                    criteria["Updated_Since"] = updated_since
                response = client.call(
                    operation_name,
                    Request_Criteria=criteria
                )
            except TypeError:
                # Fallback: try passing page only
                try:
                    response = client.call(operation_name, page=page)
                except TypeError:
                    # As a last resort, call with no pagination (single page)
                    response = client.call(operation_name)

        serialized = serialize_object(response)
        records = safe_get_records(serialized, data_key)
        all_records.extend(records)

        # Extract pagination info
        results = serialized.get("Response_Results", {})
        # Defensive: handle missing or None values
        total_pages_val = results.get("Total_Pages")
        page_val = results.get("Page")
        try:
            total_pages = int(total_pages_val) if total_pages_val is not None else 1
        except Exception:
            total_pages = 1
        try:
            current_page = int(page_val) if page_val is not None else page
        except Exception:
            current_page = page
        page = current_page + 1

        if page > total_pages:
            break

    return all_records


def emit_full_table(stream, records):
    """Write schema, transform with shared hook, and emit records.

    Args:
        stream: The stream object with schema and metadata.
        records: Iterable of records to emit.

    Returns:
        int: Number of records emitted.
    """
    transformer = Transformer(
        integer_datetime_fmt=UNIX_SECONDS_INTEGER_DATETIME_PARSING,
        pre_hook=pre_hook,
    )

    with metrics.record_counter(stream.tap_stream_id) as counter:
        for record in records:
            transformed = transformer.transform(record, stream.schema, stream.metadata)
            write_record(stream.tap_stream_id, transformed)
            counter.increment()

        return counter.value
