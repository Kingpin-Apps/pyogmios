"""The synchronous Ogmios client.

It runs an :class:`~pyogmios.AsyncClient` on a private event loop in a background thread, so both
clients share one implementation and behave the same. It is safe to use from several threads.
"""

from __future__ import annotations

import asyncio
import ssl
import threading
from collections.abc import Coroutine, Mapping
from types import TracebackType
from typing import Any, Literal, Self, TypeVar

from ._transport import DEFAULT_RECONNECT, Reconnect, Transport
from .client import DEFAULT_URL, AsyncClient, VersionCheck
from .health import Health

T = TypeVar("T")


class _Portal:
    """An event loop running in a daemon thread, to run coroutines from synchronous code."""

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, name="pyogmios-loop", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coroutine: Coroutine[Any, Any, T]) -> T:
        if threading.current_thread() is self._thread:
            coroutine.close()
            raise RuntimeError("pyogmios.Client cannot be used from inside its own event loop")
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

    def stop(self) -> None:
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            self._thread.join()
        self.loop.close()


class Client:
    """A synchronous client for Ogmios v7, with the same methods as :class:`~pyogmios.AsyncClient`.

    ::

        with Client("ws://localhost:1337") as client:
            epoch = client.call("queryLedgerState/epoch")

    See :class:`~pyogmios.AsyncClient` for the parameters.
    """

    def __init__(
        self,
        url: str = DEFAULT_URL,
        *,
        timeout: float | None = 60.0,
        headers: Mapping[str, str] | None = None,
        reconnect: Reconnect | None = DEFAULT_RECONNECT,
        check_version: VersionCheck = "warn",
        open_timeout: float | None = 10.0,
        ssl_context: ssl.SSLContext | None = None,
        transport: Transport | None = None,
    ) -> None:
        self._portal = _Portal()
        self._client = AsyncClient(
            url,
            timeout=timeout,
            headers=headers,
            reconnect=reconnect,
            check_version=check_version,
            open_timeout=open_timeout,
            ssl_context=ssl_context,
            transport=transport,
        )
        self._closed = False

    @property
    def url(self) -> str:
        return self._client.url

    @property
    def server_health(self) -> Health | None:
        """The health read when connecting, when ``check_version`` is not ``"off"``."""
        return self._client.server_health

    @property
    def generation(self) -> int:
        """How many WebSocket connections have been opened; see :attr:`AsyncClient.generation`."""
        return self._client.generation

    def connect(self) -> Self:
        """Check the server version and open the connection. Called by ``with``."""
        self._portal.run(self._client.connect())
        return self

    def close(self) -> None:
        """Close the connection and stop the background thread. Called at the end of ``with``."""
        if self._closed:
            return
        self._closed = True
        try:
            self._portal.run(self._client.close())
        finally:
            self._portal.stop()

    def __enter__(self) -> Self:
        return self.connect()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def health(self) -> Health:
        """Read the server's ``/health``; see :meth:`AsyncClient.health`."""
        return self._portal.run(self._client.health())

    def request(
        self,
        method: str,
        params: Any = None,
        *,
        timeout: float | Literal["default"] | None = "default",
    ) -> Any:
        """Send any JSON-RPC request and return its raw result; see :meth:`AsyncClient.request`."""
        return self._portal.run(self._client.request(method, params, timeout=timeout))

    def call(
        self,
        method: str,
        params: Any = None,
        *,
        timeout: float | Literal["default"] | None = "default",
    ) -> Any:
        """Call a method and return its parsed result; see :meth:`AsyncClient.call`."""
        return self._portal.run(self._client.call(method, params, timeout=timeout))
