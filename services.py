"""Shared runtime services + orchestration.

ONE place builds the store, risk engine, alert channel and simulators, and exposes
the ingest pipeline (store -> evaluate -> alert). The CLI demo, the FastAPI ingest
endpoint and the Streamlit dashboard all call these same functions, so behaviour is
identical across surfaces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from alerts.dispatcher import alert_from_rule, build_channel, send_alert
from config import get_settings
from graph.seed import ensure_seeded
from graph.store import get_store
from logging_setup import get_logger
from risk.engine import RiskEngine
from risk.models import LEVEL_ORDER
from sim.generator import SensorSimulator

log = get_logger("services")


@dataclass
class Services:
    settings: Any
    store: Any
    engine: RiskEngine
    channel: Any
    sims: dict = field(default_factory=dict)
    _episode: dict = field(default_factory=dict)   # gh_id -> last alerted (kind, level)

    # --- simulator per greenhouse -----------------------------------------
    def simulator(self, gh_id: str) -> SensorSimulator:
        if gh_id not in self.sims:
            self.sims[gh_id] = SensorSimulator(greenhouse_id=gh_id)
        return self.sims[gh_id]

    def inject(self, gh_id: str, kind: str = "late_blight", ticks: int = 12) -> None:
        self.simulator(gh_id).inject_event(kind, ticks)

    # --- the ingest pipeline ----------------------------------------------
    def ingest(self, reading: Any, gh_id: str | None = None) -> dict:
        gh_id = gh_id or getattr(reading, "greenhouse_id", None) or \
            (reading.get("greenhouse_id") if isinstance(reading, dict) else None)
        reading_id = self.store.add_reading(gh_id, reading)
        assessment = self.engine.evaluate(gh_id)
        top = assessment.top
        out = {
            "reading_id": reading_id, "gh_id": gh_id,
            "level": top.level, "kind": top.kind, "fired": top.fired,
            "reason": top.reason, "metrics": top.metrics, "alert": None,
        }
        if assessment.alert_worthy and self._should_alert(gh_id, top):
            alert = alert_from_rule(gh_id, top, ts=_ts_of(reading))
            alert_id, result = send_alert(
                self.store, self.channel, alert,
                triggered_by=top.contributing_reading_ids,
                to=self.settings.FARMER_PHONE,
            )
            out["alert"] = {"id": alert_id, "level": alert.level, "kind": alert.kind,
                            "message": alert.message, "delivery": result.mode,
                            "provider": result.provider, "detail": result.detail}
        return out

    def tick_and_ingest(self, gh_id: str) -> dict:
        reading = self.simulator(gh_id).tick()
        return self.ingest(reading, gh_id=gh_id)

    def _should_alert(self, gh_id: str, top) -> bool:
        prev = self._episode.get(gh_id)
        if not top.fired or top.level == "LOW":
            self._episode.pop(gh_id, None)
            return False
        if prev and prev["kind"] == top.kind and \
                LEVEL_ORDER[top.level] <= LEVEL_ORDER[prev["level"]]:
            return False  # already alerted at >= this severity this episode
        self._episode[gh_id] = {"kind": top.kind, "level": top.level}
        return True


def _ts_of(reading: Any) -> str:
    if isinstance(reading, dict):
        return reading.get("ts", "")
    return getattr(reading, "ts", "")


def build_services(settings=None, seed: bool = True) -> Services:
    settings = settings or get_settings()
    store = get_store(settings)
    if hasattr(store, "apply_schema"):
        store.apply_schema()
    if seed and store.mode == "memory":
        ensure_seeded(store)            # memory is per-process -> always seed
    elif seed and store.stats()["node_total"] == 0:
        ensure_seeded(store)            # empty Neo4j -> seed once
    channel = build_channel(settings)
    return Services(settings=settings, store=store, engine=RiskEngine(store), channel=channel)
