"""A fake Ogmios server for unit tests: it replays recorded fixtures over a real WebSocket.

It answers each request with the recorded response for its method (the ``ok`` case, unless a test
sets another), with the request's own ``id``, and serves ``GET /health``. Tests can make it slow,
answer out of order, or drop the connection.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any

from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.datastructures import Headers
from websockets.exceptions import ConnectionClosed
from websockets.http11 import Request, Response

from .conftest import FIXTURE_LIST

HEALTH = {
    "version": "v7.0.0 (ef123abd)",
    "network": "preview",
    "connectionStatus": "connected",
    "networkSynchronization": 1.0,
    "currentEra": "conway",
    "currentEpoch": 1457,
    "slotInEpoch": 20186,
    "lastKnownTip": {"slot": 1, "id": "0" * 64, "height": 1},
}


def recorded(method: str, case: str = "ok") -> dict[str, Any]:
    """The recorded response for ``method`` and ``case``."""
    for fixture in FIXTURE_LIST:
        if fixture.method == method and fixture.case == case:
            return fixture.response
    for fixture in FIXTURE_LIST:  # methods without an "ok" case, such as nextBlock
        if fixture.method == method and "result" in fixture.response:
            return fixture.response
    raise KeyError(f"no fixture for {method}:{case}")


@dataclass
class FakeOgmios:
    """The fake server's behaviour, which tests change while it runs."""

    #: Responses by method, used instead of the recorded "ok" case.
    responses: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: Seconds to wait before answering, by method.
    delays: dict[str, float] = field(default_factory=dict)
    #: Hold this many requests, then answer them in reverse order.
    hold: int = 0
    #: Close the connection after receiving this many requests (once).
    drop_after: int | None = None
    #: Answers given in turn for a method, before falling back to ``responses`` (shared by all connections).
    sequences: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    #: Text sent before every answer, to test messages that are not JSON.
    noise: str | None = None
    #: Methods answered with an error that has no id, as when the server cannot read a request.
    without_id: set[str] = field(default_factory=set)
    #: What /health returns: a dict (as JSON) or an HTTP status for an error.
    health: dict[str, Any] | int = field(default_factory=lambda: dict(HEALTH))
    #: Every request received, in order.
    received: list[dict[str, Any]] = field(default_factory=list)
    #: The connection (1 for the first) each request in ``received`` arrived on.
    received_on: list[int] = field(default_factory=list)
    health_requests: int = 0
    connections: int = 0
    server: Server | None = None
    _tasks: set[asyncio.Task[None]] = field(default_factory=set)

    @property
    def port(self) -> int:
        assert self.server is not None
        return self.server.sockets[0].getsockname()[1]

    @property
    def ws_url(self) -> str:
        return f"ws://127.0.0.1:{self.port}"

    def answer(self, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method", "")
        if method in self.without_id:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "unreadable"},
                "id": None,
            }
        if self.sequences.get(method):
            response = dict(self.sequences[method].pop(0))
        else:
            response = dict(self.responses.get(method) or recorded(method))
        response["id"] = request.get("id")
        return response

    def process_request(self, connection: ServerConnection, request: Request) -> Response | None:
        if request.path != "/health":
            return None
        self.health_requests += 1
        if isinstance(self.health, int):
            return connection.respond(HTTPStatus(self.health), "error\n")
        body = json.dumps(self.health).encode()
        headers = Headers(
            [("Content-Type", "application/json"), ("Content-Length", str(len(body)))]
        )
        return Response(200, "OK", headers, body)

    async def handler(self, connection: ServerConnection) -> None:
        with suppress(ConnectionClosed):  # the client may close while an answer is being sent
            await self._handle(connection)

    async def _handle(self, connection: ServerConnection) -> None:
        self.connections += 1
        number = self.connections
        held: list[dict[str, Any]] = []
        async for raw in connection:
            request = json.loads(raw)
            self.received.append(request)
            self.received_on.append(number)
            if self.drop_after is not None and len(self.received) >= self.drop_after:
                self.drop_after = None
                await connection.close()
                return
            if self.hold:
                held.append(request)
                if len(held) == self.hold:
                    for waiting in reversed(held):
                        await connection.send(json.dumps(self.answer(waiting)))
                    held.clear()
                continue
            delay = self.delays.get(request.get("method", ""), 0)
            if delay:
                task = asyncio.create_task(self._answer_later(connection, request, delay))
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
            else:
                if self.noise is not None:
                    await connection.send(self.noise)
                await connection.send(json.dumps(self.answer(request)))

    async def _answer_later(
        self, connection: ServerConnection, request: dict[str, Any], delay: float
    ) -> None:
        await asyncio.sleep(delay)
        with suppress(ConnectionClosed):  # the client may be gone by then
            await connection.send(json.dumps(self.answer(request)))


@asynccontextmanager
async def running(fake: FakeOgmios | None = None) -> AsyncGenerator[FakeOgmios]:
    """Run a fake Ogmios on a free local port."""
    fake = fake or FakeOgmios()
    async with serve(fake.handler, "127.0.0.1", 0, process_request=fake.process_request) as server:
        fake.server = server
        yield fake
