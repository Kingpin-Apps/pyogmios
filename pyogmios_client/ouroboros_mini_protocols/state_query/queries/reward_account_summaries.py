from typing import List, Optional

from pyogmios_client.connection import InteractionContext
from pyogmios_client.enums import LedgerStateQuery
from pyogmios_client.models import (
    RewardAccountSummaries,
    AnyStakeCredential,
)
from pyogmios_client.models.response_model import (
    QueryLedgerStateRewardAccountSummariesResponse,
)
from pyogmios_client.ouroboros_mini_protocols.state_query.query import (
    query,
    RequestArgs,
)


async def reward_account_summaries(
    context: InteractionContext,
    scripts: Optional[List[AnyStakeCredential]] = None,
    keys: Optional[List[AnyStakeCredential]] = None,
) -> RewardAccountSummaries:
    """
    Query current delegation settings and rewards of some given reward accounts.
    :param context: The interaction context to use for the query.
    :param scripts: The script hashes to query.
    :param keys: The key hashes to query.
    :return: The delegations and rewards for the given stake key hashes.
    """
    request_args = RequestArgs(
        method=LedgerStateQuery.REWARD_ACCOUNT_SUMMARIES,
        params={
            "scripts": scripts,
            "keys": keys,
        },
    )

    try:
        response = await query(request_args, context)
        query_response = QueryLedgerStateRewardAccountSummariesResponse.model_validate(
            response.model_dump()
        )
        return query_response.result
    except Exception as error:
        raise error
