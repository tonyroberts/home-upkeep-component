"""
Custom integration for Home Upkeep todo lists.

For more details about this integration, please refer to
https://github.com/tonyroberts/home-upkeep-component
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import UpkeepApiClient
from .const import DOMAIN, LOGGER
from .coordinator import UpkeepCoordinator
from .data import UpkeepData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import UpkeepConfigEntry

PLATFORMS: list[Platform] = [
    Platform.TODO,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UpkeepConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    client = UpkeepApiClient(
        host=entry.data[CONF_HOST],
        port=int(entry.data[CONF_PORT]),
        session=async_get_clientsession(hass),
    )

    coordinator = UpkeepCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        client=client,
    )

    # Check we can connect to the WebSocket API
    await coordinator.async_connect_websocket()

    entry.runtime_data = UpkeepData(
        client=client,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: UpkeepConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    await entry.runtime_data.coordinator.async_disconnect_websocket()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: UpkeepConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
