"""Render the farmer's Neo4j subgraph as a readable, dark pyvis network.

pyvis gives full control: outlined high-contrast labels, curved edges, hover.
Falls back to streamlit-agraph, then JSON, so it never hard-fails.
"""
from __future__ import annotations

import json
import re

import streamlit as st
import streamlit.components.v1 as components


def _short(label: str, n: int = 22) -> str:
    """Shorten a node label for display (drop parentheticals, cap length) so wide labels
    don't overflow the frame. The full name stays on hover."""
    s = re.sub(r"\s*\(.*?\)", "", label or "").strip()
    return (s[: n - 1] + "…") if len(s) > n else s

GROUP = {
    "Farmer": ("#54B435", 30), "Greenhouse": ("#3B82F6", 26), "Season": ("#8B5CF6", 20),
    "Harvest": ("#E8A317", 20), "Alert": ("#E5484D", 22), "Reading": ("#0E9FB5", 16),
    "Action": ("#6BB02E", 18), "Cooperative": ("#6366F1", 22),
    # agronomic knowledge-graph ontology
    "Disease": ("#E5484D", 28), "Pathogen": ("#B4456B", 18), "Condition": ("#0E9FB5", 20),
    "Symptom": ("#E8A317", 16), "Pest": ("#C2410C", 22), "Treatment": ("#3F9E2A", 22),
    "Beneficial": ("#8B5CF6", 16), "Crop": ("#54B435", 24), "GrowthStage": ("#64748B", 16),
}

# shared node/edge/interaction styling — the two graphs only differ in physics so they
# render with the SAME look and both sit centred + framed in their white card.
_BASE = {
    "nodes": {
        "shape": "dot", "borderWidth": 3, "borderWidthSelected": 4,
        "color": {"border": "#FFFFFF", "highlight": {"border": "#2E7321"}},
        "shadow": {"enabled": True, "color": "rgba(46,80,40,0.20)", "size": 10, "x": 0, "y": 4},
        "font": {"size": 16, "color": "#1B2A1F", "face": "Inter",
                 "strokeWidth": 5, "strokeColor": "#FFFFFF", "vadjust": -2},
    },
    "edges": {
        "color": {"color": "#C7D2BC", "highlight": "#54B435", "hover": "#54B435", "opacity": 0.9},
        "width": 1.5, "selectionWidth": 2.5,
        "smooth": {"type": "continuous", "roundness": 0.25},
        "arrows": {"to": {"enabled": True, "scaleFactor": 0.55}},
        "font": {"size": 11, "color": "#6E7D70", "face": "JetBrains Mono",
                 "strokeWidth": 5, "strokeColor": "#FFFFFF", "align": "middle"},
    },
    # locked: no scroll-zoom / no pan (so page scroll works + graph stays in frame)
    "interaction": {"hover": True, "tooltipDelay": 120, "dragNodes": True,
                    "dragView": False, "zoomView": False, "navigationButtons": False},
}
# bigger farm record (~20 nodes): spread out to fill the frame
_PHYSICS_FARM = {
    "barnesHut": {"gravitationalConstant": -9500, "springLength": 135, "centralGravity": 0.3,
                  "springConstant": 0.045, "damping": 0.55, "avoidOverlap": 0.6},
    "stabilization": {"enabled": True, "iterations": 220, "fit": True}, "minVelocity": 0.6,
}
# small KG subgraph (~9 nodes): stronger central pull + overlap avoidance so the focus
# disease stays centred (not flung to the edge) and the long treatment labels don't clip
_PHYSICS_KG = {
    "barnesHut": {"gravitationalConstant": -4200, "springLength": 150, "centralGravity": 0.85,
                  "springConstant": 0.05, "damping": 0.6, "avoidOverlap": 1.0},
    "stabilization": {"enabled": True, "iterations": 320, "fit": True}, "minVelocity": 0.5,
}
_OPTIONS = json.dumps({**_BASE, "physics": _PHYSICS_FARM})
_KG_OPTIONS = json.dumps({**_BASE, "physics": _PHYSICS_KG})


