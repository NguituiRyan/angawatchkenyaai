"""Standalone Credit-Risk Agent demo:  python -m agents.demo

Runs the agent on the hero farmer: deterministic score + grounded narration +
audit record. Uses live OpenRouter narration if OPENROUTER_API_KEY is set, else a
labeled deterministic template.
"""
from __future__ import annotations

import json

from agents.credit_crew import CreditRiskAgent
from config import get_settings
from graph.seed import ensure_seeded
from graph.store import get_store
from logging_setup import tag


def main() -> None:
    settings = get_settings()
    store = get_store(settings)
    ensure_seeded(store)

    agent = CreditRiskAgent(settings)
    assessment = agent.assess(store, settings.DEFAULT_FARMER_ID)

    print(f"\n{tag(assessment.mode['narration'])} narration "
          f"({assessment.mode['narration']}) | scorer: {assessment.mode['scorer']}\n")
    print("NARRATIVE:\n  " + assessment.narrative + "\n")
    print("EXPLAINABLE OUTPUT (JSON):")
    print(json.dumps(assessment.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()
