"""Stable cache module — holds the @st.cache_resource singletons (Services, Masumi
client) so they SURVIVE the hot-reload force-refresh that app.py applies to
dashboard.state / theme / components.

Streamlit Cloud hot-reloads app.py but not changed sub-modules, so app.py drops the
fast-changing presentation/logic modules from sys.modules each run to avoid stale-cache
crashes. This module is deliberately NOT in that list: the cache_resource function
identities stay stable, so the cached Services (and the live Neo4j connection + seeded
graph) are built once and reused — never rebuilt per rerun.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _load_secrets_into_env() -> None:
    """Copy flat Streamlit secrets (NEO4J_URI, OPENROUTER_API_KEY, ...) into env.

    st.secrets is AUTHORITATIVE on the cloud: OVERWRITE so a secrets change actually
    propagates (the old code skipped keys already set, which pinned stale values)."""
    try:
        for key, value in st.secrets.items():
            if isinstance(value, (str, int, float, bool)):
                os.environ[key] = str(value)
    except Exception:  # noqa: BLE001  (no secrets file -> fine, run as mock)
        pass


def _env_version() -> str:
    """Hash the env values that pick modes/targets, so the cached Services REBUILDS when
    secrets change. Streamlit reboots on a secrets save but keeps @st.cache_resource keyed
    on source; without this a secrets-only change (e.g. adding AT creds, new FARMER_PHONE)
    would never take effect — the stale Services would keep serving."""
    import hashlib
    keys = ("NEO4J_URI", "NEO4J_PASSWORD", "GRAPH_BACKEND", "OPENROUTER_API_KEY", "LLM_MODE",
            "TWILIO_SID", "TWILIO_TOKEN", "TWILIO_FROM", "FARMER_PHONE", "AT_USERNAME",
            "AT_API_KEY", "AT_SENDER_ID", "AT_SANDBOX", "MASUMI_MODE", "MASUMI_PRERECORDED_TX",
            "SOKOSUMI_API_KEY", "VISION_MODE")
    h = hashlib.sha256()
    for k in keys:
        h.update(f"{k}={os.environ.get(k, '')}\n".encode())
    return h.hexdigest()[:12]


# The cached Services holds the Neo4j connection so it can't be hot-refreshed — but that
# means a SIGNATURE change to a Services method (e.g. tick_and_ingest gaining a param) would
# crash against the stale instance until a manual reboot. To self-heal: key the cache on a
# hash of the services-layer source, so the Services rebuilds automatically when that code
# changes, and persists (one build) otherwise.
def _src_version() -> str:
    import hashlib
    root = Path(__file__).resolve().parents[1]
    h = hashlib.sha256()
    for rel in ("services.py", "config.py", "graph/store.py", "graph/seed.py",
                "graph/memory_store.py", "risk/engine.py", "sim/generator.py",
                "alerts/dispatcher.py"):
        try:
            h.update((root / rel).read_bytes())
        except Exception:  # noqa: BLE001
            pass
    return h.hexdigest()[:12]


@st.cache_resource(show_spinner=False)
def _build(_version: str, _env: str):
    from config import get_settings
    get_settings.cache_clear()           # re-read the (now-updated) environment
    from services import build_services
    settings = get_settings()
    return build_services(settings)


def get_services():
    _load_secrets_into_env()             # load FIRST so the env hash reflects current secrets
    return _build(_src_version(), _env_version())


def _masumi_client(settings):
    # NOT cached: the client is cheap (no connection) and caching the instance would
    # pin stale masumi_integration code across a Streamlit hot-reload. Build fresh so it
    # always uses the current client/backends (the round-trip stays deterministic).
    from masumi_integration.client import build_masumi_client
    return build_masumi_client(settings)
