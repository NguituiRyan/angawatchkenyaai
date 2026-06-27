"""Graph TOOLS the agentic agronomist can choose from — each is a Cypher-backed
(on Neo4j) traversal over the agronomic knowledge graph, with a Python fallback for the
in-memory store. The agent decides WHICH tools to call and in what order (see agentic.py);
this module just exposes them with names + descriptions + a uniform run(ctx, **args).

Including a GUARDED, read-only `ask_graph` tool means the agent can also compose its OWN
Cypher against the known schema (text2cypher) — safely (no writes, auto-LIMIT, timeout).
"""
from __future__ import annotations

import re
from types import SimpleNamespace

from graph import agronomy as A
from graph import kg
from logging_setup import get_logger

log = get_logger("agents.graph_tools")

SCHEMA_HINT = (
    "Knowledge-graph schema (read-only):\n"
    "(:Disease {id,name,severity})-[:CAUSED_BY]->(:Pathogen {name})\n"
    "(:Disease)-[:FAVORS_REVERSE]->(:Condition {id,name})   // microclimate that favours it\n"
    "(:Disease)-[:SHOWS]->(:Symptom {name})   (:Disease)-[:AFFECTS]->(:Crop {name})\n"
    "(:Pest {id,name})-[:VECTORS]->(:Disease)   (:Pest)-[:DAMAGES]->(:Crop)\n"
    "(:Treatment {id,name,type,active,phi_days,efficacy,cost_kes})-[:CONTROLS {efficacy}]->(:Disease|:Pest)\n"
    "(:Treatment)-[:HARMFUL_TO]->(:Beneficial {name})   (:GrowthStage)-[:SUSCEPTIBLE_TO]->(:Disease)\n"
    "operational links: (:Reading)-[:INDICATES]->(:Condition), (:Alert)-[:FOR_DISEASE]->(:Disease), "
    "(:Action)-[:APPLIED]->(:Treatment)"
)

_WRITE = re.compile(r"\b(create|delete|set|merge|remove|detach|drop|load\s+csv|foreach|"
                    r"call\s*\{[^}]*\b(create|delete|set|merge)\b)", re.I)


def _ctx(store, settings, gh_id: str) -> SimpleNamespace:
    return SimpleNamespace(store=store, settings=settings, gh_id=gh_id)


def _resolve_target(name: str) -> tuple[str, str] | None:
    """Map a free-text disease/pest name to (label, id)."""
    n = (name or "").strip().lower()
    for d in A.NODES["Disease"]:
        if n == d["id"] or n in d["name"].lower() or d["name"].lower() in n:
            return ("Disease", d["id"])
    for p in A.NODES["Pest"]:
        if n == p["id"] or n in p["name"].lower() or p["name"].lower() in n:
            return ("Pest", p["id"])
    return None


# ---- tool implementations (each returns {"observation": str, "data": any}) ----
def _diagnose(ctx, **_):
    d = kg.diagnose(ctx.store, ctx.gh_id)
    if not d["diseases"]:
        return {"observation": f"No risk conditions indicated. Conditions: {d['conditions'] or 'none'}.",
                "data": d}
    top = d["diseases"][0]
    others = ", ".join(x["name"] for x in d["diseases"][1:3])
    obs = (f"Indicated conditions: {', '.join(d['conditions'])}. Most likely: {top['name']} "
           f"(via {', '.join(top['via'])})" + (f"; also possible: {others}." if others else "."))
    return {"observation": obs, "data": d}


def _explain_alert(ctx, **_):
    alerts = ctx.store.list_alerts(ctx.gh_id, limit=1)
    if not alerts:
        return {"observation": "No alerts on record for this greenhouse.", "data": None}
    path = kg.explain_alert(ctx.store, alerts[0]["id"])
    if not path:
        return {"observation": "Could not resolve the latest alert.", "data": None}
    dz = (path.get("disease") or {}).get("name")
    obs = (f"Latest alert: {path['alert'].get('kind')} ({path['alert'].get('level')}) -> {dz}, "
           f"caused by {path.get('pathogen')}; favoured by {', '.join(path.get('conditions') or []) or 'n/a'}. "
           f"{len(path.get('treatments') or [])} treatments control it.")
    return {"observation": obs, "data": path}


def _treatments(ctx, target: str = "", **_):
    tgt = _resolve_target(target)
    if not tgt:
        return {"observation": f"Unknown disease/pest '{target}'. Try a name like 'late blight' or 'whitefly'.",
                "data": None}
    ts = kg.treatments_for(ctx.store, tgt[0], tgt[1])
    if not ts:
        return {"observation": f"No treatments found for {target}.", "data": []}
    lines = []
    for t in ts[:5]:
        warn = f" [HARMS {', '.join(t['harmful_to'])}]" if t.get("harmful_to") else ""
        lines.append(f"{t['name']} ({t.get('type')}, PHI {t.get('phi_days')}d, "
                     f"eff {t.get('edge_efficacy') or t.get('efficacy')}, ~KES {t.get('cost_kes')}){warn}")
    return {"observation": f"Ranked controls for {target}: " + "; ".join(lines), "data": ts}


