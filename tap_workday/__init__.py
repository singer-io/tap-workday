import json
import sys

import singer

from tap_workday.client import Client
from tap_workday.discover import discover
from tap_workday.sync import sync

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS = [
    "tenant",
    "username",
    "password",
    "hostname",
    "start_date",
]


def do_discover():
    """
    Discover and emit the catalog to stdout
    """
    LOGGER.info("Starting discover")
    catalog = discover()
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

    client = Client(parsed_args.config)
    if parsed_args.discover:
        do_discover()
    elif parsed_args.catalog:
        sync(
            client=client,
            config=parsed_args.config,
            catalog=parsed_args.catalog,
            state=state,
        )


if __name__ == "__main__":
    main()
