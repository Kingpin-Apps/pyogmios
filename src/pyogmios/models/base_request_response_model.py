from __future__ import annotations

from abc import ABC
from typing import Any

from pyogmios.enums import LedgerStateQuery, Method, NetworkQuery
from pyogmios.models.base_model import BaseModel


class BaseRequestResponse(ABC, BaseModel):
    jsonrpc: str | None = "2.0"
    id: int | str | None = None
    method: Method | LedgerStateQuery | NetworkQuery | None = None


class BaseRequest(BaseRequestResponse):
    params: Any | None = None


class BaseResponse(BaseRequestResponse):
    result: Any | None = None


class BaseErrorResponse(BaseRequestResponse):
    error: Any | None = None
