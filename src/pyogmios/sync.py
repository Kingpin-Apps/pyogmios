"""The synchronous Ogmios client.

It runs an :class:`~pyogmios.AsyncClient` on a private event loop in a background thread, so both
clients share one implementation and behave the same. It is safe to use from several threads.
"""

from __future__ import annotations

import asyncio
import ssl
import threading
from collections.abc import Awaitable, Coroutine, Iterator, Mapping, Sequence
from types import TracebackType
from typing import Any, Generic, Literal, Self, TypeVar

from ._generated import models
from ._generated.api import LedgerStateQueries, NetworkQueries
from ._transport import DEFAULT_RECONNECT, Reconnect, Transport
from .client import DEFAULT_URL, AsyncClient, VersionCheck
from .health import Health
from .protocols import ChainSync, LedgerStateAt, MempoolMonitor, MempoolSnapshot, PointLike

T = TypeVar("T")


async def _await(awaitable: Awaitable[T]) -> T:
    return await awaitable


class _Portal:
    """An event loop running in a daemon thread, to run coroutines from synchronous code."""

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, name="pyogmios-loop", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coroutine: Awaitable[T]) -> T:
        if threading.current_thread() is self._thread:
            if isinstance(coroutine, Coroutine):
                coroutine.close()  # avoid a "never awaited" warning
            raise RuntimeError("pyogmios.Client cannot be used from inside its own event loop")
        return asyncio.run_coroutine_threadsafe(_await(coroutine), self.loop).result()

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
        #: The ledger state queries: ``client.ledger_state.epoch()``.
        self.ledger_state = LedgerStateQueries(self._client.ledger_state, self._portal.run)
        #: The network queries: ``client.network.tip()``.
        self.network = NetworkQueries(self._client.network, self._portal.run)

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

    def submit_transaction(self, transaction: str | bytes) -> models.SubmitTransactionResult:
        """Submit a signed transaction; see :meth:`AsyncClient.submit_transaction`."""
        return self._portal.run(self._client.submit_transaction(transaction))

    def evaluate_transaction(
        self,
        transaction: str | bytes,
        *,
        additional_utxo: models.Utxo | Sequence[Any] | None = None,
    ) -> models.EvaluateTransactionResult:
        """Evaluate a transaction's scripts; see :meth:`AsyncClient.evaluate_transaction`."""
        return self._portal.run(
            self._client.evaluate_transaction(transaction, additional_utxo=additional_utxo)
        )

    def chain_sync(
        self,
        points: Sequence[PointLike] = ("origin",),
        *,
        pipeline: int = 50,
        resume: bool = True,
        raw: bool = False,
    ) -> SyncChainSync:
        """Follow the chain: ``with client.chain_sync(points) as sync: for event in sync: ...``.

        See :meth:`AsyncClient.chain_sync`.
        """
        sync = self._client.chain_sync(points, pipeline=pipeline, resume=resume, raw=raw)
        return SyncChainSync(sync, self._portal)

    def ledger_state_at(self, point: PointLike) -> SyncLedgerStateAt:
        """Query the ledger as it was at ``point``: ``with client.ledger_state_at(point) as ledger``."""
        return SyncLedgerStateAt(self._client.ledger_state_at(point), self._portal)

    def mempool_snapshot(self, *, full: bool = False) -> SyncMempoolSnapshot:
        """A snapshot of the mempool; see :meth:`AsyncClient.mempool_snapshot`."""
        return SyncMempoolSnapshot(self._client.mempool_snapshot(full=full), self._portal)

    def mempool(self, *, full: bool = False) -> SyncStream[MempoolMonitor]:
        """Every transaction entering the mempool: ``with client.mempool() as txs: for tx in txs``."""
        return SyncStream(self._client.mempool(full=full), self._portal)


S = TypeVar("S", ChainSync, MempoolMonitor, MempoolSnapshot)


class SyncStream(Generic[S]):
    """A synchronous ``with`` / ``for`` wrapper around an asynchronous protocol stream."""

    def __init__(self, stream: S, portal: _Portal) -> None:
        self.stream = stream
        self._portal = portal

    def __enter__(self) -> Self:
        self._portal.run(self.stream.__aenter__())
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._portal.run(self.stream.__aexit__(exc_type, exc, traceback))

    def __iter__(self) -> Iterator[Any]:
        return self

    def __next__(self) -> Any:
        try:
            return self._portal.run(self.stream.__anext__())
        except StopAsyncIteration:
            raise StopIteration from None


class SyncChainSync(SyncStream[ChainSync]):
    """A synchronous chain sync; see :class:`~pyogmios.protocols.ChainSync`."""

    @property
    def intersection(self) -> models.PointOrOrigin | None:
        """The intersection found: a point, or ``"origin"``."""
        return self.stream.intersection

    @property
    def tip(self) -> models.TipOrOrigin | None:
        """The server's tip when the intersection was found."""
        return self.stream.tip


class SyncMempoolSnapshot(SyncStream[MempoolSnapshot]):
    """A synchronous mempool snapshot; see :class:`~pyogmios.protocols.MempoolSnapshot`."""

    @property
    def slot(self) -> int | None:
        return self.stream.slot

    def acquire(self) -> int:
        return self._portal.run(self.stream.acquire())

    def size(self) -> models.MempoolSizeAndCapacity:
        return self._portal.run(self.stream.size())

    def has(self, transaction_id: str) -> bool:
        return self._portal.run(self.stream.has(transaction_id))

    def next(self) -> Any:
        return self._portal.run(self.stream.next())


class SyncLedgerStateAt:
    """``with client.ledger_state_at(point) as ledger``: every ledger query, at that point."""

    def __init__(self, state: LedgerStateAt, portal: _Portal) -> None:
        self.state = state
        self._portal = portal

    def __enter__(self) -> LedgerStateQueries:
        queries = self._portal.run(self.state.__aenter__())
        return LedgerStateQueries(queries, self._portal.run)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._portal.run(self.state.__aexit__(exc_type, exc, traceback))
