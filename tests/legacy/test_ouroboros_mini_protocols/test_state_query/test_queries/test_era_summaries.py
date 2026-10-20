import pytest

from pyogmios.connection import (
    create_interaction_context,
)
from pyogmios.exceptions import UnknownResultError
from pyogmios.models import (
    Bound,
    Epoch,
    EraParameters,
    EraSummary,
    RelativeTime,
    SafeZone,
    SlotLength,
)
from pyogmios.models.response_model import (
    EraSummariesResponse,
    QueryResponseReflection,
)
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)


@pytest.mark.asyncio
async def test_era_summaries(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.era_summaries.query",
        return_value=EraSummariesResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=[
                EraSummary(
                    start=Bound(time=RelativeTime(123456789), slot=123456789, epoch=Epoch(500)),
                    end=Bound(time=RelativeTime(123456789), slot=123456789, epoch=Epoch(500)),
                    parameters=EraParameters(
                        epochLength=Epoch(500),
                        slotLength=SlotLength(123),
                        safeZone=SafeZone(1232),
                    ),
                )
            ],
        ),
    )

    interaction_context = await create_interaction_context()
    client = await create_state_query_client(interaction_context)
    era_summaries = await client.era_summaries()
    await client.shutdown()
    assert isinstance(era_summaries, list)
    assert isinstance(era_summaries[0], EraSummary)


@pytest.mark.asyncio
async def test_era_start_unknown_result(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.era_summaries.query",
        return_value=EraSummariesResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id")
        ),
    )

    # Act & Assert
    with pytest.raises(UnknownResultError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        era_summaries = await client.era_summaries()
        client.shutdown()

        assert isinstance(era_summaries, EraSummariesResponse)
        assert exc_info.value.result == era_summaries
        assert exc_info.value.message == f"Unknown result error:  {era_summaries}"
