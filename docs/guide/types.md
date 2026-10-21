# Types

Every Ogmios and Cardano type is in `pyogmios.types`: about 500 Pydantic models and type aliases,
generated from the Ogmios v7 JSON schema.

```python
from pyogmios.types import Block, Point, ProtocolParameters, RollBackward, RollForward, Utxo, Value
```

## Field names

Fields have Python (snake_case) names and read and write Ogmios's (camelCase) names:

```python
parameters = client.ledger_state.protocol_parameters()
parameters.max_transaction_size  # maxTransactionSize on the wire
parameters.min_utxo_deposit_coefficient
```

Field names that are Python keywords get a trailing underscore: `from_`, `json_`, `list_`.

## Simple types are plain values

Types that are a number, a string or a list are aliases, not wrappers: an `Epoch` is an `int`, a
`TransactionId` is a `str`, a `Utxo` is a list of outputs. Use them as annotations:

```python
from pyogmios.types import Epoch, TransactionId


def describe(epoch: Epoch, transaction: TransactionId) -> str:
    return f"{transaction} in epoch {epoch}"
```

## Unions

Where Ogmios answers with one of several shapes, the type is a union; check which one you have:

```python
from pyogmios.types import Point

tip = client.network.tip()  # Point, or "origin" before the first block
if isinstance(tip, Point):
    print(tip.slot, tip.id)
```

## Values and assets

A `Value` holds ada and native assets. Ada is `value.ada.lovelace`; each asset policy is an extra
field, keyed by its policy id, mapping asset names (hex) to quantities:

```python
utxo = client.ledger_state.utxo(addresses=["addr_test1..."])[0]
print(utxo.value.ada.lovelace)
for policy_id, assets in (utxo.value.model_extra or {}).items():
    for name, quantity in assets.items():
        print(policy_id, bytes.fromhex(name), quantity)
```

## Back to JSON

`model_dump(mode="json", by_alias=True, exclude_unset=True)` gives back exactly the JSON Ogmios sent:

```python
block_json = event.block.model_dump(mode="json", by_alias=True, exclude_unset=True)
```

## Forward compatibility

The models ignore fields they do not know, so a newer Ogmios that adds fields does not break parsing.
Parameters you send are strict: an unknown field is an error, so a typo cannot silently widen a query.

## Where the schema is wrong

The types come from the Ogmios v7.0.0 schema, corrected in ten places where it disagrees with what the
server sends (for example, the schema's `Value` rejects its own `ada` key). Each correction is
documented, and tested to still be needed: see [Compatibility](../compatibility.md#schema-corrections).
