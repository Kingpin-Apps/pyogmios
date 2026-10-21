"""``pyogmios``: query and follow an Ogmios server from the command line.

::

    pyogmios health
    pyogmios tip
    pyogmios query epoch
    pyogmios query utxo '{"addresses": ["addr_test1..."]}'
    pyogmios follow --from tip
    pyogmios mempool
    pyogmios submit tx.signed          # hex, CBOR bytes, or a cardano-cli text envelope
    pyogmios evaluate tx.raw

Output is JSON: indented in a terminal, one compact document (or one per line for streams) otherwise.
The server is ``--url``, or ``OGMIOS_URL``, or ``ws://localhost:1337``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, TypeAdapter

from . import __version__
from ._generated.methods import METHODS
from ._transport import Reconnect
from .client import DEFAULT_URL, AsyncClient
from .errors import OgmiosConnectionError, OgmiosError, ResponseError

#: Exit codes: 1 for an error answered by the server, 3 when the server cannot be reached.
EXIT_RESPONSE_ERROR = 1
EXIT_CONNECTION_ERROR = 3


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _query_names() -> dict[str, str]:
    """Query names on the command line: ``ledger-state/epoch``, ``network/tip``, and the short name
    (``epoch``) unless it is ambiguous (``tip`` is in both namespaces)."""
    full: dict[str, str] = {}
    for method in METHODS:
        namespace, _, name = method.partition("/")
        if namespace in ("queryLedgerState", "queryNetwork"):
            prefix = "network" if namespace == "queryNetwork" else "ledger-state"
            full[f"{prefix}/{_snake(name)}"] = method
    shorts = [key.split("/", 1)[1] for key in full]
    names = dict(full)
    for key, method in full.items():
        short = key.split("/", 1)[1]
        if shorts.count(short) == 1:
            names[short] = method
    return names


QUERIES = _query_names()


def to_json(value: Any) -> Any:
    """Plain JSON values, with Ogmios field names."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True, exclude_unset=True)
    return TypeAdapter(Any).dump_python(value, mode="json", by_alias=True)


class Output:
    def __init__(self, stream: Any = None, *, pretty: bool | None = None) -> None:
        self.stream = stream or sys.stdout
        self.pretty = self.stream.isatty() if pretty is None else pretty

    def write(self, value: Any, *, line: bool = False) -> None:
        indent = None if line or not self.pretty else 2
        self.stream.write(json.dumps(to_json(value), indent=indent) + "\n")
        self.stream.flush()


def read_transaction(source: str) -> str:
    """Transaction CBOR as hex, from hex, a file of hex or CBOR bytes, or a cardano-cli text envelope."""
    path = Path(source)
    if not path.is_file():
        if re.fullmatch(r"[0-9a-fA-F]+", source):
            return source.lower()
        raise ValueError(f"{source!r} is neither a file nor hex CBOR")
    data = path.read_bytes()
    try:
        text = data.decode().strip()
    except UnicodeDecodeError:
        return data.hex()  # raw CBOR
    if text.startswith("{"):
        envelope = json.loads(text)
        if "cborHex" not in envelope:
            raise ValueError(
                f"{source}: a JSON file must be a text envelope with a 'cborHex' field"
            )
        return str(envelope["cborHex"]).lower()
    if re.fullmatch(r"[0-9a-fA-F]+", text):
        return text.lower()
    return data.hex()


def parse_params(text: str | None) -> Any:
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"params must be JSON: {error}") from error


