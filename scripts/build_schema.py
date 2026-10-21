"""Combine Ogmios' ``ogmios.json`` and ``cardano.json`` into one schema for model generation.

Every type the client needs becomes a named definition, so the generated classes get readable names:

- all ``cardano.json`` and ``ogmios.json`` definitions;
- ``<Method>Params`` and ``<Method>Result`` for each method, taken from the request ``params`` and the
  successful response's ``result``;
- one definition per error, named after the schema's title for it;
- titled inline objects anywhere in the schema (for example ``SubmitTransactionFailure<EraMismatch>``).

It also writes ``methods.json``: for each method, the name of its params, result and error definitions.

Usage: python scripts/build_schema.py <schema dir> <output dir>
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

Schema = dict[str, Any]

#: Envelope keys every JSON-RPC message carries; they are handled by the client, not the models.
ENVELOPE_KEYS = {"jsonrpc", "method", "id"}


def type_name(name: str) -> str:
    """Turn a schema key or title into a class name: ``SubmitTransactionFailure<EraMismatch>`` -> ``SubmitTransactionFailureEraMismatch``."""
    parts = re.split(r"[^0-9A-Za-z]+", name)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


class Builder:
    def __init__(self, ogmios: Schema, cardano: Schema) -> None:
        self.ogmios = ogmios
        self.cardano = cardano
        self.definitions: dict[str, Schema] = {}
        self.methods: dict[str, dict[str, Any]] = {}

    # References ---------------------------------------------------------------------------------

    def rewrite_ref(self, ref: str) -> str:
        """Point a reference at the combined schema's definitions."""
        if ref.startswith(
            ("cardano.json#/definitions/", "ogmios.json#/definitions/", "#/definitions/")
        ):
            # Keep any path inside the definition, such as Metadatum/anyOf/0.
            name, *inner = ref.split("#/definitions/", 1)[1].split("/")
            return "/".join(["#/definitions", type_name(name), *inner])
        if ref.startswith("ogmios.json#/properties/"):
            # Shared error envelopes, such as QueryLedgerStateEraMismatch: refer to their error object.
            return "#/definitions/" + type_name(ref.rsplit("/", 1)[1])
        raise ValueError(f"unexpected $ref: {ref}")

    def rewrite(self, node: Any) -> Any:
        """Copy a schema, rewriting every $ref."""
        if isinstance(node, dict):
            return {
                k: (self.rewrite_ref(v) if k == "$ref" else self.rewrite(v))
                for k, v in node.items()
            }
        if isinstance(node, list):
            return [self.rewrite(item) for item in node]
        return node

    # Definitions --------------------------------------------------------------------------------

    def add(self, name: str, schema: Schema) -> str:
        if name in self.definitions and self.definitions[name] != schema:
            raise ValueError(f"two different schemas want the name {name}")
        self.definitions[name] = schema
        return name

    def add_error(self, envelope: Schema, fallback: str) -> str:
        """Register the ``error`` object of an error envelope and return its definition name."""
        error = self.rewrite(envelope["properties"]["error"])
        return self.add(type_name(envelope.get("title") or fallback), error)

    def build(self) -> None:
        for key, schema in self.cardano["definitions"].items():
            self.add(type_name(key), self.rewrite(schema))
        for key, schema in self.ogmios["definitions"].items():
            self.add(type_name(key), self.rewrite(schema))

        properties: dict[str, Schema] = self.ogmios["properties"]
        # Shared error envelopes that responses refer to by $ref.
        shared_errors = {
            key: schema
            for key, schema in properties.items()
            if "properties" in schema
            and "error" in schema["properties"]
            and "result" not in schema["properties"]
        }
        for key, schema in shared_errors.items():
            self.add_error(schema, key)

        for key, request in properties.items():
            if key.endswith("Response") or key in shared_errors or "properties" not in request:
                continue
            method = request["properties"]["method"]["enum"][0]
            entry: dict[str, Any] = {"request": key, "params": None, "result": None, "errors": []}
            if "params" in request["properties"]:
                entry["params"] = self.add(
                    f"{key}Params", self.rewrite(request["properties"]["params"])
                )
            entry["params_required"] = "params" in request.get("required", [])

            response = properties[f"{key}Response"]
            for branch in response.get("oneOf", [response]):
                if "$ref" in branch:
                    entry["errors"].append(self.rewrite_ref(branch["$ref"]).rsplit("/", 1)[1])
                elif "result" in branch["properties"]:
                    result = branch["properties"]["result"]
                    if "$ref" in result:
                        entry["result"] = self.rewrite_ref(result["$ref"]).rsplit("/", 1)[1]
                    else:
                        entry["result"] = self.add(f"{key}Result", self.rewrite(result))
                else:
                    entry["errors"].append(self.add_error(branch, f"{key}Error"))
            self.methods[method] = entry

        self.allow_new_fields()
        self.lift_referenced_branches()
        self.lift_titled_objects()
        self.lift_inline_objects()

    def lift_referenced_branches(self) -> None:
        """Give union branches that are referenced directly (``Metadatum/anyOf/0``) their own definition.

        The definition is named after the branch's title, and every reference to the branch points to it.
        """
        moved: dict[str, str] = {}

        def find_refs(node: Any) -> None:
            if isinstance(node, dict):
                ref = node.get("$ref", "")
                if ref.count("/") > 2 and ref not in moved:
                    _, _, name, *path = ref.split("/")
                    parent, branch = self.definitions[name], None
                    for step in path[:-1]:
                        parent = parent[step]
                    branch = parent[int(path[-1])]
                    lifted = type_name(branch["title"])
                    parent[int(path[-1])] = {"$ref": f"#/definitions/{lifted}"}
                    moved[ref] = self.add(lifted, branch)
                for value in node.values():
                    find_refs(value)
            elif isinstance(node, list):
                for item in node:
                    find_refs(item)

        def repoint(node: Any) -> Any:
            if isinstance(node, dict):
                if node.get("$ref") in moved:
                    return {**node, "$ref": f"#/definitions/{moved[node['$ref']]}"}
                return {key: repoint(value) for key, value in node.items()}
            if isinstance(node, list):
                return [repoint(item) for item in node]
            return node

        for name in list(self.definitions):
            find_refs(self.definitions[name])
        for name in list(self.definitions):
            self.definitions[name] = repoint(self.definitions[name])

    def lift_inline_objects(self) -> None:
        """Name inline objects after where they sit: ``<Owner><Property>``, and ``<Owner><Property>Item`` in arrays.

        Without this, the generator numbers them (``Data1``...``Data69`` for the error payloads alone).
        """

        def is_null(node: Any) -> bool:
            return node in ({"type": "null"}, {"$ref": "#/definitions/Null"})

        def is_inline_object(node: Any) -> bool:
            return (
                isinstance(node, dict)
                and "$ref" not in node
                and ("properties" in node or "oneOf" in node)
            )

        def visit(node: Any, path: str) -> None:
            if isinstance(node, list):
                for item in node:
                    visit(item, path)
                return
            if not isinstance(node, dict):
                return
            # Map values and array items: otherwise the generator gives them the owner's name and renames the
            # owner Owner1 (LiveStakeDistribution became the per-pool entry, the map LiveStakeDistribution1).
            for key, suffix in (("additionalProperties", "Entry"), ("items", "Item")):
                value = node.get(key)
                if is_inline_object(value) and "properties" in value:
                    visit(value, path + suffix)
                    node[key] = {"$ref": f"#/definitions/{self.add(path + suffix, value)}"}
            # A nullable object, oneOf [null, {...}]: name the object <Owner>Value.
            branches = node.get("oneOf")
            if isinstance(branches, list) and len(branches) == 2 and any(map(is_null, branches)):
                for i, branch in enumerate(branches):
                    if is_inline_object(branch) and "properties" in branch:
                        visit(branch, path + "Value")
                        branches[i] = {"$ref": f"#/definitions/{self.add(path + 'Value', branch)}"}
            # Other untitled object branches of a union: name them after their required keys.
            for union in ("oneOf", "anyOf"):
                for i, branch in enumerate(node.get(union) or []):
                    if (
                        is_inline_object(branch)
                        and "properties" in branch
                        and branch.get("required")
                    ):
                        tags = [
                            prop["enum"][0]
                            for prop in branch["properties"].values()
                            if isinstance(prop, dict) and len(prop.get("enum", [])) == 1
                        ]
                        name = path + type_name(tags[0] if tags else "_".join(branch["required"]))
                        visit(branch, name)
                        node[union][i] = {"$ref": f"#/definitions/{self.add(name, branch)}"}
            for key, value in (node.get("properties") or {}).items():
                prop_path = path + type_name(key)
                visit(value, prop_path)
                if is_inline_object(value) and "properties" in value:
                    node["properties"][key] = {
                        "$ref": f"#/definitions/{self.add(prop_path, value)}"
                    }
                elif (
                    isinstance(value, dict)
                    and is_inline_object(value.get("items"))
                    and "properties" in value["items"]
                ):
                    value["items"] = {
                        "$ref": f"#/definitions/{self.add(prop_path + 'Item', value['items'])}"
                    }
            for key, value in node.items():
                if key != "properties":
                    visit(value, path)

        for name in list(self.definitions):
            visit(self.definitions[name], name)

    def lift_titled_objects(self) -> None:
        """Give titled inline objects their own definitions, so they are not named ``Foo1``, ``Foo2``..."""

        def visit(node: Any, owner: str, depth: int, in_union: bool = False) -> Any:
            if isinstance(node, list):
                return [visit(item, owner, depth, in_union) for item in node]
            if not isinstance(node, dict):
                return node
            node = {k: visit(v, owner, depth + 1, k in ("oneOf", "anyOf")) for k, v in node.items()}
            title = node.get("title")
            # Titled objects and unions anywhere, and titled union branches of any type (such as a titled string).
            lift = (
                "properties" in node or "oneOf" in node or (in_union and node.get("type") != "null")
            )
            if depth > 0 and title and "$ref" not in node and lift:
                name = type_name(title)
                if name in self.definitions and self.definitions[name] != node:
                    name = owner + name
                self.add(name, node)
                return {"$ref": f"#/definitions/{name}"}
            return node

        for name in list(self.definitions):
            self.definitions[name] = visit(self.definitions[name], name, 0)

    def allow_new_fields(self) -> None:
        """Drop ``additionalProperties: false``, so models ignore fields a newer server adds.

        Objects whose extra keys carry data (``Value``'s asset policies) keep their typed
        ``additionalProperties`` and so keep those keys. Forcing ``extra="ignore"`` on every model instead
        silently dropped native assets.

        Request params shapes stay strict: they are what the client sends, and in a union of shapes a
        lenient empty one (``WholeUtxo``) would otherwise accept ``{"addresses": [...]}`` by dropping
        the addresses, turning a filtered query into a query for everything.
        """

        def visit(node: Any, strict: bool = False) -> None:
            if isinstance(node, dict):
                if node.get("additionalProperties") is False and not strict:
                    del node["additionalProperties"]
                for key, value in node.items():
                    # A strict params shape's direct union branches are param shapes too.
                    visit(value, strict and key in ("oneOf", "anyOf"))
            elif isinstance(node, list):
                for item in node:
                    visit(item, strict)

        for name, schema in self.definitions.items():
            visit(schema, strict=name.endswith("Params"))

    def schema(self) -> Schema:
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Ogmios",
            "definitions": dict(sorted(self.definitions.items())),
        }


