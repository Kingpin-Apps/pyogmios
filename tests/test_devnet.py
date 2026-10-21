"""End to end against the local devnet: real, signed transactions (``just devnet-up``, ``just test-devnet``).

The devnet's genesis keys let these tests do what a public network cannot without spending someone's
funds: submit transactions that succeed, mint native tokens, and watch them reach a block.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

import pyogmios
from pyogmios import errors
from pyogmios.types import RollForward

from .devnet import STATE, URL, Key, Transaction, balance, funded_key, signature_policy

pytestmark = pytest.mark.devnet

ADA = 1_000_000


@pytest.fixture
async def client() -> Any:
    if not (STATE / "utxo-keys").is_dir():
        pytest.skip("no devnet state: run `just devnet-up`")
    ogmios = pyogmios.AsyncClient(URL, check_version="strict", reconnect=None)
    try:
        await ogmios.connect()
    except pyogmios.OgmiosConnectionError as error:
        pytest.skip(f"no devnet Ogmios at {URL}: {error}")
    async with ogmios:
        yield ogmios


async def largest_utxo(client: pyogmios.AsyncClient, key: Key) -> Any:
    utxos = await client.ledger_state.utxo(addresses=[key.address])
    assert utxos, f"no UTxO at {key.address}"
    return max(utxos, key=lambda utxo: utxo.value.ada.lovelace)


async def wait_for_block_with(client: pyogmios.AsyncClient, start: Any, transaction_id: str) -> Any:
    """Follow the chain from ``start`` until a block contains ``transaction_id``."""
    async with asyncio.timeout(60), client.chain_sync([start]) as sync:
        async for event in sync:
            if isinstance(event, RollForward):
                ids = [transaction.id for transaction in event.block.transactions or []]
                if transaction_id in ids:
                    return event.block
    raise AssertionError("unreachable")


async def test_the_devnet_is_conway_and_has_governance(client: pyogmios.AsyncClient) -> None:
    assert client.server_health is not None
    assert client.server_health.current_era == "conway"
    assert len(await client.ledger_state.stake_pools()) == 1
    committee = await client.ledger_state.constitutional_committee()
    assert committee is not None
    assert len(committee.members) == 1
    representatives = await client.ledger_state.delegate_representatives()
    assert any(getattr(drep, "type", None) == "registered" for drep in representatives)


async def test_a_signed_payment_reaches_a_block(client: pyogmios.AsyncClient) -> None:
    sender, receiver = funded_key(1), Key.generate()
    utxo = await largest_utxo(client, sender)
    parameters = await client.ledger_state.protocol_parameters()
    transaction = Transaction(
        inputs=[(utxo.transaction.id, utxo.index)],
        outputs=[(receiver.address_bytes, 10 * ADA, {})],
    )
    signed = balance(transaction, sender, utxo.value.ada.lovelace, parameters, sender)

    assert await client.evaluate_transaction(signed) == []  # no scripts to run
    tip = await client.network.tip()
    submitted = await client.submit_transaction(signed)
    assert submitted.transaction.id == transaction.id

    block = await wait_for_block_with(client, tip, transaction.id)
    in_block = next(t for t in block.transactions if t.id == transaction.id)
    assert in_block.fee.ada.lovelace == transaction.fee
    received = await client.ledger_state.utxo(addresses=[receiver.address])
    assert [(u.transaction.id, u.value.ada.lovelace) for u in received] == [
        (transaction.id, 10 * ADA)
    ]

    # Spending the same output again: rejected before or by the ledger, with a specific error.
    with pytest.raises(errors.SubmitTransactionError) as raised:
        await client.submit_transaction(signed)
    assert type(raised.value) is not errors.SubmitTransactionError
    assert raised.value.details is not None


async def test_minted_native_tokens_survive_the_round_trip(client: pyogmios.AsyncClient) -> None:
    """Mint tokens with a native script and read them back: Value must keep its asset policies."""
    minter, holder = funded_key(2), Key.generate()
    utxo = await largest_utxo(client, minter)
    parameters = await client.ledger_state.protocol_parameters()
    script, policy = signature_policy(minter)
    tokens = {b"PYOGMIOS": 1_000, b"\x00\x01": 7}
    transaction = Transaction(
        inputs=[(utxo.transaction.id, utxo.index)],
        outputs=[(holder.address_bytes, 5 * ADA, {policy: tokens})],
        mint={policy: tokens},
        native_scripts=[script],
    )
    signed = balance(transaction, minter, utxo.value.ada.lovelace, parameters, minter)
    tip = await client.network.tip()
    await client.submit_transaction(signed)
    block = await wait_for_block_with(client, tip, transaction.id)

    in_block = next(t for t in block.transactions if t.id == transaction.id)
    assert in_block.mint is not None
    (held,) = await client.ledger_state.utxo(addresses=[holder.address])
    value = held.model_dump(mode="json", by_alias=True)["value"]
    assert value == {
        "ada": {"lovelace": 5 * ADA},
        policy.hex(): {"50594f474d494f53": 1_000, "0001": 7},
    }


async def test_the_mempool_sees_a_submitted_transaction(client: pyogmios.AsyncClient) -> None:
    sender = funded_key(1)
    utxo = await largest_utxo(client, sender)
    parameters = await client.ledger_state.protocol_parameters()
    transaction = Transaction(
        inputs=[(utxo.transaction.id, utxo.index)],
        outputs=[(Key.generate().address_bytes, 2 * ADA, {})],
    )
    signed = balance(transaction, sender, utxo.value.ada.lovelace, parameters, sender)
    async with client.mempool() as transactions:
        await client.submit_transaction(signed)
        async with asyncio.timeout(30):
            async for transaction_id in transactions:
                if transaction_id == transaction.id:
                    break
