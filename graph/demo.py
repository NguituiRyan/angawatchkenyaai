"""Standalone graph demo:  python -m graph.demo

Seeds the store, prints stats, and dumps Farmer-A's compact subgraph (the exact
shape the credit scorer + GraphRAG agent consume).
"""
from __future__ import annotations

import json

from config import get_settings
from graph.seed import ensure_seeded
from graph.store import get_store


def main() -> None:
    settings = get_settings()
    store = get_store(settings)
    ensure_seeded(store)
    stats = store.stats()
    print(f"\nBackend: {stats['mode']}  |  nodes={stats['node_total']}  rels={stats['rel_total']}\n")

    sub = store.get_farmer_subgraph(settings.DEFAULT_FARMER_ID)
    print(f"Subgraph for {settings.DEFAULT_FARMER_ID}:")
    print(json.dumps(sub, indent=2, default=str))


if __name__ == "__main__":
    main()
