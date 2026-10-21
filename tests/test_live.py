"""The client against a live Ogmios v7 server (``just test-integration``; OGMIOS_URL, OGMIOS_LIVE_BLOCKS).

Every query over WebSocket and HTTP, the sync client, chain sync and the mempool: each result must
parse, and dump back to exactly what the server sent.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import pytest
from pydantic import TypeAdapter

import pyogmios
from pyogmios._generated.methods import METHODS

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
    assert_round_trips(method, await client.call(method, params), raw)


@pytest.mark.parametrize(("method", "params"), QUERIES, ids=[f"{m}:{p}" for m, p in QUERIES])
async def test_query_over_http(client: pyogmios.AsyncClient, method: str, params: Any) -> None:
    async with pyogmios.AsyncClient(HTTP_URL, check_version="off") as http:
        raw = await http.request(method, params)
        assert_round_trips(method, await http.call(method, params), raw)


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
