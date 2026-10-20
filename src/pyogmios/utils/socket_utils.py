"""
Socket utilities.

This module contains utilities for working with sockets.
"""

from websocket import WebSocketApp

from pyogmios.exceptions import WebSocketClosedError


async def ensure_socket_is_open(websocket_app: WebSocketApp) -> None:
    """
    Ensure the socket is open.
    :param websocket_app: The websocket app
    """
    if not websocket_app.sock.connected:
        raise WebSocketClosedError()
