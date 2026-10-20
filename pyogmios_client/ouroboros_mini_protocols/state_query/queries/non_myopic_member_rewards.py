from typing import List

from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import Method
from pyogmios_client.exceptions import (
    QueryUnavailableInCurrentEraError,
    EraMismatchError,
    UnknownResultError,
)
from pyogmios_client.models import (
    Lovelace,
    DigestBlake2bCredential,
    NonMyopicMemberRewards,
    StakeAddress,
    QueryUnavailableInCurrentEra,
    EraMismatch,
)
from pyogmios_client.models.response_model import NonMyopicMemberRewardsResponse
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def non_myopic_member_rewards(
    context: InteractionContext,
    input_list: List[Lovelace] | List[DigestBlake2bCredential] | List[StakeAddress],
) -> NonMyopicMemberRewards:
    """
    Query the non-myopic member rewards for the given stake key hashes.
    :param context: The interaction context to use for the query.
    :param input_list: The stake key hashes to query.
    :return: The non-myopic member rewards for the given stake key hashes.
    """
    request_args = RequestArgs(
        method=Method.QUERY,
        params={"query": {"nonMyopicMemberRewards": input_list}},
    )

    try:
        response = await query(request_args, context)
        query_response = NonMyopicMemberRewardsResponse(**response.model_dump())
        result = query_response.result
        if isinstance(result, QueryUnavailableInCurrentEra):
            raise QueryUnavailableInCurrentEraError("nonMyopicMemberRewards")
        elif isinstance(result, NonMyopicMemberRewards):
            return result
        elif isinstance(result, EraMismatch):
            raise EraMismatchError(result.queryEra.value, result.ledgerEra.value)
        else:
            raise UnknownResultError(response)
    except Exception as error:
        raise error
