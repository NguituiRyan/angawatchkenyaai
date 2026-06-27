"""Tests for the Masumi layer — round-trip, agent-to-agent, on-chain metadata, A2A price.
Covers the bounty-critical paths the assessment flagged as untested. All mock (no network)."""
import os

os.environ["GRAPH_BACKEND"] = "memory"
os.environ["LLM_MODE"] = "mock"
os.environ["MASUMI_MODE"] = "mock"

from agents.advisory import AdvisoryAgent  # noqa: E402
from agents.input_price import AgroInputPriceAgent, quote  # noqa: E402
from config import get_settings  # noqa: E402
from graph.memory_store import InMemoryGraphStore  # noqa: E402
from graph.seed import ensure_seeded  # noqa: E402
from masumi_integration.client import build_masumi_client  # noqa: E402
from masumi_integration.onchain import META_LABEL, decision_metadata  # noqa: E402


def _report():
    s = InMemoryGraphStore()
    ensure_seeded(s)
    return s, AdvisoryAgent(get_settings()).report(s, "gh-001", farm_id="Farmer-A", risk_level="HIGH")


def test_round_trip_commits_result_hash():
    s, rep = _report()
    client = build_masumi_client(get_settings())
    trip = client.run_round_trip(rep, store=s)
    assert len(trip["steps"]) == 5
    assert trip["audit"].result_hash == rep.result_hash      # the diagnosis hash is what's logged
    # the audit record was written ABOUT the farmer in the graph
    assert any(a.get("result_hash") == rep.result_hash for a in s.audits)


def test_round_trip_does_not_crash_without_onchain():
    s, rep = _report()
    client = build_masumi_client(get_settings())
    trip = client.run_round_trip(rep, store=s, live_onchain=True)   # no wallet -> falls back
    assert trip["onchain"] is None and len(trip["steps"]) == 5


def test_agent_to_agent_hire():
    _, rep = _report()
    client = build_masumi_client(get_settings())
    q = AgroInputPriceAgent().quote_for_report(rep)
    assert q and q["product"] and len(q["result_hash"]) == 64
    sub = client.hire_agent("Angawatch AgroInput Price Agent", "price agent",
                            {"treatment_id": q["treatment_id"]}, q["result_hash"])
    assert len(sub["steps"]) == 4 and sub["audit"].result_hash == q["result_hash"]


def test_input_price_quote_is_deterministic():
    t = {"id": "mancozeb", "name": "Mancozeb", "cost_kes": 3000, "type": "chemical"}
    assert quote(t)["result_hash"] == quote(t)["result_hash"]
    assert quote(t)["price_kes"] >= 3000     # dealer markup applied


def test_onchain_metadata_shape_and_caps():
    meta = decision_metadata("h" * 80, "agent_x", "gh-001", "Late blight", "Visit now")
    assert meta["type"] == "advisory-decision-log"
    assert meta["result_hash"] == "h" * 64   # 64-byte Cardano cap enforced
    assert META_LABEL == 8434


def test_onchain_live_disabled_by_default():
    assert get_settings().onchain_live() is False
