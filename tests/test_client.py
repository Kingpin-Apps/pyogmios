"""AsyncClient and Client against the fake Ogmios server (WebSocket) and a mocked HTTP server."""

from __future__ import annotations

import asyncio
import logging
import threading
import warnings
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

import pyogmios
from pyogmios import _json, errors
from pyogmios._jsonrpc import parse_result
from pyogmios._transport import HttpTransport, Reconnect, WebSocketTransport
from pyogmios.health import health_url, parse_version
from pyogmios.types import UtxoByOutputReferences

from .conftest import FIXTURE_LIST, Fixture
from .fake_server import FakeOgmios, recorded, running

FAST_RECONNECT = Reconnect(attempts=3, initial_delay=0.01, max_delay=0.02)

QUERY_RESULTS = [f for f in FIXTURE_LIST if f.method.startswith("query") and "result" in f.response]
ERRORS = [f for f in FIXTURE_LIST if "error" in f.response]


def client(fake: FakeOgmios, **options: Any) -> pyogmios.AsyncClient:
    return pyogmios.AsyncClient(fake.ws_url, reconnect=FAST_RECONNECT, **options)


# Results and errors --------------------------------------------------------------------------------


@pytest.mark.parametrize("fixture", QUERY_RESULTS, ids=lambda f: f.id)
async def test_call_returns_the_parsed_result(fixture: Fixture) -> None:
    fake = FakeOgmios(responses={fixture.method: fixture.response})
    async with running(fake), client(fake) as ogmios:
        result = await ogmios.call(fixture.method, _params_for(fixture))
    assert result == parse_result(fixture.method, fixture.response["result"])


@pytest.mark.parametrize("fixture", ERRORS, ids=lambda f: f.id)
async def test_errors_raise_the_matching_exception(fixture: Fixture) -> None:
    error = fixture.response["error"]
    expected = errors.error_class(error["code"], fixture.method)
    fake = FakeOgmios(responses={fixture.method: fixture.response})
    async with running(fake), client(fake) as ogmios:
        with pytest.raises(expected) as raised:
            await ogmios.request(fixture.method)
    assert raised.value.code == error["code"]
    assert raised.value.message == error["message"]
    assert raised.value.data == error.get("data")
    assert raised.value.method == fixture.method
    if error["code"] >= 0:  # method-specific errors are parsed into their model
        assert raised.value.details is not None


def test_error_classes_by_code() -> None:
    assert errors.error_class(-32602, "submitTransaction") is errors.TransactionDeserialisationError
    assert errors.error_class(3005, "submitTransaction") is errors.SubmitEraMismatchError
    assert errors.error_class(3117, "submitTransaction") is errors.UnknownOutputReferencesError
    assert errors.error_class(3999, "submitTransaction") is errors.SubmitTransactionError
    assert issubclass(errors.UnknownOutputReferencesError, errors.SubmitTransactionError)
    assert errors.error_class(3010, "evaluateTransaction") is errors.ScriptExecutionFailureError
    assert errors.error_class(3099, "evaluateTransaction") is errors.EvaluateTransactionError
    assert errors.error_class(2003, "queryLedgerState/epoch") is errors.AcquiredExpiredError
    assert errors.error_class(1999, None) is errors.ChainSyncError
    assert errors.error_class(-32099, None) is errors.JsonRpcError
    assert errors.error_class(42, None) is errors.ResponseError
    assert issubclass(errors.TransactionDeserialisationError, errors.InvalidParamsError)


# Params ------------------------------------------------------------------------------------------


async def test_params_accept_models_and_either_field_naming() -> None:
    reference = {"transaction": {"id": "0" * 64}, "index": 0}
    async with running() as fake, client(fake) as ogmios:
        await ogmios.call("queryLedgerState/utxo", {"output_references": [reference]})
        await ogmios.call("queryLedgerState/utxo", {"outputReferences": [reference]})
        await ogmios.call(
            "queryLedgerState/utxo",
            UtxoByOutputReferences.model_validate({"outputReferences": [reference]}),
        )
    sent = [r["params"] for r in fake.received if r["method"] == "queryLedgerState/utxo"]
    assert sent == [{"outputReferences": [reference]}] * 3


