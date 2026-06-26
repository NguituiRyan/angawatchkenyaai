"""Headless smoke test: run the Streamlit app in-process and click the key
buttons, asserting no exception is raised (catches render/runtime errors)."""
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


def test_request_assessment_and_masumi():
    at = _run()
    at.button(key="assess").click().run()
    assert not at.exception, at.exception
    at.button(key="masumi_pay").click().run()
    assert not at.exception, at.exception
