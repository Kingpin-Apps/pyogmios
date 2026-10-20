from __future__ import annotations

from abc import ABC
from typing import Optional, Any

from pyogmios.enums import Method, NetworkQuery, LedgerStateQuery
from pyogmios.models.base_model import BaseModel


class BaseRequestResponse(ABC, BaseModel):
    jsonrpc: Optional[str] = "2.0"
    id: Optional[int | str] = None
    method: Optional[Method | LedgerStateQuery | NetworkQuery] = None


class BaseRequest(BaseRequestResponse):
    params: Optional[Any] = None


class BaseResponse(BaseRequestResponse):
    result: Optional[Any] = None


class BaseErrorResponse(BaseRequestResponse):
    error: Optional[Any] = None
