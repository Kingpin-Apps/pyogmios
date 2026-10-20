from __future__ import annotations

from datetime import datetime
from enum import Enum
from types import UnionType
from typing import Optional, Dict, List, Union

from pydantic import conint, Field, constr, confloat, AnyUrl, RootModel
from typing_extensions import Annotated, Literal, TypedDict

from pyogmios.enums import (
    RewardPot,
    NonceEnum,
    Network,
    InputSource,
    Language,
    InvalidEntityType,
    InvalidEntityEntity,
    IncompatibleEraEnum,
)
from pyogmios.models.base_model import BaseModel

Slot = int

DigestAny = str


class Origin(RootModel):
    root: str = "origin"


BlockNo = int

Metadatum: UnionType = int | str | bytes | List | Dict

StakePoolId = str

DigestBlake2B224 = str
"""A Blake2b 28-byte hash digest, encoded in base16."""


class Address(RootModel):
    root: Annotated[
        str,
        Field(
            pattern=r"[1-9A-HJ-NP-Za-km-z]*",
            description="A Cardano address (either legacy format or new format).",
            examples=[
                "addr1q9d34spgg2kdy47n82e7x9pdd6vql6d2engxmpj20jmhuc2047yqd4xnh7u6u5jp4t0q3fkxzckph4tgnzvamlu7k5psuahzcp",
                "DdzFFzCqrht8mbSTZHqpM2u4HeND2mdspsaBhdQ1BowPJBMzbDeBMeKgqdoKqo1D4sdPusEdZJVrFJRBBxX1jUEofNDYCJSZLg8MkyCE",
            ],
        ),
    ]


class AddressAttributes(RootModel):
    root: str = Field(
        ...,
        description="Extra attributes carried by Byron addresses (network magic and/or HD payload).",
    )


class AssetQuantity(RootModel):
    root: int = Field(
        ..., description="A number of asset, can be negative went burning assets."
    )


class BlockNo(RootModel):
    root: conint(ge=0, le=18446744073709552999) = Field(
        ..., description="A block number, the i-th block to be minted is number i."
    )


class BlockNoOrOrigin(RootModel):
    root: Union[BlockNo, Origin]


class BlockSize(RootModel):
    root: conint(ge=0, le=18446744073709552999) = Field(
        ..., description="The size of the block in bytes."
    )


class StakeDelegation(BaseModel):
    delegator: DigestBlake2bCredential
    delegatee: PoolId


class StakeDelegationCertificate(BaseModel):
    stakeDelegation: StakeDelegation


class StakeKeyRegistrationCertificate(BaseModel):
    stakeKeyRegistration: DigestBlake2bCredential


class StakeKeyDeregistrationCertificate(BaseModel):
    stakeKeyDeregistration: DigestBlake2bCredential


class PoolRegistrationCertificate(BaseModel):
    poolRegistration: PoolParameters


class PoolRetirement(BaseModel):
    retirementEpoch: Epoch
    poolId: PoolId


class PoolRetirementCertificate(BaseModel):
    poolRetirement: PoolRetirement


class GenesisDelegation(BaseModel):
    delegateKeyHash: DigestBlake2bVerificationKey
    verificationKeyHash: DigestBlake2bVerificationKey
    vrfVerificationKeyHash: DigestBlake2bVrfVerificationKey


class GenesisDelegationCertificate(BaseModel):
    genesisDelegation: GenesisDelegation


class MoveInstantaneousRewards(BaseModel):
    rewards: Optional[Rewards] = None
    value: Optional[Lovelace] = None
    pot: RewardPot


class MoveInstantaneousRewardsCertificate(BaseModel):
    moveInstantaneousRewards: MoveInstantaneousRewards


Certificate = (
    StakeDelegationCertificate
    | StakeKeyRegistrationCertificate
    | StakeKeyDeregistrationCertificate
    | PoolRegistrationCertificate
    | PoolRetirementCertificate
    | GenesisDelegationCertificate
    | MoveInstantaneousRewardsCertificate
)


class CertifiedVrf(BaseModel):
    proof: Optional[VrfProof] = None
    output: Optional[VrfOutput] = None


class ChainCode(RootModel):
    root: str = Field(
        ..., description="An Ed25519-BIP32 chain-code for key deriviation."
    )


class CostModel(RootModel):
    root: Optional[List[Int64]] = None


class CostModels(RootModel):
    root: Optional[Dict[str, CostModel]] = None


class Datum(RootModel):
    root: str


class RewardAccountSummaries(RootModel):
    root: Optional[Dict[str, RewardAccountSummary]] = None


class RewardAccountSummary(BaseModel):
    delegate: TypedDict("id", {"id": StakePoolId})
    rewards: Lovelace


DigestBlake2BCredential = str


