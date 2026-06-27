"""Neo4j-backed graph store + the get_store() factory (auto-fallback to memory).

Neo4jGraphStore mirrors InMemoryGraphStore method-for-method so callers are
backend-agnostic. If Neo4j is configured but unreachable, get_store() returns
the in-memory store and LOGS the downgrade.
"""
from __future__ import annotations

from typing import Any

from graph.common import new_id, to_props
from graph.memory_store import InMemoryGraphStore
from logging_setup import get_logger, tag

log = get_logger("graph.store")


class Neo4jGraphStore:
    mode = "neo4j"

    def __init__(self, driver, database: str | None = None) -> None:
        self.driver = driver
        self.database = database or None   # None -> use the home/default database

    # --- low-level ---------------------------------------------------------
    def _run(self, cypher: str, **params) -> list[dict]:
        with self.driver.session(database=self.database) as s:
            return [r.data() for r in s.run(cypher, **params)]

    def health_check(self) -> bool:
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:  # noqa: BLE001
            return False

    def apply_schema(self) -> None:
        from graph.schema import apply_schema
        apply_schema(self.driver, self.database)

    def wipe(self) -> None:
        self._run("MATCH (n) DETACH DELETE n")

    # --- bulk seed ---------------------------------------------------------
    def load_seed(self, data: dict) -> None:
        self.wipe()
        self.apply_schema()
        self._run("UNWIND $rows AS r CREATE (f:Farmer) SET f = r", rows=data.get("farmers", []))
        self._run("UNWIND $rows AS r CREATE (c:Cooperative) SET c = r", rows=data.get("cooperatives", []))
        self._run("UNWIND $rows AS r CREATE (l:Lender) SET l = r", rows=data.get("lenders", []))
        self._run(
            "UNWIND $rows AS r MATCH (f:Farmer {id:r.farmer_id}) "
            "CREATE (g:Greenhouse) SET g = r CREATE (f)-[:OWNS]->(g)",
            rows=data.get("greenhouses", []),
        )
        self._run(
            "UNWIND $rows AS r MATCH (g:Greenhouse {id:r.greenhouse_id}) "
            "CREATE (s:Season) SET s = r CREATE (g)-[:HAS_SEASON]->(s)",
            rows=data.get("seasons", []),
        )
        self._run(
            "UNWIND $rows AS r MATCH (g:Greenhouse {id:r.greenhouse_id}) "
            "CREATE (x:Reading) SET x = r CREATE (g)-[:RECORDED]->(x) "
            "WITH x, r WHERE r.season_id IS NOT NULL "
            "MATCH (s:Season {id:r.season_id}) CREATE (s)-[:DURING]->(x)",
            rows=data.get("readings", []),
        )
        self._run(
            "UNWIND $rows AS r MATCH (g:Greenhouse {id:r.greenhouse_id}) "
            "CREATE (a:Alert) SET a = apoc.map.removeKey(r,'triggered_by') "
            "CREATE (g)-[:RAISED]->(a)",
            rows=data.get("alerts", []),
        ) if self._has_apoc() else self._load_alerts_no_apoc(data.get("alerts", []))
        # TRIGGERED_BY
        triggers = [{"alert_id": a["id"], "reading_id": rid}
                    for a in data.get("alerts", []) for rid in a.get("triggered_by", [])]
        self._run(
            "UNWIND $rows AS r MATCH (a:Alert {id:r.alert_id}),(x:Reading {id:r.reading_id}) "
            "CREATE (a)-[:TRIGGERED_BY]->(x)", rows=triggers,
        )
        self._run(
            "UNWIND $rows AS r MATCH (a:Alert {id:r.alert_id}) "
            "CREATE (x:Action) SET x = r CREATE (a)-[:RESPONDED_WITH]->(x)",
            rows=data.get("actions", []),
        )
        self._run(
            "UNWIND $rows AS r MATCH (s:Season {id:r.season_id}) "
            "CREATE (h:Harvest) SET h = r CREATE (s)-[:YIELDED]->(h)",
            rows=data.get("harvests", []),
        )
        self._run(
            "UNWIND $rows AS r MATCH (f:Farmer {id:r.farmer_id}),(c:Cooperative {id:r.cooperative_id}) "
            "CREATE (f)-[:MEMBER_OF]->(c)", rows=data.get("memberships", []),
        )
        self._run(
            "UNWIND $rows AS r MATCH (c:Cooperative {id:r.cooperative_id}),(l:Lender {id:r.lender_id}) "
            "CREATE (c)-[:PARTNERS_WITH]->(l)", rows=data.get("partnerships", []),
        )
        log.info("Seed loaded into Neo4j: %s", self.stats()["nodes"])

    def _has_apoc(self) -> bool:
        try:
            self._run("RETURN apoc.version() AS v")
            return True
        except Exception:  # noqa: BLE001
            return False

    def _load_alerts_no_apoc(self, alerts: list[dict]) -> None:
        clean = [{k: v for k, v in a.items() if k != "triggered_by"} for a in alerts]
        self._run(
            "UNWIND $rows AS r MATCH (g:Greenhouse {id:r.greenhouse_id}) "
            "CREATE (a:Alert) SET a = r CREATE (g)-[:RAISED]->(a)", rows=clean,
        )

    # --- runtime writes ----------------------------------------------------
    def add_reading(self, gh_id: str, reading: Any, season_id: str | None = None) -> str:
        props = to_props(reading)
        props.setdefault("id", new_id("r"))
        props["greenhouse_id"] = gh_id
        if season_id:
            props["season_id"] = season_id
        self._run(
            "MATCH (g:Greenhouse {id:$gh}) CREATE (x:Reading) SET x = $p "
            "CREATE (g)-[:RECORDED]->(x)", gh=gh_id, p=props,
        )
        return props["id"]

    def add_alert(self, gh_id: str, alert: Any, triggered_by: list[str] | None = None) -> str:
        props = to_props(alert)
        props.setdefault("id", new_id("a"))
        trig = list(triggered_by or props.get("triggered_by") or [])
        props.pop("triggered_by", None)
        props["greenhouse_id"] = gh_id
        self._run(
            "MATCH (g:Greenhouse {id:$gh}) CREATE (a:Alert) SET a = $p "
            "CREATE (g)-[:RAISED]->(a)", gh=gh_id, p=props,
        )
        if trig:
            self._run(
                "MATCH (a:Alert {id:$aid}) UNWIND $rids AS rid "
                "MATCH (x:Reading {id:rid}) CREATE (a)-[:TRIGGERED_BY]->(x)",
                aid=props["id"], rids=trig,
            )
        return props["id"]

    def add_action(self, alert_id: str, action: Any) -> str:
        props = to_props(action)
        props.setdefault("id", new_id("act"))
        props["alert_id"] = alert_id
        self._run(
            "MATCH (a:Alert {id:$aid}) CREATE (x:Action) SET x = $p "
            "CREATE (a)-[:RESPONDED_WITH]->(x)", aid=alert_id, p=props,
        )
        return props["id"]

    def add_audit_record(self, farmer_id: str, lender: dict, record: Any) -> str:
        props = to_props(record)
        props.setdefault("id", new_id("audit"))
        self._run(
            "MATCH (f:Farmer {id:$fid}) "
            "MERGE (l:Lender {id:$lid}) SET l.name=$lname, l.type=$ltype "
            "CREATE (u:AuditRecord) SET u = $p "
            "CREATE (u)-[:ABOUT]->(f) CREATE (u)-[:REQUESTED_BY]->(l)",
            fid=farmer_id, lid=(lender or {}).get("id", "lender-unknown"),
            lname=(lender or {}).get("name", "Unknown"),
            ltype=(lender or {}).get("type", "SACCO"), p=props,
        )
        return props["id"]

    # --- reads -------------------------------------------------------------
    def list_recent_readings(self, gh_id: str, limit: int = 50) -> list[dict]:
        return self._run(
            "MATCH (g:Greenhouse {id:$gh})-[:RECORDED]->(x:Reading) "
            "RETURN x ORDER BY x.ts DESC LIMIT $lim", gh=gh_id, lim=limit,
        )

    def list_alerts(self, gh_id: str, limit: int = 50) -> list[dict]:
        rows = self._run(
            "MATCH (g:Greenhouse {id:$gh})-[:RAISED]->(a:Alert) "
            "RETURN a ORDER BY a.ts DESC LIMIT $lim", gh=gh_id, lim=limit,
        )
        return [r["a"] for r in rows]

    def get_farmer_subgraph(self, farmer_id: str) -> dict:
        head = self._run(
            "MATCH (f:Farmer {id:$fid}) "
            "OPTIONAL MATCH (f)-[:OWNS]->(g:Greenhouse) "
            "OPTIONAL MATCH (f)-[:MEMBER_OF]->(co:Cooperative) "
            "RETURN f{.id,.name,.county,.joined_date} AS farmer, "
            "g{.id,.structure_type,.has_netting,.irrigation,.climate_resilience,.area_m2} AS greenhouse, "
            "co{.id,.name,.region,.members} AS cooperative", fid=farmer_id,
        )
        if not head or not head[0]["farmer"]:
            return {"farmer": None, "greenhouse": None, "cooperative": None,
                    "seasons": [], "harvests": [], "alerts": [],
                    "alert_count": 0, "action_count": 0}
        row = head[0]
        seasons = [r["s"] for r in self._run(
            "MATCH (f:Farmer {id:$fid})-[:OWNS]->(:Greenhouse)-[:HAS_SEASON]->(s:Season) "
            "RETURN s{.index,.start_date,.end_date} AS s ORDER BY s.index", fid=farmer_id)]
        harvests = self._run(
            "MATCH (f:Farmer {id:$fid})-[:OWNS]->(:Greenhouse)-[:HAS_SEASON]->(s:Season)-[:YIELDED]->(h:Harvest) "
            "RETURN s.index AS season_index, h.yield_kg AS yield_kg, h.expected_kg AS expected_kg, "
            "h.loss_pct AS loss_pct, h.grade_a_pct AS grade_a_pct ORDER BY s.index", fid=farmer_id)
        alerts = self._run(
            "MATCH (f:Farmer {id:$fid})-[:OWNS]->(:Greenhouse)-[:RAISED]->(a:Alert) "
            "WHERE a.season_id IS NOT NULL "   # only resolved/historical alerts
            "OPTIONAL MATCH (a)-[:RESPONDED_WITH]->(act:Action) "
            "RETURN a.id AS id, a.kind AS kind, a.level AS level, a.ts AS ts, "
            "a.lead_time_hr AS lead_time_hr, count(act) > 0 AS actioned "
            "ORDER BY a.ts", fid=farmer_id)
        return {
            "farmer": row["farmer"], "greenhouse": row["greenhouse"],
            "cooperative": row["cooperative"], "seasons": seasons, "harvests": harvests,
            "alerts": alerts, "alert_count": len(alerts),
            "action_count": sum(1 for a in alerts if a.get("actioned")),
        }

    def get_visual_graph(self, farmer_id: str, reading_limit: int = 8) -> dict:
        rows = self._run(
            "MATCH (f:Farmer {id:$fid}) "
            "OPTIONAL MATCH (f)-[:OWNS]->(g:Greenhouse) "
            "OPTIONAL MATCH (f)-[:MEMBER_OF]->(co:Cooperative) "
            "OPTIONAL MATCH (g)-[:HAS_SEASON]->(s:Season)-[:YIELDED]->(h:Harvest) "
            "OPTIONAL MATCH (g)-[:RAISED]->(a:Alert) "
            "OPTIONAL MATCH (a)-[:TRIGGERED_BY]->(r:Reading) "
            "OPTIONAL MATCH (a)-[:RESPONDED_WITH]->(act:Action) "
            "RETURN f,g,co,collect(DISTINCT s) AS ss, collect(DISTINCT h) AS hh, "
            "collect(DISTINCT a) AS aa, collect(DISTINCT r) AS rr, collect(DISTINCT act) AS cc, "
            "collect(DISTINCT [a.id,r.id]) AS trig, collect(DISTINCT [a.id,act.id]) AS resp, "
            "collect(DISTINCT [s.id,h.id]) AS yld", fid=farmer_id)
        if not rows:
            return {"nodes": [], "edges": []}
        d = rows[0]
        nodes, edges, seen = [], [], set()

        def node(nid, label, group):
            if nid and nid not in seen:
                seen.add(nid); nodes.append({"id": nid, "label": str(label), "group": group})

        def edge(s, t, label):
            if s in seen and t in seen:
                edges.append({"source": s, "target": t, "label": label})

        f, g, co = d.get("f"), d.get("g"), d.get("co")
        if f:
            node(f["id"], f.get("name", f["id"]), "Farmer")
        if g:
            node(g["id"], "Greenhouse", "Greenhouse"); edge(f["id"], g["id"], "OWNS")
        if co:
            node(co["id"], co.get("name", "Co-op"), "Cooperative"); edge(f["id"], co["id"], "MEMBER_OF")
        for s in d.get("ss") or []:
            if s:
                node(s["id"], f"Season {s.get('index')}", "Season"); edge(g["id"], s["id"], "HAS_SEASON")
        for h in d.get("hh") or []:
            if h:
                node(h["id"], f"{h.get('yield_kg')}kg", "Harvest")
        for pair in d.get("yld") or []:
            if pair and pair[0] and pair[1]:
                edge(pair[0], pair[1], "YIELDED")
        for a in d.get("aa") or []:
            if a:
                node(a["id"], f"{a.get('kind')} ({a.get('level')})", "Alert"); edge(g["id"], a["id"], "RAISED")
        for r in d.get("rr") or []:
            if r:
                node(r["id"], f"RH{int(r.get('humidity',0))}/{r.get('temp_c')}C", "Reading")
        for act in d.get("cc") or []:
            if act:
                node(act["id"], act.get("type", "action"), "Action")
        for pair in d.get("trig") or []:
            if pair and pair[0] and pair[1]:
                edge(pair[0], pair[1], "TRIGGERED_BY")
        for pair in d.get("resp") or []:
            if pair and pair[0] and pair[1]:
                edge(pair[0], pair[1], "RESPONDED_WITH")
        return {"nodes": nodes, "edges": edges}

    def stats(self) -> dict:
        labels = ["Farmer", "Cooperative", "Lender", "Greenhouse", "Season",
                  "Reading", "Alert", "Action", "Harvest", "AuditRecord"]
        node_counts = {}
        for lab in labels:
            rec = self._run(f"MATCH (n:{lab}) RETURN count(n) AS c")
            node_counts[lab] = rec[0]["c"] if rec else 0
        rec = self._run("MATCH ()-[r]->() RETURN count(r) AS c")
        return {"mode": self.mode, "nodes": node_counts,
                "node_total": sum(node_counts.values()),
                "rel_total": rec[0]["c"] if rec else 0}

    def close(self) -> None:
        try:
            self.driver.close()
        except Exception:  # noqa: BLE001
            pass


def get_store(settings=None):
    """Factory: real Neo4j if reachable, else the in-memory mock (labeled)."""
    from config import get_settings
    settings = settings or get_settings()
    if settings.graph_mode() == "neo4j":
        try:
            from graph.connection import get_driver
            driver = get_driver(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            log.info("%s graph backend: Neo4j Aura (%s)", tag("live"), settings.NEO4J_URI)
            return Neo4jGraphStore(driver, database=settings.NEO4J_DATABASE)
        except Exception as exc:  # noqa: BLE001
            log.warning("%s Neo4j unavailable (%s) → in-memory store", tag("mock"), exc)
    else:
        log.info("%s graph backend: in-memory (no Neo4j configured)", tag("mock"))
    return InMemoryGraphStore()
