"""Unit tests for the Crop-Health Advisory Agent + report (the hireable deliverable)."""
import os

os.environ["GRAPH_BACKEND"] = "memory"
os.environ["LLM_MODE"] = "mock"

from agents.advisory import AdvisoryAgent  # noqa: E402
from config import get_settings  # noqa: E402
from graph.memory_store import InMemoryGraphStore  # noqa: E402
from graph.seed import ensure_seeded  # noqa: E402


def _store():
    s = InMemoryGraphStore()
    ensure_seeded(s)
    return s


def test_report_has_diagnosis_plan_and_priority():
    s = _store()
    rep = AdvisoryAgent(get_settings()).report(s, "gh-001", farm_id="Farmer-A",
                                               risk_level="HIGH")
    assert rep.diagnosis and rep.diagnosis != "No active disease detected"
    assert rep.recommended_actions                      # ranked treatment plan
    assert rep.priority.startswith("Visit now")         # HIGH -> visit now
    assert rep.limits                                   # human-in-the-loop limits present
    assert len(rep.result_hash) == 64                   # commits to diagnosis + plan


def test_result_hash_is_deterministic_and_excludes_prose():
    s = _store()
    agent = AdvisoryAgent(get_settings())
    h1 = agent.report(s, "gh-001", risk_level="HIGH").result_hash
    h2 = agent.report(s, "gh-001", risk_level="HIGH").result_hash
    assert h1 == h2 and len(h1) == 64


def test_priority_tracks_risk_level():
    s = _store()
    agent = AdvisoryAgent(get_settings())
    assert agent.report(s, "gh-001", risk_level="LOW").priority_rank == 2
    assert agent.report(s, "gh-001", risk_level="HIGH").priority_rank == 0


def test_narrate_false_skips_llm_path():
    s = _store()
    rep = AdvisoryAgent(get_settings()).report(s, "gh-001", risk_level="HIGH", narrate=False)
    assert rep.narration_mode == "mock"      # template only, no live call
    assert rep.narrative
