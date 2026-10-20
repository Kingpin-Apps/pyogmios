from typing import List, Union, Optional, Dict

from pydantic import RootModel, Field, model_validator

from pyogmios.enums import AcquireFailureDetails
from pyogmios.models import (
    SubmitTxErrorUnspendableDatums,
    SubmitTxErrorCollectErrors,
    SubmitTxErrorExecutionUnitsTooLarge,
    SubmitTxErrorCollateralHasNonAdaAssets,
    SubmitTxErrorCollateralIsScript,
    SubmitTxErrorMissingDatumHashesForInputs,
    ExtraRedeemers,
    SubmitTxErrorUnspendableScriptInputs,
    SubmitTxErrorMissingRequiredRedeemers,
    SubmitTxErrorUpdateWrongEpoch,
    SubmitTxErrorWrongPoolCertificate,
    SubmitTxErrorTooManyAssetsInOutput,
    SubmitTxErrorOutputTooSmall,
    SubmitTxErrorNetworkMismatch,
    SubmitTxErrorValueNotConserved,
    SubmitTxErrorOutsideOfValidityInterval,
    SubmitTxErrorBadInputs,
    PointOrOrigin,
    Slot,
    ExecutionUnits,
    TipOrOrigin,
    Block,
    TxId,
    SubmitTxErrorMissingVkWitnesses,
    SubmitTxErrorMissingScriptWitnesses,
    SubmitTxErrorScriptWitnessNotValidating,
    SubmitTxErrorInsufficientGenesisSignatures,
    SubmitTxErrorMirNegativeTransferNotCurrentlyAllowed,
    SubmitTxErrorMissingTxMetadata,
    SubmitTxErrorMissingTxMetadataHash,
    SubmitTxErrorMirTransferNotCurrentlyAllowed,
    SubmitTxErrorTxMetadataHashMismatch,
    SubmitTxErrorExpiredUtxo,
    SubmitTxErrorTxTooLarge,
    SubmitTxErrorMissingAtLeastOneInputUtxo,
    SubmitTxErrorInvalidMetadata,
    SubmitTxErrorFeeTooSmall,
    SubmitTxErrorAddressAttributesTooLarge,
    SubmitTxErrorTriesToForgeAda,
    SubmitTxErrorDelegateNotRegistered,
    SubmitTxErrorUnknownOrIncompleteWithdrawals,
    SubmitTxErrorStakePoolNotRegistered,
    SubmitTxErrorWrongRetirementEpoch,
    SubmitTxErrorStakeKeyAlreadyRegistered,
    SubmitTxErrorPoolCostTooSmall,
    SubmitTxErrorPoolMetadataHashTooBig,
    SubmitTxErrorStakeKeyNotRegistered,
    SubmitTxErrorRewardAccountNotExisting,
    SubmitTxErrorWrongCertificateType,
    SubmitTxErrorRewardAccountNotEmpty,
    SubmitTxErrorUnknownGenesisKey,
    SubmitTxErrorAlreadyDelegating,
    SubmitTxErrorInsufficientFundsForMir,
    SubmitTxErrorTooLateForMir,
    SubmitTxErrorMirProducesNegativeUpdate,
    SubmitTxErrorDuplicateGenesisVrf,
    SubmitTxErrorNonGenesisVoters,
    SubmitTxErrorProtocolVersionCannotFollow,
    MissingRequiredDatums,
    SubmitTxErrorExtraDataMismatch,
    SubmitTxErrorMissingRequiredSignatures,
    SubmitTxErrorMissingCollateralInputs,
    SubmitTxErrorCollateralTooSmall,
    SubmitTxErrorTooManyCollateralInputs,
    SubmitTxErrorValidationTagMismatch,
    SubmitTxErrorOutsideForecast,
    SubmitTxErrorExtraScriptWitnesses,
    SubmitTxErrorMirNegativeTransfer,
    SubmitTxErrorTotalCollateralMismatch,
    SubmitTxErrorMalformedReferenceScripts,
    SubmitTxErrorMalformedScriptWitnesses,
    SubmitTxErrorInvalidWitnesses,
    SubmitTxErrorEraMismatch,
    EraMismatch,
    Any,
)
from pyogmios.models.base_model import BaseModel


