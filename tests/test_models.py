"""The generated models against recorded server responses: every one parses and dumps back unchanged."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import TypeAdapter

from pyogmios._generated import models
from pyogmios._generated.methods import METHODS

from .conftest import FIXTURE_LIST, Fixture

RESULTS = [f for f in FIXTURE_LIST if "result" in f.response]
ERRORS = [f for f in FIXTURE_LIST if "error" in f.response and not f.is_rpc_error]


def dump(adapter: TypeAdapter[Any], value: Any) -> Any:
    return adapter.dump_python(value, mode="json", by_alias=True, exclude_unset=True)


@pytest.mark.parametrize("fixture", RESULTS, ids=lambda f: f.id)
def test_result_round_trips(fixture: Fixture) -> None:
    adapter: TypeAdapter[Any] = TypeAdapter(METHODS[fixture.method].result)
    result = fixture.response["result"]
    assert dump(adapter, adapter.validate_python(result)) == result


@pytest.mark.parametrize("fixture", ERRORS, ids=lambda f: f.id)
def test_error_parses_as_a_declared_error(fixture: Fixture) -> None:
    error = fixture.response["error"]
    declared = METHODS[fixture.method].errors
    assert declared, f"{fixture.method} declares no errors but returned {error['code']}"
    matches = []
    for error_type in declared:
        try:
            matches.append(TypeAdapter(error_type).validate_python(error))
        except ValueError:
            continue
    assert matches, f"code {error['code']} is none of {[t.__name__ for t in declared]}"


def test_native_assets_are_kept() -> None:
    """Value keeps its asset policies: a global extra="ignore" once dropped them silently."""
    value = {
        "ada": {"lovelace": 1_180_940},
        "b7e779b1a6fbf65f5ff45594c22046e1e0d7367737ae605c2cc9b120": {
            "444a4544": 1000,
            "5348454e": 1000,
        },
    }
    adapter = TypeAdapter(models.Value)
    assert dump(adapter, adapter.validate_python(value)) == value


def test_unknown_fields_are_ignored() -> None:
    """A newer server may add fields: they must not break parsing."""
    point = models.Point.model_validate({"slot": 1, "id": "0" * 64, "addedLater": True})
    assert point.slot == 1


def test_anchor_url_accepts_real_world_urls() -> None:
    """Preview pools register URLs that are not valid URIs (ADJUSTMENTS: accept_any_anchor_url)."""
    anchor = models.Anchor.model_validate({"hash": "00", "url": "tinyurl.com/4uszu5zt"})
    assert anchor.url == "tinyurl.com/4uszu5zt"


def test_utc_time_parses() -> None:
    """A regex pattern on a datetime made every time fail (ADJUSTMENTS: parse_utc_time)."""
    start = TypeAdapter(models.UtcTime).validate_python("2022-10-25T00:00:00Z")
    assert start.year == 2022
