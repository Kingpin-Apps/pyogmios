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
    PoolRank,
    PoolsRanking,
    QueryUnavailableInCurrentEra,
)
from pyogmios.models.response_model import (
    PoolsRankingResponse,
    QueryResponseReflection,
)
from pyogmios.models.result_models import EraMismatchResult
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)


@pytest.mark.asyncio
async def test_pool_ranking(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.pools_ranking.query",
        return_value=PoolsRankingResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=PoolsRanking(
                {
                    "pool1uyc7gl90ufh355m9wfwhgs5dcftxvaxrp3gs9h97f4frssq5zhsq4": PoolRank(
                        score=100,
                        estimatedHitRate=100,
                    ),
                }
            ),
        ),
    )

    interaction_context = await create_interaction_context()
    client = await create_state_query_client(interaction_context)
    pools_ranking = await client.pools_ranking()
    await client.shutdown()
    assert isinstance(pools_ranking, PoolsRanking)


@pytest.mark.asyncio
async def test_pool_ranking_query_unavailable(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.pools_ranking.query",
        return_value=PoolsRankingResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result="QueryUnavailableInCurrentEra",
        ),
    )

    # Act & Assert
    with pytest.raises(QueryUnavailableInCurrentEraError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        pools_ranking = await client.pools_ranking()
        client.shutdown()
        assert isinstance(pools_ranking, QueryUnavailableInCurrentEra)
    assert exc_info.value.query_name == "poolsRanking"
    assert exc_info.value.message == "QueryUnavailableInCurrentEra. poolsRanking"


@pytest.mark.asyncio
async def test_pool_ranking_era_mismatch(mocker, fake_era_mismatch_result):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.pools_ranking.query",
        return_value=PoolsRankingResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=EraMismatch(**fake_era_mismatch_result["eraMismatch"]),
        ),
    )

    # Act & Assert
    with pytest.raises(EraMismatchError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        pools_ranking = await client.pools_ranking()
        client.shutdown()
        assert isinstance(pools_ranking, EraMismatchResult)

    query_era = Era(fake_era_mismatch_result["eraMismatch"]["queryEra"]).value
    ledger_era = Era(fake_era_mismatch_result["eraMismatch"]["ledgerEra"]).value

    assert exc_info.value.query_era == query_era
    assert exc_info.value.ledger_era == ledger_era
    assert (
        exc_info.value.message
        == f"Era mismatch. Query from era {query_era}. Ledger is in {ledger_era}"
    )
