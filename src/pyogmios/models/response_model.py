from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from pyogmios.enums import Method
from pyogmios.models import (
    BaseModel,
    BlockNoOrOrigin,
    Bound,
    Epoch,
    EraMismatch,
    EraSummary,
    EvaluationFailure,
    EvaluationResult,
    GenesisAlonzo,
    GenesisByron,
    GenesisConway,
    GenesisShelley,
    MempoolSizeAndCapacity,
    NonMyopicMemberRewards,
    Null,
    PointOrOrigin,
    PoolDistribution,
    PoolId,
    PoolParameters,
    PoolsRanking,
    ProtocolParameters,
    ProtocolParametersAlonzo,
    ProtocolParametersBabbage,
    ProtocolParametersShelley,
    QueryUnavailableInCurrentEra,
    RewardAccountSummaries,
    RewardsProvenance,
    RewardsProvenanceNew,
    TxAlonzo,
    TxBabbage,
    TxId,
    UtcTime,
    Utxo,
)
from pyogmios.models.base_request_response_model import BaseResponse
from pyogmios.models.result_models import (
    AcquireFailureResult,
    AcquireSuccessResult,
    AwaitAcquiredResult,
    FindIntersectResult,
    ReleaseResponseResult,
    RollBackwardResult,
    RollForwardResult,
    SubmitTxError,
)


class Response(BaseResponse):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class SubmitTransactionSuccess(BaseModel):
    result: dict[str, Any]


class SubmitTxResponseSubmitSuccess(BaseModel):
    SubmitSuccess: SubmitTransactionSuccess


class SubmitTxResponseSubmitFail(BaseModel):
    SubmitFail: SubmitTxError


class SubmitTxResponse(BaseModel):
    methodname: Method = Method.SUBMIT_TRANSACTION
    result: SubmitTxResponseSubmitSuccess | SubmitTxResponseSubmitFail
    reflection: dict[str, Any] | None = None


class EvaluateTxResponse(BaseModel):
    methodname: Method = Method.EVALUATE_TRANSACTION
    result: EvaluationResult | EvaluationFailure
    reflection: dict[str, Any] | None = None


class AwaitAcquireResponse(BaseModel):
    methodname: Method = Method.ACQUIRE_LEDGER_STATE
    result: AwaitAcquiredResult
    reflection: dict[str, Any] | None = None


class HasTxResponse(BaseModel):
    methodname: Method = Method.HAS_TRANSACTION
    result: bool
    reflection: dict[str, Any] | None = None


class NextTxResponse(BaseModel):
    methodname: Method = Method.NEXT_TRANSACTION
    result: TxId | TxAlonzo | TxBabbage | Null
    reflection: dict[str, Any] | None = None


class ReleaseMempoolResponse(BaseModel):
    methodname: Method = Method.RELEASE_MEMPOOL
    result: str
    reflection: dict[str, Any] | None = None


class SizeAndCapacityResponse(BaseModel):
    methodname: Method = Method.SIZE_OF_MEMPOOL
    result: MempoolSizeAndCapacity
    reflection: dict[str, Any] | None = None


class QueryResponseReflection(BaseModel):
    requestId: str | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class QueryResponse(Response):
    @staticmethod
    def from_base_response(
        request_id: str,
        method: Method,
        result: Any | None = None,
    ) -> QueryResponse:
        """
        Creates a query response from a base response.

        :param request_id: The request id
        :param method: The method
        :param result: The result
        :return: The :class:`QueryResponse` object
        """
        return QueryResponse(
            id=request_id,
            method=method,
            result=result,
        )


class FindIntersectResponse(QueryResponse):
    methodname: Method = Method.FIND_INTERSECTION
    result: FindIntersectResult

    class Config:
        populate_by_name = True


class QueryNetworkBlockHeightResponse(QueryResponse):
    result: BlockNoOrOrigin | QueryUnavailableInCurrentEra


class RequestNextResponse(QueryResponse):
    result: RollForwardResult | RollBackwardResult


class ReleaseResponse(QueryResponse):
    methodname: Method = Method.RELEASE_LEDGER_STATE
    result: ReleaseResponseResult


class AcquireResponse(QueryResponse):
    methodname: Method = Method.ACQUIRE_LEDGER_STATE
    result: AcquireSuccessResult | AcquireFailureResult


class QueryNetworkTipResponse(QueryResponse):
    result: PointOrOrigin


class QueryLedgerStateEpochResponse(QueryResponse):
    result: Epoch


class QueryLedgerStateProtocolParametersResponse(QueryResponse):
    result: ProtocolParameters


class QueryLedgerStateRewardAccountSummariesResponse(QueryResponse):
    result: RewardAccountSummaries


class QueryLedgerStateEraStartResponse(QueryResponse):
    result: Bound | None = None


class EraSummariesResponse(QueryResponse):
    result: list[EraSummary] | None = None


class QueryNetworkGenesisConfigurationResponse(QueryResponse):
    result: GenesisByron | GenesisShelley | GenesisAlonzo | GenesisConway | None


class QueryLedgerStateTipResponse(QueryResponse):
    result: PointOrOrigin | None = None


class NonMyopicMemberRewardsResponse(QueryResponse):
    result: NonMyopicMemberRewards | EraMismatch | QueryUnavailableInCurrentEra | None = None


class PoolIdsResponse(QueryResponse):
    result: list[PoolId] | EraMismatch | QueryUnavailableInCurrentEra | None = None


class PoolParametersResponse(QueryResponse):
    result: dict[str, PoolParameters] | EraMismatch | QueryUnavailableInCurrentEra | None = None


class PoolsRankingResponse(QueryResponse):
    result: PoolsRanking | EraMismatch | QueryUnavailableInCurrentEra | None = None


class ProposedProtocolParametersResponse(QueryResponse):
    result: (
        dict[str, ProtocolParametersShelley]
        | dict[str, ProtocolParametersAlonzo]
        | dict[str, ProtocolParametersBabbage]
        | EraMismatch
        | QueryUnavailableInCurrentEra
        | None
    ) = None


class RewardsProvenanceResponse(QueryResponse):
    result: RewardsProvenance | EraMismatch | QueryUnavailableInCurrentEra | None = None


class RewardsProvenanceNewResponse(QueryResponse):
    result: RewardsProvenanceNew | EraMismatch | QueryUnavailableInCurrentEra | None = None


class StakeDistributionResponse(QueryResponse):
    result: PoolDistribution | EraMismatch | QueryUnavailableInCurrentEra | None = None


class SystemStartResponse(QueryResponse):
    result: UtcTime | EraMismatch | QueryUnavailableInCurrentEra | None = None


class UtxoResponse(QueryResponse):
    result: Utxo | EraMismatch | QueryUnavailableInCurrentEra | None = None


Response.model_rebuild()
