"""Standalone Masumi round-trip demo:  python -m masumi_integration.demo

Lender discovers -> hires -> pays escrow -> agent delivers -> on-chain audit.
Runs the labeled mock by default; set MASUMI_MODE=real (+ keys + funded wallet)
for genuine preprod, or MASUMI_PRERECORDED_TX=<txhash> to show a real audit link.
"""
from __future__ import annotations

from agents.credit_crew import CreditRiskAgent
from config import get_settings
from graph.seed import ensure_seeded
from graph.store import get_store
from logging_setup import tag
from masumi_integration.client import build_masumi_client


def main() -> None:
    settings = get_settings()
    store = get_store(settings)
    ensure_seeded(store)

    assessment = CreditRiskAgent(settings).assess(store, settings.DEFAULT_FARMER_ID)
    client = build_masumi_client(settings)
    trip = client.run_round_trip(assessment, store=store)

    print(f"\nMasumi round-trip  —  backend: {tag(client.mode)} {client.mode}\n")
    for s in trip["steps"]:
        line = f"  {tag(s['mode'])} {s['label']:<42} {s['detail']}"
        print(line)
        if s["tx_hash"]:
            link = s["explorer_url"] or "(simulated — no on-chain tx)"
            print(f"        tx: {s['tx_hash'][:34]}…  {link}")
    audit = trip["audit"]
    print(f"\n  Audit: {audit.status}  proof={audit.proof_kind}  "
          f"requester={audit.requester}")
    print(f"  result_hash committed: {audit.result_hash[:24]}…\n")


if __name__ == "__main__":
    main()
