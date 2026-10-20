from __future__ import annotations

from typing import Optional, Any

from pyogmios_client.enums import Method
from pyogmios_client.models import PointOrOrigin
from pyogmios_client.models.base_request_response_model import BaseRequest


class Request(BaseRequest):
    @staticmethod
    def from_base_request(
        request_id: str, method: Method, params: Optional[Any] = None
    ) -> Request:
        """
        Creates a request from a base request.

        :param request_id: The request id
        :param method: The method
        :param params: The params
        :return: The :class:`Request` object
        """
        return Request(id=request_id, method=method, params=params)


class NextBlock(Request):
    method: Method = Method.NEXT_BLOCK

    @staticmethod
    def from_base(request_id: str) -> NextBlock:
        """
        Creates a next block request from a base request.

        :param request_id: The request id
        :param params: The params
        :return: The :class:`NextBlock` object
        """
        return NextBlock.model_validate(
            Request.from_base_request(
                method=Method.NEXT_BLOCK, request_id=request_id
            ).model_dump()
        )


class ReleaseLedgerState(Request):
    methodname: Method = Method.RELEASE_LEDGER_STATE

    @staticmethod
    def from_base(
        request_id: str,
    ) -> ReleaseLedgerState:
        """
        Creates a release ledger state request from a base request.

        :param request_id: The request id
        :return: The :class:`ReleaseLedgerState` object
        """
        return ReleaseLedgerState.model_validate(
            Request.from_base_request(
                method=Method.RELEASE_LEDGER_STATE,
                request_id=request_id,
            ).model_dump()
        )


class AcquireLedgerState(Request):
    @staticmethod
    def from_base(request_id: str, point: PointOrOrigin) -> AcquireLedgerState:
        """
        Creates an acquire ledger state request from a base request.

        :param request_id: The request id
        :param point: The point or origin
        :return: The :class:`AcquireLedgerState` object
        """
        return AcquireLedgerState.model_validate(
            Request.from_base_request(
                method=Method.ACQUIRE_LEDGER_STATE,
                request_id=request_id,
                params={"point": point},
            ).model_dump()
        )
