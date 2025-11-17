from datetime import date, datetime
from decimal import Decimal

from singer import (
    UNIX_SECONDS_INTEGER_DATETIME_PARSING,
    Transformer,
    metrics,
    write_record,
)
from zeep.helpers import serialize_object


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

    # Always convert datetime/date to ISO string, even if schema format is missing
    if isinstance(data, datetime):
        return data.isoformat()
    if isinstance(data, date):
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
            # Handle Ledger_Data array unwrapping
            elif key == "Ledger_Data" and isinstance(value, list) and len(value) == 1:
                unwrapped_data = value[0]
                # Recursively process the unwrapped data
                if isinstance(unwrapped_data, dict):
                    for inner_key, inner_value in list(unwrapped_data.items()):
                        if inner_key in ["Commitment_Ledger_Data", "Obligation_Ledger_Data"] and isinstance(inner_value, list) and len(inner_value) == 0:
                            unwrapped_data[inner_key] = None
                data[key] = unwrapped_data
            # Handle empty array fields that should be null or objects in schema
            elif key in ["Commitment_Ledger_Data", "Obligation_Ledger_Data"] and isinstance(value, list) and len(value) == 0:
                data[key] = None

    return data


def _normalize_records_to_list(records):
    """Convert records to a list format, handling None, dict, or list inputs.
    
    Args:
        records: Records data that can be None, dict, or list.
        
    Returns:
        list: Normalized list of records.
    """
    if records is None:
        return []
    if isinstance(records, list):
        return records
    if isinstance(records, dict):
        return [records]
    return []


def safe_get_records(serialized: dict, data_key: str):
    """Return a list of records from a Workday SOAP response.

    Handles cases where `Response_Data` is None or missing, when it's a list,
    and when the leaf at `data_key` is a single object instead of a list.

    Args:
        serialized (dict): The serialized SOAP response.
        data_key (str): The key for the data leaf.

    Returns:
        list: List of records (dicts).
    """
    if not isinstance(serialized, dict):
        return []
    
    resp = serialized.get("Response_Data")
    if resp is None:
        return []

    # Handle list of Response_Data items
    if isinstance(resp, list):
        all_records = []
        for item in resp:
            if isinstance(item, dict):
                records = item.get(data_key)
                all_records.extend(_normalize_records_to_list(records))
        return all_records

    # Handle single Response_Data dict
    if isinstance(resp, dict):
        records = resp.get(data_key)
        return _normalize_records_to_list(records)

    return []


