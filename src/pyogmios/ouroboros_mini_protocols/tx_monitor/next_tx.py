import json
from typing import TypedDict, Union

from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import UnknownResultError
from pyogmios.models import TxId, TxAlonzo, TxBabbage, Null
from pyogmios.models.request_model import Request
from pyogmios.models.response_model import NextTxResponse


async def next_tx(
    context: InteractionContext, args: TypedDict("Args", {"fields": str})
) -> TxId | TxAlonzo | TxBabbage | Null:
    """
    Request the next mempool transaction from an acquired snapshot.
    :param context: The interaction context
    :param args: Also return full transactions
    :return:
    """
    request = Request.from_base_request(
        method_name=Method.HAS_TRANSACTION,
        args=args,
    )
    try:
        websocket = context.socket
        websocket.send(request.model_dump_json())
        result = websocket.sock.recv()
        next_tx_response = NextTxResponse(**json.loads(result))
        return handle_next_tx_response(next_tx_response)
    except Exception as error:
        raise error


def handle_next_tx_response(
    response: NextTxResponse,
) -> Union[TxId, TxAlonzo, TxBabbage, Null]:
    """
    Handle the next tx response.
    :param response: The response
    :return: The result
    """
    try:
        result = response.result
        if (
            isinstance(result, TxId)
            or isinstance(result, TxAlonzo)
            or isinstance(result, TxBabbage)
            or isinstance(result, Null)
        ):
            return result
        else:
            raise UnknownResultError(result)
    except Exception as error:
        raise error
