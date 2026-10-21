"""Edge cases and error paths: misuse, failures while opening, and the sync client's every wrapper."""

from __future__ import annotations

import asyncio
import threading
from typing import Any

import pytest

import pyogmios
from pyogmios import errors
from pyogmios._transport import Reconnect
from pyogmios.protocols import ChainSync, MempoolSnapshot
from pyogmios.types import MempoolSizeAndCapacity, Point

from .fake_server import FakeOgmios, recorded, running

FAST_RECONNECT = Reconnect(attempts=2, initial_delay=0.01, max_delay=0.02)
BACKWARD = recorded("nextBlock", "backward")


async def read(stream: Any, count: int) -> None:
    for _ in range(count):
        await anext(stream)


def client(fake: FakeOgmios) -> pyogmios.AsyncClient:
    return pyogmios.AsyncClient(fake.ws_url, reconnect=FAST_RECONNECT)


# Protocols ----------------------------------------------------------------------------------------


async def test_chain_sync_rejects_an_empty_pipeline() -> None:
    with pytest.raises(ValueError, match="pipeline"):
        pyogmios.AsyncClient("ws://x").chain_sync(pipeline=0)


async def test_chain_sync_must_be_entered_before_iterating() -> None:
    sync = pyogmios.AsyncClient("ws://x").chain_sync()
    with pytest.raises(RuntimeError, match="async with"):
        await anext(sync)


async def test_chain_sync_accepts_point_models() -> None:
    point = Point(slot=1, id="ab" * 32)
    async with running() as fake, client(fake) as ogmios, ogmios.chain_sync([point, "origin"]):
        pass
    sent = next(r["params"] for r in fake.received if r["method"] == "findIntersection")
    assert sent == {"points": [{"slot": 1, "id": "ab" * 32}, "origin"]}


async def test_chain_sync_gives_up_when_it_cannot_reconnect() -> None:
    fake = FakeOgmios(sequences={"nextBlock": [BACKWARD, recorded("nextBlock", "recent-01")]})
    async with running(fake), client(fake) as ogmios, ogmios.chain_sync(pipeline=1) as sync:
        await anext(sync)
        assert fake.server is not None
        fake.server.close()  # the server goes away for good
        await fake.server.wait_closed()
        with pytest.raises(pyogmios.OgmiosConnectionError):
            await asyncio.wait_for(read(sync, 5), timeout=30)  # events already received come first


async def test_ledger_state_at_closes_its_connection_when_acquiring_fails() -> None:
    fake = FakeOgmios(
        responses={"acquireLedgerState": recorded("acquireLedgerState", "point-not-on-chain")}
    )
    async with running(fake), client(fake) as ogmios:
        state = ogmios.ledger_state_at("origin")
        with pytest.raises(errors.AcquireLedgerStateError):
            await state.__aenter__()
        assert state._client is not None
        assert not state._client._connected


async def test_mempool_snapshot_must_be_entered_first() -> None:
    snapshot = MempoolSnapshot(pyogmios.AsyncClient("ws://x"))
    with pytest.raises(RuntimeError, match="mempool_snapshot"):
        await snapshot.size()


async def test_mempool_snapshot_closes_its_connection_when_acquiring_fails() -> None:
    fake = FakeOgmios(responses={"acquireMempool": recorded("sizeOfMempool", "not-acquired")})
    async with running(fake), client(fake) as ogmios:
        snapshot = ogmios.mempool_snapshot()
        with pytest.raises(errors.MempoolError):
            await snapshot.__aenter__()
        assert snapshot._client is not None
        assert not snapshot._client._connected


async def test_epoch_boundary_blocks_are_not_remembered_as_points() -> None:
    """Epoch boundary blocks have no slot, so they cannot be intersection points after a reconnect."""
    sync = ChainSync(pyogmios.AsyncClient("ws://x"), ["origin"], raw=True)
    sync._remember({"direction": "forward", "block": {"type": "ebb", "id": "aa" * 32, "height": 0}})
    sync._remember(
        {
            "direction": "forward",
            "block": {"type": "praos", "id": "bb" * 32, "slot": 5, "height": 1},
        }
    )
    sync._remember({"direction": "backward", "point": "origin"})
    assert list(sync._recent) == []


# The sync client: every wrapper -------------------------------------------------------------------


@pytest.fixture
def sync_fake() -> Any:
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    fake = FakeOgmios()
    context = running(fake)
    asyncio.run_coroutine_threadsafe(context.__aenter__(), loop).result()
    yield fake
    asyncio.run_coroutine_threadsafe(context.__aexit__(None, None, None), loop).result()
    loop.call_soon_threadsafe(loop.stop)
    thread.join()
    loop.close()


def test_sync_client_wrappers(sync_fake: FakeOgmios) -> None:
    sync_fake.responses["submitTransaction"] = {
        "jsonrpc": "2.0",
        "method": "submitTransaction",
        "result": {"transaction": {"id": "cd" * 32}},
    }
    sync_fake.sequences["nextTransaction"] = [
        {
            "jsonrpc": "2.0",
            "method": "nextTransaction",
            "result": {"transaction": {"id": "aa" * 32}},
        },
        {"jsonrpc": "2.0", "method": "nextTransaction", "result": {"transaction": None}},
        {
            "jsonrpc": "2.0",
            "method": "nextTransaction",
            "result": {"transaction": {"id": "bb" * 32}},
        },
    ]
    with pyogmios.Client(sync_fake.ws_url, reconnect=FAST_RECONNECT) as ogmios:
        assert ogmios.url == sync_fake.ws_url
        assert ogmios.generation == 1
        assert ogmios.health().network == "preview"
        assert ogmios.request("queryNetwork/tip") == recorded("queryNetwork/tip")["result"]
        assert ogmios.submit_transaction("84a0").transaction.id == "cd" * 32
        assert (
            ogmios.evaluate_transaction(b"\x84\xa0", additional_utxo=[])
            == recorded("evaluateTransaction", "no-scripts")["result"]
        )
        with ogmios.mempool_snapshot() as snapshot:
            assert snapshot.has("aa" * 32) in (True, False)
            assert snapshot.next() == "aa" * 32
            assert snapshot.next() is None
            assert isinstance(snapshot.acquire(), int)
            assert isinstance(snapshot.size(), MempoolSizeAndCapacity)
        with ogmios.mempool() as transactions:
            assert next(transactions) == "bb" * 32
    ogmios.close()  # closing twice is harmless


def test_sync_client_cannot_be_used_from_its_own_event_loop(sync_fake: FakeOgmios) -> None:
    with pyogmios.Client(sync_fake.ws_url, reconnect=FAST_RECONNECT) as ogmios:

        async def from_inside() -> None:
            with pytest.raises(RuntimeError, match="its own event loop"):
                ogmios.call("queryLedgerState/epoch")

        asyncio.run_coroutine_threadsafe(from_inside(), ogmios._portal.loop).result()


def test_sync_iteration_ends_with_the_stream(sync_fake: FakeOgmios) -> None:
    sync_fake.sequences["nextTransaction"] = [
        {"jsonrpc": "2.0", "method": "nextTransaction", "result": {"transaction": None}},
    ]
    with (
        pyogmios.Client(sync_fake.ws_url, reconnect=FAST_RECONNECT) as ogmios,
        ogmios.mempool_snapshot() as snapshot,
    ):
        assert list(snapshot) == []