def _render_pyvis(data: dict, options: str | None = None, fit_scale: float = 0.9) -> bool:
    try:
        from pyvis.network import Network
    except Exception:  # noqa: BLE001
        return False
    net = Network(height="450px", width="100%", bgcolor="#FFFFFF",
                  font_color="#1B2A1F", directed=True, cdn_resources="remote")
    net.set_options(options or _OPTIONS)
    for n in data["nodes"]:
        color, size = GROUP.get(n["group"], ("#94A3B8", 16))
        net.add_node(n["id"], label=_short(n["label"]), color=color, size=size,
                     title=f"{n['group']}: {n['label']}", group=n["group"])
    for e in data["edges"]:
        net.add_edge(e["source"], e["target"], label=e.get("label", ""), title=e.get("label", ""))
    try:
        html = net.generate_html(notebook=False)
    except Exception:  # noqa: BLE001
        html = net.generate_html()
    # round the iframe corners to match our cards
    html = html.replace("<body>", '<body style="margin:0;background:#FFFFFF;border-radius:16px">')
    # freeze physics once stabilized, fit to all nodes, then zoom out a touch so node
    # LABELS (which extend past the dots) never clip at the frame edge — both graphs framed alike
    freeze = ("<script>setTimeout(function(){try{network.setOptions({physics:false});"
              "network.fit({animation:false});"
              f"network.moveTo({{scale:network.getScale()*{fit_scale},animation:false}});"
              "}catch(e){}},2600);</script>")
    html = html.replace("</body>", freeze + "</body>")
    components.html(html, height=466, scrolling=False)
    return True


def render_graph(store, farmer_id: str) -> None:
    data = store.get_visual_graph(farmer_id)
    if not data["nodes"]:
        st.info("No graph data for this farmer.")
        return
    if _render_pyvis(data):
        _legend()
        return
    # fallback: streamlit-agraph -> JSON
    try:
        from streamlit_agraph import Config, Edge, Node, agraph
        nodes = [Node(id=n["id"], label=n["label"], size=15, color=GROUP.get(n["group"], ("#94A3B8",))[0])
                 for n in data["nodes"]]
        edges = [Edge(source=e["source"], target=e["target"], label=e.get("label", "")) for e in data["edges"]]
        agraph(nodes=nodes, edges=edges, config=Config(width=720, height=440, directed=True, physics=True))
        _legend()
    except Exception:  # noqa: BLE001
        st.json(data)


def render_kg(subgraph: dict) -> None:
    """Render an agronomic knowledge-graph subgraph (disease + neighbours)."""
    if not subgraph.get("nodes"):
        st.info("No knowledge-graph data.")
        return
    if not _render_pyvis(subgraph, options=_KG_OPTIONS, fit_scale=0.72):
        st.json(subgraph)
        return
    groups = {n["group"] for n in subgraph["nodes"]}
    chips = "".join(
        f'<span class="aw-pill" style="background:#F4F7F0;border:1px solid #E7ECE0;'
        f'color:#6E7D70"><span class="dot" style="background:{GROUP.get(g,("#94A3B8",))[0]}"></span>'
        f'{g}</span> ' for g in sorted(groups))
    st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:6px;margin-top:10px'>{chips}</div>",
                unsafe_allow_html=True)


def _legend() -> None:
    show = ["Farmer", "Greenhouse", "Season", "Harvest", "Alert", "Reading", "Action", "Cooperative"]
    chips = "".join(
        f'<span class="aw-pill" style="background:#F4F7F0;border:1px solid #E7ECE0;'
        f'color:#6E7D70"><span class="dot" style="background:{GROUP[g][0]}"></span>{g}</span> '
        for g in show)
    st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:6px;margin-top:10px'>{chips}</div>",
                unsafe_allow_html=True)
