"""Standalone vision demo:  python -m vision.demo [image_path]

Classifies a tomato leaf image. Uses the real HF PlantVillage model when
available (VISION_MODE=live and transformers/torch installed), else the labeled
mock. Drop a real PlantVillage tomato leaf into data/sample_leaf/ for a live run.
"""
from __future__ import annotations

import sys
from pathlib import Path

from logging_setup import tag
from vision.classifier import classify

DEFAULT = Path(__file__).resolve().parents[1] / "data" / "sample_leaf" / "tomato_leaf_blight.png"


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT)
    d = classify(path)
    print(f"\nImage: {path}")
    print(f"{tag(d.mode)} classifier ({d.mode})")
    print(f"  Disease      : {d.disease}")
    print(f"  Severity     : {d.severity}")
    print(f"  Health score : {d.health_score}/100")
    print(f"  Confidence   : {d.confidence}")
    print(f"  Raw label    : {d.raw_label}\n")


if __name__ == "__main__":
    main()
