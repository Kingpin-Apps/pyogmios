# pyogmios

A Python client for [Ogmios](https://ogmios.dev) **v7**, the lightweight JSON-RPC bridge to
`cardano-node`. Query the ledger, follow the chain, watch the mempool and submit transactions, with
every request and answer typed.

<!-- test: run -->
```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    epoch = client.ledger_state.epoch()
    tip = client.network.tip()
    parameters = client.ledger_state.protocol_parameters()
    print(f"epoch {epoch}, tip {tip}, max tx size {parameters.max_transaction_size.bytes} bytes")
```

## Why pyogmios

- **All of Ogmios v7.** All 24 ledger and network queries, chain sync, mempool monitoring, transaction
  submission and evaluation. Each query is a typed method: `client.ledger_state.utxo(addresses=[...])`.
- **Typed from the schema, checked against the chain.** The 500 or so result and error types are
  generated from the Ogmios JSON schema, corrected where the schema and the server disagree, and checked
  against every block of the preview network and a local devnet. Results are Pydantic models.
- **Async and sync.** `AsyncClient` for asyncio; `Client` for everything else, with the same methods.
- **Built for long-running programs.** Many requests in flight on one WebSocket connection,
  keep-alive, timeouts, reconnection with backoff, and chain sync that resumes by itself after a
  dropped connection.
- **Errors you can catch precisely.** Every Ogmios error code is its own exception, from
  `IntersectionNotFoundError` to the 74 ledger rules a transaction can break, such as
  `ValueNotConservedError`, with the server's details parsed.
- **A command line** for quick checks: `pyogmios tip`, `pyogmios query epoch`, `pyogmios follow`.
- **Python 3.11 to 3.15**, including the free-threaded builds. Apache-2.0.

## Where next

- [Getting started](getting-started.md): install, connect, and run your first queries.
- [Guide](guide/clients.md): each part of the library in depth.
- [Recipes](recipes.md): complete programs for common tasks.
- [API reference](reference/clients.md): every class and method.