class DigestBlake2bAuxiliaryDataBody(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ...,
        description="A Blake2b 32-byte digest of an 'AuxiliaryDataBody', serialised as CBOR.",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class DigestBlake2bBlockBody(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ...,
        description="A Blake2b 32-byte digest of an era-independent block body.",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class HeaderEnum(Enum):
    genesis = "genesis"


class DigestBlake2bBlockHeader(RootModel):
    root: Union[constr(min_length=64, max_length=64), HeaderEnum]


class DigestBlake2bCredential(RootModel):
    root: constr(min_length=56, max_length=56) = Field(
        ...,
        description="A Blake2b 28-byte digest of a verification key or a script.",
        examples=["90181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d3"],
    )


class DigestBlake2bDatum(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ...,
        description="A Blake2b 32-byte digest of a serialized datum, CBOR-encoded.",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class DigestBlake2bMerkleRoot(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ...,
        description="A Blake2b 32-byte digest of a Merkle tree (or all block's transactions) root hash.",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class DigestBlake2bNonce(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ...,
        description="A Blake2b 32-byte digest of some arbitrary to make a nonce.",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class DigestBlake2bPoolMetadata(RootModel):
    root: str = Field(
        ...,
        description="A Blake2b 32-byte digest of stake pool (canonical) JSON metadata.",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class DigestBlake2bScript(RootModel):
    root: constr(min_length=56, max_length=56) = Field(
        ...,
        description="A Blake2b 32-byte digest of a phase-1 or phase-2 script, CBOR-encoded.",
        examples=["90181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d3"],
    )


class DigestBlake2bScriptIntegrity(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ...,
        description="A Blake2b 32-byte digest of a script-integrity hash (i.e redeemers, datums and cost model, CBOR-encoded).",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class DigestBlake2bVerificationKey(RootModel):
    root: constr(min_length=56) = Field(
        ...,
        description="A Blake2b 28-byte digest of an Ed25519 verification key.",
        examples=["90181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d3"],
    )


class DigestBlake2bVrfVerificationKey(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ...,
        description="A Blake2b 32-byte digest of a VRF verification key.",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class HeaderHash(RootModel):
    root: DigestBlake2bBlockHeader


class Nonce(RootModel):
    root: NonceEnum | DigestBlake2bNonce


class DlgPayload(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ...,
        description="A Blake2b 32-byte digest of a Byron delegation payload, CBOR-encoded.",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class Epoch(RootModel):
    root: conint(ge=0, le=18446744073709552000) = Field(
        ..., description="An epoch number or length."
    )


class ExecutionUnits(BaseModel):
    memory: UInt64
    cpu: UInt64


class GenesisVerificationKey(RootModel):
    root: constr(min_length=128, max_length=128) = Field(
        ...,
        description="An Ed25519-BIP32 Byron genesis delegate verification key with chain-code.",
    )


class IssuerVrfVerificationKey(RootModel):
    root: str = Field(..., description="A key identifying a block issuer.")


class IssuerSignature(RootModel):
    root: str = Field(
        ...,
        description="Signature proving a block was issued by a given issuer VRF key.",
    )


class Int64(RootModel):
    root: conint(ge=-9223372036854775808, le=9223372036854775807)


class KesVerificationKey(RootModel):
    root: str


class Lovelace(BaseModel):
    lovelace: int = Field(
        ..., description="A number of lovelace, possibly large when summed up."
    )


class LovelaceDelta(RootModel):
    root: conint(ge=-9223372036854775808, le=9223372036854775807) = Field(
        ...,
        description="An amount, possibly negative, in Lovelace (1e6 Lovelace = 1 Ada).",
    )


class MempoolSizeAndCapacity(BaseModel):
    capacity: UInt32
    currentSize: UInt32
    numberOfTxs: UInt32


class NetworkMagic(RootModel):
    root: conint(ge=0, le=4294967296) = Field(
        ...,
        description="A magic number for telling networks apart. (e.g. 764824073)",
        examples=[764824073],
    )


class NonMyopicMemberRewards(RootModel):
    root: Optional[Dict[str, Dict[str, confloat(ge=0.0)]]] = None


class Null(RootModel):
    root: None


class NullableRatio(RootModel):
    root: Ratio | Null


class NullableUInt64(RootModel):
    root: UInt64 | Null


class ProtocolMagicId(RootModel):
    root: conint(ge=0, le=4294967295) = Field(..., examples=[764824073])


class ProtocolVersion(BaseModel):
    major: UInt32
    minor: UInt32
    patch: Optional[UInt32] = None


class PoolId(RootModel):
    root: Annotated[
        str,
        Field(
            pattern=r"^pool1[0-9a-z]*$",
            description="A Blake2b 32-byte digest of a pool's verification key.",
            examples=[
                "pool1qqqqpanw9zc0rzh0yp247nzf2s35uvnsm7aaesfl2nnejaev0uc",
                "pool1qqqqqdk4zhsjuxxd8jyvwncf5eucfskz0xjjj64fdmlgj735lr9",
            ],
        ),
    ]


class QueryUnavailableInCurrentEra(RootModel):
    root: str = "QueryUnavailableInCurrentEra"


class Prices(BaseModel):
    memory: Ratio
    steps: Ratio


class ScriptExecutionPrices(BaseModel):
    memory: Ratio
    cpu: Ratio


class Ratio(RootModel):
    root: Annotated[
        str,
        Field(
            pattern=r"^-?[0-9]+/[0-9]+$",
            description="A ratio of two integers, to express exact fractions.",
            examples=["2/3", "7/8"],
        ),
    ]


class ProtocolParametersUpdate(BaseModel):
    network: Optional[Ratio] = None
    economic: Optional[Ratio] = None
    technical: Optional[Ratio] = None
    governance: Optional[Ratio] = None


class DelegateRepresentativeVotingThresholds(BaseModel):
    no_confidence: Optional[Ratio] = Field(None, alias="noConfidence")
    constitution: Optional[Ratio] = None
    constitutional_committee: Optional[ConstitutionalCommittee] = Field(
        None, alias="constitutionalCommittee"
    )
    hard_fork_initiation: Optional[Ratio] = Field(None, alias="hardForkInitiation")
    protocol_parameters_update: Optional[ProtocolParametersUpdate] = Field(
        None, alias="protocolParametersUpdate"
    )
    treasury_withdrawals: Optional[Ratio] = Field(None, alias="treasuryWithdrawals")


class Size(BaseModel):
    bytes: Int64


class Mandate(BaseModel):
    epoch: Epoch


class ConstitutionalCommitteeMember(BaseModel):
    id: DigestBlake2B224
    mandate: Mandate


class ConstitutionalCommittee(BaseModel):
    default: Optional[Ratio] = None
    state_of_no_confidence: Optional[Ratio] = Field(None, alias="stateOfNoConfidence")
    members: Optional[List[ConstitutionalCommitteeMember]]
    quorum: Optional[Ratio]


class StakePoolVotingThresholds(BaseModel):
    no_confidence: Optional[Ratio] = Field(None, alias="noConfidence")
    constitutional_committee: Optional[ConstitutionalCommittee] = Field(
        None, alias="constitutionalCommittee"
    )
    hard_fork_initiation: Optional[Ratio] = Field(None, alias="hardForkInitiation")


class Redeemer(BaseModel):
    redeemer: RedeemerData
    executionUnits: ExecutionUnits


class RedeemerData(RootModel):
    root: str = Field(..., description="Plutus data, CBOR-serialised.")


class RedeemerPointer(RootModel):
    root: Annotated[str, Field(pattern=r"^(spend|mint|certificate|withdrawal):[0-9]+$")]


class RelativeTime(BaseModel):
    seconds: int = Field(
        description="A time in seconds relative to another one (typically, system start or era start). Starting from v5.5.4, this can be a floating number. Before v5.5.4, the floating value would be rounded to the nearest second.",
    )


class Rewards(RootModel):
    root: Optional[Dict[str, LovelaceDelta]] = None


class RewardAccount(RootModel):
    root: Annotated[
        str,
        Field(
            pattern=r"^stake(_test)?1[0-9a-z]+$",
            description="A reward account, also known as 'stake address'.",
            examples=["stake1ux7pt9adw8z46tgqn2f8fvurrhk325gcm4mf75mkmmxpx6gae9mzv"],
        ),
    ]


class SoftwareVersion(BaseModel):
    appName: str
    number: UInt32


class StakeAddress(RootModel):
    root: Annotated[
        str,
        Field(
            pattern=r"^(stake|stake_test)1[0-9a-z]*$",
            description="A stake address (a.k.a reward account)",
            examples=["stake179kzq4qulejydh045yzxwk4ksx780khkl4gdve9kzwd9vjcek9u8h"],
        ),
    ]


class Signature(RootModel):
    root: str = Field(
        ...,
        description="A signature coming from an Ed25519 or Ed25519-BIP32 signing key.",
    )


class SoftForkRule(BaseModel):
    initThreshold: NullableRatio
    minThreshold: NullableRatio
    decrementThreshold: NullableRatio


class TxFeePolicy(BaseModel):
    coefficient: Ratio
    constant: float


class TxId(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ..., description="A Blake2b 32-byte digest of a transaction body, CBOR-encoded."
    )


class UInt32(RootModel):
    root: conint(ge=0, le=4294967295)


class UInt64(RootModel):
    root: conint(ge=0, le=18446744073709552999)


class UpdatePayload(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ...,
        description="A Blake2b 32-byte digest of a Byron update payload, CBOR-encoded.",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class UtcTime(RootModel):
    root: datetime


class Value(BaseModel):
    coins: Lovelace
    assets: Optional[Dict[str, AssetQuantity]] = None


class VerificationKey(RootModel):
    root: str = Field(..., description="An Ed25519 verification key.")


class VrfOutput(RootModel):
    root: str


class VrfProof(RootModel):
    root: str


class Withdrawals(RootModel):
    root: Optional[Dict[str, Lovelace]] = None


class WitnessHash(RootModel):
    root: constr(min_length=64, max_length=64) = Field(
        ...,
        description="A Blake2b 32-byte digest of a Byron transaction witness set, CBOR-encoded.",
        examples=["c248757d390181c517a5beadc9c3fe64bf821d3e889a963fc717003ec248757d"],
    )


class ScriptNative(RootModel):
    root: DigestBlake2bVerificationKey | Any | All | NOf | ExpiresAt | StartsAt = Field(
        ...,
        description="A phase-1 monetary script. Timelocks constraints are only supported since Allegra.",
        examples=[
            "3c07030e36bfff7cd2f004356ef320f3fe3c07030e7cd2f004356437",
            {
                "all": [
                    "ec09e5293d384637cd2f004356ef320f3fe3c07030e36bfffe67e2e2",
                    "3c07030e36bfff7cd2f004356ef320f3fe3c07030e7cd2f004356437",
                ]
            },
        ],
    )


class ScriptPlutus(RootModel):
    root: str = Field(
        ...,
        description="A phase-2 Plutus script; or said differently, a serialized Plutus-core program.",
    )


class All(BaseModel):
    all: List[ScriptNative]


class Any(BaseModel):
    any: List[ScriptNative]


class NOf(RootModel):
    root: Dict[str, List[ScriptNative]]


class ExpiresAt(BaseModel):
    expires_at: Slot


class StartsAt(BaseModel):
    starts_at: Slot


class Native(BaseModel):
    native: ScriptNative


class PlutusV1(BaseModel):
    plutus_v1: ScriptPlutus = Field(..., alias="plutus:v1")


class PlutusV2(BaseModel):
    plutus_v2: ScriptPlutus = Field(..., alias="plutus:v2")


Script = Native | PlutusV1 | PlutusV2


class PoolMetadata(BaseModel):
    hash: DigestBlake2bPoolMetadata
    url: AnyUrl


class PoolParameters(BaseModel):
    owners: Optional[List[DigestBlake2bVerificationKey]]
    cost: Lovelace
    margin: Ratio
    pledge: Lovelace
    vrf: Optional[DigestBlake2bVrfVerificationKey]
    metadata: Optional[Null | PoolMetadata]
    id: Optional[PoolId]
    relays: Optional[List[Relay]]
    rewardAccount: Optional[RewardAccount]


class OpCert(BaseModel):
    count: Optional[UInt64] = None
    sigma: Optional[Signature] = None
    kesPeriod: Optional[UInt64] = None
    hotVk: Optional[KesVerificationKey] = None


class ByAddress(BaseModel):
    ipv4: str | Null
    ipv6: str | Null
    port: conint(ge=0, le=65535) | Null


class ByName(BaseModel):
    hostname: str
    port: conint(ge=0, le=65535) | Null


Relay = ByAddress | ByName


class DlgCertificate(BaseModel):
    epoch: Epoch
    issuerVk: GenesisVerificationKey
    delegateVk: GenesisVerificationKey
    signature: IssuerSignature


class GenesisByron(BaseModel):
    era: Literal["byron"]
    genesisKeyHashes: List[DigestBlake2bVerificationKey]
    genesisDelegations: Dict[str, DlgCertificate]
    systemStart: UtcTime
    initialFunds: Dict[str, Lovelace]
    initialCoinOffering: Dict[str, Lovelace]
    securityParameter: UInt64
    networkMagic: NetworkMagic
    protocolParameters: ProtocolParametersByron


class GenesisAlonzo(BaseModel):
    era: Literal["alonzo"]
    coinsPerUtxoWord: UInt64
    collateralPercentage: UInt64
    costModels: CostModels
    maxCollateralInputs: NullableUInt64
    maxExecutionUnitsPerBlock: ExecutionUnits
    maxExecutionUnitsPerTransaction: ExecutionUnits
    maxValueSize: NullableUInt64
    prices: Prices


class GenesisDelegate(BaseModel):
    delegate: DigestBlake2bVerificationKey
    vrf: DigestBlake2bVrfVerificationKey


class GenesisShelley(BaseModel):
    era: Literal["shelley"]
    systemStart: UtcTime
    networkMagic: NetworkMagic
    network: Network
    activeSlotsCoefficient: Ratio
    securityParameter: UInt64
    epochLength: Epoch
    slotsPerKesPeriod: UInt64
    maxKesEvolutions: UInt64
    slotLength: SlotLength
    updateQuorum: UInt64
    maxLovelaceSupply: UInt64
    protocolParameters: ProtocolParametersShelley
    initialDelegates: Dict[str, GenesisDelegate] = Field(..., title="InitialDelegates")
    initialFunds: Dict[str, Lovelace] = Field(..., title="InitialFunds")
    initialPools: GenesisPools


class Anchor(BaseModel):
    hash: DigestAny
    url: str


class Constitution(BaseModel):
    hash: DigestBlake2B224
    anchor: Anchor


class UpdatableParameters(BaseModel):
    stakePoolVotingThresholds: StakePoolVotingThresholds
    constitutionalCommitteeMinSize: UInt64
    constitutionalCommitteeMaxTermLength: UInt64
    governanceActionLifetime: Epoch
    governanceActionDeposit: Lovelace
    delegateRepresentativeVotingThresholds: DelegateRepresentativeVotingThresholds
    delegateRepresentativeDeposit: Lovelace
    delegateRepresentativeMaxIdleTime: Epoch


class GenesisConway(BaseModel):
    era: Literal["conway"]
    constitution: Constitution
    constitutional_committee: ConstitutionalCommittee = Field(
        ..., alias="constitutionalCommittee"
    )
    updatable_parameters: UpdatableParameters = Field(..., alias="updatableParameters")


class GenesisPools(BaseModel):
    pools: Dict[str, PoolParameters]
    delegators: Dict[str, PoolId]


class ProtocolParametersAlonzo(BaseModel):
    minFeeCoefficient: NullableUInt64
    minFeeConstant: NullableUInt64
    maxBlockBodySize: NullableUInt64
    maxBlockHeaderSize: NullableUInt64
    maxTxSize: NullableUInt64
    stakeKeyDeposit: NullableUInt64
    poolDeposit: NullableUInt64
    poolRetirementEpochBound: NullableUInt64
    desiredNumberOfPools: NullableUInt64
    poolInfluence: NullableRatio
    monetaryExpansion: NullableRatio
    treasuryExpansion: NullableRatio
    decentralizationParameter: NullableRatio
    minPoolCost: NullableUInt64
    coinsPerUtxoWord: NullableUInt64
    maxValueSize: NullableUInt64
    collateralPercentage: NullableUInt64
    maxCollateralInputs: NullableUInt64
    extraEntropy: Nonce | Null
    protocolVersion: ProtocolVersion | Null
    costModels: CostModels | Null
    prices: Prices | Null
    maxExecutionUnitsPerTransaction: ExecutionUnits | Null
    maxExecutionUnitsPerBlock: ExecutionUnits | Null


class ProtocolParametersBabbage(BaseModel):
    minFeeCoefficient: NullableUInt64
    minFeeConstant: NullableUInt64
    maxBlockBodySize: NullableUInt64
    maxBlockHeaderSize: NullableUInt64
    maxTxSize: NullableUInt64
    stakeKeyDeposit: NullableUInt64
    poolDeposit: NullableUInt64
    poolRetirementEpochBound: NullableUInt64
    desiredNumberOfPools: NullableUInt64
    poolInfluence: NullableRatio
    monetaryExpansion: NullableRatio
    treasuryExpansion: NullableRatio
    minPoolCost: NullableUInt64
    coinsPerUtxoByte: NullableUInt64
    maxValueSize: NullableUInt64
    collateralPercentage: NullableUInt64
    maxCollateralInputs: NullableUInt64
    protocolVersion: ProtocolVersion | Null
    costModels: CostModels | Null
    prices: Prices | Null
    maxExecutionUnitsPerTransaction: ExecutionUnits | Null
    maxExecutionUnitsPerBlock: ExecutionUnits | Null


class ProtocolParametersByron(BaseModel):
    heavyDlgThreshold: NullableRatio
    maxBlockSize: NullableUInt64
    maxHeaderSize: NullableUInt64
    maxProposalSize: NullableUInt64
    maxTxSize: NullableUInt64
    mpcThreshold: NullableRatio
    scriptVersion: NullableUInt64
    slotDuration: NullableUInt64
    unlockStakeEpoch: NullableUInt64
    updateProposalThreshold: NullableRatio
    updateProposalTimeToLive: NullableUInt64
    updateVoteThreshold: NullableRatio
    txFeePolicy: TxFeePolicy | Null
    softforkRule: SoftForkRule | Null


class ProtocolParametersShelley(BaseModel):
    minFeeCoefficient: NullableUInt64
    minFeeConstant: NullableUInt64
    maxBlockBodySize: NullableUInt64
    maxBlockHeaderSize: NullableUInt64
    maxTxSize: NullableUInt64
    stakeKeyDeposit: NullableUInt64
    poolDeposit: NullableUInt64
    poolRetirementEpochBound: NullableUInt64
    desiredNumberOfPools: NullableUInt64
    poolInfluence: NullableRatio
    monetaryExpansion: NullableRatio
    treasuryExpansion: NullableRatio
    decentralizationParameter: NullableRatio
    minUtxoValue: NullableUInt64
    minPoolCost: NullableUInt64
    extraEntropy: Nonce | Null
    protocolVersion: ProtocolVersion | Null


class ProtocolParameters(BaseModel):
    min_fee_coefficient: Optional[NullableUInt64] = Field(
        None, alias="minFeeCoefficient"
    )
    min_fee_constant: Optional[Lovelace] = Field(None, alias="minFeeConstant")
    min_utxo_deposit_coefficient: Optional[NullableUInt64] = Field(
        None, alias="minUtxoDepositCoefficient"
    )
    min_utxo_deposit_constant: Optional[Lovelace | int] = Field(
        None, alias="minUtxoDepositConstant"
    )
    max_block_body_size: Optional[Size] = Field(None, alias="maxBlockBodySize")
    max_block_header_size: Optional[Size] = Field(None, alias="maxBlockHeaderSize")
    max_transaction_size: Optional[Size] = Field(None, alias="maxTransactionSize")
    max_value_size: Optional[Size] = Field(None, alias="maxValueSize")
    extra_entropy: Optional[Nonce] = Field(None, alias="extraEntropy")
    stake_credential_deposit: Optional[Lovelace] = Field(
        None, alias="stakeCredentialDeposit"
    )
    stake_pool_deposit: Optional[Lovelace] = Field(None, alias="stakePoolDeposit")
    stake_pool_retirement_epoch_bound: Optional[NullableUInt64] = Field(
        None, alias="stakePoolRetirementEpochBound"
    )
    stake_pool_pledge_influence: Optional[NullableRatio] = Field(
        None, alias="stakePoolPledgeInfluence"
    )
    min_stake_pool_cost: Optional[Lovelace] = Field(None, alias="minStakePoolCost")
    desired_number_of_stake_pools: Optional[NullableUInt64] = Field(
        None, alias="desiredNumberOfStakePools"
    )
    federated_block_production_ratio: Optional[NullableRatio] = Field(
        None, alias="federatedBlockProductionRatio"
    )
    monetary_expansion: Optional[NullableRatio] = Field(None, alias="monetaryExpansion")
    treasury_expansion: Optional[NullableRatio] = Field(None, alias="treasuryExpansion")
    collateral_percentage: Optional[NullableUInt64] = Field(
        None, alias="collateralPercentage"
    )
    max_collateral_inputs: Optional[NullableUInt64] = Field(
        None, alias="maxCollateralInputs"
    )
    plutus_cost_models: Optional[CostModels] = Field(None, alias="plutusCostModels")
    script_execution_prices: Optional[ScriptExecutionPrices] = Field(
        None, alias="scriptExecutionPrices"
    )
    max_execution_units_per_transaction: Optional[ExecutionUnits] = Field(
        None, alias="maxExecutionUnitsPerTransaction"
    )
    max_execution_units_per_block: Optional[ExecutionUnits] = Field(
        None, alias="maxExecutionUnitsPerBlock"
    )
    stake_pool_voting_thresholds: Optional[StakePoolVotingThresholds] = Field(
        None, alias="stakePoolVotingThresholds"
    )
    constitutional_committee_min_size: Optional[NullableUInt64] = Field(
        None, alias="constitutionalCommitteeMinSize"
    )
    constitutional_committee_max_term_length: Optional[NullableUInt64] = Field(
        None, alias="constitutionalCommitteeMaxTermLength"
    )
    governance_action_lifetime: Optional[Epoch] = Field(
        None, alias="governanceActionLifetime"
    )
    governance_action_deposit: Optional[Lovelace] = Field(
        None, alias="governanceActionDeposit"
    )
    delegate_representative_voting_thresholds: Optional[
        DelegateRepresentativeVotingThresholds
    ] = Field(None, alias="delegateRepresentativeVotingThresholds")
    delegate_representative_deposit: Optional[Lovelace] = Field(
        None, alias="delegateRepresentativeDeposit"
    )
    delegate_representative_max_idle_time: Optional[Epoch] = Field(
        None, alias="delegateRepresentativeMaxIdleTime"
    )
    version: Optional[ProtocolVersion] = None


class Allegra(BaseModel):
    allegra: BlockAllegra
    block_type: Literal["allegra"]


class Alonzo(BaseModel):
    alonzo: BlockAlonzo
    block_type: Literal["alonzo"]


class AuxiliaryData(BaseModel):
    hash: DigestBlake2bAuxiliaryDataBody
    body: AuxiliaryDataBody


class AuxiliaryDataBody(BaseModel):
    blob: Optional[Dict[str, Metadatum]] = None
    scripts: Optional[List[Script]] = None


class Babbage(BaseModel):
    babbage: BlockBabbage
    block_type: Literal["babbage"]


class BlockAllegra(BaseModel):
    body: List[TxAllegra]
    headerHash: HeaderHash
    header: Header


class BlockAlonzo(BaseModel):
    body: List[TxAlonzo]
    headerHash: HeaderHash
    header: Header


class BlockBabbage(BaseModel):
    body: List[TxBabbage]
    headerHash: DigestBlake2bBlockHeader
    header: Header


class BlockMary(BaseModel):
    body: List[TxMary]
    headerHash: HeaderHash
    header: Header


class BlockProof(BaseModel):
    utxo: Utxo
    delegation: DlgPayload
    update: UpdatePayload


class BlockShelley(BaseModel):
    body: List[TxShelley]
    headerHash: DigestBlake2bBlockHeader
    header: Header


class BlockSignature(BaseModel):
    dlgCertificate: DlgCertificate
    signature: IssuerSignature


class Byron(BaseModel):
    byron: BlockByron
    block_type: Literal["byron"]


class EpochBoundaryBlock(BaseModel):
    hash: DigestBlake2bBlockHeader
    header: EpochBoundaryBlockHeader


class EpochBoundaryBlockHeader(BaseModel):
    blockHeight: BlockNo
    epoch: Epoch
    prevHash: DigestBlake2bBlockHeader


class Header(BaseModel):
    blockHeight: BlockNo
    slot: Slot
    prevHash: DigestBlake2bBlockHeader
    issuerVk: VerificationKey
    issuerVrf: IssuerVrfVerificationKey
    blockSize: BlockSize
    blockHash: DigestBlake2bBlockBody
    opCert: OpCert
    protocolVersion: ProtocolVersion
    signature: IssuerSignature
    vrfInput: Optional[CertifiedVrf] = None


class Vote(BaseModel):
    voterVk: VerificationKey
    proposalId: DigestBlake2bVerificationKey
    signature: Signature


class Mary(BaseModel):
    mary: BlockMary
    block_type: Literal["mary"]


class Point(BaseModel):
    slot: Slot
    id: DigestBlake2bBlockHeader


class RedeemWitness(BaseModel):
    key: VerificationKey
    signature: Signature


class RollBackward(BaseModel):
    point: PointOrOrigin
    tip: TipOrOrigin


class RollForward(BaseModel):
    block: Block
    tip: TipOrOrigin


class Shelley(BaseModel):
    shelley: BlockShelley
    block_type: Literal["shelley"]


class StandardBlock(BaseModel):
    hash: DigestBlake2bBlockHeader
    header: StandardBlockHeader
    body: StandardBlockBody


class StandardBlockBodyUpdatePayload(BaseModel):
    proposal: Optional[Union[Null, UpdateProposalByron]]
    votes: List[Vote]


class StandardBlockBody(BaseModel):
    txPayload: List[TxByron]
    dlgPayload: List[DlgCertificate]
    updatePayload: StandardBlockBodyUpdatePayload


class StandardBlockHeader(BaseModel):
    blockHeight: BlockNo
    genesisKey: GenesisVerificationKey
    prevHash: DigestBlake2bBlockHeader
    proof: BlockProof
    protocolMagicId: ProtocolMagicId
    protocolVersion: ProtocolVersion
    signature: BlockSignature
    slot: Slot
    softwareVersion: SoftwareVersion


class Tip(BaseModel):
    slot: Slot
    hash: DigestBlake2bBlockHeader
    blockNo: BlockNo


class TxAllegra(BaseModel):
    id: DigestBlake2bBlockBody
    body: TxAllegraBody
    witness: Witness
    metadata: Union[AuxiliaryData, Null]
    raw: str = Field(
        ..., description="The raw serialized transaction, as found on-chain."
    )


class TxAllegraBody(BaseModel):
    inputs: List[TxIn]
    outputs: List[TxOut]
    certificates: List[Certificate]
    withdrawals: Withdrawals
    fee: Lovelace
    validityInterval: ValidityInterval
    update: UpdateShelley


class TxAlonzo(BaseModel):
    id: DigestBlake2bBlockBody
    inputSource: InputSource
    body: TxAlonzoBody
    witness: Witness
    metadata: Union[AuxiliaryData, Null]
    raw: str = Field(
        ..., description="The raw serialized transaction, as found on-chain."
    )


class TxAlonzoBody(BaseModel):
    inputs: List[TxIn]
    collaterals: List[TxIn]
    outputs: List[TxOut]
    certificates: List[Certificate]
    withdrawals: Withdrawals
    fee: Lovelace
    validityInterval: ValidityInterval
    update: UpdateAlonzo
    mint: Value
    network: Union[Network, Null]
    scriptIntegrityHash: Union[DigestBlake2bScriptIntegrity, Null]
    requiredExtraSignatures: List[DigestBlake2bVerificationKey]


class TxBabbage(BaseModel):
    id: DigestBlake2bBlockBody
    inputSource: InputSource
    body: TxBabbageBody
    witness: Witness
    metadata: Union[AuxiliaryData, Null]
    raw: str = Field(
        ..., description="The raw serialized transaction, as found on-chain."
    )


class TxBabbageBody(BaseModel):
    inputs: List[TxIn]
    references: List[TxIn]
    collaterals: List[TxIn]
    collateralReturn: Union[TxOut, Null]
    totalCollateral: Union[Lovelace, Null]
    outputs: List[TxOut]
    certificates: List[Certificate]
    withdrawals: Withdrawals
    fee: Lovelace
    validityInterval: ValidityInterval
    update: UpdateBabbage
    mint: Value
    network: Union[Network, Null]
    scriptIntegrityHash: Union[DigestBlake2bScriptIntegrity, Null]
    requiredExtraSignatures: List[DigestBlake2bVerificationKey]


class TxByron(BaseModel):
    id: TxId
    body: TxByronBody
    witness: List[TxWitness]
    raw: str = Field(
        ..., description="The raw serialized transaction, as found on-chain."
    )


class TxByronBody(BaseModel):
    inputs: List[TxIn]
    outputs: List[TxOut]


class TxIn(BaseModel):
    txId: TxId
    index: UInt32


class TxMary(BaseModel):
    id: DigestBlake2bBlockBody
    body: TxMaryBody
    witness: Witness
    metadata: Union[AuxiliaryData, Null]
    raw: str = Field(
        ..., description="The raw serialized transaction, as found on-chain."
    )


class TxMaryBody(BaseModel):
    inputs: List[TxIn]
    outputs: List[TxOut]
    certificates: List[Certificate]
    withdrawals: Withdrawals
    fee: Lovelace
    validityInterval: ValidityInterval
    update: UpdateShelley
    mint: Value


class TxOut(BaseModel):
    address: Address
    value: Value
    datumHash: Optional[Union[DigestBlake2bDatum, Null]] = None
    datum: Optional[Union[Any, Datum, Null]] = None
    script: Optional[Union[Script, Null]] = None


class TxRedeemWitness(BaseModel):
    redeemWitness: RedeemWitness


class TxShelley(BaseModel):
    id: DigestBlake2bBlockBody
    body: TxShellyBody
    witness: Witness
    metadata: Union[AuxiliaryData, Null]
    raw: str = Field(
        ..., description="The raw serialized transaction, as found on-chain."
    )


class TxShellyBody(BaseModel):
    inputs: List[TxIn]
    outputs: List[TxOut]
    certificates: List[Certificate]
    withdrawals: Withdrawals
    fee: Lovelace
    timeToLive: Slot
    update: UpdateShelley


class TxWitnessVk(BaseModel):
    witnessVk: WitnessVk


class UpdateProposalAlonzo(BaseModel):
    epoch: Epoch
    proposal: Dict[str, ProtocolParametersAlonzo]


class UpdateProposalBabbage(BaseModel):
    epoch: Epoch
    proposal: Dict[str, ProtocolParametersBabbage]


class UpdateProposalShelley(BaseModel):
    epoch: Epoch
    proposal: Dict[str, ProtocolParametersShelley]


class UpdateProposalByronBody(BaseModel):
    protocolVersion: ProtocolVersion
    softwareVersion: SoftwareVersion
    metadata: Dict[str, str]
    parametersUpdate: ProtocolParametersByron


class UpdateProposalByron(BaseModel):
    body: UpdateProposalByronBody
    issuer: IssuerVrfVerificationKey
    signature: IssuerSignature


class Utxo(BaseModel):
    number: UInt32
    root: DigestBlake2bMerkleRoot
    witnessesHash: WitnessHash


class ValidityInterval(BaseModel):
    invalidBefore: Union[Slot, Null]
    invalidHereafter: Union[Slot, Null]


class WitnessVk(BaseModel):
    key: DigestBlake2bVerificationKey
    signature: Signature


class BootstrapWitness(BaseModel):
    signature: Signature
    chainCode: Union[ChainCode, Null]
    addressAttributes: Union[AddressAttributes, Null]
    key: VerificationKey


class Witness(BaseModel):
    signatures: Dict[str, Signature]
    scripts: Optional[Dict[str, Script]]
    bootstrap: Optional[List[BootstrapWitness]]
    datums: Optional[Dict[str, Datum]]
    redeemers: Optional[Dict[str, Redeemer]]


Block = Union[Babbage, Alonzo, Mary, Allegra, Shelley, Byron]

BlockByron = Union[StandardBlock, EpochBoundaryBlock]

PointOrOrigin = Union[Point, Origin]

TipOrOrigin = Union[Tip, Origin]

TxWitness = Union[TxWitnessVk, TxRedeemWitness]

UpdateAlonzo = Union[Null, UpdateProposalAlonzo]

UpdateBabbage = Union[Null, UpdateProposalBabbage]

UpdateShelley = Union[Null, UpdateProposalShelley]


class SubmitTxErrorMissingVkWitnesses(BaseModel):
    missingVkWitnesses: List[DigestBlake2bVerificationKey]


class SubmitTxErrorMissingScriptWitnesses(BaseModel):
    missingScriptWitnesses: List[DigestBlake2bScript]


class SubmitTxErrorScriptWitnessNotValidating(BaseModel):
    scriptWitnessNotValidating: List[DigestBlake2bScript]


class SubmitTxErrorInsufficientGenesisSignatures(BaseModel):
    insufficientGenesisSignatures: List[DigestBlake2bVerificationKey]


class SubmitTxErrorMissingTxMetadata(BaseModel):
    missingTxMetadata: DigestBlake2bAuxiliaryDataBody


class SubmitTxErrorMissingTxMetadataHash(BaseModel):
    missingTxMetadataHash: DigestBlake2bAuxiliaryDataBody


class TxMetadataHashMismatch(BaseModel):
    includedHash: DigestBlake2bAuxiliaryDataBody
    expectedHash: DigestBlake2bAuxiliaryDataBody


class SubmitTxErrorTxMetadataHashMismatch(BaseModel):
    txMetadataHashMismatch: TxMetadataHashMismatch


class ExpiredUtxo(BaseModel):
    currentSlot: Slot
    transactionTimeToLive: Slot


class SubmitTxErrorExpiredUtxo(BaseModel):
    expiredUtxo: ExpiredUtxo


class TxTooLarge(BaseModel):
    maximumSize: Int64
    actualSize: Int64


class SubmitTxErrorTxTooLarge(BaseModel):
    txTooLarge: TxTooLarge


class SubmitTxErrorMissingAtLeastOneInputUtxo(BaseModel):
    missingAtLeastOneInputUtxo: None


class SubmitTxErrorInvalidMetadata(BaseModel):
    invalidMetadata: None


class FeeTooSmall(BaseModel):
    requiredFee: Lovelace
    actualFee: Lovelace


class SubmitTxErrorFeeTooSmall(BaseModel):
    feeTooSmall: FeeTooSmall


class SubmitTxErrorAddressAttributesTooLarge(BaseModel):
    addressAttributesTooLarge: List[Address]


class SubmitTxErrorTriesToForgeAda(BaseModel):
    triesToForgeAda: None


class SubmitTxErrorDelegateNotRegistered(BaseModel):
    delegateNotRegistered: PoolId


class SubmitTxErrorUnknownOrIncompleteWithdrawals(BaseModel):
    unknownOrIncompleteWithdrawals: Withdrawals


class SubmitTxErrorStakePoolNotRegistered(BaseModel):
    stakePoolNotRegistered: PoolId


class WrongRetirementEpoch(BaseModel):
    currentEpoch: Epoch
    requestedEpoch: Epoch
    firstUnreachableEpoch: Epoch


class SubmitTxErrorWrongRetirementEpoch(BaseModel):
    wrongRetirementEpoch: WrongRetirementEpoch


class UInt8(RootModel):
    root: conint(ge=0, le=255)


class SubmitTxErrorStakeKeyAlreadyRegistered(BaseModel):
    stakeKeyAlreadyRegistered: DigestBlake2bVerificationKey


class PolicyId(RootModel):
    root: DigestBlake2bScript


class PoolCostTooSmall(BaseModel):
    minimumCost: Lovelace


class SubmitTxErrorPoolCostTooSmall(BaseModel):
    poolCostTooSmall: PoolCostTooSmall


class PoolMetadataHashTooBig(BaseModel):
    poolId: PoolId
    measuredSize: Int64


class SubmitTxErrorPoolMetadataHashTooBig(BaseModel):
    poolMetadataHashTooBig: PoolMetadataHashTooBig


class SubmitTxErrorStakeKeyNotRegistered(BaseModel):
    stakeKeyNotRegistered: DigestBlake2bVerificationKey


class SubmitTxErrorRewardAccountNotExisting(BaseModel):
    rewardAccountNotExisting: None


class RewardAccountNotEmpty(BaseModel):
    balance: Lovelace


class SubmitTxErrorRewardAccountNotEmpty(BaseModel):
    rewardAccountNotEmpty: RewardAccountNotEmpty


class SubmitTxErrorWrongCertificateType(BaseModel):
    wrongCertificateType: None


class SubmitTxErrorUnknownGenesisKey(BaseModel):
    unknownGenesisKey: DigestBlake2bVerificationKey


class SubmitTxErrorAlreadyDelegating(BaseModel):
    alreadyDelegating: DigestBlake2bVerificationKey


class InsufficientFundsForMir(BaseModel):
    rewardSource: RewardPot
    sourceSize: Lovelace
    requestedAmount: Lovelace


class SubmitTxErrorInsufficientFundsForMir(BaseModel):
    insufficientFundsForMir: InsufficientFundsForMir


class TooLateForMir(BaseModel):
    currentSlot: Slot
    lastAllowedSlot: Slot


class SubmitTxErrorTooLateForMir(BaseModel):
    tooLateForMir: TooLateForMir


class SubmitTxErrorMirTransferNotCurrentlyAllowed(BaseModel):
    mirTransferNotCurrentlyAllowed: None


class SubmitTxErrorMirNegativeTransferNotCurrentlyAllowed(BaseModel):
    mirNegativeTransferNotCurrentlyAllowed: None


class SubmitTxErrorMirProducesNegativeUpdate(BaseModel):
    mirProducesNegativeUpdate: None


class MirNegativeTransfer(BaseModel):
    rewardSource: RewardPot
    attemptedTransfer: Lovelace


class SubmitTxErrorMirNegativeTransfer(BaseModel):
    mirNegativeTransfer: MirNegativeTransfer


class SubmitTxErrorDuplicateGenesisVrf(BaseModel):
    duplicateGenesisVrf: DigestBlake2bVrfVerificationKey


class NonGenesisVoters(BaseModel):
    currentlyVoting: List[DigestBlake2bVerificationKey]
    shouldBeVoting: List[DigestBlake2bVerificationKey]


class SubmitTxErrorNonGenesisVoters(BaseModel):
    nonGenesisVoters: NonGenesisVoters


class VotingPeriod(Enum):
    voteForThisEpoch = "voteForThisEpoch"
    voteForNextEpoch = "voteForNextEpoch"


class SubmitTxErrorProtocolVersionCannotFollow(BaseModel):
    protocolVersionCannotFollow: ProtocolVersion


class MissingRequiredDatumsObject(BaseModel):
    provided: Optional[List[DigestBlake2bDatum]] = None
    missing: List[DigestBlake2bDatum]


class MissingRequiredDatums(BaseModel):
    missingRequiredDatums: MissingRequiredDatumsObject


class UnspendableDatums(BaseModel):
    nonSpendable: List[DigestBlake2bDatum]
    acceptable: List[DigestBlake2bDatum]


class SubmitTxErrorUnspendableDatums(BaseModel):
    unspendableDatums: UnspendableDatums


class ExtraDataMismatch(BaseModel):
    provided: Union[DigestBlake2bScriptIntegrity, Null]
    inferredFromParameters: Union[DigestBlake2bScriptIntegrity, Null]


class ScriptPurposeSpend(BaseModel):
    spend: TxIn


class ScriptPurposeMint(BaseModel):
    mint: PolicyId


class ScriptPurposeCertificate(BaseModel):
    certificate: Certificate


class ScriptPurposeWithdrawal(BaseModel):
    withdrawal: RewardAccount


class ScriptPurpose(RootModel):
    root: Union[
        ScriptPurposeSpend,
        ScriptPurposeMint,
        ScriptPurposeCertificate,
        ScriptPurposeWithdrawal,
    ]


class NoRedeemer(BaseModel):
    noRedeemer: ScriptPurpose


class NoWitness(BaseModel):
    noWitness: DigestBlake2bScript


class NoCostModel(BaseModel):
    noCostModel: Language


class BadTranslation(BaseModel):
    badTranslation: str = Field(
        ...,
        description="An (hopefully) informative error about the transaction execution failure.",
    )


class SubmitTxErrorCollectErrors(BaseModel):
    collectErrors: List[Union[NoRedeemer, NoWitness, NoCostModel, BadTranslation]]


class SubmitTxErrorExtraDataMismatch(BaseModel):
    extraDataMismatch: ExtraDataMismatch


class SubmitTxErrorMissingRequiredSignatures(BaseModel):
    missingRequiredSignatures: List[DigestBlake2bVerificationKey]


class SubmitTxErrorMissingCollateralInputs(BaseModel):
    missingCollateralInputs: None


class CollateralTooSmall(BaseModel):
    requiredCollateral: Lovelace
    actualCollateral: Lovelace


class SubmitTxErrorCollateralTooSmall(BaseModel):
    collateralTooSmall: CollateralTooSmall


class TooManyCollateralInputs(BaseModel):
    maximumCollateralInputs: UInt64
    actualCollateralInputs: UInt64


class SubmitTxErrorTooManyCollateralInputs(BaseModel):
    tooManyCollateralInputs: TooManyCollateralInputs


class SubmitTxErrorOutsideForecast(BaseModel):
    outsideForecast: Slot


class SubmitTxErrorValidationTagMismatch(BaseModel):
    validationTagMismatch: None


class SubmitTxErrorExtraScriptWitnesses(BaseModel):
    extraScriptWitnesses: List[DigestBlake2bScript]


class ExecutionUnitsTooLarge(BaseModel):
    maximumExecutionUnits: ExecutionUnits
    actualExecutionUnits: ExecutionUnits


class SubmitTxErrorExecutionUnitsTooLarge(BaseModel):
    executionUnitsTooLarge: ExecutionUnitsTooLarge


class SubmitTxErrorUnspendableScriptInputs(BaseModel):
    unspendableScriptInputs: List[TxIn]


class MissingRequiredRedeemers(BaseModel):
    missing: List[Dict[str, ScriptPurpose]]


class UpdateWrongEpoch(BaseModel):
    currentEpoch: Epoch
    requestedEpoch: Epoch
    votingPeriod: VotingPeriod


class SubmitTxErrorWrongPoolCertificate(BaseModel):
    wrongPoolCertificate: UInt8


class SubmitTxErrorUpdateWrongEpoch(BaseModel):
    updateWrongEpoch: UpdateWrongEpoch


class SubmitTxErrorMissingRequiredRedeemers(BaseModel):
    missingRequiredRedeemers: MissingRequiredRedeemers


class InvalidEntityAddress(BaseModel):
    type: InvalidEntityType = InvalidEntityType.ADDRESS
    entity: InvalidEntityEntity = InvalidEntityEntity.ADDRESS


class InvalidEntityPoolRegistration(BaseModel):
    type: InvalidEntityType = InvalidEntityType.POOL_REGISTRATION
    entity: InvalidEntityEntity = InvalidEntityEntity.POOL_REGISTRATION


class InvalidEntityRewardAccount(BaseModel):
    type: InvalidEntityType = InvalidEntityType.REWARD_ACCOUNT
    entity: InvalidEntityEntity = InvalidEntityEntity.REWARD_ACCOUNT


class InvalidEntity(RootModel):
    root: Union[
        InvalidEntityAddress, InvalidEntityPoolRegistration, InvalidEntityRewardAccount
    ]


class NetworkMismatch(BaseModel):
    expectedNetwork: Network
    invalidEntities: List[InvalidEntity]


class SubmitTxErrorNetworkMismatch(BaseModel):
    networkMismatch: NetworkMismatch


class OutputTooSmall(BaseModel):
    output: TxOut
    minimumRequiredValue: Lovelace


class SubmitTxErrorOutputTooSmall(BaseModel):
    outputTooSmall: List[Union[TxOut, OutputTooSmall]]


class SubmitTxErrorTooManyAssetsInOutput(BaseModel):
    tooManyAssetsInOutput: List[TxOut]


class ValueNotConserved(BaseModel):
    consumed: Union[LovelaceDelta, Value]
    produced: Union[LovelaceDelta, Value]


class SubmitTxErrorInvalidWitnesses(BaseModel):
    invalidWitnesses: List[VerificationKey]


class SubmitTxErrorBadInputs(BaseModel):
    badInputs: List[TxIn]


class OutsideOfValidityInterval(BaseModel):
    currentSlot: Slot
    interval: ValidityInterval


class SubmitTxErrorOutsideOfValidityInterval(BaseModel):
    outsideOfValidityInterval: OutsideOfValidityInterval


class SubmitTxErrorValueNotConserved(BaseModel):
    valueNotConserved: ValueNotConserved


class ExtraRedeemers(BaseModel):
    extraRedeemers: List[str]


class Era(Enum):
    Byron = "Byron"
    Shelley = "Shelley"
    Allegra = "Allegra"
    Mary = "Mary"
    Alonzo = "Alonzo"
    Babbage = "Babbage"


class EraMismatch(BaseModel):
    queryEra: Era
    ledgerEra: Era


class SubmitTxErrorEraMismatch(BaseModel):
    eraMismatch: EraMismatch


class SubmitTxErrorCollateralHasNonAdaAssets(BaseModel):
    collateralHasNonAdaAssets: Value


class SubmitTxErrorMissingDatumHashesForInputs(BaseModel):
    missingDatumHashesForInputs: List[TxIn]


class SubmitTxErrorCollateralIsScript(BaseModel):
    collateralIsScript: Utxo


class TotalCollateralMismatch(BaseModel):
    computedFromDelta: Lovelace
    declaredInField: Lovelace


class SubmitTxErrorTotalCollateralMismatch(BaseModel):
    totalCollateralMismatch: TotalCollateralMismatch


class SubmitTxErrorMalformedReferenceScripts(BaseModel):
    malformedReferenceScripts: List[DigestBlake2bScript]


class SubmitTxErrorMalformedScriptWitnesses(BaseModel):
    malformedScriptWitnesses: List[DigestBlake2bScript]


class Bound(BaseModel):
    time: RelativeTime
    slot: Slot
    epoch: Epoch


class EraSummary(BaseModel):
    start: Bound
    end: Optional[Bound]
    parameters: EraParameters


class SlotLength(BaseModel):
    milliseconds: int = Field(
        description="A slot length, in seconds. Starting from v5.5.4, this can be a floating number. Before v5.5.4, "
        "the floating value would be rounded to the nearest second.",
    )


class SafeZone(RootModel):
    root: conint(ge=0, le=18446744073709552999) = Field(
        description="Number of slots from the tip of the ledger in which it is guaranteed that no hard fork can take "
        "place. This should be (at least) the number of slots in which we are guaranteed to have k blocks.",
    )


class EraParameters(BaseModel):
    epoch_length: Epoch = Field(alias="epochLength")
    slot_length: SlotLength = Field(alias="slotLength")
    safe_zone: Optional[SafeZone] = Field(alias="safeZone")


class PoolRank(BaseModel):
    score: float
    estimatedHitRate: float


class PoolsRanking(RootModel):
    root: Optional[Dict[str, PoolRank]] = None


GenesisConfig = GenesisByron | GenesisShelley | GenesisAlonzo | GenesisConway


class RewardInfoPool(BaseModel):
    stake: Lovelace
    ownerStake: Lovelace = Field(
        ...,
        description="The number of Lovelace owned by the stake pool owners. If this value is not at least as large as the 'pledgeRatio', the stake pool will not earn any rewards for the given epoch.",
    )
    approximatePerformance: confloat(ge=0.0) = Field(
        ...,
        description="Number of blocks produced divided by expected number of blocks (based on stake and epoch progress). Can be larger than 1.0 for pools that get lucky.",
    )
    poolParameters: PoolParameters = Field(
        ...,
        description="Some of the pool parameters relevant for the reward calculation.",
    )


class IndividualPoolRewardsProvenance(BaseModel):
    totalMintedBlocks: UInt64 = Field(
        ..., description="The number of blocks the pool produced."
    )
    totalStakeShare: Ratio = Field(
        ..., description="The stake pool's stake share (portion of the total stake)."
    )
    activeStakeShare: Ratio = Field(
        ...,
        description="The stake pool's active stake share (portion of the active stake).",
    )
    ownerStake: Lovelace = Field(
        ...,
        description="The number of Lovelace owned by the stake pool owners. If this value is not at least as large as the 'pledgeRatio', the stake pool will not earn any rewards for the given epoch.",
    )
    parameters: PoolParameters
    pledgeRatio: Ratio = Field(
        ..., description="The stake pool's pledge ratio (over its total stake)."
    )
    maxRewards: Lovelace = Field(
        ..., description="The maximum number of Lovelace this stake pool can earn."
    )
    apparentPerformance: Ratio = Field(
        ...,
        description="The stake pool's apparent performance according to Section 5.5.2 of the Shelley Design Spec.",
    )
    totalRewards: Lovelace = Field(
        ..., description="The total Lovelace earned by the stake pool."
    )
    leaderRewards: Lovelace = Field(
        ..., description="The total Lovelace earned by the stake pool leader."
    )


class RewardsProvenance(BaseModel):
    epochLength: Epoch
    decentralizationParameter: Ratio
    maxLovelaceSupply: Lovelace
    mintedBlocks: Dict[str, UInt64] = Field(
        ..., description="Number of blocks minted by each pool."
    )
    totalMintedBlocks: Int64 = Field(
        ..., description="The total number of blocks minted during the given epoch."
    )
    totalExpectedBlocks: Int64 = Field(
        ...,
        description="The number of blocks expected to be produced during the given epoch.",
    )
    incentive: Lovelace = Field(
        ...,
        description="The maximum amount of Lovelace which can be removed from the reserves to be given out as rewards for the given epoch.",
    )
    rewardsGap: Lovelace = Field(
        ...,
        description="The difference between the 'availableRewards' and what was actually distributed.",
    )
    availableRewards: Lovelace = Field(
        ...,
        description="The total Lovelace available for rewards for the given epoch, equal to 'totalRewards' less 'treasuryTax'.",
    )
    totalRewards: Lovelace = Field(
        ...,
        description="The reward pot for the given epoch, equal to the 'incentive' plus the fee pot.",
    )
    treasuryTax: Lovelace = Field(
        ...,
        description="The amount of Lovelace taken for the treasury for the given epoch.",
    )
    activeStake: Lovelace = Field(
        ...,
        description="The amount of Lovelace that is delegated during the given epoch.",
    )
    pools: Dict[str, IndividualPoolRewardsProvenance]


class RewardsProvenanceNew(BaseModel):
    desiredNumberOfPools: conint(ge=0, le=18446744073709552999) = Field(
        ..., description="Desired number of stake pools."
    )
    poolInfluence: Annotated[
        str,
        Field(
            pattern=r"^-?[0-9]+/[0-9]+$",
            description="Influence of the pool owner's pledge on rewards, "
            "as a ratio of two integers.",
            examples=["2/3", "7/8"],
        ),
    ]
    totalRewards: int = Field(
        ..., description="Total rewards available for the given epoch."
    )
    activeStake: int = Field(
        ..., description="The total amount of staked Lovelace during this epoch."
    )
    pools: Dict[str, RewardInfoPool]


class PoolDistribution(BaseModel):
    stake: Ratio
    vrf: DigestBlake2bVrfVerificationKey


class PoolDistributions(RootModel):
    root: Optional[Dict[str, PoolDistribution]] = None


class EvaluationResult(BaseModel):
    EvaluationResult: Dict[str, ExecutionUnits]


class MissingRequiredScripts(BaseModel):
    missing: List[RedeemerPointer]
    resolved: Dict[str, DigestBlake2bScript]


class ScriptFailureMissingRequiredScripts(BaseModel):
    missingRequiredScripts: MissingRequiredScripts


class ValidatorFailed(BaseModel):
    error: str
    traces: List[str]


class ValidatorFailedError(BaseModel):
    validatorFailed: ValidatorFailed


class NoCostModelForLanguage(BaseModel):
    noCostModelForLanguage: Language


class UnknownInputReferencedByRedeemer(BaseModel):
    unknownInputReferencedByRedeemer: TxIn


class NonScriptInputReferencedByRedeemer(BaseModel):
    nonScriptInputReferencedByRedeemer: TxIn


class IllFormedExecutionBudget(BaseModel):
    illFormedExecutionBudget: Union[ExecutionUnits, Null]


class ScriptFailure(RootModel):
    root: List[
        Union[
            ExtraRedeemers,
            MissingRequiredDatums,
            ScriptFailureMissingRequiredScripts,
            ValidatorFailedError,
            UnknownInputReferencedByRedeemer,
            NonScriptInputReferencedByRedeemer,
            IllFormedExecutionBudget,
            NoCostModelForLanguage,
        ]
    ] = Field(
        ..., description="Errors which may occur when evaluating an on-chain script."
    )


class EvaluationFailureScriptFailures(BaseModel):
    ScriptFailures: Dict[str, ScriptFailure]


class EvaluationFailureIncompatibleEra(BaseModel):
    IncompatibleEra: IncompatibleEraEnum = Field(
        ..., description="The era in which the transaction has been identified."
    )


class EvaluationFailureAdditionalUtxoOverlap(BaseModel):
    AdditionalUtxoOverlap: List[TxIn]


class EvaluationFailureNotEnoughSynced(BaseModel):
    NotEnoughSynced: NotEnoughSynced


class CannotCreateEvaluationContext(BaseModel):
    reason: str


class EvaluationFailureCannotCreateEvaluationContext(BaseModel):
    CannotCreateEvaluationContext: CannotCreateEvaluationContext


class EvaluationFailure(BaseModel):
    EvaluationFailure: Union[
        EvaluationFailureScriptFailures,
        EvaluationFailureIncompatibleEra,
        EvaluationFailureAdditionalUtxoOverlap,
        EvaluationFailureNotEnoughSynced,
        EvaluationFailureCannotCreateEvaluationContext,
    ]


Base16 = str
"""A stake key or script hash in base16."""

Bech32 = str
"""A Blake2b 28-byte hash digest of a verification key or script."""

AnyStakeCredential = Base16 | Bech32 | StakeAddress

AuxiliaryData.model_rebuild()
AuxiliaryDataBody.model_rebuild()
BlockAllegra.model_rebuild()
BlockAlonzo.model_rebuild()
BlockBabbage.model_rebuild()
BlockMary.model_rebuild()
BlockProof.model_rebuild()
BlockShelley.model_rebuild()
Byron.model_rebuild()
CostModel.model_rebuild()
RewardAccountSummary.model_rebuild()
RewardAccountSummaries.model_rebuild()
EpochBoundaryBlock.model_rebuild()
EraSummary.model_rebuild()
ExecutionUnits.model_rebuild()
GenesisAlonzo.model_rebuild()
GenesisByron.model_rebuild()
GenesisShelley.model_rebuild()
NullableRatio.model_rebuild()
NullableUInt64.model_rebuild()
Prices.model_rebuild()
ProtocolVersion.model_rebuild()
RollForward.model_rebuild()
StandardBlock.model_rebuild()
StandardBlockBody.model_rebuild()
SoftwareVersion.model_rebuild()
StandardBlockBodyUpdatePayload.model_rebuild()
SubmitTxErrorCollateralIsScript.model_rebuild()
TxBabbage.model_rebuild()
TxByron.model_rebuild()
TxByronBody.model_rebuild()
TxOut.model_rebuild()
TxWitnessVk.model_rebuild()
Witness.model_rebuild()
