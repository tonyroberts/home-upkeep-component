"""DataUpdateCoordinator for home-upkeep-component."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


class UpkeepCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        return

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False
