"""Transports: how JSON-RPC messages reach Ogmios, over WebSocket or HTTP."""

from __future__ import annotations

import asyncio
import contextlib
import itertools
import logging
import random
import ssl
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import websockets
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidURI

from . import _json
from .errors import OgmiosConnectionError, OgmiosError, OgmiosTimeoutError

logger = logging.getLogger("pyogmios")


@dataclass(frozen=True, slots=True)
class Reconnect:
    """How to retry connecting, on the first connect and after the connection drops.

    The delay before retry ``n`` is ``initial_delay * factor ** n``, capped at ``max_delay``, with up
    to ``jitter`` of it added or removed at random. Pass ``reconnect=None`` to the client to never
    retry.
    """

    attempts: int = 5
    """Connection attempts before giving up, including the first."""
    initial_delay: float = 0.5
    max_delay: float = 10.0
    factor: float = 2.0
    jitter: float = 0.1

    def delays(self) -> list[float]:
        """The delays to wait before each retry."""
        delays = []
        for attempt in range(self.attempts - 1):
            delay = min(self.max_delay, self.initial_delay * self.factor**attempt)
            delays.append(max(0.0, delay * (1 + random.uniform(-self.jitter, self.jitter))))
        return delays


#: The default policy: five attempts, backing off from 0.5s to 10s.
DEFAULT_RECONNECT = Reconnect()


class Transport(Protocol):
    """Sends one JSON-RPC request and returns the server's response object."""

    #: Whether the connection keeps state between requests (chain sync, mempool, acquired ledger state).
    stateful: bool

    async def connect(self) -> None: ...

    async def request(self, message: dict[str, Any], timeout: float | None) -> dict[str, Any]: ...

    async def close(self) -> None: ...


class WebSocketTransport:
    """One WebSocket connection, with any number of requests in flight.

    A reader task matches each response to its request by ``id``. When the connection drops, every
    request in flight fails with :class:`OgmiosConnectionError`; the next request reconnects, using the
    ``reconnect`` policy. :attr:`generation` goes up on every new connection, so callers can tell that
    connection state (chain sync position, acquired ledger state or mempool) was lost.
    """

    stateful = True

    def __init__(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        open_timeout: float | None = 10.0,
        ping_interval: float | None = 20.0,
        ping_timeout: float | None = 20.0,
        ssl_context: ssl.SSLContext | None = None,
        reconnect: Reconnect | None = DEFAULT_RECONNECT,
        happy_eyeballs_delay: float | None = 0.25,
    ) -> None:
        self.url = url
        self.headers = dict(headers or {})
        self.open_timeout = open_timeout
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.ssl_context = ssl_context
        self.reconnect = reconnect
        self.happy_eyeballs_delay = happy_eyeballs_delay
        #: How many connections have been opened; increases on every reconnect.
        self.generation = 0
        self._ws: ClientConnection | None = None
        self._reader: asyncio.Task[None] | None = None
        self._pending: dict[Any, asyncio.Future[dict[str, Any]]] = {}
        self._connect_lock = asyncio.Lock()
        self._closing = False

    @property
    def connected(self) -> bool:
        return self._ws is not None and self._reader is not None and not self._reader.done()

    async def connect(self) -> None:
        async with self._connect_lock:
            if self.connected:
                return
            self._closing = False
            delays = self.reconnect.delays() if self.reconnect else []
            for attempt in itertools.count():
                try:
                    ws = await self._open()
                    break
                except (OSError, InvalidHandshake, TimeoutError) as error:
                    if attempt >= len(delays):
                        raise OgmiosConnectionError(
                            f"cannot connect to Ogmios at {self.url}: {error}"
                        ) from error
                    logger.warning(
                        "Ogmios connection failed (%s); retrying in %.1fs", error, delays[attempt]
                    )
                    await asyncio.sleep(delays[attempt])
            self._ws = ws
            self.generation += 1
            self._reader = asyncio.create_task(self._read(ws), name="pyogmios-reader")
            logger.debug("connected to %s (generation %d)", self.url, self.generation)

    async def _open(self) -> ClientConnection:
        extra: dict[str, Any] = {}
        if self.happy_eyeballs_delay is not None:
            # Passed through to loop.create_connection: try IPv6 and IPv4 addresses in parallel
            # (RFC 8305), so a host whose IPv6 route hangs does not stall the connection.
            extra["happy_eyeballs_delay"] = self.happy_eyeballs_delay
        if self.ssl_context is not None:
            extra["ssl"] = self.ssl_context
        try:
            return await websockets.connect(
                self.url,
                additional_headers=self.headers or None,
                open_timeout=self.open_timeout,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout,
                max_size=None,  # some query results are tens of megabytes
                **extra,
            )
        except InvalidURI as error:
            raise OgmiosError(f"invalid Ogmios URL {self.url!r}: {error}") from error

    async def _read(self, ws: ClientConnection) -> None:
        reason = ""
        try:
            async for raw in ws:
                self._dispatch(raw)
        except ConnectionClosed as closed:
            reason = f": {closed}"
        finally:
            if not self._closing:
                logger.warning("Ogmios connection to %s closed%s", self.url, reason)
            self._fail_pending(OgmiosConnectionError(f"connection to Ogmios closed{reason}"))

    def _dispatch(self, raw: str | bytes) -> None:
        try:
            response = _json.loads(raw)
        except ValueError:
            logger.error("Ogmios sent a message that is not JSON: %.200r", raw)
            return
        request_id = response.get("id") if isinstance(response, dict) else None
        future = self._pending.pop(request_id, None) if request_id is not None else None
        if future is None:
            if request_id is None and isinstance(response, dict) and "error" in response:
                # The server could not read a request's id; it cannot be matched, so fail them all.
                self._fail_pending(OgmiosError(f"Ogmios rejected a request: {response['error']}"))
            else:
                logger.debug("dropping a response nobody is waiting for (id %r)", request_id)
            return
        if not future.done():
            future.set_result(response)

    def _fail_pending(self, error: Exception) -> None:
        pending, self._pending = self._pending, {}
        for future in pending.values():
            if not future.done():
                future.set_exception(error)

    async def request(self, message: dict[str, Any], timeout: float | None) -> dict[str, Any]:
        if not self.connected:
            if self.generation and self.reconnect is None:
                raise OgmiosConnectionError(
                    "the connection to Ogmios was lost and reconnect is off"
                )
            await self.connect()
        assert self._ws is not None
        request_id = message["id"]
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        try:
            await self._ws.send(_json.dumps(message))
            return await asyncio.wait_for(future, timeout)
        except ConnectionClosed as error:
            raise OgmiosConnectionError(f"connection to Ogmios closed: {error}") from error
        except TimeoutError as error:
            raise OgmiosTimeoutError(
                f"Ogmios did not answer {message['method']} within {timeout}s"
            ) from error
        finally:
            self._pending.pop(request_id, None)

    async def close(self) -> None:
        self._closing = True
        if self._ws is not None:
            await self._ws.close()
        if self._reader is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader
        self._ws = None
        self._reader = None


