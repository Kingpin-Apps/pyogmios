"""Helpers for tests against the local devnet: its keys, addresses and minimal signed transactions.

The devnet (``just devnet-up``) generates fresh keys on every start and writes them to
``devnet/.state``. These helpers read them and build the few transactions the tests need, by hand:
CBOR with cbor2, hashes with hashlib's BLAKE2b, signatures with PyNaCl.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cbor2
from nacl.signing import SigningKey

ROOT = Path(__file__).resolve().parents[1]
STATE = Path(os.environ.get("DEVNET_DIR", ROOT / "devnet" / ".state"))
URL = os.environ.get("DEVNET_OGMIOS_URL", "ws://localhost:1338")

_BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def blake2b(data: bytes, size: int) -> bytes:
    return hashlib.blake2b(data, digest_size=size).digest()


def bech32(hrp: str, data: bytes) -> str:
    """BIP-173 bech32 encoding, without the 90 character limit (Cardano addresses are longer)."""

    def polymod(values: list[int]) -> int:
        generator = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
        checksum = 1
        for value in values:
            top = checksum >> 25
            checksum = (checksum & 0x1FFFFFF) << 5 ^ value
            for i in range(5):
                checksum ^= generator[i] if (top >> i) & 1 else 0
        return checksum

    words, accumulator, bits = [], 0, 0
    for byte in data:
        accumulator, bits = (accumulator << 8) | byte, bits + 8
        while bits >= 5:
            bits -= 5
            words.append((accumulator >> bits) & 31)
    if bits:
        words.append((accumulator << (5 - bits)) & 31)
    expanded = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    checksum = polymod([*expanded, *words, 0, 0, 0, 0, 0, 0]) ^ 1
    words += [(checksum >> 5 * (5 - i)) & 31 for i in range(6)]
    return f"{hrp}1" + "".join(_BECH32[w] for w in words)


@dataclass
class Key:
    """An Ed25519 payment key and its enterprise address on a test network."""

    signing: SigningKey

    @classmethod
    def load(cls, path: Path) -> Key:
        cbor_hex = json.loads(path.read_text())["cborHex"]
        return cls(SigningKey(bytes.fromhex(cbor_hex)[2:]))  # 0x5820 + 32-byte seed

    @classmethod
    def generate(cls) -> Key:
        return cls(SigningKey.generate())

    @property
    def verification_key(self) -> bytes:
        return bytes(self.signing.verify_key)

    @property
    def key_hash(self) -> bytes:
        return blake2b(self.verification_key, 28)

    @property
    def address_bytes(self) -> bytes:
        return bytes([0x60]) + self.key_hash  # enterprise address, key hash, network id 0

    @property
    def address(self) -> str:
        return bech32("addr_test", self.address_bytes)


def funded_key(number: int = 1) -> Key:
    """One of the devnet's genesis UTxO keys, funded with 22.5 million test ada."""
    return Key.load(STATE / "utxo-keys" / f"utxo{number}" / "utxo.skey")


def signature_policy(key: Key) -> tuple[list[Any], bytes]:
    """A native script requiring ``key``'s signature, and its policy id."""
    script = [0, key.key_hash]
    return script, blake2b(b"\x00" + cbor2.dumps(script), 28)


@dataclass
class Transaction:
    """A Conway transaction with key-hash inputs, built and signed by hand."""

    inputs: list[tuple[str, int]]
    outputs: list[tuple[bytes, int, dict[bytes, dict[bytes, int]]]] = field(default_factory=list)
    fee: int = 0
    mint: dict[bytes, dict[bytes, int]] = field(default_factory=dict)
    native_scripts: list[list[Any]] = field(default_factory=list)

    def body(self) -> bytes:
        body: dict[int, Any] = {
            0: [[bytes.fromhex(tx_id), index] for tx_id, index in self.inputs],
            1: [
                [address, [coin, assets] if assets else coin]
                for address, coin, assets in self.outputs
            ],
            2: self.fee,
        }
        if self.mint:
            body[9] = self.mint
        return cbor2.dumps(body)

    @property
    def id(self) -> str:
        return blake2b(self.body(), 32).hex()

    def signed(self, *keys: Key) -> bytes:
        body = self.body()
        digest = blake2b(body, 32)
        witnesses: dict[int, Any] = {
            0: [[k.verification_key, k.signing.sign(digest).signature] for k in keys]
        }
        if self.native_scripts:
            witnesses[1] = self.native_scripts
        # The body's exact bytes are kept, so its hash (the transaction id) matches the signature.
        return b"\x84" + body + cbor2.dumps(witnesses) + b"\xf5\xf6"


def balance(
    transaction: Transaction, change_to: Key, available: int, parameters: Any, *keys: Key
) -> bytes:
    """Set the fee from the signed size (twice, as the fee's own size can change it) and add change."""
    coefficient = parameters.min_fee_coefficient
    constant = parameters.min_fee_constant.ada.lovelace
    spent = sum(coin for _, coin, _ in transaction.outputs)
    outputs = list(transaction.outputs)
    for _ in range(2):
        transaction.outputs = [
            *outputs,
            (change_to.address_bytes, available - spent - transaction.fee, {}),
        ]
        size = len(transaction.signed(*keys))
        transaction.fee = (
            coefficient * size + constant + 100
        )  # a small margin for the change's encoding
    transaction.outputs = [
        *outputs,
        (change_to.address_bytes, available - spent - transaction.fee, {}),
    ]
    return transaction.signed(*keys)
