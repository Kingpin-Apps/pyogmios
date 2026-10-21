# Getting started

## Install

```shell
pip install pyogmios
```

Or with [uv](https://docs.astral.sh/uv/): `uv add pyogmios`. For faster JSON, add the `speedups` extra
(`pip install "pyogmios[speedups]"`, which installs orjson; not available on the free-threaded builds).

pyogmios needs Python 3.11 or newer.

## Run Ogmios

pyogmios talks to an [Ogmios](https://ogmios.dev) v7 server connected to a `cardano-node`. Any of these
works:

- **Your own node.** Install Ogmios ([releases](https://github.com/CardanoSolutions/ogmios/releases),
  or `brew install cardanosolutions/formulas/ogmios` on macOS) and point it at your node's socket:
  `ogmios --node-socket /path/to/node.socket --node-config /path/to/config.json`.
- **Docker.** The `cardanosolutions/cardano-node-ogmios` image runs a node and Ogmios together, for
  mainnet, preprod or preview.
- **A local devnet.** The pyogmios repository has one that starts in seconds: see
  [Testing with the devnet](contributing.md#the-devnet).
- **A hosted provider.** Pass its URL, and any API key header with `headers=`.

Ogmios listens on `ws://localhost:1337` by default; `curl localhost:1337/health` shows its version,
network and sync progress.

## Your first queries

=== "Sync"

    <!-- test: run -->
    ```python
    import pyogmios

    with pyogmios.Client("ws://localhost:1337") as client:
        print("connected to", client.server_health.version, "on", client.server_health.network)
        print("epoch", client.ledger_state.epoch())
        print("tip", client.network.tip())
        for summary in client.ledger_state.era_summaries():
            print(summary.start.epoch, summary.parameters.slot_length)
    ```

=== "Async"

    <!-- test: run -->
    ```python
    import asyncio

    import pyogmios


    async def main() -> None:
        async with pyogmios.AsyncClient("ws://localhost:1337") as client:
            epoch, tip, height = await asyncio.gather(
                client.ledger_state.epoch(),
                client.network.tip(),
                client.network.block_height(),
            )
            print(f"epoch {epoch}, block {height}, tip {tip}")


    asyncio.run(main())
    ```

The client checks on connect that the server runs Ogmios 7 (see
[version check](guide/clients.md#the-version-check)). Results are typed models from
[`pyogmios.types`](guide/types.md): an editor knows that `client.ledger_state.protocol_parameters()`
returns `ProtocolParameters`, with fields such as `max_transaction_size` and `min_fee_coefficient`.

## From the command line

```shell
pyogmios health
pyogmios query epoch
pyogmios follow --from tip --headers
```

See [Command line](guide/cli.md).

## Next

- [Clients and connections](guide/clients.md): URLs, timeouts, reconnecting and health.
- [Queries](guide/queries.md): every query and its parameters.
- [Following the chain](guide/chain-sync.md), [the mempool](guide/mempool.md) and
  [transactions](guide/transactions.md).
