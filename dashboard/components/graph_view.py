"""Render the farmer's Neo4j subgraph with streamlit-agraph (falls back to JSON)."""
from __future__ import annotations

import streamlit as st

GROUP_COLORS = {
    "Farmer": "#2e7d32", "Greenhouse": "#1565c0", "Season": "#6a1b9a",
    "Harvest": "#ef6c00", "Alert": "#c62828", "Reading": "#00838f",
    "Action": "#558b2f", "Cooperative": "#4527a0",
}


def render_graph(store, farmer_id: str) -> None:
    data = store.get_visual_graph(farmer_id)
    if not data["nodes"]:
        st.info("No graph data for this farmer.")
        return
    try:
        from streamlit_agraph import Config, Edge, Node, agraph
    except Exception:  # noqa: BLE001
        st.caption("(install streamlit-agraph for the interactive view — showing JSON)")
        st.json(data)
        return

    nodes = [Node(id=n["id"], label=n["label"], size=16,
                  color=GROUP_COLORS.get(n["group"], "#888")) for n in data["nodes"]]
    edges = [Edge(source=e["source"], target=e["target"], label=e.get("label", ""))
             for e in data["edges"]]
    config = Config(width=720, height=430, directed=True, physics=True,
                    nodeHighlightBehavior=True, collapsible=False)
    agraph(nodes=nodes, edges=edges, config=config)
    legend = "  ".join(f":{c[1:]}[●] {g}" if False else f"{g}" for g, c in GROUP_COLORS.items())
    st.caption("Nodes: " + legend)
