"""Angawatch dashboard (Streamlit) — light agri-SaaS UI.

  streamlit run dashboard/app.py

A role-select landing gates the app: pick FARMER or CO-OP and see only that user's
tabs, so each flow is clean to follow. Farmer = phone-first crop-saving; Co-op = portfolio
triage, GraphRAG diagnosis, the verified Neo4j record, and hiring the agent via Masumi.
Every capability shows a LIVE/MOCK badge.
"""
from __future__ import annotations

import html
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Streamlit Cloud hot-reloads app.py but NOT changed sub-modules — so a new app.py can
# run against stale cached modules and crash until a manual reboot. Force-refresh the
# fast-changing, STATELESS code each run. NOT refreshed: dashboard.services_cache / services
# / graph.store / graph.seed / config — they hold the cached Services + Neo4j connection.
_REFRESH = ("dashboard.theme", "dashboard.state", "dashboard.components",
            "agents", "masumi_integration", "comms", "graph.kg", "graph.agronomy")
for _m in [m for m in list(sys.modules)
           if any(m == p or m.startswith(p + ".") for p in _REFRESH)]:
    del sys.modules[_m]

from dashboard.components.graph_view import render_graph, render_kg  # noqa: E402
from dashboard.components.masumi_panel import render_masumi       # noqa: E402
from dashboard.components.advisory_card import render_advisory_report  # noqa: E402
from dashboard.state import (advisory_a2a, advisory_answer,  # noqa: E402
                             advisory_report, agentic_answer,
                             agronomist_diagnose, agronomist_explain,
                             calm_ticks, classify_leaf, coop_triage,
                             get_services, inject_and_run, kg_subgraph,
                             masumi_round_trip, offline_box, send_text,
                             set_language, sms_reply, sokosumi_marketplace)
from dashboard import theme                                       # noqa: E402

st.set_page_config(page_title="Angawatch", page_icon="🌱", layout="wide")
theme.inject_theme()

services = get_services()
settings = services.settings
FARMERS = {"Farmer-A": ("gh-001", "Nakuru"), "Farmer-B": ("gh-002", "Kiambu"),
           "Farmer-C": ("gh-003", "Kajiado")}


def _smode(name: str) -> str:
    """Read a Settings *_mode() resolver, tolerating a stale cached Settings (e.g. one
    built before at_mode existed) so a hot-reload can't crash the app before a reboot."""
    fn = getattr(settings, name, None)
    return fn() if callable(fn) else "mock"


# ============================================================ LANDING ========
def render_landing() -> None:
    st.markdown(
        f"<div style='text-align:center;margin:18px 0 6px'>"
        f"<div style='font-size:1.9rem;font-weight:800;color:var(--fg)'>"
        f"<span class='aw-logo'>{theme.icon('leaf',26)}</span> Angawatch</div>"
        f"<p style='color:var(--muted);font-size:1rem;margin-top:4px'>Greenhouse intelligence — "
        f"choose how to explore the demo.</p></div>", unsafe_allow_html=True)

    def card(color, ic, title, sub, rows):
        items = "".join(
            f"<div style='font-size:.9rem;color:var(--fg);margin:7px 0'>"
            f"<span style='color:var(--muted)'>{theme.icon(i,15)}</span> &nbsp;{lbl}</div>"
            for i, lbl in rows)
        return (f"<div class='aw-card' style='border-top:5px solid {color};height:100%'>"
                f"<div style='width:46px;height:46px;border-radius:50%;background:{color}22;"
                f"display:flex;align-items:center;justify-content:center;margin-bottom:10px;"
                f"color:{color}'>{theme.icon(ic,24)}</div>"
                f"<div style='font-size:1.15rem;font-weight:800;color:var(--fg)'>{title}</div>"
                f"<div style='color:var(--muted);font-size:.85rem;margin-bottom:10px'>{sub}</div>"
                f"{items}</div>")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(card("#54B435", "leaf", "I'm a farmer", "Phone-first, simple",
                         [("thermo", "My greenhouse"), ("scan", "Leaf scan"),
                          ("activity", "My phone — SMS / WhatsApp")]), unsafe_allow_html=True)
        if st.button("Enter as farmer  →", key="role_farmer", type="primary",
                     use_container_width=True):
            st.session_state.role = "farmer"
            st.rerun()
    with c2:
        st.markdown(card("#3B82F6", "bank", "I'm a cooperative", "Triage, diagnose, hire",
                         [("shield", "Farm triage & hire (Masumi)"),
                          ("spark", "Crop doctor — graph reasoning"),
                          ("link", "Verified record (Neo4j)"), ("scan", "Leaf scan")]),
                    unsafe_allow_html=True)
        if st.button("Enter as co-op  →", key="role_coop", type="primary",
                     use_container_width=True):
            st.session_state.role = "coop"
            st.rerun()

    st.markdown(
        f"<div style='display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:18px'>"
        f"<span style='color:var(--faint);font-size:.78rem'>live:</span>"
        f"{theme.pill(services.store.mode,'Neo4j · '+services.store.mode)}"
        f"{theme.pill(settings.llm_mode(),'LLM · '+settings.llm_mode())}"
        f"{theme.pill(_smode('alert_mode'),'WhatsApp · '+_smode('alert_mode'))}"
        f"{theme.pill(_smode('at_mode'),'SMS · '+_smode('at_mode'))}"
        f"{theme.pill('real' if getattr(settings,'MASUMI_PRERECORDED_TX',None) else 'mock','Masumi')}"
        f"</div>", unsafe_allow_html=True)


