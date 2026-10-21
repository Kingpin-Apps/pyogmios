"""Check real blocks from across the whole chain against the corrected schema and the models.

Picks evenly spaced heights between the origin and the node's tip, finds each block's hash with Koios's
public API (read-only), follows the chain from there for a few hundred blocks, and checks every block:
against the corrected JSON schema, and by parsing it into the models and dumping it back unchanged.
Each distinct problem is reported once, with the first block it was seen in.

With ``--full``, it instead parses every block from the origin to the tip with the models only (the
JSON schema check is too slow for millions of blocks), reporting progress as it goes.

Usage: python scripts/sweep_blocks.py [--samples 60] [--blocks 300] [--network preview]
       python scripts/sweep_blocks.py --full
       (OGMIOS_URL, default ws://localhost:1337)
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import importlib.util
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator
from pydantic import TypeAdapter, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pyogmios  # noqa: E402
from pyogmios._generated.methods import METHODS, OGMIOS_VERSION  # noqa: E402

KOIOS = {
    "mainnet": "https://api.koios.rest/api/v1",
    "preprod": "https://preprod.koios.rest/api/v1",
    "preview": "https://preview.koios.rest/api/v1",
}


def corrected_block_validator() -> Draft7Validator:
    spec = importlib.util.spec_from_file_location(
        "build_schema", ROOT / "scripts" / "build_schema.py"
    )
    assert spec is not None
    assert spec.loader is not None
    build_schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_schema)
    schemas = ROOT / "schemas" / f"v{OGMIOS_VERSION}"
    ogmios = json.loads((schemas / "ogmios.json").read_text())
    cardano = json.loads((schemas / "cardano.json").read_text())
    ogmios, cardano = copy.deepcopy(ogmios), copy.deepcopy(cardano)
    for correction in build_schema.CORRECTIONS:
        correction(ogmios, cardano)
    registry = Registry().with_resources(
        [
            ("ogmios.json", Resource(ogmios, specification=DRAFT7)),
            ("cardano.json", Resource(cardano, specification=DRAFT7)),
        ]
    )
    return Draft7Validator({"$ref": "cardano.json#/definitions/Block"}, registry=registry)


def block_at(koios: str, height: int) -> dict[str, Any] | None:
    url = f"{koios}/blocks?block_height=eq.{height}&select=hash,abs_slot"
    with urllib.request.urlopen(url, timeout=30) as response:
        rows = json.load(response)
    return {"slot": rows[0]["abs_slot"], "id": rows[0]["hash"]} if rows else None


def deepest(error: Any) -> Any:
    while error.context:
        error = max(error.context, key=lambda e: len(list(e.absolute_path)))
    return error


async def sweep(url: str, koios: str, samples: int, blocks: int) -> int:
    validator = corrected_block_validator()
    adapter: TypeAdapter[Any] = TypeAdapter(METHODS["nextBlock"].result)
    problems: dict[str, str] = {}
    checked = 0
    started = time.perf_counter()
    async with pyogmios.AsyncClient(url, check_version="strict") as client:
        top = await client.network.block_height()
        tip_height = top if isinstance(top, int) else 0
        heights = [1 + i * (tip_height - blocks) // max(1, samples - 1) for i in range(samples)]
        for height in heights:
            point = "origin" if height <= 1 else await asyncio.to_thread(block_at, koios, height)
            if point is None:
                continue
            async with client.chain_sync([point], raw=True, pipeline=100) as sync:
                count = 0
                async for event in sync:
                    if event["direction"] != "forward":
                        continue
                    block = event["block"]
                    where = f"{block.get('era')} block {block.get('height')} ({block['id'][:16]})"
                    for error in validator.iter_errors(block):
                        leaf = deepest(error)
                        path = "/".join(
                            str(p) for p in leaf.absolute_path if not isinstance(p, int)
                        )
                        problems.setdefault(f"schema: {path}: {leaf.message[:160]}", where)
                    try:
                        parsed = adapter.validate_python(event)
                        if (
                            adapter.dump_python(
                                parsed, mode="json", by_alias=True, exclude_unset=True
                            )
                            != event
                        ):
                            problems.setdefault("model: dump differs from the server's JSON", where)
                    except ValidationError as error:
                        first = error.errors()[0]
                        problems.setdefault(
                            f"model: {'/'.join(map(str, first['loc'][:8]))}: {first['msg']}", where
                        )
                    checked += 1
                    count += 1
                    if count >= blocks:
                        break
            print(
                f"  height {height:>9}: {checked} blocks checked, {len(problems)} distinct problems",
                flush=True,
            )
    print(
        f"\n{checked} blocks in {time.perf_counter() - started:.0f}s; {len(problems)} distinct problems"
    )
    for problem, where in sorted(problems.items()):
        print(f"- {problem}\n    first seen in {where}")
    return 1 if problems else 0


async def full_sweep(url: str) -> int:
    adapter: TypeAdapter[Any] = TypeAdapter(METHODS["nextBlock"].result)
    problems: dict[str, str] = {}
    checked = 0
    started = time.perf_counter()
    async with pyogmios.AsyncClient(url, check_version="strict") as client:
        tip_height = await client.network.block_height()
        async with client.chain_sync(["origin"], raw=True, pipeline=200) as sync:
            async for event in sync:
                if event["direction"] != "forward":
                    continue
                block = event["block"]
                try:
                    adapter.validate_python(event)
                except ValidationError as error:
                    first = error.errors()[0]
                    key = f"{'/'.join(str(p) for p in first['loc'][:10] if not isinstance(p, int))}: {first['msg']}"
                    if key not in problems:
                        problems[key] = (
                            f"{block.get('era')} block {block.get('height')} ({block['id']})"
                        )
                        print(f"PROBLEM {key}\n    in {problems[key]}", flush=True)
                checked += 1
                if checked % 100_000 == 0:
                    rate = checked / (time.perf_counter() - started)
                    print(
                        f"  {checked:,} blocks, height {block.get('height')}, {rate:,.0f} blocks/s, {len(problems)} problems",
                        flush=True,
                    )
                if block.get("height", 0) >= tip_height:
                    break
    print(
        f"\n{checked:,} blocks in {time.perf_counter() - started:,.0f}s; {len(problems)} distinct problems"
    )
    for problem, where in sorted(problems.items()):
        print(f"- {problem}\n    first seen in {where}")
    return 1 if problems else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--samples", type=int, default=60, help="points spread across the chain")
    parser.add_argument("--blocks", type=int, default=300, help="blocks to check from each point")
    parser.add_argument("--network", choices=sorted(KOIOS), default="preview")
    parser.add_argument("--full", action="store_true", help="parse every block from the origin")
    args = parser.parse_args()
    url = os.environ.get("OGMIOS_URL", "ws://localhost:1337")
    if args.full:
        sys.exit(asyncio.run(full_sweep(url)))
    sys.exit(asyncio.run(sweep(url, KOIOS[args.network], args.samples, args.blocks)))


if __name__ == "__main__":
    main()
