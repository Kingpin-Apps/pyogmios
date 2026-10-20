import asyncio

from pyogmios.connection import (
    InteractionContextOptions,
    create_interaction_context,
)
from pyogmios.enums import InteractionType
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)


async def main():
    """
    This will query the epoch of the node through Ogmios.
    """
    interaction_context = await create_interaction_context(
        options=InteractionContextOptions(interaction_type=InteractionType.ONE_TIME)
    )

    client = await create_state_query_client(interaction_context)
    epoch = await client.query_ledger_state.epoch()
    await client.shutdown()

    print(f"Current epoch: {epoch.root}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
