"""Todo integration for Home Upkeep."""

from __future__ import annotations

import asyncio
import contextlib
import datetime
import logging
from typing import TYPE_CHECKING

import aiohttp
from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity

from .api import UpkeepApiClient, UpkeepApiClientCommunicationError
from .entity import UpkeepEntity

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import UpkeepCoordinator
    from .data import UpkeepConfigEntry


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: UpkeepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the todo platform."""
    coordinator: UpkeepCoordinator = entry.runtime_data.coordinator
    client: UpkeepApiClient = coordinator.config_entry.runtime_data.client
    existing_entities = {}

    # Load initial todo entities from the API
    async def _load_initial_entities() -> None:
        """Load initial todo entities from the API."""
        new_entities = []
        for task_list in await client.async_get_lists():
            existing_entity = existing_entities.get(task_list["id"])
            if existing_entity is None:
                new_entity = UpkeepTodoEntity(coordinator, task_list)
                new_entities.append(new_entity)
                existing_entities[task_list["id"]] = new_entity
            else:
                await existing_entity.reload_initial_data()
        async_add_entities(new_entities)

    # Subscribe to websocket events for new lists
    async def _handle_websocket_message(message: dict) -> None:
        if message["type"] == "list_created":
            task_list = message["list"]
            existing_entity = existing_entities.get(task_list["id"])
            if existing_entity is None:
                new_entity = UpkeepTodoEntity(coordinator, task_list)
                existing_entities[task_list["id"]] = new_entity
                async_add_entities([new_entity])
            else:
                await existing_entity.reload_initial_data()

    def _handle_websocket_close() -> None:
        """Handle WebSocket close and schedule reconnection."""
        _hass.async_create_task(_reconnect_websocket())

    async def _reconnect_websocket() -> None:
        """Reconnect WebSocket and re-add message handler."""
        delay = 5.0
        while True:
            try:
                await asyncio.sleep(delay)
                _LOGGER.debug("Attempting to reconnect WebSocket for setup")
                await client.async_add_close_handler(_handle_websocket_close)
                await client.async_add_message_handler(_handle_websocket_message)
                await _load_initial_entities()
                _LOGGER.debug("WebSocket reconnected successfully for setup")
                break
            except (
                UpkeepApiClientCommunicationError,
                ConnectionError,
                TimeoutError,
            ) as exception:
                _LOGGER.warning(
                    "WebSocket reconnection failed for setup: %s", exception
                )
                delay = min(delay * 1.5, 60.0)

    await client.async_add_close_handler(_handle_websocket_close)
    await client.async_add_message_handler(_handle_websocket_message)
    await _load_initial_entities()


class UpkeepTodoEntity(UpkeepEntity, TodoListEntity):
    """UpkeepTodoEntity class."""

    def __init__(self, coordinator: UpkeepCoordinator, task_list: dict) -> None:
        """Initialize the todo entity class."""
        super().__init__(coordinator)
        self._attr_unique_id = f"upkeep_list_{task_list['id']}"
        self.__client = coordinator.config_entry.runtime_data.client
        self.__id = task_list["id"]
        self.__name = task_list["name"]
        self.__deleted = False
        self.__reconnection_task: asyncio.Task | None = None
        self.__reconnection_delay = 5.0  # seconds
        self.__tasks = []

    async def async_added_to_hass(self) -> None:
        """Start the todo entity."""
        await super().async_added_to_hass()
        await self.__client.async_add_close_handler(self.__handle_websocket_close)
        await self.__client.async_add_message_handler(
            self.__async_handle_websocket_message
        )
        await self.__load_initial_data()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        await self.__client.async_remove_message_handler(
            self.__async_handle_websocket_message
        )
        await self.__client.async_remove_close_handler(self.__handle_websocket_close)
        if self.__reconnection_task:
            self.__reconnection_task.cancel()
            self.__reconnection_task = None
        await super().async_will_remove_from_hass()

    async def reload_initial_data(self) -> None:
        """Reload initial task data and list information."""
        try:
            await self.__load_initial_data()
        except UpkeepApiClientCommunicationError as e:
            if e.status != aiohttp.web.HTTPNotFound.status_code:
                raise
            self.__mark_unavailable()

    async def __load_initial_data(self) -> None:
        """Load initial task data and list information."""
        self.__tasks = await self.__client.async_get_tasks(self.__id)
        task_list = await self.__client.async_get_list(self.__id)
        self.__update_state(task_list)

    def __handle_websocket_close(self) -> None:
        """Handle WebSocket close event."""
        self.__mark_unavailable()
        self.__schedule_reconnection()

    def __mark_unavailable(self) -> None:
        """Mark entity as unavailable and update state."""
        self.__deleted = True
        self.schedule_update_ha_state()

    def __schedule_reconnection(self) -> None:
        """Schedule a WebSocket reconnection attempt."""
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
                await self.__attempt_reconnection()
                await self.reload_initial_data()
                _LOGGER.debug(
                    "WebSocket reconnected successfully for entity %s", self.__id
                )
                break
            except (
                UpkeepApiClientCommunicationError,
                ConnectionError,
                TimeoutError,
            ) as exception:
                _LOGGER.warning(
                    "WebSocket reconnection failed for entity %s: %s",
                    self.__id,
                    exception,
                )
                delay = min(delay * 1.5, 60.0)

        self.__reconnection_task = None

    async def __attempt_reconnection(self) -> None:
        """Attempt to reconnect to WebSocket."""
        _LOGGER.debug("Attempting to reconnect WebSocket for entity %s", self.__id)
        await self.__client.async_add_close_handler(self.__handle_websocket_close)
        await self.__client.async_add_message_handler(
            self.__async_handle_websocket_message
        )

    async def __async_handle_websocket_message(self, message: dict) -> None:
        if message["type"] == "list_updated":
            task_list = message["list"]
            if task_list["id"] == self.__id:
                self.__update_state(task_list)
        elif message["type"] == "list_deleted":
            list_id = message["list_id"]
            if list_id == self.__id:
                self.__deleted = True
                self.async_write_ha_state()
        elif message["type"] == "task_created":
            if message["list_id"] == self.__id:
                self.__add_task(message["task"])
        elif message["type"] == "task_updated":
            if message["list_id"] == self.__id:
                self.__update_task(message["task"])
        elif message["type"] == "task_deleted":
            if message["list_id"] == self.__id:
                self.__delete_task(message["task_id"])

    def __add_task(self, task: dict) -> None:
        self.__tasks.append(task)
        self.schedule_update_ha_state()

    def __update_task(self, task: dict) -> None:
        for existing_task in self.__tasks:
            if existing_task["id"] == task["id"]:
                existing_task.update(task)
                self.schedule_update_ha_state()
                break

    def __delete_task(self, task_id: str) -> None:
        self.__tasks = [task for task in self.__tasks if task["id"] != task_id]
        self.schedule_update_ha_state()

    def __update_state(self, task_list: dict) -> None:
        if "name" in task_list:
            self.__name = task_list["name"]
        self.__deleted = False
        self.schedule_update_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the todo list."""
        return self.__name

    @property
    def available(self) -> bool:
        """Return if the todo list is available."""
        return not self.__deleted

    @property
    def state(self) -> str:
        """Return number of active tasks."""
        return sum([1 for t in self.__tasks if not t.get("completed", False)])

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return list of todo items."""
        items = []
        for task in self.__tasks:
            status = (
                TodoItemStatus.COMPLETED
                if task.get("completed")
                else TodoItemStatus.NEEDS_ACTION
            )

            # Parse optional due date
            due_date = None
            if due_date_str := task.get("due_date"):
                with contextlib.suppress(ValueError, TypeError):
                    due_date = datetime.datetime.fromisoformat(due_date_str)

            items.append(
                TodoItem(
                    summary=task["title"],
                    uid=task["id"],
                    status=status,
                    due=due_date,
                )
            )
        return items
