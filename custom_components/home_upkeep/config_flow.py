"""Adds config flow for Blueprint."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    UpkeepApiClient,
    UpkeepApiClientAuthenticationError,
    UpkeepApiClientCommunicationError,
    UpkeepApiClientError,
)
from .const import DOMAIN, LOGGER


class UpkeepFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Upkeep."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_api_connection(
                    host=user_input[CONF_HOST],
                    port=int(user_input[CONF_PORT]),
                )
            except UpkeepApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except UpkeepApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except UpkeepApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="Home Upkeep",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, "127.0.0.1"),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_PORT,
                        default=(user_input or {}).get(CONF_PORT, "8125"),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.NUMBER,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_api_connection(self, host: str, port: int) -> None:
        """Validate credentials."""
        client = UpkeepApiClient(
            host=host,
            port=port,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_lists()
