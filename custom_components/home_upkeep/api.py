"""Sample API Client."""

from __future__ import annotations

import asyncio
import contextlib
import datetime
import logging
import socket
from typing import TYPE_CHECKING, Any

import aiohttp
import async_timeout

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    UpkeepApiClientCallback = Callable[[dict], Awaitable[None]]

_LOGGER = logging.getLogger(__name__)


class UpkeepApiClientError(Exception):
    """Exception to indicate a general API error."""


class UpkeepApiClientCommunicationError(
    UpkeepApiClientError,
):
    """Exception to indicate a communication error."""

    def __init__(self, message: str, status: int | None = None) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.status = status


class UpkeepApiClientAuthenticationError(
    UpkeepApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise UpkeepApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class UpkeepApiClient:
    """Sample API Client."""

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession,
    ) -> None:
        """Client to connect to the Upkeep addon."""
        self._host = host
        self._port = port
        self._session = session
        self._websocket: aiohttp.ClientWebSocketResponse | None = None
        self._websocket_task: asyncio.Task | None = None
        self._message_handlers: list[Callable[[dict], None]] = []
        self._close_handlers: list[Callable[[], None]] = []

    async def async_get_lists(self) -> Any:
        """Get all task lists from the addon."""
        return await self._api_wrapper(
            method="get",
            url=f"http://{self._host}:{self._port}/lists",
        )

    async def async_get_list(self, list_id: int) -> dict:
        """Get a task list from the addon."""
        return await self._api_wrapper(
            method="get",
            url=f"http://{self._host}:{self._port}/lists/{list_id}",
        )

    async def async_get_tasks(self, list_id: str) -> Any:
        """Get all tasks from the addon."""
        return await self._api_wrapper(
            method="get",
            url=f"http://{self._host}:{self._port}/tasks?list_id={list_id}",
        )

    async def async_update_task(
        self,
        task_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        completed: bool | None = None,
        due_date: datetime.date | None = None,
    ) -> None:
        """Update a task in the addon."""
        if isinstance(due_date, datetime.date):
            due_date = due_date.date()

        return await self._api_wrapper(
            method="patch",
            url=f"http://{self._host}:{self._port}/tasks/{task_id}",
            data={
                "task_id": task_id,
                "title": title,
                "description": description,
                "completed": completed,
                "due_date": due_date.isoformat() if due_date else None,
            },
            headers={"Content-Type": "application/json"},
        )

    async def async_delete_task(self, task_id: int) -> None:
        """Delete a task in the addon."""
        return await self._api_wrapper(
            method="delete",
            url=f"http://{self._host}:{self._port}/tasks/{task_id}",
        )

    async def async_connect_websocket(self) -> None:
        """Connect to the WebSocket API."""
        if self._websocket is not None:
            return

        _LOGGER.debug("Connecting to WebSocket API")
        try:
            ws_url = f"ws://{self._host}:{self._port}/ws"
            self._websocket = await self._session.ws_connect(ws_url)
            self._websocket_task = asyncio.create_task(self._websocket_listener())
        except Exception as exception:
            msg = f"Error connecting to WebSocket - {exception}"
            raise UpkeepApiClientCommunicationError(msg) from exception
        _LOGGER.debug("WebSocket API connected")

    async def async_disconnect_websocket(self) -> None:
        """Disconnect from the WebSocket API."""
        _LOGGER.debug("Disconnecting from WebSocket API")
        if self._websocket_task is not None:
            self._websocket_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._websocket_task
            self._websocket_task = None

        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None
        _LOGGER.debug("WebSocket API disconnected")

    async def async_add_message_handler(self, handler: UpkeepApiClientCallback) -> None:
        """Add a message handler for WebSocket updates."""
        if self._websocket is None:
            await self.async_connect_websocket()
        self._message_handlers.append(handler)

    async def async_remove_message_handler(
        self, handler: UpkeepApiClientCallback
    ) -> None:
        """Remove a message handler."""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)

    async def async_add_close_handler(
        self, handler: Callable[[], Awaitable[None]] | None = None
    ) -> None:
        """Add a close handler for WebSocket disconnections."""
        if self._websocket is None:
            await self.async_connect_websocket()
        self._close_handlers.append(handler)

    async def async_remove_close_handler(self, handler: Callable[[], None]) -> None:
        """Remove a close handler."""
        if handler in self._close_handlers:
            self._close_handlers.remove(handler)

    async def _websocket_listener(self) -> None:
        """Listen for WebSocket messages and dispatch to handlers."""
        if self._websocket is None:
            msg = "WebSocket must be connected before listening for messages"
            raise RuntimeError(msg)

        try:
            async for msg in self._websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_text_message(msg)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.error("WebSocket error: %s", self._websocket.exception())
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    _LOGGER.info("WebSocket connection closed")
                    break
        except asyncio.CancelledError:
            pass
        except (aiohttp.ClientError, ConnectionError):
            _LOGGER.exception("WebSocket listener error")
        finally:
            self._websocket = None
            await self._notify_close_handlers()

    async def _handle_text_message(self, msg: aiohttp.WSMessage) -> None:
        """Handle incoming text messages."""
        try:
            data = msg.json()
            for handler in self._message_handlers:
                try:
                    await handler(data)
                except (ValueError, TypeError, KeyError) as exception:
                    _LOGGER.warning("Error in WebSocket handler: %s", exception)
        except (ValueError, TypeError) as exception:
            _LOGGER.warning("Error parsing WebSocket message: %s", exception)

    async def _notify_close_handlers(self) -> None:
        """Notify all close handlers."""
        for handler in self._close_handlers:
            try:
                await handler()
            except (ValueError, TypeError, RuntimeError) as exception:
                _LOGGER.warning("Error in close handler: %s", exception)

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise UpkeepApiClientCommunicationError(
                msg,
            ) from exception
        except aiohttp.ClientResponseError as exception:
            msg = f"Error fetching information - {exception}"
            raise UpkeepApiClientCommunicationError(
                msg, status=exception.status
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise UpkeepApiClientCommunicationError(msg) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise UpkeepApiClientError(
                msg,
            ) from exception
