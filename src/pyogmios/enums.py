from enum import Enum


class AcquireFailureDetails(Enum):
    POINT_TOO_OLD = "pointTooOld"
    POINT_NOT_ON_CHAIN = "pointNotOnChain"


class InputSource(Enum):
    INPUTS = "inputs"
    COLLATERALS = "collaterals"


class InteractionType(Enum):
    ONE_TIME = "OneTime"
    LONG_RUNNING = "LongRunning"


class Language(Enum):
    PLUTUS_V_1 = "plutus:v1"
    PLUTUS_V_2 = "plutus:v2"


class Method(Enum):
    """
    The method.
    """

    NEXT_BLOCK = "nextBlock"
    FIND_INTERSECTION = "findIntersection"
    SUBMIT_TRANSACTION = "submitTransaction"
    EVALUATE_TRANSACTION = "evaluateTransaction"
    ACQUIRE_LEDGER_STATE = "acquireLedgerState"
    RELEASE_LEDGER_STATE = "releaseLedgerState"
    ACQUIRE_MEMPOOL = "acquireMempool"
    NEXT_TRANSACTION = "nextTransaction"
    HAS_TRANSACTION = "hasTransaction"
    SIZE_OF_MEMPOOL = "sizeOfMempool"
    RELEASE_MEMPOOL = "releaseMempool"
    QUERY_LEDGER_STATE = "queryLedgerState"
    QUERY_NETWORK = "queryNetwork"


class NetworkQuery(Enum):
    """
    The network queries.
    """

    BLOCK_HEIGHT = f"{Method.QUERY_NETWORK.value}/blockHeight"
    TIP = f"{Method.QUERY_NETWORK.value}/tip"
    GENESIS_CONFIGURATION = f"{Method.QUERY_NETWORK.value}/genesisConfiguration"
    START_TIME = f"{Method.QUERY_NETWORK.value}/startTime"


class LedgerStateQuery(Enum):
    """
    The ledger state queries.
    """

    EPOCH = f"{Method.QUERY_LEDGER_STATE.value}/epoch"
    PROTOCOL_PARAMETERS = f"{Method.QUERY_LEDGER_STATE.value}/protocolParameters"
    REWARD_ACCOUNT_SUMMARIES = f"{Method.QUERY_LEDGER_STATE.value}/rewardAccountSummaries"
    ERA_START = f"{Method.QUERY_LEDGER_STATE.value}/eraStart"
    ERA_SUMMARIES = f"{Method.QUERY_LEDGER_STATE.value}/eraSummaries"
    TIP = f"{Method.QUERY_LEDGER_STATE.value}/tip"
    PROJECTED_REWARDS = f"{Method.QUERY_LEDGER_STATE.value}/projectedRewards"
    PROPOSED_PROTOCOL_PARAMETERS = f"{Method.QUERY_LEDGER_STATE.value}/proposedProtocolParameters"
    REWARDS_PROVENANCE = f"{Method.QUERY_LEDGER_STATE.value}/rewardsProvenance"
    LIVE_STAKE_DISTRIBUTION = f"{Method.QUERY_LEDGER_STATE.value}/liveStakeDistribution"
    UTXO = f"{Method.QUERY_LEDGER_STATE.value}/utxo"


class Network(Enum):
    MAINNET = "mainnet"
    TESTNET = "testnet"


class NonceEnum(Enum):
    NEUTRAL = "neutral"


# class Origin(Enum):
#     ORIGIN = 'origin'
class Origin(Enum):
    origin = "origin"


class RewardPot(Enum):
    RESERVES = "reserves"
    TREASURY = "treasury"


class ServiceName(Enum):
    OGMIOS = "ogmios"


class Type(Enum):
    JSONWSP_REQUEST = "jsonwsp/request"
    JSONWSP_RESPONSE = "jsonwsp/response"
    JSONWSP_FAULT = "jsonwsp/fault"


class Version(Enum):
    v1_0 = "1.0"


class InvalidEntityType(Enum):
    ADDRESS = "address"
    POOL_REGISTRATION = "poolRegistration"
    REWARD_ACCOUNT = "rewardAccount"


class InvalidEntityEntity(Enum):
    ADDRESS = "Address"
    POOL_REGISTRATION = "PoolId"
    REWARD_ACCOUNT = "RewardAccount"


class EraWithGenesis(Enum):
    BYRON = "Byron"
    SHELLEY = "Shelley"
    ALONZO = "Alonzo"
    CONWAY = "Conway"


class IncompatibleEraEnum(Enum):
    BYRON = "Byron"
    SHELLEY = "Shelley"
    ALLEGRA = "Allegra"
    MARY = "Mary"
