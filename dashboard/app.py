"""Angawatch lender dashboard (Streamlit) — dark, data-dense, premium UI.

  streamlit run dashboard/app.py

A SACCO/MFI/insurer view: the farmer's verified Neo4j record, a live sensor feed
with a staged blight event, an explainable credit assessment, and the Masumi
round-trip. Every capability shows a LIVE/MOCK badge. Deployable to Streamlit Cloud.
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
from dashboard import theme                                       # noqa: E402

st.set_page_config(page_title="Angawatch — farm-to-finance", page_icon="🌱", layout="wide")
theme.inject_theme()

services = get_services()
settings = services.settings
FARMERS = {"Farmer-A": "gh-001", "Farmer-B": "gh-002", "Farmer-C": "gh-003"}

# ---------------------------------------------------------------- header ----
theme.hero({
    "Graph": services.store.mode,
    "Alerts": services.channel.mode,
    "LLM": settings.llm_mode(),
    "Masumi": settings.masumi_mode(),
})

# --------------------------------------------------------------- sidebar ----
with st.sidebar:
    st.markdown(f"### {theme.icon('bank',18)} Lender view", unsafe_allow_html=True)
    farmer_id = st.selectbox("Farmer", list(FARMERS), index=0)
    gh_id = FARMERS[farmer_id]
    st.markdown(f"<span class='aw-hash'>greenhouse {gh_id}</span>", unsafe_allow_html=True)
    st.divider()
    st.markdown("**Demo flow**")
    st.markdown("1. See the verified farm record\n2. Stage a blight event → early alert\n"
                "3. Request the credit assessment\n4. Pay & audit via Masumi")
    st.divider()
    st.caption("Mocks are labeled 🟠. Nothing here hides a mock — that's the point.")

if "warmed" not in st.session_state:
    calm_ticks(services, gh_id, n=3)
    st.session_state.warmed = True

tab_farm, tab_credit, tab_advice = st.tabs(
    ["Farm record & live feed", "Credit assessment (lender)", "Leaf scan & advisor"])

# ============================================================ FARM TAB ======
with tab_farm:
    left, right = st.columns([3, 2], gap="large")
    with left:
        theme.section("Verified farm record", "Neo4j graph: readings → alerts "
                      "(TRIGGERED_BY) → actions → harvests.", "shield")
        render_graph(services.store, farmer_id)

    with right:
        theme.section("Live sensor feed", "Stage a blight event and watch the alert fire.",
                      "activity")
        b1, b2 = st.columns(2)
        if b1.button("Stream calm readings", key="calm", use_container_width=True):
            calm_ticks(services, gh_id, n=3)
        if b2.button("Inject blight event", type="primary", key="inject",
                     use_container_width=True):
            st.session_state.last_run = inject_and_run(services, gh_id)

        run = st.session_state.get("last_run")
        fired = next((r["alert"] for r in (run or []) if r.get("alert")), None)
        if fired:
            theme.alert_card(fired["level"], fired["kind"], fired["message"],
                             fired["delivery"], fired["provider"])

        readings = services.store.list_recent_readings(gh_id, limit=12)
        if readings:
            df = pd.DataFrame(readings)[["ts", "humidity", "temp_c", "leaf_wetness_hr", "trap_count"]]
            df["ts"] = df["ts"].astype(str).str[11:16]
            latest = readings[0]
            theme.kpis([
                {"label": "Humidity", "value": f"{latest.get('humidity'):.0f}%", "tone": "k-blue",
                 "sub": "RH (≥90% favours blight)"},
                {"label": "Air temp", "value": f"{latest.get('temp_c'):.0f}°C", "tone": "k-amber",
                 "sub": "blight band 10–26°C"},
                {"label": "Leaf wetness", "value": f"{latest.get('leaf_wetness_hr'):.0f}h",
                 "tone": "k-brand", "sub": "trailing window"},
                {"label": "Pest trap", "value": f"{latest.get('trap_count')}", "tone": "k-brand",
                 "sub": "males/trap/week"},
            ])
            st.line_chart(df.set_index("ts")[["humidity", "temp_c"]], height=200)

        alerts = services.store.list_alerts(gh_id, limit=5)
        if alerts:
            st.caption("Recent alerts on record")
            adf = pd.DataFrame(alerts)[["ts", "kind", "level", "delivery"]]
            st.dataframe(adf, hide_index=True, use_container_width=True, height=150)

# ========================================================== CREDIT TAB ======
with tab_credit:
    theme.section(f"Credit-Risk assessment — {farmer_id}",
                  "Hire the agent: it reads the farmer's own subgraph and returns an "
                  "explainable, multi-factor recommendation. A loan officer approves.", "bank")
    if st.button("Request assessment", type="primary", key="assess"):
        with st.spinner("Agent reading the farm record and scoring…"):
            st.session_state.assessment = assess(services, farmer_id)

    a = st.session_state.get("assessment")
    if a and a.farmer_id == farmer_id:
        render_score_card(a)
        st.divider()
        theme.section("Hire & pay the agent via Masumi",
                      "Discover → pay escrow (USDM/ADA) → deliver → on-chain audit.", "link")
        if st.button("Pay & deliver via Masumi", type="primary", key="masumi_pay"):
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
    vcol, acol = st.columns(2, gap="large")
    with vcol:
        theme.section("Leaf disease scan", "Pre-trained PlantVillage tomato classifier "
                      "(inference only).", "scan")
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
            st.markdown(theme.pill(d.mode), unsafe_allow_html=True)
            theme.kpis([
                {"label": "Disease", "value": d.disease, "tone": "k-amber"},
                {"label": "Severity", "value": d.severity.title(), "tone": "k-blue"},
                {"label": "Health", "value": f"{d.health_score:.0f}/100", "tone": "k-brand"},
            ])
            st.markdown(f"<span class='aw-hash'>confidence {d.confidence} · "
                        f"label {d.raw_label}</span>", unsafe_allow_html=True)

    with acol:
        theme.section("Ask the advisor (GraphRAG)", f"Grounded in {farmer_id}'s own farm record.",
                      "spark")
        q = st.text_input("Your question", "Should I spray for blight tonight? Humidity is high.")
        if st.button("Ask", key="ask", type="primary"):
            with st.spinner("Reading your record…"):
                st.session_state.advice = advisory_answer(services, farmer_id, q)
        adv = st.session_state.get("advice")
        if adv:
            st.markdown(theme.pill(adv["mode"], f"{adv['mode']} · grounded on {adv['grounded_on']}"),
                        unsafe_allow_html=True)
            st.markdown(f"<div class='aw-card' style='margin-top:10px'>{adv['answer']}</div>",
                        unsafe_allow_html=True)
