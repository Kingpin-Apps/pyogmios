# The ledger at a point

`client.ledger_state_at(point)` acquires the ledger as it was at `point`. Every ledger query on it then
answers for that point, however far the chain has moved on:

<!-- test: run -->
```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    tip = client.network.tip()
    with client.ledger_state_at(tip) as ledger:
        epoch = ledger.epoch()
        parameters = ledger.protocol_parameters()
        pools = ledger.stake_pools()
    print(f"at {tip}: epoch {epoch}, {len(pools)} pools, protocol {parameters.version.major}")
```

With asyncio, it is `async with client.ledger_state_at(point) as ledger:` and `await ledger.epoch()`.

Use it when several answers must agree with each other: queries on `client.ledger_state` each answer
for the tip at that moment, and the tip can move between two of them.

## How far back

Nodes keep only the recent ledger states, roughly the last 2160 blocks (about 12 hours on mainnet).
Acquiring an older point, or one not on the chain, raises `AcquireLedgerStateError`. An acquired state
can also become too old while you hold it; queries then raise `AcquiredExpiredError`: acquire it again.

## Its own connection

In Ogmios, an acquired ledger state applies to every query on the connection. So `ledger_state_at`
opens a connection of its own, and the client's other queries keep answering for the tip. When the
block ends, the state is released and the connection closed.
