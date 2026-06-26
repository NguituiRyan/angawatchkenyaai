"""Shared helpers for the graph stores (props coercion, ids, subgraph shaping)."""
from __future__ import annotations

import dataclasses
import uuid
from typing import Any

# The compact subgraph shape returned by get_farmer_subgraph() — this is the
# CONTRACT the deterministic scorer and the GraphRAG agent both consume. Both
# store backends MUST produce this identical shape.
SUBGRAPH_KEYS = (
    "farmer", "greenhouse", "cooperative", "seasons", "harvests",
    "alerts", "alert_count", "action_count",
)


def to_props(obj: Any) -> dict:
    """Coerce a dataclass / object-with-to_props / dict into a plain dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "to_props") and callable(obj.to_props):
        return dict(obj.to_props())
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return dict(vars(obj))


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def empty_seed() -> dict:
    return {
        "farmers": [], "cooperatives": [], "lenders": [], "greenhouses": [],
        "seasons": [], "readings": [], "alerts": [], "actions": [],
        "harvests": [], "memberships": [], "partnerships": [],
    }
