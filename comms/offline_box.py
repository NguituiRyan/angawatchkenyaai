"""Simulated in-greenhouse offline alert box (ESP32 + OLED + buzzer + LED).

For farms with NO cell/internet: a sensor node talks to this box over ESP-NOW
(peer-to-peer radio, no router) and it shows a short bilingual actionable alert
with colour + buzzer, for low-literacy users. This is a software simulation of
the hardware; the real node would POST the same readings to /ingest when online
(store-and-forward).
"""
from __future__ import annotations

from comms import i18n

# LED colour + buzzer pattern by severity
_LED = {"HIGH": "#E5484D", "MED": "#E8A317", "LOW": "#54B435"}
_BUZZER = {"HIGH": "long (10s) + pulse", "MED": "short pulse", "LOW": "silent"}
_ICON = {"late_blight": "drop", "early_blight": "leaf", "tuta": "bug", "": "leaf"}


def box_state(kind: str, level: str, lang: str | None) -> dict:
    line1, line2 = i18n.alert_lines(kind if level != "LOW" else "", level, lang)
    return {
        "level": level,
        "line1": line1,
        "line2": line2,
        "led": _LED.get(level, "#54B435"),
        "buzzer": _BUZZER.get(level, "silent"),
        "icon": _ICON.get(kind, "leaf"),
        "lang": lang or i18n.DEFAULT_LANG,
    }


def box_for_greenhouse(services, gh_id: str, lang: str | None) -> dict:
    """Compute the box display from the greenhouse's current risk."""
    top = services.engine.evaluate(gh_id).top
    return box_state(top.kind, top.level, lang)
