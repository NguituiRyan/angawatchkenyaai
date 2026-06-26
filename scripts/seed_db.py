"""Seed the farm-and-finance graph and print stats (Module 1 checkpoint).

Run:  python scripts/seed_db.py     (or:  python -m scripts.seed_db)

Uses Neo4j Aura if NEO4J_* is configured and reachable, otherwise a clearly
labeled in-memory store. Either way it prints node/relationship counts.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # allow direct execution

from graph.seed import ensure_seeded, load_dataset  # noqa: E402
from graph.store import get_store  # noqa: E402
from logging_setup import get_logger, tag  # noqa: E402

log = get_logger("seed_db")


def main() -> None:
    data = load_dataset()
    store = get_store()
    if hasattr(store, "apply_schema"):
        store.apply_schema()
    ensure_seeded(store, data)
    stats = store.stats()

    print()
    print(f"  Angawatch graph seeded  —  backend: {tag(stats['mode'])} {stats['mode']}")
    print("  " + "-" * 46)
    for label, count in stats["nodes"].items():
        print(f"    {label:<14} {count:>6}")
    print("  " + "-" * 46)
    print(f"    {'NODES total':<14} {stats['node_total']:>6}")
    print(f"    {'RELS total':<14} {stats['rel_total']:>6}")
    print()
    if stats["mode"] != "neo4j":
        print("  Note: in-memory mock (set NEO4J_URI/PASSWORD in .env for a live Aura record).")
    if hasattr(store, "close"):
        store.close()


if __name__ == "__main__":
    main()
