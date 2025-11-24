import json
import sys

import singer

from tap_workday.client import Client
from tap_workday.discover import discover
from tap_workday.sync import sync
from typing import Dict

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS = [
    "tenant",
    "username",
    "password",
    "hostname",
    "start_date",
]


@singer.utils.handle_top_exception(LOGGER)
def main():
    """
    Run the tap
    """
    LOGGER.info(f"Starting tap-workday with required config keys: {REQUIRED_CONFIG_KEYS}")


if __name__ == "__main__":
    main()