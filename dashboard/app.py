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

# Streamlit Cloud hot-reloads app.py but NOT changed sub-modules — so a new app.py
# can run against a stale cached module and crash until a manual reboot. Force-refresh
# the fast-changing presentation/logic modules each run so signature changes can never
# crash the deployed app between push and reboot. The @st.cache_resource singletons live
# in dashboard.services_cache (NOT refreshed), so Services / the Neo4j connection persist.
for _m in [m for m in list(sys.modules)
           if m in ("dashboard.theme", "dashboard.state")
           or m.startswith("dashboard.components")]:
    del sys.modules[_m]

from dashboard.components.graph_view import render_graph, render_kg  # noqa: E402
from dashboard.components.masumi_panel import render_masumi       # noqa: E402
from dashboard.components.advisory_card import render_advisory_report  # noqa: E402
from dashboard.state import (advisory_answer, advisory_report,  # noqa: E402
                             agronomist_diagnose, agronomist_explain,
                             calm_ticks, classify_leaf, coop_triage,
                             get_services, inject_and_run, kg_subgraph,
                             masumi_round_trip, offline_box, set_language,
                             sms_reply)
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
             "Angawatch — early crop-saving alerts + a graph-grounded crop-health advisory a co-op hires via Masumi",
             datetime.now().strftime("%a %H:%M"), alerts=alerts_n)

# ------- precompute hero/snapshot (rendered inside the Farm tab) -------------
latest = (services.store.list_recent_readings(gh_id, limit=1) or [{}])[0]
engine_risk = None
try:
    engine_risk = services.engine.evaluate(gh_id).top
except Exception:  # noqa: BLE001
    pass
risk_level = engine_risk.level if engine_risk else "LOW"
risk_kind = engine_risk.kind if engine_risk else "—"
snapshot = advisory_report(services, gh_id, farm_id=farmer_id, risk_level=risk_level, narrate=False)

# ---- primary navigation: big, high, stunning (the main thing) --------------
tab_farm, tab_doctor, tab_coop, tab_advice, tab_phone = st.tabs(
    ["🌡️  Farm record & live feed", "🧠  Crop doctor (GraphRAG)", "🤝  Co-op triage & hire",
     "🍃  Leaf scan & advisor", "📱  Feature phone & offline"])