class WorkdayPaginator:
    """Centralized pagination handler for Workday SOAP operations"""

    def __init__(self, client, operation_name):
        self.client = client
        self.operation_name = operation_name

    def _try_pagination_strategies(self, page, updated_since, custom_params=None):
        """Try each pagination strategy in order of preference."""
        def call_with_response_filter(page, updated_since):
            response_filter = {"Page": page}
            if updated_since:
                response_filter["Updated_Since"] = updated_since
            params = {"Response_Filter": response_filter}
            if custom_params:
                params.update(custom_params)
            return self.client.call(self.operation_name, **params)

        def call_with_request_criteria(page, updated_since):
            criteria = {"Page": page}
            if updated_since:
                criteria["Updated_Since"] = updated_since
            params = {"Request_Criteria": criteria}
            if custom_params:
                params.update(custom_params)
            return self.client.call(self.operation_name, **params)

        def call_with_page_arg(page, updated_since):
            # updated_since is ignored here as not all APIs support it in this form
            params = {"page": page}
            if custom_params:
                params.update(custom_params)
            return self.client.call(self.operation_name, **params)

        def call_without_pagination(page, updated_since):
            params = custom_params or {}
            return self.client.call(self.operation_name, **params)
        
        def call_with_request_reference_strategy(page, updated_since):
            """Strategy for operations that require Request_Reference parameter."""
            request_ref = {
                "Get_Ledger_Account_Summaries": {"Ledger_Reference": []}
            }.get(self.operation_name, {})
            
            params = {"Request_Reference": request_ref, "Response_Filter": {"Page": page}}
            if updated_since:
                params["Response_Filter"]["Updated_Since"] = updated_since
            if custom_params:
                params.update(custom_params)
            return self.client.call(self.operation_name, **params)
        
        def call_with_raw_response_fallback(page, updated_since):
            """Fallback strategy using raw response handling for problematic operations."""
            response_filter = {"Page": page}
            if updated_since:
                response_filter["Updated_Since"] = updated_since
            params = {"Response_Filter": response_filter}
            if custom_params:
                params.update(custom_params)
            if hasattr(self.client, 'call_with_raw_response'):
                return self.client.call_with_raw_response(self.operation_name, **params)
            else:
                return self.client.call(self.operation_name, **params)

        strategies = [
            call_with_response_filter,
            call_with_request_criteria,
            call_with_request_reference_strategy,
            call_with_page_arg,
            call_without_pagination,
            call_with_raw_response_fallback,
        ]

        for strategy in strategies:
            try:
                return strategy(page, updated_since)
            except TypeError:
                continue
        raise RuntimeError(f"All pagination strategies failed for {self.operation_name}")

    def paginate_operation(self, data_key, updated_since=None, custom_params=None, max_pages=None):
        """Handles pagination and returns all records for a Workday operation.
        
        Args:
            data_key (str): The key to extract records from response.
            updated_since (str, optional): Filter records updated since this RFC 3339 value.
            custom_params (dict, optional): Additional parameters to pass to the operation.
            max_pages (int, optional): Maximum number of pages to process. If None, process all pages.
            
        Returns:
            list: All records retrieved from the operation.
        """
        all_records = []
        page = 1
        total_pages = 1

        while page <= total_pages and (max_pages is None or page <= max_pages):
            response = self._try_pagination_strategies(page, updated_since, custom_params)
            serialized = serialize_object(response)
            records = safe_get_records(serialized, data_key)
            all_records.extend(records)

            results = serialized.get("Response_Results", {})
            # Defensive: handle missing, None values, or list format
            if isinstance(results, list):
                # Use first element if list is not empty, else empty dict
                results = results[0] if results else {}

            total_pages_val = results.get("Total_Pages")
            page_val = results.get("Page")
            try:
                total_pages = int(total_pages_val) if total_pages_val is not None else 1
            except (ValueError, TypeError):
                total_pages = 1
            try:
                current_page = int(page_val) if page_val is not None else page
            except (ValueError, TypeError):
                current_page = page
            page = current_page + 1

            if page > total_pages:
                break

        return all_records


def _workday_paginate(client, operation_name, data_key, updated_since):
    """Handles pagination and returns all records for a Workday operation."""
    paginator = WorkdayPaginator(client, operation_name)
    return paginator.paginate_operation(data_key, updated_since)


def _extract_key_value(record, wid_key):
    """Extract the WID value from a Workday reference field.
    
    Args:
        record (dict): The record containing the reference field.
        wid_key (str): The key name for the reference field (e.g., "Absence_Input_Reference").
    
    Returns:
        str or None: The WID value if found, None otherwise.
    """
    if not isinstance(record, dict) or not wid_key:
        return None
    
    ref_field = record.get(wid_key)
    if not isinstance(ref_field, dict):
        return None
    
    id_list = ref_field.get("ID")
    if not isinstance(id_list, list):
        return None
    
    # Find the ID entry with type "WID"
    for id_entry in id_list:
        if isinstance(id_entry, dict) and id_entry.get("type") == "WID":
            return id_entry.get("_value_1")
    
    return None


def call_workday_operation(client, operation_name: str, data_key: str, updated_since=None, wid_key=None):
    """
    Call a Workday SOAP operation and retrieve all paginated records.

    Args:
        client: Workday SOAP client instance.
        operation_name (str): Name of the Workday operation to call.
        data_key (str): Key to extract records from the response.
        updated_since (optional): Filter records updated since this RFC 3339 value.
        wid_key (str, optional): Key name for the reference field to extract key_value from.

    Returns:
        list: All records retrieved from the operation under data_key.
    """
    records = _workday_paginate(client, operation_name, data_key, updated_since)
    
    # Add key_value to each record if wid_key is provided
    if wid_key:
        for record in records:
            key_value = _extract_key_value(record, wid_key)
            if key_value:
                record["key_value"] = key_value
    
    return records


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
