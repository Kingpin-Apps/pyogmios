"""The client against a live Ogmios v7 server (``just test-integration``; OGMIOS_URL, OGMIOS_LIVE_BLOCKS).

Every query over WebSocket and HTTP, the sync client, chain sync and the mempool: each result must
parse, and dump back to exactly what the server sent.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import cbor2
import pytest
from pydantic import TypeAdapter

import pyogmios
from pyogmios._generated.methods import METHODS
from pyogmios.types import RollBackward

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.integration

WS_URL = os.environ.get("OGMIOS_URL", "ws://localhost:1337")
HTTP_URL = WS_URL.replace("wss://", "https://").replace("ws://", "http://")
BLOCKS = int(os.environ.get("OGMIOS_LIVE_BLOCKS", "300"))

#: Params for queries that need them.
PARAMS: dict[str, list[Any]] = {
    "queryNetwork/genesisConfiguration": [
        {"era": era} for era in ("byron", "shelley", "alonzo", "conway")
    ],
    "queryLedgerState/projectedRewards": [{"stake": [{"ada": {"lovelace": 1_000_000_000}}]}],
    "queryLedgerState/rewardAccountSummaries": [{"keys": []}],
    "queryLedgerState/utxo": [
        {"outputReferences": [{"transaction": {"id": "0" * 64}, "index": 0}]}
    ],
}
SKIP = {"queryLedgerState/dump"}  # writes to the server's disk

QUERIES = [
    (name, params)
    for name in METHODS
    if name.startswith("query") and name not in SKIP
    for params in PARAMS.get(name, [None])
]


def parse(method: str, raw: Any) -> Any:
    return TypeAdapter(METHODS[method].result).validate_python(raw)


def assert_round_trips(method: str, parsed: Any, raw: Any) -> None:
    adapter: TypeAdapter[Any] = TypeAdapter(METHODS[method].result)
    assert adapter.dump_python(parsed, mode="json", by_alias=True, exclude_unset=True) == raw


@pytest.fixture
async def client() -> Any:
    ogmios = pyogmios.AsyncClient(WS_URL, check_version="strict", reconnect=None)
    try:
        await ogmios.connect()
    except pyogmios.OgmiosConnectionError as error:
        pytest.skip(f"no Ogmios server at {WS_URL}: {error}")
    async with ogmios:
        yield ogmios


@pytest.mark.parametrize(("method", "params"), QUERIES, ids=[f"{m}:{p}" for m, p in QUERIES])
async def test_query_over_websocket(client: pyogmios.AsyncClient, method: str, params: Any) -> None:
    raw = await client.request(method, params)
    # Parse that same answer: on a fast chain, a second request can see a newer tip.
    assert_round_trips(method, parse(method, raw), raw)
    await client.call(method, params)  # and the typed path parses a fresh answer


@pytest.mark.parametrize(("method", "params"), QUERIES, ids=[f"{m}:{p}" for m, p in QUERIES])
async def test_query_over_http(client: pyogmios.AsyncClient, method: str, params: Any) -> None:
    async with pyogmios.AsyncClient(HTTP_URL, check_version="off") as http:
        raw = await http.request(method, params)
        assert_round_trips(method, parse(method, raw), raw)
        await http.call(method, params)


async def test_server_is_v7_and_concurrent_queries_work(client: pyogmios.AsyncClient) -> None:
    assert client.server_health is not None
    assert client.server_health.server_version is not None
    assert client.server_health.server_version[0] == 7
    heights = await asyncio.gather(*(client.call("queryNetwork/blockHeight") for _ in range(100)))
    assert len(heights) == 100


async def test_chain_sync_blocks(client: pyogmios.AsyncClient) -> None:
    """Roll forward from the origin and round-trip every block (OGMIOS_LIVE_BLOCKS, default 300)."""
    await client.call("findIntersection", {"points": ["origin"]})
    adapter: TypeAdapter[Any] = TypeAdapter(METHODS["nextBlock"].result)
    directions = []
    for _ in range(BLOCKS):
        raw = await client.request("nextBlock")
        assert_round_trips("nextBlock", adapter.validate_python(raw), raw)
        directions.append(raw["direction"])
    assert directions[0] == "backward"
    assert directions.count("forward") == BLOCKS - 1


async def test_mempool(client: pyogmios.AsyncClient) -> None:
    await client.call("acquireMempool")
    await client.call("sizeOfMempool")
    await client.call("hasTransaction", {"id": "0" * 64})
    await client.call("nextTransaction")
    await client.call("releaseMempool")


async def test_errors_from_the_server(client: pyogmios.AsyncClient) -> None:
    with pytest.raises(pyogmios.errors.AcquireLedgerStateError) as raised:
        await client.call("acquireLedgerState", {"point": {"slot": 1, "id": "0" * 64}})
    assert raised.value.details is not None
    with pytest.raises(pyogmios.errors.IntersectionNotFoundError):
        await client.call("findIntersection", {"points": [{"slot": 1, "id": "0" * 64}]})
    with pytest.raises(pyogmios.errors.TransactionDeserialisationError):
        await client.call("evaluateTransaction", {"transaction": {"cbor": "00"}})
    with pytest.raises(pyogmios.errors.InvalidRequestError):
        await client.request("queryLedgerState/notAQuery")


def test_sync_client() -> None:
    ogmios = pyogmios.Client(WS_URL, check_version="strict", reconnect=None)
    try:
        ogmios.connect()
    except pyogmios.OgmiosConnectionError as error:
        ogmios.close()
        pytest.skip(f"no Ogmios server at {WS_URL}: {error}")
    with ogmios:
        assert isinstance(ogmios.call("queryLedgerState/epoch"), int)
        assert ogmios.health().network is not None


# Phase 4: typed queries, stateful protocols and transactions ---------------------------------------


async def test_typed_queries(client: pyogmios.AsyncClient) -> None:
    epoch = await client.ledger_state.epoch()
    assert isinstance(epoch, int)
    assert (await client.network.genesis_configuration(era="conway")).era == "conway"
    pools = await client.ledger_state.stake_pools()
    some_pool = next(iter(pools))
    filtered = await client.ledger_state.stake_pools(stake_pools=[{"id": some_pool}])
    assert list(filtered) == [some_pool]
    assert (
        await client.ledger_state.utxo(
            output_references=[{"transaction": {"id": "0" * 64}, "index": 0}]
        )
        == []
    )


async def test_chain_sync_from_origin_and_from_the_tip(client: pyogmios.AsyncClient) -> None:
    async with client.chain_sync(["origin"], pipeline=100) as sync:
        events = [await anext(sync) for _ in range(BLOCKS)]
    assert isinstance(events[0], RollBackward)
    heights = [event.block.height for event in events[1:]]
    assert heights == sorted(heights)
    tip = await client.network.tip()
    async with client.chain_sync([tip]) as sync:
        assert sync.intersection == tip
        assert isinstance(await anext(sync), RollBackward)


async def test_ledger_state_at_the_tip(client: pyogmios.AsyncClient) -> None:
    tip = await client.network.tip()
    async with client.ledger_state_at(tip) as ledger:
        assert await ledger.epoch() == await client.ledger_state.epoch()
        assert await ledger.tip() == tip


async def test_mempool_snapshot(client: pyogmios.AsyncClient) -> None:
    async with client.mempool_snapshot() as snapshot:
        size = await snapshot.size()
        assert size.max_capacity.bytes > 0
        assert len([transaction async for transaction in snapshot]) == size.transactions.count


async def test_the_ledger_rejects_an_unsigned_transaction(client: pyogmios.AsyncClient) -> None:
    """An unsigned transaction spending a real UTxO is rejected by a ledger rule, with typed details."""
    utxo = None
    # Find a live UTxO through the recorded recent blocks' output addresses.
    for fixture in sorted(
        (ROOT / "tests" / "fixtures" / f"v{pyogmios.OGMIOS_VERSION}" / "nextBlock").glob(
            "recent-*.json"
        )
    ):
        block = json.loads(fixture.read_text())["result"]["block"]
        for transaction in block.get("transactions", []):
            for output in transaction["outputs"]:
                found = await client.ledger_state.utxo(addresses=[output["address"]])
                if found:
                    utxo = found[0]
                    break
            if utxo:
                break
        if utxo:
            break
    if utxo is None:
        pytest.skip("no UTxO left at the recorded blocks' addresses; run `just record-fixtures`")
    address = bytes([0x60]) + bytes(range(28))
    body = {
        0: [[bytes.fromhex(utxo.transaction.id), utxo.index]],
        1: [[address, 2_000_000]],
        2: 200_000,
    }
    transaction = cbor2.dumps([body, {}, True, None])
    with pytest.raises(pyogmios.errors.SubmitTransactionError) as raised:
        await client.submit_transaction(transaction)
    assert 3100 <= raised.value.code < 3200
    assert (
        type(raised.value) is not pyogmios.errors.SubmitTransactionError
    )  # a specific ledger rule
    assert raised.value.details is not None
    assert await client.evaluate_transaction(transaction) == []  # no scripts to run


def test_sync_client_protocols() -> None:
    ogmios = pyogmios.Client(WS_URL, check_version="strict", reconnect=None)
    try:
        ogmios.connect()
    except pyogmios.OgmiosConnectionError as error:
        ogmios.close()
        pytest.skip(f"no Ogmios server at {WS_URL}: {error}")
    with ogmios:
        tip = ogmios.network.tip()
        with ogmios.chain_sync(["origin"]) as sync:
            assert [type(next(sync)).__name__ for _ in range(3)] == [
                "RollBackward",
                "RollForward",
                "RollForward",
            ]
        with ogmios.ledger_state_at(tip) as ledger:
            assert isinstance(ledger.epoch(), int)
