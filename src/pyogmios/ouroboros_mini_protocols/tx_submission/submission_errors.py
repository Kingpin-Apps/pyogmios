import json
from typing import Union

from pyogmios.models import (
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
    ExtraRedeemers,
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
    MissingRequiredDatums,
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
    SubmitTxErrorMissingRequiredRedeemers,
    SubmitTxErrorAddressAttributesTooLarge,
)


class AddressAttributesTooLargeError(Exception):
    """
    Address attributes too large error.
    """

    def __init__(self, raw_error: SubmitTxErrorAddressAttributesTooLarge):
        super().__init__()
        self.message = json.dumps(raw_error.addressAttributesTooLarge)


class AlreadyDelegatingError(Exception):
    """
    Already delegating error.
    """

    def __init__(self, raw_error: SubmitTxErrorAlreadyDelegating):
        super().__init__()
        self.message = json.dumps(raw_error.alreadyDelegating)


class BadInputsError(Exception):
    """
    Bad inputs error.
    """

    def __init__(self, raw_error: SubmitTxErrorBadInputs):
        super().__init__()
        self.message = json.dumps(raw_error.badInputs)


class CollateralHasNonAdaAssetsError(Exception):
    """
    Collateral has non ada assets error.
    """

    def __init__(self, raw_error: SubmitTxErrorCollateralHasNonAdaAssets):
        super().__init__()
        self.message = json.dumps(raw_error.collateralHasNonAdaAssets)


class CollateralIsScriptError(Exception):
    """
    Collateral is script error.
    """

    def __init__(self, raw_error: SubmitTxErrorCollateralIsScript):
        super().__init__()
        self.message = json.dumps(raw_error.collateralIsScript)


class CollateralTooSmallError(Exception):
    """
    Collateral too small error.
    """

    def __init__(self, raw_error: SubmitTxErrorCollateralTooSmall):
        super().__init__()
        self.message = json.dumps(raw_error.collateralTooSmall)


class CollectErrorsError(Exception):
    """
    Collect errors error.
    """

    def __init__(self, raw_error: SubmitTxErrorCollectErrors):
        super().__init__()
        self.message = json.dumps(raw_error.collectErrors)


class DelegateNotRegisteredError(Exception):
    """
    Delegate not registered error.
    """

    def __init__(self, raw_error: SubmitTxErrorDelegateNotRegistered):
        super().__init__()
        self.message = json.dumps(raw_error.delegateNotRegistered)


class DuplicateGenesisVrfError(Exception):
    """
    Duplicate genesis vrf error.
    """

    def __init__(self, raw_error: SubmitTxErrorDuplicateGenesisVrf):
        super().__init__()
        self.message = json.dumps(raw_error.duplicateGenesisVrf)


class EraMismatchError(Exception):
    """
    Era mismatch error.
    """

    def __init__(self, raw_error: SubmitTxErrorEraMismatch):
        super().__init__()
        self.message = json.dumps(raw_error.eraMismatch)


class ExecutionUnitsTooLargeError(Exception):
    """
    Execution units too large error.
    """

    def __init__(self, raw_error: SubmitTxErrorExecutionUnitsTooLarge):
        super().__init__()
        self.message = json.dumps(raw_error.executionUnitsTooLarge)


class ExpiredUtxoError(Exception):
    """
    Expired utxo error.
    """

    def __init__(self, raw_error: SubmitTxErrorExpiredUtxo):
        super().__init__()
        self.message = json.dumps(raw_error.expiredUtxo)


class ExtraDataMismatchError(Exception):
    """
    Extra data mismatch error.
    """

    def __init__(self, raw_error: SubmitTxErrorExtraDataMismatch):
        super().__init__()
        self.message = json.dumps(raw_error.extraDataMismatch)


class ExtraRedeemersError(Exception):
    """
    Extra redeemers error.
    """

    def __init__(self, raw_error: ExtraRedeemers):
        super().__init__()
        self.message = json.dumps(raw_error.extraRedeemers)


class ExtraScriptWitnessesError(Exception):
    """
    Extra script witnesses error.
    """

    def __init__(self, raw_error: SubmitTxErrorExtraScriptWitnesses):
        super().__init__()
        self.message = json.dumps(raw_error.extraScriptWitnesses)


