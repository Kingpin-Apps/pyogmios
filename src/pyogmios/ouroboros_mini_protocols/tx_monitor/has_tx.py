import json

from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import UnknownResultError
from pyogmios.models import TxId
from pyogmios.models.request_model import Request
from pyogmios.models.response_model import HasTxResponse


async def has_tx(context: InteractionContext, tx_id: TxId) -> bool:
    """
    Ask whether a given transaction is present in the acquired mempool snapshot.
    :param context: The interaction context
    :param tx_id: The Transaction id
    :return:
    """
    request = Request.from_base_request(
        method_name=Method.HAS_TRANSACTION,
        args={"id": tx_id},
    )
    try:
        websocket = context.socket
        websocket.send(request.model_dump_json())
        result = websocket.sock.recv()
        has_tx_response = HasTxResponse(**json.loads(result))
        return handle_has_tx_response(has_tx_response)
    except Exception as error:
        raise error


def handle_has_tx_response(response: HasTxResponse) -> bool:
    """
    Handle the has tx response.
    :param response: The response
    :return: The result
    """
    try:
        result = response.result
        if isinstance(result, bool):
            return result
        else:
            raise UnknownResultError(result)
    except Exception as error:
        raise error
