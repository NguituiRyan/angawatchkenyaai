"""Africa's Talking SMS channel — real SMS to a Kenyan phone (alongside Twilio WhatsApp).

Sends the same farmer-facing, bilingual (EN/SW) alert message over SMS via the Africa's
Talking REST API. Never raises into the demo: on any failure it degrades to the console
(returns mode='mock'). Uses raw HTTP (requests) so no extra dependency.

LIVE account -> real phone. Sandbox (AT_SANDBOX=1 or AT_USERNAME='sandbox') -> the AT
simulator app, not a real handset.
"""
from __future__ import annotations

from alerts.channel import Alert, AlertChannel, DeliveryResult
from alerts.console_channel import ConsoleChannel
from logging_setup import get_logger

log = get_logger("alerts.africastalking")

_LIVE = "https://api.africastalking.com"
_SANDBOX = "https://api.sandbox.africastalking.com"


def _sms_safe(text: str) -> str:
    """Trim the alert to a plain SMS body (drop emoji / non-GSM glyphs -> cheaper segments)."""
    return (text or "").replace("⚠️", "").replace("·", "-").replace("→", "->").strip()


class AfricasTalkingChannel(AlertChannel):
    mode = "live"

    def __init__(self, settings) -> None:
        self.settings = settings
        self._console = ConsoleChannel()

    def send(self, to: str | None, alert: Alert) -> DeliveryResult:
        to = (to or self.settings.FARMER_PHONE or "").replace("whatsapp:", "")
        if not to:
            return self._console.send(to, alert)
        sandbox = bool(self.settings.AT_SANDBOX) or self.settings.AT_USERNAME == "sandbox"
        base = _SANDBOX if sandbox else _LIVE
        data = {"username": self.settings.AT_USERNAME, "to": to, "message": _sms_safe(alert.message)}
        if self.settings.AT_SENDER_ID:
            data["from"] = self.settings.AT_SENDER_ID
        try:
            import requests
            resp = requests.post(
                f"{base}/version1/messaging",
                headers={"apiKey": self.settings.AT_API_KEY, "Accept": "application/json",
                         "Content-Type": "application/x-www-form-urlencoded"},
                data=data, timeout=20)
            resp.raise_for_status()
            recips = resp.json().get("SMSMessageData", {}).get("Recipients", [])
            sent = next((r for r in recips if r.get("status") == "Success"), None)
            if sent:
                log.info("[LIVE] AT SMS sent id=%s -> %s (%s)", sent.get("messageId"),
                         to, sent.get("cost"))
                return DeliveryResult(True, "live", "sms",
                                      f"AT id={sent.get('messageId')} {sent.get('cost','')}".strip())
            why = recips[0].get("status") if recips else \
                resp.json().get("SMSMessageData", {}).get("Message", "no recipients")
            log.warning("AT SMS not delivered (%s)", why)
        except Exception as exc:  # noqa: BLE001
            log.warning("Africa's Talking SMS failed (%s) — console", exc)
        return self._console.send(to, alert)
