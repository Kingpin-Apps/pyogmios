from typing import List

from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import Method
from pyogmios_client.exceptions import (
    QueryUnavailableInCurrentEraError,
    EraMismatchError,
    UnknownResultError,
)
from pyogmios_client.models import EraMismatch, Address, TxIn, Utxo
from pyogmios_client.models.response_model import UtxoResponse
from pyogmios_client.models.result_models import EraMismatchResult
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


def is_era_mismatch(response: UtxoResponse) -> bool:
    if isinstance(response, EraMismatch):
        return response.eraMismatch is not None


def is_utxo_list(response: UtxoResponse) -> bool:
    result = response.result
    if isinstance(result, Utxo):
        return True
    return False


async def utxo(
    context: InteractionContext, filters: List[Address] | List[TxIn]
) -> Utxo:
    """
    Query the utxo for the given stake key or transaction hashes.
    :param context: The interaction context to use for the query.
    :param filters: The stake key or transaction hashes to query.
    :return: The Unspent Transaction Output."""
    request_args = RequestArgs(
        method=Method.QUERY,
        params={
            "query": {"utxo": filters}
            if isinstance(filters, List) and len(filters) > 0
            else "utxo"
        },
    )

    try:
        response = await query(request_args, context)
        query_response = UtxoResponse(**response.model_dump())
        result = query_response.result
        if result == "QueryUnavailableInCurrentEra":
            raise QueryUnavailableInCurrentEraError("utxo")
        elif is_utxo_list(query_response):
            return result
        elif isinstance(result, EraMismatchResult):
            era_mismatch = result.eraMismatch
            raise EraMismatchError(
                str(era_mismatch.queryEra), str(era_mismatch.ledgerEra)
            )
        else:
            raise UnknownResultError(response)
    except Exception as error:
        raise error
