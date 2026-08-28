"""Serve the Lit frontend and register the Home Upkeep custom panel."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.panel_custom import async_register_panel
from homeassistant.loader import async_get_integration

# ruff (TC002) wants type-only imports under TYPE_CHECKING to avoid an
# unnecessary runtime import, since `from __future__ import annotations`
# means annotations are never evaluated at runtime anyway.
if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    PANEL_ICON,
    PANEL_STATIC_PATH,
    PANEL_TITLE,
    PANEL_URL_PATH,
    PANEL_WEBCOMPONENT_NAME,
)

FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"


async def async_register(hass: HomeAssistant) -> None:
    """Serve the built frontend and register the sidebar panel."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(PANEL_STATIC_PATH, str(FRONTEND_DIST), cache_headers=True)]
    )

    # entrypoint.js has a fixed filename, so with cache_headers=True a stale
    # copy would stick around in the browser cache across integration
    # upgrades. Bust it with the manifest version as a query string.
    integration = await async_get_integration(hass, DOMAIN)
    module_url = f"{PANEL_STATIC_PATH}/entrypoint.js?v={integration.version}"

    await async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_WEBCOMPONENT_NAME,
        module_url=module_url,
        embed_iframe=False,
        require_admin=False,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
    )