async def test_invalid_params_are_rejected_before_sending() -> None:
    async with running() as fake, client(fake) as ogmios:
        with pytest.raises(ValidationError):
            await ogmios.call("queryLedgerState/projectedRewards", {"stake": "lots"})
        with pytest.raises(TypeError, match="takes no params"):
            await ogmios.call("queryLedgerState/epoch", {"oops": 1})
        with pytest.raises(ValueError, match="unknown Ogmios method"):
            await ogmios.call("queryLedgerState/nope")
    assert fake.received == []


async def test_next_transaction_always_sends_params() -> None:
    """The server rejects nextTransaction without params, although the schema says they are optional."""
    async with running() as fake, client(fake) as ogmios:
        await ogmios.call("nextTransaction")
    assert fake.received[-1]["params"] == {}


async def test_request_sends_raw_params_and_returns_raw_json() -> None:
    async with running() as fake, client(fake) as ogmios:
        result = await ogmios.request("queryNetwork/tip")
    assert result == recorded("queryNetwork/tip")["result"]
    assert "params" not in fake.received[-1]


# Concurrency, timeouts and cancellation -----------------------------------------------------------


async def test_concurrent_requests_out_of_order() -> None:
    async with running(FakeOgmios(hold=20)) as fake, client(fake) as ogmios:
        methods = [
            "queryNetwork/tip",
            "queryLedgerState/epoch",
            "queryNetwork/blockHeight",
            "queryLedgerState/eraStart",
        ] * 5
        results = await asyncio.gather(*(ogmios.request(method) for method in methods))
    assert results == [recorded(method)["result"] for method in methods]


async def test_timeout_then_the_connection_keeps_working(caplog: pytest.LogCaptureFixture) -> None:
    fake = FakeOgmios(delays={"queryLedgerState/epoch": 0.3})
    async with running(fake), client(fake, timeout=0.05) as ogmios:
        with pytest.raises(errors.OgmiosTimeoutError) as raised:
            await ogmios.request("queryLedgerState/epoch")
        assert isinstance(raised.value, TimeoutError)
        assert (
            await ogmios.request("queryNetwork/blockHeight")
            == recorded("queryNetwork/blockHeight")["result"]
        )
        with caplog.at_level(logging.DEBUG, logger="pyogmios"):
            await asyncio.sleep(0.4)  # the late answer arrives and is dropped
        assert ogmios.generation == 1
    assert "nobody is waiting" in caplog.text


async def test_per_call_timeout_overrides_the_client_default() -> None:
    fake = FakeOgmios(delays={"queryLedgerState/epoch": 0.1})
    async with running(fake), client(fake, timeout=0.01) as ogmios:
        assert (
            await ogmios.request("queryLedgerState/epoch", timeout=2)
            == recorded("queryLedgerState/epoch")["result"]
        )


async def test_cancelled_request_is_forgotten() -> None:
    fake = FakeOgmios(delays={"queryLedgerState/epoch": 0.5})
    async with running(fake), client(fake) as ogmios:
        task = asyncio.create_task(ogmios.request("queryLedgerState/epoch"))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert isinstance(ogmios.transport, WebSocketTransport)
        assert ogmios.transport._pending == {}


# Connection loss and reconnect ---------------------------------------------------------------------


async def test_dropped_connection_fails_in_flight_requests_then_reconnects() -> None:
    async with running(FakeOgmios(drop_after=1)) as fake, client(fake) as ogmios:
        with pytest.raises(errors.OgmiosConnectionError):
            await ogmios.request("queryLedgerState/epoch")
        assert (
            await ogmios.request("queryLedgerState/epoch")
            == recorded("queryLedgerState/epoch")["result"]
        )
        assert ogmios.generation == 2
        assert fake.connections == 2


async def test_no_reconnect_when_turned_off() -> None:
    fake = FakeOgmios(drop_after=1)
    async with running(fake), pyogmios.AsyncClient(fake.ws_url, reconnect=None) as ogmios:
        with pytest.raises(errors.OgmiosConnectionError):
            await ogmios.request("queryLedgerState/epoch")
        with pytest.raises(errors.OgmiosConnectionError, match="reconnect is off"):
            await ogmios.request("queryLedgerState/epoch")


async def test_connect_retries_then_gives_up() -> None:
    async with running() as fake:
        url = fake.ws_url
    ogmios = pyogmios.AsyncClient(url, reconnect=FAST_RECONNECT, check_version="off")
    with pytest.raises(errors.OgmiosConnectionError, match="cannot connect"):
        await ogmios.connect()


