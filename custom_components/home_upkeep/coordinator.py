"""DataUpdateCoordinator for home-upkeep-component."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import UpkeepApiClientCommunicationError
from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .api import UpkeepApiClient

_LOGGER = logging.getLogger(__name__)


class UpkeepCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        name: str,
        client: UpkeepApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, logger, name=name)
        self.__client = client
        self.__websocket_connected = False
        self.__reconnection_task: asyncio.Task | None = None
        self.__reconnection_delay = 5.0  # seconds
        self.__lists = {}
        self.__tasks = {}

    async def async_connect_websocket(self) -> None:
        """Connect to the WebSocket API."""
        if self.__websocket_connected:
            return
        await self.__client.async_connect_websocket()
        self.__websocket_connected = True
        await self.__client.async_add_close_handler(self.__handle_websocket_close)
        await self.__client.async_add_message_handler(
            self.__async_handle_websocket_message
        )
        _LOGGER.debug("WebSocket connected successfully")

    async def async_disconnect_websocket(self) -> None:
        """Disconnect from the WebSocket API."""
        if self.__reconnection_task is not None:
            self.__reconnection_task.cancel()
            self.__reconnection_task = None
        if self.__websocket_connected:
            await self.__client.async_disconnect_websocket()
            self.__websocket_connected = False
            _LOGGER.debug("WebSocket disconnected successfully")

    @property
    def client(self) -> UpkeepApiClient:
        """Return the client."""
        return self.__client

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def lists(self) -> dict[str, dict]:
        """Return the lists."""
        return self.__lists

    @property
    def tasks(self) -> dict[str, dict[str, dict]]:
        """Return the tasks."""
        return self.__tasks

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        self.__lists = {}
        self.__tasks = {}
        if not self.__websocket_connected:
            await self.async_connect_websocket()
        for task_list in await self.client.async_get_lists():
            list_id = task_list["id"]
            self.__lists[list_id] = task_list
            self.__tasks.setdefault(list_id, {})
            for task in await self.client.async_get_tasks(list_id):
                self.__tasks[list_id][task["id"]] = task
        async_dispatcher_send(self.hass, f"{DOMAIN}_reloaded")

    async def __handle_websocket_close(self) -> None:
        """Handle WebSocket close event."""
        _LOGGER.debug("WebSocket closed")
        self.__lists = {}
        self.__tasks = {}
        self.async_update_listeners()
        if not self.__reconnection_task:
            self.__reconnection_task = self.hass.async_create_task(
                self.__reconnect_websocket()
            )

    async def __reconnect_websocket(self) -> None:
        """Attempt to reconnect WebSocket by re-adding message handler."""
        delay = self.__reconnection_delay
        while True:
            try:
                await asyncio.sleep(delay)
                _LOGGER.debug("Attempting to reconnect WebSocket")
                await self.__client.async_add_close_handler(
                    self.__handle_websocket_close
                )
                await self.__client.async_add_message_handler(
                    self.__async_handle_websocket_message
                )
                _LOGGER.debug("WebSocket reconnected successfully")
                break
            except (
                UpkeepApiClientCommunicationError,
                ConnectionError,
                TimeoutError,
            ):
                _LOGGER.warning("WebSocket reconnection failed")
                delay = min(delay * 1.5, 60.0)

        self.__reconnection_task = None
        await self.async_request_refresh()

    async def __async_handle_websocket_message(self, message: dict) -> None:
        """Handle WebSocket message."""
        _LOGGER.debug("WebSocket message received: %s", message)
        list_id = None
        if message["type"] == "list_created" or message["type"] == "list_updated":
            task_list = message["list"]
            list_id = task_list["id"]
            self.__lists.setdefault(list_id, {}).update(message["list"])
        elif message["type"] == "list_deleted":
            list_id = message["list_id"]
            self.__lists.pop(list_id, None)
        elif message["type"] == "task_created" or message["type"] == "task_updated":
            list_id = message["list_id"]
            task = message["task"]
            tasks = self.__tasks.setdefault(list_id, {})
            tasks.setdefault(task["id"], {}).update(task)
        elif message["type"] == "task_deleted":
            list_id = message["list_id"]
            tasks = self.__tasks.setdefault(list_id, {})
            tasks.pop(message["task_id"], None)

        if message["type"] == "list_created":
            _LOGGER.debug("Sending list created notification for list %s", list_id)
            async_dispatcher_send(self.hass, f"{DOMAIN}_list_created", list_id)

        if list_id is not None:
            _LOGGER.debug("Sending update for list %s", list_id)
            async_dispatcher_send(self.hass, f"{DOMAIN}_update_{list_id}")
