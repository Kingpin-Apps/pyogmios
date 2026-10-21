"""Shared helpers for the Ogmios v7 tests: recorded fixtures and the schema they are checked against."""

from __future__ import annotations

import copy
import importlib.util
import json
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator
from jsonschema.protocols import Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

from pyogmios._generated.methods import OGMIOS_VERSION

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / f"v{OGMIOS_VERSION}"
FIXTURES = ROOT / "tests" / "fixtures" / f"v{OGMIOS_VERSION}"

Schema = dict[str, Any]
#: A schema correction or adjustment from scripts/build_schema.py.
Fix = Callable[[Schema, Schema], None]


@dataclass(frozen=True)
class Fixture:
    """One recorded JSON-RPC response."""

    method: str
    case: str
    response: dict[str, Any]

    @property
    def id(self) -> str:
        return f"{self.method}:{self.case}"

    @property
    def is_rpc_error(self) -> bool:
        """A JSON-RPC level error (negative code): invalid request, params or method."""
        return "error" in self.response and self.response["error"]["code"] < 0


def load_fixtures() -> list[Fixture]:
    fixtures = []
    for path in sorted(FIXTURES.glob("*/*.json")):
        response = json.loads(path.read_text())
        method = response["id"].rsplit(":", 1)[0]
        fixtures.append(Fixture(method=method, case=path.stem, response=response))
    return fixtures


FIXTURE_LIST = load_fixtures()


@cache
def build_schema_module() -> Any:
    """scripts/build_schema.py, which holds the schema corrections."""
    spec = importlib.util.spec_from_file_location(
        "build_schema", ROOT / "scripts" / "build_schema.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_schemas() -> tuple[Schema, Schema]:
    ogmios = json.loads((SCHEMAS / "ogmios.json").read_text())
    cardano = json.loads((SCHEMAS / "cardano.json").read_text())
    return ogmios, cardano


def corrected_schemas(skip: Fix | None = None) -> tuple[Schema, Schema]:
    """The schemas with every correction applied, except ``skip``."""
    ogmios, cardano = (copy.deepcopy(schema) for schema in raw_schemas())
    for correction in build_schema_module().CORRECTIONS:
        if correction is not skip:
            correction(ogmios, cardano)
    return ogmios, cardano


def response_validator(ogmios: Schema, cardano: Schema, request: str) -> Validator:
    """A validator for ``<request>Response`` in the given schemas."""
    registry = Registry().with_resources(
        [
            ("ogmios.json", Resource(ogmios, specification=DRAFT7)),
            ("cardano.json", Resource(cardano, specification=DRAFT7)),
        ]
    )
    return Draft7Validator(
        {"$ref": f"ogmios.json#/properties/{request}Response"}, registry=registry
    )
