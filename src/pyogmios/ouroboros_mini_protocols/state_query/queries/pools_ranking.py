from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import (
    EraMismatchError,
    QueryUnavailableInCurrentEraError,
    UnknownResultError,
)
from pyogmios.models import (
    EraMismatch,
    PoolsRanking,
    QueryUnavailableInCurrentEra,
)
from pyogmios.models.response_model import PoolsRankingResponse
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    RequestArgs,
    query,
)


async def pools_ranking(context: InteractionContext) -> PoolsRanking:
    """
    Query the pools ranking.
    :param context: The interaction context to use for the query.
    :return: The pools ranking.
    """
    request_args = RequestArgs(method=Method.QUERY, params={"query": "poolsRanking"})

    try:
        response = await query(request_args, context)
        query_response = PoolsRankingResponse(**response.model_dump())
        result = query_response.result
        if isinstance(result, QueryUnavailableInCurrentEra):
            raise QueryUnavailableInCurrentEraError("poolsRanking")
        elif isinstance(result, EraMismatch):
            raise EraMismatchError(result.queryEra.value, result.ledgerEra.value)
        elif isinstance(result, PoolsRanking):
            return result
        else:
            raise UnknownResultError(response)
    except Exception as error:
        raise error
