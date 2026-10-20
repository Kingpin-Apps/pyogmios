import pytest

from pyogmios.connection import (
    create_interaction_context,
)
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    StateQueryClient,
    create_state_query_client,
)


@pytest.mark.asyncio
async def test_create_state_query_client():
    interaction_context = await create_interaction_context()

    client = await create_state_query_client(interaction_context)
    assert isinstance(client, StateQueryClient)
