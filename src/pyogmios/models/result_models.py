from pydantic import Field, RootModel, model_validator

from pyogmios.enums import AcquireFailureDetails
from pyogmios.models import (
    Any,
    Block,
    EraMismatch,
    ExecutionUnits,
    ExtraRedeemers,
    MissingRequiredDatums,
    PointOrOrigin,
    Slot,
    SubmitTxErrorAddressAttributesTooLarge,
    SubmitTxErrorAlreadyDelegating,
    SubmitTxErrorBadInputs,
    SubmitTxErrorCollateralHasNonAdaAssets,
    SubmitTxErrorCollateralIsScript,
    SubmitTxErrorCollateralTooSmall,
    SubmitTxErrorCollectErrors,
    SubmitTxErrorDelegateNotRegistered,
    SubmitTxErrorDuplicateGenesisVrf,
    SubmitTxErrorEraMismatch,
    SubmitTxErrorExecutionUnitsTooLarge,
    SubmitTxErrorExpiredUtxo,
    SubmitTxErrorExtraDataMismatch,
    SubmitTxErrorExtraScriptWitnesses,
    SubmitTxErrorFeeTooSmall,
    SubmitTxErrorInsufficientFundsForMir,
    SubmitTxErrorInsufficientGenesisSignatures,
    SubmitTxErrorInvalidMetadata,
    SubmitTxErrorInvalidWitnesses,
    SubmitTxErrorMalformedReferenceScripts,
    SubmitTxErrorMalformedScriptWitnesses,
    SubmitTxErrorMirNegativeTransfer,
    SubmitTxErrorMirNegativeTransferNotCurrentlyAllowed,
    SubmitTxErrorMirProducesNegativeUpdate,
    SubmitTxErrorMirTransferNotCurrentlyAllowed,
    SubmitTxErrorMissingAtLeastOneInputUtxo,
    SubmitTxErrorMissingCollateralInputs,
    SubmitTxErrorMissingDatumHashesForInputs,
    SubmitTxErrorMissingRequiredRedeemers,
    SubmitTxErrorMissingRequiredSignatures,
    SubmitTxErrorMissingScriptWitnesses,
    SubmitTxErrorMissingTxMetadata,
    SubmitTxErrorMissingTxMetadataHash,
    SubmitTxErrorMissingVkWitnesses,
    SubmitTxErrorNetworkMismatch,
    SubmitTxErrorNonGenesisVoters,
    SubmitTxErrorOutputTooSmall,
    SubmitTxErrorOutsideForecast,
    SubmitTxErrorOutsideOfValidityInterval,
    SubmitTxErrorPoolCostTooSmall,
    SubmitTxErrorPoolMetadataHashTooBig,
    SubmitTxErrorProtocolVersionCannotFollow,
    SubmitTxErrorRewardAccountNotEmpty,
    SubmitTxErrorRewardAccountNotExisting,
    SubmitTxErrorScriptWitnessNotValidating,
    SubmitTxErrorStakeKeyAlreadyRegistered,
    SubmitTxErrorStakeKeyNotRegistered,
    SubmitTxErrorStakePoolNotRegistered,
    SubmitTxErrorTooLateForMir,
    SubmitTxErrorTooManyAssetsInOutput,
    SubmitTxErrorTooManyCollateralInputs,
    SubmitTxErrorTotalCollateralMismatch,
    SubmitTxErrorTriesToForgeAda,
    SubmitTxErrorTxMetadataHashMismatch,
    SubmitTxErrorTxTooLarge,
    SubmitTxErrorUnknownGenesisKey,
    SubmitTxErrorUnknownOrIncompleteWithdrawals,
    SubmitTxErrorUnspendableDatums,
    SubmitTxErrorUnspendableScriptInputs,
    SubmitTxErrorUpdateWrongEpoch,
    SubmitTxErrorValidationTagMismatch,
    SubmitTxErrorValueNotConserved,
    SubmitTxErrorWrongCertificateType,
    SubmitTxErrorWrongPoolCertificate,
    SubmitTxErrorWrongRetirementEpoch,
    TipOrOrigin,
    TxId,
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
    evaluation_result: dict[str, ExecutionUnits] = Field(None, alias="EvaluationResult")


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
    eraMismatch: EraMismatch | None = None


class SubmitTxError(RootModel):
    root: list[
        SubmitTxErrorEraMismatch
        | SubmitTxErrorInvalidWitnesses
        | SubmitTxErrorMissingVkWitnesses
        | SubmitTxErrorMissingScriptWitnesses
        | SubmitTxErrorScriptWitnessNotValidating
        | SubmitTxErrorInsufficientGenesisSignatures
        | SubmitTxErrorMissingTxMetadata
        | SubmitTxErrorMissingTxMetadataHash
        | SubmitTxErrorTxMetadataHashMismatch
        | SubmitTxErrorBadInputs
        | SubmitTxErrorExpiredUtxo
        | SubmitTxErrorOutsideOfValidityInterval
        | SubmitTxErrorTxTooLarge
        | SubmitTxErrorMissingAtLeastOneInputUtxo
        | SubmitTxErrorInvalidMetadata
        | SubmitTxErrorFeeTooSmall
        | SubmitTxErrorValueNotConserved
        | SubmitTxErrorNetworkMismatch
        | SubmitTxErrorOutputTooSmall
        | SubmitTxErrorTooManyAssetsInOutput
        | SubmitTxErrorAddressAttributesTooLarge
        | SubmitTxErrorTriesToForgeAda
        | SubmitTxErrorDelegateNotRegistered
        | SubmitTxErrorUnknownOrIncompleteWithdrawals
        | SubmitTxErrorStakePoolNotRegistered
        | SubmitTxErrorWrongRetirementEpoch
        | SubmitTxErrorWrongPoolCertificate
        | SubmitTxErrorStakeKeyAlreadyRegistered
        | SubmitTxErrorPoolCostTooSmall
        | SubmitTxErrorPoolMetadataHashTooBig
        | SubmitTxErrorStakeKeyNotRegistered
        | SubmitTxErrorRewardAccountNotExisting
        | SubmitTxErrorRewardAccountNotEmpty
        | SubmitTxErrorWrongCertificateType
        | SubmitTxErrorUnknownGenesisKey
        | SubmitTxErrorAlreadyDelegating
        | SubmitTxErrorInsufficientFundsForMir
        | SubmitTxErrorTooLateForMir
        | SubmitTxErrorMirTransferNotCurrentlyAllowed
        | SubmitTxErrorMirNegativeTransferNotCurrentlyAllowed
        | SubmitTxErrorMirProducesNegativeUpdate
        | SubmitTxErrorDuplicateGenesisVrf
        | SubmitTxErrorNonGenesisVoters
        | SubmitTxErrorUpdateWrongEpoch
        | SubmitTxErrorProtocolVersionCannotFollow
        | SubmitTxErrorMissingRequiredRedeemers
        | MissingRequiredDatums
        | SubmitTxErrorUnspendableDatums
        | SubmitTxErrorExtraDataMismatch
        | SubmitTxErrorMissingRequiredSignatures
        | SubmitTxErrorUnspendableScriptInputs
        | ExtraRedeemers
        | SubmitTxErrorMissingDatumHashesForInputs
        | SubmitTxErrorMissingCollateralInputs
        | SubmitTxErrorCollateralTooSmall
        | SubmitTxErrorCollateralIsScript
        | SubmitTxErrorCollateralHasNonAdaAssets
        | SubmitTxErrorTooManyCollateralInputs
        | SubmitTxErrorExecutionUnitsTooLarge
        | SubmitTxErrorOutsideForecast
        | SubmitTxErrorValidationTagMismatch
        | SubmitTxErrorCollectErrors
        | SubmitTxErrorExtraScriptWitnesses
        | SubmitTxErrorMirNegativeTransfer
        | SubmitTxErrorTotalCollateralMismatch
        | SubmitTxErrorMalformedReferenceScripts
        | SubmitTxErrorMalformedScriptWitnesses
    ]


class Result(BaseModel):
    acquire_failure: AcquireFailure | None = Field(None, alias="AcquireFailure")
    acquire_success: AcquireSuccess | None = Field(None, alias="AcquireSuccess")
    await_acquired: AwaitAcquired | None = Field(None, alias="AwaitAcquired")
    evaluation_result: EvaluationResult | None = Field(None, alias="EvaluationResult")
    intersection_found: IntersectionFound | None = Field(None, alias="IntersectionFound")
    intersection_not_found: IntersectionNotFound | None = Field(None, alias="IntersectionNotFound")
    released: str | None = Field(None, alias="Released")
    roll_backward: RollBackward | None = Field(None, alias="RollBackward")
    roll_forward: RollForward | None = Field(None, alias="RollForward")
    submit_success: SubmitSuccess | None = Field(None, alias="SubmitTransactionSuccess")
    submit_tx_error: SubmitTxError | None = Field(None, alias="SubmitTxError")


class FindIntersectResult(BaseModel):
    intersection_found: IntersectionFound | None = Field(None, alias="IntersectionFound")
    intersection_not_found: IntersectionNotFound | None = Field(None, alias="IntersectionNotFound")
