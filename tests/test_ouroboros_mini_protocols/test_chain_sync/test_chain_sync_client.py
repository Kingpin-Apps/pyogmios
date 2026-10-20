from unittest.mock import MagicMock

import pytest

from pyogmios.connection import (
    create_interaction_context,
)
from pyogmios.ouroboros_mini_protocols.chain_sync.chain_sync_client import (
    create_chain_sync_client,
    ChainSyncMessageHandlers,
    ChainSyncClient,
)


# @pytest.fixture
# def context():
#     return InteractionContext()
#
#
# @pytest.fixture
# def message_handlers():
#     return ChainSyncMessageHandlers()
#
#
# @pytest.fixture
# def options():
#     return InteractionContextOptions(sequential=True)
#
#
# @pytest.fixture
# def response():
#     return RequestNextResponse(methodname=Method.NEXT_BLOCK)


@pytest.mark.asyncio
async def test_create_chain_sync_client(mocker):
    chain_sync_message_handlers = MagicMock(spec=ChainSyncMessageHandlers)

    interaction_context = await create_interaction_context()
    client = await create_chain_sync_client(
        interaction_context, chain_sync_message_handlers
    )
    assert isinstance(client, ChainSyncClient)
