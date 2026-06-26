"""CrewAI custom tool: query a farmer's OWN subgraph (GraphRAG grounding).

The agent answers grounded in the farmer's Neo4j subgraph, not generic text. Built
lazily so the package imports fine even when crewai isn't installed.
"""
from __future__ import annotations

import json


def build_subgraph_tool(store):
    """Return a CrewAI tool bound to `store`, or None if crewai is unavailable."""
    try:
        from crewai.tools import tool
    except Exception:  # noqa: BLE001
        return None

    @tool("FarmerSubgraph")
    def farmer_subgraph(farmer_id: str) -> str:
        """Fetch the farmer's verified farm-and-finance subgraph (seasons, harvests,
        alerts, actions, cooperative, greenhouse) as JSON. Use this as the ONLY
        source of facts about the farmer."""
        return json.dumps(store.get_farmer_subgraph(farmer_id), default=str)

    return farmer_subgraph


def build_advisory_tool(store):
    """Same subgraph access, for the advisory agent (Module 6)."""
    return build_subgraph_tool(store)
