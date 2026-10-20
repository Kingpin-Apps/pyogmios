from pyogmios.connection import InteractionContext
from pyogmios.enums import LedgerStateQuery
from pyogmios.models import EraSummary
from pyogmios.models.response_model import EraSummariesResponse
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    RequestArgs,
    query,
)


async def era_summaries(context: InteractionContext) -> list[EraSummary]:
    """
    Query the era summaries.
    :param context: The interaction context to use for the query.
    :return: The era summaries.
    """
    request_args = RequestArgs(method=LedgerStateQuery.ERA_SUMMARIES)

    try:
        response = await query(request_args, context)
        query_response = EraSummariesResponse.model_validate(response.model_dump())
        return query_response.result
    except Exception as error:
        raise error