class FeeTooSmallError(Exception):
    """
    Extra script witnesses error.
    """

    def __init__(self, raw_error: SubmitTxErrorFeeTooSmall):
        super().__init__()
        self.message = json.dumps(raw_error.feeTooSmall)


class InsufficientFundsForMirError(Exception):
    """
    Insufficient funds for mir error.
    """

    def __init__(self, raw_error: SubmitTxErrorInsufficientFundsForMir):
        super().__init__()
        self.message = json.dumps(raw_error.insufficientFundsForMir)


class InsufficientGenesisSignaturesError(Exception):
    """
    Insufficient genesis signatures error.
    """

    def __init__(self, raw_error: SubmitTxErrorInsufficientGenesisSignatures):
        super().__init__()
        self.message = json.dumps(raw_error.insufficientGenesisSignatures)


class InvalidMetadataError(Exception):
    """
    Invalid metadata error.
    """

    def __init__(self, raw_error: SubmitTxErrorInvalidMetadata):
        super().__init__()
        self.message = json.dumps(raw_error.invalidMetadata)


class InvalidWitnessesError(Exception):
    """
    Invalid witnesses error.
    """

    def __init__(self, raw_error: SubmitTxErrorInvalidWitnesses):
        super().__init__()
        self.message = json.dumps(raw_error.invalidWitnesses)


class MalformedReferenceScriptsError(Exception):
    """
    Malformed reference scripts error.
    """

    def __init__(self, raw_error: SubmitTxErrorMalformedReferenceScripts):
        super().__init__()
        self.message = json.dumps(raw_error.malformedReferenceScripts)


class MalformedScriptWitnessesError(Exception):
    """
    Malformed script witnesses error.
    """

    def __init__(self, raw_error: SubmitTxErrorMalformedScriptWitnesses):
        super().__init__()
        self.message = json.dumps(raw_error.malformedScriptWitnesses)


class MirNegativeTransferError(Exception):
    """
    Mir negative transfer error.
    """

    def __init__(self, raw_error: SubmitTxErrorMirNegativeTransfer):
        super().__init__()
        self.message = json.dumps(raw_error.mirNegativeTransfer)


class MirNegativeTransferNotCurrentlyAllowedError(Exception):
    """
    Mir negative transfer not currently allowed error.
    """

    def __init__(self, raw_error: SubmitTxErrorMirNegativeTransferNotCurrentlyAllowed):
        super().__init__()
        self.message = json.dumps(raw_error.mirNegativeTransferNotCurrentlyAllowed)


class MirProducesNegativeUpdateError(Exception):
    """
    Mir produces negative update error.
    """

    def __init__(self, raw_error: SubmitTxErrorMirProducesNegativeUpdate):
        super().__init__()
        self.message = json.dumps(raw_error.mirProducesNegativeUpdate)


class MirTransferNotCurrentlyAllowedError(Exception):
    """
    Mir transfer not currently allowed error.
    """

    def __init__(self, raw_error: SubmitTxErrorMirTransferNotCurrentlyAllowed):
        super().__init__()
        self.message = json.dumps(raw_error.mirTransferNotCurrentlyAllowed)


class MissingAtLeastOneInputUtxoError(Exception):
    """
    Missing at least one input utxo error.
    """

    def __init__(self, raw_error: SubmitTxErrorMissingAtLeastOneInputUtxo):
        super().__init__()
        self.message = json.dumps(raw_error.missingAtLeastOneInputUtxo)


class MissingCollateralInputsError(Exception):
    """
    Missing collateral inputs error.
    """

    def __init__(self, raw_error: SubmitTxErrorMissingCollateralInputs):
        super().__init__()
        self.message = json.dumps(raw_error.missingCollateralInputs)


class MissingDatumHashesForInputsError(Exception):
    """
    Missing datum hashes for inputs error.
    """

    def __init__(self, raw_error: SubmitTxErrorMissingDatumHashesForInputs):
        super().__init__()
        self.message = json.dumps(raw_error.missingDatumHashesForInputs)


class MissingRequiredDatumsError(Exception):
    """
    Missing input witnesses error.
    """

    def __init__(self, raw_error: MissingRequiredDatums):
        super().__init__()
        self.message = json.dumps(raw_error.missingRequiredDatums)


