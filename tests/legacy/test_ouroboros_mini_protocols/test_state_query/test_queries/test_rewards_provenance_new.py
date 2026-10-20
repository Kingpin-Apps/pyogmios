import pytest

from pyogmios.connection import (
    create_interaction_context,
)
from pyogmios.exceptions import (
    EraMismatchError,
    QueryUnavailableInCurrentEraError,
)
from pyogmios.models import (
    Era,
    EraMismatch,
    QueryUnavailableInCurrentEra,
    RewardsProvenanceNew,
)
from pyogmios.models.response_model import (
    QueryResponseReflection,
    RewardsProvenanceNewResponse,
)
from pyogmios.models.result_models import EraMismatchResult
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)
from tests.legacy.conftest import RewardsProvenanceNewFactory


@pytest.mark.asyncio
async def test_rewards_provenance_new(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.rewards_provenance_new.query",
        return_value=RewardsProvenanceNewResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=RewardsProvenanceNewFactory.build(),
        ),
    )

    interaction_context = await create_interaction_context()
    client = await create_state_query_client(interaction_context)
    rewards_provenance_new = await client.rewards_provenance_new()
    await client.shutdown()
    assert isinstance(rewards_provenance_new, RewardsProvenanceNew)


@pytest.mark.asyncio
async def test_rewards_provenance_new_query_unavailable(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.rewards_provenance_new.query",
        return_value=RewardsProvenanceNewResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result="QueryUnavailableInCurrentEra",
        ),
    )

    # Act & Assert
    with pytest.raises(QueryUnavailableInCurrentEraError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        rewards_provenance_new = await client.rewards_provenance_new()
        client.shutdown()
        assert isinstance(rewards_provenance_new, QueryUnavailableInCurrentEra)
    assert exc_info.value.query_name == "rewardsProvenance'"
    assert exc_info.value.message == "QueryUnavailableInCurrentEra. rewardsProvenance'"


@pytest.mark.asyncio
async def test_rewards_provenance_new_era_mismatch(mocker, fake_era_mismatch_result):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.rewards_provenance_new.query",
        return_value=RewardsProvenanceNewResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=EraMismatch(**fake_era_mismatch_result["eraMismatch"]),
        ),
    )

    # Act & Assert
    with pytest.raises(EraMismatchError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        rewards_provenance_new = await client.rewards_provenance_new()
        client.shutdown()
        assert isinstance(rewards_provenance_new, EraMismatchResult)

    query_era = Era(fake_era_mismatch_result["eraMismatch"]["queryEra"]).value
    ledger_era = Era(fake_era_mismatch_result["eraMismatch"]["ledgerEra"]).value

    assert exc_info.value.query_era == query_era
    assert exc_info.value.ledger_era == ledger_era
    assert (
        exc_info.value.message
        == f"Era mismatch. Query from era {query_era}. Ledger is in {ledger_era}"
    )
