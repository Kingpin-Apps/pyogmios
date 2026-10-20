from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import NetworkQuery
from pyogmios_client.exceptions import QueryUnavailableInCurrentEraError
from pyogmios_client.models import PointOrOrigin, QueryUnavailableInCurrentEra
from pyogmios_client.models.response_model import QueryNetworkTipResponse
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def tip(context: InteractionContext) -> PointOrOrigin:
    """
    Query the current chain tip.
    :param context: The interaction context to use for the query.
    :return: The current chain tip.
    """
    request_args = RequestArgs(method=NetworkQuery.TIP)

    try:
        response = await query(request_args, context)
        query_response = QueryNetworkTipResponse(**response.model_dump())
        result = query_response.result
        if isinstance(result, QueryUnavailableInCurrentEra):
            raise QueryUnavailableInCurrentEraError(request_args.method.value)
        return result
    except Exception as error:
        raise error