# ===================================================== TAB BODIES ============
def render_my_greenhouse(gh_id: str, county: str, farmer_id: str) -> None:
    latest = (services.store.list_recent_readings(gh_id, limit=1) or [{}])[0]
    try:
        top = services.engine.evaluate(gh_id).top
        risk_level, risk_kind = top.level, top.kind
    except Exception:  # noqa: BLE001
        risk_level, risk_kind = "LOW", "—"
    snapshot = advisory_report(services, gh_id, farm_id=farmer_id, risk_level=risk_level, narrate=False)

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
            f'<span class="ic">{theme.icon("spark",18)}</span><div><h3>What to do</h3>'
            f'<p>graph-grounded advice for your farm</p></div></div>'
            f'<div style="font-size:.72rem;color:var(--faint);font-family:JetBrains Mono,monospace">DIAGNOSIS</div>'
            f'<div style="font-size:1.3rem;font-weight:800;color:var(--fg);line-height:1.15">{snapshot.diagnosis}</div>'
            f'<div style="margin:10px 0"><span style="background:{_tone};color:#fff;border-radius:9px;'
            f'padding:5px 11px;font-weight:700;font-size:.8rem">{snapshot.priority}</span></div>'
            f'<div style="font-size:.72rem;color:var(--faint);font-family:JetBrains Mono,monospace">TOP ACTION</div>'
            f'<div style="font-weight:600;color:var(--fg)">{_topact}</div></div>', unsafe_allow_html=True)

    st.markdown(
        "<div class='aw-card' style='border-left:4px solid var(--brand);background:var(--surface-2);"
        "margin-top:14px'><span style='font-size:.7rem;color:var(--faint);"
        "font-family:JetBrains Mono,monospace'>🌾 PILOT FIELD TEST · Baba Neema, Nakuru</span><br>"
        "<span style='font-style:italic;color:var(--fg)'>“One cold, misty night the box messaged my "
        "phone — high blight risk, ventilate and spray — two days before I saw any spots. I sprayed "
        "that morning and saved the crop. I lost half my tomatoes to blight last season; this time I "
        "kept almost all of it. I want the box on my second tunnel too.”</span></div>",
        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    theme.section("Live sensor feed", "Stage a blight event and watch the alert fire.", "activity")
    b1, b2, _ = st.columns([1, 1, 2])
    if b1.button("Stream calm readings", key="calm", use_container_width=True):
        calm_ticks(services, gh_id, n=3)
    if b2.button("Inject blight event", type="primary", key="inject", use_container_width=True):
        _alang = "sw" if st.session_state.get("phone_lang") == "Kiswahili" else "en"
        st.session_state.last_run = inject_and_run(services, gh_id, lang=_alang)

    run = st.session_state.get("last_run")
    _alerts = [r["alert"] for r in (run or []) if r.get("alert")]
    _ord = {"LOW": 0, "MED": 1, "HIGH": 2}
    fired = max(_alerts, key=lambda a: _ord.get(a["level"], 0)) if _alerts else None
    if fired:
        st.caption("📲 The farmer instantly receives this WhatsApp/SMS — simple + what to do:")
        theme.alert_card(fired["level"], fired["kind"], fired["message"],
                         fired["delivery"], fired["provider"])
        if fired.get("reason"):
            st.caption(f"Why it fired (on record): {fired['reason']}")

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
        st.caption("Humidity vs air temp over recent readings — sustained RH ≥90% in the "
                   "10–26°C band drives blight risk")
        theme.feed_chart(df.iloc[::-1])


def render_verified_record(farmer_id: str, gh_id: str) -> None:
    theme.section("Verified farm record", "Neo4j graph: readings → alerts (TRIGGERED_BY) → "
                  "actions → harvests. The auditable history a lender or insurer can trust.", "shield")
    render_graph(services.store, farmer_id)
    alerts = services.store.list_alerts(gh_id, limit=6)
    if alerts:
        st.caption("Recent alerts on record")
        adf = pd.DataFrame(alerts)[["ts", "kind", "level", "delivery"]]
        st.dataframe(adf, hide_index=True, use_container_width=True, height=180)


def render_crop_doctor(gh_id: str) -> None:
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
                "farmer view, then come back.")
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
            chips = " ".join(f'<span class="aw-tag phi">{c}</span>' for c in exp["conditions"])
            n_r = len(exp.get("trigger_readings") or [])
            st.markdown(
                f'<div style="margin:4px 0 10px"><span style="color:var(--muted);font-size:.8rem">'
                f'graph evidence — favoured by {n_r} linked sensor reading(s): </span>{chips}</div>',
                unsafe_allow_html=True)

        st.markdown(theme.pill(exp.get("narration_mode", "mock"),
                               f"agronomist narration · {exp.get('narration_mode','mock')} · "
                               f"graph backend {exp.get('backend','memory')}"), unsafe_allow_html=True)
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
                          "The disease/pest and its neighbours in the knowledge graph.", "shield")
            if tgt.get("id"):
                render_kg(kg_subgraph(services, tgt["id"]))
            else:
                st.caption("No graph target for this alert.")

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

    st.divider()
    theme.section("Ask the agent — it plans its own graph queries",
                  "Type a question. The AGENT decides which knowledge-graph tools (and Cypher) to "
                  "run, step by step, and shows the reasoning trace — not a single canned query.", "spark")
    aq = st.text_input("Ask the agronomist agent",
                       "What's my main disease risk now and the cheapest safe treatment?",
                       key="agentic_q")
    if st.button("Run the agent", key="agentic_run", type="primary"):
        with st.spinner("Agent planning graph queries…"):
            st.session_state.agentic = agentic_answer(services, gh_id, aq)
    ag = st.session_state.get("agentic")
    if ag:
        st.markdown(theme.pill(ag["mode"], f"agent planner · {ag['mode']} · {len(ag['trace'])} steps · "
                               f"tools: {', '.join(dict.fromkeys(ag['tools_used'])) or '—'}"),
                    unsafe_allow_html=True)
        st.markdown("**Decision trace** — the tools the agent chose, in order")
        st.markdown(theme.decision_trace(ag["trace"]), unsafe_allow_html=True)
        _ans = (ag.get("answer") or "").replace("**", "").replace("*", "")
        st.markdown(f"<div class='aw-card' style='margin-top:8px'><b>Answer.</b> {html.escape(_ans)}</div>",
                    unsafe_allow_html=True)


