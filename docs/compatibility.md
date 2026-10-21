# Compatibility

| pyogmios | Ogmios | cardano-node (tested) | Python |
|---|---|---|---|
| 1.x | 7.x | 11.0.1 and 11.1.2 | 3.11 to 3.15, including 3.14t and 3.15t |
| 0.7.x | 5.x | — | 3.10 and up |

pyogmios checks the server's version when it connects: Ogmios older than 7 is refused, newer warns
(see [the version check](guide/clients.md#the-version-check)).

## Eras

The types cover every era, Byron to Conway, as the Ogmios schema describes them. Checked against real
blocks so far: every block of the preview network, 4.78 million from Alonzo to Conway, parses into the
models and dumps back unchanged. Earlier eras (Byron to Mary) are only on mainnet and preprod, which
have not been swept yet. The Dijkstra era and Plutus V4, which Ogmios 7.0.0 supports provisionally,
are in the types but cannot be checked against a real chain yet.

## Schema corrections

The types are generated from the Ogmios 7.0.0 JSON schema. In these places, the schema disagrees with
what the server sends, and pyogmios follows the server:

1. `Value`: the schema rejects the `ada` key it requires, so every output and UTxO failed.
2. `RewardTransfer` (treasury withdrawals): keyed by stake address, not by hex credential.
3. `ProjectedRewards`: inner keys are bech32 stake pool ids, not hex.
4. Byron delegation certificates: keys are 128-character extended keys (key and chain code).
5. `Genesis<Byron>`: requires `protocolParameters` but means `updatableParameters`, which holds
   Byron-era parameters.
6. `queryNetwork/genesisConfiguration`: its error is a response error, not part of the result.
7. `nextTransaction`: the server requires params, even if empty.
8. Pre-Conway update proposals have no `guardrails`.
9. Pre-Conway votes by genesis delegates have no `from`.
10. The JSON-RPC error message field is `message`, not `string`.

Two more adjustments make the models accept real data the schema allows: anchor URLs are any string
(some registered metadata URLs are not valid URIs), and UTC times are parsed without the schema's
regular expression. The test suite checks that each correction is still needed, so they can be removed
when the schema is fixed.

## Optional dependencies

- `pyogmios[speedups]` installs orjson for faster JSON. It is not available on the free-threaded
  builds yet. pyogmios keeps integers above 64 bits exact either way.
