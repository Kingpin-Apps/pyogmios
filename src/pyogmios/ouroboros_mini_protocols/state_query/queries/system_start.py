from pyogmios.connection import InteractionContext
from pyogmios.enums import NetworkQuery
from pyogmios.models import UtcTime
from pyogmios.models.response_model import SystemStartResponse
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    RequestArgs,
    query,
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
