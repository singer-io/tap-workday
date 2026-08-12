import json
import sys

import singer

from tap_workday.client import Client
from tap_workday.discover import discover
from tap_workday.sync import sync
from typing import Dict

LOGGER = singer.get_logger()

OAUTH_CONFIG_FIELDS = ("client_id", "client_secret", "refresh_token")

# OAuth 2.0 is the primary authentication mechanism; client_id, client_secret,
# and refresh_token are always required.  username/password are optional and
# used only as a fallback when OAuth authentication fails.
REQUIRED_CONFIG_KEYS = [
    "tenant",
    "hostname",
    "start_date",
    *OAUTH_CONFIG_FIELDS,
]


def do_discover(config, client=None):
    """
    Discover and emit the catalog to stdout
    """
    LOGGER.info("Starting discover")
    catalog = discover(config, client=client)
    json.dump(catalog.to_dict(), sys.stdout, indent=2)
    LOGGER.info("Finished discover")


@singer.utils.handle_top_exception(LOGGER)
def main():
    """
    Run the tap
    """
    parsed_args = singer.utils.parse_args(REQUIRED_CONFIG_KEYS)
    state = {}
    if parsed_args.state:
        state = parsed_args.state

    # Pass config_path so the OAuth token manager can persist rotated refresh tokens
    # back to the config file for subsequent tap processes to read.
    client = Client(parsed_args.config, config_path=parsed_args.config_path)
    client.check_credentials()

    if parsed_args.discover:
        do_discover(parsed_args.config, client)
    elif parsed_args.catalog:
        sync(
            client=client,
            config=parsed_args.config,
            catalog=parsed_args.catalog,
            state=state,
        )


if __name__ == "__main__":
    main()
