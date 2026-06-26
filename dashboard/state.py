"""Shared state for the Streamlit dashboard.

Loads Streamlit secrets into the environment, builds ONE Services per session
(stateful simulator), and exposes the same calls the CLI demo uses, so both
surfaces behave identically.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _load_secrets_into_env() -> None:
    """Copy flat Streamlit secrets (NEO4J_URI, OPENROUTER_API_KEY, ...) into env."""
    try:
        for key, value in st.secrets.items():
            if isinstance(value, (str, int, float, bool)) and not os.environ.get(key):
                os.environ[key] = str(value)
    except Exception:  # noqa: BLE001  (no secrets file -> fine, run as mock)
        pass


@st.cache_resource(show_spinner=False)
def _build():
    _load_secrets_into_env()
    from config import get_settings
    get_settings.cache_clear()
    from services import build_services
    settings = get_settings()
    return build_services(settings)


def get_services():
    return _build()


def inject_and_run(services, gh_id: str, ticks: int = 9) -> list[dict]:
    """Inject a blight event then stream ticks; return the per-tick risk results."""
    services.inject(gh_id, "late_blight", ticks=ticks + 2)
    out = []
    for _ in range(ticks):
        res = services.tick_and_ingest(gh_id)
        out.append(res)
        if res.get("alert") and res["alert"]["level"] == "HIGH":
            break
    return out


def calm_ticks(services, gh_id: str, n: int = 3) -> list[dict]:
    return [services.tick_and_ingest(gh_id) for _ in range(n)]


def assess(services, farmer_id: str):
    from agents.credit_crew import CreditRiskAgent
    return CreditRiskAgent(services.settings).assess(services.store, farmer_id)


@st.cache_resource(show_spinner=False)
def _masumi_client(_settings):
    from masumi_integration.client import build_masumi_client
    return build_masumi_client(_settings)


def masumi_round_trip(services, assessment):
    client = _masumi_client(services.settings)
    return client.run_round_trip(assessment, store=services.store), client.mode


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
