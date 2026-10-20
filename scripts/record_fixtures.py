"""Record real Ogmios responses as test fixtures.

Calls every method on a live server, including requests that are meant to fail, and saves each full
JSON-RPC response to ``tests/fixtures/v<version>/<method>/<case>.json``. Large results are trimmed to a
few entries per list or keyed map, so the fixtures stay small but keep the real shapes.

Usage: python scripts/record_fixtures.py [ws://localhost:1337]   (or set OGMIOS_URL)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

import websockets

ROOT = Path(__file__).resolve().parent.parent
VERSION = (ROOT / "schemas" / "VERSION").read_text().strip()
OUTPUT = ROOT / "tests" / "fixtures" / f"v{VERSION}"

#: Entries kept per list or keyed map when trimming.
KEEP = 3
#: Map keys that are data (pool ids, addresses, credentials, hashes, numbers), not field names.
DATA_KEY = re.compile(
    r"^((pool|stake|drep|cc_hot|cc_cold|addr|script)[a-z_]*1[0-9a-z]+|[0-9a-f]{56,}|\d+)$"
)
#: Koios public API for preview, used only to find a recent block to start chain sync from.
KOIOS = "https://preview.koios.rest/api/v1"
#: Blocks scanned to find a varied set of real blocks.
BLOCKS_TO_SCAN = 400
BLOCKS_TO_KEEP = 12


def trim(value: Any) -> Any:
    """Keep the first few entries of every list and data-keyed map, at any depth."""
    if isinstance(value, list):
        return [trim(item) for item in value[:KEEP]]
    if isinstance(value, dict):
        items = list(value.items())
        if len(items) > KEEP and all(DATA_KEY.match(key) for key, _ in items):
            items = items[:KEEP]
        return {key: trim(item) for key, item in items}
    return value


def save(method: str, case: str, response: dict[str, Any]) -> None:
    folder = OUTPUT / method.replace("/", "-")
    folder.mkdir(parents=True, exist_ok=True)
    response = {**response, "id": f"{method}:{case}"}
    if "result" in response:
        response["result"] = trim(response["result"])
    (folder / f"{case}.json").write_text(json.dumps(response, indent=2, sort_keys=True) + "\n")
    print(
        f"  {method:42} {case:28} {'error ' + str(response['error']['code']) if 'error' in response else 'ok'}"
    )


class Recorder:
    def __init__(self, ws: Any) -> None:
        self.ws = ws

    async def call(self, method: str, params: Any = None) -> dict[str, Any]:
        request: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "id": method}
        if params is not None:
            request["params"] = params
        await self.ws.send(json.dumps(request))
        response: dict[str, Any] = json.loads(await self.ws.recv())
        return response

    async def record(self, method: str, case: str, params: Any = None) -> dict[str, Any]:
        response = await self.call(method, params)
        save(method, case, response)
        return response


def block_features(block: dict[str, Any]) -> set[str]:
    """What makes a block interesting for coverage: its era, type and transaction contents."""
    features = {f"era:{block.get('era')}", f"type:{block.get('type')}"}
    for tx in block.get("transactions", []):
        features |= {f"tx:{key}" for key in tx}
        features |= {f"certificate:{cert['type']}" for cert in tx.get("certificates", [])}
        features |= {f"script:{script['language']}" for script in tx.get("scripts", {}).values()}
    return features


def recent_point(height: int) -> dict[str, Any]:
    """The point of the preview block at ``height``, from Koios's public API (read-only)."""
    url = f"{KOIOS}/blocks?block_height=eq.{height}&select=hash,abs_slot"
    with urllib.request.urlopen(url, timeout=30) as response:
        block = json.load(response)[0]
    return {"slot": block["abs_slot"], "id": block["hash"]}


async def scan_blocks(r: Recorder, label: str, scan: int, keep: int) -> None:
    """Roll forward ``scan`` blocks and save up to ``keep`` that add something new (era, certificate...)."""
    seen: set[str] = set()
    kept = 0
    for _ in range(scan):
        response = await asyncio.wait_for(r.call("nextBlock"), timeout=120)
        result = response["result"]
        if result["direction"] != "forward":
            continue
        if block_features(result["block"]) - seen:
            seen |= block_features(result["block"])
            kept += 1
            save("nextBlock", f"{label}-{kept:02d}", response)
            if kept == keep:
                return


