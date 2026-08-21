# home-upkeep-component: Merge with the Home Upkeep Panel Integration — Design

- **Date:** 2026-08-21
- **Status:** Approved design, pending spec review
- **Author:** Hugo (with Claude)

## 1. Context

This repo (`home-upkeep-component`) started as a companion integration that
talks to the `home-upkeep` add-on's REST/WebSocket API to expose `todo`
entities. The add-on itself has since been rewritten as a self-contained
Home Assistant custom integration + Lit panel, living in
`tonyroberts/home-upkeep-addon` under `custom_components/home_upkeep/` (see
that repo's `docs/superpowers/specs/2026-07-13-home-upkeep-panel-migration-design.md`).
That design's decision 5 and §13 always intended this repo to eventually
retire: *"the `todo`-entity role of the separate `home-upkeep-component` repo
folds in here"* and *"the separate `home-upkeep-component` repo is
retired/redirected."*

The currently open PR #17 (`auto-migration-and-domain-fix`) took a
stopgap path toward that: it renamed this repo's domain to
`home_upkeep_addon_bridge` (to avoid colliding with the panel integration's
`home_upkeep` domain when both are installed side by side) and added an
automatic migration that pulls add-on data via this repo's existing
`UpkeepApiClient` and calls a `home_upkeep.import_from_addon` **HA service**
exposed by the separately-installed panel integration. That PR was never
released — no real users have installed the `home_upkeep_addon_bridge`
domain.

This design skips the two-integration stopgap and does the retirement
directly: **this repo becomes the panel integration.** Upgrading
`home-upkeep-component` via HACS results in a one-time data migration (for
users who had the add-on + this component installed) and a complete new
panel — no separate panel integration to install, no domain collision to
avoid, no cross-integration service call.

## 2. Locked decisions

1. **Wholesale replacement.** `custom_components/home_upkeep_addon_bridge/`
   is deleted. `custom_components/home_upkeep/` in this repo becomes a copy
   of `home-upkeep-addon`'s `custom_components/home_upkeep/` (store, WS API,
   `todo.py`, `panel.py`, Lit frontend, existing `migration.py` manual import
   paths) — domain reverts to `home_upkeep` (no collision risk once there is
   only one integration).
2. **Upgrade migration is a one-time, in-process function call, not an HA
   service.** The only caller was the bridge integration calling across to
   the panel integration; now it's the same integration calling its own
   code. `migration.py` gains `async_import_addon_docs(store, docs,
   *, overwrite_list_ids=None) -> dict` (the logic already implemented for
   the `import_from_addon` service handler, extracted so both a caller and
   the manual paths can share it). The `import_from_addon` HA service itself
   is dropped — nothing else can call it now, and the manual fallback
   (`import_from_json` service, console script, panel Import button) is
   unaffected and stays as-is.
3. **Upgrade detection: legacy `CONF_HOST`/`CONF_PORT` in the config
   entry.** Only the pre-PR17 released version (domain `home_upkeep`, entry
   data `{host, port}` of the add-on, discovered via the `hassio` supervisor
   or entered manually) ever shipped to real users. `async_setup_entry`
   checks for those keys — if present and `store.migrated_from_addon` is
   not yet set, it fetches lists/tasks via a small ported REST-only
   `UpkeepApiClient` (trimmed from today's `api.py` — no WebSocket
   coordinator, no `todo` entities backed by the add-on; the panel's own
   `todo.py` covers `todo` entities from the store going forward) and calls
   `async_import_addon_docs` directly. Failures are caught and logged;
   the flag is only set on success or a reported conflict (mirrors the
   existing `migrated_from_addon` semantics — see decision 4 below).
4. **Reuse the existing `migrated_from_addon` flag and banner as-is.** No
   new UI is needed — the flag/store/WS-command/frontend-banner code
   ported wholesale in decision 1 already implements "a dismissible red
   banner nudging the user to uninstall the add-on," which is the
   requirement this task must preserve.
5. **Config entry cleanup.** After a successful (or conflicted) upgrade
   migration attempt, `CONF_HOST`/`CONF_PORT` are removed from the config
   entry's data via `async_update_entry` — they have no further purpose
   once migration has been attempted, and the new config flow (decision 6)
   never writes them for fresh installs.
6. **Config flow becomes the panel's simple single-instance flow.** No add-on
   discovery, no host/port form — copied from `home-upkeep-addon`'s
   `config_flow.py` as-is. Existing entries from before this change keep
   whatever data they have; the flow itself is only invoked for new
   installs.
