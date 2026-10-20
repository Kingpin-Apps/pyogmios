"""
This module contains the send function.

The send function is used to send requests and call the after each function.
"""
import json
import logging
from typing import Callable, TypeVar

from websocket import WebSocketApp, WebSocketConnectionClosedException

from pyogmios.connection import InteractionContext
from pyogmios.models.base_request_response_model import BaseErrorResponse
from pyogmios.models.request_model import Request
from pyogmios.models.response_model import Response

T = TypeVar("T")


async def send(to_send: Callable[[WebSocketApp], T], context: InteractionContext) -> T:
    """
    Sends a request to the node.
    :param to_send: The function to send the request.
    :param context: The interaction context to use for the request.
    :return: The response.
    """
    socket = context.socket
    after_each = context.after_each

    try:
        result = await to_send(socket)
    except Exception as error:
        raise error
    else:
        after_each(socket, lambda: logging.debug(result))
        return result


async def send_request(request: Request, context: InteractionContext) -> Response:
    """
    Sends a request to Ogmios. Raises an exception if the response is a fault or the connection is closed.
    :param request: The request to send.
    :param context: The interaction context to use for the request.
    :return: The response.
    """
    try:
        websocket = context.socket
        websocket.send(request.model_dump_json(exclude_none=True))
        result = websocket.sock.recv()

        result_json = json.loads(result)
        if "error" in result_json.keys():
            return BaseErrorResponse.model_validate(result_json)
        response = Response(**json.loads(result))
        # TODO: Handle errors :class:`BaseErrorResponse`
        # if response.type is Type.JSONWSP_FAULT:
        #     raise JsonwspFaultError(response.fault["code"], response.fault["string"])
        return response
    except WebSocketConnectionClosedException as error:
        raise error
