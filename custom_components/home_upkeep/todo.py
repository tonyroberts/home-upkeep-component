"""Todo integration for Home Upkeep."""

from __future__ import annotations

import contextlib
import datetime
import logging
from typing import TYPE_CHECKING

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .entity import UpkeepEntity

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from typing import ClassVar

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import UpkeepCoordinator
    from .data import UpkeepConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UpkeepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the todo platform."""
    coordinator: UpkeepCoordinator = entry.runtime_data.coordinator
    existing_lists = set()

    async def _handle_list_added(list_id: int) -> None:
        if list_id not in existing_lists:
            existing_lists.add(list_id)
            async_add_entities([UpkeepTodoEntity(coordinator, list_id)])

    async def _load_initial_entities() -> None:
        list_entities = []
        for list_id in coordinator.lists:
            if list_id not in existing_lists:
                list_entities.append(UpkeepTodoEntity(coordinator, list_id))
                existing_lists.add(list_id)
        async_add_entities(list_entities)

    entry.runtime_data.todo_unsub = async_dispatcher_connect(
        hass,
        f"{DOMAIN}_list_created",
        _handle_list_added,
    )

    entry.runtime_data.todo_unsub = async_dispatcher_connect(
        hass,
        f"{DOMAIN}_reloaded",
        _load_initial_entities,
    )

    await _load_initial_entities()


async def async_unload_entry(
    _hass: HomeAssistant,
    entry: UpkeepConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    if entry.runtime_data.todo_unsub is not None:
        entry.runtime_data.todo_unsub()
        entry.runtime_data.todo_unsub = None


def _parse_datetime(dt_str: str) -> datetime:
    """
    Parse a date/time string known to be in UTC into a timezone-aware datetime.

    Supports ISO 8601 formats with or without timezone info, including 'Z' suffix.
    """
    # Replace 'Z' (ISO 8601 UTC) with '+00:00' so fromisoformat can handle it
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"

    dt = datetime.datetime.fromisoformat(dt_str)

    # If it's naive (no timezone info), assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.UTC)

    # Normalize to local timezone
    return dt.astimezone()


class UpkeepTodoEntity(UpkeepEntity, TodoListEntity):
    """UpkeepTodoEntity class."""

    _attr_supported_features: ClassVar[int] = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(self, coordinator: UpkeepCoordinator, list_id: int) -> None:
        """Initialize the todo entity class."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}-{list_id}"
        self.__client = coordinator.client
        self.__id = list_id

    async def async_added_to_hass(self) -> None:
        """Handle when entity is added to Home Assistant."""
        self._unsub = async_dispatcher_connect(
            self.hass,
            f"{DOMAIN}_update_{self.__id}",
            self.schedule_update_ha_state,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Handle when entity is removed from Home Assistant."""
        self._unsub()

    @property
    def name(self) -> str:
        """Return the name of the todo list."""
        return self.coordinator.lists.get(self.__id, {}).get("name")

    @property
    def available(self) -> bool:
        """Return if the todo list is available."""
        return self.__id in self.coordinator.lists

    @property
    def state(self) -> str:
        """Return number of active tasks."""
        tasks = self.coordinator.tasks.get(self.__id, {})
        return sum([1 for t in tasks.values() if not t.get("completed", False)])

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return list of todo items."""
        items = []
        tasks = self.coordinator.tasks.get(self.__id, {})

        # Parse tasks and group them
        due_tasks = []
        upcoming_tasks = []
        completed_tasks = []

        today = (
            datetime.datetime.now(tz=datetime.UTC)
            .astimezone()
            .replace(hour=0, minute=0, second=0, microsecond=0)
        )

        for task in tasks.values():
            # Parse datetime strings
            due_date = None
            completed_at = None
            created_at = None

            if due_date_str := task.get("due_date"):
                with contextlib.suppress(ValueError, TypeError):
                    due_date = datetime.date.fromisoformat(due_date_str)

            if completed_at_str := task.get("completed_at"):
                with contextlib.suppress(ValueError, TypeError):
                    completed_at = _parse_datetime(completed_at_str).astimezone()

            if created_at_str := task.get("created_at"):
                with contextlib.suppress(ValueError, TypeError):
                    created_at = _parse_datetime(created_at_str).astimezone()

            task_data = (task, due_date, completed_at, created_at)
            is_completed = task.get("completed", False)

            if is_completed:
                completed_tasks.append(task_data)
            elif due_date and due_date <= today.date():
                due_tasks.append(task_data)
            else:
                upcoming_tasks.append(task_data)

        # Sort each group by due_date, completed_at, created_at (descending order)
        min_dt = datetime.datetime.min.replace(tzinfo=today.tzinfo)

        def _pending_sort_key(
            x: tuple[
                dict,
                datetime.datetime | None,
                datetime.datetime | None,
                datetime.datetime | None,
            ],
        ) -> tuple[datetime.datetime, datetime.datetime, datetime.datetime]:
            (_task, due_date, _completed_at, created_at) = x
            return (due_date or min_dt.date(), created_at or min_dt)

        def _completed_sort_key(
            x: tuple[
                dict,
                datetime.datetime | None,
                datetime.datetime | None,
                datetime.datetime | None,
            ],
        ) -> tuple[datetime.datetime, datetime.datetime, datetime.datetime]:
            (_task, _due_date, completed_at, created_at) = x
            return (
                completed_at or min_dt,
                created_at or min_dt,
            )

        due_tasks.sort(key=_pending_sort_key, reverse=True)
        upcoming_tasks.sort(key=_pending_sort_key, reverse=True)
        completed_tasks.sort(key=_completed_sort_key, reverse=True)

        # Concatenate the three groups in order: due, upcoming, completed
        all_tasks = due_tasks + upcoming_tasks + completed_tasks

        # Create TodoItem objects from sorted tasks
        for task, due_date, _, _ in all_tasks:
            status = (
                TodoItemStatus.COMPLETED
                if task.get("completed")
                else TodoItemStatus.NEEDS_ACTION
            )

            items.append(
                TodoItem(
                    summary=task["title"],
                    description=task.get("description", None),
                    uid=str(task["id"]),
                    status=status,
                    due=due_date,
                )
            )
        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        await self.__client.async_create_task(
            list_id=self.__id,
            title=item.summary,
            due_date=item.due,
        )

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an item in the To-do list."""
        await self.__client.async_update_task(
            task_id=int(item.uid),
            title=item.summary,
            completed=item.status == TodoItemStatus.COMPLETED,
            due_date=item.due,
            description=item.description,
        )

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete an item in the To-do list."""
        for uid in uids:
            await self.__client.async_delete_task(task_id=int(uid))