# Corrections and adjustments ------------------------------------------------------------------------------
# CORRECTIONS: places where the published schema and a real Ogmios v7.0.0 server disagree, checked against
# a preview node on 2026-10-20. ADJUSTMENTS: the schema is right, but the generated Pydantic models would
# reject real data. Both are applied to the source schemas before anything else.


def accept_any_anchor_url(ogmios: Schema, cardano: Schema) -> None:
    """Anchor URLs: real pool and governance metadata URLs are not always valid URIs.

    Preview stake pools register URLs such as ``tinyurl.com/4uszu5zt``, which fail ``format: uri``.
    """
    del cardano["definitions"]["Anchor"]["properties"]["url"]["format"]


def parse_utc_time(ogmios: Schema, cardano: Schema) -> None:
    """UtcTime: drop the regex ``pattern`` next to ``format: date-time``.

    Pydantic cannot apply a pattern to a datetime, so every time value failed to parse. The format
    still validates it.
    """
    del cardano["definitions"]["UtcTime"]["pattern"]


def projected_rewards_pool_ids(ogmios: Schema, cardano: Schema) -> None:
    """ProjectedRewards: the inner keys are bech32 stake pool ids, not hex.

    The schema's own example uses ``pool1...`` keys, and so does the server.
    """
    inner = ogmios["definitions"]["ProjectedRewards"]["additionalProperties"]
    inner["propertyNames"] = {"$ref": "cardano.json#/definitions/StakePoolId"}


