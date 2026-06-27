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


def _masumi_client(settings):
    # NOT cached: the client is cheap (no connection) and caching the instance would
    # pin stale masumi_integration code across a Streamlit hot-reload. Build fresh so it
    # always uses the current client/backends (the round-trip stays deterministic).
    from masumi_integration.client import build_masumi_client
    return build_masumi_client(settings)
