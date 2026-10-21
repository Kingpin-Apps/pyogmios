"""pyogmios: a Python client for Ogmios v7, the JSON-RPC bridge to cardano-node.

::

    import pyogmios

    with pyogmios.Client("ws://localhost:1337") as client:
        print(client.call("queryLedgerState/epoch"))

Use :class:`AsyncClient` from asyncio code. Every Ogmios and Cardano type is in :mod:`pyogmios.types`
and every exception in :mod:`pyogmios.errors`.
"""

import logging

from ._generated.methods import OGMIOS_VERSION
from ._transport import Reconnect
from .client import AsyncClient
from .errors import (
    OgmiosConnectionError,
    OgmiosError,
    OgmiosTimeoutError,
    ResponseError,
    ServerVersionError,
    StatefulOverHttpError,
)
from .health import Health
from .sync import Client

__version__ = "0.7.4"

__all__ = [
    "OGMIOS_VERSION",
    "AsyncClient",
    "Client",
    "Health",
    "OgmiosConnectionError",
    "OgmiosError",
    "OgmiosTimeoutError",
    "Reconnect",
    "ResponseError",
    "ServerVersionError",
    "StatefulOverHttpError",
    "__version__",
]

logging.getLogger("pyogmios").addHandler(logging.NullHandler())
