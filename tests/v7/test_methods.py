"""The generated method table against the schema and the recorded fixtures."""

from __future__ import annotations

from pyogmios._generated.methods import METHODS, OGMIOS_VERSION

from .conftest import FIXTURE_LIST, ROOT, raw_schemas

#: Methods with no recorded fixture, and why.
NOT_RECORDED = {
    "queryLedgerState/dump": "writes the ledger state to a file on the server's disk",
}


def test_version_matches_the_pinned_schema() -> None:
    assert (ROOT / "schemas" / "VERSION").read_text().strip() == OGMIOS_VERSION


def test_every_method_in_the_schema_is_in_the_table() -> None:
    ogmios, _ = raw_schemas()
    # Requests are the messages with a method that are neither responses nor error envelopes.
    requests = {
        schema["properties"]["method"]["enum"][0]
        for name, schema in ogmios["properties"].items()
        if not name.endswith("Response")
        and "method" in schema.get("properties", {})
        and not {"result", "error"} & set(schema["properties"])
    }
    assert requests == set(METHODS)
    assert len(METHODS) == 35


def test_every_method_has_a_fixture() -> None:
    recorded = {fixture.method for fixture in FIXTURE_LIST}
    missing = set(METHODS) - recorded - set(NOT_RECORDED)
    assert not missing, f"no fixture for {sorted(missing)}: run `just record-fixtures`"


def test_ledger_state_queries_share_the_acquired_state_errors() -> None:
    for name, spec in METHODS.items():
        if name.startswith("queryLedgerState/"):
            assert {error.__name__ for error in spec.errors} == {
                "QueryLedgerStateEraMismatch",
                "QueryLedgerStateUnavailableInCurrentEra",
                "QueryLedgerStateAcquiredExpired",
            }
