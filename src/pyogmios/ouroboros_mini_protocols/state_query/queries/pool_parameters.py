from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import (
    EraMismatchError,
    QueryUnavailableInCurrentEraError,
    UnknownResultError,
)
from pyogmios.models import (
    EraMismatch,
    PoolId,
    PoolParameters,
    QueryUnavailableInCurrentEra,
)
from pyogmios.models.response_model import PoolParametersResponse
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    RequestArgs,
    query,
)


async def pool_parameters(
    context: InteractionContext, pools: list[PoolId]
) -> dict[str, PoolParameters]:
    """
    Query the pool parameters.
    :param context: The interaction context to use for the query.
    :param pools: The list of pool ids to query.
    :return: The pool parameters.
    """
    request_args = RequestArgs(method=Method.QUERY, params={"query": {"poolParameters": pools}})

    try:
        response = await query(request_args, context)
        query_response = PoolParametersResponse(**response.model_dump())
        result = query_response.result
        if isinstance(result, QueryUnavailableInCurrentEra):
            raise QueryUnavailableInCurrentEraError("poolParameters")
        elif isinstance(result, EraMismatch):
            raise EraMismatchError(result.queryEra.value, result.ledgerEra.value)
        elif isinstance(result, dict):
            return result
        else:
            raise UnknownResultError(response)
    except Exception as error:
        raise error
