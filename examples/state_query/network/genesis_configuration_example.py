import asyncio

from pyogmios_client.connection import (
    create_interaction_context,
    InteractionContextOptions,
)
from pyogmios_client.enums import InteractionType, EraWithGenesis
from pyogmios_client.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)


async def main():
    """
    This will query the block height of the node through Ogmios.
    """
    interaction_context = await create_interaction_context(
        options=InteractionContextOptions(interaction_type=InteractionType.ONE_TIME)
    )
    client = await create_state_query_client(interaction_context)
    byron_genesis_config = await client.query_network.genesis_config(
        EraWithGenesis.BYRON
    )
    await client.shutdown()

    print(byron_genesis_config.model_dump_json(indent=4, by_alias=True))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
