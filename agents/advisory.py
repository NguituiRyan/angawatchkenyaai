"""Crop-Health Advisory Agent — the hireable Masumi service.

A horticulture cooperative / off-taker hires this agent to monitor its contracted
greenhouses: it TRIAGES which farms are at risk, DIAGNOSES the problem by traversing
the agronomic knowledge graph, and PREPARES a ranked, PHI-aware treatment plan plus an
officer-visit priority — work a co-op's scarce field officers can't do at scale.

The deliverable is an `AdvisoryReport`. Its `result_hash` commits to the DIAGNOSIS and
the plan (not an opinion-score), so Masumi pays per report and Decision-Logs the actual
agronomic recommendation on-chain. A co-op agronomist approves before any spray.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from agents.agronomist import AgronomistAgent
from graph import kg
from logging_setup import get_logger

log = get_logger("agents.advisory")

DEFAULT_COOP = {"id": "coop-1", "name": "Rift Valley Fresh Co-op", "type": "cooperative"}

LIMITS = [
    "RECOMMENDATION for the co-op's field officer / agronomist — not an automated "
    "treatment order. A human approves before any spray.",
    "Diagnosis is inferred from sensor microclimate + the agronomic knowledge graph, not "
    "a lab test or in-field inspection. Confirm visually before acting.",
    "Follow the product label rate and the stated pre-harvest interval (PHI); observe "
    "bee-safety windows for any bloom-time spray.",
    "Efficacy and cost are regional estimates — verify local availability and PCPB "
    "registration before purchase.",
]

# risk level -> (officer-visit priority text, sort rank)
PRIORITY = {"HIGH": ("Visit now — within 24h", 0),
            "MED": ("Schedule visit — 2–3 days", 1),
            "LOW": ("Routine monitoring", 2)}


@dataclass
class AdvisoryReport:
    greenhouse_id: str
    farm_id: str | None
    requested_by: str
    generated_at: str
    risk_level: str
    priority: str
    priority_rank: int
    diagnosis: str
    pathogen: str | None
    confidence: dict
    conditions: list
    trigger_readings: list
    recommended_actions: list
    narrative: str
    narration_mode: str
    backend: str
    limits: list
    result_hash: str = ""

    def canonical(self) -> dict:
        """Deterministic payload the result_hash commits to (excludes prose)."""
        return {
            "greenhouse_id": self.greenhouse_id,
            "risk_level": self.risk_level,
            "priority": self.priority,
            "diagnosis": self.diagnosis,
            "pathogen": self.pathogen,
            "conditions": sorted(self.conditions),
            "actions": [{"id": a.get("id"), "name": a.get("name"),
                         "efficacy": a.get("edge_efficacy") or a.get("efficacy"),
                         "phi_days": a.get("phi_days")}
                        for a in self.recommended_actions[:5]],
        }

    def compute_hash(self) -> str:
        payload = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":"))
        self.result_hash = hashlib.sha256(payload.encode()).hexdigest()
        return self.result_hash

    def to_dict(self) -> dict:
        return asdict(self)


def _confidence(risk_level: str, diagnosis: str | None, n_readings: int) -> dict:
    if diagnosis and risk_level == "HIGH" and n_readings:
        return {"level": "high", "value": 0.82,
                "driver": f"{n_readings} corroborating readings + knowledge-graph match"}
    if diagnosis:
        return {"level": "medium", "value": 0.60, "driver": "knowledge-graph match, limited corroboration"}
    return {"level": "low", "value": 0.35, "driver": "no active disease signal"}


class AdvisoryAgent:
    role = "Greenhouse Crop-Health Advisor"

    def __init__(self, settings) -> None:
        self.settings = settings
        self._agro = AgronomistAgent(settings)

    def report(self, store, gh_id: str, requested_by: str | None = None,
               risk_level: str | None = None, farm_id: str | None = None,
               narrate: bool = True) -> AdvisoryReport:
        """Produce the advisory report for one greenhouse (the deliverable Masumi sells).
        `narrate=False` skips the LLM (template only) — used for the fast co-op triage table."""
        requested_by = requested_by or DEFAULT_COOP["name"]
        alerts = store.list_alerts(gh_id, limit=1)
        path = self._agro.explain_alert(store, alerts[0]["id"], narrate=narrate) if alerts else None

        if path:
            rl = risk_level or (path["alert"].get("level") or "MED")
            diagnosis = (path.get("disease") or {}).get("name")
            pathogen = path.get("pathogen")
            conditions = path.get("conditions") or []
            trig = path.get("trigger_readings") or []
            actions = path.get("treatments") or []
            narrative = path.get("narrative") or ""
            nmode = path.get("narration_mode", "mock")
            backend = path.get("backend", store.mode)
        else:
            d = self._agro.diagnose(store, gh_id)
            rl = risk_level or ("MED" if d.get("diseases") else "LOW")
            top = (d.get("diseases") or [{}])[0]
            diagnosis = top.get("name")
            patho = kg.pathogen_of(top["id"]) if top.get("id") else None
            pathogen = patho["name"] if patho else None
            conditions = d.get("conditions") or []
            trig = []
            actions = d.get("treatments") or []
            narrative, nmode, backend = "", "mock", store.mode

        prio, rank = PRIORITY.get(rl, PRIORITY["LOW"])
        rep = AdvisoryReport(
            greenhouse_id=gh_id, farm_id=farm_id, requested_by=requested_by,
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            risk_level=rl, priority=prio, priority_rank=rank,
            diagnosis=diagnosis or "No active disease detected",
            pathogen=pathogen, confidence=_confidence(rl, diagnosis, len(trig)),
            conditions=conditions, trigger_readings=trig, recommended_actions=actions,
            narrative=narrative or self._fallback(diagnosis, conditions, actions),
            narration_mode=nmode, backend=backend, limits=LIMITS)
        rep.compute_hash()
        log.info("advisory report %s · %s · %s", gh_id, rep.diagnosis, rep.result_hash[:12])
        return rep

    @staticmethod
    def _fallback(diagnosis, conditions, actions) -> str:
        if not diagnosis:
            return ("No active disease signal from current conditions — continue routine "
                    "monitoring and keep ventilation up overnight.")
        tops = "; ".join(a["name"] for a in actions[:3]) or "cultural controls"
        cond = ", ".join(conditions) or "recent conditions"
        return (f"{diagnosis} is indicated by {cond}. Recommended, cheap/cultural first: {tops}. "
                "A field officer should confirm before spraying.")
