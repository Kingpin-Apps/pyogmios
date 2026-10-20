import json
from typing import Dict

from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import UnknownResultError
from pyogmios.models.request_model import Request
from pyogmios.models.response_model import ReleaseMempoolResponse


async def release(context: InteractionContext, args: Dict) -> str:
    """
    Release a previously acquired mempool snapshot.
    :param context: The interaction context
    :param args: The arguments
    :return:
    """
    request = Request.from_base_request(
        method_name=Method.RELEASE_MEMPOOL,
        args=args,
    )
    try:
        websocket = context.socket
        websocket.send(request.model_dump_json())
        result = websocket.sock.recv()
        release_response = ReleaseMempoolResponse(**json.loads(result))
        return handle_release_response(release_response)
    except Exception as error:
        raise error


def handle_release_response(response: ReleaseMempoolResponse) -> str:
    """
    Handle the next tx response.
    :param response: The response
    :return: The result
    """
    try:
        result = response.result
        if result == "Released":
            return result
        else:
            raise UnknownResultError(result)
    except Exception as error:
        raise error
