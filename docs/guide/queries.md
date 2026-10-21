# Queries

Ogmios has two families of queries, and pyogmios groups them the same way:

- **`client.ledger_state`**: the ledger as the node sees it (`queryLedgerState/*`): UTxOs, protocol
  parameters, stake pools, governance, rewards.
- **`client.network`**: the chain and its configuration (`queryNetwork/*`): tip, block height,
  start time, genesis configuration.

<!-- test: run -->
```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    parameters = client.ledger_state.protocol_parameters()
    print(
        "min fee:",
        parameters.min_fee_coefficient,
        "per byte +",
        parameters.min_fee_constant.ada.lovelace,
    )
    pools = client.ledger_state.stake_pools()
    print(len(pools), "stake pools")
    print("treasury:", client.ledger_state.treasury_and_reserves().treasury.ada.lovelace)
    print("start time:", client.network.start_time())
```

Every query returns a typed result (see [Types](types.md)) and takes an optional `timeout=` in
seconds.

## Parameters

Queries that take parameters have keyword arguments. Where a parameter holds objects, you can pass the
model from `pyogmios.types` or a plain dict, with Python (`output_references`) or Ogmios
(`outputReferences`) field names. Parameters are checked before anything is sent: a typo raises a
Pydantic `ValidationError`.

```python
utxos = client.ledger_state.utxo(addresses=["addr_test1..."])
utxos = client.ledger_state.utxo(
    output_references=[{"transaction": {"id": "a1b2..."}, "index": 0}],
)
pool = client.ledger_state.stake_pools(stake_pools=[{"id": "pool1..."}], include_stake=True)
conway = client.network.genesis_configuration(era="conway")
```

Leaving optional parameters out queries everything: `client.ledger_state.utxo()` returns the
**whole** UTxO set, which is very large on mainnet. Prefer a filter.

## Every query

<!-- queries:table -->

## The ledger at a point

Ledger queries answer for the node's current tip. To query the ledger as it was at a recent point, see
[The ledger at a point](ledger-state-at.md).

## Errors

A query the ledger cannot answer raises a [`LedgerStateQueryError`](errors.md): for example
`UnavailableInCurrentEraError` for a Conway-only query on an older era.
