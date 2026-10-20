"""
PyOgmios client exceptions

This module contains the various exceptions that maybe raised by the client.
"""
from typing import List

from pyogmios.models import PointOrOrigin


class ServerNotReady(Exception):
    """
    Server not ready exception
    """

    def __init__(self, health):
        self.health = health
        self.message = (
            f"Server not ready. Network synchronization at: {health.network_sync_at}"
        )
        super().__init__(self.message)


class RequestError(Exception):
    """
    Request error exception
    """

    def __init__(self, response):
        self.response = response
        self.message = f"Request error: {response.status}"
        super().__init__(self.message)


class IntersectionNotFoundError(Exception):
    """
    Intersection not found exception
    """

    def __init__(self, points: PointOrOrigin | List[PointOrOrigin]):
        self.points = points
        if isinstance(points, list):
            self.message = f"Intersection with points {[point.model_dump_json() for point in points]} not found"
        else:
            self.message = (
                f"Intersection with points {points.model_dump_json()} not found"
            )
        super().__init__(self.message)


class UnknownResultError(Exception):
    """
    Unknown result error exception
    """

    def __init__(self, result):
        self.result = result
        self.message = f"Unknown result error: {result}"
        super().__init__(self.message)


class TipIsOriginError(Exception):
    """
    Tip is origin error exception
    """

    def __init__(self):
        self.message = "Unable to produce point as the chain tip is the origin"
        super().__init__(self.message)


class WebSocketClosedError(Exception):
    """
    WebSocket closed error exception
    """

    def __init__(self):
        self.message = "WebSocket is closed"
        super().__init__(self.message)


class QueryUnavailableInCurrentEraError(Exception):
    """
    Query unavailable in current era error exception
    """

    def __init__(self, query_name):
        self.query_name = query_name
        self.message = f"QueryUnavailableInCurrentEra. {query_name}"
        super().__init__(self.message)


class AcquirePointTooOldError(Exception):
    """
    Acquire point too old error exception
    """

    def __init__(self):
        self.message = "Acquire point too old"
        super().__init__(self.message)


class AcquirePointNotOnChainError(Exception):
    """
    Acquire point not on chain error exception
    """

    def __init__(self):
        self.message = "Acquire point not on chain"
        super().__init__(self.message)


class AcquirePointFailureError(Exception):
    """
    Acquire point failure error exception
    """

    def __init__(self, failure):
        self.failure = failure
        self.message = f"Unknown AcquirePointFailure ${failure}"
        super().__init__(self.message)


class EraMismatchError(Exception):
    """
    Era mismatch error exception
    """

    def __init__(self, query_era: str, ledger_era: str):
        self.query_era = query_era
        self.ledger_era = ledger_era
        self.message = (
            f"Era mismatch. Query from era {query_era}. Ledger is in {ledger_era}"
        )
        super().__init__(self.message)


class JsonwspFaultError(Exception):
    """
    Jsonwsp fault error exception
    """

    def __init__(self, code: str, string: str):
        self.code = code
        self.message = f"Jsonwsp fault error code {code}. {string}"
        super().__init__(self.message)


class PyOgmiosError(Exception):
    """
    PyOgmios error exception
    """

    pass