def reward_transfer_stake_addresses(ogmios: Schema, cardano: Schema) -> None:
    """RewardTransfer: treasury withdrawals are keyed by stake address, not by hex credential.

    ``queryLedgerState/governanceProposals`` returns keys such as ``stake_test1uz3q3kanff...``.
    """
    cardano["definitions"]["RewardTransfer"]["propertyNames"] = {
        "$ref": "cardano.json#/definitions/RewardAccount"
    }


def next_transaction_needs_params(ogmios: Schema, cardano: Schema) -> None:
    """nextTransaction: the server answers -32600 'field "params" not found' without params."""
    ogmios["properties"]["NextTransaction"]["required"].append("params")


def byron_delegation_extended_keys(ogmios: Schema, cardano: Schema) -> None:
    """BootstrapOperationalCertificate: Byron delegation keys are extended keys (key and chain code).

    v7.0.0 changed Byron keys to carry the chain code, so the server sends 128 hex characters, but the
    certificate still refers to the 64-character VerificationKey. ExtendedVerificationKey is the right type.
    """
    certificate = cardano["definitions"]["BootstrapOperationalCertificate"]["properties"]
    for role in ("issuer", "delegate"):
        certificate[role]["properties"]["verificationKey"] = {
            "$ref": "cardano.json#/definitions/ExtendedVerificationKey"
        }


