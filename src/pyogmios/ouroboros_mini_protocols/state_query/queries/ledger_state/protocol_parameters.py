from pyogmios.connection import InteractionContext
from pyogmios.enums import LedgerStateQuery
from pyogmios.models import (
    ProtocolParameters,
)
from pyogmios.models.response_model import (
    QueryLedgerStateProtocolParametersResponse,
)
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def protocol_parameters(
    context: InteractionContext,
) -> ProtocolParameters:
    """
    Query the protocol parameters.
    :param context: The interaction context to use for the query.
    :return: The protocol parameters.
    """
    request_args = RequestArgs(method=LedgerStateQuery.PROTOCOL_PARAMETERS)

    try:
        response = await query(request_args, context)
        query_response = QueryLedgerStateProtocolParametersResponse.model_validate(
            response.model_dump()
        )
        return query_response.result
    except Exception as error:
        raise error