async def test_connects_on_first_use_without_a_context_manager() -> None:
    async with running() as fake:
        ogmios = client(fake)
        assert (
            await ogmios.request("queryLedgerState/epoch")
            == recorded("queryLedgerState/epoch")["result"]
        )
        await ogmios.close()


async def test_messages_that_are_not_json_are_ignored(caplog: pytest.LogCaptureFixture) -> None:
    fake = FakeOgmios(noise="this is not JSON")
    async with running(fake), client(fake) as ogmios:
        assert (
            await ogmios.request("queryLedgerState/epoch")
            == recorded("queryLedgerState/epoch")["result"]
        )
    assert "not JSON" in caplog.text


async def test_an_error_without_id_fails_every_request_in_flight() -> None:
    fake = FakeOgmios(without_id={"queryNetwork/tip"}, delays={"queryLedgerState/epoch": 0.2})
    async with running(fake), client(fake) as ogmios:
        slow = asyncio.create_task(ogmios.request("queryLedgerState/epoch"))
        await asyncio.sleep(0.05)
        with pytest.raises(pyogmios.OgmiosError, match="rejected a request"):
            await ogmios.request("queryNetwork/tip")
        with pytest.raises(pyogmios.OgmiosError, match="rejected a request"):
            await slow


# Version check ----------------------------------------------------------------------------------


async def test_reads_health_when_connecting() -> None:
    async with running() as fake, client(fake) as ogmios:
        assert ogmios.server_health is not None
        assert ogmios.server_health.server_version == (7, 0, 0)
        assert ogmios.server_health.is_synced
        assert (await ogmios.health()).network == "preview"


async def test_older_server_is_refused() -> None:
    fake = FakeOgmios(health={"version": "v6.14.0 (abc)"})
    async with running(fake):
        with pytest.raises(pyogmios.ServerVersionError, match="too old"):
            await client(fake).connect()
    assert fake.connections == 0


async def test_newer_server_warns_or_raises_when_strict() -> None:
    fake = FakeOgmios(health={"version": "v8.0.0"})
    async with running(fake):
        with pytest.warns(UserWarning, match="newer than this client"):
            await (await client(fake).connect()).close()
        with pytest.raises(pyogmios.ServerVersionError):
            await client(fake, check_version="strict").connect()


async def test_unreadable_health_warns_or_raises_when_strict() -> None:
    fake = FakeOgmios(health=404)
    async with running(fake):
        with pytest.warns(UserWarning, match="could not check the Ogmios version"):
            await (await client(fake).connect()).close()
        with pytest.raises(pyogmios.ServerVersionError):
            await client(fake, check_version="strict").connect()


async def test_health_without_a_version() -> None:
    fake = FakeOgmios(health={"network": "preview"})
    async with running(fake):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            await (await client(fake).connect()).close()
        with pytest.raises(pyogmios.ServerVersionError, match="no version"):
            await client(fake, check_version="strict").connect()


async def test_version_check_off_skips_health() -> None:
    async with running() as fake:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            await (await client(fake, check_version="off").connect()).close()
    assert fake.health_requests == 0


def test_health_url_and_version_parsing() -> None:
    assert health_url("ws://localhost:1337") == "http://localhost:1337/health"
    assert (
        health_url("wss://ogmios.example.com/api/v7/") == "https://ogmios.example.com/api/v7/health"
    )
    assert health_url("https://host:443/x?key=1") == "https://host:443/x/health"
    with pytest.raises(ValueError, match="unsupported scheme"):
        health_url("tcp://host")
    assert parse_version("v7.0.0 (ef123abd)") == (7, 0, 0)
    assert parse_version("7.12.3") == (7, 12, 3)
    assert parse_version("unknown") is None


def test_unsupported_url_scheme() -> None:
    with pytest.raises(ValueError, match="unsupported Ogmios URL"):
        pyogmios.AsyncClient("tcp://localhost:1337")


# HTTP ---------------------------------------------------------------------------------------------


