# The mempool

The mempool holds transactions the node has accepted but not yet put in a block. pyogmios reads it two
ways, each on its own connection.

## Every new transaction

`client.mempool()` yields each transaction as it enters the mempool, once, then waits for more:

```python
with client.mempool() as transactions:
    for transaction_id in transactions:
        print("new:", transaction_id)
```

With `full=True` it yields whole transactions (`pyogmios.types.Transaction`) instead of ids.

## A snapshot

`client.mempool_snapshot()` takes a snapshot of the mempool, to look at as it was then:

<!-- test: run -->
```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client, client.mempool_snapshot() as snapshot:
    size = snapshot.size()
    print(
        f"slot {snapshot.slot}: {size.transactions.count} transactions,"
        f" {size.current_size.bytes} of {size.max_capacity.bytes} bytes"
    )
    for transaction_id in snapshot:
        print(transaction_id)
```

- `size()`: the number of transactions, their total size and the mempool's capacity.
- `has(transaction_id)`: whether the snapshot contains a transaction.
- `next()`, or iterating: its transactions, one at a time (`None` at the end).
- `acquire()`: take a new snapshot. After the first, this waits until the mempool has changed.
