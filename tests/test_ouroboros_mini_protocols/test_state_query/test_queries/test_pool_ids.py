from typing import List

import pytest

from pyogmios.connection import (
    create_interaction_context,
)
from pyogmios.exceptions import (
    QueryUnavailableInCurrentEraError,
    EraMismatchError,
)
from pyogmios.models import (
    PoolId,
    QueryUnavailableInCurrentEra,
    Era,
    EraMismatch,
)
from pyogmios.models.response_model import (
    PoolIdsResponse,
    QueryResponseReflection,
)
from pyogmios.models.result_models import EraMismatchResult
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)


@pytest.mark.asyncio
async def test_pool_ids(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.pool_ids.query",
        return_value=PoolIdsResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=[
                PoolId("pool1uyc7gl90ufh355m9wfwhgs5dcftxvaxrp3gs9h97f4frssq5zhsq4")
            ],
        ),
    )

    interaction_context = await create_interaction_context()
    client = await create_state_query_client(interaction_context)
    pool_ids = await client.pool_ids()
    await client.shutdown()
    assert isinstance(pool_ids, List)
    assert isinstance(pool_ids[0], PoolId)


@pytest.mark.asyncio
async def test_pool_ids_query_unavailable(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.pool_ids.query",
        return_value=PoolIdsResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result="QueryUnavailableInCurrentEra",
        ),
    )

    # Act & Assert
    with pytest.raises(QueryUnavailableInCurrentEraError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        pool_ids = await client.pool_ids()
        client.shutdown()
        assert isinstance(pool_ids, QueryUnavailableInCurrentEra)
    assert exc_info.value.query_name == "poolIds"
    assert exc_info.value.message == "QueryUnavailableInCurrentEra. poolIds"


@pytest.mark.asyncio
async def test_pool_ids_era_mismatch(mocker, fake_era_mismatch_result):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.pool_ids.query",
        return_value=PoolIdsResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=EraMismatch(**fake_era_mismatch_result["eraMismatch"]),
        ),
    )

    # Act & Assert
    with pytest.raises(EraMismatchError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        pool_ids = await client.pool_ids()
        client.shutdown()
        assert isinstance(pool_ids, EraMismatchResult)

    query_era = Era(fake_era_mismatch_result["eraMismatch"]["queryEra"]).value
    ledger_era = Era(fake_era_mismatch_result["eraMismatch"]["ledgerEra"]).value

    assert exc_info.value.query_era == query_era
    assert exc_info.value.ledger_era == ledger_era
    assert (
        exc_info.value.message
        == f"Era mismatch. Query from era {query_era}. Ledger is in {ledger_era}"
    )
