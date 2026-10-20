import asyncio

from pyogmios.connection import (
    InteractionContextOptions,
    create_connection_object,
)
from pyogmios.enums import InteractionType
from pyogmios.server_health import get_server_health, Options


async def main():
    """
    This will get the Ogmios server health.
    """
    interaction_context_options = InteractionContextOptions(
        interaction_type=InteractionType.ONE_TIME
    )

    connection = create_connection_object(interaction_context_options.connection_config)

    health = await get_server_health(Options(connection=connection))
    print(health.model_dump_json(indent=4))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
