from unittest.mock import MagicMock

import pytest

from pyogmios.exceptions import (
    IntersectionNotFoundError,
    RequestError,
    ServerNotReady,
    TipIsOriginError,
    UnknownResultError,
    WebSocketClosedError,
)
from pyogmios.models import Origin


def test_server_not_ready_exception():
    health = MagicMock()
    health.network_sync_at = "sync_at"
    message = "Server not ready. Network synchronization at: sync_at"

    with pytest.raises(ServerNotReady, match=message) as excinfo:
        raise ServerNotReady(health)

    assert excinfo.value.health == health


def test_request_error_exception():
    response = MagicMock()
    response.status = "error_status"
    message = "Request error: error_status"

    with pytest.raises(RequestError, match=message) as excinfo:
        raise RequestError(response)

    assert excinfo.value.response == response


def test_intersection_not_found_error_exception():
    origin = Origin("origin")
    message = 'Intersection with points "origin" not found'

    with pytest.raises(IntersectionNotFoundError, match=message) as excinfo:
        raise IntersectionNotFoundError(origin)

    assert excinfo.value.points == origin


def test_unknown_result_error_exception():
    result = "unknown_result"
    message = "Unknown result error: unknown_result"

    with pytest.raises(UnknownResultError, match=message) as excinfo:
        raise UnknownResultError(result)

    assert excinfo.value.result == result


def test_tip_is_origin_error_exception():
    message = "Unable to produce point as the chain tip is the origin"

    with pytest.raises(TipIsOriginError, match=message):
        raise TipIsOriginError()


def test_websocket_closed_error_exception():
    message = "WebSocket is closed"

    with pytest.raises(WebSocketClosedError, match=message):
        raise WebSocketClosedError()
