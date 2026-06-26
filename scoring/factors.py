"""The 7 PURE credit factors. Each maps the farmer subgraph -> a Factor with
its raw value, 0-100 sub-score, weight, contribution and the graph evidence that
justifies it. No I/O, no LLM — fully unit-testable and reproducible.
"""
from __future__ import annotations

from math import tanh
from statistics import mean, pstdev

from scoring.models import Factor

WEIGHTS = {
    "yield_consistency": 0.22,
    "harvest_trend": 0.18,
    "alert_response_rate": 0.20,
    "disease_pressure_handled": 0.12,
    "seasons_of_history": 0.10,
    "cooperative_membership": 0.08,
    "climate_resilience": 0.10,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _yields(sub: dict) -> list[float]:
    return [h["yield_kg"] for h in sub.get("harvests", []) if h.get("yield_kg") is not None]


def _factor(name, label, raw, sub_score, evidence, note=""):
    w = WEIGHTS[name]
    sub_score = round(_clamp(sub_score), 1)
    return Factor(name=name, label=label, raw_value=round(raw, 3), sub_score=sub_score,
                  weight=w, contribution=round(w * sub_score, 2), evidence=evidence, note=note)


def yield_consistency(sub: dict) -> Factor:
    ys = _yields(sub)
    if len(ys) < 2:
        return _factor("yield_consistency", "Yield consistency", 0.0, 60.0,
                       {"yields_kg": ys}, "needs >=2 seasons for a reliable estimate")
    m = mean(ys)
    cv = (pstdev(ys) / m) if m else 0.0
    sub_score = 100 * (1 - cv / 0.5)        # CV 0 -> 100; CV 0.5 -> 0
    return _factor("yield_consistency", "Yield consistency (low variation)", cv, sub_score,
                   {"yields_kg": ys, "cv": round(cv, 3)})


def harvest_trend(sub: dict) -> Factor:
    hs = [h for h in sub.get("harvests", []) if h.get("yield_kg") is not None]
    ys = [h["yield_kg"] for h in hs]
    if len(ys) < 2:
        return _factor("harvest_trend", "Harvest trend", 0.0, 55.0, {"yields_kg": ys},
                       "needs >=2 seasons to detect a trend")
    xs = [h.get("season_index") or (i + 1) for i, h in enumerate(hs)]
    xm, ym = mean(xs), mean(ys)
    denom = sum((x - xm) ** 2 for x in xs) or 1.0
    slope = sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / denom
    norm = slope / ym if ym else 0.0          # fractional change per season
    sub_score = 50 + 50 * tanh(norm * 6)
    return _factor("harvest_trend", "Harvest trend (improving yields)", slope, sub_score,
                   {"yields_kg": ys, "slope_kg_per_season": round(slope, 1),
                    "pct_per_season": round(norm * 100, 1)})


def alert_response_rate(sub: dict) -> Factor:
    ac = sub.get("alert_count", 0)
    act = sub.get("action_count", 0)
    if ac == 0:
        return _factor("alert_response_rate", "Alert-response rate", 0.0, 70.0,
                       {"alerts": 0, "actioned": 0}, "no alerts on record yet")
    rate = act / ac
    return _factor("alert_response_rate", "Alert-response rate (acts on warnings)", rate,
                   100 * rate, {"alerts": ac, "actioned": act, "rate": round(rate, 2)})


def disease_pressure_handled(sub: dict) -> Factor:
    losses = [h["loss_pct"] for h in sub.get("harvests", []) if h.get("loss_pct") is not None]
    high_alerts = sum(1 for a in sub.get("alerts", []) if a.get("level") == "HIGH")
    if not losses:
        return _factor("disease_pressure_handled", "Disease pressure handled", 0.0, 60.0,
                       {"loss_pct": []}, "no harvest-loss records")
    mean_loss = mean(losses) / 100.0
    sub_score = 100 * (1 - mean_loss)
    return _factor("disease_pressure_handled", "Disease pressure handled (low losses)",
                   mean_loss, sub_score,
                   {"loss_pct_by_season": losses, "mean_loss_pct": round(mean(losses), 1),
                    "high_alerts": high_alerts})


def seasons_of_history(sub: dict) -> Factor:
    n = max(len(sub.get("seasons", [])), len(sub.get("harvests", [])))
    return _factor("seasons_of_history", "Seasons of verified history", float(n),
                   min(100, n * 25), {"seasons": n})


def cooperative_membership(sub: dict) -> Factor:
    coop = sub.get("cooperative")
    if coop:
        members = coop.get("members", 0) or 0
        sub_score = 80 + min(20, members / 20)
        return _factor("cooperative_membership", "Cooperative membership", 1.0, sub_score,
                       {"cooperative": coop.get("name"), "members": members})
    return _factor("cooperative_membership", "Cooperative membership", 0.0, 40.0,
                   {"cooperative": None}, "not a cooperative member (weaker peer guarantee)")


def climate_resilience(sub: dict) -> Factor:
    gh = sub.get("greenhouse") or {}
    cr = gh.get("climate_resilience")
    cr = 0.5 if cr is None else cr
    return _factor("climate_resilience", "Climate/structure resilience", cr, 100 * cr,
                   {"structure_type": gh.get("structure_type"),
                    "has_netting": gh.get("has_netting"),
                    "irrigation": gh.get("irrigation"),
                    "climate_resilience": cr})


ALL_FACTORS = [
    yield_consistency, harvest_trend, alert_response_rate, disease_pressure_handled,
    seasons_of_history, cooperative_membership, climate_resilience,
]
