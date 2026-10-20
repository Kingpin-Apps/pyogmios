from pyogmios.connection import InteractionContext
from pyogmios.enums import LedgerStateQuery
from pyogmios.exceptions import (
    EraMismatchError,
    QueryUnavailableInCurrentEraError,
    UnknownResultError,
)
from pyogmios.models import Epoch, QueryUnavailableInCurrentEra
from pyogmios.models.response_model import QueryLedgerStateEpochResponse
from pyogmios.models.result_models import EraMismatchResult
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    RequestArgs,
    query,
)


async def epoch(context: InteractionContext) -> Epoch:
    """
    Query the current epoch.
    :param context: The interaction context to use for the query.
    :return: The current epoch.
    """
    request_args = RequestArgs(method=LedgerStateQuery.EPOCH)

    try:
        response = await query(request_args, context)
        query_response = QueryLedgerStateEpochResponse(**response.model_dump())
        result = query_response.result
        if isinstance(result, QueryUnavailableInCurrentEra):
            raise QueryUnavailableInCurrentEraError(request_args.method.value)
        elif isinstance(result, Epoch):
            return result
        elif isinstance(result, EraMismatchResult):
            era_mismatch = result.eraMismatch
            raise EraMismatchError(era_mismatch.queryEra.value, era_mismatch.ledgerEra.value)
        else:
            raise UnknownResultError(response)
    except Exception as error:
        raise error
