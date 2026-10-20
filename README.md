# PyOgmios

Python implementation of Ogmios Client

> [!NOTE]
> This branch is the in-progress 1.0 rewrite for **Ogmios v7**. The import name is now `pyogmios` (it was
> `pyogmios_client`), and the usage examples below still show the 0.7 API. The released 0.7.x on PyPI speaks
> Ogmios v5 only.

## What is PyOgmios?

**PyOgmios** is based on [Ogmios](https://github.com/CardanoSolutions/ogmios) JSON/RPC lightweight bridge interface
for [Cardano Node](https://github.com/input-output-hk/cardano-node/)
by [Matthias Benkort](https://github.com/KtorZ). <br>
It offers a **WebSocket API** that enables local clients to
speak [Ouroboros' mini-protocols](https://input-output-hk.github.io/ouroboros-network/) via **JSON/RPC**.

## Overview

**PyOgmios** is a Python library that can be used to convert Python Objects into their **Ogmios** Requests **JSON/RPC**
representation. It can also be used to convert **Ogmios JSON/RPC** Responses to their equivalent Python objects. <br>
The Python library allows asynchronous communication with **Ogmios** Server by interacting with a Websocket client
connection. <br>

### Background

The standard Ogmios interface uses a websocket and Json WSP messages. While this is good for exposing the node's
information to a lot of different programming environments, there is a lot of boilerplate code to write in each language
to convert json wsp messages into usable objects. This is where **PyOgmios** comes in for the Python language.

The api is broken up into using 4 different logical client types: **StateQuery**, **TxSubmit**, **TxMonitor**, and
**ChainSync**.

## Features

- Asynchronous messaging using Python objects
- Transaction submission with enhanced error messages
- Transaction Evaluation
- Structured Python Objects logging
- Full ledger state query support:

| Query                          | Result                                                                           |     Supported      |
|--------------------------------|----------------------------------------------------------------------------------|:------------------:|
| `block_height`                 | The chain's highest block number.                                                | :heavy_check_mark: |
| `chain_tip`                    | The chain's current tip.                                                         | :heavy_check_mark: |
| `current_epoch`                | The current epoch of the ledger.                                                 | :heavy_check_mark: |
| `current_protocol_parameters`  | The current protocol parameters.                                                 | :heavy_check_mark: |
| `delegations_and_rewards`      | Current delegation settings and rewards of given reward accounts.                | :heavy_check_mark: |
| `era_start`                    | The information regarding the beginning of the current era.                      | :heavy_check_mark: |
| `era_summaries`                | Era bounds and slotting parameters details, required for proper slot arithmetic. | :heavy_check_mark: |
| `genesis_config`               | Get a compact version of the era's genesis configuration.                        | :heavy_check_mark: |
| `ledger_tip`                   | The most recent block tip known of the ledger.                                   | :heavy_check_mark: |
| `non_myopic_member_rewards`    | Non-myopic member rewards for each pool. Used in ranking.                        | :heavy_check_mark: |
| `pool_ids`                     | The list of all pool identifiers currently registered and active.                | :heavy_check_mark: |
| `pool_parameters`              | Stake pool parameters submitted with registration certificates.                  | :heavy_check_mark: |
| `pools_ranking`                | Retrieve stake pools ranking (a.k.a desirability).                               | :heavy_check_mark: |
| `proposed_protocol_parameters` | The last update proposal w.r.t. protocol parameters, if any.                     | :heavy_check_mark: |
| `rewards_provenance`           | Get details about rewards calculation for the ongoing epoch.                     | :heavy_check_mark: |
| `stake_distribution`           | Distribution of the stake across all known stake pools.                          | :heavy_check_mark: |
| `system_start`                 | The chain's start time (UTC).                                                    | :heavy_check_mark: |
| `utxo`                         | Current UTXO, possibly filtered by output reference.                             | :heavy_check_mark: |

# Getting Started

```shell
pip install pyogmios
```

## Setup

In order to use **PyOgmios**, you will need to have a running instance of Ogmios pointed at an active instance of
cardano-node. Please refer to the Ogmios documentation for setup instructions.

On the **PyOgmios** side, all you will need is the ip/dns name of the Ogmios server as well as the port it is running
on (
default: 1337).

### Hosted Dandelion's instances, by [Gimbalabs](https://gimbalabs.com/).

| Network | URL                                        |
|---------|--------------------------------------------|
| Mainnet | `wss://ogmios-api.mainnet.dandelion.link/` |
| Testnet | `wss://ogmios-api.testnet.dandelion.link/` |

## Usage

Below, you will find a few example usages of the **PyOgmios** api. To find more exhaustive examples, refer to the
example code
in this repository.

When you are done using a **PyOgmios** client, you should clean up and call the `shutdown()` method explicitly, OR you
can initialize the `InteractionContext` with `InteractionType.ONE_TIME` to ensure clean up happens automatically. This
latter approach is what we will use in the examples.

All methods must be called from inside a Coroutine Context. The client methods will suspend until data returns from the
server, or an exception is thrown. Many calls can be made through **PyOgmios** using the same Client object. Only clean
it up once you are done with it, or it has thrown an error. In the case of errors, it is best to create a new instance
of the Client, so it can re-connect.

### StateQuery

The **StateQuery** client is used for querying the current (or past) state of the node and blockchain. In most cases,
the api will automatically acquire the tip of the blockchain. You should not need to explicitly call `acquire(point)`
unless you have advanced needs.

#### ChainTip Example:

```python
import asyncio

from pyogmios.connection import (
    create_interaction_context,
    InteractionContextOptions,
)
from pyogmios.enums import InteractionType
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)


async def main():
    """
    This will query the chain tip of the node through Ogmios.
    """
    interaction_context_options = InteractionContextOptions(
        interaction_type=InteractionType.ONE_TIME
    )
    interaction_context = await create_interaction_context(options=interaction_context_options)
    client = await create_state_query_client(interaction_context)
    chain_tip = await client.tip()
    # await client.shutdown()
    print(chain_tip)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
```

### ChainSync

```python
import asyncio
from typing import Callable

from pyogmios.connection import (
    create_interaction_context,
    InteractionContextOptions,
)
from pyogmios.enums import InteractionType, Origin
from pyogmios.models import RollBackward, RollForward
from pyogmios.ouroboros_mini_protocols.chain_sync.chain_sync_client import (
    ChainSyncMessageHandlers,
    create_chain_sync_client,
)


async def main():
    """
    This run the chain sync client and print the output.
    """
    interaction_context_options = InteractionContextOptions(
        interaction_type=InteractionType.LONG_RUNNING
    )
    interaction_context = await create_interaction_context(options=interaction_context_options)
    await asyncio.sleep(1)
    print(interaction_context.socket.sock.connected)

    def roll_backward_callback(roll_backward: RollBackward, callback: Callable[[], None]):
        """
        Roll backward callback
        :param roll_backward: The roll backward result
        :param callback: The request next callback
        """
        print(f"Roll backward: {roll_backward}")
        callback()

    def roll_forward_callback(roll_forward: RollForward, callback: Callable[[], None]):
        """
        Roll forward callback
        :param roll_forward: The roll forward result
        :param callback: The request next callback
        """
        print(f"Roll forward: {roll_forward}")
        callback()

    chain_sync_message_handlers = ChainSyncMessageHandlers(
        roll_backward=roll_backward_callback, roll_forward=roll_forward_callback
    )

    chain_sync_client = await create_chain_sync_client(
        interaction_context, chain_sync_message_handlers
    )
    await chain_sync_client.start_sync([Origin.origin], 0)
    await asyncio.sleep(10)
    await chain_sync_client.shutdown()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
```

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
```

Run `uv run pre-commit install` once to lint and format on commit and check commit messages
([Conventional Commits](https://www.conventionalcommits.org/)). Releases are cut with `just bump`, and pushing the
`v*` tag publishes to PyPI.
