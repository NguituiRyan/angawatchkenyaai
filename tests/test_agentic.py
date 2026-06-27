"""Tests for the agentic agronomist — question-aware tool selection + decision trace."""
import os

os.environ["GRAPH_BACKEND"] = "memory"
os.environ["LLM_MODE"] = "mock"

from agents.agentic import AgenticAgronomist  # noqa: E402
from agents import graph_tools as gt  # noqa: E402
from config import get_settings  # noqa: E402
from graph.memory_store import InMemoryGraphStore  # noqa: E402
from graph.seed import ensure_seeded  # noqa: E402


def _store():
    s = InMemoryGraphStore()
    ensure_seeded(s)
    return s


def test_multi_step_trace_with_observations():
    s = _store()
    r = AgenticAgronomist(get_settings()).answer(s, "gh-001", "Why was I warned and what do I do?")
    assert len(r["trace"]) >= 2                      # genuinely multi-step
    assert all(step["observation"] for step in r["trace"])
    assert r["answer"]
    assert "explain_latest_alert" in r["tools_used"]  # routed to the alert tool by intent


def test_tool_selection_is_question_aware():
    s = _store()
    agent = AgenticAgronomist(get_settings())
    vec = agent.answer(s, "gh-001", "Can whitefly spread a virus to my tomatoes?")
    assert "pest_vector_risk" in vec["tools_used"]
    tre = agent.answer(s, "gh-001", "What treatment for early blight?")
    assert "treatments_for" in tre["tools_used"]


def test_ask_graph_refuses_writes():
    s = _store()
    bad = gt.run_tool("ask_graph", s, get_settings(), "gh-001",
                      cypher="MATCH (d:Disease) DETACH DELETE d")
    assert "read-only" in bad["observation"].lower() or "refused" in bad["observation"].lower()


def test_tools_catalog_lists_graph_tools():
    cat = gt.tool_catalog()
    for name in ("diagnose_conditions", "explain_latest_alert", "treatments_for", "ask_graph"):
        assert name in cat
