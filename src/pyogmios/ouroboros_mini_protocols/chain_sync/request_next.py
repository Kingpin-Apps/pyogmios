from typing import Optional, TypeVar

from websocket import WebSocketApp

from pyogmios.models.base_model import BaseModel
from pyogmios.models.request_model import NextBlock

T = TypeVar("T")


class Options(BaseModel):
    mirror: Optional[str]


def request_next(socket: WebSocketApp, options: Options = None) -> None:
    """
    Request next.
    :param socket: The websocket
    :param options: The options
    """
    request = NextBlock.from_base(request_id=options.mirror if options else None)
    socket.send(request.model_dump_json())