class AcquireFailure(BaseModel):
    failure: AcquireFailureDetails


class AcquireSuccess(BaseModel):
    point: PointOrOrigin


class AcquireFailureResult(BaseModel):
    acquire_failure: AcquireFailure = Field(None, alias="AcquireFailure")


class AcquireSuccessResult(BaseModel):
    acquire_success: AcquireSuccess = Field(None, alias="AcquireSuccess")


class AwaitAcquired(BaseModel):
    slot: Slot


class AwaitAcquiredResult(BaseModel):
    await_acquired: AwaitAcquired = Field(None, alias="AwaitAcquired")


class EvaluationResult(BaseModel):
    evaluation_result: Dict[str, ExecutionUnits] = Field(None, alias="EvaluationResult")


class IntersectionFound(BaseModel):
    point: PointOrOrigin
    tip: TipOrOrigin


class IntersectionNotFound(BaseModel):
    tip: TipOrOrigin


class RollBackward(BaseModel):
    point: PointOrOrigin
    tip: TipOrOrigin


class RollForward(BaseModel):
    block: Block = Field(discriminator="block_type")
    tip: TipOrOrigin

    @model_validator(mode="before")
    @classmethod
    def block_type_coerce(cls, data: Any) -> Any:
        if data["tip"] == "origin":
            return data
        block_keys = set(data["block"].keys())

        if "babbage" in block_keys:
            data["block"]["block_type"] = "babbage"
        elif "alonzo" in block_keys:
            data["block"]["block_type"] = "alonzo"
        elif "allegra" in block_keys:
            data["block"]["block_type"] = "allegra"
        elif "mary" in block_keys:
            data["block"]["block_type"] = "mary"
        elif "shelley" in block_keys:
            data["block"]["block_type"] = "shelley"
        elif "byron" in block_keys:
            data["block"]["block_type"] = "byron"

        return data


class RollBackwardResult(BaseModel):
    roll_backward: RollBackward = Field(alias="RollBackward")


class RollForwardResult(BaseModel):
    roll_forward: RollForward = Field(alias="RollForward")


class SubmitSuccess(BaseModel):
    txId: TxId


class ReleaseResponseResult(BaseModel):
    released: str = Field("Released", alias="Released")


class EraMismatchResult(BaseModel):
    eraMismatch: Optional[EraMismatch] = None


