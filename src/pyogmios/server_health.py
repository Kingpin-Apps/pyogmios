"""
Server health module

This module contains the functions to check the server health.
"""
from typing import Optional

import aiohttp
from pyogmios.models.base_model import BaseModel

from pyogmios.exceptions import RequestError
from pyogmios.models.server_health_model import ServerHealth


class ConnectionConfig(BaseModel):
    """
    Connection configuration model class
    """

    host: Optional[str] = None
    port: Optional[int] = None
    tls: Optional[bool] = None
    max_payload: Optional[int] = None


class Address(BaseModel):
    """
    Address model class
    """

    http: Optional[str] = None
    webSocket: Optional[str] = None


class Connection(ConnectionConfig):
    """
    Connection model class
    """

    max_payload: int
    address: Address


class Options(BaseModel):
    """
    Options model class
    """

    connection: Connection


async def get_server_health(options: Options) -> ServerHealth | RequestError:
    """
    Checks the server health.
    :param options: The options
    :return: The server health or an error
    """
    url = f"{options.connection.address.http}/health"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as response:
            if response.status == 200:
                server_health = ServerHealth(**await response.json())
            else:
                raise RequestError(response=response)

    return server_health
