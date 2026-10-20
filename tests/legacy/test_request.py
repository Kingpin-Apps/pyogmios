"""
Test the request module.
"""

import json
from unittest.mock import Mock

import pytest
from websocket import WebSocketApp

from pyogmios.connection import (
    InteractionContext,
    create_interaction_context,
)
from pyogmios.enums import Method
from pyogmios.exceptions import JsonwspFaultError, PyOgmiosError
from pyogmios.models.request_model import Request
from pyogmios.models.response_model import Response
from pyogmios.request import send, send_request
from tests.legacy.conftest import ConnectionFactory


@pytest.mark.asyncio
async def test_send_success():
    context = await create_interaction_context()
    test_result = {"result": "test"}

    async def to_send(_: WebSocketApp) -> dict:
        """
        Test function to send.
        """
        return test_result

    # Call the send function and capture the result
    result = await send(to_send, context)

    # Check if the result is the return value of the to_send function
    assert isinstance(result, dict)
    assert result == test_result


@pytest.mark.asyncio
async def test_send_fail():
    context = await create_interaction_context()
    test_error = "Expected error result"

    async def to_send(_: WebSocketApp) -> dict:
        """
        Test function to send.
        """
        raise PyOgmiosError(test_error)

    # Act & Assert
    with pytest.raises(PyOgmiosError) as exc_info:
        await send(to_send, context)
    assert str(exc_info.value) == test_error


class MockWebSocketApp(WebSocketApp):
    def __init__(self, recv_data):
        self.sock = Mock()
        self.sock.recv.return_value = json.dumps(recv_data)


@pytest.mark.asyncio
async def test_send_request_success():
    # Arrange
    request = Request.from_base_request(
        method_name=Method.QUERY,
        args={"query": "test-query"},
        mirror={"mirror": "test-mirror"},
    )
    context = InteractionContext(
        socket=MockWebSocketApp(
            {"type": "jsonwsp/response", "version": "1.0", "result": "test-result"}
        ),
        connection=ConnectionFactory.build(),
        after_each=lambda socket, function: function(),
    )

    # Act
    response = await send_request(request, context)

    # Assert
    assert isinstance(response, Response)
    assert response.result == "test-result"


@pytest.mark.asyncio
async def test_send_request_fault():
    # Arrange
    request = Request.from_base_request(
        method_name=Method.QUERY,
        args={"query": "test-query"},
        mirror={"mirror": "test-mirror"},
    )
    context = InteractionContext(
        socket=MockWebSocketApp(
            {
                "type": "jsonwsp/fault",
                "version": "1.0",
                "fault": {"code": 100, "string": "test-error"},
            }
        ),
        connection=ConnectionFactory.build(),
        after_each=lambda socket, function: function(),
    )

    # Act & Assert
    with pytest.raises(JsonwspFaultError) as exc_info:
        await send_request(request, context)
    assert exc_info.value.code == 100
    assert exc_info.value.message == "Jsonwsp fault error code 100. test-error"
