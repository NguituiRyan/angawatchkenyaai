"""Standalone scoring demo:  python -m scoring.demo

Deterministic credit assessment for the hero farmer and a thin-file comparison.
No LLM, no network — pure, reproducible (same result_hash every run).
"""
from __future__ import annotations

from graph.seed import ensure_seeded
from graph.store import get_store
from scoring.scorer import CreditScorer


def _show(a) -> None:
    print(f"\n=== {a.farmer_id} ===")
    print(f"  Overall score : {a.overall_score}/100   -> Credit {a.credit['grade']} "
          f"({a.credit['limit']})   Insurance {a.insurance['grade']}")
    print(f"  Confidence    : {a.confidence['level']} ({a.confidence['value']}) — {a.confidence['driver']}")
    print("  Factors (contribution = weight x sub_score):")
    for f in a.factors:
        bar = "#" * int(f.sub_score / 5)
        print(f"    {f.label:<38} {f.sub_score:>5.1f}  x{f.weight:<4} = {f.contribution:>5.2f}  {bar}")
    print(f"  result_hash   : {a.result_hash[:24]}...")


def main() -> None:
    store = get_store()
    ensure_seeded(store)
    scorer = CreditScorer()
    for fid in ("Farmer-A", "Farmer-B"):
        _show(scorer.score_farmer(store, fid))
    print("\nHuman-in-the-loop limits:")
    for lim in CreditScorer().score_farmer(store, "Farmer-A").limits:
        print(f"  • {lim}")
    print()


if __name__ == "__main__":
    main()
