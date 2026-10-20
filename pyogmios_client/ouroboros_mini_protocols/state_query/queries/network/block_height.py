from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import NetworkQuery
from pyogmios_client.exceptions import QueryUnavailableInCurrentEraError
from pyogmios_client.models import BlockNoOrOrigin
from pyogmios_client.models.response_model import QueryNetworkBlockHeightResponse
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def block_height(context: InteractionContext) -> BlockNoOrOrigin:
    """
    Query the current block height.
    :param context: The interaction context to use for the query.
    :return: The current block height number or origin.
    """
    request_args = RequestArgs(method=NetworkQuery.BLOCK_HEIGHT)

    try:
        response = await query(request_args, context)
        query_response = QueryNetworkBlockHeightResponse(**response.model_dump())
        result = query_response.result
        if result.root.root == "QueryUnavailableInCurrentEra":
            raise QueryUnavailableInCurrentEraError(request_args.method.value)
        return result
    except Exception as error:
        raise error