def render_coop_triage() -> None:
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
    _can_live = bool(getattr(settings, "onchain_live", lambda: False)())
    live_oc = st.checkbox("Commit the Decision-Log LIVE on-chain this run (real preprod tx, ~20s)",
                          value=False, key="masumi_live", disabled=not _can_live,
                          help=("Requires a funded wallet + Blockfrost + MASUMI_ONCHAIN_LIVE=1."
                                if not _can_live else
                                "Submits a fresh, verifiable Cardano preprod transaction now."))
    if st.button("Pay & deliver via Masumi", type="primary", key="masumi_pay"):
        with st.spinner("Discovering agent → escrow payment → deliver advisory → audit…"):
            trip, mode = masumi_round_trip(services, rep, live_onchain=bool(live_oc))
            st.session_state.masumi = (trip, mode, rep.greenhouse_id)
    m = st.session_state.get("masumi")
    if m and m[2] == rep.greenhouse_id:
        render_masumi(m[0], m[1])

        st.divider()
        theme.section("Agent-to-agent — the advisory agent hires a second agent",
                      "To complete the plan, the Advisory Agent itself becomes a buyer on Masumi: it "
                      "hires the AgroInput Price Agent to source the recommended product's price — "
                      "agent-to-agent coordination, not just human→agent.", "link")
        if st.button("Run agent-to-agent (source the input price)", key="a2a_run"):
            with st.spinner("Advisory agent discovering & paying the Price Agent…"):
                st.session_state.a2a = (advisory_a2a(services, rep), rep.greenhouse_id)
        a2a = st.session_state.get("a2a")
        if a2a and a2a[1] == rep.greenhouse_id and a2a[0]:
            q = a2a[0]["quote"]
            theme.kpis([
                {"label": "Product", "value": q["product"], "icon": "leaf", "tone": "fill",
                 "sub": f"for {q['treatment']}"},
                {"label": "Price", "value": f"KES {q['price_kes']:,}" if q["price_kes"] else "—",
                 "icon": "bank", "sub": q["pack_size"]},
                {"label": "Supplier", "value": q["supplier"], "icon": "shield",
                 "sub": f"{q['availability']} · {q['lead_time_days']}d"},
            ])
            st.markdown(theme.pill(a2a[0]["mode"], f"agent-to-agent · {a2a[0]['mode']}"),
                        unsafe_allow_html=True)
            st.markdown(f"<div class='aw-card'>{theme.stepper(a2a[0]['subtrip']['steps'])}</div>",
                        unsafe_allow_html=True)

        st.divider()
        theme.section("Discoverable on Sokosumi (the Masumi marketplace)",
                      "Sokosumi is where businesses discover & hire AI coworkers. Below is a LIVE "
                      "call to the marketplace + the Angawatch coworker ready to list.", "link")
        if "soko" not in st.session_state:
            with st.spinner("Connecting to the Sokosumi marketplace…"):
                st.session_state.soko = sokosumi_marketplace(services)
        soko = st.session_state.soko
        st.markdown(theme.pill(soko["mode"], f"Sokosumi · {soko['mode']} · "
                               f"{soko['marketplace_count']} coworkers discoverable"),
                    unsafe_allow_html=True)
        if soko["marketplace"]:
            scols = st.columns(2)
            for i, agc in enumerate(soko["marketplace"][:6]):
                cred = f"{agc['credits']} credits" if agc.get("credits") is not None else "—"
                scols[i % 2].markdown(
                    f"<div class='aw-tag tt' style='display:inline-block;margin:3px 0'>"
                    f"{html.escape(str(agc['name']))}</div> "
                    f"<span style='color:var(--faint);font-size:.74rem'>{cred}</span>",
                    unsafe_allow_html=True)
        p = soko["profile"]
        st.markdown(
            f"<div class='aw-card' style='margin-top:8px'><b>Our coworker:</b> "
            f"{html.escape(p['name'])}<br><span style='color:var(--muted);font-size:.84rem'>"
            f"price {p['price']['amount']} {p['price']['unit']} · tags: "
            f"{', '.join(p['tags'])}</span></div>", unsafe_allow_html=True)
        with st.expander("How we list this coworker on Sokosumi"):
            for s in soko["listing_plan"]:
                st.markdown(f"- {s}")