def _vector_risk(ctx, **_):
    pairs = [(p, d) for fl, p, rel, tl, d, _ in A.EDGES if rel == "VECTORS"]
    if not pairs:
        return {"observation": "No pest->disease vector links in the graph.", "data": []}
    obs = "; ".join(f"{kg._node('Pest', p)['name']} can transmit {kg._node('Disease', d)['name']}"
                    for p, d in pairs)
    return {"observation": "Pest-vectored disease risk: " + obs +
            ". Watch trap counts; control the vector AND remove infected plants.", "data": pairs}


def _knowledge_lookup(ctx, name: str = "", **_):
    tgt = _resolve_target(name)
    if not tgt or tgt[0] != "Disease":
        return {"observation": f"No disease node matched '{name}'.", "data": None}
    did = tgt[1]
    patho = kg.pathogen_of(did)
    conds = kg.favoring_conditions(did)
    ts = kg.treatments_for(ctx.store, "Disease", did)
    obs = (f"{kg._node('Disease', did)['name']}: caused by {(patho or {}).get('name','?')}; "
           f"favoured by {', '.join(c['name'] for c in conds) or 'n/a'}; "
           f"top control {ts[0]['name'] if ts else 'n/a'}.")
    return {"observation": obs, "data": {"pathogen": patho, "conditions": conds, "treatments": ts}}


def _ask_graph(ctx, cypher: str = "", **_):
    """Guarded, read-only Cypher the agent composed itself (text2cypher)."""
    q = (cypher or "").strip().rstrip(";")
    if not q or "match" not in q.lower():
        return {"observation": "ask_graph needs a read MATCH...RETURN query.", "data": None, "cypher": q}
    if _WRITE.search(q):
        return {"observation": "Refused: only read-only queries are allowed (no writes).",
                "data": None, "cypher": q}
    if " limit " not in q.lower():
        q += " LIMIT 25"
    if ctx.store.mode != "neo4j":
        return {"observation": "ask_graph runs on the Neo4j backend (offline demo uses the typed tools).",
                "data": None, "cypher": q}
    try:
        rows = ctx.store._run(q)
        sample = rows[:8]
        return {"observation": f"{len(rows)} row(s). Sample: {sample}", "data": rows, "cypher": q}
    except Exception as exc:  # noqa: BLE001
        return {"observation": f"Query error: {exc}", "data": None, "cypher": q}


TOOLS = {
    "diagnose_conditions": {
        "fn": _diagnose,
        "args": {},
        "desc": "Diagnose the most likely disease(s) from the greenhouse's CURRENT sensor conditions "
                "(reads latest readings -> indicated microclimate conditions -> diseases they favour)."},
    "explain_latest_alert": {
        "fn": _explain_alert,
        "args": {},
        "desc": "Explain why the latest alert fired: the disease, its pathogen, the conditions that "
                "triggered it, and how many treatments control it."},
    "treatments_for": {
        "fn": _treatments,
        "args": {"target": "disease or pest name, e.g. 'late blight' or 'whitefly'"},
        "desc": "List the ranked controls for a given disease/pest (efficacy -> pre-harvest interval -> "
                "cost, with beneficial-safety warnings)."},
    "pest_vector_risk": {
        "fn": _vector_risk,
        "args": {},
        "desc": "List which pests can VECTOR (transmit) which diseases — for assessing virus risk from "
                "trap counts."},
    "knowledge_lookup": {
        "fn": _knowledge_lookup,
        "args": {"name": "disease name to look up"},
        "desc": "Look up a disease's pathogen, favouring conditions, and top control from the ontology."},
    "ask_graph": {
        "fn": _ask_graph,
        "args": {"cypher": "a single read-only Cypher MATCH...RETURN query against the schema"},
        "desc": "Run your OWN read-only Cypher query against the knowledge graph when no typed tool fits. "
                "Schema is provided. No writes."},
}


def run_tool(tool_name: str, store, settings, gh_id: str, **args) -> dict:
    spec = TOOLS.get(tool_name)
    if not spec:
        return {"observation": f"Unknown tool '{tool_name}'.", "data": None}
    try:
        return spec["fn"](_ctx(store, settings, gh_id), **args)
    except Exception as exc:  # noqa: BLE001
        log.warning("tool %s failed: %s", tool_name, exc)
        return {"observation": f"Tool {tool_name} error: {exc}", "data": None}


def tool_catalog() -> str:
    lines = []
    for n, s in TOOLS.items():
        a = ", ".join(f"{k}: {v}" for k, v in s["args"].items()) or "(no args)"
        lines.append(f"- {n}({a}): {s['desc']}")
    return "\n".join(lines)
