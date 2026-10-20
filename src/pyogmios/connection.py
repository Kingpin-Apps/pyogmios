"""
Create a connection to the server.

This module contains the classes and default functions to create a connection to the server.
"""
import logging
import threading
from typing import Optional, Callable

import websocket
from websocket import WebSocketApp, enableTrace

from pyogmios.enums import InteractionType
from pyogmios.exceptions import ServerNotReady, WebSocketClosedError
from pyogmios.models.base_model import BaseModel
from pyogmios.server_health import (
    get_server_health,
    ConnectionConfig,
    Connection,
    Options as ServerHealthOptions,
)


class InteractionContext(BaseModel):
    """
    Interaction context model class
    """

    connection: Connection
    socket: WebSocketApp
    after_each: Callable[[WebSocketApp, Callable[[], None]], None]
    log_level: Optional[str] = "DEBUG"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logging.basicConfig(format="%(levelname)s - %(message)s")
        logging.getLogger().setLevel(logging.getLevelName(self.log_level.upper()))


class InteractionContextOptions(BaseModel):
    """
    Interaction context options model class
    """

    connection_config: Optional[ConnectionConfig] = None
    interaction_type: Optional[InteractionType] = None
    log_level: Optional[str] = "DEBUG"


def default_error_handler(_: WebSocketApp, error: Exception):
    """
    Default error handler.
    :param _: The websocket app
    :param error: The exception
    """
    logging.error(error)
    raise error


def default_close_handler(_: WebSocketApp, close_status_code: int, close_msg: str):
    """
    Default close handler.
    :param _: The websocket app
    :param close_status_code: The close status code
    :param close_msg: The close message
    """
    if close_status_code or close_msg:
        print(f"Closed with code: {close_status_code} and reason: {close_msg}")
    else:
        print("Closed without code or reason")


def create_connection_object(config: ConnectionConfig = None) -> Connection:
    """
    Creates a connection object.
    :param config: The connection config
    :return: The :class:`Connection` object
    """
    host = config.host or "localhost" if config else "localhost"
    port = config.port or 1337 if config else 1337
    tls = config.tls or False if config else False
    max_payload = (
        config.max_payload or 128 * 1024 * 1024 if config else 128 * 1024 * 1024
    )

    host_and_port = f"{host}:{port}"

    connection = {
        "host": host,
        "port": port,
        "tls": tls,
        "max_payload": max_payload,
        "address": {
            "http": f"https://{host_and_port}" if tls else f"http://{host_and_port}",
            "webSocket": f"wss://{host_and_port}" if tls else f"ws://{host_and_port}",
        },
    }
    return Connection(**connection)


async def create_interaction_context(
    error_handler: Optional[Callable[[WebSocketApp, Exception], None]] = None,
    close_handler: Optional[Callable[[WebSocketApp, int, str], None]] = None,
    options: Optional[InteractionContextOptions] = None,
) -> InteractionContext | None:
    """
    Create an interaction context.
    :param error_handler: The error handler
    :param close_handler: The close handler
    :param options: The :class:`InteractionContextOptions` object
    :return: The :class:`InteractionContext` object
    """
    interaction_context_options = options or InteractionContextOptions(
        interaction_type=InteractionType.ONE_TIME
    )

    connection = create_connection_object(interaction_context_options.connection_config)

    health = await get_server_health(ServerHealthOptions(connection=connection))

    def close_on_completion() -> bool:
        """
        Whether to close the socket on completion.
        :return:
        """
        return interaction_context_options.interaction_type is InteractionType.ONE_TIME

    try:
        if health.last_tip_update is None:
            raise ServerNotReady(health)

        # Create an event to signal when the websocket is opened
        websocket_opened = threading.Event()

        def after_each(ws_app: WebSocketApp, callback: Callable[[], None]):
            """
            Callback to run after each.
            :param ws_app: The websocket app
            :param callback: The callback
            """
            if close_on_completion():
                callback()
                ws_app.close(
                    status=websocket.STATUS_NORMAL, reason="Closed on completion"
                )
            else:
                callback()

        def on_initial_error(ws_app: WebSocketApp, error: Exception):
            """
            On initial error.
            :param ws_app: The websocket app
            :param error: The error
            """
            logging.error(error)
            ws_app.close()
            raise error

        def on_message_handler(ws_app, message):
            """
            On message.
            :param ws_app: The websocket app
            :param message: The message
            """
            if message == "error":
                on_initial_error(ws_app, Exception(message))
            elif message == "close":
                raise WebSocketClosedError()

        def on_open_handler(_: WebSocketApp):
            """
            On open.
            :param _: The websocket app
            """
            websocket_opened.set()

        if interaction_context_options.log_level == "INFO":
            enableTrace(True)

        websocket_app = WebSocketApp(
            connection.address.webSocket,
            on_message=on_message_handler,
            on_open=on_open_handler,
            on_close=close_handler or default_close_handler,
            on_error=error_handler or default_error_handler,
        )

        websocket_thread = threading.Thread(target=websocket_app.run_forever)
        websocket_thread.daemon = True
        websocket_thread.start()

        if not websocket_opened.is_set():
            websocket_opened.wait()

        return InteractionContext(
            connection=connection,
            socket=websocket_app,
            after_each=after_each,
            log_level=interaction_context_options.log_level,
        )

    except ServerNotReady as e:
        logging.error(e)
        return None
