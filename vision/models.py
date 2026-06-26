"""Leaf diagnosis model."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class LeafDiagnosis:
    disease: str            # cleaned label, e.g. "Late blight" / "Healthy"
    severity: str           # low | moderate | high
    health_score: float     # 0-100 (100 = healthy)
    confidence: float       # 0-1 top-class probability
    mode: str               # live | mock
    raw_label: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
