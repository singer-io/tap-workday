## 0.1.0
  * Streams the credentials cannot access (403 / authorization failure) are now excluded from the catalog during discovery instead of raising an error.
  * `discover()` now accepts a `Client` instance instead of a raw config dict, enabling access checks during discovery.
  * Added `check_access()` instance method to `BaseStream` and `WorkdayTableStream`; `Ledgers.check_access` converted from classmethod to instance method.
  * Added `WorkdayForbiddenError` exception class for authorization failures.
  * Added `_apply_access_checks()` and `_prune_inaccessible_children()` helpers in `discover.py` with cascading child-stream exclusion.
  * Added unit tests for discovery, access-check behaviour, and stream-exclusion cascading.

## 0.0.2
  * Supports discovery and sync modes for Workday SOAP API streams
  * Streams cover Human Resources, Financial Management, Absence Management, and Performance Management modules
