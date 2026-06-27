"""Shared state for the Streamlit dashboard.

Loads Streamlit secrets into the environment, builds ONE Services per session
(stateful simulator), and exposes the same calls the CLI demo uses, so both
surfaces behave identically.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# The @st.cache_resource singletons live in a STABLE module so they survive app.py's
# hot-reload force-refresh of this module (signature changes here must never crash the
# deployed app, and must never rebuild the cached Services / Neo4j connection).
from dashboard.services_cache import (_masumi_client,  # noqa: E402,F401
                                      get_services)


def inject_and_run(services, gh_id: str, ticks: int = 9, lang: str = "en") -> list[dict]:
    """Inject a blight event then stream ticks; return the per-tick risk results.
    The fired alert carries a simple, action-first farmer message (in `lang`)."""
    services.inject(gh_id, "late_blight", ticks=ticks + 2)
    out = []
    for _ in range(ticks):
        try:
            res = services.tick_and_ingest(gh_id, lang=lang)
        except TypeError:
            # stale cached Services (built before the lang param) — reboot to apply language
            res = services.tick_and_ingest(gh_id)
        out.append(res)
        if res.get("alert") and res["alert"]["level"] == "HIGH":
            break
    return out


def calm_ticks(services, gh_id: str, n: int = 3) -> list[dict]:
    return [services.tick_and_ingest(gh_id) for _ in range(n)]


def advisory_report(services, gh_id: str, requested_by: str | None = None,
                    risk_level: str | None = None, farm_id: str | None = None,
                    narrate: bool = True):
    """The Crop-Health Advisory Agent's deliverable for one greenhouse."""
    from agents.advisory import AdvisoryAgent
    if risk_level is None:
        try:
            risk_level = services.engine.evaluate(gh_id).top.level
        except Exception:  # noqa: BLE001
            risk_level = None
    return AdvisoryAgent(services.settings).report(
        services.store, gh_id, requested_by=requested_by, risk_level=risk_level,
        farm_id=farm_id, narrate=narrate)


def coop_triage(services, farms: list[tuple]) -> list[dict]:
    """Portfolio view for the co-op: a report per greenhouse, sorted by visit priority.
    farms: list of (farmer_id, gh_id, county). Template-only (no LLM) so it's fast."""
    from agents.advisory import AdvisoryAgent
    agent = AdvisoryAgent(services.settings)
    out = []
    for farmer_id, gh_id, county in farms:
        try:
            lvl = services.engine.evaluate(gh_id).top.level
        except Exception:  # noqa: BLE001
            lvl = None
        rep = agent.report(services.store, gh_id, risk_level=lvl, farm_id=farmer_id, narrate=False)
        out.append({"farmer_id": farmer_id, "gh_id": gh_id, "county": county, "report": rep})
    out.sort(key=lambda x: x["report"].priority_rank)
    return out


def masumi_round_trip(services, report, live_onchain: bool = False):
    client = _masumi_client(services.settings)
    trip = client.run_round_trip(report, store=services.store, live_onchain=live_onchain)
    return trip, client.mode


def sokosumi_marketplace(services) -> dict:
    """LIVE Sokosumi marketplace discovery (the +10 coworker bonus evidence)."""
    from masumi_integration.sokosumi import sokosumi_status
    return sokosumi_status(services.settings)


def advisory_a2a(services, report):
    """Agent-to-agent: the advisory agent hires the AgroInput Price Agent over Masumi."""
    from agents.input_price import PROFILE, AgroInputPriceAgent
    q = AgroInputPriceAgent().quote_for_report(report)
    if not q:
        return None
    client = _masumi_client(services.settings)
    sub = client.hire_agent(
        PROFILE["name"], PROFILE["description"],
        input_data={"treatment_id": q["treatment_id"], "region": "Nakuru"},
        result_hash=q["result_hash"])
    return {"quote": q, "subtrip": sub, "mode": client.mode}


def classify_leaf(services, uploaded_or_path):
    import os
    import tempfile

    from vision.classifier import classify
    if hasattr(uploaded_or_path, "getvalue"):
        suffix = os.path.splitext(getattr(uploaded_or_path, "name", "leaf.png"))[1] or ".png"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(uploaded_or_path.getvalue())
        tmp.close()
        return classify(tmp.name, services.settings)
    return classify(str(uploaded_or_path), services.settings)


def advisory_answer(services, farmer_id: str, question: str) -> dict:
    from agents.advisory_crew import answer
    return answer(services.settings, services.store, farmer_id, question)


def agronomist_explain(services, gh_id: str):
    """GraphRAG: explain the greenhouse's latest alert by traversing the KG."""
    from agents.agronomist import AgronomistAgent
    alerts = services.store.list_alerts(gh_id, limit=1)
    if not alerts:
        return None
    return AgronomistAgent(services.settings).explain_alert(services.store, alerts[0]["id"])


def agronomist_diagnose(services, gh_id: str) -> dict:
    """GraphRAG: diagnose likely diseases from the greenhouse's current conditions."""
    from agents.agronomist import AgronomistAgent
    return AgronomistAgent(services.settings).diagnose(services.store, gh_id)


def kg_subgraph(services, disease_id: str) -> dict:
    from graph.kg import kg_subgraph as _kg
    return _kg(services.store, disease_id)


def agentic_answer(services, gh_id: str, question: str) -> dict:
    """The agronomist AGENT plans which graph tools to call; returns the decision trace."""
    from agents.agentic import AgenticAgronomist
    return AgenticAgronomist(services.settings).answer(services.store, gh_id, question)


def set_language(services, farmer_id: str, lang: str) -> None:
    # getattr-guard so a Streamlit hot-reload with a cached old store module
    # (no update_farmer yet) degrades gracefully instead of crashing the app
    upd = getattr(services.store, "update_farmer", None)
    if callable(upd):
        try:
            upd(farmer_id, language=lang)
        except Exception:  # noqa: BLE001
            pass


def sms_reply(services, farmer_id: str, text: str) -> dict:
    from comms.sms import handle_inbound
    return handle_inbound(services, farmer_id, text)


def send_text(services, to: str, text: str, gh_id: str = "gh-001") -> dict:
    """Actually DELIVER an arbitrary message body to a phone via the configured channel
    (Africa's Talking SMS + Twilio WhatsApp). Used so the feature-phone tab sends a real
    SMS on a keyword press. Never raises into the UI; in mock mode it logs to console."""
    from datetime import datetime
    from alerts.channel import Alert
    try:
        alert = Alert(gh_id=gh_id, kind="sms_reply", level="INFO", message=text,
                      ts=datetime.now().isoformat(), channel="sms")
        res = services.channel.send(to, alert)
        return {"ok": res.ok, "mode": res.mode, "provider": res.provider, "detail": res.detail}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "mode": "mock", "provider": "console", "detail": str(exc)}


def offline_box(services, gh_id: str, lang: str) -> dict:
    from comms.offline_box import box_for_greenhouse
    return box_for_greenhouse(services, gh_id, lang)