def render_leaf_scan(farmer_id: str) -> None:
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


def render_phone(farmer_id: str, gh_id: str) -> None:
    theme.section("Feature-phone & offline reach",
                  "Many smallholders use basic phones in low-signal areas. The SAME risk engine "
                  "and advisory, delivered over SMS or an offline in-greenhouse box.", "activity")
    lang_label = st.radio("Language / Lugha", ["English", "Kiswahili"], horizontal=True,
                          key="phone_lang")
    lang = "sw" if lang_label == "Kiswahili" else "en"
    if st.session_state.get("_lang_for") != (farmer_id, lang):
        set_language(services, farmer_id, lang)
        st.session_state._lang_for = (farmer_id, lang)

    to_phone = getattr(services.settings, "FARMER_PHONE", None)
    pcol, ocol = st.columns(2, gap="large")
    with pcol:
        st.markdown("**Two-way SMS** — the farmer texts the Angawatch number (no smartphone/data)")
        if _smode("at_mode") == "live" and to_phone:
            st.caption(f"📲 Each keyword sends the reply as a **real SMS** to {to_phone} via "
                       "Africa's Talking (and WhatsApp when in session). Each send costs ~KES 0.8.")
        else:
            st.caption("🟠 Simulated here (drives the real engine + advisory). Add Africa's Talking "
                       "creds to deliver the reply as a real SMS to the farmer's phone.")

        def _send(text):
            r = sms_reply(services, farmer_id, text)
            th = st.session_state.setdefault("sms_thread", [])
            th.append((farmer_id, "out", text))
            th.append(("Angawatch", "in", r["reply"]))
            if to_phone:                       # actually deliver the reply to the phone
                st.session_state.sms_delivery = (send_text(services, to_phone, r["reply"], gh_id),
                                                 to_phone)

        kcols = st.columns(4)
        for col, (kw, lbl) in zip(kcols, [("STATUS", "Status"), ("ADVICE", "Advice"),
                                          ("ALERTS", "Subscribe"), ("HELP", "Help")]):
            if col.button(lbl, key=f"sms_{kw}", use_container_width=True):
                _send(kw)
        custom = st.text_input("…or type a keyword (STATUS / USHAURI / SW / EN / STOP)", key="sms_in")
        if st.button("Send SMS", key="sms_send") and custom.strip():
            _send(custom.strip())

        deliv = st.session_state.get("sms_delivery")
        if deliv:
            d, to = deliv
            if d["mode"] == "live":
                st.success(f"📲 Reply delivered to {to} — LIVE via {d['provider']} · {d['detail']}")
            else:
                st.caption(f"🟠 Reply simulated (no live channel) — would go to {to}")

        thread = st.session_state.get("sms_thread", [])
        if thread:
            st.markdown(theme.sms_thread(thread[-8:]), unsafe_allow_html=True)
        else:
            st.caption("Tap a keyword above — the farmer's SMS reply is generated by the live engine.")

    with ocol:
        st.markdown("**Offline alert box** — ESP-NOW node in the greenhouse, **no internet**")
        box = offline_box(services, gh_id, lang)
        st.markdown(theme.offline_device(box), unsafe_allow_html=True)
        st.caption("When there's no cell signal, the sensor node radios the alert to this in-house "
                   "box (OLED + LED + buzzer). It caches readings and syncs to /ingest when a "
                   "signal returns (store-and-forward).")
        st.info("🛰️ Hardware path (real seam): ESP32 + 7-in-1 soil sensor + DHT22 + GSM → "
                "POST /ingest. See docs for the BOM + connectivity ladder.")


