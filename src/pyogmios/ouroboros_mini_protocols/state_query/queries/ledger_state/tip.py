from pyogmios.connection import InteractionContext
from pyogmios.enums import LedgerStateQuery
from pyogmios.models import PointOrOrigin
from pyogmios.models.response_model import QueryLedgerStateTipResponse
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def tip(context: InteractionContext) -> PointOrOrigin:
    """
    Query the current ledger tip.
    :param context: The interaction context to use for the query.
    :return: The current ledger tip.
    """
    request_args = RequestArgs(method=LedgerStateQuery.TIP)

    try:
        response = await query(request_args, context)
        query_response = QueryLedgerStateTipResponse(**response.model_dump())
        result = query_response.result
        return result
    except Exception as error:
        raise error
