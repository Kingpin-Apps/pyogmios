"""The typed query methods, transactions, chain sync, acquired ledger states and the mempool."""

from __future__ import annotations

import asyncio
import gc
import inspect
import re
import threading
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

import pyogmios
from pyogmios import errors
from pyogmios._generated.api import LedgerStateQueries, NetworkQueries
from pyogmios._generated.methods import METHODS
from pyogmios._transport import HttpTransport, Reconnect
from pyogmios.types import MempoolSizeAndCapacity, Point, RollBackward, RollForward

from .fake_server import FakeOgmios, recorded, running

FAST_RECONNECT = Reconnect(attempts=3, initial_delay=0.01, max_delay=0.02)
ADDRESS = recorded("queryLedgerState/utxo", "by-address")["result"][0]["address"]
REFERENCE = {"transaction": {"id": "ab" * 32}, "index": 1}


def client(fake: FakeOgmios, **options: Any) -> pyogmios.AsyncClient:
    return pyogmios.AsyncClient(fake.ws_url, reconnect=FAST_RECONNECT, **options)


def sent(fake: FakeOgmios, method: str) -> list[Any]:
    return [request.get("params") for request in fake.received if request["method"] == method]


async def drain(stream: Any, count: int) -> None:
    for _ in range(count):
        await anext(stream)


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name.split("/", 1)[1]).lower()


# Typed queries ----------------------------------------------------------------------------------

QUERIES = sorted(name for name in METHODS if name.startswith("query"))


@pytest.mark.parametrize("method", QUERIES)
def test_every_query_has_a_typed_method_on_both_clients(method: str) -> None:
    namespace = "ledger_state" if method.startswith("queryLedgerState/") else "network"
    async_method = getattr(
        pyogmios.AsyncClient("ws://x").__getattribute__(namespace), snake(method)
    )
    assert inspect.iscoroutinefunction(async_method)
    assert async_method.__doc__
    sync_class = {"ledger_state": LedgerStateQueries, "network": NetworkQueries}
    assert callable(getattr(sync_class[namespace], snake(method)))


async def test_query_keywords_become_wire_params() -> None:
    async with running() as fake, client(fake) as ogmios:
        await ogmios.ledger_state.utxo(addresses=[ADDRESS])
        await ogmios.ledger_state.utxo(output_references=[REFERENCE])
        await ogmios.ledger_state.utxo()
        await ogmios.ledger_state.stake_pools(include_stake=True)
        await ogmios.ledger_state.projected_rewards()
        await ogmios.network.genesis_configuration(era="conway")
    assert sent(fake, "queryLedgerState/utxo") == [
        {"addresses": [ADDRESS]},
        {"outputReferences": [REFERENCE]},
        None,
    ]
    assert sent(fake, "queryLedgerState/stakePools") == [{"includeStake": True}]
    assert sent(fake, "queryLedgerState/projectedRewards") == [
        {}
    ]  # params are required, even when empty
    assert sent(fake, "queryNetwork/genesisConfiguration") == [{"era": "conway"}]


async def test_a_filtered_query_is_never_sent_as_a_query_for_everything() -> None:
    """Regression: a lenient empty params shape (WholeUtxo) once swallowed {"addresses": [...]}."""
    async with running() as fake, client(fake) as ogmios:
        await ogmios.call("queryLedgerState/utxo", {"addresses": [ADDRESS]})
        with pytest.raises(ValidationError):
            await ogmios.call(
                "queryLedgerState/utxo", {"adresses": [ADDRESS]}
            )  # typo: rejected, not dropped
    assert sent(fake, "queryLedgerState/utxo") == [{"addresses": [ADDRESS]}]


async def test_query_results_are_typed() -> None:
    async with running() as fake, client(fake) as ogmios:
        assert await ogmios.ledger_state.epoch() == recorded("queryLedgerState/epoch")["result"]
        tip = await ogmios.network.tip()
        assert isinstance(tip, Point)
        assert tip.slot == recorded("queryNetwork/tip")["result"]["slot"]


# Transactions -----------------------------------------------------------------------------------


async def test_submit_and_evaluate_send_hex_cbor() -> None:
    fake = FakeOgmios(
        responses={
            "submitTransaction": {
                "jsonrpc": "2.0",
                "method": "submitTransaction",
                "result": {"transaction": {"id": "cd" * 32}},
            }
        }
    )
    async with running(fake), client(fake) as ogmios:
        submitted = await ogmios.submit_transaction(bytes.fromhex("84A0"))
        await ogmios.evaluate_transaction("84A0", additional_utxo=[])
    assert submitted.transaction.id == "cd" * 32
    assert sent(fake, "submitTransaction") == [{"transaction": {"cbor": "84a0"}}]
    assert sent(fake, "evaluateTransaction") == [
        {"transaction": {"cbor": "84a0"}, "additionalUtxo": []}
    ]


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("ledger-rejection", errors.SubmitTransactionError),
        ("unknown-input", errors.UnexpectedMempoolError),
        ("deserialisation", errors.TransactionDeserialisationError),
    ],
)
async def test_submission_failures_raise_their_own_class(
    case: str, expected: type[errors.ResponseError]
) -> None:
    response = recorded("submitTransaction", case)
    async with (
        running(FakeOgmios(responses={"submitTransaction": response})) as fake,
        client(fake) as ogmios,
    ):
        with pytest.raises(expected) as raised:
            await ogmios.submit_transaction("84a0")
    assert raised.value.code == response["error"]["code"]
    specific = errors.error_class(response["error"]["code"], "submitTransaction")
    assert type(raised.value) is specific
    if response["error"]["code"] >= 0:
        assert raised.value.details is not None


