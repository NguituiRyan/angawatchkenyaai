"""Two-way SMS for feature phones (bilingual EN/SW), reusing the real engine.

A farmer texts a keyword to the Angawatch number and gets an instant reply:
  STATUS / HALI   -> live greenhouse status + any action alert
  LOAN / MKOPO    -> credit score, band and limit (a loan officer approves)
  ALERTS          -> subscribe to push alerts   STOP -> unsubscribe
  SW / EN         -> set language               HELP -> options

handle_inbound() returns the reply text. An Africa's Talking webhook (the Kenyan
USSD/SMS aggregator) or the built-in simulator can drive it. Outbound push alerts
reuse alert_sms().
"""
from __future__ import annotations

from comms import i18n
from logging_setup import get_logger

log = get_logger("comms.sms")

_KW = {
    "status": {"STATUS", "HALI", "STATS"},
    "loan": {"LOAN", "MKOPO", "CREDIT"},
    "subscribe": {"ALERTS", "ARIFA", "ON", "SUBSCRIBE", "JIUNGE"},
    "stop": {"STOP", "ACHA", "OFF"},
    "sw": {"SW", "KISWAHILI", "SWAHILI"},
    "en": {"EN", "ENGLISH", "KIINGEREZA"},
    "help": {"HELP", "MSAADA", "?"},
}


def _kind(text: str) -> str:
    word = (text or "").strip().upper().split()[0] if text.strip() else "HELP"
    for k, words in _KW.items():
        if word in words:
            return k
    return "unknown"


def handle_inbound(services, farmer_id: str, text: str) -> dict:
    store = services.store
    sub = store.get_farmer_subgraph(farmer_id)
    farmer = sub.get("farmer") or {}
    lang = farmer.get("language") or i18n.DEFAULT_LANG
    gh = (sub.get("greenhouse") or {}).get("id") or services.settings.DEFAULT_GREENHOUSE_ID
    kind = _kind(text)

    if kind == "status":
        rs = store.list_recent_readings(gh, limit=1)
        r = rs[0] if rs else {}
        top = services.engine.evaluate(gh).top
        title = i18n.ui("status_title", lang, gh=gh)
        body = i18n.ui("status_body", lang, temp=round(r.get("temp_c", 0)),
                       hum=round(r.get("humidity", 0)), lvl=i18n.risk_word(top.level, lang))
        reply = f"{title}: {body}"
        if top.fired and top.level != "LOW":
            reply += "\n" + i18n.alert_text(top.kind, top.level, lang)
    elif kind == "loan":
        from scoring.scorer import CreditScorer
        a = CreditScorer().score_farmer(store, farmer_id)
        reply = i18n.ui("loan", lang, score=int(round(a.overall_score)),
                        band=a.credit["grade"], limit=a.credit["limit"])
    elif kind == "subscribe":
        store.update_farmer(farmer_id, subscribed=True)
        reply = i18n.ui("subscribed", lang)
    elif kind == "stop":
        store.update_farmer(farmer_id, subscribed=False)
        reply = i18n.ui("stopped", lang)
    elif kind in ("sw", "en"):
        lang = kind
        store.update_farmer(farmer_id, language=lang)
        reply = i18n.ui("lang_set", lang)
    elif kind == "help":
        reply = i18n.ui("help", lang)
    else:
        reply = i18n.ui("unknown", lang)

    log.info("[SIM SMS] %s '%s' -> %s", farmer_id, (text or "").strip(), kind)
    return {"reply": reply, "lang": lang, "keyword": kind, "to": farmer.get("phone")}


def alert_sms(kind: str, level: str, lang: str | None) -> str:
    """Outbound push-alert SMS body (bilingual)."""
    return "Angawatch: " + i18n.alert_text(kind, level, lang)
