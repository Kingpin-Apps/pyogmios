from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import Method
from pyogmios_client.exceptions import (
    QueryUnavailableInCurrentEraError,
    EraMismatchError,
)
from pyogmios_client.models import (
    RewardsProvenanceNew,
    QueryUnavailableInCurrentEra,
    EraMismatch,
)
from pyogmios_client.models.response_model import RewardsProvenanceNewResponse
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def rewards_provenance_new(context: InteractionContext) -> RewardsProvenanceNew:
    """
    Query the rewards provenance new.
    :param context: The interaction context to use for the query.
    :return: The new rewards provenance.
    """
    request_args = RequestArgs(
        method=Method.QUERY, params={"query": "rewardsProvenance'"}
    )

    try:
        response = await query(request_args, context)
        query_response = RewardsProvenanceNewResponse(**response.model_dump())
        result = query_response.result
        if isinstance(result, QueryUnavailableInCurrentEra):
            raise QueryUnavailableInCurrentEraError("rewardsProvenance'")
        elif isinstance(result, RewardsProvenanceNew):
            return result
        elif isinstance(result, EraMismatch):
            raise EraMismatchError(result.queryEra.value, result.ledgerEra.value)
        else:
            return result
    except Exception as error:
        raise error
