"""Write a greenhouse's advisory result_hash to a REAL Cardano preprod transaction.

  python scripts/cardano_record.py

Needs: BLOCKFROST_PROJECT_ID set + the preprod wallet (scripts/cardano_setup.py)
funded via the faucet. Prints the tx hash + cardanoscan link; set the printed
MASUMI_PRERECORDED_TX in .env so the dashboard audit step shows the real link.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.advisory import AdvisoryAgent  # noqa: E402
from config import get_settings  # noqa: E402
from graph.seed import ensure_seeded  # noqa: E402
from graph.store import get_store  # noqa: E402
from masumi_integration.onchain import record_decision_on_chain, wallet_address  # noqa: E402


def main() -> None:
    s = get_settings()
    if not s.BLOCKFROST_PROJECT_ID:
        print("\n  BLOCKFROST_PROJECT_ID not set. Get a free preprod key at blockfrost.io,")
        print("  set it in .env, fund the wallet (python scripts/cardano_setup.py), then re-run.\n")
        return

    gh_id = s.DEFAULT_GREENHOUSE_ID
    store = get_store(s)
    if store.mode == "memory":
        ensure_seeded(store)
    rep = AdvisoryAgent(s).report(store, gh_id, farm_id=s.DEFAULT_FARMER_ID, narrate=False)
    agent_id = s.AGENT_IDENTIFIER or "agent_angawatch_advisory"

    _, addr = wallet_address(s)
    print(f"\n  Recording on-chain advisory decision log for {gh_id}")
    print(f"  wallet    : {addr}")
    print(f"  diagnosis : {rep.diagnosis} ({rep.priority})")
    print(f"  hash      : {rep.result_hash}")
    print("  submitting to Cardano preprod (Blockfrost)…")
    try:
        r = record_decision_on_chain(rep.result_hash, agent_id, gh_id,
                                     rep.diagnosis, rep.priority, s)
    except Exception as exc:  # noqa: BLE001
        print(f"\n  FAILED: {exc}")
        print("  Common causes: wallet not funded yet (wait ~1 min after the faucet), or "
              "wrong/again-rate-limited Blockfrost key.\n")
        return

    print("\n  ✅ ON-CHAIN — real, verifiable:")
    print(f"     tx     : {r['tx_hash']}")
    print(f"     verify : {r['explorer_url']}")
    print("\n  Set this in .env (and Streamlit secrets) so the audit link is real:")
    print(f"     MASUMI_PRERECORDED_TX={r['tx_hash']}")
    print(f"     AGENT_IDENTIFIER={agent_id}\n")
    _ = rep  # advisory report committed above


if __name__ == "__main__":
    main()
