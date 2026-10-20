from __future__ import annotations

import json

from nanoid import generate

from pyogmios.connection import InteractionContext
from pyogmios.enums import AcquireFailureDetails, EraWithGenesis
from pyogmios.exceptions import (
    AcquirePointNotOnChainError,
    AcquirePointTooOldError,
    RequestError,
    UnknownResultError,
)
from pyogmios.models import (
    AnyStakeCredential,
    BaseModel,
    BlockNoOrOrigin,
    Bound,
    DigestBlake2bCredential,
    Epoch,
    EraSummary,
    GenesisConfig,
    Lovelace,
    NonMyopicMemberRewards,
    PointOrOrigin,
    PoolDistribution,
    PoolId,
    PoolParameters,
    PoolsRanking,
    ProtocolParameters,
    ProtocolParametersAlonzo,
    ProtocolParametersBabbage,
    ProtocolParametersShelley,
    RewardAccountSummaries,
    RewardsProvenance,
    RewardsProvenanceNew,
    UtcTime,
)
from pyogmios.models.request_model import AcquireLedgerState, ReleaseLedgerState
from pyogmios.models.response_model import AcquireResponse, ReleaseResponse
from pyogmios.models.result_models import (
    AcquireFailureResult,
    AcquireSuccessResult,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.ledger_state.epoch import (
    epoch,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.ledger_state.era_start import (
    era_start,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.ledger_state.era_summaries import (
    era_summaries,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.ledger_state.protocol_parameters import (
    protocol_parameters,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.ledger_state.tip import (
    tip as ledger_tip,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.network.block_height import (
    block_height,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.network.genesis_config import (
    genesis_config,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.network.tip import (
    tip,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.non_myopic_member_rewards import (
    non_myopic_member_rewards,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.pool_ids import (
    pool_ids,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.pool_parameters import (
    pool_parameters,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.pools_ranking import (
    pools_ranking,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.proposed_protocol_parameters import (
    proposed_protocol_parameters,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.reward_account_summaries import (
    reward_account_summaries,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.rewards_provenance import (
    rewards_provenance,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.rewards_provenance_new import (
    rewards_provenance_new,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.stake_distribution import (
    stake_distribution,
)
from pyogmios.ouroboros_mini_protocols.state_query.queries.system_start import (
    start_time,
)
from pyogmios.utils.socket_utils import ensure_socket_is_open


class Options(BaseModel):
    point: PointOrOrigin


class QueryLedgerState(BaseModel):
    """
    Namespace for ledger state queries
    """

    context: InteractionContext

    async def epoch(self) -> Epoch:
        """
        Query the epoch
        """
        await ensure_socket_is_open(self.context.socket)
        return await epoch(self.context)

    async def protocol_parameters(self) -> ProtocolParameters:
        """
        Query the current protocol parameters
        """
        await ensure_socket_is_open(self.context.socket)
        return await protocol_parameters(self.context)

    async def reward_account_summaries(
        self,
        scripts: list[AnyStakeCredential] | None = None,
        keys: list[AnyStakeCredential] | None = None,
    ) -> RewardAccountSummaries:
        """
        Query delegations and rewards
        """
        await ensure_socket_is_open(self.context.socket)
        return await reward_account_summaries(self.context, scripts, keys)

    async def era_start(self) -> Bound:
        """
        Query the era start
        """
        await ensure_socket_is_open(self.context.socket)
        return await era_start(self.context)

    async def era_summaries(self) -> list[EraSummary]:
        """
        Query the era summaries
        """
        await ensure_socket_is_open(self.context.socket)
        return await era_summaries(self.context)

    async def tip(self) -> PointOrOrigin:
        """
        Query the ledger tip
        """
        await ensure_socket_is_open(self.context.socket)
        return await ledger_tip(self.context)


class QueryNetwork(BaseModel):
    """
    Namespace for network queries
    """

    context: InteractionContext

    async def block_height(self) -> BlockNoOrOrigin:
        """
        Query the block height
        """
        await ensure_socket_is_open(self.context.socket)
        return await block_height(self.context)

    async def tip(self) -> PointOrOrigin:
        """
        Query the chain tip
        """
        await ensure_socket_is_open(self.context.socket)
        return await tip(self.context)

    async def genesis_config(self, era: EraWithGenesis) -> GenesisConfig:
        """
        Query the genesis config
        """
        await ensure_socket_is_open(self.context.socket)
        return await genesis_config(self.context, era)

    async def start_time(self) -> UtcTime:
        """
        Query system start
        """
        await ensure_socket_is_open(self.context.socket)
        return await start_time(self.context)


class StateQueryClient(BaseModel):
    """
    Data model for the state query client
    """

    context: InteractionContext
    query_ledger_state: QueryLedgerState
    query_network: QueryNetwork

    async def acquire(self, point: PointOrOrigin) -> StateQueryClient:
        """
        Acquire the a point
        """
        return await create_state_query_client(self.context, Options(point=point))

    async def release(self) -> ReleaseResponse | None:
        """
        Release the state query client
        """
        websocket_app = self.context.socket

        await ensure_socket_is_open(websocket_app)
        request_id = generate(size=5)
        try:
            request = ReleaseLedgerState.from_base(request_id=request_id)
            websocket_app.send(request.model_dump_json())
            result = websocket_app.sock.recv()
            release_response = ReleaseResponse(**json.loads(result))

            if release_response.reflection.requestId != request_id:
                return None

            return release_response
        except Exception as e:
            raise e

    async def shutdown(self) -> None:
        """
        Shutdown the state query client
        """
        try:
            await ensure_socket_is_open(self.context.socket)
            self.context.socket.close()
        except Exception as err:
            print(err)
        else:
            print("Shutting down State Query Client...")

    async def non_myopic_member_rewards(
        self,
        input_list: list[Lovelace] | list[DigestBlake2bCredential],
    ) -> NonMyopicMemberRewards:
        """
        Query non myopic member rewards
        """
        await ensure_socket_is_open(self.context.socket)
        return await non_myopic_member_rewards(self.context, input_list)

    async def pool_ids(self) -> list[PoolId]:
        """
        Query pool ids
        """
        await ensure_socket_is_open(self.context.socket)
        return await pool_ids(self.context)

    async def pool_parameters(self, pools: list[PoolId]) -> dict[str, PoolParameters]:
        """
        Query pool parameters
        """
        await ensure_socket_is_open(self.context.socket)
        return await pool_parameters(self.context, pools)

    async def pools_ranking(self) -> PoolsRanking:
        """
        Query pools ranking
        """
        await ensure_socket_is_open(self.context.socket)
        return await pools_ranking(self.context)

    async def proposed_protocol_parameters(
        self,
    ) -> (
        dict[str, ProtocolParametersShelley]
        | dict[str, ProtocolParametersAlonzo]
        | dict[str, ProtocolParametersBabbage]
        | None
    ):
        """
        Query proposed protocol parameters
        """
        await ensure_socket_is_open(self.context.socket)
        return await proposed_protocol_parameters(self.context)

    async def rewards_provenance(self) -> RewardsProvenance:
        """
        Query rewards provenance
        """
        await ensure_socket_is_open(self.context.socket)
        return await rewards_provenance(self.context)

    async def rewards_provenance_new(self) -> RewardsProvenanceNew:
        """
        Query rewards provenance new
        """
        await ensure_socket_is_open(self.context.socket)
        return await rewards_provenance_new(self.context)

    async def stake_distribution(self) -> PoolDistribution:
        """
        Query stake distribution
        """
        await ensure_socket_is_open(self.context.socket)
        return await stake_distribution(self.context)


async def create_state_query_client(
    context: InteractionContext, options: Options = None
) -> StateQueryClient | None:
    """
    Create a state query client
    :param context: The interaction context
    :param options: The options
    :return: A state query client
    """
    websocket_app = context.socket

    try:

        def create_client() -> StateQueryClient:
            """
            Create a state query client
            """
            return StateQueryClient(
                context=context,
                query_ledger_state=QueryLedgerState(context=context),
                query_network=QueryNetwork(context=context),
            )

        if options and options.point:
            # point = options.point
            await_acquire_request_id = generate(size=5)
            # await ensure_socket_is_open(websocket_app)
            try:
                await_acquire_request = AcquireLedgerState.from_base(
                    request_id=await_acquire_request_id
                )
                websocket_app.send(await_acquire_request.model_dump_json())
                await_acquire_result = websocket_app.sock.recv()
                acquire_response = AcquireResponse(**json.loads(await_acquire_result))

                if acquire_response.reflection.requestId != await_acquire_request_id:
                    return None

                if isinstance(acquire_response.result, AcquireSuccessResult):
                    return create_client()
                elif isinstance(acquire_response.result, AcquireFailureResult):
                    websocket_app.close()
                    failure = acquire_response.result.AcquireFailure.failure
                    match failure:
                        case AcquireFailureDetails.POINT_TOO_OLD:
                            raise AcquirePointTooOldError()
                        case AcquireFailureDetails.POINT_NOT_ON_CHAIN:
                            raise AcquirePointNotOnChainError()
                        case _:
                            raise RequestError(failure)
                else:
                    raise UnknownResultError(acquire_response.result)
            except Exception as error:
                raise error
        else:
            return create_client()
    except Exception as e:
        raise e
