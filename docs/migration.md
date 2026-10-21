# Migrating from 0.7

pyogmios 1.0 is a new library for Ogmios 7. Version 0.7 spoke Ogmios 5, whose protocol Ogmios 6 and 7
replaced, so there is no compatibility layer: code written for 0.7 needs rewriting. It usually gets
much shorter.

## What changed

| 0.7 | 1.0 |
|---|---|
| `import pyogmios_client` | `import pyogmios` |
| Ogmios 5 (`jsonwsp`) | Ogmios 7 (JSON-RPC 2.0) |
| Python 3.10+ | Python 3.11+ |
| `create_interaction_context()`, then a client per protocol | one `Client` or `AsyncClient` |
| async only | `AsyncClient` and `Client` (sync) |
| callbacks for chain sync | `async for event in client.chain_sync(points)` |
| v5 queries (`current_epoch`, `chain_tip`, `pool_ids`...) | v7 queries (`client.ledger_state.epoch()`, `client.network.tip()`, `client.ledger_state.stake_pools()`...) |

## Side by side

=== "0.7"

    ```python
    from pyogmios_client.connection import create_interaction_context, InteractionContextOptions
    from pyogmios_client.enums import InteractionType
    from pyogmios_client.ouroboros_mini_protocols.state_query.state_query_client import (
        create_state_query_client,
    )


    async def main():
        options = InteractionContextOptions(interaction_type=InteractionType.ONE_TIME)
        context = await create_interaction_context(options=options)
        client = await create_state_query_client(context)
        print(await client.chain_tip())
    ```

=== "1.0"

    ```python
    import pyogmios


    async def main():
        async with pyogmios.AsyncClient("ws://localhost:1337") as client:
            print(await client.network.tip())
    ```

## Queries

Ogmios 6 renamed and regrouped the queries. The closest 1.0 equivalents of 0.7's:

| 0.7 | 1.0 |
|---|---|
| `block_height` | `client.network.block_height()` |
| `chain_tip` | `client.network.tip()` |
| `ledger_tip` | `client.ledger_state.tip()` |
| `current_epoch` | `client.ledger_state.epoch()` |
| `current_protocol_parameters` | `client.ledger_state.protocol_parameters()` |
| `proposed_protocol_parameters` | removed by Ogmios 6.14; see `client.ledger_state.governance_proposals()` |
| `delegations_and_rewards` | `client.ledger_state.reward_account_summaries(keys=[...])` |
| `era_start`, `era_summaries` | `client.ledger_state.era_start()`, `client.ledger_state.era_summaries()` |
| `genesis_config` | `client.network.genesis_configuration(era=...)` |
| `non_myopic_member_rewards` | `client.ledger_state.projected_rewards(stake=[...])` |
| `pool_ids`, `pool_parameters` | `client.ledger_state.stake_pools()`, filtered with `stake_pools=[...]` |
| `pools_ranking` | `client.ledger_state.projected_rewards(...)` |
| `rewards_provenance` | `client.ledger_state.rewards_provenance()` or `stake_pools_performances()` |
| `stake_distribution` | `client.ledger_state.live_stake_distribution()` |
| `system_start` | `client.network.start_time()` |
| `utxo` | `client.ledger_state.utxo(addresses=[...])` or `utxo(output_references=[...])` |

## Transactions and the mempool

- `submit_tx` is `client.submit_transaction(cbor)`, and each ledger rejection is its own exception.
- `evaluate_tx` is `client.evaluate_transaction(cbor, additional_utxo=...)`.
- The transaction monitor is `client.mempool()` (every new transaction) and `client.mempool_snapshot()`.
