import pytest

from pyogmios.connection import (
    create_interaction_context,
)
from pyogmios.enums import EraWithGenesis
from pyogmios.exceptions import (
    EraMismatchError,
    QueryUnavailableInCurrentEraError,
)
from pyogmios.models import (
    Era,
    EraMismatch,
    GenesisAlonzo,
    GenesisByron,
    GenesisShelley,
    QueryUnavailableInCurrentEra,
)
from pyogmios.models.response_model import (
    QueryNetworkGenesisConfigurationResponse,
    QueryResponseReflection,
)
from pyogmios.models.result_models import EraMismatchResult
from pyogmios.ouroboros_mini_protocols.state_query.state_query_client import (
    create_state_query_client,
)
from tests.legacy.conftest import (
    GenesisAlonzoFactory,
    GenesisByronFactory,
    GenesisShelleyFactory,
)


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        (GenesisAlonzoFactory.build(), GenesisAlonzo),
        (GenesisByronFactory.build(), GenesisByron),
        (GenesisShelleyFactory.build(), GenesisShelley),
    ],
)
@pytest.mark.asyncio
async def test_genesis_config(mocker, test_input, expected):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.genesis_config.query",
        return_value=QueryNetworkGenesisConfigurationResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=test_input,
        ),
    )
    interaction_context = await create_interaction_context()
    client = await create_state_query_client(interaction_context)
    genesis_config = await client.genesis_config(EraWithGenesis.SHELLEY)
    await client.shutdown()

    assert isinstance(genesis_config, expected)


@pytest.mark.asyncio
async def test_genesis_config_query_unavailable(mocker):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.genesis_config.query",
        return_value=QueryNetworkGenesisConfigurationResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result="QueryUnavailableInCurrentEra",
        ),
    )

    # Act & Assert
    with pytest.raises(QueryUnavailableInCurrentEraError) as exc_info:
        interaction_context = await create_interaction_context()
        client = await create_state_query_client(interaction_context)
        genesis_config = await client.genesis_config(EraWithGenesis.SHELLEY)
        client.shutdown()
        assert isinstance(genesis_config, QueryUnavailableInCurrentEra)
    assert exc_info.value.query_name == "genesisConfig"
    assert exc_info.value.message == "QueryUnavailableInCurrentEra. genesisConfig"


@pytest.mark.asyncio
async def test_genesis_config_era_mismatch(mocker, fake_era_mismatch_result):
    mocker.patch(
        "pyogmios.ouroboros_mini_protocols.state_query.queries.genesis_config.query",
        return_value=QueryNetworkGenesisConfigurationResponse.from_base_response(
            reflection=QueryResponseReflection(requestId="test-request-id"),
            result=EraMismatch(**fake_era_mismatch_result["eraMismatch"]),
        ),
    )

    # Act & Assert
    with pytest.raises(EraMismatchError) as exc_info:
        interaction_context = await create_interaction_context()

        client = await create_state_query_client(interaction_context)
        genesis_config = await client.genesis_config(EraWithGenesis.SHELLEY)
        client.shutdown()
        assert isinstance(genesis_config, EraMismatchResult)

    query_era = Era(fake_era_mismatch_result["eraMismatch"]["queryEra"]).value
    ledger_era = Era(fake_era_mismatch_result["eraMismatch"]["ledgerEra"]).value

    assert exc_info.value.query_era == query_era
    assert exc_info.value.ledger_era == ledger_era
    assert (
        exc_info.value.message
        == f"Era mismatch. Query from era {query_era}. Ledger is in {ledger_era}"
    )
