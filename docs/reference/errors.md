# Errors

The hand-written exception classes. The per-code transaction errors are listed, with their codes, in
[Errors](../guide/errors.md#every-error-code).

::: pyogmios.errors
    options:
      members:
        - OgmiosError
        - OgmiosConnectionError
        - OgmiosTimeoutError
        - ServerVersionError
        - StatefulOverHttpError
        - ResponseError
        - JsonRpcError
        - ParseError
        - InvalidRequestError
        - MethodNotFoundError
        - InvalidParamsError
        - InternalError
        - ChainSyncError
        - IntersectionNotFoundError
        - IntersectionInterleavedError
        - LedgerStateQueryError
        - AcquireLedgerStateError
        - EraMismatchError
        - UnavailableInCurrentEraError
        - AcquiredExpiredError
        - InvalidGenesisError
        - TransactionError
        - EvaluateTransactionError
        - SubmitTransactionError
        - TransactionDeserialisationError
        - MempoolError
        - MustAcquireMempoolFirstError
        - error_class
