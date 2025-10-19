"""Constants for home-upkeep-component."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "home-upkeep"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

# Default host for Upkeep API
UPKEEP_DEFAULT_HOST = "127.0.0.1"

# Default port for Upkeep API
UPKEEP_DEFAULT_PORT = 8125
