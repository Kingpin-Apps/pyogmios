from typing import Callable, Coroutine, Any, Dict

from pyogmios.connection import InteractionContext
from pyogmios.models import BaseModel, Slot, TxId, TxAlonzo, TxBabbage, Null
from pyogmios.ouroboros_mini_protocols.tx_monitor.await_acquire import (
    await_acquire,
)
from pyogmios.ouroboros_mini_protocols.tx_monitor.has_tx import has_tx
from pyogmios.ouroboros_mini_protocols.tx_monitor.next_tx import next_tx
from pyogmios.ouroboros_mini_protocols.tx_monitor.release import release
from pyogmios.ouroboros_mini_protocols.tx_monitor.size_and_capacity import (
    size_and_capacity,
)
from pyogmios.utils.socket_utils import ensure_socket_is_open


class TxMonitorClient(BaseModel):
    context: InteractionContext
    awaitAcquire: Callable[[dict], Coroutine[Any, Any, Slot]]
    hasTx: Callable[[TxId], Coroutine[Any, Any, bool]]
    nextTx: Callable[[Dict], Coroutine[Any, Any, TxId | TxAlonzo | TxBabbage | Null]]
    release: Callable[[Dict], Coroutine[Any, Any, str]]
    sizeAndCapacity: Callable[[Dict], Coroutine[Any, Any, str]]
    shutdown: Callable[[], Coroutine[Any, Any, None]]


async def create_tx_monitor_client(context: InteractionContext) -> TxMonitorClient:
    """
    Creates a tx monitor client.
    :param context: The interaction context
    :return: The tx monitor client
    """
    websocket_app = context.socket

    async def default_await_acquire(args: dict) -> Slot:
        """
        Await acquire.
        :return: The slot
        """
        await ensure_socket_is_open(context.socket)
        return await await_acquire(context, args)

    async def default_has_tx(tx_id: TxId) -> bool:
        """
        Has tx.
        :return: True if it has tx
        """
        await ensure_socket_is_open(context.socket)
        return await has_tx(context, tx_id)

    async def default_next_tx(args: Dict) -> TxId | TxAlonzo | TxBabbage | Null:
        """
        Next tx.
        :return: The tx id
        """
        await ensure_socket_is_open(context.socket)
        return await next_tx(context, args)

    async def default_release(args: Dict) -> str:
        """
        Release.
        :return: The release
        """
        await ensure_socket_is_open(context.socket)
        return await release(context, args)

    async def default_size_and_capacity(args: Dict) -> str:
        """
        Size and capacity.
        :return: The size and capacity
        """
        await ensure_socket_is_open(context.socket)
        return await size_and_capacity(context, args)

    async def default_shutdown() -> None:
        """
        Shutdown the tx monitor client.
        :return: None
        """
        try:
            await ensure_socket_is_open(websocket_app)
            websocket_app.close()
        except Exception as err:
            print(err)
        else:
            print("Shutting down TxMonitor Client...")

    return TxMonitorClient(
        context=context,
        awaitAcquire=default_await_acquire,
        hasTx=default_has_tx,
        nextTx=default_next_tx,
        release=default_release,
        sizeAndCapacity=default_size_and_capacity,
        shutdown=default_shutdown,
    )
