import { DateTime } from "luxon";

import type { HomeAssistant, UnsubscribeFunc } from "./ha";

export interface Task {
  id: number;
  list_id: number;
  title: string;
  description: string | null;
  completed: boolean;
  due_date: string | null;
  reschedule_period: string | null;
  reschedule_base: "completed" | "due" | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  prohibited_months: number[];
  constraints: string[];
}

export interface TaskCreate {
  list_id: number;
  title: string;
  description?: string | null;
  completed?: boolean;
  due_date?: string | null;
  reschedule_period?: string | null;
  reschedule_base?: "completed" | "due" | null;
  prohibited_months?: number[];
  constraints?: string[];
}

export interface TaskUpdate {
  list_id?: number;
  title?: string;
  description?: string | null;
  completed?: boolean;
  due_date?: string | null;
  reschedule_period?: string | null;
  reschedule_base?: "completed" | "due" | null;
  completed_at?: string | null;
  updated_at?: string;
  prohibited_months?: number[];
  constraints?: string[];
}

export interface TaskUpdateResponse {
  task: Task;
  created_task: Task | null;
}

export interface TaskList {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

/** One add-on `list_<id>.json` file's parsed content. */
export interface ImportDoc {
  version?: number;
  list: TaskList;
  tasks: Task[];
}

export interface ImportConflict {
  id: number;
  name: string;
}

export interface ImportResult {
  imported: boolean;
  conflicts: ImportConflict[];
  list_count?: number;
  task_count?: number;
}

export interface HomeUpkeepEvent {
  type:
    | "task_created"
    | "task_updated"
    | "task_deleted"
    | "list_created"
    | "list_updated"
    | "list_deleted"
    | "data_imported"
    | "migrated_from_addon";
  list_id?: number;
  task?: Task;
  created_task?: Task | null;
  task_id?: number;
  list?: TaskList;
  migrated_from_addon?: boolean;
}

/** Thin typed wrapper over `hass.connection` for the home_upkeep WS commands. */
export class HomeUpkeepApi {
  constructor(private hass: HomeAssistant) {}

  listLists(): Promise<TaskList[]> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/lists/list",
    });
  }

  createList(name: string): Promise<TaskList> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/lists/create",
      name,
    });
  }

  renameList(listId: number, name: string): Promise<TaskList> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/lists/update",
      list_id: listId,
      name,
    });
  }

  deleteList(listId: number): Promise<{ success: boolean }> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/lists/delete",
      list_id: listId,
    });
  }

  listTasks(listId: number): Promise<Task[]> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/tasks/list",
      list_id: listId,
    });
  }

  createTask(payload: TaskCreate): Promise<Task> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/tasks/create",
      ...payload,
    });
  }

  updateTask(
    taskId: number,
    payload: TaskUpdate,
  ): Promise<TaskUpdateResponse> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/tasks/update",
      task_id: taskId,
      ...payload,
      // Local timezone, so due dates recomputed on completion land on the
      // correct local day (see CLAUDE.md's timezone-handling note). Set
      // after the payload spread so it can't be clobbered by a caller
      // that includes `updated_at` in its payload.
      updated_at: payload.updated_at ?? DateTime.now().toISO(),
    });
  }

  snoozeTask(
    taskId: number,
    period: string,
    updatedAt?: string,
  ): Promise<Task> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/tasks/snooze",
      task_id: taskId,
      period,
      updated_at: updatedAt ?? DateTime.now().toISO(),
    });
  }

  deleteTask(taskId: number): Promise<{ success: boolean }> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/tasks/delete",
      task_id: taskId,
    });
  }

  importJson(
    docs: ImportDoc[],
    overwriteListIds: number[] = [],
  ): Promise<ImportResult> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/import_json",
      docs,
      overwrite_list_ids: overwriteListIds,
    });
  }

  getMigrationStatus(): Promise<{ migrated_from_addon: boolean }> {
    return this.hass.connection.sendMessagePromise({
      type: "home_upkeep/migration_status",
    });
  }

  subscribe(
    callback: (event: HomeUpkeepEvent) => void,
  ): Promise<UnsubscribeFunc> {
    return this.hass.connection.subscribeMessage<HomeUpkeepEvent>(callback, {
      type: "home_upkeep/subscribe",
    });
  }
}
