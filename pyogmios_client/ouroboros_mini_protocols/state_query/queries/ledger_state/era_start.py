from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import LedgerStateQuery
from pyogmios_client.models import Bound
from pyogmios_client.models.response_model import QueryLedgerStateEraStartResponse
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def era_start(context: InteractionContext) -> Bound:
    """
    Query the start of the current era.
    :param context: The interaction context to use for the query.
    :return: The start of the current era.
    """
    request_args = RequestArgs(method=LedgerStateQuery.ERA_START)

    try:
        response = await query(request_args, context)
        query_response = QueryLedgerStateEraStartResponse.model_validate(
            response.model_dump()
        )
        return query_response.result
    except Exception as error:
        raise error
