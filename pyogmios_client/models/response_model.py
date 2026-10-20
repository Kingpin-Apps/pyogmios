from __future__ import annotations

from typing import Optional, Any, Dict, Union, List

from pydantic import ConfigDict

from pyogmios_client.enums import Method
from pyogmios_client.models import (
    BaseModel,
    BlockNoOrOrigin,
    QueryUnavailableInCurrentEra,
    PointOrOrigin,
    EraMismatch,
    Epoch,
    ProtocolParametersShelley,
    ProtocolParametersAlonzo,
    ProtocolParametersBabbage,
    RewardAccountSummaries,
    Bound,
    EraSummary,
    GenesisByron,
    GenesisShelley,
    GenesisAlonzo,
    NonMyopicMemberRewards,
    PoolId,
    PoolParameters,
    RewardsProvenance,
    RewardsProvenanceNew,
    UtcTime,
    Utxo,
    TxId,
    EvaluationResult,
    EvaluationFailure,
    PoolDistribution,
    PoolsRanking,
    TxAlonzo,
    TxBabbage,
    Null,
    MempoolSizeAndCapacity,
    ProtocolParameters,
    GenesisConway,
)
from pyogmios_client.models.base_request_response_model import BaseResponse
from pyogmios_client.models.result_models import (
    SubmitTxError,
    RollForwardResult,
    RollBackwardResult,
    FindIntersectResult,
    AcquireSuccessResult,
    AcquireFailureResult,
    AwaitAcquiredResult,
    ReleaseResponseResult,
)


class Response(BaseResponse):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class SubmitTransactionSuccess(BaseModel):
    result: Dict[str, Any]


class SubmitTxResponseSubmitSuccess(BaseModel):
    SubmitSuccess: SubmitTransactionSuccess


class SubmitTxResponseSubmitFail(BaseModel):
    SubmitFail: SubmitTxError


class SubmitTxResponse(BaseModel):
    methodname: Method = Method.SUBMIT_TRANSACTION
    result: Union[SubmitTxResponseSubmitSuccess, SubmitTxResponseSubmitFail]
    reflection: Optional[Dict[str, Any]] = None


class EvaluateTxResponse(BaseModel):
    methodname: Method = Method.EVALUATE_TRANSACTION
    result: Union[EvaluationResult, EvaluationFailure]
    reflection: Optional[Dict[str, Any]] = None


class AwaitAcquireResponse(BaseModel):
    methodname: Method = Method.ACQUIRE_LEDGER_STATE
    result: AwaitAcquiredResult
    reflection: Optional[Dict[str, Any]] = None


class HasTxResponse(BaseModel):
    methodname: Method = Method.HAS_TRANSACTION
    result: bool
    reflection: Optional[Dict[str, Any]] = None


class NextTxResponse(BaseModel):
    methodname: Method = Method.NEXT_TRANSACTION
    result: Union[TxId, TxAlonzo, TxBabbage, Null]
    reflection: Optional[Dict[str, Any]] = None


class ReleaseMempoolResponse(BaseModel):
    methodname: Method = Method.RELEASE_MEMPOOL
    result: str
    reflection: Optional[Dict[str, Any]] = None


class SizeAndCapacityResponse(BaseModel):
    methodname: Method = Method.SIZE_OF_MEMPOOL
    result: MempoolSizeAndCapacity
    reflection: Optional[Dict[str, Any]] = None


class QueryResponseReflection(BaseModel):
    requestId: Optional[str] = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class QueryResponse(Response):
    @staticmethod
    def from_base_response(
        request_id: str,
        method: Method,
        result: Optional[Any] = None,
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
    result: Union[RollForwardResult, RollBackwardResult]


class ReleaseResponse(QueryResponse):
    methodname: Method = Method.RELEASE_LEDGER_STATE
    result: ReleaseResponseResult


class AcquireResponse(QueryResponse):
    methodname: Method = Method.ACQUIRE_LEDGER_STATE
    result: Union[AcquireSuccessResult, AcquireFailureResult]


class QueryNetworkTipResponse(QueryResponse):
    result: PointOrOrigin


class QueryLedgerStateEpochResponse(QueryResponse):
    result: Epoch


class QueryLedgerStateProtocolParametersResponse(QueryResponse):
    result: ProtocolParameters


class QueryLedgerStateRewardAccountSummariesResponse(QueryResponse):
    result: RewardAccountSummaries


class QueryLedgerStateEraStartResponse(QueryResponse):
    result: Optional[Bound] = None


class EraSummariesResponse(QueryResponse):
    result: Optional[List[EraSummary]] = None


class QueryNetworkGenesisConfigurationResponse(QueryResponse):
    result: Optional[GenesisByron | GenesisShelley | GenesisAlonzo | GenesisConway]


class QueryLedgerStateTipResponse(QueryResponse):
    result: Optional[PointOrOrigin] = None


class NonMyopicMemberRewardsResponse(QueryResponse):
    result: Optional[
        Union[NonMyopicMemberRewards, EraMismatch, QueryUnavailableInCurrentEra]
    ] = None


class PoolIdsResponse(QueryResponse):
    result: Optional[
        Union[List[PoolId], EraMismatch, QueryUnavailableInCurrentEra]
    ] = None


class PoolParametersResponse(QueryResponse):
    result: Optional[
        Union[Dict[str, PoolParameters], EraMismatch, QueryUnavailableInCurrentEra]
    ] = None


class PoolsRankingResponse(QueryResponse):
    result: Optional[
        Union[PoolsRanking, EraMismatch, QueryUnavailableInCurrentEra]
    ] = None


class ProposedProtocolParametersResponse(QueryResponse):
    result: Optional[
        Union[
            Dict[str, ProtocolParametersShelley],
            Dict[str, ProtocolParametersAlonzo],
            Dict[str, ProtocolParametersBabbage],
            EraMismatch,
            QueryUnavailableInCurrentEra,
        ]
    ] = None


class RewardsProvenanceResponse(QueryResponse):
    result: Optional[
        Union[RewardsProvenance, EraMismatch, QueryUnavailableInCurrentEra]
    ] = None


class RewardsProvenanceNewResponse(QueryResponse):
    result: Optional[
        Union[RewardsProvenanceNew, EraMismatch, QueryUnavailableInCurrentEra]
    ] = None


class StakeDistributionResponse(QueryResponse):
    result: Optional[
        Union[PoolDistribution, EraMismatch, QueryUnavailableInCurrentEra]
    ] = None


class SystemStartResponse(QueryResponse):
    result: Optional[Union[UtcTime, EraMismatch, QueryUnavailableInCurrentEra]] = None


class UtxoResponse(QueryResponse):
    result: Optional[Union[Utxo, EraMismatch, QueryUnavailableInCurrentEra]] = None


Response.model_rebuild()
