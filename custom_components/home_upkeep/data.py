"""Custom types for home-upkeep-component."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import UpkeepApiClient
    from .coordinator import UpkeepCoordinator


type UpkeepConfigEntry = ConfigEntry[UpkeepData]


@dataclass
class UpkeepData:
    """Data for the Upkeep integration."""

    client: UpkeepApiClient
    coordinator: UpkeepCoordinator
    integration: Integration
