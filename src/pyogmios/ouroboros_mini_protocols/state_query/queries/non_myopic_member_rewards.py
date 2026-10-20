from pyogmios.connection import InteractionContext
from pyogmios.enums import Method
from pyogmios.exceptions import (
    EraMismatchError,
    QueryUnavailableInCurrentEraError,
    UnknownResultError,
)
from pyogmios.models import (
    DigestBlake2bCredential,
    EraMismatch,
    Lovelace,
    NonMyopicMemberRewards,
    QueryUnavailableInCurrentEra,
    StakeAddress,
)
from pyogmios.models.response_model import NonMyopicMemberRewardsResponse
from pyogmios.ouroboros_mini_protocols.state_query.query import (
    RequestArgs,
    query,
)


async def non_myopic_member_rewards(
    context: InteractionContext,
    input_list: list[Lovelace] | list[DigestBlake2bCredential] | list[StakeAddress],
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
