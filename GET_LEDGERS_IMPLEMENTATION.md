# Get_Ledgers Implementation Without Request_Reference

## Overview
This document describes the changes made to support calling the Workday Get_Ledgers operation without the Request_Reference parameter, as specified in the Workday API documentation.

## Problem Statement
The Workday Get_Ledgers operation supports an optional Request_Reference parameter that can be used to filter specific ledgers. When omitted, the operation returns all available ledgers for the company. The generic WorkdayTableStream implementation was potentially trying to include Request_Reference parameters automatically.

## Solution
Modified the `Ledgers` class in `tap_workday/streams/financial_management.py` to include a custom `sync()` method that:

1. **Calls Get_Ledgers without Request_Reference**: The operation is called with only the Response_Filter parameter for pagination
2. **Maintains pagination support**: Uses Response_Filter with Page parameter for proper pagination
3. **Preserves existing functionality**: Maintains key_value extraction and record processing
4. **Follows error handling patterns**: Includes fallback strategies and proper exception handling

## Changes Made

### File: `tap_workday/streams/financial_management.py`

#### Modified the Ledgers class:
```python
class Ledgers(WorkdayTableStream):
    # ... existing properties ...
    
    def sync(self, state, transformer, parent_obj=None):
        """Custom sync for Get_Ledgers that calls without Request_Reference parameter."""
        # Custom implementation that:
        # 1. Gets all ledgers by omitting Request_Reference
        # 2. Uses Response_Filter only for pagination
        # 3. Handles fallback scenarios
        # 4. Maintains compatibility with existing patterns
```

## Key Implementation Details

### API Call Pattern
```python
# Primary call pattern - with Response_Filter only
response = client.call("Get_Ledgers", Response_Filter={"Page": page, "Updated_Since": updated_since})

# Fallback pattern - no parameters (gets all ledgers, first page only)  
response = client.call("Get_Ledgers")
```

### Request Structure (per Workday documentation)
```xml
<bsvc:Get_Ledgers_Request xmlns:bsvc="urn:com.workday/bsvc" bsvc:version="string">
  <!-- Request_Reference is OPTIONAL - omitted to get all ledgers -->
  <bsvc:Response_Filter> <!-- Optional -->
    <bsvc:Page>1</bsvc:Page>
    <bsvc:Updated_Since>2024-01-01T00:00:00Z</bsvc:Updated_Since>
  </bsvc:Response_Filter>
</bsvc:Get_Ledgers_Request>
```

### Response Processing
- Extracts records from `Response_Data.Actuals_Ledger`
- Handles pagination via `Response_Results` metadata
- Maintains `key_value` extraction using `Actuals_Ledger_Reference`

## Benefits

1. **Compliance with API**: Follows Workday documentation by making Request_Reference truly optional
2. **Gets all ledgers**: Returns complete ledger dataset without needing specific references
3. **Backward compatible**: Maintains existing stream interface and behavior
4. **Robust error handling**: Includes fallback strategies for different API response patterns
5. **Follows Singer.io patterns**: Maintains compliance with Singer specification and tap best practices

## Testing

The implementation can be tested by:
1. Running the tap with the financial_management_ledgers stream selected
2. Verifying that all ledgers are returned without filtering
3. Confirming pagination works correctly for large datasets
4. Checking that key_value extraction functions properly

## Notes

- This change only affects the Get_Ledgers operation in the Financial_Management service
- All other streams continue to use the generic WorkdayTableStream implementation
- The change maintains full compatibility with existing configurations and state management
- Error handling follows the established patterns in the codebase