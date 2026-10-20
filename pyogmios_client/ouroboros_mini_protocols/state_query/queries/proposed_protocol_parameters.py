from typing import Dict

from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import Method
from pyogmios_client.exceptions import (
    QueryUnavailableInCurrentEraError,
    EraMismatchError,
)
from pyogmios_client.models import (
    ProtocolParametersBabbage,
    ProtocolParametersAlonzo,
    ProtocolParametersShelley,
)
from pyogmios_client.models.response_model import PoolsRankingResponse
from pyogmios_client.models.result_models import EraMismatchResult
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def proposed_protocol_parameters(
    context: InteractionContext,
) -> Dict[str, ProtocolParametersShelley] | Dict[str, ProtocolParametersAlonzo] | Dict[
    str, ProtocolParametersBabbage
] | None:
    """
    Query the proposed protocol parameters.
    :param context: The interaction context to use for the query.
    :return: The proposed protocol parameters.
    """
    request_args = RequestArgs(
        method=Method.QUERY, params={"query": "proposedProtocolParameters"}
    )

    try:
        response = await query(request_args, context)
        query_response = PoolsRankingResponse(**response.model_dump())
        result = query_response.result
        if result == "QueryUnavailableInCurrentEra":
            raise QueryUnavailableInCurrentEraError("proposedProtocolParameters")
        elif isinstance(result, EraMismatchResult):
            era_mismatch = result.eraMismatch
            raise EraMismatchError(
                str(era_mismatch.queryEra), str(era_mismatch.ledgerEra)
            )
        else:
            return result
    except Exception as error:
        raise error
