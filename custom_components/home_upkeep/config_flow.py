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
from .const import DOMAIN, LOGGER, UPKEEP_DEFAULT_HOST, UPKEEP_DEFAULT_PORT


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
                        default=(user_input or {}).get(CONF_HOST, UPKEEP_DEFAULT_HOST),
                        description="The IP address or hostname of the Upkeep server",
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_PORT,
                        default=(user_input or {}).get(
                            CONF_PORT, str(UPKEEP_DEFAULT_PORT)
                        ),
                        description="The port number of the Upkeep server",
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.NUMBER,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
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
                return self.async_update_entry(
                    data=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(
                            user_input.get(CONF_HOST)
                            if user_input
                            else self.config_entry.data.get(
                                CONF_HOST, UPKEEP_DEFAULT_HOST
                            )
                        ),
                        description="The IP address or hostname of the Upkeep server",
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_PORT,
                        default=(
                            user_input.get(CONF_PORT)
                            if user_input
                            else self.config_entry.data.get(
                                CONF_PORT, str(UPKEEP_DEFAULT_PORT)
                            )
                        ),
                        description="The port number of the Upkeep server",
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
