"""
This module contains the error types that can be returned by the evaluation endpoint.

The error types are:

- AdditionalUtxoOverlapError
- CannotCreateEvaluationContextError
- ExtraRedeemersError
- IllFormedExecutionBudgetError
- IncompatibleEraError
- MissingRequiredDatumsError
- MissingRequiredScriptsError
- NoCostModelForLanguageError
- NonScriptInputReferencedByRedeemerError
- NotEnoughSyncedError
- UnknownInputReferencedByRedeemerError
- UnknownResultError
- ValidatorFailedError
"""

import json
from typing import Union

from pyogmios.models import (
    EvaluationFailureAdditionalUtxoOverlap,
    EvaluationFailureCannotCreateEvaluationContext,
    EvaluationFailureIncompatibleEra,
    EvaluationFailureNotEnoughSynced,
    ExtraRedeemers,
    IllFormedExecutionBudget,
    MissingRequiredDatums,
    MissingRequiredScripts,
    NoCostModelForLanguage,
    NonScriptInputReferencedByRedeemer,
    UnknownInputReferencedByRedeemer,
    ValidatorFailedError,
)

AdditionalUtxoOverlap = EvaluationFailureAdditionalUtxoOverlap
CannotCreateEvaluationContext = EvaluationFailureCannotCreateEvaluationContext
IncompatibleEra = EvaluationFailureIncompatibleEra
NotEnoughSynced = EvaluationFailureNotEnoughSynced

EvaluateTxError = Union[
    AdditionalUtxoOverlap,
    CannotCreateEvaluationContext,
    ExtraRedeemers,
    IllFormedExecutionBudget,
    IncompatibleEra,
    MissingRequiredDatums,
    MissingRequiredScripts,
    NoCostModelForLanguage,
    NonScriptInputReferencedByRedeemer,
    NotEnoughSynced,
    UnknownInputReferencedByRedeemer,
    ValidatorFailedError,
    Exception,
]


class AdditionalUtxoOverlapError(Exception):
    """
    Additional utxo overlap error.
    """

    def __init__(self, raw_error: AdditionalUtxoOverlap):
        super().__init__()
        self.message = json.dumps(raw_error.AdditionalUtxoOverlap)


class ExtraRedeemersError(Exception):
    """
    Extra redeemers error.
    """

    def __init__(self, raw_error: ExtraRedeemers):
        super().__init__()
        self.message = json.dumps(raw_error.extraRedeemers)


class IllFormedExecutionBudgetError(Exception):
    """
    Ill formed execution budget error.
    """

    def __init__(self, raw_error: IllFormedExecutionBudget):
        super().__init__()
        self.message = json.dumps(raw_error.illFormedExecutionBudget)


class IncompatibleEraError(Exception):
    """
    Incompatible era error.
    """

    def __init__(self, raw_error: IncompatibleEra):
        super().__init__()
        self.message = json.dumps(raw_error.IncompatibleEra)


class MissingRequiredDatumsError(Exception):
    """
    Missing required datums error.
    """

    def __init__(self, raw_error: MissingRequiredDatums):
        super().__init__()
        self.message = json.dumps(raw_error.missingRequiredDatums)


class MissingRequiredScriptsError(Exception):
    """
    Missing required scripts error.
    """

    def __init__(self, raw_error: MissingRequiredScripts):
        super().__init__()
        self.message = json.dumps(raw_error.missing)


class NoCostModelForLanguageError(Exception):
    """
    No cost model for language error.
    """

    def __init__(self, raw_error: NoCostModelForLanguage):
        super().__init__()
        self.message = json.dumps(raw_error.noCostModelForLanguage)


class NonScriptInputReferencedByRedeemerError(Exception):
    """
    Non script input referenced by redeemer error.
    """

    def __init__(self, raw_error: NonScriptInputReferencedByRedeemer):
        super().__init__()
        self.message = json.dumps(raw_error.nonScriptInputReferencedByRedeemer)


class UnknownInputReferencedByRedeemerError(Exception):
    """
    Unknown input referenced by redeemer error.
    """

    def __init__(self, raw_error: UnknownInputReferencedByRedeemer):
        super().__init__()
        self.message = json.dumps(raw_error.unknownInputReferencedByRedeemer)


class ValidatorFailedError(Exception):
    """
    Validator failed error.
    """

    def __init__(self, raw_error: ValidatorFailedError):
        super().__init__()
        self.message = json.dumps(raw_error.validatorFailed)


class NotEnoughSyncedError(Exception):
    """
    Not enough synced error.
    """

    def __init__(self, raw_error: NotEnoughSynced):
        super().__init__()
        self.message = json.dumps(raw_error.NotEnoughSynced)


class CannotCreateEvaluationContextError(Exception):
    """
    Cannot create evaluation context error.
    """

    def __init__(self, raw_error: CannotCreateEvaluationContext):
        super().__init__()
        self.message = json.dumps(raw_error.CannotCreateEvaluationContext)
