"""Angawatch lender dashboard (Streamlit) — light agri-SaaS UI.

  streamlit run dashboard/app.py

Greenhouse-monitoring + farm-to-finance: the farmer's verified Neo4j record, a
live sensor feed with a staged blight event, an explainable credit assessment,
and the Masumi round-trip. Every capability shows a LIVE/MOCK badge.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.components.graph_view import render_graph          # noqa: E402
from dashboard.components.masumi_panel import render_masumi       # noqa: E402
from dashboard.components.score_card import render_score_card     # noqa: E402
from dashboard.state import (advisory_answer, assess, calm_ticks,  # noqa: E402
                             classify_leaf, get_services, inject_and_run,
                             masumi_round_trip, offline_box, quick_score,
                             set_language, sms_reply)
from dashboard import theme                                       # noqa: E402

st.set_page_config(page_title="Angawatch — Greenhouse Monitoring", page_icon="🌱", layout="wide")
theme.inject_theme()

services = get_services()
settings = services.settings
FARMERS = {"Farmer-A": ("gh-001", "Nakuru"), "Farmer-B": ("gh-002", "Kiambu"),
           "Farmer-C": ("gh-003", "Kajiado")}

# --------------------------------------------------------------- sidebar ----
with st.sidebar:
    st.markdown(f"### {theme.icon('leaf',18)} Angawatch", unsafe_allow_html=True)
    farmer_id = st.selectbox("Farmer", list(FARMERS), index=0)
    gh_id, county = FARMERS[farmer_id]
    st.markdown(f"<span class='aw-hash'>greenhouse {gh_id} · {county}</span>", unsafe_allow_html=True)
    st.divider()
    st.markdown("**Demo flow** — what to do")
    sb_flow = st.container()   # vertical progress tracker, filled at end of the run
    st.divider()
    # inline (not settings.masumi_status()) so a hot-reload with a cached config
    # module can't crash the app on a newly-added method
    _mstat = ("real" if settings.masumi_mode() == "real"
              else "hybrid" if getattr(settings, "MASUMI_PRERECORDED_TX", None) else "mock")
    _mlabel = {"real": "Masumi · real preprod",
               "hybrid": "Masumi · on-chain proof ✓",
               "mock": "Masumi · mock"}[_mstat]
    _mpill = theme.pill("real" if _mstat in ("real", "hybrid") else "mock", _mlabel)
    st.markdown(
        f"**Live status**<br>"
        f"{theme.pill(services.store.mode,'Graph · '+services.store.mode)}<br>"
        f"{theme.pill(services.channel.mode,'Alerts · '+services.channel.mode)}<br>"
        f"{theme.pill(settings.llm_mode(),'LLM · '+settings.llm_mode())}<br>"
        f"{_mpill}",
        unsafe_allow_html=True)
    st.divider()
    if st.button("↺ Reset demo", use_container_width=True, key="reset"):
        for _k in ("last_run", "assessment", "masumi", "advice", "warmed"):
            st.session_state.pop(_k, None)
        st.rerun()
    st.caption("Mocks are labeled 🟠. Nothing here hides a mock — that's the point.")

if "warmed" not in st.session_state:
    calm_ticks(services, gh_id, n=4)
    st.session_state.warmed = True

# ---------------------------------------------------------------- topbar ----
alerts_n = len(services.store.list_alerts(gh_id, limit=20))
theme.topbar("Greenhouse Monitoring",
             "Angawatch — early crop-saving alerts + a verified farm record lenders price risk against",
             datetime.now().strftime("%a %H:%M"), alerts=alerts_n)

# ------- precompute hero/readiness (rendered inside the Farm tab) ------------
latest = (services.store.list_recent_readings(gh_id, limit=1) or [{}])[0]
engine_risk = None
try:
    engine_risk = services.engine.evaluate(gh_id).top
except Exception:  # noqa: BLE001
    pass
risk_level = engine_risk.level if engine_risk else "LOW"
risk_kind = engine_risk.kind if engine_risk else "—"
teaser = quick_score(services, farmer_id)

# ---- primary navigation: big, high, stunning (the main thing) --------------
tab_farm, tab_credit, tab_advice, tab_phone = st.tabs(
    ["🌡️  Farm record & live feed", "🏦  Credit assessment", "🍃  Leaf scan & advisor",
     "📱  Feature phone & offline"])

# ============================================================ FARM TAB ======
with tab_farm:
    hcol, gcol = st.columns([2, 1], gap="large")
    with hcol:
        theme.hero_conditions(gh_id, county, latest, datetime.now().strftime("%a %d %b"),
                              risk_level, risk_kind)
    with gcol:
        st.markdown(
            f'<div class="aw-card" style="height:100%"><div class="aw-section" style="margin-bottom:10px">'
            f'<span class="ic">{theme.icon("bank",18)}</span><div><h3>Finance readiness</h3>'
            f'<p>credit score from the farm record</p></div></div>'
            f'{theme.gauge(teaser["score"], "Credit band " + teaser["grade"], teaser["limit"])}'
            f'<p style="color:var(--muted);font-size:.82rem;margin-top:12px">A SACCO can hire the '
            f'Credit-Risk Agent via Masumi to turn this record into an explainable, auditable score.</p>'
            f'</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
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
            lat = readings[0]
            theme.kpis([
                {"label": "Humidity", "value": f"{lat.get('humidity'):.0f}%", "icon": "drop",
                 "sub": "RH ≥90% favours blight", "tone": "fill"},
                {"label": "Air temp", "value": f"{lat.get('temp_c'):.0f}°C", "icon": "thermo",
                 "sub": "blight band 10–26°C"},
                {"label": "Leaf wetness", "value": f"{lat.get('leaf_wetness_hr'):.0f}h", "icon": "sun",
                 "sub": "trailing window"},
                {"label": "Pest trap", "value": f"{lat.get('trap_count')}", "icon": "bug",
                 "sub": "males/trap/week"},
            ])
            st.caption("Humidity (green) vs air temp (amber) over recent readings — sustained "
                       "RH ≥90% in the 10–26°C band drives blight risk")
            theme.feed_chart(df.iloc[::-1])

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
                {"label": "Disease", "value": d.disease, "icon": "leaf", "tone": "fill"},
                {"label": "Severity", "value": d.severity.title(), "icon": "alert"},
                {"label": "Health", "value": f"{d.health_score:.0f}/100", "icon": "shield"},
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

# ========================================================== PHONE TAB =======
with tab_phone:
    theme.section("Feature-phone & offline reach",
                  "Many smallholders use basic phones in low-signal areas. The SAME risk engine "
                  "and credit score, delivered over SMS or an offline in-greenhouse box.", "activity")
    lang_label = st.radio("Language / Lugha", ["English", "Kiswahili"], horizontal=True,
                          key="phone_lang")
    lang = "sw" if lang_label == "Kiswahili" else "en"
    if st.session_state.get("_lang_for") != (farmer_id, lang):
        set_language(services, farmer_id, lang)   # only write when it actually changes
        st.session_state._lang_for = (farmer_id, lang)

    pcol, ocol = st.columns(2, gap="large")
    with pcol:
        st.markdown("**Two-way SMS** — the farmer texts the Angawatch number (no smartphone/data)")

        def _send(text):
            r = sms_reply(services, farmer_id, text)
            th = st.session_state.setdefault("sms_thread", [])
            th.append((farmer_id, "out", text))
            th.append(("Angawatch", "in", r["reply"]))

        kcols = st.columns(4)
        for col, (kw, lbl) in zip(kcols, [("STATUS", "Status"), ("LOAN", "Loan"),
                                          ("ALERTS", "Subscribe"), ("HELP", "Help")]):
            if col.button(lbl, key=f"sms_{kw}", use_container_width=True):
                _send(kw)
        custom = st.text_input("…or type a keyword (STATUS / MKOPO / SW / EN / STOP)", key="sms_in")
        if st.button("Send SMS", key="sms_send") and custom.strip():
            _send(custom.strip())

        thread = st.session_state.get("sms_thread", [])
        if thread:
            st.markdown(theme.sms_thread(thread[-8:]), unsafe_allow_html=True)
        else:
            st.caption("Tap a keyword above to simulate a farmer's SMS.")

    with ocol:
        st.markdown("**Offline alert box** — ESP-NOW node in the greenhouse, **no internet**")
        box = offline_box(services, gh_id, lang)
        st.markdown(theme.offline_device(box), unsafe_allow_html=True)
        st.caption("When there's no cell signal, the sensor node radios the alert to this in-house "
                   "box (OLED + LED + buzzer). It caches readings and syncs to /ingest when a "
                   "signal returns (store-and-forward).")
        st.info("🛰️ Hardware path (real seam): ESP32 + 7-in-1 soil sensor + DHT22 + GSM → "
                "POST /ingest. See docs for the BOM + connectivity ladder.")

# ---------------------------------------------- guided progress + footer ----
_run = st.session_state.get("last_run")
_has_alert = bool(_run and any(r.get("alert") for r in _run))
_has_assess = bool(st.session_state.get("assessment"))
_has_masumi = bool(st.session_state.get("masumi"))
with sb_flow:
    theme.flow_steps([
        ("Verified farm record", "done"),
        ("Early blight alert", "done" if _has_alert else "active"),
        ("Explainable credit score", "done" if _has_assess else ("active" if _has_alert else "")),
        ("On-chain Masumi audit", "done" if _has_masumi else ("active" if _has_assess else "")),
    ], vertical=True)
theme.footer()
