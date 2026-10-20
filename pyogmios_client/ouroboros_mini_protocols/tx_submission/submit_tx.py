from typing import List

from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import Method
from pyogmios_client.exceptions import UnknownResultError, EraMismatchError
from pyogmios_client.models import (
    TxId,
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
)
from pyogmios_client.models.request_model import Request
from pyogmios_client.models.response_model import (
    SubmitTxResponse,
    SubmitTxResponseSubmitFail,
    SubmitTxResponseSubmitSuccess,
)
from pyogmios_client.ouroboros_mini_protocols.tx_submission.submission_errors import (
    SubmitTxErrorShelley,
    InvalidWitnessesError,
    MissingScriptWitnessesError,
    MissingVkWitnessesError,
    ScriptWitnessNotValidatingError,
    InsufficientGenesisSignaturesError,
    MissingTxMetadataError,
    MissingTxMetadataHashError,
    TxMetadataHashMismatchError,
    BadInputsError,
    ExpiredUtxoError,
    OutsideOfValidityIntervalError,
    TxTooLargeError,
    MissingAtLeastOneInputUtxoError,
    InvalidMetadataError,
    FeeTooSmallError,
    ValueNotConservedError,
    NetworkMismatchError,
    OutputTooSmallError,
    TooManyAssetsInOutputError,
    AddressAttributesTooLargeError,
    TriesToForgeAdaError,
    DelegateNotRegisteredError,
    UnknownOrIncompleteWithdrawalsError,
    StakePoolNotRegisteredError,
    WrongRetirementEpochError,
    WrongPoolCertificateError,
    StakeKeyAlreadyRegisteredError,
    PoolCostTooSmallError,
    PoolMetadataHashTooBigError,
    StakeKeyNotRegisteredError,
    RewardAccountNotExistingError,
    RewardAccountNotEmptyError,
    WrongCertificateTypeError,
    UnknownGenesisKeyError,
    AlreadyDelegatingError,
    InsufficientFundsForMirError,
    TooLateForMirError,
    MirTransferNotCurrentlyAllowedError,
    MirNegativeTransferNotCurrentlyAllowedError,
    MirProducesNegativeUpdateError,
    DuplicateGenesisVrfError,
    NonGenesisVotersError,
    UpdateWrongEpochError,
    ProtocolVersionCannotFollowError,
    MissingRequiredRedeemersError,
    MissingRequiredDatumsError,
    UnspendableDatumsError,
    ExtraDataMismatchError,
    MissingRequiredSignaturesError,
    UnspendableScriptInputsError,
    ExtraRedeemersError,
    MissingDatumHashesForInputsError,
    MissingCollateralInputsError,
    CollateralTooSmallError,
    CollateralIsScriptError,
    CollateralHasNonAdaAssetsError,
    TooManyCollateralInputsError,
    ExecutionUnitsTooLargeError,
    OutsideForecastError,
    ValidationTagMismatchError,
    CollectErrorsError,
    ExtraScriptWitnessesError,
    MirNegativeTransferError,
    TotalCollateralMismatchError,
    MalformedReferenceScriptsError,
    MalformedScriptWitnessesError,
)
from pyogmios_client.request import send_request


async def submit_tx(
    context: InteractionContext, bytes_: str
) -> TxId | List[SubmitTxErrorShelley]:
    """
    Evaluate a transaction.
    :param context: The interaction context
    :param bytes_: The bytes
    :return: The tx id
    """
    request = Request.from_base_request(
        method_name=Method.SUBMIT_TRANSACTION,
        args={"submit": bytes_},
    )
    try:
        # websocket = context.socket
        # websocket.send(request.json())
        # result = websocket.sock.recv()
        evaluate_tx_response = SubmitTxResponse.model_validate(
            await send_request(request, context)
        )
        return handle_submit_tx_response(evaluate_tx_response)
    except Exception as error:
        raise error


