"""Angawatch end-to-end narrated demo (resilient; degrades gracefully).

  python scripts/run_demo.py                # prefer live, auto-downgrade per dep
  python scripts/run_demo.py --all-mock     # fully offline, every step labeled

Sequence: PREFLIGHT -> SEED -> SIM -> INJECT -> RISK/ALERT/RECORD ->
          ASSESS (Masumi) -> SCORE -> AUDIT -> SUMMARY
ASSESS/SCORE/AUDIT are wired in Modules 3 & 5; the AgriFin hero loop (through
RECORD) is fully live here.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _force_all_mock() -> None:
    os.environ["GRAPH_BACKEND"] = "memory"
    os.environ["LLM_MODE"] = "mock"
    os.environ["VISION_MODE"] = "mock"
    os.environ["MASUMI_MODE"] = "mock"
    os.environ["TWILIO_SID"] = ""
    os.environ["TWILIO_TOKEN"] = ""


def _matrix(services, settings) -> str:
    from logging_setup import tag
    rows = [
        ("Graph (Neo4j/Aura)", services.store.mode),
        ("Alerts (Twilio)", services.channel.mode),
        ("LLM narration", settings.llm_mode()),
        ("Vision classifier", settings.vision_mode()),
        ("Masumi pay/audit", settings.masumi_mode()),
    ]
    return "\n".join(f"   {tag(m):<7} {name:<22} ({m})" for name, m in rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-mock", action="store_true", help="force every backend to mock")
    ap.add_argument("--gh", default=None, help="greenhouse id")
    args = ap.parse_args()
    if args.all_mock:
        _force_all_mock()

    from config import get_settings
    get_settings.cache_clear()
    from logging_setup import banner
    from services import build_services

    settings = get_settings()
    gh = args.gh or settings.DEFAULT_GREENHOUSE_ID

    # 0. PREFLIGHT -----------------------------------------------------------
    print(banner("ANGAWATCH — end-to-end demo",
                 ["mode: " + ("ALL-MOCK (offline)" if args.all_mock else "prefer-live")]))
    services = build_services(settings)
    print("\nLive/Mock matrix:")
    print(_matrix(services, settings))

    # 1. SEED ----------------------------------------------------------------
    stats = services.store.stats()
    print(banner("1. FARM RECORD (Neo4j graph)",
                 [f"backend: {stats['mode']}",
                  f"nodes: {stats['node_total']}   relationships: {stats['rel_total']}",
                  f"hero farmer: {settings.DEFAULT_FARMER_ID}  greenhouse: {gh}"]))

    # 2. SIM (calm baseline) -------------------------------------------------
    print(banner("2. LIVE SENSOR FEED (calm)"))
    for _ in range(4):
        out = services.tick_and_ingest(gh)
        _print_reading(services, gh, out)

    # 3. INJECT --------------------------------------------------------------
    print(banner("3. STAGED BLIGHT EVENT", ["inject_event('late_blight') — humidity climbs"]))
    services.inject(gh, "late_blight", ticks=10)

    # 4-6. RISK -> ALERT -> RECORD ------------------------------------------
    print(banner("4-6. RISK ENGINE -> ALERT -> GRAPH"))
    hero_alert = None
    for _ in range(9):
        out = services.tick_and_ingest(gh)
        _print_reading(services, gh, out)
        if out["alert"]:
            hero_alert = out["alert"]
            a = out["alert"]
            print(f"\n   📲 {a['delivery'].upper()} ALERT via {a['provider']}: "
                  f"[{a['level']}] {a['kind']}")
            print(f"      {a['message']}")
        if hero_alert and hero_alert["level"] == "HIGH":
            break

    if hero_alert:
        latest = services.store.list_alerts(gh, limit=1)
        if latest:
            node = latest[0]
            print("\n   New Alert node written to the graph:")
            print(f"      id={node.get('id')}  level={node.get('level')}  "
                  f"kind={node.get('kind')}  delivery={node.get('delivery')}")
            print(f"      TRIGGERED_BY readings: {node.get('triggered_by')}")
    else:
        print("\n   (no HIGH alert this run — re-run; event regime is randomized)")

    # 7. ASSESS — lender hires the Credit-Risk Agent ------------------------
    from agents.credit_crew import CreditRiskAgent
    from logging_setup import tag
    from masumi_integration.client import build_masumi_client

    print(banner("7. LENDER HIRES THE CREDIT-RISK AGENT"))
    assessment = CreditRiskAgent(settings).assess(services.store, settings.DEFAULT_FARMER_ID)

    # 8. SCORE — explainable, multi-factor ----------------------------------
    print(banner("8. EXPLAINABLE CREDIT SCORE",
                 [f"score {assessment.overall_score}/100  ->  Credit {assessment.credit['grade']} "
                  f"({assessment.credit['limit']})  |  Insurance {assessment.insurance['grade']}",
                  f"confidence: {assessment.confidence['level']} ({assessment.confidence['value']})",
                  f"narration: {tag(assessment.mode['narration'])} {assessment.mode['narration']}"]))
    for f in sorted(assessment.factors, key=lambda x: x.contribution, reverse=True):
        print(f"   {f.label:<40} {f.sub_score:>5.1f}/100  x{f.weight:<4} = +{f.contribution:.2f}")
    print(f"\n   {assessment.narrative}")
    print(f"\n   result_hash: {assessment.result_hash}")

    # 9. AUDIT — pay + deliver + on-chain proof via Masumi ------------------
    print(banner("9. MASUMI: PAY -> DELIVER -> ON-CHAIN AUDIT"))
    client = build_masumi_client(settings)
    trip = client.run_round_trip(assessment, store=services.store)
    for s in trip["steps"]:
        print(f"   {tag(s['mode'])} {s['label']:<42} {s['detail']}")
        if s["tx_hash"]:
            print(f"          tx {s['tx_hash'][:30]}…  {s['explorer_url'] or '(simulated)'}")
    print(f"\n   Audit: {trip['audit'].status} (proof={trip['audit'].proof_kind})")

    # SUMMARY ----------------------------------------------------------------
    print(banner("SUMMARY — Live/Mock matrix"))
    print(_matrix(services, settings))
    print("\nAgriFin hero loop complete: staged blight -> early HIGH alert -> graph record.\n")


def _print_reading(services, gh, out) -> None:
    rs = services.store.list_recent_readings(gh, limit=1)
    r = rs[0] if rs else {}
    flag = {"HIGH": "  <== HIGH", "MED": "  <- moderate"}.get(out["level"], "")
    print(f"   {str(r.get('ts',''))[11:16]}  RH={r.get('humidity'):>4}%  "
          f"T={r.get('temp_c'):>4}C  -> risk={out['level']}{flag}")


if __name__ == "__main__":
    main()
