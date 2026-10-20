from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import NetworkQuery
from pyogmios_client.models import UtcTime
from pyogmios_client.models.response_model import SystemStartResponse
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def start_time(context: InteractionContext) -> UtcTime:
    """
    Query the system start time.
    :param context: The interaction context to use for the query.
    :return: The system start time.
    """
    request_args = RequestArgs(method=NetworkQuery.START_TIME)

    try:
        response = await query(request_args, context)
        query_response = SystemStartResponse.model_validate(response.model_dump())
        result = query_response.result
        return result
    except Exception as error:
        raise error
