from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import (
    QueryUnavailableInCurrentEraError,
    EraMismatchError,
)
from pyogmios.models import (
    RewardsProvenance,
    QueryUnavailableInCurrentEra,
    EraMismatch,
)
from pyogmios.models.response_model import RewardsProvenanceResponse
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def rewards_provenance(context: InteractionContext) -> RewardsProvenance:
    """
    Query the rewards provenance.
    :param context: The interaction context to use for the query.
    :return: The rewards provenance.
    """
    request_args = RequestArgs(
        method=Method.QUERY, params={"query": "rewardsProvenance"}
    )

    try:
        response = await query(request_args, context)
        query_response = RewardsProvenanceResponse(**response.model_dump())
        result = query_response.result
        if isinstance(result, QueryUnavailableInCurrentEra):
            raise QueryUnavailableInCurrentEraError("rewardsProvenance")
        elif isinstance(result, RewardsProvenance):
            return result
        elif isinstance(result, EraMismatch):
            raise EraMismatchError(result.queryEra.value, result.ledgerEra.value)
        else:
            return result
    except Exception as error:
        raise error
