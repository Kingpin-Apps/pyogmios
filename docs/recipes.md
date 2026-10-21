# Recipes

Complete programs for common tasks. Change the URL to your Ogmios server.

## Print new blocks as they arrive

```python
import asyncio

import pyogmios
from pyogmios.types import RollForward


async def main() -> None:
    async with pyogmios.AsyncClient("ws://localhost:1337") as client:
        tip = await client.network.tip()
        async with client.chain_sync([tip]) as sync:
            async for event in sync:
                if isinstance(event, RollForward):
                    block = event.block
                    count = len(getattr(block, "transactions", None) or [])
                    print(f"block {block.height} at slot {block.slot}: {count} transactions")
                else:
                    print(f"rolled back to {event.point}")


asyncio.run(main())
```

## Watch an address for payments

Follow the chain and report every output paid to an address. Outputs in a block that is later rolled
back should be forgotten; this example only prints.

```python
import asyncio

import pyogmios
from pyogmios.types import RollForward

ADDRESS = "addr_test1..."


async def main() -> None:
    async with pyogmios.AsyncClient("ws://localhost:1337") as client:
        async with client.chain_sync([await client.network.tip()]) as sync:
            async for event in sync:
                if not isinstance(event, RollForward):
                    continue
                for transaction in getattr(event.block, "transactions", None) or []:
                    for index, output in enumerate(transaction.outputs):
                        if output.address == ADDRESS:
                            ada = output.value.ada.lovelace / 1_000_000
                            print(f"{ada} ada in {transaction.id}#{index}")


asyncio.run(main())
```

## Wait for a transaction to be on chain

Submit, then follow the chain from the tip at submission until a block contains the transaction.

```python
import asyncio

import pyogmios
from pyogmios.types import RollForward


async def submit_and_wait(client: pyogmios.AsyncClient, cbor: bytes, timeout: float = 300) -> int:
    """Submit a signed transaction and return the height of the block that includes it."""
    tip = await client.network.tip()
    transaction_id = (await client.submit_transaction(cbor)).transaction.id
    async with asyncio.timeout(timeout), client.chain_sync([tip]) as sync:
        async for event in sync:
            if isinstance(event, RollForward):
                ids = {t.id for t in getattr(event.block, "transactions", None) or []}
                if transaction_id in ids:
                    return event.block.height
    raise AssertionError("unreachable")
```

For more certainty, wait for a few more blocks on top of it before treating it as final.

## Carry on from where a program stopped

Save the points of the last blocks you processed, and start from them next time. Several points
protect against the latest having been rolled back while you were away.

```python
import json
from pathlib import Path

import pyogmios
from pyogmios.types import RollForward

CHECKPOINT = Path("checkpoint.json")

points = json.loads(CHECKPOINT.read_text()) if CHECKPOINT.exists() else ["origin"]
with pyogmios.Client("ws://localhost:1337") as client, client.chain_sync(points) as sync:
    recent: list[dict] = []
    for event in sync:
        if isinstance(event, RollForward) and getattr(event.block, "slot", None) is not None:
            recent = [{"slot": event.block.slot, "id": event.block.id}, *recent][:10]
            CHECKPOINT.write_text(json.dumps(recent))  # most recent first
```

## Slots and times

Convert a slot to a time with the era summaries and the network's start time:

<!-- test: run -->
```python
from datetime import timedelta

import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    start = client.network.start_time()
    summaries = client.ledger_state.era_summaries()
    tip = client.network.tip()


def slot_time(slot: int):
    for era in summaries:
        if era.end is None or slot < era.end.slot:
            seconds = (
                era.start.time.seconds
                + (slot - era.start.slot) * era.parameters.slot_length.milliseconds / 1000
            )
            return start + timedelta(seconds=seconds)
    raise ValueError(f"slot {slot} is beyond the known eras")


print(f"the tip, slot {tip.slot}, was produced at {slot_time(tip.slot):%Y-%m-%d %H:%M:%S %Z}")
```

Era summaries only reach a little into the future (the "safe zone"), because a hard fork could change
the slot length.

## Governance at a glance

<!-- test: run -->
```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    for proposal in client.ledger_state.governance_proposals():
        votes = {}
        for vote in proposal.votes:
            votes[vote.vote] = votes.get(vote.vote, 0) + 1
        print(proposal.action.type, "until epoch", proposal.until.epoch, votes)
    for representative in client.ledger_state.delegate_representatives():
        print(
            representative.type,
            getattr(representative, "id", ""),
            getattr(representative, "stake", ""),
        )
    committee = client.ledger_state.constitutional_committee()
    if committee is not None:
        print(len(committee.members), "committee members, quorum", committee.quorum)
```

## Is the node ready?

<!-- test: run -->
```python
import pyogmios

with pyogmios.Client("ws://localhost:1337") as client:
    health = client.health()
    if not health.is_synced:
        print(f"still syncing: {health.network_synchronization:.2%}")
    else:
        print(f"{health.network} is synced, era {health.current_era}, epoch {health.current_epoch}")
```

## Using pyogmios with pycardano

To build and sign transactions with [pycardano](https://pycardano.readthedocs.io) against an Ogmios
node, use the Ogmios chain context from [pccontext](https://pccontext.readthedocs.io).
