from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import EraWithGenesis, NetworkQuery
from pyogmios_client.models import (
    GenesisConfig,
)
from pyogmios_client.models.response_model import (
    QueryNetworkGenesisConfigurationResponse,
)
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def genesis_config(
    context: InteractionContext, era: EraWithGenesis
) -> GenesisConfig:
    """
    Query the genesis config.
    :param context: The interaction context to use for the query.
    :param era: The era to query the genesis config for.
    :return: The genesis config.
    """
    request_args = RequestArgs(
        method=NetworkQuery.GENESIS_CONFIGURATION,
        params={"era": era},
    )

    try:
        response = await query(request_args, context)
        query_response = QueryNetworkGenesisConfigurationResponse.model_validate(
            response.model_dump()
        )
        return query_response.result
    except Exception as error:
        raise error
