"""Unit tests for the deterministic credit scorer."""
import pytest

from graph.memory_store import InMemoryGraphStore
from graph.seed import ensure_seeded
from scoring.scorer import CreditScorer


@pytest.fixture(scope="module")
def store():
    s = InMemoryGraphStore()
    ensure_seeded(s)
    return s


def test_hero_farmer_is_band_a(store):
    a = CreditScorer().score_farmer(store, "Farmer-A")
    assert a.overall_score >= 75
    assert a.credit["grade"] == "A"
    assert a.confidence["level"] in ("medium", "high")


def test_thin_file_farmer_is_weak(store):
    a = CreditScorer().score_farmer(store, "Farmer-B")
    assert a.overall_score < 60
    assert a.confidence["level"] == "low"           # 1 season only


def test_contributions_sum_to_overall(store):
    a = CreditScorer().score_farmer(store, "Farmer-A")
    assert abs(sum(f.contribution for f in a.factors) - a.overall_score) < 0.2


def test_seven_factors_and_limits(store):
    a = CreditScorer().score_farmer(store, "Farmer-A")
    assert len(a.factors) == 7
    assert a.limits and any("loan officer" in s.lower() for s in a.limits)


def test_result_hash_is_deterministic(store):
    h1 = CreditScorer().score_farmer(store, "Farmer-A").result_hash
    h2 = CreditScorer().score_farmer(store, "Farmer-A").result_hash
    assert h1 == h2 and len(h1) == 64


def test_alert_response_reflects_graph(store):
    a = CreditScorer().score_farmer(store, "Farmer-A")
    resp = next(f for f in a.factors if f.name == "alert_response_rate")
    assert resp.evidence["alerts"] == 3 and resp.evidence["actioned"] == 2
