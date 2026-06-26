"""Risk-engine data models (plain, serializable)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

LEVEL_ORDER = {"LOW": 0, "MED": 1, "HIGH": 2}


@dataclass
class RuleResult:
    fired: bool
    level: str                       # LOW | MED | HIGH
    kind: str                        # late_blight | early_blight | tuta
    reason: str
    contributing_reading_ids: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def to_props(self) -> dict:
        return asdict(self)


@dataclass
class RiskAssessment:
    gh_id: str
    top: RuleResult                  # highest-severity fired rule (or a LOW none)
    results: list[RuleResult] = field(default_factory=list)

    @property
    def alert_worthy(self) -> bool:
        return self.top.fired and LEVEL_ORDER[self.top.level] >= LEVEL_ORDER["MED"]

    def to_dict(self) -> dict:
        return {"gh_id": self.gh_id, "top": self.top.to_props(),
                "results": [r.to_props() for r in self.results]}
