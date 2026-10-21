"""Recorded server responses against the Ogmios JSON schema, and the corrections made to it."""

from __future__ import annotations

import pytest
from jsonschema.exceptions import best_match

from pyogmios._generated.methods import METHODS

from .conftest import (
    FIXTURE_LIST,
    Fix,
    Fixture,
    build_schema_module,
    corrected_schemas,
    response_validator,
)

# JSON-RPC level errors are checked by the client's own envelope, not the schema: the schema's
# RpcError requires a "string" field, but the server sends "message", as JSON-RPC 2.0 specifies.
SCHEMA_FIXTURES = [f for f in FIXTURE_LIST if not f.is_rpc_error]


@pytest.mark.parametrize("fixture", SCHEMA_FIXTURES, ids=lambda f: f.id)
def test_response_matches_corrected_schema(fixture: Fixture) -> None:
    validator = response_validator(*corrected_schemas(), METHODS[fixture.method].schema_name)
    error = best_match(validator.iter_errors(fixture.response))
    assert error is None, f"{list(error.absolute_path)}: {error.message[:300]}"


@pytest.mark.parametrize(
    "correction", build_schema_module().CORRECTIONS, ids=lambda correction: correction.__name__
)
def test_correction_is_still_needed(correction: Fix) -> None:
    """Each correction must be needed by at least one real response, or a request the server rejects.

    When this fails, Ogmios has fixed its schema: remove the correction.
    """
    if correction is build_schema_module().next_transaction_needs_params:
        pytest.skip(
            "about a request the server rejects, not a response; recorded in nextTransaction fixtures"
        )
    ogmios, cardano = corrected_schemas(skip=correction)
    failing = [
        f.id
        for f in SCHEMA_FIXTURES
        if not response_validator(ogmios, cardano, METHODS[f.method].schema_name).is_valid(
            f.response
        )
    ]
    assert failing, "no recorded response needs this correction any more"
