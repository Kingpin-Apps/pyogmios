"""The ``pyogmios`` command line, against the fake Ogmios server."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

import pyogmios
from pyogmios._generated.methods import METHODS
from pyogmios.cli import QUERIES, main, read_transaction

from .fake_server import FakeOgmios, recorded, running

BACKWARD = recorded("nextBlock", "backward")


@pytest.fixture
def fake() -> Any:
    """A fake Ogmios on its own event loop thread: the command line runs its own loop."""
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    server = FakeOgmios(sequences={"nextBlock": [BACKWARD, recorded("nextBlock", "recent-01")]})
    context = running(server)
    asyncio.run_coroutine_threadsafe(context.__aenter__(), loop).result()
    yield server
    asyncio.run_coroutine_threadsafe(context.__aexit__(None, None, None), loop).result()
    loop.call_soon_threadsafe(loop.stop)
    thread.join()
    loop.close()


def run(fake: FakeOgmios, *args: str) -> int:
    return main(["--url", fake.ws_url, "--compact", *args])


def output(capsys: pytest.CaptureFixture[str]) -> list[Any]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines()]


def test_health_and_tip(fake: FakeOgmios, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(fake, "health") == 0
    assert output(capsys)[0]["version"].startswith("v7")
    assert run(fake, "tip") == 0
    tip = output(capsys)[0]
    assert tip["tip"] == recorded("queryNetwork/tip")["result"]
    assert tip["blockHeight"] == recorded("queryNetwork/blockHeight")["result"]


def test_query_by_short_and_full_name(fake: FakeOgmios, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(fake, "query", "epoch") == 0
    assert run(fake, "query", "ledger-state/epoch") == 0
    assert output(capsys) == [recorded("queryLedgerState/epoch")["result"]] * 2
    # The output is the server's JSON, with Ogmios field names.
    assert run(fake, "query", "protocol-parameters") == 0
    assert "maxTransactionSize" in output(capsys)[0]


def test_query_params(fake: FakeOgmios, capsys: pytest.CaptureFixture[str]) -> None:
    address = recorded("queryLedgerState/utxo", "by-address")["result"][0]["address"]
    assert run(fake, "query", "utxo", json.dumps({"addresses": [address]})) == 0
    assert fake.received[-1]["params"] == {"addresses": [address]}
    assert run(fake, "query", "utxo", "{not json") == 1
    assert "params must be JSON" in capsys.readouterr().err


def test_every_query_has_a_name() -> None:
    methods = {name for name in METHODS if name.startswith("query")}
    assert set(QUERIES.values()) == methods
    assert "tip" not in QUERIES  # ambiguous: ledger-state/tip or network/tip
    assert {"ledger-state/tip", "network/tip"} <= set(QUERIES)


def test_unknown_query_is_a_usage_error(fake: FakeOgmios) -> None:
    with pytest.raises(SystemExit) as raised:
        run(fake, "query", "nope")
    assert raised.value.code == 2


def test_options_after_the_command(fake: FakeOgmios, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["query", "epoch", "--url", fake.ws_url, "--pretty"]) == 0
    assert capsys.readouterr().out.strip() == json.dumps(
        recorded("queryLedgerState/epoch")["result"]
    )


def test_follow(fake: FakeOgmios, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(fake, "follow", "--from", "origin", "--count", "2", "--headers") == 0
    events = output(capsys)
    assert [event["direction"] for event in events] == ["backward", "forward"]
    assert "transactions" not in events[1]["block"]
    intersections = [r["params"] for r in fake.received if r["method"] == "findIntersection"]
    assert intersections == [{"points": ["origin"]}]
    assert run(fake, "follow", "--from", "nonsense") == 1


def test_mempool(fake: FakeOgmios, capsys: pytest.CaptureFixture[str]) -> None:
    fake.sequences["nextTransaction"] = [
        {
            "jsonrpc": "2.0",
            "method": "nextTransaction",
            "result": {"transaction": {"id": "aa" * 32}},
        }
    ]
    assert run(fake, "mempool", "--count", "1") == 0
    assert output(capsys) == ["aa" * 32]


def test_submit_reports_the_ledger_error(
    fake: FakeOgmios, capsys: pytest.CaptureFixture[str]
) -> None:
    fake.responses["submitTransaction"] = recorded("submitTransaction", "ledger-rejection")
    assert run(fake, "submit", "84a0") == 1
    err = capsys.readouterr().err
    assert "MissingScriptsError" in err or "Error" in err
    assert fake.received[-1]["params"] == {"transaction": {"cbor": "84a0"}}


def test_evaluate(fake: FakeOgmios, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(fake, "evaluate", "84A0") == 0
    assert output(capsys) == [recorded("evaluateTransaction", "no-scripts")["result"]]


def test_unreachable_server_exits_3(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--url", "ws://127.0.0.1:1", "query", "epoch"]) == 3
    err = capsys.readouterr().err
    assert "cannot connect" in err
    assert "version" not in err  # no misleading version warning first


def test_read_transaction(tmp_path: Path) -> None:
    assert read_transaction("84A0") == "84a0"
    (tmp_path / "hex").write_text("84A0\n")
    assert read_transaction(str(tmp_path / "hex")) == "84a0"
    (tmp_path / "bytes").write_bytes(bytes.fromhex("84a0ff"))
    assert read_transaction(str(tmp_path / "bytes")) == "84a0ff"
    envelope = {"type": "Witnessed Tx ConwayEra", "description": "", "cborHex": "84A0"}
    (tmp_path / "tx.signed").write_text(json.dumps(envelope))
    assert read_transaction(str(tmp_path / "tx.signed")) == "84a0"
    (tmp_path / "other.json").write_text("{}")
    with pytest.raises(ValueError, match="cborHex"):
        read_transaction(str(tmp_path / "other.json"))
    with pytest.raises(ValueError, match="neither a file nor hex"):
        read_transaction("not-a-file")


def test_python_dash_m() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pyogmios", "--version"], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == f"pyogmios {pyogmios.__version__}"