# ============================================================ FARM TAB ======
with tab_farm:
    hcol, gcol = st.columns([2, 1], gap="large")
    with hcol:
        theme.hero_conditions(gh_id, county, latest, datetime.now().strftime("%a %d %b"),
                              risk_level, risk_kind)
    with gcol:
        _tone = {"HIGH": "#E5484D", "MED": "#E8A317", "LOW": "#54B435"}.get(risk_level, "#54B435")
        _topact = (snapshot.recommended_actions[0]["name"]
                   if snapshot.recommended_actions else "Monitor conditions")
        st.markdown(
            f'<div class="aw-card" style="height:100%"><div class="aw-section" style="margin-bottom:10px">'
            f'<span class="ic">{theme.icon("spark",18)}</span><div><h3>Advisory snapshot</h3>'
            f'<p>graph-grounded crop-health for this farm</p></div></div>'
            f'<div style="font-size:.72rem;color:var(--faint);font-family:JetBrains Mono,monospace">DIAGNOSIS</div>'
            f'<div style="font-size:1.3rem;font-weight:800;color:var(--fg);line-height:1.15">{snapshot.diagnosis}</div>'
            f'<div style="margin:10px 0"><span style="background:{_tone};color:#fff;border-radius:9px;'
            f'padding:5px 11px;font-weight:700;font-size:.8rem">{snapshot.priority}</span></div>'
            f'<div style="font-size:.72rem;color:var(--faint);font-family:JetBrains Mono,monospace">TOP ACTION</div>'
            f'<div style="font-weight:600;color:var(--fg)">{_topact}</div>'
            f'<p style="color:var(--muted);font-size:.82rem;margin-top:12px">A co-op hires this '
            f'advisory agent via Masumi to triage farms and get an auditable diagnosis — see '
            f'<b>Co-op triage &amp; hire</b>.</p>'
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

# ====================================================== CROP DOCTOR TAB =====
with tab_doctor:
    theme.section("Crop doctor — GraphRAG over the agronomic knowledge graph",
                  "“Why was I warned, and what do I do?” The agent TRAVERSES the graph: "
                  "sensor readings → microclimate conditions → disease → pathogen → ranked "
                  "treatments — multi-hop reasoning, not a flat lookup. It shows the path it walked.",
                  "spark")
    bcol1, bcol2, _ = st.columns([1, 1, 1])
    run_explain = bcol1.button("🔎 Explain my latest alert", type="primary", key="kg_explain",
                               use_container_width=True)
    run_diag = bcol2.button("🩺 Diagnose current conditions", key="kg_diag_btn",
                            use_container_width=True)

    if run_explain or st.session_state.get("kg_for") != gh_id:
        st.session_state.kg_exp = agronomist_explain(services, gh_id)
        st.session_state.kg_for = gh_id
    exp = st.session_state.get("kg_exp")

    if not exp:
        st.info("No alerts on record yet for this greenhouse — stage a blight event in the "
                "**Farm record** tab, then come back.")
    else:
        d = exp.get("disease") or {}
        tgt = exp.get("target", {})
        hops = [{"kind": "Alert", "value": f"{exp['alert'].get('kind')} · {exp['alert'].get('level')}",
                 "rel": "FOR_DISEASE"},
                {"kind": "Disease" if tgt.get("label") == "Disease" else "Pest",
                 "value": d.get("name", "—"), "cls": "dis",
                 "rel": "CAUSED_BY" if exp.get("pathogen") else "CONTROLLED_BY"}]
        if exp.get("pathogen"):
            hops.append({"kind": "Pathogen", "value": exp["pathogen"], "cls": "path",
                         "rel": "CONTROLLED_BY"})
        hops.append({"kind": "Treatment", "value": f"{len(exp.get('treatments', []))} ranked options"})
        st.markdown(theme.kg_path(hops), unsafe_allow_html=True)

        if exp.get("conditions"):
            chips = " ".join(
                f'<span class="aw-tag phi">{c}</span>' for c in exp["conditions"])
            n_r = len(exp.get("trigger_readings") or [])
            st.markdown(
                f'<div style="margin:4px 0 10px"><span style="color:var(--muted);font-size:.8rem">'
                f'graph evidence — favoured by {n_r} linked sensor reading(s): </span>{chips}</div>',
                unsafe_allow_html=True)

        st.markdown(theme.pill(exp.get("narration_mode", "mock"),
                               f"agronomist narration · {exp.get('narration_mode','mock')} · "
                               f"graph backend {exp.get('backend','memory')}"),
                    unsafe_allow_html=True)
        _narr = (exp.get("narrative", "") or "").replace("**", "").replace("*", "")
        st.markdown(f"<div class='aw-card' style='margin:8px 0 14px'>{_narr}</div>",
                    unsafe_allow_html=True)

        tcol, gcol = st.columns([1, 1], gap="large")
        with tcol:
            theme.section("Recommended actions — ranked",
                          "By efficacy → pre-harvest interval → cost. Cultural/cheap first.", "check")
            st.markdown(theme.treatment_list(exp.get("treatments", []), n=6), unsafe_allow_html=True)
        with gcol:
            theme.section("The path on the graph",
                          "The disease and its neighbours in the knowledge graph.", "shield")
            if tgt.get("label") == "Disease" and tgt.get("id"):
                render_kg(kg_subgraph(services, tgt["id"]))
            else:
                st.caption("Pest target — see the ranked controls on the left.")

        with st.expander("🧠 Shows thinking — the Cypher traversal the agent ran"):
            st.code(exp.get("cypher", ""), language="cypher")
            st.caption("This walks Alert→Disease→Pathogen and Disease←Treatment in one query — "
                       "the kind of multi-hop join a graph does natively and a flat table can't.")

    if run_diag:
        st.session_state.kg_diag = agronomist_diagnose(services, gh_id)
    diag = st.session_state.get("kg_diag")
    if diag is not None and (run_diag or st.session_state.get("kg_diag_open")):
        st.session_state.kg_diag_open = True
        st.divider()
        theme.section("Diagnose from current conditions",
                      "Latest readings → indicated microclimate conditions → likely diseases.", "scan")
        cds = " ".join(f'<span class="aw-tag phi">{c}</span>' for c in diag.get("conditions", [])) \
            or "<span style='color:var(--muted)'>no risk conditions indicated right now</span>"
        st.markdown(f'<div style="margin-bottom:8px"><b>Indicated conditions:</b> {cds}</div>',
                    unsafe_allow_html=True)
        for dz in diag.get("diseases", [])[:4]:
            st.markdown(f"- **{dz['name']}** — via {', '.join(dz['via'])}")
        if diag.get("treatments"):
            st.caption(f"Top control for {diag['diseases'][0]['name']}:")
            st.markdown(theme.treatment_list(diag["treatments"], n=3), unsafe_allow_html=True)

# ========================================================= CO-OP TRIAGE =====
with tab_coop:
    theme.section("Co-op crop-health triage — the buyer's view",
                  "A horticulture co-op / off-taker contracts hundreds of greenhouses but has only "
                  "a few field officers. The agent monitors every farm, TRIAGES who's at risk, and "
                  "prepares a per-farm diagnosis + plan — so a scarce officer is sent where it matters. "
                  "The co-op agronomist approves.", "shield")

    farms = [(fid, gh, ct) for fid, (gh, ct) in FARMERS.items()]
    triage = coop_triage(services, farms)

    st.markdown("**Member greenhouses — officer-visit priority** (highest risk first)")
    trows = [{"priority": t["report"].priority, "greenhouse": t["gh_id"], "farmer": t["farmer_id"],
              "county": t["county"], "risk": t["report"].risk_level,
              "diagnosis": t["report"].diagnosis} for t in triage]
    st.dataframe(pd.DataFrame(trows), hide_index=True, use_container_width=True)
    n_high = sum(1 for t in triage if t["report"].risk_level == "HIGH")
    st.caption(f"{len(triage)} contracted greenhouses · {n_high} need a visit now · the agent ranks "
               "them so 3 officers can cover 400 farms by exception, not by rota.")

    st.divider()
    options = [t["farmer_id"] for t in triage]
    pick = st.selectbox("Prepare a verified advisory report for:", options, index=0, key="coop_pick")
    picked = next(t for t in triage if t["farmer_id"] == pick)
    ckey = (pick, picked["report"].risk_level)
    if st.session_state.get("coop_rep_key") != ckey:
        with st.spinner("Agent traversing the knowledge graph…"):
            st.session_state.coop_rep = advisory_report(
                services, picked["gh_id"], farm_id=pick, risk_level=picked["report"].risk_level)
        st.session_state.coop_rep_key = ckey
    rep = st.session_state.coop_rep
    render_advisory_report(rep)

    st.divider()
    theme.section("Hire & pay the agent via Masumi",
                  "Co-op discovers → pays per report (escrow USDM/ADA) → deliver → on-chain audit.", "link")
    if st.button("Pay & deliver via Masumi", type="primary", key="masumi_pay"):
        with st.spinner("Discovering agent → escrow payment → deliver advisory → audit…"):
            trip, mode = masumi_round_trip(services, rep)
            st.session_state.masumi = (trip, mode, rep.greenhouse_id)
    m = st.session_state.get("masumi")
    if m and m[2] == rep.greenhouse_id:
        render_masumi(m[0], m[1])

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
        for col, (kw, lbl) in zip(kcols, [("STATUS", "Status"), ("ADVICE", "Advice"),
                                          ("ALERTS", "Subscribe"), ("HELP", "Help")]):
            if col.button(lbl, key=f"sms_{kw}", use_container_width=True):
                _send(kw)
        custom = st.text_input("…or type a keyword (STATUS / USHAURI / SW / EN / STOP)", key="sms_in")
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
_has_doctor = bool(st.session_state.get("kg_exp"))
_has_advisory = bool(st.session_state.get("coop_rep"))
_has_masumi = bool(st.session_state.get("masumi"))
_flow = [
    ("Verified farm record", "done"),
    ("Blight alert fires", "done" if _has_alert else "active"),
    ("GraphRAG crop diagnosis", "done" if _has_doctor else ("active" if _has_alert else "")),
    ("Co-op triage + advisory", "done" if _has_advisory else ("active" if _has_doctor else "")),
    ("Hire & on-chain audit (Masumi)", "done" if _has_masumi else ("active" if _has_advisory else "")),
]
with sb_flow:
    try:
        theme.flow_steps(_flow, vertical=True)
    except TypeError:                # stale cached theme without the vertical kwarg
        theme.flow_steps(_flow)
theme.footer()