def _shared_options(parser: argparse.ArgumentParser, *, top_level: bool) -> None:
    """Options accepted before and after the command. After it, they default to "not given", so they
    do not overwrite a value given before it."""
    unset = None if top_level else argparse.SUPPRESS
    parser.add_argument(
        "--url",
        default=os.environ.get("OGMIOS_URL", DEFAULT_URL) if top_level else unset,
        help="Ogmios URL (default: $OGMIOS_URL or ws://localhost:1337)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0 if top_level else unset,
        help="seconds per request (default: 60)",
    )
    style = parser.add_mutually_exclusive_group()
    style.add_argument(
        "--pretty", action="store_true", default=unset, help="indent the JSON output"
    )
    style.add_argument(
        "--compact", action="store_false", dest="pretty", default=unset, help="one line of JSON"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyogmios",
        description="Query and follow an Ogmios v7 server.",
        epilog="Queries: " + ", ".join(sorted(key for key in QUERIES if "/" not in key)),
    )
    parser.add_argument("--version", action="version", version=f"pyogmios {__version__}")
    _shared_options(parser, top_level=True)
    shared = argparse.ArgumentParser(add_help=False)
    _shared_options(shared, top_level=False)
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")

    def command(name: str, text: str) -> argparse.ArgumentParser:
        return commands.add_parser(name, help=text, description=text, parents=[shared])

    command("health", "the server's version, network, sync progress and tip")
    command("tip", "the network tip and block height")

    query = command("query", "run any ledger state or network query")
    query.add_argument(
        "name", choices=sorted(QUERIES), metavar="name", help="for example epoch or utxo"
    )
    query.add_argument(
        "params", nargs="?", help="params as JSON, for example '{\"addresses\": [...]}'"
    )

    follow = command("follow", "follow the chain: one JSON event per line")
    follow.add_argument(
        "--from", dest="start", default="tip", help="'tip', 'origin', or slot.id (default: tip)"
    )
    follow.add_argument("--count", type=int, help="stop after this many events")
    follow.add_argument(
        "--headers", action="store_true", help="print block headers only, without transactions"
    )

    mempool = command("mempool", "transactions entering the mempool: one per line")
    mempool.add_argument(
        "--full", action="store_true", help="print whole transactions, not just ids"
    )
    mempool.add_argument("--count", type=int, help="stop after this many transactions")

    for name, text in (
        ("submit", "submit a signed transaction"),
        ("evaluate", "evaluate a transaction's scripts"),
    ):
        command(name, text).add_argument(
            "transaction", help="hex CBOR, or a file of hex, CBOR or a cardano-cli text envelope"
        )
    return parser


async def run(args: argparse.Namespace, out: Output) -> None:
    # One retry: a command should fail fast when the server is down.
    reconnect = Reconnect(attempts=2, initial_delay=0.5)
    async with AsyncClient(args.url, timeout=args.timeout, reconnect=reconnect) as client:
        if args.command == "health":
            out.write(await client.health())
        elif args.command == "tip":
            tip, height = await asyncio.gather(client.network.tip(), client.network.block_height())
            out.write({"tip": to_json(tip), "blockHeight": height})
        elif args.command == "query":
            out.write(await client.call(QUERIES[args.name], parse_params(args.params)))
        elif args.command == "follow":
            await follow(client, args, out)
        elif args.command == "mempool":
            async with client.mempool(full=args.full) as transactions:
                count = 0
                async for transaction in transactions:
                    out.write(transaction, line=True)
                    count += 1
                    if args.count is not None and count >= args.count:
                        break
        elif args.command == "submit":
            out.write(await client.submit_transaction(read_transaction(args.transaction)))
        elif args.command == "evaluate":
            out.write(await client.evaluate_transaction(read_transaction(args.transaction)))


async def follow(client: AsyncClient, args: argparse.Namespace, out: Output) -> None:
    if args.start == "tip":
        points: list[Any] = [await client.network.tip()]
    elif args.start == "origin":
        points = ["origin"]
    else:
        slot, _, block_id = args.start.partition(".")
        if not (slot.isdigit() and block_id):
            raise ValueError("--from must be 'tip', 'origin' or slot.id, for example 1234.abcd...")
        points = [{"slot": int(slot), "id": block_id}]
    async with client.chain_sync(points, raw=True) as sync:
        count = 0
        async for event in sync:
            if args.headers and event["direction"] == "forward":
                event = {
                    **event,
                    "block": {k: v for k, v in event["block"].items() if k != "transactions"},
                }
            out.write(event, line=True)
            count += 1
            if args.count is not None and count >= args.count:
                break


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out = Output(pretty=args.pretty)
    try:
        asyncio.run(run(args, out))
    except KeyboardInterrupt:
        return 130
    except ResponseError as error:
        print(f"pyogmios: {type(error).__name__}: {error}", file=sys.stderr)
        if error.data is not None:
            print(json.dumps(error.data, indent=2), file=sys.stderr)
        return EXIT_RESPONSE_ERROR
    except OgmiosConnectionError as error:
        print(f"pyogmios: {error}", file=sys.stderr)
        return EXIT_CONNECTION_ERROR
    except (OgmiosError, ValueError) as error:
        print(f"pyogmios: {error}", file=sys.stderr)
        return EXIT_RESPONSE_ERROR
    return 0
