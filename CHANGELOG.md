# Changelog


## 0.2.0
  * Added OAuth 2.0 authentication support alongside existing username/password auth
  * Integration tests improvements [#32](https://github.com/singer-io/tap-workday/pull/32)

## 0.1.0
  * Supports discovery and sync modes for Workday SOAP API streams
  * Streams cover Human Resources, Financial Management, Absence Management, and Performance Management modules
  * Unauthorized streams (403/auth error) are now excluded from the catalog during discovery instead of raising an error [#9](https://github.com/singer-io/tap-workday/pull/9)

## 0.0.2
  * Bump requests to 2.33.0 for security updates [#23](https://github.com/singer-io/tap-workday/pull/23)
