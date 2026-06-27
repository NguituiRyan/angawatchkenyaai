"""Knowledge-graph engine: seed the agronomic ontology and run the MULTI-HOP
traversals that make the graph matter. Cypher on Neo4j (the showcase), with a
Python fallback over the same ontology for the in-memory store (offline demos).

Showcase traversal — "why was I warned + what do I do":
  (Alert)-[:FOR_DISEASE]->(Disease)-[:CAUSED_BY]->(Pathogen)
  (Disease)<-[:FAVORS_REVERSE]-(Condition)<-[:INDICATES]-(Reading the alert TRIGGERED_BY)
  (Disease)<-[:CONTROLS]-(Treatment)   ranked by efficacy / pre-harvest-interval / cost
  (Treatment)-[:HARMFUL_TO]->(Beneficial)   -> safety warning
"""
from __future__ import annotations

from graph import agronomy as A
from logging_setup import get_logger

log = get_logger("graph.kg")

# ---- in-memory indices over the ontology (for the memory-store fallback) ----
_NODE = {lab: {n["id"]: n for n in rows} for lab, rows in A.NODES.items()}


def _node(label: str, nid: str) -> dict:
    return _NODE.get(label, {}).get(nid, {"id": nid, "name": nid})


def _controls(target_label: str, target_id: str) -> list[dict]:
    """Treatments that CONTROL a disease/pest, with their props + efficacy."""
    out = []
    for fl, fid, rel, tl, tid, props in A.EDGES:
        if rel == "CONTROLS" and tl == target_label and tid == target_id:
            tr = dict(_node("Treatment", fid))
            tr["edge_efficacy"] = props.get("efficacy", tr.get("efficacy"))
            tr["harmful_to"] = [_node("Beneficial", b)["name"]
                                for f2, i2, r2, l2, b2, _ in A.EDGES
                                for b in [b2] if r2 == "HARMFUL_TO" and i2 == fid]
            out.append(tr)
    return out


def _rank_treatments(treatments: list[dict], days_to_harvest: int | None) -> list[dict]:
    def key(t):
        eff = A.EFFICACY_RANK.get(t.get("edge_efficacy") or t.get("efficacy", ""), 0)
        phi_ok = 1 if (days_to_harvest is None or t.get("phi_days", 0) <= days_to_harvest) else 0
        cheap = -(t.get("cost_kes", 0))
        return (phi_ok, eff, cheap)
    return sorted(treatments, key=key, reverse=True)


def favoring_conditions(disease_id: str) -> list[dict]:
    return [_node("Condition", cid) for fl, fid, rel, tl, cid, _ in A.EDGES
            if rel == "FAVORS_REVERSE" and fl == "Disease" and fid == disease_id and tl == "Condition"]


def pathogen_of(disease_id: str) -> dict | None:
    for fl, fid, rel, tl, pid, _ in A.EDGES:
        if rel == "CAUSED_BY" and fid == disease_id:
            return _node("Pathogen", pid)
    return None


# ============================================================ seeding =======
def seed_agronomy(store) -> None:
    """Create the ontology + edges in Neo4j and link the operational data into it.
    For the in-memory store this is a no-op (traversals use the module ontology)."""
    if store.mode != "neo4j":
        return
    run = store._run
    # nodes
    for label, rows in A.NODES.items():
        run(f"UNWIND $rows AS r MERGE (n:{label} {{id:r.id}}) SET n += r", rows=rows)
    # ontology edges
    by_rel: dict[str, list] = {}
    for fl, fid, rel, tl, tid, props in A.EDGES:
        by_rel.setdefault((fl, rel, tl), []).append({"f": fid, "t": tid, **props})
    for (fl, rel, tl), rows in by_rel.items():
        run(f"UNWIND $rows AS e MATCH (a:{fl} {{id:e.f}}),(b:{tl} {{id:e.t}}) "
            f"MERGE (a)-[x:{rel}]->(b) SET x += e", rows=rows)
    # link operational data into the ontology
    run("MATCH (a:Alert) WHERE a.kind IN ['late_blight','early_blight'] "
        "MATCH (d:Disease {id:a.kind}) MERGE (a)-[:FOR_DISEASE]->(d)")
    run("MATCH (a:Alert {kind:'tuta'}) MATCH (p:Pest {id:'tuta'}) MERGE (a)-[:FOR_PEST]->(p)")
    run("MATCH (act:Action) WITH act, CASE act.type WHEN 'sprayed' THEN 'mancozeb' "
        "WHEN 'ventilated' THEN 'ventilation' WHEN 'removed_leaves' THEN 'sanitation' END AS tid "
        "WHERE tid IS NOT NULL MATCH (tr:Treatment {id:tid}) MERGE (act)-[:APPLIED]->(tr)")
    # Reading -> Condition (sensor data linked to the ontology)
    cond_rules = [
        ("cool_humid_night", "r.humidity>=90 AND r.temp_c>=10 AND r.temp_c<=26"),
        ("warm_humid", "r.humidity>=90 AND r.temp_c>=20 AND r.temp_c<=32"),
        ("high_humidity", "r.humidity>=85"),
        ("prolonged_wetness", "r.leaf_wetness_hr>=10"),
    ]
    for cid, pred in cond_rules:
        run(f"MATCH (r:Reading) WHERE {pred} MATCH (c:Condition {{id:'{cid}'}}) "
            f"MERGE (r)-[:INDICATES]->(c)")
    log.info("Agronomic knowledge graph seeded + linked into Neo4j")


