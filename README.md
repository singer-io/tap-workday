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
    "username": "user@talend_1",
    "password": "TLND&01",
    "tenant": "talend_1",
    "hostname": "wd1-impl-services1.workday.com",
    "start_date": "2019-01-01T00:00:00Z",
    "user_agent": "tap-workday <api_user_email@your_company.com>"
}
```

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
