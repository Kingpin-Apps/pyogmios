import json

from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import Method
from pyogmios_client.exceptions import UnknownResultError
from pyogmios_client.models import Slot
from pyogmios_client.models.request_model import Request
from pyogmios_client.models.response_model import AwaitAcquireResponse
from pyogmios_client.models.result_models import AwaitAcquiredResult


async def await_acquire(context: InteractionContext, args: dict) -> Slot:
    """
    Send a request to the node to acquire the tx submission protocol.
    :param context: The interaction context
    :param args: The params
    :return: The Slot
    """
    request = Request.from_base_request(
        method_name=Method.AWAIT_ACQUIRE,
        args=args,
    )
    try:
        websocket = context.socket
        websocket.send(request.model_dump_json())
        result = websocket.sock.recv()
        await_acquire_response = AwaitAcquireResponse(**json.loads(result))
        return handle_await_acquire_response(await_acquire_response)
    except Exception as error:
        raise error


def handle_await_acquire_response(response: AwaitAcquireResponse) -> Slot:
    """
    Handle the await acquire response.
    :param response: The response
    :return: The result
    """
    try:
        result = response.result
        if isinstance(result, AwaitAcquiredResult):
            return result.AwaitAcquired.slot
        else:
            raise UnknownResultError(result)
    except Exception as error:
        raise error
