from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import (
    EraMismatchError,
    QueryUnavailableInCurrentEraError,
    UnknownResultError,
)
from pyogmios.models import PoolDistribution
from pyogmios.models.response_model import StakeDistributionResponse
from pyogmios.models.result_models import EraMismatchResult
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    RequestArgs,
    query,
)


def is_stake_distribution(response: StakeDistributionResponse) -> bool:
    """
    Check if the response is a stake distribution.
    :param response: The response to check.
    :return: True if the response is a stake distribution, False otherwise.
    """
    return isinstance(response.result, PoolDistribution)


async def stake_distribution(context: InteractionContext) -> PoolDistribution:
    """
    Query the stake distribution.
    :param context: The interaction context to use for the query.
    :return: The stake distribution.
    """
    request_args = RequestArgs(method=Method.QUERY, params={"query": "stakeDistribution"})

    try:
        response = await query(request_args, context)
        query_response = StakeDistributionResponse(**response.model_dump())
        result = query_response.result
        if result == "QueryUnavailableInCurrentEra":
            raise QueryUnavailableInCurrentEraError("stakeDistribution")
        elif is_stake_distribution(query_response):
            return result
        elif isinstance(result, EraMismatchResult):
            era_mismatch = result.eraMismatch
            raise EraMismatchError(str(era_mismatch.queryEra), str(era_mismatch.ledgerEra))
        else:
            raise UnknownResultError(response)
    except Exception as error:
        raise error
