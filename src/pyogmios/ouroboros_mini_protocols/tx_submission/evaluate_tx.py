"""
This module contains the evaluate_tx function.

The evaluate_tx function is used to evaluate a transaction.
"""

from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import UnknownResultError
from pyogmios.models import (
    EvaluationFailure,
    EvaluationFailureAdditionalUtxoOverlap,
    EvaluationFailureCannotCreateEvaluationContext,
    EvaluationFailureIncompatibleEra,
    EvaluationFailureNotEnoughSynced,
    EvaluationFailureScriptFailures,
    EvaluationResult,
    ExtraRedeemers,
    IllFormedExecutionBudget,
    MissingRequiredScripts,
    NoCostModelForLanguage,
    NonScriptInputReferencedByRedeemer,
    UnknownInputReferencedByRedeemer,
    Utxo,
)
from pyogmios.models import (
    ValidatorFailedError as ValidatorFailedErrorModel,
)
from pyogmios.models.request_model import Request
from pyogmios.models.response_model import EvaluateTxResponse
from pyogmios.ouroboros_mini_protocols.tx_submission.evaluation_errors import (
    AdditionalUtxoOverlapError,
    CannotCreateEvaluationContextError,
    ExtraRedeemersError,
    IllFormedExecutionBudgetError,
    IncompatibleEraError,
    MissingRequiredDatums,
    MissingRequiredDatumsError,
    MissingRequiredScriptsError,
    NoCostModelForLanguageError,
    NonScriptInputReferencedByRedeemerError,
    NotEnoughSyncedError,
    UnknownInputReferencedByRedeemerError,
    ValidatorFailedError,
)
from pyogmios.request import send_request


async def evaluate_tx(
    context: InteractionContext, bytes_: str, additional_utxo_set: Utxo | None = None
) -> EvaluationResult | list[Exception]:
    """
    Evaluate a transaction.
    :param context: The interaction context
    :param bytes_: The bytes
    :param additional_utxo_set: The additional utxo set
    :return: The evaluation result
    """
    request = Request.from_base_request(
        method_name=Method.EVALUATE_TRANSACTION,
        args={
            **(
                {"additionalUtxoSet": additional_utxo_set}
                if additional_utxo_set is not None
                else {}
            ),
            "evaluate": bytes_,
        },
    )
    try:
        # websocket = context.socket
        # websocket.send(request.json())
        # result = websocket.sock.recv()
        evaluate_tx_response = EvaluateTxResponse.model_validate(
            await send_request(request, context)
        )
        return handle_evaluate_tx_response(evaluate_tx_response)
    except Exception as error:
        raise error


def handle_evaluate_tx_response(
    response: EvaluateTxResponse,
) -> EvaluationResult | list[Exception]:
    """
    Handle the evaluate tx response.
    :param response: The response
    :return: The evaluation result
    """
    try:
        result = response.result
        errors = []
        if isinstance(result, EvaluationResult):
            return result
        elif isinstance(result, EvaluationFailure):
            evaluation_failure = result.EvaluationFailure
            if isinstance(evaluation_failure, EvaluationFailureScriptFailures):
                script_failures = evaluation_failure.ScriptFailures
                for k in script_failures:
                    failure = script_failures[k]
                    if isinstance(failure, ExtraRedeemers):
                        errors += ExtraRedeemersError(failure)
                    elif isinstance(failure, IllFormedExecutionBudget):
                        errors += IllFormedExecutionBudgetError(failure)
                    elif isinstance(failure, MissingRequiredDatums):
                        errors += MissingRequiredDatumsError(failure)
                    elif isinstance(failure, MissingRequiredScripts):
                        errors += MissingRequiredScriptsError(failure)
                    elif isinstance(failure, NoCostModelForLanguage):
                        errors += NoCostModelForLanguageError(failure)
                    elif isinstance(failure, NonScriptInputReferencedByRedeemer):
                        errors += NonScriptInputReferencedByRedeemerError(failure)
                    elif isinstance(failure, UnknownInputReferencedByRedeemer):
                        errors += UnknownInputReferencedByRedeemerError(failure)
                    elif isinstance(failure, ValidatorFailedErrorModel):
                        errors += ValidatorFailedError(failure)
                    else:
                        errors += UnknownResultError(response)
            elif isinstance(result, EvaluationFailureIncompatibleEra):
                errors += IncompatibleEraError(result)
            elif isinstance(result, EvaluationFailureAdditionalUtxoOverlap):
                errors += AdditionalUtxoOverlapError(result)
            elif isinstance(result, EvaluationFailureNotEnoughSynced):
                errors += NotEnoughSyncedError(result)
            elif isinstance(result, EvaluationFailureCannotCreateEvaluationContext):
                errors += CannotCreateEvaluationContextError(result)
        else:
            errors += UnknownResultError(response)
        return errors
    except Exception as error:
        raise error
