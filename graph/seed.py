"""Load the synthetic dataset and seed any GraphStore.

Reused by scripts/seed_db.py, the dashboard, and run_demo so the in-memory
store (ephemeral per process) is always populated from the same JSON.
"""
from __future__ import annotations

import json
from pathlib import Path

from logging_setup import get_logger

log = get_logger("graph.seed")
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic_history.json"


def load_dataset() -> dict:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    log.info("No %s — generating synthetic dataset", DATA_PATH.name)
    from scripts.gen_synthetic import build_synthetic
    data = build_synthetic()
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def ensure_seeded(store, data: dict | None = None) -> dict:
    data = data or load_dataset()
    store.load_seed(data)
    try:
        from graph.kg import seed_agronomy
        seed_agronomy(store)   # add the agronomic knowledge graph + link operational data
    except Exception as exc:  # noqa: BLE001
        log.warning("agronomy KG seed skipped: %s", exc)
    return data
