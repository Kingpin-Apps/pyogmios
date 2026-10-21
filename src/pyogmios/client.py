"""The asynchronous Ogmios client."""

from __future__ import annotations

import itertools
import logging
import ssl
import warnings
from collections.abc import Mapping, Sequence
from types import TracebackType
from typing import Any, Literal, Self

import httpx

from . import _jsonrpc
from ._generated import models
from ._generated.api import AsyncLedgerStateQueries, AsyncNetworkQueries
from ._transport import DEFAULT_RECONNECT, HttpTransport, Reconnect, Transport, WebSocketTransport
from .errors import OgmiosConnectionError, OgmiosError, ServerVersionError, StatefulOverHttpError
from .health import SUPPORTED_MAJOR, Health, health_url
from .protocols import ChainSync, LedgerStateAt, MempoolMonitor, MempoolSnapshot, PointLike

logger = logging.getLogger("pyogmios")

DEFAULT_URL = "ws://localhost:1337"

VersionCheck = Literal["strict", "warn", "off"]


class AsyncClient:
    """An asynchronous client for Ogmios v7.

    ::

        async with AsyncClient("ws://localhost:1337") as client:
            epoch = await client.call("queryLedgerState/epoch")

    The URL scheme picks the transport: ``ws://`` and ``wss://`` use WebSocket (every method, many
    requests in flight on one connection), ``http://`` and ``https://`` use HTTP (queries and
    submission only; stateful methods raise :class:`~pyogmios.errors.StatefulOverHttpError`).

    :param url: The Ogmios server, including any path a hosted provider needs.
    :param timeout: Seconds to wait for each response; ``None`` waits forever. Some large queries
        (``delegateRepresentatives``, ``rewardsProvenance``) take several seconds on mainnet.
    :param headers: Extra headers for the connection, for example an API key for hosted Ogmios.
    :param reconnect: How to retry connecting; ``None`` never retries.
    :param check_version: On connect, read ``/health`` and check the server runs Ogmios 7.
        ``"strict"`` raises when it cannot tell, ``"warn"`` (the default) only warns then, ``"off"``
        skips the check. An older server always raises :class:`~pyogmios.errors.ServerVersionError`.
    :param open_timeout: Seconds to wait for a connection to open.
    :param ssl_context: TLS settings for ``wss://`` and ``https://``.
    :param transport: A ready-made transport, mainly for tests; replaces ``url``-based selection.
    """

    def __init__(
        self,
        url: str = DEFAULT_URL,
        *,
        timeout: float | None = 60.0,
        headers: Mapping[str, str] | None = None,
        reconnect: Reconnect | None = DEFAULT_RECONNECT,
        check_version: VersionCheck = "warn",
        open_timeout: float | None = 10.0,
        ssl_context: ssl.SSLContext | None = None,
        transport: Transport | None = None,
    ) -> None:
        self.url = url
        self.timeout = timeout
        self.headers = dict(headers or {})
        self.check_version = check_version
        self.open_timeout = open_timeout
        self.ssl_context = ssl_context
        self.transport: Transport = transport or self._transport_for(url, reconnect)
        #: The health read when connecting, when ``check_version`` is not ``"off"``.
        self.server_health: Health | None = None
        self._ids = itertools.count(1)
        self._connected = False
        self._reconnect = reconnect
        #: The ledger state queries: ``await client.ledger_state.epoch()``.
        self.ledger_state = AsyncLedgerStateQueries(self)
        #: The network queries: ``await client.network.tip()``.
        self.network = AsyncNetworkQueries(self)

    def _transport_for(self, url: str, reconnect: Reconnect | None) -> Transport:
        scheme = url.partition("://")[0].lower()
        if scheme in ("ws", "wss"):
            return WebSocketTransport(
                url,
                headers=self.headers,
                open_timeout=self.open_timeout,
                ssl_context=self.ssl_context,
                reconnect=reconnect,
            )
        if scheme in ("http", "https"):
            return HttpTransport(
                url,
                headers=self.headers,
                open_timeout=self.open_timeout,
                ssl_context=self.ssl_context,
                reconnect=reconnect,
            )
        raise ValueError(f"unsupported Ogmios URL {url!r}: use ws://, wss://, http:// or https://")

    # Connection ---------------------------------------------------------------------------------

    async def connect(self) -> Self:
        """Check the server version and open the connection. Called by ``async with``."""
        if self.check_version != "off":
            await self._check_version()
        await self.transport.connect()
        self._connected = True
        return self

    async def close(self) -> None:
        """Close the connection. Called at the end of ``async with``."""
        self._connected = False
        await self.transport.close()

    async def __aenter__(self) -> Self:
        return await self.connect()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def _check_version(self) -> None:
        try:
            self.server_health = await self.health()
        except OgmiosError as error:
            if self.check_version == "strict":
                raise ServerVersionError(
                    f"cannot read the Ogmios version from /health: {error}"
                ) from error
            warnings.warn(
                f"could not check the Ogmios version ({error}); this client needs Ogmios {SUPPORTED_MAJOR}",
                stacklevel=3,
            )
            return
        version = self.server_health.server_version
        if version is None:
            if self.check_version == "strict":
                raise ServerVersionError(
                    f"/health reports no version: {self.server_health.version!r}"
                )
            return
        if version[0] < SUPPORTED_MAJOR:
            raise ServerVersionError(
                f"Ogmios {self.server_health.version} is too old: this client needs Ogmios {SUPPORTED_MAJOR}"
            )
        if version[0] > SUPPORTED_MAJOR:
            message = (
                f"Ogmios {self.server_health.version} is newer than this client supports "
                f"(Ogmios {SUPPORTED_MAJOR}); some responses may not parse"
            )
            if self.check_version == "strict":
                raise ServerVersionError(message)
            warnings.warn(message, stacklevel=3)

    async def health(self) -> Health:
        """Read the server's ``/health``: node connection, sync progress, tip, era and version."""
        url = health_url(self.url)
        try:
            async with httpx.AsyncClient(
                headers=self.headers,
                timeout=self.open_timeout,
                verify=self.ssl_context if self.ssl_context is not None else True,
            ) as http:
                response = await http.get(url)
        except httpx.HTTPError as error:
            raise OgmiosConnectionError(f"cannot read {url}: {error}") from error
        if response.status_code != 200:
            raise OgmiosError(f"{url} answered HTTP {response.status_code}")
        return Health.model_validate_json(response.content)

    # Requests -----------------------------------------------------------------------------------

    async def request(
        self,
        method: str,
        params: Any = None,
        *,
        timeout: float | Literal["default"] | None = "default",
    ) -> Any:
        """Send any JSON-RPC request and return its raw ``result`` (plain JSON values).

        ``params`` are sent as given. Errors raise a :class:`~pyogmios.errors.ResponseError`
        subclass. Prefer :meth:`call`, which validates params and parses the result.
        """
        response = await self._send(method, params, timeout)
        return response["result"]

    async def call(
        self,
        method: str,
        params: Any = None,
        *,
        timeout: float | Literal["default"] | None = "default",
    ) -> Any:
        """Call an Ogmios method and return its result parsed into the types in :mod:`pyogmios.types`.

        ``params`` may be the method's params model, or a mapping using the Python (snake_case) or
        wire (camelCase) field names. They are validated before anything is sent.
        """
        encoded = _jsonrpc.build_params(method, params)
        response = await self._send(method, encoded, timeout)
        return _jsonrpc.parse_result(method, response["result"])

    async def _send(
        self, method: str, params: Any, timeout: float | Literal["default"] | None
    ) -> dict[str, Any]:
        if method in _jsonrpc.STATEFUL_METHODS and not self.transport.stateful:
            raise StatefulOverHttpError(
                f"{method} keeps state on the connection: use a ws:// or wss:// URL"
            )
        if not self._connected:  # used without `async with` or connect(): connect on first use
            await self.connect()
        message = _jsonrpc.request(method, params, next(self._ids))
        response = await self.transport.request(
            message, self.timeout if timeout == "default" else timeout
        )
        _jsonrpc.raise_for_error(response, method)
        if "result" not in response:
            raise OgmiosError(
                f"Ogmios answered {method} with neither a result nor an error: {response!r:.200}"
            )
        return response

    # Transactions --------------------------------------------------------------------------------

    async def submit_transaction(self, transaction: str | bytes) -> models.SubmitTransactionResult:
        """Submit a signed transaction (CBOR, as bytes or hex) and return its id.

        A rejection raises a :class:`~pyogmios.errors.SubmitTransactionError` subclass for the ledger
        rule that failed, for example :class:`~pyogmios.errors.UnknownOutputReferencesError`, with the
        ledger's details in ``details``.
        """
        return await self.call("submitTransaction", {"transaction": {"cbor": _hex(transaction)}})

    async def evaluate_transaction(
        self,
        transaction: str | bytes,
        *,
        additional_utxo: models.Utxo | Sequence[Any] | None = None,
    ) -> models.EvaluateTransactionResult:
        """Run a transaction's scripts and return the execution units each redeemer needs.

        ``additional_utxo`` adds outputs the node does not know yet, such as those of a transaction
        still being built; they take precedence over the node's own.
        """
        params: dict[str, Any] = {"transaction": {"cbor": _hex(transaction)}}
        if additional_utxo is not None:
            params["additional_utxo"] = list(additional_utxo)
        return await self.call("evaluateTransaction", params)

    # Stateful protocols, each on its own connection ----------------------------------------------

    def chain_sync(
        self,
        points: Sequence[PointLike] = ("origin",),
        *,
        pipeline: int = 50,
        resume: bool = True,
        raw: bool = False,
    ) -> ChainSync:
        """Follow the chain from the most recent of ``points`` that is on it; see :class:`ChainSync`.

        ``raw=True`` yields plain JSON instead of models, which is faster for indexers.
        """
        return ChainSync(self, points, pipeline=pipeline, resume=resume, raw=raw)

    def ledger_state_at(self, point: PointLike) -> LedgerStateAt:
        """Query the ledger as it was at ``point``; see :class:`LedgerStateAt`."""
        return LedgerStateAt(self, point)

    def mempool_snapshot(self, *, full: bool = False) -> MempoolSnapshot:
        """A snapshot of the node's mempool; see :class:`MempoolSnapshot`."""
        return MempoolSnapshot(self, full=full)

    def mempool(self, *, full: bool = False) -> MempoolMonitor:
        """Every transaction that enters the mempool; see :class:`MempoolMonitor`."""
        return MempoolMonitor(self, full=full)

    def _dedicated(self) -> AsyncClient:
        """A client on its own connection, for state that must not be shared or silently lost.

        It never reconnects by itself: losing the connection loses the state, so it raises instead.
        """
        if not self.transport.stateful:
            raise StatefulOverHttpError(
                "chain sync, an acquired ledger state and the mempool need a ws:// or wss:// URL"
            )
        return AsyncClient(
            self.url,
            timeout=self.timeout,
            headers=self.headers,
            reconnect=None,
            check_version="off",
            open_timeout=self.open_timeout,
            ssl_context=self.ssl_context,
        )

    @property
    def generation(self) -> int:
        """How many WebSocket connections have been opened; increases on every reconnect.

        Chain sync position, an acquired ledger state and an acquired mempool belong to one
        connection: when this changes, they are gone.
        """
        return getattr(self.transport, "generation", 0)


def _hex(transaction: str | bytes) -> str:
    """Transaction CBOR as lowercase hex."""
    return transaction.hex() if isinstance(transaction, bytes) else transaction.lower()
