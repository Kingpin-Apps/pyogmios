import pytest

from pyogmios.connection import (
    create_interaction_context,
)
from pyogmios.exceptions import EraMismatchError
from pyogmios.models import (
    Era,
    ProtocolParametersAlonzo,
    ProtocolParametersBabbage,
    ProtocolParametersShelley,
)
from pyogmios.models.response_model import (
    QueryLedgerStateProtocolParametersResponse,
    QueryResponseReflection,
)
from pyogmios.models.result_models import EraMismatchResult
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)
from tests.conftest import (
    ProtocolParametersAlonzoFactory,
    ProtocolParametersBabbageFactory,
    ProtocolParametersShelleyFactory,
)


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        (ProtocolParametersShelleyFactory.build(), ProtocolParametersShelley),
        (ProtocolParametersAlonzoFactory.build(), ProtocolParametersAlonzo),
        (ProtocolParametersBabbageFactory.build(), ProtocolParametersBabbage),
    ],
)
@pytest.mark.asyncio
async def test_current_protocol_parameters(mocker, test_input, expected):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.protocol_parameters.query",
        return_value=QueryLedgerStateProtocolParametersResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=test_input,
        ),
    )

    interaction_context = await create_interaction_context()

    client = await create_state_query_client(interaction_context)
    current_protocol_parameters = await client.protocol_parameters()
    await client.shutdown()

    assert isinstance(current_protocol_parameters, expected)


@pytest.mark.asyncio
async def test_current_protocol_parameters_era_mismatch(mocker, fake_era_mismatch_result):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.protocol_parameters.query",
        return_value=QueryLedgerStateProtocolParametersResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=EraMismatchResult(**fake_era_mismatch_result),
        ),
    )

    # Act & Assert
    with pytest.raises(EraMismatchError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        current_protocol_parameters = await client.protocol_parameters()
        client.shutdown()
        assert isinstance(current_protocol_parameters, EraMismatchResult)

    query_era = Era(fake_era_mismatch_result["eraMismatch"]["queryEra"]).value
    ledger_era = Era(fake_era_mismatch_result["eraMismatch"]["ledgerEra"]).value

    assert exc_info.value.query_era == query_era
    assert exc_info.value.ledger_era == ledger_era
    assert (
        exc_info.value.message
        == f"Era mismatch. Query from era {query_era}. Ledger is in {ledger_era}"
    )
