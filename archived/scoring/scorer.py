"""CreditScorer: subgraph -> deterministic CreditAssessment (numbers + hash).

The LLM is NOT involved here. agents/credit_crew.py adds the prose narrative on top.
"""
from __future__ import annotations

from datetime import datetime

from scoring.factors import ALL_FACTORS
from scoring.models import CreditAssessment, credit_band, insurance_band

_BASE_CONF = {0: 0.30, 1: 0.42, 2: 0.56, 3: 0.70}


def _confidence(sub: dict, n_seasons: int) -> dict:
    base = _BASE_CONF.get(n_seasons, 0.80 if n_seasons >= 4 else 0.30)
    harvests = sub.get("harvests", [])
    checks = [
        bool(harvests),
        all(h.get("loss_pct") is not None for h in harvests) if harvests else False,
        sub.get("alert_count", 0) > 0,
        bool(sub.get("greenhouse")),
    ]
    completeness = sum(checks) / len(checks)
    value = round(base * (0.7 + 0.3 * completeness), 3)
    level = "high" if value >= 0.7 else "medium" if value >= 0.5 else "low"
    driver = f"{n_seasons} season(s) of history, {int(completeness * 100)}% record completeness"
    return {"level": level, "value": value, "driver": driver}


class CreditScorer:
    def score(self, subgraph: dict) -> CreditAssessment:
        if not subgraph or not subgraph.get("farmer"):
            raise ValueError("subgraph has no farmer")
        factors = [f(subgraph) for f in ALL_FACTORS]
        overall = round(sum(f.contribution for f in factors), 1)
        n_seasons = max(len(subgraph.get("seasons", [])), len(subgraph.get("harvests", [])))
        assessment = CreditAssessment(
            farmer_id=subgraph["farmer"]["id"],
            overall_score=overall,
            factors=factors,
            confidence=_confidence(subgraph, n_seasons),
            credit=credit_band(overall),
            insurance=insurance_band(overall),
            generated_at=datetime.now().isoformat(timespec="seconds"),
        )
        assessment.compute_hash()
        return assessment

    def score_farmer(self, store, farmer_id: str) -> CreditAssessment:
        return self.score(store.get_farmer_subgraph(farmer_id))
