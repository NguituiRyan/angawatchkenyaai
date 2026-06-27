"""Headless smoke test: run the Streamlit app in-process and click the key
buttons, asserting no exception is raised (catches render/runtime errors).

Forced to in-memory + mock so the suite is fast, deterministic, and never writes
to a live Aura instance even when .env has real creds.
"""
import os

os.environ["GRAPH_BACKEND"] = "memory"
os.environ["VISION_MODE"] = "mock"
os.environ["MASUMI_MODE"] = "mock"
os.environ["LLM_MODE"] = "mock"

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = "dashboard/app.py"


def _run():
    at = AppTest.from_file(APP, default_timeout=90)
    at.run()
    return at


def test_app_boots_without_exception():
    at = _run()
    assert not at.exception, at.exception


def test_inject_blight_button():
    at = _run()
    at.button(key="inject").click().run()
    assert not at.exception, at.exception


def test_coop_triage_and_masumi():
    at = _run()
    # the Co-op triage tab renders the portfolio + a verified report automatically;
    # hiring the agent via Masumi must not raise
    at.button(key="masumi_pay").click().run()
    assert not at.exception, at.exception
    # the agent-to-agent button appears after the round-trip renders
    if any(b.key == "a2a_run" for b in at.button):
        at.button(key="a2a_run").click().run()
        assert not at.exception, at.exception


def test_leaf_scan_and_advisor():
    at = _run()
    at.button(key="sample_leaf").click().run()
    assert not at.exception, at.exception
    at.button(key="ask").click().run()
    assert not at.exception, at.exception


def test_feature_phone_sms_and_box():
    at = _run()
    at.button(key="sms_STATUS").click().run()
    assert not at.exception, at.exception
    at.button(key="sms_ADVICE").click().run()
    assert not at.exception, at.exception


def test_crop_doctor_graphrag():
    at = _run()
    # the Crop-doctor tab auto-runs explain on load; exercise the buttons too
    at.button(key="kg_explain").click().run()
    assert not at.exception, at.exception
    at.button(key="kg_diag_btn").click().run()
    assert not at.exception, at.exception
    at.button(key="agentic_run").click().run()   # the agentic decision-trace panel
    assert not at.exception, at.exception
