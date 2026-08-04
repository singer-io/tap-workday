# tap-workday

A [Singer](https://singer.io) tap for extracting data from Workday, outputting JSON that follows the [Singer specification](https://github.com/singer-io/getting-started/blob/master/docs/SPEC.md).

**Features:**
- Connects to the Workday API and retrieves data.
- Supports extraction from these Workday modules:
    - [Absence_Management](https://community.workday.com/sites/default/files/file-hosting/productionapi/Absence_Management/v45.0/Absence_Management.html)
    - [Financial_Management](https://community.workday.com/sites/default/files/file-hosting/productionapi/Financial_Management/v45.0/Financial_Management.html)
    - [Human_Resources](https://community.workday.com/sites/default/files/file-hosting/productionapi/Human_Resources/v45.0/Human_Resources.html)
    - [Performance_Management](https://community.workday.com/sites/default/files/file-hosting/productionapi/Performance_Management/v45.0/Performance_Management.html)
    - [Staffing](https://community.workday.com/sites/default/files/file-hosting/productionapi/Staffing/v45.0/Staffing.html)
- Outputs schemas for each resource.
- Handles incremental syncs using state.

---

## Available Streams

The tap extracts data from the following 30 streams, grouped by Workday module. Each stream corresponds to a JSON schema file in `tap_workday/schemas/`.

### Absence Management

| Stream Name | Schema File | Description |
|---|---|---|
| `absence_management_absence_inputs` | [absence_management_absence_inputs.json](tap_workday/schemas/absence_management_absence_inputs.json) | Employee absence input records including absence type, dates, and quantities |
| `absence_management_override_balances` | [absence_management_override_balances.json](tap_workday/schemas/absence_management_override_balances.json) | Manual override balance adjustments for employee absence accrual plans |

### Financial Management

| Stream Name | Schema File | Description |
|---|---|---|
| `financial_management_cost_centers` | [financial_management_cost_centers.json](tap_workday/schemas/financial_management_cost_centers.json) | Cost center definitions used for financial tracking and reporting |
| `financial_management_customer_categories` | [financial_management_customer_categories.json](tap_workday/schemas/financial_management_customer_categories.json) | Categories used to classify customers in financial transactions |
| `financial_management_fund_hierarchies` | [financial_management_fund_hierarchies.json](tap_workday/schemas/financial_management_fund_hierarchies.json) | Hierarchical groupings of funds for financial reporting |
| `financial_management_fund_types` | [financial_management_fund_types.json](tap_workday/schemas/financial_management_fund_types.json) | Types used to classify financial funds |
| `financial_management_funding_sources` | [financial_management_funding_sources.json](tap_workday/schemas/financial_management_funding_sources.json) | Sources of funding associated with financial transactions and grants |
| `financial_management_funds` | [financial_management_funds.json](tap_workday/schemas/financial_management_funds.json) | Fund definitions used in financial and grant management |
| `financial_management_journal_sources` | [financial_management_journal_sources.json](tap_workday/schemas/financial_management_journal_sources.json) | Source definitions that originate journal entries |
| `financial_management_journals` | [financial_management_journals.json](tap_workday/schemas/financial_management_journals.json) | Journal entries recording financial transactions and accounting events |
| `financial_management_ledger_account_summaries` | [financial_management_ledger_account_summaries.json](tap_workday/schemas/financial_management_ledger_account_summaries.json) | Summary-level ledger accounts used for financial roll-up reporting |
| `financial_management_ledgers` | [financial_management_ledgers.json](tap_workday/schemas/financial_management_ledgers.json) | Ledger definitions that organize financial accounts |
| `financial_management_organizations` | [financial_management_organizations.json](tap_workday/schemas/financial_management_organizations.json) | Financial management organizations such as companies and business units |
| `financial_management_position_budgets` | [financial_management_position_budgets.json](tap_workday/schemas/financial_management_position_budgets.json) | Budget allocations associated with workforce positions |
| `financial_management_program_hierarchies` | [financial_management_program_hierarchies.json](tap_workday/schemas/financial_management_program_hierarchies.json) | Hierarchical groupings of financial programs |
| `financial_management_programs` | [financial_management_programs.json](tap_workday/schemas/financial_management_programs.json) | Financial programs used to track spending and funding by initiative |
| `financial_management_revenue_categories` | [financial_management_revenue_categories.json](tap_workday/schemas/financial_management_revenue_categories.json) | Categories used to classify revenue in financial transactions |
| `financial_management_revenue_category_hierarchies` | [financial_management_revenue_category_hierarchies.json](tap_workday/schemas/financial_management_revenue_category_hierarchies.json) | Hierarchical groupings of revenue categories |
| `financial_management_spend_category_hierarchies` | [financial_management_spend_category_hierarchies.json](tap_workday/schemas/financial_management_spend_category_hierarchies.json) | Hierarchical groupings of spend categories for expense classification |
| `financial_management_supplier_categories` | [financial_management_supplier_categories.json](tap_workday/schemas/financial_management_supplier_categories.json) | Categories used to classify suppliers in procurement and payables |

### Human Resources

| Stream Name | Schema File | Description |
|---|---|---|
| `human_resources_job_categories` | [human_resources_job_categories.json](tap_workday/schemas/human_resources_job_categories.json) | Categories used to group and classify job profiles |
| `human_resources_job_family_groups` | [human_resources_job_family_groups.json](tap_workday/schemas/human_resources_job_family_groups.json) | Top-level groupings of related job families |
| `human_resources_job_profiles` | [human_resources_job_profiles.json](tap_workday/schemas/human_resources_job_profiles.json) | Job profile definitions including title, level, and compensation details |
| `human_resources_locations` | [human_resources_locations.json](tap_workday/schemas/human_resources_locations.json) | Physical and virtual work locations used across the organization |
| `human_resources_organizations` | [human_resources_organizations.json](tap_workday/schemas/human_resources_organizations.json) | HR organizations such as supervisory orgs and departments |

### Performance Management

| Stream Name | Schema File | Description |
|---|---|---|
| `performance_management_certification_issuers` | [performance_management_certification_issuers.json](tap_workday/schemas/performance_management_certification_issuers.json) | Organizations authorized to issue employee certifications |
| `performance_management_competencies` | [performance_management_competencies.json](tap_workday/schemas/performance_management_competencies.json) | Skills and behaviors used to evaluate employee performance |
| `performance_management_competency_categories` | [performance_management_competency_categories.json](tap_workday/schemas/performance_management_competency_categories.json) | Categories used to group related competencies |
| `performance_management_degrees` | [performance_management_degrees.json](tap_workday/schemas/performance_management_degrees.json) | Academic degree types recognized in employee education records |

### Staffing

| Stream Name | Schema File | Description |
|---|---|---|
| `staffing_organizations` | [staffing_organizations.json](tap_workday/schemas/staffing_organizations.json) | Staffing organizations used for headcount planning and position management |

---

## Getting Started

### 1. Installation

Clone the repository and install the tap in a virtual environment:

```bash
virtualenv -p python3 venv
source venv/bin/activate
python setup.py install
# or
cd .../tap-workday
pip install -e .
```

### 2. Dependencies

Install required libraries:

```bash
pip install singer-python target-stitch target-json
```
You may also want to check out:
- [singer-tools](https://github.com/singer-io/singer-tools)
- [target-stitch](https://github.com/singer-io/target-stitch)

### 3. Configuration

Create a `config.json` file with your Workday credentials and settings:

```json
{
    "client_id": "Y2Q5YmU4...",
    "client_secret": "bma39u1i...",
    "refresh_token": "k2grvt6s...",
    "tenant": "your_tenant",
    "hostname": "wd2-impl-services1.workday.com",
    "start_date": "2024-01-01T00:00:00Z"
}
```

**Optional:** to enable a WS-Security username/password fallback when OAuth fails:

```json
{
    "client_id": "Y2Q5YmU4...",
    "client_secret": "bma39u1i...",
    "refresh_token": "k2grvt6s...",
    "tenant": "your_tenant",
    "hostname": "wd2-impl-services1.workday.com",
    "start_date": "2024-01-01T00:00:00Z",
    "enable_wssecurity_fallback": true,
    "username": "user@your_tenant",
    "password": "your_password"
}
```

| Key | Required | Default | Description |
|---|---|---|---|
| `client_id` | Yes | — | OAuth 2.0 client ID |
| `client_secret` | Yes | — | OAuth 2.0 client secret |
| `refresh_token` | Yes | — | OAuth 2.0 refresh token |
| `tenant` | Yes | — | Workday tenant name |
| `hostname` | Yes | — | Workday API hostname |
| `start_date` | Yes | — | Earliest date to sync (RFC 3339) |
| `enable_wssecurity_fallback` | No | `false` | When `true`, falls back to username/password if OAuth fails |
| `username` | No | — | ISU username — required only when `enable_wssecurity_fallback` is `true` |
| `password` | No | — | ISU password — required only when `enable_wssecurity_fallback` is `true` |
| `token_endpoint` | No | derived | Override the OAuth token URL (derived from `hostname`+`tenant` by default) |

Optionally, you can also create a `state.json` file to track sync progress:

```json
{
    "currently_syncing": "engage",
    "bookmarks": {
        "export": "2019-09-27T22:34:39.000000Z",
        "funnels": "2019-09-28T15:30:26.000000Z",
        "revenue": "2019-09-28T18:23:53Z"
    }
}
```

### 4. Discovery Mode

Generate a catalog of available streams and fields:

```bash
tap-workday --config config.json --discover > catalog.json
```

### 5. Sync Mode

Run the tap to extract data and update the state:

```bash
tap-workday --config tap_config.json --catalog catalog.json > state.json
tail -1 state.json > state.json.tmp && mv state.json.tmp state.json
```

To output to JSON for review:

```bash
tap-workday --config tap_config.json --catalog catalog.json | target-json > state.json
tail -1 state.json > state.json.tmp && mv state.json.tmp state.json
```

To test with Stitch Import API in dry-run mode:

```bash
tap-workday --config tap_config.json --catalog catalog.json | target-stitch --config target_config.json --dry-run > state.json
tail -1 state.json > state.json.tmp && mv state.json.tmp state.json
```

### 6. Testing

Lint your code for quality:

```bash
pylint tap_workday -d missing-docstring -d logging-format-interpolation -d too-many-locals -d too-many-arguments
```

Example output:
```
Your code has been rated at 9.67/10
```

To validate the tap with [singer-check-tap](https://github.com/singer-io/singer-tools#singer-check-tap):

```bash
tap_workday --config tap_config.json --catalog catalog.json | singer-check-tap > state.json
tail -1 state.json > state.json.tmp && mv state.json.tmp state.json
```

#### Unit Testing

Run tests with:

```bash
python -m pytest --verbose
```

Install test dependencies if needed:

```bash
pip install -e .'[dev]'
```

---

© 2019 Stitch
