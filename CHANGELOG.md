# Changelog

## 0.1.0
  * Supports discovery and sync modes for Workday SOAP API streams
  * Streams cover Human Resources, Financial Management, Absence Management, and Performance Management modules
  * Unauthorized streams (403/auth error) are now excluded from the catalog during discovery instead of raising an error [#PR](https://github.com/singer-io/tap-workday/pull/TBD)

## 0.0.2
  * Bump requests to 2.33.0 for security updates [#23](https://github.com/singer-io/tap-workday/pull/23)
