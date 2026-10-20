"""
Transaction monitor client example
"""
import asyncio

from pyogmios.connection import (
    create_interaction_context,
    InteractionContextOptions,
)
from pyogmios.enums import InteractionType
from pyogmios.models import TxId
from pyogmios.ouroboros_mini_protocols.tx_monitor.tx_monitor_client import (
    create_tx_monitor_client,
)


async def main():
    """
    This run the tx submission client and print the output.
    """
    interaction_context_options = InteractionContextOptions(
        interaction_type=InteractionType.ONE_TIME
    )
    interaction_context = await create_interaction_context(
        options=interaction_context_options
    )
    # await asyncio.sleep(1)
    # print(interaction_context.socket.sock.connected)

    tx_monitor_client = await create_tx_monitor_client(interaction_context)

    tx_hash = TxId(
        __root__="810b37cc2eb254a4cd6bde6149d08dbca8138b7ba4ec5ad996dbcb971271beb4"
    )

    print("Has Tx")
    result = await tx_monitor_client.hasTx(tx_hash)
    print(f"Transaction monitor hasTx result: {result}")
    print("Shutting down")
    await tx_monitor_client.shutdown()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