# ============================================================ SIDEBAR ========
role = st.session_state.get("role")
sb_flow = None
farmer_id, gh_id, county = "Farmer-A", "gh-001", "Nakuru"

with st.sidebar:
    st.markdown(f"### {theme.icon('leaf',18)} Angawatch", unsafe_allow_html=True)
    if role:
        st.markdown(theme.pill("real" if role == "coop" else "live",
                               ("Cooperative view" if role == "coop" else "Farmer view")),
                    unsafe_allow_html=True)
        if st.button("↺ Switch role", use_container_width=True, key="switch_role"):
            st.session_state.role = None
            st.rerun()
        st.divider()
        if role == "coop":
            farmer_id = st.selectbox("Member greenhouse", list(FARMERS), index=0)
            gh_id, county = FARMERS[farmer_id]
            st.markdown(f"<span class='aw-hash'>greenhouse {gh_id} · {county}</span>",
                        unsafe_allow_html=True)
        else:
            farmer_id, (gh_id, county) = "Farmer-A", FARMERS["Farmer-A"]
            st.markdown(f"<span class='aw-hash'>your greenhouse {gh_id} · {county}</span>",
                        unsafe_allow_html=True)
        st.divider()
        st.markdown("**Demo flow** — what to do")
        sb_flow = st.container()
        st.divider()
        _mpill = theme.pill("real" if getattr(settings, "MASUMI_PRERECORDED_TX", None) else "mock",
                            "Masumi · on-chain proof ✓" if getattr(settings, "MASUMI_PRERECORDED_TX", None)
                            else "Masumi · mock")
        st.markdown(
            f"**Live status**<br>"
            f"{theme.pill(services.store.mode,'Graph · '+services.store.mode)}<br>"
            f"{theme.pill(_smode('alert_mode'),'WhatsApp · '+_smode('alert_mode'))}<br>"
            f"{theme.pill(_smode('at_mode'),'SMS · '+_smode('at_mode'))}<br>"
            f"{theme.pill(settings.llm_mode(),'LLM · '+settings.llm_mode())}<br>{_mpill}",
            unsafe_allow_html=True)
        with st.expander("🔎 Integration check"):
            _set = lambda n: "✓ set" if getattr(settings, n, None) else "✗ MISSING"
            st.markdown(
                f"- SMS (Africa's Talking): **{_smode('at_mode')}**\n"
                f"- `AT_USERNAME`: {_set('AT_USERNAME')}\n"
                f"- `AT_API_KEY`: {_set('AT_API_KEY')}\n"
                f"- `FARMER_PHONE`: `{settings.FARMER_PHONE or '✗ MISSING'}`\n"
                f"- WhatsApp (Twilio): **{_smode('alert_mode')}**")
            if _smode("at_mode") != "live":
                st.caption("SMS is mock → AT_USERNAME and AT_API_KEY must BOTH be present in "
                           "secrets. If one says ✗ MISSING, add it and Save.")
        st.divider()
        if st.button("↺ Reset demo", use_container_width=True, key="reset"):
            for _k in ("last_run", "kg_exp", "kg_for", "coop_rep", "coop_rep_key", "masumi",
                       "a2a", "advice", "agentic", "sms_thread", "warmed"):
                st.session_state.pop(_k, None)
            st.rerun()
        st.caption("Mocks are labeled 🟠 — nothing here hides a mock.")
    else:
        st.caption("Choose a role on the right to begin →")

