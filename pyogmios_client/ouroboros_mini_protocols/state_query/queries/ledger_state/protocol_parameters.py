from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import LedgerStateQuery
from pyogmios_client.models import (
    ProtocolParameters,
)
from pyogmios_client.models.response_model import (
    QueryLedgerStateProtocolParametersResponse,
)
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
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
