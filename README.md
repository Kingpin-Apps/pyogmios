# PyOgmios

A Python client for [Ogmios](https://ogmios.dev) v7, the JSON-RPC bridge to `cardano-node`.

> [!NOTE]
> This branch is the in-progress 1.0 rewrite for **Ogmios v7**. The released 0.7.x on PyPI speaks Ogmios v5 only,
> and the import name has changed from `pyogmios_client` to `pyogmios`. Full documentation comes with 1.0.

## Features

- **Ogmios v7**: every method of the v7.0.0 schema (all 24 queries, chain sync, mempool monitoring, transaction
  submission and evaluation), with types generated from the schema and checked against a live node.
- **Async and sync**: `AsyncClient` for asyncio, `Client` for everything else; the same methods on both.
- **WebSocket and HTTP**: many requests in flight on one WebSocket connection; HTTP for one-off queries.
- **Resilient**: reconnects with backoff, keep-alive pings, per-request timeouts, and a server version check.
- **Typed**: results are Pydantic models (`pyogmios.types`), and errors are exceptions chosen by the Ogmios error
  code, with the error data parsed (`pyogmios.errors`).
- **Python 3.11 to 3.15**, including the free-threaded builds. Apache-2.0.

## Install

```shell
pip install pyogmios              # once 1.0 is released
pip install "pyogmios[speedups]"  # with orjson for faster JSON
```

You need a running Ogmios v7 connected to a `cardano-node`; see the
[Ogmios getting started guide](https://ogmios.dev/getting-started/).

## Usage

Every Ogmios query is a typed method, grouped as in Ogmios (`queryLedgerState/*`, `queryNetwork/*`):

```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    epoch = client.ledger_state.epoch()
    tip = client.network.tip()
    parameters = client.ledger_state.protocol_parameters()
    utxos = client.ledger_state.utxo(addresses=["addr_test1..."])
    print(epoch, parameters.max_transaction_size, len(utxos))
```

With asyncio, requests run concurrently on one connection:

```python
import asyncio
import pyogmios


async def main() -> None:
    async with pyogmios.AsyncClient("ws://localhost:1337") as client:
        epoch, tip = await asyncio.gather(client.ledger_state.epoch(), client.network.tip())
        print(epoch, tip)


asyncio.run(main())
```

### Following the chain

```python
from pyogmios.types import RollForward

async with client.chain_sync(["origin"]) as sync:
    async for event in sync:
        if isinstance(event, RollForward):
            print(event.block.height, event.block.id)
        else:
            print("rolled back to", event.point)
```

Chain sync keeps up to 50 requests in flight (`pipeline=`), and if the connection drops it reconnects and carries on
from the last block it saw. Chain sync, an acquired ledger state and the mempool each use their own connection, so
they never affect the client's other requests.

### The ledger at a point, and the mempool

```python
async with client.ledger_state_at(point) as ledger:
    print(await ledger.epoch(), await ledger.stake_pools())

async with client.mempool() as transactions:  # every transaction entering the mempool
    async for transaction_id in transactions:
        print(transaction_id)
```

### Transactions

```python
from pyogmios.errors import SubmitTransactionError

try:
    submitted = await client.submit_transaction(signed_cbor)  # bytes or hex
    print(submitted.transaction.id)
except SubmitTransactionError as error:
    # A subclass per ledger rule, for example MissingSignatoriesError or ValueNotConservedError.
    print(type(error).__name__, error.code, error.details)

budgets = await client.evaluate_transaction(transaction_cbor, additional_utxo=[...])
```

Every error from the server is an exception chosen by its Ogmios error code (`pyogmios.errors`), carrying `code`,
`message`, `data` and `details` (the data parsed into a model). Results are Pydantic models from `pyogmios.types`, with
Python field names: `parameters.max_transaction_size` is `maxTransactionSize` on the wire.

`client.call(method, params)` calls any method by its Ogmios name, and `client.health()` reads the server's sync
progress, tip, era and version.

## Command line

```shell
pyogmios health                       # version, network, sync progress and tip
pyogmios tip
pyogmios query epoch
pyogmios query utxo '{"addresses": ["addr_test1..."]}'
pyogmios follow --from origin --headers  # chain events, one JSON document per line
pyogmios mempool                      # transaction ids as they enter the mempool
pyogmios submit tx.signed             # hex, CBOR, or a cardano-cli text envelope
```

The server is `--url`, `$OGMIOS_URL` or `ws://localhost:1337`. Output is JSON, indented in a terminal. Exit codes are
0 on success, 1 for an error from the server, 2 for a usage error and 3 when the server cannot be reached.

## Development

PyOgmios uses [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/). It supports Python 3.11 to 3.15,
including the free-threaded builds.

```shell
just sync                # install the project and all development groups
just test                # unit tests on the default Python
just test-all            # unit tests on Python 3.11, 3.12, 3.13, 3.14 and 3.15
just test-free-threaded  # unit tests on 3.14t and 3.15t
just test-integration    # live tests against Ogmios (OGMIOS_URL, default ws://localhost:1337)
just check               # lint, type-check and test
just regen-models        # regenerate the types from the pinned Ogmios schema
just record-fixtures     # record test fixtures from a live Ogmios
just sweep               # check blocks from across the whole chain against the schema and models
```

Run `uv run pre-commit install` once to lint and format on commit and check commit messages
([Conventional Commits](https://www.conventionalcommits.org/)). Releases are cut with `just bump`, and pushing the
`v*` tag publishes to PyPI.
