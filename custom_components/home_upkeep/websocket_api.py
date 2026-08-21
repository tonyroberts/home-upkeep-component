"""
WebSocket command surface for the Home Upkeep integration.

Mirrors the add-on backend's REST endpoints 1:1 (see `backend/app/main.py`).
Auth is implicit: only authenticated WebSocket connections reach these
handlers at all.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util

from .const import SIGNAL_UPKEEP_CHANGED
from .logic import calculate_next_due_date
from .migration import async_import_from_docs
from .store import _UNSET, ImportConflictError, async_get_store

# ruff (TC002) wants type-only imports under TYPE_CHECKING to avoid an
# unnecessary runtime import, since `from __future__ import annotations`
# means annotations are never evaluated at runtime anyway.
if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.components.websocket_api import ActiveConnection
    from homeassistant.core import HomeAssistant

    from .models import StoredTask
    from .store import HomeUpkeepStore

_MONTH = vol.All(int, vol.Range(min=1, max=12))
_RESCHEDULE_PERIOD = vol.Match(r"^[0-9]+[dwm]$")
_TITLE = vol.All(str, vol.Length(min=1, max=200))
_DESCRIPTION = vol.Any(None, vol.All(str, vol.Length(max=1000)))

# tasks/update sends explicit `null` to clear these fields (matching the
# add-on REST API's nullable semantics), so their validators must accept
# None in addition to a real value.
_NULLABLE_DATE = vol.Any(None, cv.date)
_NULLABLE_DATETIME = vol.Any(None, cv.datetime)
_NULLABLE_RESCHEDULE_PERIOD = vol.Any(None, _RESCHEDULE_PERIOD)
_NULLABLE_RESCHEDULE_BASE = vol.Any(None, vol.In(["completed", "due"]))


def _serialize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Convert an event's StoredTask/StoredList payloads to JSON-safe dicts."""
    serialized = dict(event)
    for key in ("task", "created_task", "list"):
        if serialized.get(key) is not None:
            serialized[key] = serialized[key].to_storage()
    return serialized


def _create_followup_task(
    store: HomeUpkeepStore, task: StoredTask, updated_at: datetime | None
) -> StoredTask:
    """
    Create the rescheduled follow-up task for a just-completed task.

    The client-supplied `updated_at` (local timezone) is preferred over
    server time so due dates land on the correct local day, matching the
    add-on backend's `update_task` behavior.
    """
    if task.reschedule_base == "due":
        base_date = task.due_date
    elif updated_at is not None:
        base_date = updated_at.date()
    elif task.completed_at is not None:
        # completed_at is stored in UTC (see store.py); convert to local
        # time before taking the date, or this reintroduces the
        # raw-UTC day-early bug fixed in commit 8439bf6.
        base_date = dt_util.as_local(task.completed_at).date()
    else:
        base_date = None
    base_date = base_date or dt_util.now().date()

    next_due = calculate_next_due_date(
        base_date, task.reschedule_period, task.prohibited_months
    )
    return store.create_task(
        task.list_id,
        task.title,
        task.description,
        due_date=next_due,
        reschedule_period=task.reschedule_period,
        reschedule_base=task.reschedule_base,
        prohibited_months=task.prohibited_months,
        constraints=task.constraints,
    )


# -------- Lists --------