# ---- role gate: landing first, every load ----------------------------------
if not role:
    render_landing()
    st.stop()

if "warmed" not in st.session_state:
    calm_ticks(services, gh_id, n=4)
    st.session_state.warmed = True

# ---- top role switch (one tap to flip Co-op <-> Farmer, no sidebar needed) ---
_other, _other_label = (("coop", "Co-op view") if role == "farmer"
                        else ("farmer", "Farmer view"))
_now_label = "Farmer view" if role == "farmer" else "Co-op view"
_sw_l, _sw_r = st.columns([5, 2])
with _sw_l:
    st.markdown(f"<div style='padding-top:6px'>{theme.pill('live' if role=='farmer' else 'real', _now_label)}"
                f" <span style='color:var(--faint);font-size:.8rem'>you're viewing as</span></div>",
                unsafe_allow_html=True)
with _sw_r:
    if st.button(f"⇄  Switch to {_other_label}", key="top_switch", use_container_width=True):
        st.session_state.role = _other
        st.rerun()

# ---------------------------------------------------------------- topbar -----
if role == "farmer":
    theme.topbar("My greenhouse",
                 "Angawatch — your crop is watched day and night; you get a simple alert in time to act.")
else:
    theme.topbar("Co-op console",
                 "Triage your contracted greenhouses, diagnose by knowledge graph, and hire the "
                 "advisory agent via Masumi.")

# ---- primary navigation: only the tabs this role needs ----------------------
if role == "farmer":
    t_green, t_leaf, t_phone = st.tabs(["🌡️  My greenhouse", "🍃  Leaf scan", "📱  My phone"])
    with t_green:
        render_my_greenhouse(gh_id, county, farmer_id)
    with t_leaf:
        render_leaf_scan(farmer_id)
    with t_phone:
        render_phone(farmer_id, gh_id)
else:
    t_triage, t_doctor, t_record, t_leaf = st.tabs(
        ["🤝  Farm triage & hire", "🧠  Crop doctor (GraphRAG)", "🛡️  Verified record",
         "🍃  Leaf scan"])
    with t_triage:
        render_coop_triage()
    with t_doctor:
        render_crop_doctor(gh_id)
    with t_record:
        render_verified_record(farmer_id, gh_id)
    with t_leaf:
        render_leaf_scan(farmer_id)

# ---------------------------------------------- guided progress + footer -----
_has_alert = bool((st.session_state.get("last_run") or []) and
                  any(r.get("alert") for r in st.session_state["last_run"]))
if role == "farmer":
    _flow = [("Live conditions", "done"),
             ("Blight alert fires", "done" if _has_alert else "active"),
             ("Advice on your phone", "active" if _has_alert else "")]
else:
    _has_doctor = bool(st.session_state.get("kg_exp"))
    _has_advisory = bool(st.session_state.get("coop_rep"))
    _has_masumi = bool(st.session_state.get("masumi"))
    _flow = [
        ("Triage the farms", "done"),
        ("GraphRAG diagnosis", "done" if _has_doctor else "active"),
        ("Verified advisory", "done" if _has_advisory else ("active" if _has_doctor else "")),
        ("Hire & audit (Masumi)", "done" if _has_masumi else ("active" if _has_advisory else "")),
    ]
if sb_flow is not None:
    with sb_flow:
        try:
            theme.flow_steps(_flow, vertical=True)
        except TypeError:
            theme.flow_steps(_flow)
theme.footer()
