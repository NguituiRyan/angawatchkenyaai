"""RiskEngine: take a recent TIME window from the store, run all rules, pick worst.

We bound the window by time (not just count) so historical seed readings from past
seasons never contaminate live monitoring of current conditions.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from risk.models import LEVEL_ORDER, RiskAssessment, RuleResult
from risk.rules import early_blight, late_blight, tuta_degree_day


def _parse(ts) -> datetime | None:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return None


class RiskEngine:
    def __init__(self, store, window_hours: int = 48, fetch_limit: int = 240) -> None:
        self.store = store
        self.window_hours = window_hours
        self.fetch_limit = fetch_limit

    def _recent_window(self, gh_id: str, new_reading: dict | None) -> list[dict]:
        readings = list(self.store.list_recent_readings(gh_id, limit=self.fetch_limit))
        if new_reading is not None:
            rid = new_reading.get("id") if isinstance(new_reading, dict) else None
            if not any(r.get("id") == rid for r in readings):
                readings = [new_reading] + readings
        stamped = [(r, _parse(r.get("ts"))) for r in readings]
        stamped = [(r, t) for r, t in stamped if t is not None]
        if not stamped:
            return [r for r in readings]
        latest = max(t for _, t in stamped)
        cutoff = latest - timedelta(hours=self.window_hours)
        return [r for r, t in stamped if t >= cutoff]

    def evaluate(self, gh_id: str, new_reading: dict | None = None) -> RiskAssessment:
        window = self._recent_window(gh_id, new_reading)
        results: list[RuleResult] = [
            late_blight(window),
            early_blight(window),
            tuta_degree_day(window, accumulated_dd=0.0),
        ]
        top = max(results, key=lambda r: (r.fired, LEVEL_ORDER[r.level]))
        return RiskAssessment(gh_id=gh_id, top=top, results=results)
