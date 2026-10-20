from __future__ import annotations

from typing import List, Callable, Coroutine

from websocket import WebSocketApp

from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import UnknownResultError
from pyogmios.models import (
    RollBackward,
    RollForward,
    PointOrOrigin,
    Any,
)
from pyogmios.models.base_model import BaseModel
from pyogmios.models.response_model import RequestNextResponse, Response
from pyogmios.models.result_models import (
    IntersectionFound,
    RollForwardResult,
    RollBackwardResult,
)
from pyogmios.ouroboros_mini_protocols.chain_sync.find_intersect import (
    find_intersect,
    create_point_from_current_tip,
)
from pyogmios.ouroboros_mini_protocols.chain_sync.request_next import (
    request_next,
)
from pyogmios.utils.queue import Queue
from pyogmios.utils.socket_utils import ensure_socket_is_open


class Options(BaseModel):
    sequential: bool


class ChainSyncMessageHandlers(BaseModel):
    roll_backward: Callable[[RollBackward, Callable[[], None]], None]
    roll_forward: Callable[[RollForward, Callable[[], None]], None]


class ChainSyncClient(BaseModel):
    context: InteractionContext
    shutdown: Callable[[], Coroutine[Any, Any, None]]
    start_sync: Callable[
        [List[PointOrOrigin], int], Coroutine[Any, Any, IntersectionFound]
    ]


async def create_chain_sync_client(
    context: InteractionContext,
    message_handlers: ChainSyncMessageHandlers,
    options: Options = None,
) -> ChainSyncClient:
    """
    Create a chain sync client.
    :param context: The interaction context
    :param message_handlers: The message handlers
    :param options: The options
    :return: The chain sync client
    """
    websocket_app = context.socket

    try:

        def message_handler(response: RequestNextResponse) -> None:
            """
            Handle the response.
            :param response: The response
            """
            if isinstance(response.result, RollBackwardResult):
                message_handlers.roll_backward(
                    response.result.roll_backward, lambda: request_next(websocket_app)
                )
            elif isinstance(response.result, RollForwardResult):
                message_handlers.roll_forward(
                    response.result.roll_forward, lambda: request_next(websocket_app)
                )
            else:
                raise UnknownResultError(response.result)

        def response_handler(response: RequestNextResponse) -> None:
            """
            Handle the response.
            :param response:
            :return:
            """
            if options is None:
                return message_handler(response)
            return (
                Queue().promise_push(message_handler(response))
                if options.sequential is True
                else message_handler(response)
            )

        def on_message(_: WebSocketApp, message: str) -> None:
            """
            Handle the message.
            :param _:
            :param message:
            """
            response = Response.model_validate_json(message)
            if response.methodname is Method.NEXT_BLOCK:
                try:
                    response_handler(RequestNextResponse.model_validate_json(message))
                except Exception as err:
                    print(err)
            elif response.methodname is Method.FIND_INTERSECTION:
                request_next(websocket_app)

        websocket_app.on_message = on_message

        async def shutdown() -> None:
            """
            Shutdown the chain sync client.
            """
            try:
                await ensure_socket_is_open(websocket_app)
                websocket_app.close()
            except Exception as error:
                print(error)
            else:
                print("Shutting down Chain Sync Client...")

        async def start_sync(
            points: List[PointOrOrigin], in_flight: int
        ) -> IntersectionFound:
            """
            Start the sync.
            :param points: The points
            :param in_flight: The in flight
            :return: The intersection found
            """
            try:
                intersection = await find_intersect(
                    context, points or [await create_point_from_current_tip(context)]
                )
                await ensure_socket_is_open(websocket_app)
                for _ in range(in_flight or 100):
                    request_next(websocket_app)
            except Exception as error:
                print(error)
            else:
                return intersection

    except Exception:
        pass
    else:
        return ChainSyncClient(
            context=context, shutdown=shutdown, start_sync=start_sync
        )
