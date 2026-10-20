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
    This will query the reward account summaries of the node through Ogmios.
    """
    interaction_context = await create_interaction_context(
        options=InteractionContextOptions(interaction_type=InteractionType.ONE_TIME)
    )

    client = await create_state_query_client(interaction_context)
    reward_account_summaries = await client.query_ledger_state.reward_account_summaries(
        keys=["stake_test1uqwcz0754wwpuhm6xhdpda6u9enyahaj5ynlc9ay5l4mlms4pyqyg"]
    )
    await client.shutdown()

    print(reward_account_summaries.model_dump_json(indent=4, by_alias=True))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
