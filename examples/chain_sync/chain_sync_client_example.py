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
    interaction_context = await create_interaction_context(
        options=interaction_context_options
    )
    # await asyncio.sleep(1)
    # print(interaction_context.socket.sock.connected)

    def roll_backward_callback(
        roll_backward: RollBackward, callback: Callable[[], None]
    ):
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
    print("start sync")
    await chain_sync_client.start_sync([Origin.origin], 0)
    print("sync started....sleeping for 20 seconds")
    await asyncio.sleep(20)
    print("shutting down")
    await chain_sync_client.shutdown()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
