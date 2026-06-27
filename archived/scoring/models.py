"""Credit-scoring data models + band mappings + the on-chain result hash.

The hash commits to the NUMBERS (not the prose narrative), so the on-chain audit
proof is reproducible: re-running the scorer yields the same hash.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

# Human-in-the-loop limit statements — emitted with EVERY assessment.
LIMIT_STATEMENTS = [
    "This is a RECOMMENDATION to support a loan officer — not an automated lending decision.",
    "Score is derived from synthetic/anonymized farm-and-sensor data only; no credit-bureau or KYC data is included.",
    "Thin-file caution applies below 3 seasons of history.",
    "Final approval requires human loan-officer review and standard KYC/AML checks.",
]


@dataclass
class Factor:
    name: str
    label: str
    raw_value: float
    sub_score: float          # 0-100
    weight: float
    contribution: float       # weight * sub_score
    evidence: dict = field(default_factory=dict)
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def credit_band(score: float) -> dict:
    if score >= 75:
        return {"grade": "A", "limit_kes": 150000, "limit": "up to KES 150,000"}
    if score >= 60:
        return {"grade": "B", "limit_kes": 80000, "limit": "up to KES 80,000"}
    if score >= 45:
        return {"grade": "C", "limit_kes": 35000, "limit": "up to KES 35,000"}
    return {"grade": "D", "limit_kes": 0, "limit": "refer — micro-pilot only"}


def insurance_band(score: float) -> dict:
    if score >= 75:
        return {"grade": "Preferred", "note": "low premium"}
    if score >= 60:
        return {"grade": "Standard", "note": "standard premium"}
    if score >= 45:
        return {"grade": "Loaded", "note": "+25% premium"}
    return {"grade": "Decline", "note": "manual underwriting only"}


@dataclass
class CreditAssessment:
    farmer_id: str
    overall_score: float
    factors: list[Factor]
    confidence: dict                      # {level, value, driver}
    credit: dict                          # credit_band(...)
    insurance: dict                       # insurance_band(...)
    narrative: str = ""
    limits: list[str] = field(default_factory=lambda: list(LIMIT_STATEMENTS))
    mode: dict = field(default_factory=lambda: {"scorer": "deterministic", "narration": "mock"})
    generated_at: str = ""
    result_hash: str = ""

    def canonical(self) -> dict:
        """The deterministic payload the result_hash commits to (no prose/time)."""
        return {
            "farmer_id": self.farmer_id,
            "overall_score": round(self.overall_score, 2),
            "credit": self.credit, "insurance": self.insurance,
            "confidence": {"level": self.confidence.get("level"),
                           "value": round(self.confidence.get("value", 0), 3)},
            "factors": [
                {"name": f.name, "sub_score": round(f.sub_score, 2),
                 "weight": f.weight, "contribution": round(f.contribution, 3)}
                for f in self.factors
            ],
        }

    def compute_hash(self) -> str:
        blob = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":"))
        self.result_hash = hashlib.sha256(blob.encode()).hexdigest()
        return self.result_hash

    def to_dict(self) -> dict:
        return {
            "farmer_id": self.farmer_id,
            "generated_at": self.generated_at,
            "overall_score": round(self.overall_score, 1),
            "credit_band": self.credit,
            "insurance_band": self.insurance,
            "confidence": self.confidence,
            "factors": [f.to_dict() for f in self.factors],
            "narrative": self.narrative,
            "limits": self.limits,
            "mode": self.mode,
            "result_hash": self.result_hash,
        }
