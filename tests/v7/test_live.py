"""The generated models against a live Ogmios server (``just test-integration``, OGMIOS_URL).

Every query, the chain-sync and mempool messages, and a run of real blocks must parse and round-trip.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import pytest
from pydantic import TypeAdapter

from pyogmios._generated.methods import METHODS

websockets = pytest.importorskip("websockets")

pytestmark = pytest.mark.integration

OGMIOS_URL = os.environ.get("OGMIOS_URL", "ws://localhost:1337")
BLOCKS = int(os.environ.get("OGMIOS_LIVE_BLOCKS", "300"))
#: Seconds to wait for one response; the largest preview queries take a few seconds.
TIMEOUT = 60

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


def round_trip(method: str, result: Any) -> None:
    adapter: TypeAdapter[Any] = TypeAdapter(METHODS[method].result)
    value = adapter.validate_python(result)
    assert adapter.dump_python(value, mode="json", by_alias=True, exclude_unset=True) == result


class Session:
    def __init__(self, ws: Any) -> None:
        self.ws = ws

    async def call(self, method: str, params: Any = None) -> dict[str, Any]:
        request: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "id": 0}
        if params is not None:
            request["params"] = params
        await self.ws.send(json.dumps(request))
        response: dict[str, Any] = json.loads(await asyncio.wait_for(self.ws.recv(), TIMEOUT))
        assert "error" not in response, response["error"]
        return response


@pytest.fixture
async def session() -> Any:
    # Only a failed connection skips; errors inside a test (TimeoutError is an OSError) must fail it.
    try:
        ws = await websockets.connect(OGMIOS_URL, max_size=None, open_timeout=10)
    except OSError as error:
        pytest.skip(f"no Ogmios server at {OGMIOS_URL}: {error}")
    async with ws:
        yield Session(ws)


QUERIES = [
    (name, params)
    for name in METHODS
    if name.startswith("query") and name not in SKIP
    for params in PARAMS.get(name, [None])
]


@pytest.mark.parametrize(("method", "params"), QUERIES, ids=[f"{m}:{p}" for m, p in QUERIES])
async def test_query(session: Session, method: str, params: Any) -> None:
    round_trip(method, (await session.call(method, params))["result"])


async def test_chain_sync_blocks(session: Session) -> None:
    """Roll forward from the origin and round-trip every block (OGMIOS_LIVE_BLOCKS, default 300).

    Old blocks stream quickly; the recorded fixtures cover recent ones.
    """
    found = await session.call("findIntersection", {"points": ["origin"]})
    round_trip("findIntersection", found["result"])
    directions = []
    for _ in range(BLOCKS):
        result = (await session.call("nextBlock"))["result"]
        round_trip("nextBlock", result)
        directions.append(result["direction"])
    assert directions[0] == "backward"
    assert directions.count("forward") == BLOCKS - 1


async def test_mempool(session: Session) -> None:
    round_trip("acquireMempool", (await session.call("acquireMempool"))["result"])
    round_trip("sizeOfMempool", (await session.call("sizeOfMempool"))["result"])
    round_trip("hasTransaction", (await session.call("hasTransaction", {"id": "0" * 64}))["result"])
    round_trip("nextTransaction", (await session.call("nextTransaction", {}))["result"])
    round_trip("releaseMempool", (await session.call("releaseMempool"))["result"])
