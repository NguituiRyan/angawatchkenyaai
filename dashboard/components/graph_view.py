"""Render the farmer's Neo4j subgraph with streamlit-agraph (falls back to JSON)."""
from __future__ import annotations

import streamlit as st

GROUP_COLORS = {
    "Farmer": "#22C55E", "Greenhouse": "#3B82F6", "Season": "#A78BFA",
    "Harvest": "#F59E0B", "Alert": "#EF4444", "Reading": "#22D3EE",
    "Action": "#84CC16", "Cooperative": "#818CF8",
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

    nodes = [Node(id=n["id"], label=n["label"], size=15,
                  color=GROUP_COLORS.get(n["group"], "#94A3B8")) for n in data["nodes"]]
    edges = [Edge(source=e["source"], target=e["target"], label=e.get("label", ""),
                  color="#3A4860") for e in data["edges"]]
    config = Config(
        width=720, height=430, directed=True, physics=True, nodeHighlightBehavior=True,
        highlightColor="#22C55E", collapsible=False,
        node={"labelProperty": "label", "font": {"color": "#E8EEF6", "size": 13,
              "face": "Inter"}},
        link={"labelProperty": "label", "renderLabel": True,
              "font": {"color": "#9AA8BD", "size": 10}},
    )
    agraph(nodes=nodes, edges=edges, config=config)

    legend = "".join(
        f'<span class="aw-pill" style="background:rgba(255,255,255,.04);border-color:{c}55;'
        f'color:var(--muted)"><span class="dot" style="background:{c}"></span>{g}</span> '
        for g, c in GROUP_COLORS.items())
    st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:6px;margin-top:8px'>{legend}</div>",
                unsafe_allow_html=True)