async def record_all(url: str) -> None:
    async with websockets.connect(url, max_size=None, open_timeout=30) as ws:
        r = Recorder(ws)
        tip = (await r.call("queryNetwork/tip"))["result"]
        bogus_point = {"slot": 1, "id": "0" * 64}

        print("Network and ledger-state queries")
        for method in (
            "queryNetwork/blockHeight", "queryNetwork/startTime", "queryNetwork/tip",
            "queryLedgerState/constitution", "queryLedgerState/constitutionalCommittee",
            "queryLedgerState/delegateRepresentatives", "queryLedgerState/epoch", "queryLedgerState/eraStart",
            "queryLedgerState/eraSummaries", "queryLedgerState/governanceProposals",
            "queryLedgerState/liveStakeDistribution", "queryLedgerState/nonces",
            "queryLedgerState/operationalCertificates", "queryLedgerState/protocolParameters",
            "queryLedgerState/rewardsProvenance", "queryLedgerState/stakePools",
            "queryLedgerState/stakePoolsPerformances", "queryLedgerState/tip",
            "queryLedgerState/treasuryAndReserves",
        ):  # fmt: skip
            await r.record(method, "ok")
        for era in ("byron", "shelley", "alonzo", "conway"):
            await r.record("queryNetwork/genesisConfiguration", era, {"era": era})
        await r.record("queryNetwork/genesisConfiguration", "dijkstra", {"era": "dijkstra"})
        await r.record(
            "queryLedgerState/projectedRewards",
            "ok",
            {"stake": [{"ada": {"lovelace": 1_000_000_000}}]},
        )

        pools = (await r.call("queryLedgerState/stakePools"))["result"]
        pool = next(iter(pools.values()))
        await r.record(
            "queryLedgerState/stakePools", "filtered", {"stakePools": [{"id": pool["id"]}]}
        )
        reward_account = pool["rewardAccount"]
        await r.record("queryLedgerState/rewardAccountSummaries", "ok", {"keys": [reward_account]})
        dreps = (await r.call("queryLedgerState/delegateRepresentatives"))["result"]
        registered = next(d for d in dreps if d.get("type") == "registered")
        await r.record(
            "queryLedgerState/delegateRepresentatives", "filtered", {"keys": [registered["id"]]}
        )

        print("UTxO")
        await r.record("queryLedgerState/utxo", "unknown-reference", {
            "outputReferences": [{"transaction": {"id": "0" * 64}, "index": 0}]
        })  # fmt: skip

        print("Ledger state acquisition")
        await r.record("acquireLedgerState", "ok", {"point": tip})
        await r.record("queryLedgerState/epoch", "acquired")
        await r.record("releaseLedgerState", "ok")
        await r.record("acquireLedgerState", "point-not-on-chain", {"point": bogus_point})

        print("Chain sync")
        await r.record("findIntersection", "not-found", {"points": [bogus_point]})
        await r.record("findIntersection", "ok", {"points": [tip]})
        await r.record("nextBlock", "backward")
        # Ogmios cannot seek by slot, so start from the origin for Byron blocks, then from a recent block
        # whose hash comes from Koios's public preview API, for blocks with today's transactions.
        await r.call("findIntersection", {"points": ["origin"]})
        await r.call("nextBlock")
        await scan_blocks(r, "byron", 30, 3)
        height = (await r.call("queryNetwork/blockHeight"))["result"]
        recent = recent_point(height - BLOCKS_TO_SCAN - 100)
        await r.call("findIntersection", {"points": [recent]})
        await r.call("nextBlock")
        await scan_blocks(r, "recent", BLOCKS_TO_SCAN, BLOCKS_TO_KEEP)
        # UTxO by address, using an output address from a recorded block.
        block = json.loads((OUTPUT / "nextBlock" / "recent-01.json").read_text())["result"]["block"]
        address = next(o["address"] for tx in block["transactions"] for o in tx["outputs"])
        await r.record("queryLedgerState/utxo", "by-address", {"addresses": [address]})

        print("Mempool")
        await r.record("sizeOfMempool", "not-acquired")
        await r.record("acquireMempool", "ok")
        await r.record("sizeOfMempool", "ok")
        await r.record("hasTransaction", "ok", {"id": "0" * 64})
        await r.record("nextTransaction", "ok", {})
        await r.record("nextTransaction", "all-fields", {"fields": "all"})
        await r.record("releaseMempool", "ok")

        print("Transaction submission (expected failures)")
        await r.record("submitTransaction", "deserialisation", {"transaction": {"cbor": "00"}})
        await r.record("evaluateTransaction", "deserialisation", {"transaction": {"cbor": "00"}})

        print("JSON-RPC errors")
        await r.record("queryLedgerState/notAQuery", "unknown-method")
        await r.record("queryLedgerState/projectedRewards", "invalid-params", {"stake": [1]})


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("OGMIOS_URL", "ws://localhost:1337")
    print(f"Recording Ogmios v{VERSION} fixtures from {url} into {OUTPUT.relative_to(ROOT)}")
    asyncio.run(record_all(url))


if __name__ == "__main__":
    main()
