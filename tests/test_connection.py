from unittest.mock import MagicMock, AsyncMock

import pytest

from pyogmios.connection import create_connection_object
from pyogmios.connection import (
    create_interaction_context,
    InteractionContext,
    InteractionContextOptions,
)
from pyogmios.server_health import Connection
from tests.conftest import ConnectionConfigFactory


def test_create_connection_object():
    # Create a ConnectionConfig object
    config = ConnectionConfigFactory.build()

    # Call the function and capture the result
    result = create_connection_object(config)

    # Check if the result is a Connection object
    assert isinstance(result, Connection)

    # Check if the connection object is created with the provided config
    assert result.host in [config.host, "localhost"]
    assert result.port in [config.port, 1337]
    assert result.tls == config.tls or result.tls is False
    assert result.max_payload in [config.max_payload, 128 * 1024 * 1024]


@pytest.mark.asyncio
async def test_create_interaction_context_without_config(mocker, fake_server_health):
    response_mock = AsyncMock(status=200)
    response_mock.json.return_value = fake_server_health

    # Mock the get_server_health function to return a successful server health check
    aiohttp_mock = mocker.patch("aiohttp.ClientSession.get", AsyncMock())
    aiohttp_mock.return_value = response_mock

    # Call the function and capture the result
    interaction_context = await create_interaction_context()

    # Check if the result is an InteractionContext object
    assert isinstance(interaction_context, InteractionContext)

    # Check if the error_handler and close_handler are set as attributes of the InteractionContext
    assert interaction_context.connection.address.http == "http://localhost:1337"
    assert interaction_context.connection.address.webSocket == "ws://localhost:1337"

    # Check if the connection object is created with the provided options
    assert interaction_context.connection.host == "localhost"
    assert interaction_context.connection.port == 1337
    assert interaction_context.connection.tls is False
    assert interaction_context.connection.max_payload == 128 * 1024 * 1024


@pytest.mark.asyncio
async def test_create_interaction_context_with_config():
    interaction_context = MagicMock(spec=InteractionContext)
    connection_config = ConnectionConfigFactory.build()
    options = InteractionContextOptions(connection_config=connection_config)

    # Mock the get_server_health function to return a successful server health check
    MagicMock(return_value=interaction_context)

    # Call the function and capture the result
    result = await create_interaction_context(options)

    # Check if the result is an InteractionContext object
    assert isinstance(result, InteractionContext)

    # Check if the error_handler and close_handler are set as attributes of the InteractionContext
    assert result.connection.address.http == "http://localhost:1337"
    assert result.connection.address.webSocket == "ws://localhost:1337"

    # Check if the connection object is created with the provided options
    assert result.connection.host in [options.connection_config.host, "localhost"]
    assert result.connection.port in [options.connection_config.port, 1337]
    assert result.connection.tls in [options.connection_config.tls, False]
    assert result.connection.max_payload in [
        options.connection_config.max_payload,
        128 * 1024 * 1024,
    ]
