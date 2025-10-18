"""Todo integration for Home Upkeep."""

from __future__ import annotations

import contextlib
import datetime
from typing import TYPE_CHECKING

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity

from .entity import UpkeepEntity

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
    existing_ids = set()

    # Subscribe to websocket events for new lists
    async def _handle_websocket_message(message: dict) -> None:
        if message["type"] == "list_created":
            task_list = message["list"]
            if task_list["id"] not in existing_ids:
                new_entity = UpkeepTodoEntity(coordinator, task_list)
                existing_ids.add(task_list["id"])
                async_add_entities([new_entity])

    await coordinator.config_entry.runtime_data.client.async_add_message_handler(
        _handle_websocket_message
    )

    # Initial load
    entities = []
    for (
        task_list
    ) in await coordinator.config_entry.runtime_data.client.async_get_lists():
        if task_list["id"] not in existing_ids:
            entities.append(UpkeepTodoEntity(coordinator, task_list))
            existing_ids.add(task_list["id"])

    async_add_entities(entities)


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
        self.__tasks = []

    async def async_added_to_hass(self) -> None:
        """Start the todo entity."""
        await super().async_added_to_hass()
        await self.__client.async_add_message_handler(
            self.__async_handle_websocket_message
        )
        self.__tasks = await self.__client.async_get_tasks(self.__id)
        task_list = await self.__client.async_get_list(self.__id)
        self.__update_state(task_list)

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
