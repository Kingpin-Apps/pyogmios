from typing import Any, Optional, TypeVar, Callable, Dict

from nanoid import generate
from websocket import WebSocketApp

from pyogmios.connection import InteractionContext
from pyogmios.enums import Method, NetworkQuery, LedgerStateQuery
from pyogmios.models.base_model import BaseModel
from pyogmios.models.request_model import Request
from pyogmios.models.response_model import Response, QueryResponse
from pyogmios.request import send, send_request

T = TypeVar("T")


class RequestArgs(BaseModel):
    method: Method | LedgerStateQuery | NetworkQuery
    params: Optional[Dict[str, Any]] = None


class ResponseHandlerArgs(BaseModel):
    response: QueryResponse
    resolve: Callable[[Optional[Response]], None]
    reject: Callable[[Exception], None]


class ResponseArgs(BaseModel):
    handler: Callable[[ResponseHandlerArgs], T]


async def query(
    request_args: RequestArgs, context: InteractionContext
) -> QueryResponse | None:
    """
    Sends a query to the node.
    :param request_args: The request arguments.
    :param context: The interaction context to use for the query.
    :return: The query response.
    """

    async def to_send(_: WebSocketApp) -> QueryResponse | None:
        """
        Sends the query to the node.
        :param _: The websocket to use for the query.
        :return: The query response.
        """
        try:
            request_id = generate(size=5)

            request = Request.from_base_request(
                method=request_args.method,
                params=request_args.params,
                request_id=request_id,
            )

            raw_response = await send_request(request, context)
            query_response = QueryResponse.model_validate(raw_response.model_dump())

            if query_response.id != request_id:
                return

            return query_response
        except Exception as error:
            raise error

    return await send(to_send, context)