class MissingRequiredRedeemersError(Exception):
    """
    Missing input witnesses error.
    """

    def __init__(self, raw_error: SubmitTxErrorMissingRequiredRedeemers):
        super().__init__()
        self.message = json.dumps(raw_error.missingRequiredRedeemers)


class MissingRequiredSignaturesError(Exception):
    """
    Missing input witnesses error.
    """

    def __init__(self, raw_error: SubmitTxErrorMissingRequiredSignatures):
        super().__init__()
        self.message = json.dumps(raw_error.missingRequiredSignatures)


class MissingScriptWitnessesError(Exception):
    """
    Missing script witnesses error.
    """

    def __init__(self, raw_error: SubmitTxErrorMissingScriptWitnesses):
        super().__init__()
        self.message = json.dumps(raw_error.missingScriptWitnesses)


class MissingTxMetadataError(Exception):
    """
    Missing tx metadata error.
    """

    def __init__(self, raw_error: SubmitTxErrorMissingTxMetadata):
        super().__init__()
        self.message = json.dumps(raw_error.missingTxMetadata)


class MissingTxMetadataHashError(Exception):
    """
    Missing tx metadata hash error.
    """

    def __init__(self, raw_error: SubmitTxErrorMissingTxMetadataHash):
        super().__init__()
        self.message = json.dumps(raw_error.missingTxMetadataHash)


class MissingVkWitnessesError(Exception):
    """
    Missing vk witnesses error.
    """

    def __init__(self, raw_error: SubmitTxErrorMissingVkWitnesses):
        super().__init__()
        self.message = json.dumps(raw_error.missingVkWitnesses)


class NetworkMismatchError(Exception):
    """
    Network mismatch error.
    """

    def __init__(self, raw_error: SubmitTxErrorNetworkMismatch):
        super().__init__()
        self.message = json.dumps(raw_error.networkMismatch)


class NonGenesisVotersError(Exception):
    """
    Non genesis voters error.
    """

    def __init__(self, raw_error: SubmitTxErrorNonGenesisVoters):
        super().__init__()
        self.message = json.dumps(raw_error.nonGenesisVoters)


class OutputTooSmallError(Exception):
    """
    Output too small error.
    """

    def __init__(self, raw_error: SubmitTxErrorOutputTooSmall):
        super().__init__()
        self.message = json.dumps(raw_error.outputTooSmall)


class OutsideForecastError(Exception):
    """
    Outside forecast error.
    """

    def __init__(self, raw_error: SubmitTxErrorOutsideForecast):
        super().__init__()
        self.message = json.dumps(raw_error.outsideForecast)


class OutsideOfValidityIntervalError(Exception):
    """
    Outside of validity interval error.
    """

    def __init__(self, raw_error: SubmitTxErrorOutsideOfValidityInterval):
        super().__init__()
        self.message = json.dumps(raw_error.outsideOfValidityInterval)


class PoolCostTooSmallError(Exception):
    """
    Pool cost too small error.
    """

    def __init__(self, raw_error: SubmitTxErrorPoolCostTooSmall):
        super().__init__()
        self.message = json.dumps(raw_error.poolCostTooSmall)


class PoolMetadataHashTooBigError(Exception):
    """
    Pool metadata hash too big error.
    """

    def __init__(self, raw_error: SubmitTxErrorPoolMetadataHashTooBig):
        super().__init__()
        self.message = json.dumps(raw_error.poolMetadataHashTooBig)


class ProtocolVersionCannotFollowError(Exception):
    """
    Protocol version cannot follow error.
    """

    def __init__(self, raw_error: SubmitTxErrorProtocolVersionCannotFollow):
        super().__init__()
        self.message = json.dumps(raw_error.protocolVersionCannotFollow)


class RewardAccountNotEmptyError(Exception):
    """
    Reward account not empty error.
    """

    def __init__(self, raw_error: SubmitTxErrorRewardAccountNotEmpty):
        super().__init__()
        self.message = json.dumps(raw_error.rewardAccountNotEmpty)