@websocket_api.websocket_command({vol.Required("type"): "home_upkeep/lists/list"})
@websocket_api.async_response
async def handle_lists_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """List all task lists."""
    store = async_get_store(hass)
    connection.send_result(msg["id"], [lst.to_storage() for lst in store.list_lists()])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_upkeep/lists/create",
        vol.Required("name"): _TITLE,
    }
)
@websocket_api.async_response
async def handle_lists_create(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create a new task list."""
    store = async_get_store(hass)
    lst = store.create_list(msg["name"])
    connection.send_result(msg["id"], lst.to_storage())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_upkeep/lists/update",
        vol.Required("list_id"): int,
        vol.Required("name"): _TITLE,
    }
)
@websocket_api.async_response
async def handle_lists_update(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Rename a task list."""
    store = async_get_store(hass)
    lst = store.rename_list(msg["list_id"], msg["name"])
    if lst is None:
        connection.send_error(
            msg["id"], websocket_api.ERR_NOT_FOUND, "List not found"
        )
        return
    connection.send_result(msg["id"], lst.to_storage())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_upkeep/lists/delete",
        vol.Required("list_id"): int,
    }
)
@websocket_api.async_response
async def handle_lists_delete(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Delete a task list and all its tasks."""
    store = async_get_store(hass)
    if not store.delete_list(msg["list_id"]):
        connection.send_error(
            msg["id"], websocket_api.ERR_NOT_FOUND, "List not found"
        )
        return
    connection.send_result(msg["id"], {"success": True})


# -------- Tasks --------


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_upkeep/tasks/list",
        vol.Required("list_id"): int,
    }
)
@websocket_api.async_response
async def handle_tasks_list(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """List all tasks for a list."""
    store = async_get_store(hass)
    tasks = store.list_tasks(msg["list_id"])
    connection.send_result(msg["id"], [task.to_storage() for task in tasks])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_upkeep/tasks/get",
        vol.Required("task_id"): int,
    }
)
@websocket_api.async_response
async def handle_tasks_get(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Get a single task by ID."""
    store = async_get_store(hass)
    task = store.get_task(msg["task_id"])
    if task is None:
        connection.send_error(
            msg["id"], websocket_api.ERR_NOT_FOUND, "Task not found"
        )
        return
    connection.send_result(msg["id"], task.to_storage())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_upkeep/tasks/create",
        vol.Required("list_id"): int,
        vol.Required("title"): _TITLE,
        vol.Optional("description"): _DESCRIPTION,
        vol.Optional("completed"): bool,
        vol.Optional("due_date"): cv.date,
        vol.Optional("reschedule_period"): _RESCHEDULE_PERIOD,
        vol.Optional("reschedule_base"): vol.In(["completed", "due"]),
        vol.Optional("prohibited_months"): [_MONTH],
        vol.Optional("constraints"): [str],
    }
)
@websocket_api.async_response
async def handle_tasks_create(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create a new task."""
    store = async_get_store(hass)
    task = store.create_task(
        msg["list_id"],
        msg["title"],
        msg.get("description"),
        completed=msg.get("completed", False),
        due_date=msg.get("due_date"),
        reschedule_period=msg.get("reschedule_period"),
        reschedule_base=msg.get("reschedule_base", "completed"),
        prohibited_months=msg.get("prohibited_months"),
        constraints=msg.get("constraints"),
    )
    connection.send_result(msg["id"], task.to_storage())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_upkeep/tasks/update",
        vol.Required("task_id"): int,
        vol.Optional("list_id"): int,
        vol.Optional("title"): _TITLE,
        vol.Optional("description"): _DESCRIPTION,
        vol.Optional("completed"): bool,
        vol.Optional("due_date"): _NULLABLE_DATE,
        vol.Optional("reschedule_period"): _NULLABLE_RESCHEDULE_PERIOD,
        vol.Optional("reschedule_base"): _NULLABLE_RESCHEDULE_BASE,
        vol.Optional("completed_at"): _NULLABLE_DATETIME,
        vol.Optional("updated_at"): cv.datetime,
        vol.Optional("prohibited_months"): [_MONTH],
        vol.Optional("constraints"): [str],
    }
)
@websocket_api.async_response
async def handle_tasks_update(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Update an existing task, creating a rescheduled follow-up if needed."""
    store = async_get_store(hass)
    previous_task = store.get_task(msg["task_id"])
    was_completed = previous_task is not None and previous_task.completed
    task = store.update_task(
        msg["task_id"],
        list_id=msg.get("list_id"),
        title=msg.get("title"),
        description=msg.get("description", _UNSET),
        completed=msg.get("completed"),
        due_date=msg.get("due_date", _UNSET),
        reschedule_period=msg.get("reschedule_period", _UNSET),
        reschedule_base=msg.get("reschedule_base", _UNSET),
        completed_at=msg.get("completed_at", _UNSET),
        prohibited_months=msg.get("prohibited_months"),
        constraints=msg.get("constraints"),
    )
    if task is None:
        connection.send_error(
            msg["id"], websocket_api.ERR_NOT_FOUND, "Task not found"
        )
        return

    # Only create a follow-up on the completed=false->true transition, not
    # on every subsequent save of an already-completed recurring task (that
    # would otherwise create a duplicate follow-up on each unrelated edit).
    created_task = None
    if not was_completed and task.completed and task.reschedule_period:
        created_task = _create_followup_task(store, task, msg.get("updated_at"))

    connection.send_result(
        msg["id"],
        {
            "task": task.to_storage(),
            "created_task": created_task.to_storage() if created_task else None,
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_upkeep/tasks/snooze",
        vol.Required("task_id"): int,
        vol.Required("period"): _RESCHEDULE_PERIOD,
        vol.Optional("updated_at"): cv.datetime,
    }
)
@websocket_api.async_response
async def handle_tasks_snooze(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Snooze a task by pushing its due date forward by `period`."""
    store = async_get_store(hass)
    updated_at = msg.get("updated_at")
    base_date = (updated_at or dt_util.now()).date()
    new_due_date = calculate_next_due_date(base_date, msg["period"])

    task = store.update_task(msg["task_id"], due_date=new_due_date)
    if task is None:
        connection.send_error(
            msg["id"], websocket_api.ERR_NOT_FOUND, "Task not found"
        )
        return
    connection.send_result(msg["id"], task.to_storage())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_upkeep/tasks/delete",
        vol.Required("task_id"): int,
    }
)
@websocket_api.async_response
async def handle_tasks_delete(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Delete a task."""
    store = async_get_store(hass)
    if not store.delete_task(msg["task_id"]):
        connection.send_error(
            msg["id"], websocket_api.ERR_NOT_FOUND, "Task not found"
        )
        return
    connection.send_result(msg["id"], {"success": True})


# -------- Migration --------


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_upkeep/import_json",
        vol.Required("docs"): [dict],
        vol.Optional("overwrite_list_ids"): [int],
    }
)
@websocket_api.async_response
async def handle_import_json(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """
    Import lists/tasks from add-on export docs uploaded via the panel.

    A list whose ID already exists is reported back as a conflict
    (`imported: false`) instead of a WS error, so the panel can ask the
    user to confirm overwriting it and resend with `overwrite_list_ids`.
    """
    store = async_get_store(hass)
    overwrite_list_ids = set(msg.get("overwrite_list_ids", []))
    try:
        list_count, task_count = await async_import_from_docs(
            store, msg["docs"], overwrite_list_ids=overwrite_list_ids
        )
    except ImportConflictError as err:
        connection.send_result(
            msg["id"],
            {
                "imported": False,
                "conflicts": [
                    {"id": lst.id, "name": lst.name}
                    for lst in err.conflicting_lists
                ],
            },
        )
        return
    except (KeyError, TypeError, ValueError) as err:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_INVALID_FORMAT,
            f"Malformed export data: {err}",
        )
        return
    connection.send_result(
        msg["id"],
        {
            "imported": True,
            "conflicts": [],
            "list_count": list_count,
            "task_count": task_count,
        },
    )


