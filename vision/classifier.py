"""classify(image) -> LeafDiagnosis using a pre-trained PlantVillage tomato model.

Inference only (no training). Lazy-loads the HF image-classification pipeline on
first use; on VISION_MODE=mock, missing deps, or any load/inference error it
falls back to the deterministic labeled mock. The deployed app should run mock to
keep the cloud build light.
"""
from __future__ import annotations

from logging_setup import get_logger, tag
from vision.models import LeafDiagnosis

log = get_logger("vision")
_PIPELINE = None
_LOAD_FAILED = False


def _clean_label(label: str) -> str:
    parts = str(label).replace("___", " · ").split(" · ")
    name = parts[-1].replace("_", " ").strip()
    return name[:1].upper() + name[1:] if name else str(label)


def _load_pipeline(model_id: str):
    global _PIPELINE, _LOAD_FAILED
    if _PIPELINE is not None or _LOAD_FAILED:
        return _PIPELINE
    try:
        from transformers import pipeline
        log.info("%s loading vision model %s (first call may download)…", tag("live"), model_id)
        _PIPELINE = pipeline("image-classification", model=model_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("%s vision model unavailable (%s) — using mock", tag("mock"), exc)
        _LOAD_FAILED = True
    return _PIPELINE


def _diagnose(label: str, conf: float) -> LeafDiagnosis:
    disease = _clean_label(label)
    healthy = "healthy" in label.lower()
    health = round(100 * conf, 1) if healthy else round(100 * (1 - conf), 1)
    severity = "low" if health >= 70 else "moderate" if health >= 40 else "high"
    return LeafDiagnosis(disease="Healthy" if healthy else disease, severity=severity,
                         health_score=health, confidence=round(conf, 3), mode="live",
                         raw_label=label)


def classify(image_path: str, settings=None) -> LeafDiagnosis:
    from config import get_settings
    settings = settings or get_settings()
    if settings.vision_mode() == "mock":
        from vision.mock_classifier import classify as mock_classify
        return mock_classify(image_path)

    pipe = _load_pipeline(settings.HF_MODEL_ID)
    if pipe is None:
        from vision.mock_classifier import classify as mock_classify
        return mock_classify(image_path)
    try:
        from PIL import Image
        preds = pipe(Image.open(image_path).convert("RGB"))
        top = preds[0]
        return _diagnose(top["label"], float(top["score"]))
    except Exception as exc:  # noqa: BLE001
        log.warning("%s inference failed (%s) — using mock", tag("mock"), exc)
        from vision.mock_classifier import classify as mock_classify
        return mock_classify(image_path)
