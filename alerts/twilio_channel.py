"""Twilio WhatsApp channel with SMS fallback. Never raises into the demo:
on any failure it degrades to the console (returns mode='mock')."""
from __future__ import annotations

from alerts.channel import Alert, AlertChannel, DeliveryResult
from alerts.console_channel import ConsoleChannel
from logging_setup import get_logger

log = get_logger("alerts.twilio")


class TwilioChannel(AlertChannel):
    mode = "live"

    def __init__(self, settings) -> None:
        self.settings = settings
        self._console = ConsoleChannel()
        self._client = None

    def _get_client(self):
        if self._client is None:
            from twilio.rest import Client  # lazy: optional dependency
            self._client = Client(self.settings.TWILIO_SID, self.settings.TWILIO_TOKEN)
        return self._client

    def send(self, to: str | None, alert: Alert) -> DeliveryResult:
        to = to or self.settings.FARMER_PHONE
        if not to:
            log.warning("No FARMER_PHONE set — falling back to console")
            return self._console.send(to, alert)
        # the farmer-facing, action-first message (already includes the Angawatch header)
        body = alert.message or alert.short()
        # 1) WhatsApp
        try:
            client = self._get_client()
            msg = client.messages.create(
                from_=self.settings.TWILIO_FROM,
                to=to if to.startswith("whatsapp:") else f"whatsapp:{to}",
                body=body,
            )
            log.info("[LIVE] WhatsApp sent sid=%s -> %s", msg.sid, to)
            return DeliveryResult(True, "live", "whatsapp", f"sid={msg.sid}")
        except Exception as exc:  # noqa: BLE001
            log.warning("WhatsApp failed (%s) — trying SMS", exc)
        # 2) SMS fallback
        try:
            sms_from = self.settings.TWILIO_SMS_FROM
            if sms_from:
                client = self._get_client()
                plain = to.replace("whatsapp:", "")
                msg = client.messages.create(from_=sms_from, to=plain, body=body)
                log.info("[LIVE] SMS sent sid=%s -> %s", msg.sid, plain)
                return DeliveryResult(True, "live", "sms", f"sid={msg.sid}")
        except Exception as exc:  # noqa: BLE001
            log.warning("SMS failed (%s) — falling back to console", exc)
        # 3) Console (labeled mock) — guarantees the demo never hard-fails
        return self._console.send(to, alert)