@websocket_api.websocket_command(
    {vol.Required("type"): "home_upkeep/migration_status"}
)
@callback
def handle_migration_status(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Report whether an automatic add-on migration has completed."""
    store = async_get_store(hass)
    connection.send_result(
        msg["id"], {"migrated_from_addon": store.migrated_from_addon}
    )


# -------- Subscription --------


@websocket_api.websocket_command({vol.Required("type"): "home_upkeep/subscribe"})
@callback
def handle_subscribe(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Subscribe to task/list change events."""

    @callback
    def forward_event(event: dict[str, Any]) -> None:
        connection.send_event(msg["id"], _serialize_event(event))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_UPKEEP_CHANGED, forward_event
    )
    connection.send_result(msg["id"])


def async_register(hass: HomeAssistant) -> None:
    """Register all home_upkeep websocket commands."""
    websocket_api.async_register_command(hass, handle_lists_list)
    websocket_api.async_register_command(hass, handle_lists_create)
    websocket_api.async_register_command(hass, handle_lists_update)
    websocket_api.async_register_command(hass, handle_lists_delete)
    websocket_api.async_register_command(hass, handle_tasks_list)
    websocket_api.async_register_command(hass, handle_tasks_get)
    websocket_api.async_register_command(hass, handle_tasks_create)
    websocket_api.async_register_command(hass, handle_tasks_update)
    websocket_api.async_register_command(hass, handle_tasks_snooze)
    websocket_api.async_register_command(hass, handle_tasks_delete)
    websocket_api.async_register_command(hass, handle_import_json)
    websocket_api.async_register_command(hass, handle_migration_status)
    websocket_api.async_register_command(hass, handle_subscribe)