def handle_submit_tx_response(
    response: SubmitTxResponse,
) -> TxId | List[SubmitTxErrorShelley]:
    """
    Handle submit tx response.
    :param response: The response
    :return: The tx id
    """
    try:
        result = response.result
        errors = []
        if isinstance(result, SubmitTxResponseSubmitSuccess):
            return result.SubmitSuccess.txId
        elif isinstance(result, SubmitTxResponseSubmitFail):
            submit_tx_error = result.SubmitFail
            for tx_error in submit_tx_error:
                if isinstance(tx_error, SubmitTxErrorEraMismatch):
                    errors += EraMismatchError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorInvalidWitnesses):
                    errors += InvalidWitnessesError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMissingVkWitnesses):
                    errors += MissingVkWitnessesError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMissingScriptWitnesses):
                    errors += MissingScriptWitnessesError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorScriptWitnessNotValidating):
                    errors += ScriptWitnessNotValidatingError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorInsufficientGenesisSignatures):
                    errors += InsufficientGenesisSignaturesError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMissingTxMetadata):
                    errors += MissingTxMetadataError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMissingTxMetadataHash):
                    errors += MissingTxMetadataHashError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorTxMetadataHashMismatch):
                    errors += TxMetadataHashMismatchError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorBadInputs):
                    errors += BadInputsError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorExpiredUtxo):
                    errors += ExpiredUtxoError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorOutsideOfValidityInterval):
                    errors += OutsideOfValidityIntervalError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorTxTooLarge):
                    errors += TxTooLargeError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMissingAtLeastOneInputUtxo):
                    errors += MissingAtLeastOneInputUtxoError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorInvalidMetadata):
                    errors += InvalidMetadataError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorFeeTooSmall):
                    errors += FeeTooSmallError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorValueNotConserved):
                    errors += ValueNotConservedError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorNetworkMismatch):
                    errors += NetworkMismatchError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorOutputTooSmall):
                    errors += OutputTooSmallError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorTooManyAssetsInOutput):
                    errors += TooManyAssetsInOutputError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorAddressAttributesTooLarge):
                    errors += AddressAttributesTooLargeError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorTriesToForgeAda):
                    errors += TriesToForgeAdaError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorDelegateNotRegistered):
                    errors += DelegateNotRegisteredError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorUnknownOrIncompleteWithdrawals):
                    errors += UnknownOrIncompleteWithdrawalsError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorStakePoolNotRegistered):
                    errors += StakePoolNotRegisteredError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorWrongRetirementEpoch):
                    errors += WrongRetirementEpochError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorWrongPoolCertificate):
                    errors += WrongPoolCertificateError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorStakeKeyAlreadyRegistered):
                    errors += StakeKeyAlreadyRegisteredError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorPoolCostTooSmall):
                    errors += PoolCostTooSmallError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorPoolMetadataHashTooBig):
                    errors += PoolMetadataHashTooBigError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorStakeKeyNotRegistered):
                    errors += StakeKeyNotRegisteredError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorRewardAccountNotExisting):
                    errors += RewardAccountNotExistingError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorRewardAccountNotEmpty):
                    errors += RewardAccountNotEmptyError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorWrongCertificateType):
                    errors += WrongCertificateTypeError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorUnknownGenesisKey):
                    errors += UnknownGenesisKeyError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorAlreadyDelegating):
                    errors += AlreadyDelegatingError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorInsufficientFundsForMir):
                    errors += InsufficientFundsForMirError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorTooLateForMir):
                    errors += TooLateForMirError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMirTransferNotCurrentlyAllowed):
                    errors += MirTransferNotCurrentlyAllowedError(tx_error)
                elif isinstance(
                    tx_error, SubmitTxErrorMirNegativeTransferNotCurrentlyAllowed
                ):
                    errors += MirNegativeTransferNotCurrentlyAllowedError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMirProducesNegativeUpdate):
                    errors += MirProducesNegativeUpdateError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorDuplicateGenesisVrf):
                    errors += DuplicateGenesisVrfError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorNonGenesisVoters):
                    errors += NonGenesisVotersError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorUpdateWrongEpoch):
                    errors += UpdateWrongEpochError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorProtocolVersionCannotFollow):
                    errors += ProtocolVersionCannotFollowError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMissingRequiredRedeemers):
                    errors += MissingRequiredRedeemersError(tx_error)
                elif isinstance(tx_error, MissingRequiredDatums):
                    errors += MissingRequiredDatumsError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorUnspendableDatums):
                    errors += UnspendableDatumsError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorExtraDataMismatch):
                    errors += ExtraDataMismatchError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMissingRequiredSignatures):
                    errors += MissingRequiredSignaturesError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorUnspendableScriptInputs):
                    errors += UnspendableScriptInputsError(tx_error)
                elif isinstance(tx_error, ExtraRedeemers):
                    errors += ExtraRedeemersError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMissingDatumHashesForInputs):
                    errors += MissingDatumHashesForInputsError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMissingCollateralInputs):
                    errors += MissingCollateralInputsError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorCollateralTooSmall):
                    errors += CollateralTooSmallError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorCollateralIsScript):
                    errors += CollateralIsScriptError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorCollateralHasNonAdaAssets):
                    errors += CollateralHasNonAdaAssetsError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorTooManyCollateralInputs):
                    errors += TooManyCollateralInputsError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorExecutionUnitsTooLarge):
                    errors += ExecutionUnitsTooLargeError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorOutsideForecast):
                    errors += OutsideForecastError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorValidationTagMismatch):
                    errors += ValidationTagMismatchError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorCollectErrors):
                    errors += CollectErrorsError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorExtraScriptWitnesses):
                    errors += ExtraScriptWitnessesError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMirNegativeTransfer):
                    errors += MirNegativeTransferError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorTotalCollateralMismatch):
                    errors += TotalCollateralMismatchError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMalformedReferenceScripts):
                    errors += MalformedReferenceScriptsError(tx_error)
                elif isinstance(tx_error, SubmitTxErrorMalformedScriptWitnesses):
                    errors += MalformedScriptWitnessesError(tx_error)
        else:
            errors += UnknownResultError(response)
        return errors
    except Exception as error:
        raise error
