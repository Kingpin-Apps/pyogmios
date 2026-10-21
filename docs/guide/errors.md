# Errors

Every exception pyogmios raises is a `pyogmios.OgmiosError`.

```text
OgmiosError
├── OgmiosConnectionError        cannot connect, or the connection dropped (also ConnectionError)
├── OgmiosTimeoutError           no answer in time (also TimeoutError)
├── ServerVersionError           the server is not Ogmios 7
├── StatefulOverHttpError        chain sync, the mempool or ledger_state_at over HTTP
└── ResponseError                the server answered with an error
    ├── JsonRpcError             the request was malformed (-32700 to -32600)
    ├── ChainSyncError           1000s
    ├── LedgerStateQueryError    2000s
    ├── TransactionError         3000s: EvaluateTransactionError and SubmitTransactionError
    └── MempoolError             4000s
```

A `ResponseError` carries what the server said:

- `code`: the Ogmios error code.
- `message`: its message.
- `data`: its data, as JSON (or `None`).
- `details`: the error parsed into its model from `pyogmios.types`, when the method declares one.
- `method`: the method that failed.

Catch as broadly or narrowly as you need:

```python
from pyogmios import errors

try:
    client.submit_transaction(cbor)
except errors.ValueNotConservedError as error:  # one ledger rule
    ...
except errors.SubmitTransactionError as error:  # any rejected submission
    ...
except errors.OgmiosConnectionError:  # the server is unreachable
    ...
```

Parameters that do not match a method's schema raise Pydantic's `ValidationError` before anything is
sent.

## Every error code

<!-- errors:table -->
