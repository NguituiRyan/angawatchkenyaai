"""Deterministic labeled-mock leaf classifier (no model download needed)."""
from __future__ import annotations

import hashlib
from pathlib import Path

from vision.models import LeafDiagnosis

_OPTIONS = [
    ("Late blight", "high", 38.0, 0.86, "Tomato___Late_blight"),
    ("Early blight", "moderate", 55.0, 0.78, "Tomato___Early_blight"),
    ("Leaf Mold", "moderate", 60.0, 0.71, "Tomato___Leaf_Mold"),
    ("Healthy", "low", 94.0, 0.93, "Tomato___healthy"),
]


def classify(image_path: str) -> LeafDiagnosis:
    name = Path(str(image_path)).name.lower()
    if "healthy" in name:
        d = _OPTIONS[3]
    elif "early" in name:
        d = _OPTIONS[1]
    elif "late" in name or "blight" in name:
        d = _OPTIONS[0]
    else:  # deterministic pick from the filename
        idx = int(hashlib.sha256(name.encode()).hexdigest(), 16) % len(_OPTIONS)
        d = _OPTIONS[idx]
    disease, severity, health, conf, raw = d
    return LeafDiagnosis(disease=disease, severity=severity, health_score=health,
                         confidence=conf, mode="mock", raw_label=raw)
