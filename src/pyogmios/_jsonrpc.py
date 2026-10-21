"""JSON-RPC 2.0 messages for Ogmios: building requests, reading results and raising errors.

The envelope is written by hand rather than generated: the schema's ``RpcError`` names the error
message ``string``, but the server sends ``message``, as JSON-RPC 2.0 specifies.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import cache
from typing import Any

from pydantic import BaseModel, TypeAdapter, ValidationError

from ._generated.methods import METHODS, MethodSpec
from .errors import ResponseError, error_class

#: Methods that keep state on the connection, so they only make sense over WebSocket.
STATEFUL_METHODS = frozenset(
    {
        "findIntersection",
        "nextBlock",
        "acquireLedgerState",
        "releaseLedgerState",
        "acquireMempool",
        "nextTransaction",
        "hasTransaction",
        "sizeOfMempool",
        "releaseMempool",
    }
)


def spec(method: str) -> MethodSpec:
    """The method's entry in the generated method table."""
    try:
        return METHODS[method]
    except KeyError:
        raise ValueError(f"unknown Ogmios method {method!r}") from None


@cache
def _adapter(tp: Any) -> TypeAdapter[Any]:
    return TypeAdapter(tp)


def build_params(method: str, params: Any) -> Any:
    """Validate ``params`` against the method's params model and encode them for the wire.

    ``params`` may be the generated model, or a mapping using either the Python (snake_case) or the
    wire (camelCase) field names. Returns ``None`` when there is nothing to send.
    """
    method_spec = spec(method)
    if method_spec.params is None:
        if params is not None:
            raise TypeError(f"{method} takes no params")
        return None
    if params is None:
        if not method_spec.params_required:
            return None
        params = {}  # for example nextTransaction, whose params are all optional but must be sent
    model = (
        params
        if isinstance(params, BaseModel)
        else _adapter(method_spec.params).validate_python(params)
    )
    return _adapter(method_spec.params).dump_python(
        model, mode="json", by_alias=True, exclude_none=True
    )


def request(method: str, params: Any, request_id: int) -> dict[str, Any]:
    """A JSON-RPC request object; ``params`` must already be encoded."""
    message: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "id": request_id}
    if params is not None:
        message["params"] = params
    return message


def parse_result(method: str, result: Any) -> Any:
    """Parse a raw ``result`` into the method's result type."""
    return _adapter(spec(method).result).validate_python(result)


def error_from(response: Mapping[str, Any], method: str | None) -> ResponseError:
    """The exception for an error response, with ``details`` parsed when the data matches a model."""
    error = response.get("error") or {}
    code = int(error.get("code", 0))
    message = str(error.get("message") or error.get("string") or "Unknown error")
    data = error.get("data")
    details = None
    if method in METHODS:
        for error_type in METHODS[method].errors:
            try:
                details = _adapter(error_type).validate_python(error)
            except ValidationError:
                continue
            break
    return error_class(code, method)(code, message, data, method=method, details=details)


def raise_for_error(response: Mapping[str, Any], method: str | None) -> None:
    """Raise the matching :class:`~pyogmios.errors.ResponseError` if ``response`` is an error."""
    if "error" in response:
        raise error_from(response, method)
