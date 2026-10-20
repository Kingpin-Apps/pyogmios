from pyogmios.connection import InteractionContext
from pyogmios.enums import EraWithGenesis, NetworkQuery
from pyogmios.models import (
    GenesisConfig,
)
from pyogmios.models.response_model import (
    QueryNetworkGenesisConfigurationResponse,
)
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    RequestArgs,
    query,
)


async def genesis_config(context: InteractionContext, era: EraWithGenesis) -> GenesisConfig:
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
