"""Standalone Crop-Health Advisory Agent demo:  python -m agents.demo

Runs the advisory agent on the hero greenhouse: graph-grounded diagnosis + ranked,
PHI-aware treatment plan + grounded narration + reproducible result_hash. Uses live
OpenRouter narration if OPENROUTER_API_KEY is set, else a labeled deterministic template.
"""
from __future__ import annotations

import json

from agents.advisory import AdvisoryAgent
from config import get_settings
from graph.seed import ensure_seeded
from graph.store import get_store
from logging_setup import tag


def main() -> None:
    settings = get_settings()
    store = get_store(settings)
    ensure_seeded(store)

    agent = AdvisoryAgent(settings)
    report = agent.report(store, settings.DEFAULT_GREENHOUSE_ID,
                          farm_id=settings.DEFAULT_FARMER_ID)

    print(f"\n{tag(report.narration_mode)} narration ({report.narration_mode}) | "
          f"graph backend: {report.backend}\n")
    print(f"DIAGNOSIS: {report.diagnosis}"
          + (f" (caused by {report.pathogen})" if report.pathogen else ""))
    print(f"RISK {report.risk_level} -> PRIORITY: {report.priority}")
    print("NARRATIVE:\n  " + report.narrative + "\n")
    print("ADVISORY REPORT (JSON):")
    print(json.dumps(report.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()
