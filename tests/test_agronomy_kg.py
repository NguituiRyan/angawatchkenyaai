"""Unit tests for the agronomic knowledge graph + GraphRAG agronomist (memory store)."""
import os

os.environ["GRAPH_BACKEND"] = "memory"
os.environ["LLM_MODE"] = "mock"

from agents.agronomist import AgronomistAgent  # noqa: E402
from config import get_settings  # noqa: E402
from graph import kg  # noqa: E402
from graph.memory_store import InMemoryGraphStore  # noqa: E402
from graph.seed import ensure_seeded  # noqa: E402


def _store():
    s = InMemoryGraphStore()
    ensure_seeded(s)
    return s


def test_treatments_ranked_and_phi_aware():
    s = _store()
    ts = kg.treatments_for(s, "Disease", "late_blight")
    names = [t["name"] for t in ts]
    assert "Dimethomorph" in names and "Mancozeb" in names
    # cultural/cheap high-efficacy controls outrank expensive chemicals
    assert ts[0]["type"] == "cultural"
    # every treatment carries the attributes the agent reasons over
    assert all("phi_days" in t and "edge_efficacy" in t for t in ts)


def test_explain_alert_walks_disease_pathogen_treatment():
    s = _store()
    aid = s.list_alerts("gh-001", limit=5)[0]["id"]
    path = AgronomistAgent(get_settings()).explain_alert(s, aid)
    assert path["disease"]["name"]
    assert path["pathogen"]                       # Disease -[:CAUSED_BY]-> Pathogen
    assert path["treatments"]                     # Disease <-[:CONTROLS]- Treatment
    assert path["narrative"]                      # grounded narration
    assert "MATCH" in path["cypher"]              # shows-thinking artifact


def test_beneficial_safety_warning_present():
    s = _store()
    # abamectin controls red spider mite AND is harmful to honeybee -> warning surfaces
    ts = kg.treatments_for(s, "Pest", "red_spider_mite")
    abam = next(t for t in ts if t["name"] == "Abamectin")
    assert "Honey bee (pollinator)" in abam["harmful_to"]


def test_diagnose_from_conditions():
    s = _store()
    d = AgronomistAgent(get_settings()).diagnose(s, "gh-001")
    assert d["conditions"]                        # readings -> indicated conditions
    assert d["diseases"]                          # conditions -> likely diseases
    assert all(dz["via"] for dz in d["diseases"])  # each disease cites the conditions