class SubmitTxError(RootModel):
    root: List[
        Union[
            SubmitTxErrorEraMismatch,
            SubmitTxErrorInvalidWitnesses,
            SubmitTxErrorMissingVkWitnesses,
            SubmitTxErrorMissingScriptWitnesses,
            SubmitTxErrorScriptWitnessNotValidating,
            SubmitTxErrorInsufficientGenesisSignatures,
            SubmitTxErrorMissingTxMetadata,
            SubmitTxErrorMissingTxMetadataHash,
            SubmitTxErrorTxMetadataHashMismatch,
            SubmitTxErrorBadInputs,
            SubmitTxErrorExpiredUtxo,
            SubmitTxErrorOutsideOfValidityInterval,
            SubmitTxErrorTxTooLarge,
            SubmitTxErrorMissingAtLeastOneInputUtxo,
            SubmitTxErrorInvalidMetadata,
            SubmitTxErrorFeeTooSmall,
            SubmitTxErrorValueNotConserved,
            SubmitTxErrorNetworkMismatch,
            SubmitTxErrorOutputTooSmall,
            SubmitTxErrorTooManyAssetsInOutput,
            SubmitTxErrorAddressAttributesTooLarge,
            SubmitTxErrorTriesToForgeAda,
            SubmitTxErrorDelegateNotRegistered,
            SubmitTxErrorUnknownOrIncompleteWithdrawals,
            SubmitTxErrorStakePoolNotRegistered,
            SubmitTxErrorWrongRetirementEpoch,
            SubmitTxErrorWrongPoolCertificate,
            SubmitTxErrorStakeKeyAlreadyRegistered,
            SubmitTxErrorPoolCostTooSmall,
            SubmitTxErrorPoolMetadataHashTooBig,
            SubmitTxErrorStakeKeyNotRegistered,
            SubmitTxErrorRewardAccountNotExisting,
            SubmitTxErrorRewardAccountNotEmpty,
            SubmitTxErrorWrongCertificateType,
            SubmitTxErrorUnknownGenesisKey,
            SubmitTxErrorAlreadyDelegating,
            SubmitTxErrorInsufficientFundsForMir,
            SubmitTxErrorTooLateForMir,
            SubmitTxErrorMirTransferNotCurrentlyAllowed,
            SubmitTxErrorMirNegativeTransferNotCurrentlyAllowed,
            SubmitTxErrorMirProducesNegativeUpdate,
            SubmitTxErrorDuplicateGenesisVrf,
            SubmitTxErrorNonGenesisVoters,
            SubmitTxErrorUpdateWrongEpoch,
            SubmitTxErrorProtocolVersionCannotFollow,
            SubmitTxErrorMissingRequiredRedeemers,
            MissingRequiredDatums,
            SubmitTxErrorUnspendableDatums,
            SubmitTxErrorExtraDataMismatch,
            SubmitTxErrorMissingRequiredSignatures,
            SubmitTxErrorUnspendableScriptInputs,
            ExtraRedeemers,
            SubmitTxErrorMissingDatumHashesForInputs,
            SubmitTxErrorMissingCollateralInputs,
            SubmitTxErrorCollateralTooSmall,
            SubmitTxErrorCollateralIsScript,
            SubmitTxErrorCollateralHasNonAdaAssets,
            SubmitTxErrorTooManyCollateralInputs,
            SubmitTxErrorExecutionUnitsTooLarge,
            SubmitTxErrorOutsideForecast,
            SubmitTxErrorValidationTagMismatch,
            SubmitTxErrorCollectErrors,
            SubmitTxErrorExtraScriptWitnesses,
            SubmitTxErrorMirNegativeTransfer,
            SubmitTxErrorTotalCollateralMismatch,
            SubmitTxErrorMalformedReferenceScripts,
            SubmitTxErrorMalformedScriptWitnesses,
        ]
    ]


class Result(BaseModel):
    acquire_failure: Optional[AcquireFailure] = Field(None, alias="AcquireFailure")
    acquire_success: Optional[AcquireSuccess] = Field(None, alias="AcquireSuccess")
    await_acquired: Optional[AwaitAcquired] = Field(None, alias="AwaitAcquired")
    evaluation_result: Optional[EvaluationResult] = Field(
        None, alias="EvaluationResult"
    )
    intersection_found: Optional[IntersectionFound] = Field(
        None, alias="IntersectionFound"
    )
    intersection_not_found: Optional[IntersectionNotFound] = Field(
        None, alias="IntersectionNotFound"
    )
    released: Optional[str] = Field(None, alias="Released")
    roll_backward: Optional[RollBackward] = Field(None, alias="RollBackward")
    roll_forward: Optional[RollForward] = Field(None, alias="RollForward")
    submit_success: Optional[SubmitSuccess] = Field(
        None, alias="SubmitTransactionSuccess"
    )
    submit_tx_error: Optional[SubmitTxError] = Field(None, alias="SubmitTxError")


class FindIntersectResult(BaseModel):
    intersection_found: Optional[IntersectionFound] = Field(
        None, alias="IntersectionFound"
    )
    intersection_not_found: Optional[IntersectionNotFound] = Field(
        None, alias="IntersectionNotFound"
    )