class RewardAccountNotExistingError(Exception):
    """
    Reward account not existing error.
    """

    def __init__(self, raw_error: SubmitTxErrorRewardAccountNotExisting):
        super().__init__()
        self.message = json.dumps(raw_error.rewardAccountNotExisting)


class ScriptWitnessNotValidatingError(Exception):
    """
    Script witness not validating error.
    """

    def __init__(self, raw_error: SubmitTxErrorScriptWitnessNotValidating):
        super().__init__()
        self.message = json.dumps(raw_error.scriptWitnessNotValidating)


class StakeKeyAlreadyRegisteredError(Exception):
    """
    Stake key already registered error.
    """

    def __init__(self, raw_error: SubmitTxErrorStakeKeyAlreadyRegistered):
        super().__init__()
        self.message = json.dumps(raw_error.stakeKeyAlreadyRegistered)


class StakeKeyNotRegisteredError(Exception):
    """
    Stake key not registered error.
    """

    def __init__(self, raw_error: SubmitTxErrorStakeKeyNotRegistered):
        super().__init__()
        self.message = json.dumps(raw_error.stakeKeyNotRegistered)


class StakePoolNotRegisteredError(Exception):
    """
    Stake pool not registered error.
    """

    def __init__(self, raw_error: SubmitTxErrorStakePoolNotRegistered):
        super().__init__()
        self.message = json.dumps(raw_error.stakePoolNotRegistered)


class TooLateForMirError(Exception):
    """
    Too late for mir error.
    """

    def __init__(self, raw_error: SubmitTxErrorTooLateForMir):
        super().__init__()
        self.message = json.dumps(raw_error.tooLateForMir)


class TooManyAssetsInOutputError(Exception):
    """
    Too many assets in output error.
    """

    def __init__(self, raw_error: SubmitTxErrorTooManyAssetsInOutput):
        super().__init__()
        self.message = json.dumps(raw_error.tooManyAssetsInOutput)


class TooManyCollateralInputsError(Exception):
    """
    Too many collateral inputs error.
    """

    def __init__(self, raw_error: SubmitTxErrorTooManyCollateralInputs):
        super().__init__()
        self.message = json.dumps(raw_error.tooManyCollateralInputs)


class TotalCollateralMismatchError(Exception):
    """
    Total collateral mismatch error.
    """

    def __init__(self, raw_error: SubmitTxErrorTotalCollateralMismatch):
        super().__init__()
        self.message = json.dumps(raw_error.totalCollateralMismatch)


class TriesToForgeAdaError(Exception):
    """
    Tries to forge ada error.
    """

    def __init__(self, raw_error: SubmitTxErrorTriesToForgeAda):
        super().__init__()
        self.message = json.dumps(raw_error.triesToForgeAda)


class TxMetadataHashMismatchError(Exception):
    """
    Tx metadata hash mismatch error.
    """

    def __init__(self, raw_error: SubmitTxErrorTxMetadataHashMismatch):
        super().__init__()
        self.message = json.dumps(raw_error.txMetadataHashMismatch)


class TxTooLargeError(Exception):
    """
    Tx too large error.
    """

    def __init__(self, raw_error: SubmitTxErrorTxTooLarge):
        super().__init__()
        self.message = json.dumps(raw_error.txTooLarge)


class UnknownGenesisKeyError(Exception):
    """
    Unknown genesis key error.
    """

    def __init__(self, raw_error: SubmitTxErrorUnknownGenesisKey):
        super().__init__()
        self.message = json.dumps(raw_error.unknownGenesisKey)


class UnknownOrIncompleteWithdrawalsError(Exception):
    """
    Unknown or incomplete withdrawals error.
    """

    def __init__(self, raw_error: SubmitTxErrorUnknownOrIncompleteWithdrawals):
        super().__init__()
        self.message = json.dumps(raw_error.unknownOrIncompleteWithdrawals)


class UnspendableDatumsError(Exception):
    """
    Unspendable datums error.
    """

    def __init__(self, raw_error: SubmitTxErrorUnspendableDatums):
        super().__init__()
        self.message = json.dumps(raw_error.unspendableDatums)


class UnspendableScriptInputsError(Exception):
    """
    Unspendable script inputs error.
    """

    def __init__(self, raw_error: SubmitTxErrorUnspendableScriptInputs):
        super().__init__()
        self.message = json.dumps(raw_error.unspendableScriptInputs)


