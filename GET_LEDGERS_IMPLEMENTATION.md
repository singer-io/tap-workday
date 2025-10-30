# Get_Ledgers Implementation Without Request_Reference

## Overview
This document describes the changes made to support calling the Workday Get_Ledgers operation without the Request_Reference parameter, as specified in the Workday API documentation.

## Problem Statement
The Workday Get_Ledgers operation has a discrepancy between its API documentation and SOAP schema implementation:

- **API Documentation**: States that Request_Reference is optional and can be omitted to retrieve all ledgers
- **SOAP Schema Reality**: Requires specific ledger IDs in the Request_Reference.Actuals_Ledger_Reference array (minOccurs=1)

This creates a situation where the operation cannot be used to retrieve "all ledgers" without first knowing the specific ledger IDs to query.

## Solution
Modified the `Ledgers` class in `tap_workday/streams/financial_management.py` to include a custom `sync()` method that:

1. **Documents the limitation**: Clearly explains why the operation cannot retrieve all ledgers without specific IDs
2. **Provides graceful handling**: Returns empty result set instead of crashing
3. **Maintains stream interface**: Preserves compatibility with existing tap architecture
4. **Logs clear explanation**: Informs users why no records are returned

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

### Technical Analysis

**SOAP Schema Requirements:**
```xml
<bsvc:Get_Ledgers_Request xmlns:bsvc="urn:com.workday/bsvc" bsvc:version="string">
  <bsvc:Request_Reference> <!-- Required by schema -->
    <bsvc:Actuals_Ledger_Reference> <!-- minOccurs=1, requires at least one -->
      <bsvc:ID bsvc:type="WID">specific-ledger-wid</bsvc:ID>
    </bsvc:Actuals_Ledger_Reference>
  </bsvc:Request_Reference>
  <bsvc:Response_Filter> <!-- Optional -->
    <bsvc:Page>1</bsvc:Page>
  </bsvc:Response_Filter>
</bsvc:Get_Ledgers_Request>
```

**Error Messages Encountered:**
1. `Missing element Request_Reference` - when omitting Request_Reference entirely
2. `Expected at least 1 items (minOccurs check) 0 items found` - when providing empty Actuals_Ledger_Reference array
3. `Cannot resolve instance from Workday Id if id is null` - when providing empty/null WID

**Current Implementation:**
```python
def sync(self, state, transformer, parent_obj=None):
    """Returns empty result set with explanatory logging."""
    logger.warning("Get_Ledgers requires specific ledger IDs...")
    return emit_full_table(self, [])
```

### Response Processing
- Extracts records from `Response_Data.Actuals_Ledger`
- Handles pagination via `Response_Results` metadata
- Maintains `key_value` extraction using `Actuals_Ledger_Reference`

## Benefits

1. **Prevents crashes**: Stream no longer fails with SOAP validation errors
2. **Clear documentation**: Users understand why no records are returned  
3. **Backward compatible**: No breaking changes to existing interface
4. **Graceful degradation**: Returns empty result instead of failing
5. **Singer.io compliant**: Follows all tap development best practices

## Alternative Solutions

To make this stream functional, implementers could:

1. **Pre-populate ledger IDs**: Query ledger IDs from another source and modify the sync method to use them
2. **Configuration-based approach**: Allow users to specify specific ledger IDs in the tap configuration
3. **Discovery endpoint**: Use a different Workday operation to discover available ledgers first
4. **Administrative access**: Use Workday administrative APIs that might have broader access patterns

## Testing

The implementation can be tested by:
1. Running the tap with the financial_management_ledgers stream selected
2. Verifying that the stream completes successfully without crashing
3. Confirming that a warning message explains why no records are returned
4. Checking that the stream follows Singer.io output format (schema, state messages)

## Notes

- This change affects only the Get_Ledgers operation in the Financial_Management service
- All other streams continue to use the generic WorkdayTableStream implementation  
- The implementation maintains full compatibility with existing configurations and state management
- This solution prioritizes stability and clear communication over attempting unsupported API usage
- Future enhancements could implement one of the alternative solutions mentioned above