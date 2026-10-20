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
    NonMyopicMemberRewards,
    QueryUnavailableInCurrentEra,
    StakeAddress,
)
from pyogmios.models.response_model import (
    NonMyopicMemberRewardsResponse,
    QueryResponseReflection,
)
from pyogmios.models.result_models import EraMismatchResult
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)


@pytest.mark.asyncio
async def test_non_myopic_member_rewards(mocker, fake_non_myopic_member_rewards):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.non_myopic_member_rewards.query",
        return_value=NonMyopicMemberRewardsResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=NonMyopicMemberRewards(**fake_non_myopic_member_rewards),
        ),
    )

    interaction_context = await create_interaction_context()
    client = await create_state_query_client(interaction_context)
    addr = StakeAddress("stake1uyc7gl90ufh355m9wfwhgs5dcftxvaxrp3gs9h97f4frssq5zhsq4")
    non_myopic_member_rewards = await client.non_myopic_member_rewards([addr])
    await client.shutdown()
    assert isinstance(non_myopic_member_rewards, NonMyopicMemberRewards)


@pytest.mark.asyncio
async def test_non_myopic_member_rewards_query_unavailable(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.non_myopic_member_rewards.query",
        return_value=NonMyopicMemberRewardsResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result="QueryUnavailableInCurrentEra",
        ),
    )

    # Act & Assert
    with pytest.raises(QueryUnavailableInCurrentEraError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        addr = StakeAddress("stake1uyc7gl90ufh355m9wfwhgs5dcftxvaxrp3gs9h97f4frssq5zhsq4")
        non_myopic_member_rewards = await client.non_myopic_member_rewards([addr])
        client.shutdown()
        assert isinstance(non_myopic_member_rewards, QueryUnavailableInCurrentEra)
    assert exc_info.value.query_name == "nonMyopicMemberRewards"
    assert exc_info.value.message == "QueryUnavailableInCurrentEra. nonMyopicMemberRewards"


@pytest.mark.asyncio
async def test_non_myopic_member_rewards_era_mismatch(mocker, fake_era_mismatch_result):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.non_myopic_member_rewards.query",
        return_value=NonMyopicMemberRewardsResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=EraMismatch(**fake_era_mismatch_result["eraMismatch"]),
        ),
    )

    # Act & Assert
    with pytest.raises(EraMismatchError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        addr = StakeAddress("stake1uyc7gl90ufh355m9wfwhgs5dcftxvaxrp3gs9h97f4frssq5zhsq4")
        non_myopic_member_rewards = await client.non_myopic_member_rewards([addr])
        client.shutdown()
        assert isinstance(non_myopic_member_rewards, EraMismatchResult)

    query_era = Era(fake_era_mismatch_result["eraMismatch"]["queryEra"]).value
    ledger_era = Era(fake_era_mismatch_result["eraMismatch"]["ledgerEra"]).value

    assert exc_info.value.query_era == query_era
    assert exc_info.value.ledger_era == ledger_era
    assert (
        exc_info.value.message
        == f"Era mismatch. Query from era {query_era}. Ledger is in {ledger_era}"
    )
