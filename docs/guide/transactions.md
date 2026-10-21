# Transactions

pyogmios submits and evaluates transactions; it does not build or sign them. Build them with a library
such as [pycardano](https://pycardano.readthedocs.io), [cardano-cli](https://github.com/IntersectMBO/cardano-cli)
or a wallet, and pass the signed transaction's CBOR, as bytes or hex.

## Submitting

```python
from pyogmios.errors import SubmitTransactionError

try:
    submitted = client.submit_transaction(signed_cbor)
    print("submitted", submitted.transaction.id)
except SubmitTransactionError as error:
    print(type(error).__name__, error.code, error.message)
    print(error.details)  # the ledger's reasons, parsed
```

The node checks the transaction against the ledger before accepting it. If a ledger rule fails, the
exception is the subclass for that rule, with the ledger's data in `error.data` (JSON) and
`error.details` (a model):

| A few of the 74 rules | Code | `error.data` holds |
|---|---|---|
| `MissingSignatoriesError` | 3101 | the key hashes whose signatures are missing |
| `UnknownOutputReferencesError` | 3117 | the inputs that are spent or never existed |
| `TransactionFeeTooSmallError` | 3122 | the minimum fee and the fee given |
| `ValueNotConservedError` | 3123 | what the inputs and outputs add up to |
| `UnexpectedMempoolError` | 3997 | the mempool's reason, such as "All inputs are spent" |

A transaction that cannot be decoded raises `TransactionDeserialisationError`, whose `data` holds the
decoder's error for each era it tried. [Errors](errors.md) lists every code.

Being accepted is not being on the chain: the transaction goes to the mempool, then into a block. To
wait for it, follow the chain (see [Recipes](../recipes.md#wait-for-a-transaction-to-be-on-chain)).

## Evaluating scripts

`client.evaluate_transaction(cbor)` runs a transaction's Plutus scripts and returns the execution units
each redeemer needs, to set them before signing:

```python
for result in client.evaluate_transaction(unsigned_cbor):
    print(result.validator.purpose, result.validator.index, result.budget.memory, result.budget.cpu)
```

A transaction without scripts evaluates to an empty list. To evaluate against outputs the node does not
know yet, for example those of another transaction you are still building, pass them with
`additional_utxo=`; they take precedence over the node's own.

Evaluation failures raise an `EvaluateTransactionError` subclass, for example
`ScriptExecutionFailureError` with each failing validator in `details`.

## Over HTTP

Submitting and evaluating work over `http://` and `https://` as well as WebSocket.
