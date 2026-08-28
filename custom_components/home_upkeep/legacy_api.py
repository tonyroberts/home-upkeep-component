"""
Minimal REST client for the retired add-on, used only for one-time upgrade migration.

Trimmed from this repo's original `api.py` (the pre-merge add-on companion
client): only the two read-only calls the upgrade migration needs
(`async_get_lists`, `async_get_tasks`) survive — no WebSocket coordinator, no
task mutation methods, since this integration no longer proxies live add-on
data (its own `todo.py` serves `todo` entities from the panel store instead).
See `docs/superpowers/specs/2026-08-21-merge-panel-integration-design.md`.
"""

from __future__ import annotations

import asyncio
import socket
from typing import Any

import aiohttp


class LegacyAddonApiError(Exception):
    """Raised when the retired add-on's REST API can't be reached or read."""


class LegacyAddonApiClient:
    """Read-only REST client for the add-on's `/lists` and `/tasks` endpoints."""

    def __init__(self, host: str, port: int, session: aiohttp.ClientSession) -> None:
        """Initialize the client with the add-on's host/port from the legacy entry."""
        self._host = host
        self._port = port
        self._session = session

    async def async_get_lists(self) -> list[dict[str, Any]]:
        """Fetch all task lists from the add-on."""
        return await self._get(f"http://{self._host}:{self._port}/lists")

    async def async_get_tasks(self, list_id: int) -> list[dict[str, Any]]:
        """Fetch all tasks for a list from the add-on."""
        return await self._get(
            f"http://{self._host}:{self._port}/tasks?list_id={list_id}"
        )

    async def _get(self, url: str) -> Any:
        try:
            async with asyncio.timeout(10):
                response = await self._session.request(method="get", url=url)
                response.raise_for_status()
                return await response.json()
        except TimeoutError as exception:
            msg = f"Timeout fetching {url}"
            raise LegacyAddonApiError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching {url}: {exception}"
            raise LegacyAddonApiError(msg) from exception