class UpdateWrongEpochError(Exception):
    """
    Update wrong epoch error.
    """

    def __init__(self, raw_error: SubmitTxErrorUpdateWrongEpoch):
        super().__init__()
        self.message = json.dumps(raw_error.updateWrongEpoch)


class ValidationTagMismatchError(Exception):
    """
    Validation tag mismatch error.
    """

    def __init__(self, raw_error: SubmitTxErrorValidationTagMismatch):
        super().__init__()
        self.message = json.dumps(raw_error.validationTagMismatch)


class ValueNotConservedError(Exception):
    """
    Value not conserved error.
    """

    def __init__(self, raw_error: SubmitTxErrorValueNotConserved):
        super().__init__()
        self.message = json.dumps(raw_error.valueNotConserved)


class WrongCertificateTypeError(Exception):
    """
    Wrong certificate type error.
    """

    def __init__(self, raw_error: SubmitTxErrorWrongCertificateType):
        super().__init__()
        self.message = json.dumps(raw_error.wrongCertificateType)


class WrongPoolCertificateError(Exception):
    """
    Wrong pool certificate error.
    """

    def __init__(self, raw_error: SubmitTxErrorWrongPoolCertificate):
        super().__init__()
        self.message = json.dumps(raw_error.wrongPoolCertificate)


class WrongRetirementEpochError(Exception):
    """
    Wrong retirement epoch error.
    """

    def __init__(self, raw_error: SubmitTxErrorWrongRetirementEpoch):
        super().__init__()
        self.message = json.dumps(raw_error.wrongRetirementEpoch)


SubmitTxErrorShelley = Union[
    AddressAttributesTooLargeError,
    AlreadyDelegatingError,
    BadInputsError,
    CollateralHasNonAdaAssetsError,
    CollateralIsScriptError,
    CollateralTooSmallError,
    CollectErrorsError,
    DelegateNotRegisteredError,
    DuplicateGenesisVrfError,
    EraMismatchError,
    ExecutionUnitsTooLargeError,
    ExpiredUtxoError,
    ExtraDataMismatchError,
    ExtraRedeemersError,
    ExtraScriptWitnessesError,
    FeeTooSmallError,
    InsufficientFundsForMirError,
    InsufficientGenesisSignaturesError,
    InvalidMetadataError,
    InvalidWitnessesError,
    MalformedReferenceScriptsError,
    MalformedScriptWitnessesError,
    MirNegativeTransferError,
    MirNegativeTransferNotCurrentlyAllowedError,
    MirProducesNegativeUpdateError,
    MirTransferNotCurrentlyAllowedError,
    MissingAtLeastOneInputUtxoError,
    MissingCollateralInputsError,
    MissingDatumHashesForInputsError,
    MissingRequiredDatumsError,
    MissingRequiredRedeemersError,
    MissingRequiredSignaturesError,
    MissingScriptWitnessesError,
    MissingTxMetadataError,
    MissingTxMetadataHashError,
    MissingVkWitnessesError,
    NetworkMismatchError,
    NonGenesisVotersError,
    OutputTooSmallError,
    OutsideForecastError,
    OutsideOfValidityIntervalError,
    PoolCostTooSmallError,
    PoolMetadataHashTooBigError,
    ProtocolVersionCannotFollowError,
    RewardAccountNotEmptyError,
    RewardAccountNotExistingError,
    ScriptWitnessNotValidatingError,
    StakeKeyAlreadyRegisteredError,
    StakeKeyNotRegisteredError,
    StakePoolNotRegisteredError,
    TooLateForMirError,
    TooManyAssetsInOutputError,
    TooManyCollateralInputsError,
    TotalCollateralMismatchError,
    TriesToForgeAdaError,
    TxMetadataHashMismatchError,
    TxTooLargeError,
    UnknownGenesisKeyError,
    UnknownOrIncompleteWithdrawalsError,
    UnspendableDatumsError,
    UnspendableScriptInputsError,
    UpdateWrongEpochError,
    ValidationTagMismatchError,
    ValueNotConservedError,
    WrongCertificateTypeError,
    WrongPoolCertificateError,
    WrongRetirementEpochError,
]