# ========================================================= traversals =======
def treatments_for(store, target_label: str, target_id: str,
                   days_to_harvest: int | None = None) -> list[dict]:
    if store.mode == "neo4j":
        rows = store._run(
            f"MATCH (t:Treatment)-[c:CONTROLS]->(x:{target_label} {{id:$id}}) "
            "OPTIONAL MATCH (t)-[:HARMFUL_TO]->(b:Beneficial) "
            "RETURN t{.id,.name,.type,.active,.phi_days,.cost_kes,.efficacy} AS t, "
            "c.efficacy AS edge_efficacy, collect(DISTINCT b.name) AS harmful_to", id=target_id)
        treatments = []
        for r in rows:
            t = dict(r["t"]); t["edge_efficacy"] = r["edge_efficacy"]
            t["harmful_to"] = [h for h in r["harmful_to"] if h]
            treatments.append(t)
    else:
        treatments = _controls(target_label, target_id)
    return _rank_treatments(treatments, days_to_harvest)


def explain_alert(store, alert_id: str) -> dict | None:
    """The showcase multi-hop path behind an alert."""
    if store.mode == "neo4j":
        head = store._run(
            "MATCH (a:Alert {id:$id}) "
            "OPTIONAL MATCH (a)-[:FOR_DISEASE]->(d:Disease)-[:CAUSED_BY]->(p:Pathogen) "
            "OPTIONAL MATCH (a)-[:TRIGGERED_BY]->(r:Reading)-[:INDICATES]->(c:Condition) "
            "RETURN a{.id,.kind,.level,.ts} AS alert, d{.id,.name} AS disease, "
            "p{.name} AS pathogen, collect(DISTINCT c.name) AS conditions, "
            "collect(DISTINCT r.id)[0..3] AS readings", id=alert_id)
        if not head:
            return None
        h = head[0]
        disease = h.get("disease") or {}
        target = ("Disease", disease.get("id")) if disease.get("id") else ("Pest", "tuta")
    else:
        alerts = [a for a in store._t["alerts"] if a.get("id") == alert_id] \
            if hasattr(store, "_t") else []
        if not alerts:
            return None
        a = alerts[0]
        tl, tid = A.ALERT_TO_TARGET.get(a.get("kind"), ("Disease", a.get("kind")))
        disease = _node("Disease", tid) if tl == "Disease" else _node("Pest", tid)
        h = {"alert": {k: a.get(k) for k in ("id", "kind", "level", "ts")},
             "disease": disease if tl == "Disease" else None,
             "pathogen": (pathogen_of(tid) or {}) if tl == "Disease" else {},
             "conditions": [c["name"] for c in favoring_conditions(tid)] if tl == "Disease" else [],
             "readings": a.get("triggered_by", [])[:3]}
        target = (tl, tid)

    treatments = treatments_for(store, target[0], target[1])
    return {
        "alert": h["alert"],
        "disease": h.get("disease") or {"name": _node("Pest", target[1]).get("name")},
        "pathogen": (h.get("pathogen") or {}).get("name") if isinstance(h.get("pathogen"), dict)
        else h.get("pathogen"),
        "conditions": [c for c in (h.get("conditions") or []) if c],
        "trigger_readings": h.get("readings") or [],
        "treatments": treatments,
        "target": {"label": target[0], "id": target[1]},
    }


def diagnose(store, gh_id: str) -> dict:
    """From the greenhouse's latest readings -> indicated conditions -> likely diseases."""
    rs = store.list_recent_readings(gh_id, limit=6)
    conds: list[str] = []
    for r in rs[:3]:
        for c in A.conditions_for_reading(r):
            if c not in conds:
                conds.append(c)
    # conditions -> diseases (FAVORS_REVERSE)
    diseases: dict[str, dict] = {}
    for fl, fid, rel, tl, cid, _ in A.EDGES:
        if rel == "FAVORS_REVERSE" and fl == "Disease" and cid in conds:
            d = diseases.setdefault(fid, {**_node("Disease", fid), "via": []})
            d["via"].append(_node("Condition", cid)["name"])
    ranked = sorted(diseases.values(), key=lambda d: len(d["via"]), reverse=True)
    return {"conditions": [_node("Condition", c)["name"] for c in conds], "diseases": ranked}


def kg_subgraph(store, focus_id: str) -> dict:
    """Small ontology subgraph around a disease (for visualization)."""
    nodes, edges, seen = [], [], set()

    def add(label, nid):
        if nid and nid not in seen:
            seen.add(nid)
            nodes.append({"id": nid, "label": _node(label, nid).get("name", nid), "group": label})

    add("Disease", focus_id)
    for fl, fid, rel, tl, tid, props in A.EDGES:
        if fid == focus_id and fl == "Disease":
            add(tl, tid)
            edges.append({"source": fid, "target": tid, "label": rel.replace("_REVERSE", "")})
        if rel == "CONTROLS" and tl == "Disease" and tid == focus_id:
            add("Treatment", fid)
            edges.append({"source": fid, "target": focus_id, "label": "CONTROLS"})
        if rel == "FAVORS_REVERSE" and fid == focus_id:
            edges.append({"source": tid, "target": fid, "label": "FAVORS"})
        if rel == "VECTORS" and tid == focus_id:
            add("Pest", fid)
            edges.append({"source": fid, "target": focus_id, "label": "VECTORS"})
    return {"nodes": nodes, "edges": edges}
