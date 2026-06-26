"""Angawatch lender dashboard (Streamlit).

  streamlit run dashboard/app.py

A SACCO/MFI/insurer view: the farmer's verified Neo4j record, the live sensor
feed with a staged blight event, and the explainable credit assessment. Every
capability shows a LIVE/MOCK badge. Deployable to Streamlit Community Cloud.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.components.graph_view import render_graph          # noqa: E402
from dashboard.components.masumi_panel import render_masumi       # noqa: E402
from dashboard.components.score_card import render_score_card     # noqa: E402
from dashboard.state import (advisory_answer, assess, calm_ticks,  # noqa: E402
                             classify_leaf, get_services, inject_and_run,
                             masumi_round_trip)
from logging_setup import badge                                   # noqa: E402

st.set_page_config(page_title="Angawatch — farm-to-finance", page_icon="🌱", layout="wide")

services = get_services()
settings = services.settings

FARMERS = {"Farmer-A": "gh-001", "Farmer-B": "gh-002", "Farmer-C": "gh-003"}

# ---------------------------------------------------------------- header ----
st.title("🌱 Angawatch")
st.caption("Early crop-saving alerts **and** a verified farm record lenders can price risk against.")

badges = {
    "Graph (Neo4j)": services.store.mode,
    "Alerts (Twilio)": services.channel.mode,
    "LLM narration": settings.llm_mode(),
    "Masumi pay/audit": settings.masumi_mode(),
}
bcols = st.columns(len(badges))
for col, (name, mode) in zip(bcols, badges.items()):
    col.markdown(f"**{name}**<br>{badge(mode)} `{mode}`", unsafe_allow_html=True)
st.divider()

# --------------------------------------------------------------- sidebar ----
with st.sidebar:
    st.header("Lender view")
    farmer_id = st.selectbox("Farmer", list(FARMERS), index=0)
    gh_id = FARMERS[farmer_id]
    st.caption(f"Greenhouse: `{gh_id}`")
    st.divider()
    st.markdown("**Demo flow**\n\n1. See the verified farm record\n2. Stage a blight event → "
                "early alert fires\n3. Request the credit assessment\n4. (Masumi) pay & audit")
    st.divider()
    st.caption("Mocks are labeled 🟠. Nothing here hides a mock — that's the point.")

# auto-stream a few calm readings on first load so the feed isn't empty
if "warmed" not in st.session_state:
    calm_ticks(services, gh_id, n=3)
    st.session_state.warmed = True

tab_farm, tab_credit, tab_advice = st.tabs(
    ["🌡️ Farm record & live feed", "🏦 Credit assessment (lender)", "🍃 Leaf scan & advisor"])

# ============================================================ FARM TAB ======
with tab_farm:
    left, right = st.columns([3, 2])
    with left:
        st.subheader("Verified farm record")
        st.caption("Neo4j graph: readings → alerts (TRIGGERED_BY) → actions → harvests.")
        render_graph(services.store, farmer_id)

    with right:
        st.subheader("Live sensor feed")
        b1, b2 = st.columns(2)
        if b1.button("➕ Stream calm readings", key="calm"):
            calm_ticks(services, gh_id, n=3)
        if b2.button("🌫️ Inject blight event", type="primary", key="inject"):
            st.session_state.last_run = inject_and_run(services, gh_id)

        run = st.session_state.get("last_run")
        fired = next((r["alert"] for r in (run or []) if r.get("alert")), None)
        if fired:
            lvl = fired["level"]
            box = st.error if lvl == "HIGH" else st.warning
            box(f"📲 {fired['delivery'].upper()} alert via {fired['provider']} — "
                f"**[{lvl}] {fired['kind']}**\n\n{fired['message']}")

        readings = services.store.list_recent_readings(gh_id, limit=10)
        if readings:
            df = pd.DataFrame(readings)[["ts", "humidity", "temp_c", "leaf_wetness_hr", "trap_count"]]
            df["ts"] = df["ts"].astype(str).str[11:16]
            st.dataframe(df.iloc[::-1], hide_index=True, use_container_width=True, height=240)
            st.line_chart(df.set_index("ts")[["humidity", "temp_c"]])

        alerts = services.store.list_alerts(gh_id, limit=5)
        if alerts:
            st.caption("Recent alerts on record")
            adf = pd.DataFrame(alerts)[["ts", "kind", "level", "delivery"]]
            st.dataframe(adf, hide_index=True, use_container_width=True, height=160)

# ========================================================== CREDIT TAB ======
with tab_credit:
    st.subheader(f"Credit-Risk assessment — {farmer_id}")
    st.caption("Hire the Credit-Risk Agent: it reads the farmer's own subgraph and returns an "
               "explainable, multi-factor recommendation. A loan officer approves.")
    if st.button("📊 Request assessment", type="primary", key="assess"):
        with st.spinner("Agent reading the farm record and scoring…"):
            st.session_state.assessment = assess(services, farmer_id)

    a = st.session_state.get("assessment")
    if a and a.farmer_id == farmer_id:
        render_score_card(a)
        st.divider()
        st.subheader("🔗 Hire & pay the agent via Masumi")
        if st.button("💳 Pay & deliver via Masumi", type="primary", key="masumi_pay"):
            with st.spinner("Discovering agent → escrow payment → deliver → audit…"):
                trip, mode = masumi_round_trip(services, a)
                st.session_state.masumi = (trip, mode, farmer_id)
        m = st.session_state.get("masumi")
        if m and m[2] == farmer_id:
            render_masumi(m[0], m[1])
    else:
        st.info("Click **Request assessment** to run the Credit-Risk Agent for this farmer.")

# ========================================================== ADVICE TAB ======
with tab_advice:
    vcol, acol = st.columns(2)
    with vcol:
        st.subheader("🍃 Leaf disease scan")
        st.caption("Pre-trained PlantVillage tomato classifier (inference only).")
        up = st.file_uploader("Upload a tomato leaf photo", type=["jpg", "jpeg", "png"])
        use_sample = st.button("Use sample leaf image", key="sample_leaf")
        target = up
        if use_sample:
            target = str(Path(__file__).resolve().parents[1] /
                         "data" / "sample_leaf" / "tomato_leaf_blight.png")
        if target is not None:
            if up is not None:
                st.image(up, width=220)
            d = classify_leaf(services, target)
            st.markdown(f"Result: {badge(d.mode)} `{d.mode}`")
            c1, c2, c3 = st.columns(3)
            c1.metric("Disease", d.disease)
            c2.metric("Severity", d.severity)
            c3.metric("Health", f"{d.health_score:.0f}/100")
            st.caption(f"confidence {d.confidence} · raw label `{d.raw_label}`")

    with acol:
        st.subheader("🤖 Ask the advisor (GraphRAG)")
        st.caption(f"Grounded in **{farmer_id}**'s own farm record.")
        q = st.text_input("Your question", "Should I spray for blight tonight? Humidity is high.")
        if st.button("Ask", key="ask"):
            with st.spinner("Reading your record…"):
                st.session_state.advice = advisory_answer(services, farmer_id, q)
        adv = st.session_state.get("advice")
        if adv:
            st.markdown(f"{badge(adv['mode'])} `{adv['mode']}` · grounded on `{adv['grounded_on']}`")
            st.write(adv["answer"])
