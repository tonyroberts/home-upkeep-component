"""Config flow for the Home Upkeep integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN


class HomeUpkeepConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Home Upkeep."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial (and only) step: single-instance setup."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Home Upkeep", data={})

        return self.async_show_form(step_id="user")
