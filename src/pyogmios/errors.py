"""Exceptions raised by pyogmios.

Every exception is an :class:`OgmiosError`. Errors returned by the server are :class:`ResponseError`
subclasses chosen by the JSON-RPC error code, and carry the server's ``code``, ``message`` and ``data``,
plus ``details``: the data parsed into the method's error model from :mod:`pyogmios.types`, when it
matches one.

::

    OgmiosError
    ├── OgmiosConnectionError        (also a builtin ConnectionError)
    ├── OgmiosTimeoutError           (also a builtin TimeoutError)
    ├── ServerVersionError
    ├── StatefulOverHttpError
    └── ResponseError
        ├── JsonRpcError                         -32700 to -32600
        │   ├── ParseError                       -32700
        │   ├── InvalidRequestError              -32600
        │   ├── MethodNotFoundError              -32601
        │   ├── InvalidParamsError               -32602
        │   │   └── TransactionDeserialisationError  (submit/evaluate)
        │   └── InternalError                    -32603
        ├── ChainSyncError                       1000s
        │   ├── IntersectionNotFoundError        1000
        │   └── IntersectionInterleavedError     1001
        ├── LedgerStateQueryError                2000s
        │   ├── AcquireLedgerStateError          2000
        │   ├── EraMismatchError                 2001
        │   ├── UnavailableInCurrentEraError     2002
        │   ├── AcquiredExpiredError             2003
        │   └── InvalidGenesisError              2004
        ├── TransactionError                     3000s
        │   ├── EvaluateTransactionError         (evaluateTransaction)
        │   └── SubmitTransactionError           (submitTransaction)
        └── MempoolError                         4000s
            └── MustAcquireMempoolFirstError     4000
"""

from __future__ import annotations

from typing import Any


class OgmiosError(Exception):
    """Base class of every pyogmios exception."""


class OgmiosConnectionError(OgmiosError, ConnectionError):
    """The client could not connect to Ogmios, or the connection was lost."""


class OgmiosTimeoutError(OgmiosError, TimeoutError):
    """Ogmios did not answer in time."""


class ServerVersionError(OgmiosError):
    """The server runs an Ogmios version this client does not support."""


class StatefulOverHttpError(OgmiosError):
    """A stateful method was called over HTTP.

    Chain sync, mempool monitoring and acquiring a ledger state keep state on the connection. Over
    HTTP every request is a new session, so the server's answers would be meaningless: use a
    ``ws://`` or ``wss://`` URL.
    """


class ResponseError(OgmiosError):
    """The server answered a request with a JSON-RPC error."""

    #: The JSON-RPC error codes this class stands for; used to choose the class for a response.
    codes: tuple[int, ...] = ()

    def __init__(
        self,
        code: int,
        message: str,
        data: Any = None,
        *,
        method: str | None = None,
        details: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.data = data
        self.method = method
        #: ``data`` parsed into the method's error model, when it matches one.
        self.details = details
        super().__init__(f"{message} (code {code}{f', {method}' if method else ''})")


class JsonRpcError(ResponseError):
    """A JSON-RPC protocol error: the request was malformed, unknown or had invalid params."""


class ParseError(JsonRpcError):
    codes = (-32700,)


class InvalidRequestError(JsonRpcError):
    """Ogmios uses this code for unknown methods and invalid params as well."""

    codes = (-32600,)


class MethodNotFoundError(JsonRpcError):
    codes = (-32601,)


class InvalidParamsError(JsonRpcError):
    codes = (-32602,)


class InternalError(JsonRpcError):
    codes = (-32603,)


class ChainSyncError(ResponseError):
    """A chain synchronization error (codes 1000 to 1999)."""


class IntersectionNotFoundError(ChainSyncError):
    """None of the given points is on the chain. ``data`` holds the server's tip."""

    codes = (1000,)


class IntersectionInterleavedError(ChainSyncError):
    """``findIntersection`` was sent while ``nextBlock`` requests were still pending."""

    codes = (1001,)


class LedgerStateQueryError(ResponseError):
    """A ledger state query error (codes 2000 to 2999)."""


class AcquireLedgerStateError(LedgerStateQueryError):
    """The point to acquire is too old or not on the chain."""

    codes = (2000,)


class EraMismatchError(LedgerStateQueryError):
    codes = (2001,)


class UnavailableInCurrentEraError(LedgerStateQueryError):
    codes = (2002,)


class AcquiredExpiredError(LedgerStateQueryError):
    """The acquired ledger state is too old to query: acquire it again."""

    codes = (2003,)


class InvalidGenesisError(LedgerStateQueryError):
    """The node has no genesis configuration for the requested era."""

    codes = (2004,)


class TransactionError(ResponseError):
    """A transaction submission or evaluation error (codes 3000 to 3999)."""


class EvaluateTransactionError(TransactionError):
    """``evaluateTransaction`` failed: see ``details`` for the reason and failing scripts."""


class SubmitTransactionError(TransactionError):
    """``submitTransaction`` was rejected: see ``details`` for the ledger's reasons."""


class TransactionDeserialisationError(InvalidParamsError, TransactionError):
    """The transaction could not be decoded in any era. ``data`` lists the decoder errors."""


class MempoolError(ResponseError):
    """A mempool monitoring error (codes 4000 to 4999)."""


class MustAcquireMempoolFirstError(MempoolError):
    codes = (4000,)


_BY_CODE: dict[int, type[ResponseError]] = {
    code: cls
    for cls in (
        ParseError,
        InvalidRequestError,
        MethodNotFoundError,
        InvalidParamsError,
        InternalError,
        IntersectionNotFoundError,
        IntersectionInterleavedError,
        AcquireLedgerStateError,
        EraMismatchError,
        UnavailableInCurrentEraError,
        AcquiredExpiredError,
        InvalidGenesisError,
        MustAcquireMempoolFirstError,
    )
    for code in cls.codes
}

_TRANSACTION_METHODS = {"submitTransaction", "evaluateTransaction"}


def error_class(code: int, method: str | None) -> type[ResponseError]:
    """The exception class for a JSON-RPC error ``code`` returned by ``method``."""
    if method in _TRANSACTION_METHODS:
        if code == -32602:
            return TransactionDeserialisationError
        if 3000 <= code < 4000:
            return (
                EvaluateTransactionError
                if method == "evaluateTransaction"
                else SubmitTransactionError
            )
    if code in _BY_CODE:
        return _BY_CODE[code]
    if -32768 <= code <= -32000:
        return JsonRpcError
    for low, cls in (
        (1000, ChainSyncError),
        (2000, LedgerStateQueryError),
        (3000, TransactionError),
        (4000, MempoolError),
    ):
        if low <= code < low + 1000:
            return cls
    return ResponseError
