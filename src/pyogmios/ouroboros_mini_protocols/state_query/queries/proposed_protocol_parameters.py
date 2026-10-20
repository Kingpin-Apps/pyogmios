from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import (
    EraMismatchError,
    QueryUnavailableInCurrentEraError,
)
from pyogmios.models import (
    ProtocolParametersAlonzo,
    ProtocolParametersBabbage,
    ProtocolParametersShelley,
)
from pyogmios.models.response_model import PoolsRankingResponse
from pyogmios.models.result_models import EraMismatchResult
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    RequestArgs,
    query,
)


async def proposed_protocol_parameters(
    context: InteractionContext,
) -> (
    dict[str, ProtocolParametersShelley]
    | dict[str, ProtocolParametersAlonzo]
    | dict[str, ProtocolParametersBabbage]
    | None
):
    """
    Query the proposed protocol parameters.
    :param context: The interaction context to use for the query.
    :return: The proposed protocol parameters.
    """
    request_args = RequestArgs(method=Method.QUERY, params={"query": "proposedProtocolParameters"})

    try:
        response = await query(request_args, context)
        query_response = PoolsRankingResponse(**response.model_dump())
        result = query_response.result
        if result == "QueryUnavailableInCurrentEra":
            raise QueryUnavailableInCurrentEraError("proposedProtocolParameters")
        elif isinstance(result, EraMismatchResult):
            era_mismatch = result.eraMismatch
            raise EraMismatchError(str(era_mismatch.queryEra), str(era_mismatch.ledgerEra))
        else:
            return result
    except Exception as error:
        raise error
