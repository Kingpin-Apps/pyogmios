import pytest

from pyogmios.connection import (
    create_interaction_context,
)
from pyogmios.exceptions import (
    EraMismatchError,
    QueryUnavailableInCurrentEraError,
)
from pyogmios.models import (
    DigestBlake2bBlockHeader,
    Era,
    EraMismatch,
    Point,
    PointOrOrigin,
    QueryUnavailableInCurrentEra,
)
from pyogmios.models.response_model import (
    QueryLedgerStateTipResponse,
    QueryResponseReflection,
)
from pyogmios.models.result_models import EraMismatchResult
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)


@pytest.mark.parametrize(
    "test_input",
    [
        Point(slot=123456789, hash=DigestBlake2bBlockHeader(b"1" * 64)),
        "origin",
    ],
)
@pytest.mark.asyncio
async def test_ledger_tip(mocker, test_input):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.ledger_tip.query",
        return_value=QueryLedgerStateTipResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=test_input,
        ),
    )
    interaction_context = await create_interaction_context()
    client = await create_state_query_client(interaction_context)
    ledger_tip = await client.ledger_tip()
    await client.shutdown()
    assert isinstance(ledger_tip, PointOrOrigin)


@pytest.mark.asyncio
async def test_ledger_tip_query_unavailable(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.ledger_tip.query",
        return_value=QueryLedgerStateTipResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result="QueryUnavailableInCurrentEra",
        ),
    )

    # Act & Assert
    with pytest.raises(QueryUnavailableInCurrentEraError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        ledger_tip = await client.ledger_tip()
        client.shutdown()
        assert isinstance(ledger_tip, QueryUnavailableInCurrentEra)
    assert exc_info.value.query_name == "ledgerTip"
    assert exc_info.value.message == "QueryUnavailableInCurrentEra. ledgerTip"


@pytest.mark.asyncio
async def test_ledger_tip_era_mismatch(mocker, fake_era_mismatch_result):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.ledger_tip.query",
        return_value=QueryLedgerStateTipResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=EraMismatch(**fake_era_mismatch_result["eraMismatch"]),
        ),
    )

    # Act & Assert
    with pytest.raises(EraMismatchError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        ledger_tip = await client.ledger_tip()
        client.shutdown()
        assert isinstance(ledger_tip, EraMismatchResult)

    query_era = Era(fake_era_mismatch_result["eraMismatch"]["queryEra"]).value
    ledger_era = Era(fake_era_mismatch_result["eraMismatch"]["ledgerEra"]).value

    assert exc_info.value.query_era == query_era
    assert exc_info.value.ledger_era == ledger_era
    assert (
        exc_info.value.message
        == f"Era mismatch. Query from era {query_era}. Ledger is in {ledger_era}"
    )
