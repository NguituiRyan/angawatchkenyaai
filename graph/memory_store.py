"""In-memory graph store — the LABELED-MOCK fallback when Neo4j Aura is absent.

Mirrors Neo4jGraphStore's interface exactly so the entire app (seed, risk, alerts,
scoring, dashboard) runs with zero cloud dependencies. `mode == "memory"`.
"""
from __future__ import annotations

from typing import Any

from graph.common import empty_seed, new_id, to_props
from logging_setup import get_logger

log = get_logger("graph.memory")


class InMemoryGraphStore:
    mode = "memory"

    def __init__(self) -> None:
        self._t = empty_seed()
        self.audits: list[dict] = []
        # adjacency we maintain explicitly for explainability traversals
        self._alert_triggers: dict[str, list[str]] = {}   # alert_id -> [reading_id]
        self._alert_actions: dict[str, list[str]] = {}     # alert_id -> [action_id]

    # --- lifecycle ---------------------------------------------------------
    def health_check(self) -> bool:
        return True

    def apply_schema(self) -> None:
        return None

    def wipe(self) -> None:
        self._t = empty_seed()
        self.audits = []
        self._alert_triggers = {}
        self._alert_actions = {}

    def load_seed(self, data: dict) -> None:
        self.wipe()
        for key in empty_seed():
            self._t[key] = list(data.get(key, []))
        for a in self._t["alerts"]:
            if a.get("triggered_by"):
                self._alert_triggers[a["id"]] = list(a["triggered_by"])
        for act in self._t["actions"]:
            self._alert_actions.setdefault(act["alert_id"], []).append(act["id"])
        log.info("Loaded seed into memory store: %s", self.stats()["nodes"])

    # --- writes ------------------------------------------------------------
    def add_reading(self, gh_id: str, reading: Any, season_id: str | None = None) -> str:
        props = to_props(reading)
        props.setdefault("id", new_id("r"))
        props["greenhouse_id"] = gh_id
        if season_id:
            props["season_id"] = season_id
        self._t["readings"].append(props)
        return props["id"]

    def add_alert(self, gh_id: str, alert: Any, triggered_by: list[str] | None = None) -> str:
        props = to_props(alert)
        props.setdefault("id", new_id("a"))
        props["greenhouse_id"] = gh_id
        props["triggered_by"] = list(triggered_by or props.get("triggered_by") or [])
        self._t["alerts"].append(props)
        if props["triggered_by"]:
            self._alert_triggers[props["id"]] = props["triggered_by"]
        return props["id"]

    def add_action(self, alert_id: str, action: Any) -> str:
        props = to_props(action)
        props.setdefault("id", new_id("act"))
        props["alert_id"] = alert_id
        self._t["actions"].append(props)
        self._alert_actions.setdefault(alert_id, []).append(props["id"])
        return props["id"]

    def update_farmer(self, farmer_id: str, **props) -> bool:
        for f in self._t["farmers"]:
            if f["id"] == farmer_id:
                f.update(props)
                return True
        return False

    def add_audit_record(self, farmer_id: str, lender: dict, record: Any) -> str:
        props = to_props(record)
        props.setdefault("id", new_id("audit"))
        props["farmer_id"] = farmer_id
        props["lender"] = lender
        if lender and not any(l["id"] == lender.get("id") for l in self._t["lenders"]):
            self._t["lenders"].append(lender)
        self.audits.append(props)
        return props["id"]

    # --- reads -------------------------------------------------------------
    def _gh_for_farmer(self, farmer_id: str) -> dict | None:
        for g in self._t["greenhouses"]:
            if g.get("farmer_id") == farmer_id:
                return g
        return None

    def list_recent_readings(self, gh_id: str, limit: int = 50) -> list[dict]:
        rs = [r for r in self._t["readings"] if r.get("greenhouse_id") == gh_id]
        rs.sort(key=lambda r: str(r.get("ts", "")), reverse=True)
        return rs[:limit]

    def list_alerts(self, gh_id: str, limit: int = 50) -> list[dict]:
        als = [a for a in self._t["alerts"] if a.get("greenhouse_id") == gh_id]
        als.sort(key=lambda a: str(a.get("ts", "")), reverse=True)
        return als[:limit]

    def get_farmer_subgraph(self, farmer_id: str) -> dict:
        farmer = next((f for f in self._t["farmers"] if f["id"] == farmer_id), None)
        if not farmer:
            return {"farmer": None, "greenhouse": None, "cooperative": None,
                    "seasons": [], "harvests": [], "alerts": [],
                    "alert_count": 0, "action_count": 0}
        gh = self._gh_for_farmer(farmer_id)
        gh_id = gh["id"] if gh else None

        coop = None
        coop_id = next((m["cooperative_id"] for m in self._t["memberships"]
                        if m["farmer_id"] == farmer_id), None)
        if coop_id:
            coop = next((c for c in self._t["cooperatives"] if c["id"] == coop_id), None)

        seasons = [s for s in self._t["seasons"] if s.get("greenhouse_id") == gh_id]
        seasons.sort(key=lambda s: s.get("index", 0))
        season_index = {s["id"]: s.get("index") for s in seasons}

        harvests = []
        for h in self._t["harvests"]:
            if h.get("greenhouse_id") == gh_id:
                harvests.append({
                    "season_index": season_index.get(h.get("season_id")),
                    "yield_kg": h.get("yield_kg"),
                    "expected_kg": h.get("expected_kg"),
                    "loss_pct": h.get("loss_pct"),
                    "grade_a_pct": h.get("grade_a_pct"),
                })
        harvests.sort(key=lambda h: (h["season_index"] or 0))

        alerts = []
        action_count = 0
        for a in self._t["alerts"]:
            if a.get("greenhouse_id") != gh_id:
                continue
            if not a.get("season_id"):
                continue  # live/open alert (just fired) — not part of the verified history
            actioned = bool(self._alert_actions.get(a["id"]))
            action_count += 1 if actioned else 0
            alerts.append({
                "id": a["id"], "kind": a.get("kind"), "level": a.get("level"),
                "ts": a.get("ts"), "lead_time_hr": a.get("lead_time_hr"),
                "actioned": actioned,
            })

        return {
            "farmer": {**{k: farmer.get(k) for k in ("id", "name", "county", "joined_date")},
                       "language": farmer.get("language"),
                       "subscribed": farmer.get("subscribed", True),
                       "phone": farmer.get("phone")},
            "greenhouse": {k: gh.get(k) for k in
                           ("id", "structure_type", "has_netting", "irrigation",
                            "climate_resilience", "area_m2")} if gh else None,
            "cooperative": {k: coop.get(k) for k in ("id", "name", "region", "members")}
                           if coop else None,
            "seasons": [{"index": s.get("index"), "start_date": s.get("start_date"),
                         "end_date": s.get("end_date")} for s in seasons],
            "harvests": harvests,
            "alerts": alerts,
            "alert_count": len(alerts),
            "action_count": action_count,
        }

    def get_visual_graph(self, farmer_id: str, reading_limit: int = 8) -> dict:
        """nodes/edges for streamlit-agraph (kept small for readability)."""
        nodes: list[dict] = []
        edges: list[dict] = []
        seen: set[str] = set()

        def node(nid, label, group):
            if nid and nid not in seen:
                seen.add(nid)
                nodes.append({"id": nid, "label": label, "group": group})

        def edge(s, t, label):
            if s in seen and t in seen:
                edges.append({"source": s, "target": t, "label": label})

        f = next((x for x in self._t["farmers"] if x["id"] == farmer_id), None)
        if not f:
            return {"nodes": [], "edges": []}
        node(f["id"], f.get("name", f["id"]), "Farmer")
        gh = self._gh_for_farmer(farmer_id)
        if gh:
            node(gh["id"], "Greenhouse", "Greenhouse")
            edge(f["id"], gh["id"], "OWNS")
        gh_id = gh["id"] if gh else None
        coop_id = next((m["cooperative_id"] for m in self._t["memberships"]
                        if m["farmer_id"] == farmer_id), None)
        if coop_id:
            c = next((x for x in self._t["cooperatives"] if x["id"] == coop_id), None)
            if c:
                node(c["id"], c.get("name", "Co-op"), "Cooperative")
                edge(f["id"], c["id"], "MEMBER_OF")
        for s in sorted([s for s in self._t["seasons"] if s.get("greenhouse_id") == gh_id],
                        key=lambda s: s.get("index", 0)):
            node(s["id"], f"Season {s.get('index')}", "Season")
            edge(gh_id, s["id"], "HAS_SEASON")
            for h in self._t["harvests"]:
                if h.get("season_id") == s["id"]:
                    node(h["id"], f"{h.get('yield_kg')}kg", "Harvest")
                    edge(s["id"], h["id"], "YIELDED")
        for a in self.list_alerts(gh_id, limit=6):
            node(a["id"], f"{a.get('kind')} ({a.get('level')})", "Alert")
            edge(gh_id, a["id"], "RAISED")
            for rid in self._alert_triggers.get(a["id"], [])[:2]:
                r = next((x for x in self._t["readings"] if x["id"] == rid), None)
                if r:
                    node(rid, f"RH{int(r.get('humidity',0))}/{r.get('temp_c')}C", "Reading")
                    edge(a["id"], rid, "TRIGGERED_BY")
            for actid in self._alert_actions.get(a["id"], []):
                act = next((x for x in self._t["actions"] if x["id"] == actid), None)
                if act:
                    node(actid, act.get("type", "action"), "Action")
                    edge(a["id"], actid, "RESPONDED_WITH")
        return {"nodes": nodes, "edges": edges}

    def stats(self) -> dict:
        node_counts = {
            "Farmer": len(self._t["farmers"]),
            "Cooperative": len(self._t["cooperatives"]),
            "Lender": len(self._t["lenders"]),
            "Greenhouse": len(self._t["greenhouses"]),
            "Season": len(self._t["seasons"]),
            "Reading": len(self._t["readings"]),
            "Alert": len(self._t["alerts"]),
            "Action": len(self._t["actions"]),
            "Harvest": len(self._t["harvests"]),
            "AuditRecord": len(self.audits),
        }
        rels = (
            len(self._t["greenhouses"])                       # OWNS
            + len(self._t["memberships"])                      # MEMBER_OF
            + len(self._t["seasons"])                          # HAS_SEASON
            + len(self._t["readings"])                         # RECORDED
            + len(self._t["alerts"])                           # RAISED
            + sum(len(v) for v in self._alert_triggers.values())   # TRIGGERED_BY
            + sum(len(v) for v in self._alert_actions.values())    # RESPONDED_WITH
            + len(self._t["harvests"])                         # YIELDED
            + len(self._t["partnerships"])                     # PARTNERS_WITH
            + len(self.audits) * 2                             # ABOUT + REQUESTED_BY
        )
        return {"mode": self.mode, "nodes": node_counts,
                "node_total": sum(node_counts.values()), "rel_total": rels}

    def close(self) -> None:
        return None
