"""Bilingual (English / Kiswahili) messages for alerts, SMS and the offline box.

NOTE: Kiswahili strings are a first pass for the demo — they should be reviewed by
a native-speaking agronomist before production (agronomic register matters). The
design (per-farmer language preference + a phrase table) is what's reusable.
"""
from __future__ import annotations

LANGS = ("en", "sw")
DEFAULT_LANG = "en"

# Short, action-first alert lines keyed by (kind, level). 2 lines max for SMS/OLED.
ALERTS: dict[tuple[str, str], dict[str, tuple[str, str]]] = {
    ("late_blight", "HIGH"): {
        "en": ("HIGH blight risk", "Ventilate at dawn + spray protectant fungicide"),
        "sw": ("Hatari kubwa ya ukungu", "Pitisha hewa asubuhi + nyunyiza dawa ya kuzuia"),
    },
    ("late_blight", "MED"): {
        "en": ("Blight risk rising", "Monitor closely; prepare to spray"),
        "sw": ("Hatari ya ukungu inaongezeka", "Fuatilia kwa karibu; jiandae kunyunyiza"),
    },
    ("early_blight", "HIGH"): {
        "en": ("Early blight HIGH", "Remove lower leaves + apply fungicide"),
        "sw": ("Baka la mapema - hatari", "Ondoa majani ya chini + weka dawa"),
    },
    ("early_blight", "MED"): {
        "en": ("Early blight watch", "Scout lower canopy for spots"),
        "sw": ("Angalia baka la mapema", "Kagua majani ya chini kuona madoa"),
    },
    ("tuta", "HIGH"): {
        "en": ("Tuta pest HIGH", "Start mass trapping + targeted control"),
        "sw": ("Wadudu Tuta - hatari", "Anza kutega kwa wingi + udhibiti"),
    },
    ("tuta", "MED"): {
        "en": ("Tuta pest rising", "Add traps + scout for leaf mines"),
        "sw": ("Wadudu Tuta wanaongezeka", "Ongeza mitego + kagua majani"),
    },
}
OK = {"en": ("All clear", "Conditions normal"),
      "sw": ("Salama", "Hali ni shwari")}

UI = {
    "status_title": {"en": "Greenhouse {gh}", "sw": "Banda {gh}"},
    "status_body": {"en": "{temp}C, humidity {hum}%, risk {lvl}",
                    "sw": "{temp}C, unyevu {hum}%, hatari {lvl}"},
    "risk_word": {"en": {"HIGH": "HIGH", "MED": "MODERATE", "LOW": "LOW"},
                  "sw": {"HIGH": "KUBWA", "MED": "WASTANI", "LOW": "NDOGO"}},
    "loan": {"en": "Credit score {score}/100, Band {band} - {limit}. A loan officer approves.",
             "sw": "Alama ya mkopo {score}/100, Daraja {band} - {limit}. Afisa wa mkopo ataidhinisha."},
    "subscribed": {"en": "Subscribed to Angawatch alerts. Reply STOP to opt out.",
                   "sw": "Umejisajili arifa za Angawatch. Jibu STOP kuacha."},
    "stopped": {"en": "Unsubscribed. Reply ALERTS to re-join.",
                "sw": "Umejiondoa. Jibu ALERTS kujiunga tena."},
    "lang_set": {"en": "Language set to English.", "sw": "Lugha imewekwa Kiswahili."},
    "help": {"en": "Angawatch: text STATUS, LOAN, ALERTS, SW/EN, or STOP.",
             "sw": "Angawatch: andika STATUS, LOAN (MKOPO), ALERTS, SW/EN, au STOP."},
    "unknown": {"en": "Sorry, didn't get that. Text HELP for options.",
                "sw": "Samahani, sikuelewa. Andika HELP kwa chaguo."},
}


def _lang(lang: str | None) -> str:
    return lang if lang in LANGS else DEFAULT_LANG


def alert_lines(kind: str, level: str, lang: str | None) -> tuple[str, str]:
    lang = _lang(lang)
    if level == "LOW" or not kind:
        return OK[lang]
    return ALERTS.get((kind, level), OK)[lang]


def alert_text(kind: str, level: str, lang: str | None) -> str:
    t, b = alert_lines(kind, level, lang)
    return f"{t}: {b}"


def ui(key: str, lang: str | None, **kw) -> str:
    lang = _lang(lang)
    val = UI[key][lang]
    return val.format(**kw) if kw else val


def risk_word(level: str, lang: str | None) -> str:
    return UI["risk_word"][_lang(lang)].get(level, level)