class HttpTransport:
    """JSON-RPC over HTTP POST: one request per call, no connection state.

    Good for one-off queries and submitting transactions. Stateful methods are refused by the client.
    """

    stateful = False

    def __init__(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        open_timeout: float | None = 10.0,
        ssl_context: ssl.SSLContext | None = None,
        reconnect: Reconnect | None = DEFAULT_RECONNECT,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.url = url
        self.reconnect = reconnect
        #: The httpx client; pass ``client`` to configure it yourself (proxies, limits, mocks).
        self._client = client or httpx.AsyncClient(
            headers={"content-type": "application/json", **dict(headers or {})},
            timeout=httpx.Timeout(None, connect=open_timeout),
            verify=ssl_context if ssl_context is not None else True,
        )

    async def connect(self) -> None:
        """Nothing to open: HTTP connections are made per request and pooled."""

    async def request(self, message: dict[str, Any], timeout: float | None) -> dict[str, Any]:
        delays = self.reconnect.delays() if self.reconnect else []
        for attempt in itertools.count():
            try:
                response = await self._client.post(
                    self.url,
                    content=_json.dumps(message),
                    timeout=httpx.Timeout(timeout, connect=None),
                )
                break
            except httpx.TimeoutException as error:
                raise OgmiosTimeoutError(
                    f"Ogmios did not answer {message['method']} within {timeout}s"
                ) from error
            except httpx.TransportError as error:
                # Only connection failures are retried: the request did not reach the server.
                if not isinstance(error, httpx.ConnectError) or attempt >= len(delays):
                    raise OgmiosConnectionError(
                        f"cannot reach Ogmios at {self.url}: {error}"
                    ) from error
                await asyncio.sleep(delays[attempt])
        try:
            body = _json.loads(response.content)
        except ValueError:
            raise OgmiosError(
                f"Ogmios answered HTTP {response.status_code}: {response.text[:200]}"
            ) from None
        if not isinstance(body, dict):
            raise OgmiosError(f"Ogmios answered HTTP {response.status_code} with {body!r:.200}")
        return body

    async def close(self) -> None:
        await self._client.aclose()