# Chain sync -------------------------------------------------------------------------------------


def forward(height: int) -> dict[str, Any]:
    """A roll forward to a made-up block at ``height``, from a real recorded block."""
    response = recorded("nextBlock", "recent-01")
    block = {
        **response["result"]["block"],
        "height": height,
        "slot": 1000 + height,
        "id": f"{height:064x}",
    }
    return {**response, "result": {**response["result"], "block": block}}


BACKWARD = recorded("nextBlock", "backward")


async def test_chain_sync_yields_events_in_order_on_its_own_connection() -> None:
    fake = FakeOgmios(sequences={"nextBlock": [BACKWARD, *(forward(h) for h in range(1, 21))]})
    async with (
        running(fake),
        client(fake) as ogmios,
        ogmios.chain_sync(["origin"], pipeline=5) as sync,
    ):
        assert sync.intersection is not None
        events = [await anext(sync) for _ in range(21)]
    assert isinstance(events[0], RollBackward)
    assert [event.block.height for event in events[1:]] == list(range(1, 21))
    assert all(isinstance(event, RollForward) for event in events[1:])
    chain_sync_connections = {
        n
        for request, n in zip(fake.received, fake.received_on, strict=True)
        if request["method"] in ("findIntersection", "nextBlock")
    }
    assert chain_sync_connections == {2}  # the client's own connection is 1


async def test_chain_sync_pipelines_requests() -> None:
    fake = FakeOgmios(sequences={"nextBlock": [BACKWARD, *(forward(h) for h in range(1, 50))]})
    async with running(fake), client(fake) as ogmios, ogmios.chain_sync(pipeline=10) as sync:
        await anext(sync)
        await asyncio.sleep(0.05)
        assert len(sent(fake, "nextBlock")) == 11  # the one answered, and ten more kept in flight


async def test_chain_sync_resumes_from_the_last_block_after_a_dropped_connection() -> None:
    fake = FakeOgmios(sequences={"nextBlock": [BACKWARD, *(forward(h) for h in range(1, 40))]})
    async with running(fake), client(fake) as ogmios, ogmios.chain_sync(pipeline=1) as sync:
        events = [await anext(sync) for _ in range(6)]
        fake.drop_after = len(fake.received) + 1  # drop on the next request
        events += [await anext(sync) for _ in range(5)]
    heights = [event.block.height for event in events if isinstance(event, RollForward)]
    assert heights == list(range(1, 11))
    resumed_from = sent(fake, "findIntersection")[-1]["points"]
    assert resumed_from[0] == {"slot": 1005, "id": f"{5:064x}"}  # the last block seen, first
    assert resumed_from[-1] == "origin"  # then the original points


async def test_chain_sync_without_resume_raises() -> None:
    fake = FakeOgmios(sequences={"nextBlock": [BACKWARD, *(forward(h) for h in range(1, 40))]})
    async with (
        running(fake),
        client(fake) as ogmios,
        ogmios.chain_sync(pipeline=1, resume=False) as sync,
    ):
        await anext(sync)
        fake.drop_after = len(fake.received) + 1
        with pytest.raises(pyogmios.OgmiosConnectionError):
            await drain(sync, 5)


async def test_chain_sync_raw_yields_json() -> None:
    fake = FakeOgmios(sequences={"nextBlock": [BACKWARD, forward(1)]})
    async with running(fake), client(fake) as ogmios, ogmios.chain_sync(raw=True) as sync:
        assert (await anext(sync))["direction"] == "backward"
        assert (await anext(sync))["block"]["height"] == 1


async def test_intersection_not_found() -> None:
    fake = FakeOgmios(responses={"findIntersection": recorded("findIntersection", "not-found")})
    async with running(fake), client(fake) as ogmios:
        with pytest.raises(errors.IntersectionNotFoundError):
            async with ogmios.chain_sync([{"slot": 1, "id": "00" * 32}]):
                pass


# Ledger state at a point ------------------------------------------------------------------------


async def test_ledger_state_at_acquires_on_its_own_connection_and_releases() -> None:
    async with (
        running() as fake,
        client(fake) as ogmios,
        ogmios.ledger_state_at({"slot": 1, "id": "00" * 32}) as ledger,
    ):
        await ledger.epoch()
        await ogmios.ledger_state.epoch()  # the client's own connection is unaffected
    calls = list(zip([r["method"] for r in fake.received], fake.received_on, strict=True))
    assert ("acquireLedgerState", 2) in calls
    assert ("queryLedgerState/epoch", 2) in calls
    assert ("queryLedgerState/epoch", 1) in calls
    assert calls[-1] == ("releaseLedgerState", 2)


