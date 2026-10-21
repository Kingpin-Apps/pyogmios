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

```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    epoch = client.call("queryLedgerState/epoch")
    tip = client.call("queryNetwork/tip")
    parameters = client.call("queryLedgerState/protocolParameters")
    print(epoch, tip.slot, parameters.max_transaction_size)
```

With asyncio, requests run concurrently on one connection:

```python
import asyncio
import pyogmios


async def main() -> None:
    async with pyogmios.AsyncClient("ws://localhost:1337") as client:
        epoch, tip = await asyncio.gather(
            client.call("queryLedgerState/epoch"),
            client.call("queryNetwork/tip"),
        )
        print(epoch, tip)


asyncio.run(main())
```

Params can be a model from `pyogmios.types` or a dict, with either Python or Ogmios field names, and are checked
before they are sent:

```python
utxos = client.call("queryLedgerState/utxo", {"addresses": ["addr_test1..."]})
```

Errors from the server are exceptions:

```python
from pyogmios.errors import AcquireLedgerStateError

try:
    client.call("acquireLedgerState", {"point": {"slot": 1, "id": "0" * 64}})
except AcquireLedgerStateError as error:
    print(error.code, error.message, error.details)
```

`client.health()` reads the server's sync progress, tip, era and version.

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
```

Run `uv run pre-commit install` once to lint and format on commit and check commit messages
([Conventional Commits](https://www.conventionalcommits.org/)). Releases are cut with `just bump`, and pushing the
`v*` tag publishes to PyPI.
