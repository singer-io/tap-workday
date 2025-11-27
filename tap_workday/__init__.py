import json
import sys

import singer

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
    parsed_args = singer.utils.parse_args(REQUIRED_CONFIG_KEYS)
    state = {}
    if parsed_args.state:
        state = parsed_args.state
    LOGGER.info(f"Starting tap-workday with required config keys: {REQUIRED_CONFIG_KEYS}")


if __name__ == "__main__":
    main()
