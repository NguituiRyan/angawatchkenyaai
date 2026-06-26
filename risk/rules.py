"""PURE agronomic risk rules — no I/O, no LLM. Unit-tested, citable.

Thresholds:
- Late blight (Hutton/BLITECAST/Smith): RH>=90% AND 10-26C sustained >=6h => HIGH
  (>=3h => MED). Demo-compressed from the Hutton "two consecutive days" criterion
  to a single sustained high-risk period so the alert fires within a live demo.
- Early blight (Alternaria): RH>=90% AND 20-32C AND leaf-wetness>=5h sustained.
- Tuta absoluta: degree-day model DD=max(0,(Tmax+Tmin)/2 - 8.0); ~340 DD per
  egg->adult generation; pheromone-trap action threshold >=3 males/trap/week.
"""
from __future__ import annotations

from datetime import datetime
from statistics import median
from typing import Any, Callable

from graph.common import to_props
from risk.models import RuleResult

TUTA_TBASE = 8.0
TUTA_GENERATION_DD = 340.0


def _as_dict(r: Any) -> dict:
    return r if isinstance(r, dict) else to_props(r)


def _parse_ts(v: Any) -> datetime:
    if isinstance(v, datetime):
        return v
    return datetime.fromisoformat(str(v).replace("Z", "+00:00"))


def _sorted(readings: list) -> list[dict]:
    rs = [_as_dict(r) for r in readings]
    return sorted(rs, key=lambda r: str(r.get("ts", "")))


def _step_hours(rs: list[dict]) -> float:
    ts = [_parse_ts(r["ts"]) for r in rs if r.get("ts")]
    if len(ts) < 2:
        return 1.0
    gaps = [(ts[i] - ts[i - 1]).total_seconds() / 3600 for i in range(1, len(ts))]
    gaps = [g for g in gaps if g > 0]
    return median(gaps) if gaps else 1.0


def _longest_run(rs: list[dict], pred: Callable[[dict], bool]) -> list[dict]:
    best: list[dict] = []
    cur: list[dict] = []
    for r in rs:
        if pred(r):
            cur.append(r)
            if len(cur) > len(best):
                best = list(cur)
        else:
            cur = []
    return best


def _none(kind: str, msg: str = "conditions normal") -> RuleResult:
    return RuleResult(fired=False, level="LOW", kind=kind, reason=msg)


# ---------------------------------------------------------------------------
def late_blight(readings: list) -> RuleResult:
    rs = _sorted(readings)
    if not rs:
        return _none("late_blight")
    step = _step_hours(rs)
    run = _longest_run(rs, lambda r: r.get("humidity", 0) >= 90
                       and 10 <= r.get("temp_c", -99) <= 26)
    hours = round(len(run) * step, 1)
    if not run:
        return _none("late_blight")
    max_rh = max(r.get("humidity", 0) for r in run)
    temps = [r.get("temp_c") for r in run]
    metrics = {"sustained_hr": hours, "max_rh": round(max_rh, 1),
               "temp_min": min(temps), "temp_max": max(temps), "step_hr": step}
    ids = [r.get("id") for r in run if r.get("id")]
    if hours >= 6:
        return RuleResult(True, "HIGH", "late_blight",
                          f"Late-blight HIGH: RH>=90% and 10-26C sustained ~{hours}h "
                          f"(max RH {max_rh:.0f}%). Ventilate at dawn and apply protectant fungicide.",
                          ids, metrics)
    if hours >= 3:
        return RuleResult(True, "MED", "late_blight",
                          f"Late-blight MODERATE: favourable conditions ~{hours}h "
                          f"(max RH {max_rh:.0f}%). Monitor closely; prepare to spray.",
                          ids, metrics)
    return _none("late_blight", f"brief favourable window (~{hours}h)")


def early_blight(readings: list) -> RuleResult:
    rs = _sorted(readings)
    if not rs:
        return _none("early_blight")
    step = _step_hours(rs)
    run = _longest_run(rs, lambda r: r.get("humidity", 0) >= 90
                       and 20 <= r.get("temp_c", -99) <= 32
                       and r.get("leaf_wetness_hr", 0) >= 5)
    hours = round(len(run) * step, 1)
    if not run:
        return _none("early_blight")
    ids = [r.get("id") for r in run if r.get("id")]
    metrics = {"sustained_hr": hours, "step_hr": step}
    if hours >= 5:
        return RuleResult(True, "HIGH", "early_blight",
                          f"Early-blight HIGH: warm, wet leaves sustained ~{hours}h. "
                          "Remove lower infected leaves and apply fungicide.", ids, metrics)
    if hours >= 2:
        return RuleResult(True, "MED", "early_blight",
                          f"Early-blight MODERATE: warm + leaf wetness ~{hours}h. Scout lower canopy.",
                          ids, metrics)
    return _none("early_blight")


def tuta_degree_day(readings: list, accumulated_dd: float = 0.0) -> RuleResult:
    rs = _sorted(readings)
    if not rs:
        return _none("tuta", "no readings")
    # Degree-days from daily (Tmax+Tmin)/2 - Tbase
    by_day: dict[str, list[float]] = {}
    for r in rs:
        day = str(r.get("ts", ""))[:10]
        by_day.setdefault(day, []).append(r.get("temp_c", 0.0))
    dd_window = sum(max(0.0, (max(t) + min(t)) / 2 - TUTA_TBASE) for t in by_day.values())
    new_accum = round(accumulated_dd + dd_window, 1)

    latest_trap = max((r.get("trap_count", 0) for r in rs[-3:]), default=0)
    ids = [r.get("id") for r in rs[-3:] if r.get("id")]
    generation_imminent = new_accum >= TUTA_GENERATION_DD
    metrics = {"dd_window": round(dd_window, 1), "accumulated_dd": new_accum,
               "trap_count": latest_trap, "generation_dd": TUTA_GENERATION_DD,
               "generation_imminent": generation_imminent}

    if latest_trap >= 6:
        return RuleResult(True, "HIGH", "tuta",
                          f"Tuta absoluta HIGH: {latest_trap} males/trap/week (>=6). "
                          "Start mass trapping and targeted control; remove mined leaves.",
                          ids, metrics)
    if latest_trap >= 3 or generation_imminent:
        why = f"{latest_trap} males/trap/week" if latest_trap >= 3 else \
              f"{new_accum:.0f} degree-days (generation due ~{TUTA_GENERATION_DD:.0f})"
        return RuleResult(True, "MED", "tuta",
                          f"Tuta absoluta MODERATE: {why}. Increase trap density and scout for mines.",
                          ids, metrics)
    return _none("tuta", f"low pest pressure ({latest_trap}/trap/wk, {new_accum:.0f} DD)")


ALL_RULES = ("late_blight", "early_blight", "tuta")
