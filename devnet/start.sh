#!/usr/bin/env bash
# Start a fresh, fast, single-pool Cardano devnet with Ogmios, inside the cardano-node-ogmios image.
#
# Every start generates a new genesis, stake pool, DRep, committee member and funded UTxO keys with
# `cardano-cli conway genesis create-testnet-data`: nothing secret is committed, and every test run
# starts from the same clean state. The chain starts in Conway, with 0.1 s slots and 50 s epochs.
#
# Generated data (keys included) is written to /devnet, mounted from devnet/.state on the host so
# the tests can sign transactions with utxo-keys/utxo1/utxo.skey.
set -euo pipefail

DATA=/devnet
MAGIC=${DEVNET_MAGIC:-42}
SPEC=/tmp/spec

rm -rf "${DATA:?}"/* "$SPEC" /db
mkdir -p "$DATA" "$SPEC"

echo "devnet: generating a fast genesis"
# A first run gives the default specs; the Shelley spec is then tuned for a fast chain.
cardano-cli conway genesis create-testnet-data --testnet-magic "$MAGIC" --out-dir "$SPEC/defaults" > /dev/null
jq '.slotLength = 0.1
    | .activeSlotsCoeff = 0.5
    | .epochLength = 500
    | .securityParam = 10
    | .protocolParams.protocolVersion.major = 10' \
  "$SPEC/defaults/shelley-genesis.json" > "$SPEC/shelley.json"

cardano-cli conway genesis create-testnet-data \
  --spec-shelley "$SPEC/shelley.json" \
  --testnet-magic "$MAGIC" \
  --pools 1 \
  --stake-delegators 1 \
  --drep-keys 1 \
  --committee-keys 1 \
  --utxo-keys 2 \
  --total-supply 100000000000000 \
  --delegated-supply 50000000000000 \
  --start-time "$(date -u -d '+5 seconds' +%Y-%m-%dT%H:%M:%SZ)" \
  --out-dir "$DATA" > /dev/null

# The node configuration: the image's preview configuration, pointed at the new genesis files, with
# every hard fork at epoch 0 so the chain starts in Conway.
jq --arg byron "$(cardano-cli byron genesis print-genesis-hash --genesis-json "$DATA/byron-genesis.json")" \
   --arg shelley "$(cardano-cli conway genesis hash --genesis "$DATA/shelley-genesis.json")" \
   --arg alonzo "$(cardano-cli conway genesis hash --genesis "$DATA/alonzo-genesis.json")" \
   --arg conway "$(cardano-cli conway genesis hash --genesis "$DATA/conway-genesis.json")" \
   'del(.CheckpointsFile, .CheckpointsFileHash, .PeerSnapshotFile)
    | .ByronGenesisFile = "byron-genesis.json" | .ByronGenesisHash = $byron
    | .ShelleyGenesisFile = "shelley-genesis.json" | .ShelleyGenesisHash = $shelley
    | .AlonzoGenesisFile = "alonzo-genesis.json" | .AlonzoGenesisHash = $alonzo
    | .ConwayGenesisFile = "conway-genesis.json" | .ConwayGenesisHash = $conway
    | .TestShelleyHardForkAtEpoch = 0 | .TestAllegraHardForkAtEpoch = 0 | .TestMaryHardForkAtEpoch = 0
    | .TestAlonzoHardForkAtEpoch = 0 | .TestBabbageHardForkAtEpoch = 0 | .TestConwayHardForkAtEpoch = 0
    | .RequiresNetworkMagic = "RequiresMagic"
    | .ConsensusMode = "PraosMode"' \
  /opt/cardano/config/preview/config.json > "$DATA/config.json"
echo '{"localRoots": [], "publicRoots": [], "useLedgerAfterSlot": -1}' > "$DATA/topology.json"
# The host reads the generated keys (to sign test transactions); the node insists its pool keys are private.
chmod -R a+rX "$DATA"
chmod 600 "$DATA"/pools-keys/pool1/*.skey

echo "devnet: starting Ogmios and a block-producing node (testnet magic $MAGIC)"
ogmios --host 0.0.0.0 --node-config "$DATA/config.json" --node-socket /ipc/node.socket &

POOL="$DATA/pools-keys/pool1"
exec cardano-node run \
  --config "$DATA/config.json" \
  --topology "$DATA/topology.json" \
  --database-path /db \
  --socket-path /ipc/node.socket \
  --host-addr 0.0.0.0 \
  --port 3001 \
  --shelley-kes-key "$POOL/kes.skey" \
  --shelley-vrf-key "$POOL/vrf.skey" \
  --shelley-operational-certificate "$POOL/opcert.cert"
