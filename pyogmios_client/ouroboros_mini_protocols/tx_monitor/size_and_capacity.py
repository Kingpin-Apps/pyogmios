import json
from typing import Dict

from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import Method
from pyogmios_client.exceptions import UnknownResultError
from pyogmios_client.models import MempoolSizeAndCapacity
from pyogmios_client.models.request_model import Request
from pyogmios_client.models.response_model import SizeAndCapacityResponse


async def size_and_capacity(context: InteractionContext, args: Dict) -> str:
    """
    Get size and capacities of the mempool (acquired snapshot).
    :param context: The interaction context
    :param args: The arguments
    :return: The result
    """
    request = Request.from_base_request(
        method_name=Method.SIZE_OF_MEMPOOL,
        args=args,
    )
    try:
        websocket = context.socket
        websocket.send(request.model_dump_json())
        result = websocket.sock.recv()
        release_response = SizeAndCapacityResponse(**json.loads(result))
        return handle_size_and_capacity_response(release_response)
    except Exception as error:
        raise error


def handle_size_and_capacity_response(response: SizeAndCapacityResponse) -> str:
    """
    Handle the size and capacity response.
    :param response: The response
    :return: The result
    """
    try:
        result = response.result
        if isinstance(result, MempoolSizeAndCapacity):
            return result
        else:
            raise UnknownResultError(result)
    except Exception as error:
        raise error
