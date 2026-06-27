"""Headless smoke test: run the Streamlit app in-process and click the key buttons,
asserting no exception (catches render/runtime errors).

The app is role-gated (a landing page with Farmer / Co-op). Tests pre-set the role in
session_state to land directly in that role's dashboard. Forced to in-memory + mock so
the suite is fast, deterministic, and never touches live Aura / Twilio / Sokosumi.
"""
import os

os.environ["GRAPH_BACKEND"] = "memory"
os.environ["VISION_MODE"] = "mock"
os.environ["MASUMI_MODE"] = "mock"
os.environ["LLM_MODE"] = "mock"
os.environ["SOKOSUMI_API_KEY"] = ""
os.environ["TWILIO_SID"] = ""
os.environ["TWILIO_TOKEN"] = ""

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = "dashboard/app.py"


def _run(role: str | None = None):
    at = AppTest.from_file(APP, default_timeout=120)
    if role:
        at.session_state["role"] = role          # skip the landing, land in the role
    at.run()
    return at


def test_landing_boots_without_exception():
    at = _run()                                   # no role -> landing page
    assert not at.exception, at.exception


def test_pick_farmer_role():
    at = _run()
    at.button(key="role_farmer").click().run()    # the landing gate works
    assert not at.exception, at.exception


def test_farmer_inject_blight():
    at = _run("farmer")
    at.button(key="inject").click().run()
    assert not at.exception, at.exception


def test_farmer_feature_phone():
    at = _run("farmer")
    at.button(key="sms_STATUS").click().run()
    assert not at.exception, at.exception
    at.button(key="sms_ADVICE").click().run()
    assert not at.exception, at.exception


def test_coop_crop_doctor_graphrag():
    at = _run("coop")
    at.button(key="kg_explain").click().run()
    assert not at.exception, at.exception
    at.button(key="kg_diag_btn").click().run()
    assert not at.exception, at.exception
    at.button(key="agentic_run").click().run()
    assert not at.exception, at.exception


def test_coop_triage_and_masumi():
    at = _run("coop")
    at.button(key="masumi_pay").click().run()
    assert not at.exception, at.exception
    if any(b.key == "a2a_run" for b in at.button):
        at.button(key="a2a_run").click().run()
        assert not at.exception, at.exception


def test_leaf_scan_and_advisor():
    at = _run("coop")
    at.button(key="sample_leaf").click().run()
    assert not at.exception, at.exception
    at.button(key="ask").click().run()
    assert not at.exception, at.exception
