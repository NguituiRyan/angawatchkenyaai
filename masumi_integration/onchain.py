"""Real Cardano PREPROD Decision Logging: write the advisory agent's result_hash to
on-chain transaction metadata via Blockfrost + pycardano.

This produces a genuine, verifiable transaction (preprod.cardanoscan.io) committing the
agent's diagnosis + treatment plan — the "verifiable result recorded on-chain" pattern,
doing real work (an auditable record of advice a farmer acted on), not decorating an
opinion. Local-only (needs BLOCKFROST_PROJECT_ID + a funded preprod wallet).
"""
from __future__ import annotations

from logging_setup import get_logger

log = get_logger("masumi.onchain")
PREPROD_EXPLORER = "https://preprod.cardanoscan.io/transaction/"
META_LABEL = 8434   # custom metadata label for Angawatch decision logs


def wallet_address(settings):
    from pycardano import (Address, Network, PaymentSigningKey,
                           PaymentVerificationKey)
    sk = PaymentSigningKey.load(settings.CARDANO_WALLET_SKEY)
    vk = PaymentVerificationKey.from_signing_key(sk)
    return sk, Address(vk.hash(), network=Network.TESTNET)


def _context(settings):
    from blockfrost import ApiUrls
    from pycardano import BlockFrostChainContext
    return BlockFrostChainContext(project_id=settings.BLOCKFROST_PROJECT_ID,
                                  base_url=ApiUrls.preprod.value)


def decision_metadata(result_hash: str, agent_id: str, subject: str,
                      diagnosis, priority: str) -> dict:
    """The on-chain Decision-Log metadata payload (Cardano string fields cap at 64 bytes)."""
    return {
        "app": "Angawatch",
        "type": "advisory-decision-log",
        "agent": str(agent_id)[:64],
        "subject": str(subject)[:64],
        "diagnosis": str(diagnosis)[:64],
        "priority": str(priority)[:64],
        "result_hash": str(result_hash)[:64],
    }


def record_decision_on_chain(result_hash: str, agent_id: str, subject: str,
                             diagnosis, priority: str, settings=None) -> dict:
    """Commit an advisory result_hash (diagnosis + plan) to preprod tx metadata."""
    from pycardano import (AuxiliaryData, Metadata, TransactionBuilder,
                           TransactionOutput)
    from config import get_settings
    settings = settings or get_settings()
    if not settings.BLOCKFROST_PROJECT_ID:
        raise RuntimeError("BLOCKFROST_PROJECT_ID not set")

    sk, addr = wallet_address(settings)
    ctx = _context(settings)
    meta = Metadata({META_LABEL: decision_metadata(
        result_hash, agent_id, subject, diagnosis, priority)})
    builder = TransactionBuilder(ctx)
    builder.add_input_address(addr)
    builder.add_output(TransactionOutput(addr, 1_500_000))   # 1.5 tADA back to self
    builder.auxiliary_data = AuxiliaryData(meta)
    signed = builder.build_and_sign([sk], change_address=addr)
    try:
        ctx.submit_tx(signed)
    except Exception:  # noqa: BLE001  (older pycardano wants cbor bytes)
        ctx.submit_tx(signed.to_cbor())
    tx_id = str(signed.id)
    log.info("[LIVE] on-chain decision log submitted: %s", tx_id)
    return {"tx_hash": tx_id, "explorer_url": PREPROD_EXPLORER + tx_id,
            "address": str(addr), "result_hash": result_hash}