def http_client(handler: Any, **options: Any) -> pyogmios.AsyncClient:
    transport = HttpTransport(
        "http://ogmios.test:1337",
        reconnect=FAST_RECONNECT,
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    return pyogmios.AsyncClient(
        "http://ogmios.test:1337", transport=transport, check_version="off", **options
    )


def replay(request: httpx.Request) -> httpx.Response:
    body = _json.loads(request.content)
    response = dict(recorded(body["method"]))
    response["id"] = body["id"]
    return httpx.Response(400 if "error" in response else 200, json=response)


async def test_http_call_and_error() -> None:
    async with http_client(replay) as ogmios:
        assert (
            await ogmios.call("queryLedgerState/epoch")
            == recorded("queryLedgerState/epoch")["result"]
        )
    error_response = recorded("acquireLedgerState", "point-not-on-chain")

    def failing(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400, json={**error_response, "id": _json.loads(request.content)["id"]}
        )

    async with http_client(failing) as ogmios:
        with pytest.raises(errors.LedgerStateQueryError):
            await ogmios.request("queryLedgerState/epoch")


async def test_http_refuses_stateful_methods() -> None:
    async with http_client(replay) as ogmios:
        for method in ("nextBlock", "findIntersection", "acquireMempool", "acquireLedgerState"):
            with pytest.raises(pyogmios.StatefulOverHttpError):
                await ogmios.request(method)


async def test_http_non_json_answer() -> None:
    async with http_client(lambda request: httpx.Response(502, text="Bad Gateway")) as ogmios:
        with pytest.raises(pyogmios.OgmiosError, match="HTTP 502"):
            await ogmios.request("queryLedgerState/epoch")


async def test_http_retries_connection_failures_only() -> None:
    attempts = 0

    def unreachable(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("refused", request=request)

    async with http_client(unreachable) as ogmios:
        with pytest.raises(errors.OgmiosConnectionError):
            await ogmios.request("queryLedgerState/epoch")
    assert attempts == FAST_RECONNECT.attempts


# The sync client ----------------------------------------------------------------------------------


@pytest.fixture
def sync_fake() -> Any:
    """A fake server on its own event loop thread, for the synchronous client."""
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    context = running()
    fake = asyncio.run_coroutine_threadsafe(context.__aenter__(), loop).result()
    yield fake
    asyncio.run_coroutine_threadsafe(context.__aexit__(None, None, None), loop).result()
    loop.call_soon_threadsafe(loop.stop)
    thread.join()
    loop.close()


def test_sync_client(sync_fake: FakeOgmios) -> None:
    sync_fake.responses["acquireLedgerState"] = recorded("acquireLedgerState", "point-not-on-chain")
    with pyogmios.Client(sync_fake.ws_url, reconnect=FAST_RECONNECT) as ogmios:
        assert ogmios.server_health is not None
        assert ogmios.call("queryLedgerState/epoch") == recorded("queryLedgerState/epoch")["result"]
        with pytest.raises(errors.AcquireLedgerStateError):
            ogmios.call("acquireLedgerState", {"point": {"slot": 1, "id": "0" * 64}})
    assert not ogmios._portal._thread.is_alive()


def test_sync_client_from_many_threads(sync_fake: FakeOgmios) -> None:
    results: list[Any] = []
    with pyogmios.Client(sync_fake.ws_url, reconnect=FAST_RECONNECT) as ogmios:
        threads = [
            threading.Thread(
                target=lambda: results.append(ogmios.request("queryNetwork/blockHeight"))
            )
            for _ in range(16)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    assert results == [recorded("queryNetwork/blockHeight")["result"]] * 16


# JSON -----------------------------------------------------------------------------------------------


def test_big_integers_stay_exact() -> None:
    """orjson decodes integers beyond 64 bits as floats; those documents use the stdlib instead."""
    big = 2**70 + 1
    assert _json.loads(_json.dumps({"n": big}))["n"] == big
    assert _json.loads('{"n": 18446744073709551616}')["n"] == 2**64
    assert _json.loads(b'{"x": 1.5, "n": 7}') == {"x": 1.5, "n": 7}


# Helpers -----------------------------------------------------------------------------------------


def _params_for(fixture: Fixture) -> Any:
    """Params that pass client-side validation, for methods that require them."""
    return {
        "queryNetwork/genesisConfiguration": {
            "era": fixture.case
            if fixture.case in ("byron", "shelley", "alonzo", "conway")
            else "conway"
        },
        "queryLedgerState/projectedRewards": {"stake": [{"ada": {"lovelace": 1}}]},
        "queryLedgerState/rewardAccountSummaries": {"keys": []},
    }.get(fixture.method)
