# pyogmios

[![PyPI](https://img.shields.io/pypi/v/pyogmios.svg)](https://pypi.org/project/pyogmios/)
[![Python](https://img.shields.io/pypi/pyversions/pyogmios.svg)](https://pypi.org/project/pyogmios/)
[![CI](https://github.com/Kingpin-Apps/pyogmios/actions/workflows/ci.yml/badge.svg)](https://github.com/Kingpin-Apps/pyogmios/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-kingpin--apps.github.io-indigo.svg)](https://kingpin-apps.github.io/pyogmios/)
[![License](https://img.shields.io/pypi/l/pyogmios.svg)](https://github.com/Kingpin-Apps/pyogmios/blob/main/LICENSE)

A Python client for [Ogmios](https://ogmios.dev) **v7**, the lightweight JSON-RPC bridge to
`cardano-node`. Query the ledger, follow the chain, watch the mempool and submit transactions, with
every request and answer typed.

**[Documentation](https://kingpin-apps.github.io/pyogmios/)**

```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    epoch = client.ledger_state.epoch()
    utxos = client.ledger_state.utxo(addresses=["addr_test1..."])
    parameters = client.ledger_state.protocol_parameters()
    print(epoch, len(utxos), parameters.max_transaction_size)
```

```python
from pyogmios.types import RollForward

async with pyogmios.AsyncClient() as client, client.chain_sync(["origin"]) as sync:
    async for event in sync:
        if isinstance(event, RollForward):
            print(event.block.height, event.block.id)
```

## Features

- **All of Ogmios v7**: the 24 ledger and network queries, chain sync, mempool monitoring, and
  transaction submission and evaluation, each a typed method.
- **Typed from the schema, checked against the chain**: about 500 Pydantic models generated from the
  Ogmios JSON schema, corrected where the schema and the server disagree, and checked against every
  block of the preview network.
- **Async and sync**: `AsyncClient` and `Client`, with the same methods.
- **Resilient**: many requests in flight on one WebSocket connection, timeouts, reconnection with
  backoff, and chain sync that resumes after a dropped connection.
- **Precise errors**: every Ogmios error code is its own exception, including each of the 74 ledger
  rules a transaction can break, with the server's details parsed.
- **A command line**: `pyogmios health`, `pyogmios query epoch`, `pyogmios follow`.
- **Python 3.11 to 3.15**, including the free-threaded builds.

## Install

```shell
pip install pyogmios
pip install "pyogmios[speedups]"   # with orjson, for faster JSON
```

You need an Ogmios v7 server connected to a `cardano-node`: see
[Getting started](https://kingpin-apps.github.io/pyogmios/latest/getting-started/).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md): uv, just, a fake Ogmios for unit tests, and a Docker devnet for
live ones.

## License

Apache-2.0.
