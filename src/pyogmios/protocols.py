"""The stateful Ogmios protocols: chain sync, an acquired ledger state and the mempool.

Ogmios keeps their state on the connection: the chain sync cursor, an acquired ledger state (which
every ledger query on that connection then reads) and an acquired mempool snapshot. So each one here
opens its own connection, separate from the client's, and other requests on the client are never
affected by it.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections import deque
from collections.abc import Sequence
from types import TracebackType
from typing import TYPE_CHECKING, Any, Literal, Self

from ._generated import models
from ._generated.api import AsyncLedgerStateQueries
from .errors import OgmiosConnectionError, OgmiosError

if TYPE_CHECKING:
    from .client import AsyncClient

logger = logging.getLogger("pyogmios")

#: A point on the chain: ``"origin"``, a :class:`~pyogmios.types.Point` or ``{"slot": ..., "id": ...}``.
PointLike = models.Point | Literal["origin"] | dict[str, Any] | str


def _point(point: PointLike) -> Any:
    if isinstance(point, models.Point):
        return point.model_dump(mode="json", by_alias=True)
    return point


class ChainSync:
    """Follow the chain from an intersection: yields a ``RollForward`` or ``RollBackward`` per step.

    ::

        async with client.chain_sync(["origin"]) as sync:
            async for event in sync:
                if isinstance(event, RollForward):
                    print(event.block.id)
                else:
                    print("rolled back to", event.point)

    The first event after the intersection is always a roll backward to it. Up to ``pipeline``
    ``nextBlock`` requests are kept in flight, which makes catching up much faster. At the tip, Ogmios
    holds each request until a new block arrives, so there is no timeout.

    If the connection drops and ``resume`` is on, it reconnects and finds an intersection again,
    starting from the most recent points it has seen, then carries on: you see a roll backward to that
    point, as after any intersection.
    """

    def __init__(
        self,
        client: AsyncClient,
        points: Sequence[PointLike],
        *,
        pipeline: int = 50,
        resume: bool = True,
        raw: bool = False,
        remember: int = 64,
    ) -> None:
        if pipeline < 1:
            raise ValueError("pipeline must be at least 1")
        self._parent = client
        self._points = [_point(point) for point in points]
        self.pipeline = pipeline
        self.resume = resume
        self.raw = raw
        self._recent: deque[dict[str, Any]] = deque(maxlen=remember)
        self._client: AsyncClient | None = None
        self._in_flight: deque[asyncio.Future[Any]] = deque()
        #: The intersection found: a point, or ``"origin"``.
        self.intersection: models.PointOrOrigin | None = None
        #: The server's tip when the intersection was found.
        self.tip: models.TipOrOrigin | None = None

    async def __aenter__(self) -> Self:
        await self._intersect(self._points)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        self._cancel_in_flight()
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def _intersect(self, points: list[Any]) -> None:
        await self.close()
        self._client = self._parent._dedicated()
        await self._client.connect()
        found = await self._client.call("findIntersection", {"points": points})
        self.intersection, self.tip = found.intersection, found.tip

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> Any:
        if self._client is None:
            raise RuntimeError("use `async with client.chain_sync(...)` before iterating")
        while True:
            self._fill()
            future = self._in_flight.popleft()
            self._fill()  # keep the pipeline full while this event is being handled
            try:
                event = await future
            except OgmiosConnectionError:
                if not self.resume:
                    raise
                await self._resume()
                continue
            self._remember(event)
            return event

    def _fill(self) -> None:
        assert self._client is not None
        while len(self._in_flight) < self.pipeline:
            request = (
                self._client.request("nextBlock", timeout=None)
                if self.raw
                else self._client.call("nextBlock", timeout=None)
            )
            self._in_flight.append(asyncio.ensure_future(request))

    def _cancel_in_flight(self) -> None:
        while self._in_flight:
            future = self._in_flight.popleft()
            if future.done():
                # Already failed (the connection dropped): retrieve the error, or asyncio logs
                # "Task exception was never retrieved" in the user's program.
                if not future.cancelled():
                    future.exception()
            else:
                future.cancel()

    def _remember(self, event: Any) -> None:
        """Keep recent points, to find an intersection again after a reconnect."""
        data = event if self.raw else event.model_dump(mode="json", by_alias=True)
        if data["direction"] == "forward":
            block = data["block"]
            if "slot" in block:  # epoch boundary blocks have no slot, so they cannot be points
                self._recent.append({"slot": block["slot"], "id": block["id"]})
        else:
            point = data["point"]
            while self._recent and (point == "origin" or self._recent[-1]["slot"] > point["slot"]):
                self._recent.pop()

    async def _resume(self) -> None:
        points = [*reversed(self._recent), *self._points]
        logger.warning("chain sync connection lost; finding an intersection again")
        for attempt in range(1, 6):
            try:
                await self._intersect(points)
                return
            except OgmiosConnectionError:
                if attempt == 5:
                    raise
                await asyncio.sleep(min(10.0, 0.5 * 2**attempt))


class LedgerStateAt:
    """Query the ledger as it was at a point: ``async with client.ledger_state_at(point) as ledger``.

    ``ledger`` has every ledger state query (``await ledger.epoch()``...), all answered for the
    acquired point. Ogmios only keeps recent ledger states (about the last 2160 blocks), and the state
    expires once it is too old: queries then raise
    :class:`~pyogmios.errors.AcquiredExpiredError`.
    """

    def __init__(self, client: AsyncClient, point: PointLike) -> None:
        self._parent = client
        self._point = _point(point)
        self._client: AsyncClient | None = None
        #: What Ogmios acquired: ``{"acquired": "ledgerState", "point": ...}``.
        self.acquired: models.AcquireLedgerStateResult | None = None

    async def __aenter__(self) -> AsyncLedgerStateQueries:
        self._client = self._parent._dedicated()
        try:
            await self._client.connect()
            self.acquired = await self._client.call("acquireLedgerState", {"point": self._point})
        except BaseException:
            await self._client.close()
            raise
        return AsyncLedgerStateQueries(self._client)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._client is not None:
            with contextlib.suppress(OgmiosError):
                await self._client.call("releaseLedgerState")
            await self._client.close()
            self._client = None


class MempoolSnapshot:
    """A snapshot of the node's mempool: ``async with client.mempool_snapshot() as snapshot``.

    ::

        async with client.mempool_snapshot() as snapshot:
            print(await snapshot.size())
            async for transaction_id in snapshot:
                ...
    """

    def __init__(self, client: AsyncClient, *, full: bool = False) -> None:
        self._parent = client
        self.full = full
        self._client: AsyncClient | None = None
        #: The slot at which the snapshot was taken.
        self.slot: int | None = None

    async def __aenter__(self) -> Self:
        self._client = self._parent._dedicated()
        try:
            await self._client.connect()
            await self.acquire()
        except BaseException:
            await self._client.close()
            raise
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._client is not None:
            with contextlib.suppress(OgmiosError):
                await self._client.call("releaseMempool")
            await self._client.close()
            self._client = None

    @property
    def _connection(self) -> AsyncClient:
        if self._client is None:
            raise RuntimeError("use `async with client.mempool_snapshot()` first")
        return self._client

    async def acquire(self) -> int:
        """Take a new snapshot. After the first, this waits until the mempool has changed."""
        acquired = await self._connection.call("acquireMempool", timeout=None)
        self.slot = acquired.slot
        return acquired.slot

    async def size(self) -> models.MempoolSizeAndCapacity:
        """The snapshot's size, capacity and number of transactions."""
        return await self._connection.call("sizeOfMempool")

    async def has(self, transaction_id: str) -> bool:
        """Whether the snapshot contains the transaction."""
        return await self._connection.call("hasTransaction", {"id": transaction_id})

    async def next(self) -> Any:
        """The next transaction in the snapshot (its id, or the transaction when ``full``), or ``None``."""
        result = await self._connection.call(
            "nextTransaction", {"fields": "all"} if self.full else {}
        )
        transaction = result.transaction
        if transaction is None or self.full:
            return transaction
        return transaction.id

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> Any:
        transaction = await self.next()
        if transaction is None:
            raise StopAsyncIteration
        return transaction


class MempoolMonitor:
    """Every transaction that enters the mempool, as it arrives: ``async for tx in client.mempool()``.

    Each snapshot's new transactions are yielded (ids, or full transactions with ``full=True``), then
    it waits for the mempool to change. A transaction is yielded once, even if it stays in the mempool
    across snapshots.
    """

    def __init__(self, client: AsyncClient, *, full: bool = False) -> None:
        self._snapshot = MempoolSnapshot(client, full=full)
        self._seen: set[str] = set()
        self._current: set[str] = set()

    async def __aenter__(self) -> Self:
        await self._snapshot.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._snapshot.__aexit__(exc_type, exc, traceback)

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> Any:
        while True:
            transaction = await self._snapshot.next()
            if transaction is None:
                # Done with this snapshot: forget transactions that left the mempool, and wait for a change.
                self._seen, self._current = self._current, set()
                await self._snapshot.acquire()
                continue
            transaction_id = transaction if isinstance(transaction, str) else transaction.id
            self._current.add(transaction_id)
            if transaction_id not in self._seen:
                return transaction