async def test_ledger_state_at_a_point_that_cannot_be_acquired() -> None:
    fake = FakeOgmios(
        responses={"acquireLedgerState": recorded("acquireLedgerState", "point-not-on-chain")}
    )
    async with running(fake), client(fake) as ogmios:
        with pytest.raises(errors.AcquireLedgerStateError):
            async with ogmios.ledger_state_at({"slot": 1, "id": "00" * 32}):
                pass


# Mempool ----------------------------------------------------------------------------------------


def next_transaction(transaction_id: str | None) -> dict[str, Any]:
    transaction = {"id": transaction_id} if transaction_id else None
    return {"jsonrpc": "2.0", "method": "nextTransaction", "result": {"transaction": transaction}}


async def test_mempool_snapshot() -> None:
    fake = FakeOgmios(
        sequences={"nextTransaction": [next_transaction("aa" * 32), next_transaction(None)]}
    )
    async with running(fake), client(fake) as ogmios, ogmios.mempool_snapshot() as snapshot:
        assert snapshot.slot is not None
        assert isinstance(await snapshot.size(), MempoolSizeAndCapacity)
        assert isinstance(await snapshot.has("aa" * 32), bool)
        assert [tx async for tx in snapshot] == ["aa" * 32]
    assert sent(fake, "nextTransaction") == [{}, {}]


async def test_mempool_monitor_yields_each_transaction_once() -> None:
    a, b, c = "aa" * 32, "bb" * 32, "cc" * 32
    fake = FakeOgmios(
        sequences={
            "nextTransaction": [
                next_transaction(a),
                next_transaction(b),
                next_transaction(None),
                next_transaction(b),
                next_transaction(c),
                next_transaction(None),
            ]
        }
    )
    async with running(fake), client(fake) as ogmios, ogmios.mempool() as transactions:
        seen = [await anext(transactions) for _ in range(3)]
    assert seen == [a, b, c]
    assert len(sent(fake, "acquireMempool")) == 2


async def test_full_transactions_are_requested() -> None:
    async with (
        running() as fake,
        client(fake) as ogmios,
        ogmios.mempool_snapshot(full=True) as snapshot,
    ):
        await snapshot.next()
    assert sent(fake, "nextTransaction") == [{"fields": "all"}]


# HTTP and the sync client -------------------------------------------------------------------------


async def test_stateful_protocols_need_websocket() -> None:
    transport = HttpTransport(
        "http://ogmios.test",
        client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(500))),
    )
    ogmios = pyogmios.AsyncClient("http://ogmios.test", transport=transport, check_version="off")
    for opening in (
        ogmios.chain_sync(),
        ogmios.ledger_state_at("origin"),
        ogmios.mempool_snapshot(),
        ogmios.mempool(),
    ):
        with pytest.raises(pyogmios.StatefulOverHttpError):
            async with opening:
                pass


@pytest.fixture
def sync_fake() -> Any:
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    fake = FakeOgmios(sequences={"nextBlock": [BACKWARD, *(forward(h) for h in range(1, 10))]})
    context = running(fake)
    asyncio.run_coroutine_threadsafe(context.__aenter__(), loop).result()
    yield fake
    asyncio.run_coroutine_threadsafe(context.__aexit__(None, None, None), loop).result()
    loop.call_soon_threadsafe(loop.stop)
    thread.join()
    loop.close()


def test_sync_client_protocols(sync_fake: FakeOgmios) -> None:
    with pyogmios.Client(sync_fake.ws_url, reconnect=FAST_RECONNECT) as ogmios:
        assert ogmios.ledger_state.epoch() == recorded("queryLedgerState/epoch")["result"]
        with ogmios.chain_sync(pipeline=3) as sync:
            assert sync.intersection is not None
            assert sync.tip is not None
            events = [next(sync) for _ in range(4)]
        assert [type(event).__name__ for event in events] == [
            "RollBackward",
            "RollForward",
            "RollForward",
            "RollForward",
        ]
        with ogmios.ledger_state_at("origin") as ledger:
            assert ledger.epoch() == recorded("queryLedgerState/epoch")["result"]
        with ogmios.mempool_snapshot() as snapshot:
            assert isinstance(snapshot.size(), MempoolSizeAndCapacity)
            assert snapshot.slot is not None


async def test_resuming_leaves_no_unretrieved_errors() -> None:
    """Requests in flight when the connection drops all fail; none may log "never retrieved"."""
    lost: list[str] = []
    asyncio.get_running_loop().set_exception_handler(
        lambda loop, context: lost.append(context["message"])
    )
    fake = FakeOgmios(sequences={"nextBlock": [BACKWARD, *(forward(h) for h in range(1, 60))]})
    async with running(fake), client(fake) as ogmios, ogmios.chain_sync(pipeline=5) as sync:
        await drain(sync, 3)
        fake.drop_after = len(fake.received) + 1
        await drain(sync, 3)
    del sync
    gc.collect()
    await asyncio.sleep(0)
    assert not [message for message in lost if "never retrieved" in message]
