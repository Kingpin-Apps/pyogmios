import pytest

from pyogmios_client.connection import (
    create_interaction_context,
)
from pyogmios_client.exceptions import (
    EraMismatchError,
    QueryUnavailableInCurrentEraError,
)
from pyogmios_client.models import (
    RewardAccountSummaries,
    Era,
    QueryUnavailableInCurrentEra,
)
from pyogmios_client.models.response_model import (
    QueryLedgerStateRewardAccountSummariesResponse,
    QueryResponseReflection,
)
from pyogmios_client.models.result_models import EraMismatchResult
from pyogmios_client.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)


@pytest.mark.asyncio
async def test_delegations_and_rewards(
    mocker, fake_delegations_and_rewards_by_accounts
):
    mocker.patch(
        "pyogmios_client.ouroboros_mini_protocols.state_query.queries.reward_account_summaries.query",
        return_value=QueryLedgerStateRewardAccountSummariesResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=fake_delegations_and_rewards_by_accounts,
        ),
    )

    interaction_context = await create_interaction_context()

    client = await create_state_query_client(interaction_context)
    delegations_and_rewards = await client.reward_account_summaries(
        ["stake1uyc7gl90ufh355m9wfwhgs5dcftxvaxrp3gs9h97f4frssq5zhsq4"]
    )
    await client.shutdown()
    assert isinstance(delegations_and_rewards, RewardAccountSummaries)


@pytest.mark.asyncio
async def test_delegations_and_rewards_era_mismatch(mocker, fake_era_mismatch_result):
    mocker.patch(
        "pyogmios_client.ouroboros_mini_protocols.state_query.queries.reward_account_summaries.query",
        return_value=QueryLedgerStateRewardAccountSummariesResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=EraMismatchResult(**fake_era_mismatch_result),
        ),
    )

    # Act & Assert
    with pytest.raises(EraMismatchError) as exc_info:
        interaction_context = await create_interaction_context()

        client = await create_state_query_client(interaction_context)
        delegations_and_rewards = await client.reward_account_summaries(
            ["stake1uyc7gl90ufh355m9wfwhgs5dcftxvaxrp3gs9h97f4frssq5zhsq4"]
        )
        client.shutdown()

        assert isinstance(delegations_and_rewards, EraMismatchResult)

    query_era = Era(fake_era_mismatch_result["eraMismatch"]["queryEra"]).value
    ledger_era = Era(fake_era_mismatch_result["eraMismatch"]["ledgerEra"]).value

    assert exc_info.value.query_era == query_era
    assert exc_info.value.ledger_era == ledger_era
    assert (
        exc_info.value.message
        == f"Era mismatch. Query from era {query_era}. Ledger is in {ledger_era}"
    )


@pytest.mark.asyncio
async def test_delegations_and_rewards_query_unavailable(mocker):
    mocker.patch(
        "pyogmios_client.ouroboros_mini_protocols.state_query.queries.reward_account_summaries.query",
        return_value=QueryLedgerStateRewardAccountSummariesResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result="QueryUnavailableInCurrentEra",
        ),
    )

    # Act & Assert
    with pytest.raises(QueryUnavailableInCurrentEraError) as exc_info:
        interaction_context = await create_interaction_context()

        client = await create_state_query_client(interaction_context)
        delegations_and_rewards = await client.reward_account_summaries(
            ["stake1uyc7gl90ufh355m9wfwhgs5dcftxvaxrp3gs9h97f4frssq5zhsq4"]
        )
        client.shutdown()
        assert isinstance(delegations_and_rewards, QueryUnavailableInCurrentEra)
    assert exc_info.value.query_name == "delegationsAndRewards"
    assert (
        exc_info.value.message == "QueryUnavailableInCurrentEra. delegationsAndRewards"
    )