def byron_genesis_updatable_parameters(ogmios: Schema, cardano: Schema) -> None:
    """Genesis<Byron>: fix ``updatableParameters``.

    ``required`` names ``protocolParameters``, but the schema's property list and the server both use
    ``updatableParameters``. Its value holds the Byron-era parameters (``scriptVersion``, ``slotDuration``...),
    which are BootstrapProtocolParameters, not the Shelley-onwards ProtocolParameters it refers to.
    """
    genesis = cardano["definitions"]["Genesis<Byron>"]
    genesis["required"][genesis["required"].index("protocolParameters")] = "updatableParameters"
    genesis["properties"]["updatableParameters"] = {
        "$ref": "cardano.json#/definitions/BootstrapProtocolParameters"
    }


def value_ada_key(ogmios: Schema, cardano: Schema) -> None:
    """Value: ``propertyNames`` must allow ``ada`` next to the policy ids.

    ``propertyNames`` applies to every key, so the 56-character policy id pattern rejected the required
    ``ada`` key, and with it every real transaction output and UTxO.
    """
    cardano["definitions"]["Value"]["propertyNames"] = {"pattern": "^(ada|[0-9a-f]{56})$"}


def genesis_configuration_error(ogmios: Schema, cardano: Schema) -> None:
    """queryNetwork/genesisConfiguration: the invalid-genesis error is a response, not a result.

    The schema lists QueryNetworkInvalidGenesis inside ``result``, but the server answers with a
    top-level ``error`` (code 2004), like every other method. The envelope also requires ``result``
    where it means ``error``.
    """
    ogmios["properties"]["QueryNetworkInvalidGenesis"]["required"] = ["jsonrpc", "method", "error"]
    response = ogmios["properties"]["QueryNetworkGenesisConfigurationResponse"]
    error_branch, genesis = response["properties"]["result"]["oneOf"]
    response["properties"]["result"] = genesis
    ogmios["properties"]["QueryNetworkGenesisConfigurationResponse"] = {
        "oneOf": [response, error_branch]
    }


def pre_conway_parameter_updates(ogmios: Schema, cardano: Schema) -> None:
    """GovernanceAction<ProtocolParametersUpdate>: ``guardrails`` is absent before Conway.

    Pre-Conway update proposals have no guardrails script; Ogmios reports them as this action without
    the field (preview block 4330, Alonzo era), but the schema requires it.
    """
    for branch in cardano["definitions"]["GovernanceAction"]["oneOf"]:
        if branch.get("title") == "GovernanceAction<ProtocolParametersUpdate>":
            branch["required"].remove("guardrails")


def genesis_delegate_voter_origin(ogmios: Schema, cardano: Schema) -> None:
    """Voter<GenesisDelegate>: ``from`` is absent.

    Pre-Conway votes by genesis delegates carry only the delegate's key hash; Ogmios omits ``from``
    (preview block 4330, Alonzo era), but the schema requires it.
    """
    for branch in cardano["definitions"]["GovernanceVoter"]["oneOf"]:
        if branch.get("title") == "Voter<GenesisDelegate>":
            branch["required"].remove("from")


CORRECTIONS = [
    projected_rewards_pool_ids,
    reward_transfer_stake_addresses,
    next_transaction_needs_params,
    byron_delegation_extended_keys,
    byron_genesis_updatable_parameters,
    value_ada_key,
    genesis_configuration_error,
    pre_conway_parameter_updates,
    genesis_delegate_voter_origin,
]

ADJUSTMENTS = [
    accept_any_anchor_url,
    parse_utc_time,
]


def main() -> None:
    source, output = Path(sys.argv[1]), Path(sys.argv[2])
    ogmios = json.loads((source / "ogmios.json").read_text())
    cardano = json.loads((source / "cardano.json").read_text())
    ogmios, cardano = copy.deepcopy(ogmios), copy.deepcopy(cardano)
    for fix in CORRECTIONS + ADJUSTMENTS:
        fix(ogmios, cardano)
    builder = Builder(ogmios, cardano)
    builder.build()
    output.mkdir(parents=True, exist_ok=True)
    (output / "combined.json").write_text(json.dumps(builder.schema(), indent=2) + "\n")
    (output / "methods.json").write_text(
        json.dumps(dict(sorted(builder.methods.items())), indent=2) + "\n"
    )
    print(f"{len(builder.definitions)} definitions, {len(builder.methods)} methods -> {output}")


if __name__ == "__main__":
    main()
