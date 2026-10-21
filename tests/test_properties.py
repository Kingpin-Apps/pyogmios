"""Property-based tests: random documents valid against the schema parse and dump back unchanged.

The fixtures only hold what a real node happened to send; these cover what the schema allows. For
each generated type, Hypothesis (with hypothesis-jsonschema) draws documents that are valid against
the corrected schema, and each must parse into the model and dump back to the same JSON.
PYOGMIOS_HYPOTHESIS_EXAMPLES sets the documents per type (default 30). They take a few minutes, so
they run separately: ``just test-properties``.
"""

from __future__ import annotations

import copy
import json
import os
import re
from datetime import datetime
from functools import cache
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import errors as hypothesis_errors
from hypothesis_jsonschema import from_schema
from pydantic import TypeAdapter

from pyogmios._generated import models

from .conftest import build_schema_module, raw_schemas

pytestmark = pytest.mark.properties

EXAMPLES = int(os.environ.get("PYOGMIOS_HYPOTHESIS_EXAMPLES", "30"))

#: Types left out, and why.
EXCLUDED = {
    "RpcError": "its schema requires a 'string' field the server never sends; the client's JSON-RPC envelope is hand-written",
}

_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


@cache
def definitions() -> dict[str, Any]:
    """The corrected schema's definitions, strict: objects have only their declared fields.

    The models ignore unknown fields by design, so documents with extra fields would not round-trip;
    and some schema objects lack ``"type": "object"``, which would allow ``null`` where the server
    always sends an object.
    """
    build_schema = build_schema_module()
    ogmios, cardano = (copy.deepcopy(schema) for schema in raw_schemas())
    for fix in build_schema.CORRECTIONS + build_schema.ADJUSTMENTS:
        fix(ogmios, cardano)
    builder = build_schema.Builder(ogmios, cardano)
    builder.build(lenient=False)

    def strict(node: Any) -> Any:
        if isinstance(node, list):
            return [strict(item) for item in node]
        if not isinstance(node, dict):
            return node
        node = {key: strict(value) for key, value in node.items()}
        if "properties" in node:
            node.setdefault("type", "object")
            node.setdefault("additionalProperties", False)
        return node

    return strict(builder.definitions)


def canonical(value: Any) -> Any:
    """Times as instants, so "+00:00" and "Z" compare equal."""
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonical(item) for item in value]
    if isinstance(value, str) and _DATETIME.match(value):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    return value


TYPES = sorted(name for name in definitions() if hasattr(models, name))


@pytest.mark.parametrize("name", TYPES)
def test_schema_valid_documents_round_trip(name: str) -> None:
    if name in EXCLUDED:
        pytest.skip(EXCLUDED[name])
    adapter: TypeAdapter[Any] = TypeAdapter(getattr(models, name))
    schema: dict[str, Any] = {"definitions": definitions(), "$ref": f"#/definitions/{name}"}
    try:
        strategy = from_schema(schema)
    except hypothesis_errors.HypothesisException as error:
        pytest.skip(f"hypothesis-jsonschema cannot draw this type: {type(error).__name__}")

    @settings(
        max_examples=EXAMPLES, deadline=None, database=None, suppress_health_check=list(HealthCheck)
    )
    @given(strategy)
    def round_trips(document: Any) -> None:
        dumped = adapter.dump_python(
            adapter.validate_python(document), mode="json", by_alias=True, exclude_unset=True
        )
        assert canonical(dumped) == canonical(document), json.dumps(document)[:500]

    try:
        round_trips()
    except Exception as error:
        # hypothesis-jsonschema's own HypothesisRefResolutionError, from a private module.
        if type(error).__name__ != "HypothesisRefResolutionError":
            raise
        pytest.skip(
            "recursive schema, which hypothesis-jsonschema cannot draw: covered by fixtures and the block sweep"
        )