7. **Manifest/packaging revert to the pre-bridge shape.** `manifest.json`
   domain `home_upkeep`, version placeholder `"0.0.0"` (this repo's
   `.github/workflows/release.yml` does a literal `sed` replace of
   `0.0.0` → the git tag at release time — unchanged by this task, and it
   already targets `custom_components/home_upkeep/`, so reverting the
   folder name/domain requires no workflow edits). `hacs.json` filename
   reverts to `home_upkeep.zip` (matches release.yml's zip target,
   unchanged from before PR #17).
8. **Frontend cache-busting (`?v=<version>` query param, per
   `home-upkeep-addon`'s `CLAUDE.md`) does not apply the same way here.**
   Since `manifest.json`'s version is a release-time placeholder in this
   repo (decision 7), not hand-bumped during development, this repo's
   `panel.py` cache-busting relies on the release tag changing on each
   published release — sufficient because HACS installs are always a
   tagged release, never a live dev branch.
9. **Tests port over wholesale.** `home-upkeep-addon`'s full `tests/` suite
   (logic, store, websocket_api, migration, todo) replaces this repo's
   current `tests/test_migration.py` (which tested the now-deleted bridge
   migration code). A new `tests/test_init.py` (or extending
   `test_migration.py`) covers the upgrade-detection path in
   `async_setup_entry` (decision 3): legacy-data-present-and-migrates,
   legacy-data-present-but-already-migrated (no-op), no-legacy-data
   (fresh install, no-op), fetch/import failure (flag stays unset, entry
   data untouched).
10. **PR #17 is repurposed, not superseded.** Its branch
    (`auto-migration-and-domain-fix`) is reset to `main` and rebuilt with
    fresh commits implementing this design; force-pushed to update the PR
    in place. Title/description updated to describe the merge instead of
    the bridge.

## 3. Target structure

```
custom_components/home_upkeep/          # domain: home_upkeep (was home_upkeep_addon_bridge)
├─ manifest.json                        # version "0.0.0", deps: http, websocket_api,
│                                        #   frontend, panel_custom, todo (dropped: hassio)
├─ config_flow.py                       # single-instance flow, ported from home-upkeep-addon
├─ __init__.py                          # async_setup_entry: init store → NEW: legacy-upgrade
│                                        #   migration check → register WS cmds → register panel
│                                        #   → forward todo
├─ const.py, models.py, store.py, logic.py, websocket_api.py, todo.py, panel.py,
│  strings.json, translations/en.json, services.yaml   # ported verbatim from home-upkeep-addon
├─ migration.py                         # ported manual import paths (import_from_json service,
│                                        #   async_import_from_docs) + NEW async_import_addon_docs
│                                        #   (extracted, no longer HA-service-only) + NEW
│                                        #   async_migrate_legacy_addon(hass, entry, store)
├─ legacy_api.py                        # NEW, trimmed: REST-only async_get_lists/async_get_tasks
│                                        #   ported from today's api.py, no coordinator/websocket
└─ frontend/                            # ported verbatim (Lit + TS + Vite source, dist/)
```

Deleted: `custom_components/home_upkeep_addon_bridge/` (all of it — `api.py`,
`coordinator.py`, `data.py`, `entity.py`, `todo.py`, `migration.py`,
`__init__.py`, `const.py`, `manifest.json`, `translations/`).

## 4. Upgrade migration flow

```
async_setup_entry(hass, entry):
    store = HomeUpkeepStore(hass); await store.async_load()
    ... register runtime_data ...

    if CONF_HOST in entry.data and not store.migrated_from_addon:
        await migration.async_migrate_legacy_addon(hass, entry, store)
        # on success or reported conflict: store.async_mark_migrated_from_addon()
        # already called inside async_migrate_legacy_addon; then:
        # hass.config_entries.async_update_entry(entry, data={})
        # on exception: logged, flag left unset, entry data untouched (retries next start)

    await websocket_api.async_register(hass)
    await panel.async_register_panel(hass)
    await hass.config_entries.async_forward_entry_setups(entry, ["todo"])
```

`async_migrate_legacy_addon` mirrors the already-implemented
`_async_handle_import_from_addon` service handler's logic exactly (decision
2), just called directly instead of via `hass.services.async_call`. No new
conflict-handling behavior — an existing non-empty store (e.g. a fresh
install where the user also ran a manual import first) is reported as a
conflict, flag still set, data left alone; the manual paths remain the way
to resolve it.

## 5. Out of scope

- Detecting or aiding actual add-on uninstallation — the banner stays a
  one-way, per-session-dismissible nudge (unchanged from the existing
  design).
- Any change to the WS API surface, store schema, or frontend behavior
  beyond what's already implemented in `home-upkeep-addon` — this is a
  packaging/merge task, not a feature change to the panel itself.
- Supporting the never-released `home_upkeep_addon_bridge` domain as a
  migration source (decision 3) — no real installs exist to migrate from.
