import pytest

from pyogmios.connection import (
    create_interaction_context,
)
from pyogmios.enums import Method
from pyogmios.exceptions import PyOgmiosError
from pyogmios.models.response_model import Response
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    RequestArgs,
    query,
)


@pytest.mark.asyncio
async def test_query_success(mocker, fake_query_response):
    # Arrange
    request_args = RequestArgs(
        method=Method.QUERY,
        params={"query": "test-query"},
        mirror={"mirror": "test-mirror", "requestId": "test-request-id"},
    )
    context = await create_interaction_context()

    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.query.send_request",
        return_value=Response(**fake_query_response),
    )

    # Act
    result = await query(request_args, context)

    # Assert
    assert isinstance(result, Response)


@pytest.mark.asyncio
async def test_query_error(mocker):
    # Arrange
    request_args = RequestArgs(
        method=Method.QUERY,
        params={"query": "test-query"},
        mirror={"mirror": "test-mirror", "requestId": "test-request-id"},
    )
    context = await create_interaction_context()

    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.query.send_request",
        side_effect=PyOgmiosError("test-error"),
    )

    # Act & Assert
    with pytest.raises(PyOgmiosError) as exc_info:
        await query(request_args, context)
    assert str(exc_info.value) == "test-error"
