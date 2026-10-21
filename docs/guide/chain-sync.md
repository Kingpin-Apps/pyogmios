# Following the chain

`client.chain_sync(points)` finds where your copy of the chain meets the node's, then yields every
change from there: a `RollForward` for each new block and a `RollBackward` when the node switches to
another fork.

<!-- test: run -->
```python
import pyogmios
from pyogmios.types import RollForward

with pyogmios.Client("ws://localhost:1337") as client, client.chain_sync(["origin"]) as sync:
    print("intersection:", sync.intersection, "server tip:", sync.tip)
    for count, event in enumerate(sync):
        if isinstance(event, RollForward):
            block = event.block
            print(
                block.height,
                block.id,
                len(getattr(block, "transactions", None) or []),
                "transactions",
            )
        else:
            print("rolled back to", event.point)
        if count == 20:
            break
```

With asyncio, it is `async with client.chain_sync(...) as sync:` and `async for event in sync:`.

## Where to start

`points` is a list of points the chain may share with you, most recent first: the most recent one the
node knows is the intersection.

- `["origin"]`: from the first block.
- `[client.network.tip()]`: from now on.
- The last blocks you processed, as `{"slot": ..., "id": ...}` or `pyogmios.types.Point`: to carry on
  where you stopped. Give several, in case the latest was rolled back.

If none is on the chain, entering raises `IntersectionNotFoundError`.

The first event is always a `RollBackward` to the intersection: treat it like any rollback, and
discard anything you stored after that point.

## Rollbacks

A `RollBackward` means blocks after `event.point` are no longer on the chain. Undo whatever you derived
from them. On mainnet, rollbacks are usually one or two blocks deep, and never deeper than 2160
blocks.

## Speed

Up to `pipeline` requests (50 by default) are kept in flight, so catching up from far behind runs at
thousands of blocks a second. At the tip, Ogmios answers each request when the next block arrives, so
there is no timeout on these requests.

For indexers, `raw=True` yields plain JSON instead of models, which skips parsing.

## When the connection drops

Chain sync uses its own connection. If it drops and `resume` is on (the default), it reconnects as the
client's `reconnect` policy says, then finds an intersection again from the most recent blocks it has
yielded. You then see a `RollBackward` to that block, as after any intersection, and carry on: nothing
is skipped or yielded twice. With `resume=False`, the drop raises `OgmiosConnectionError`.
