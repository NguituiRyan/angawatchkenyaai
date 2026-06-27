"""Twilio WhatsApp channel with SMS fallback. Never raises into the demo:
on any failure it degrades to the console (returns mode='mock')."""
from __future__ import annotations

from alerts.channel import Alert, AlertChannel, DeliveryResult, split_recipients
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
        nums = split_recipients(to or self.settings.FARMER_PHONE)
        if not nums:
            log.warning("No FARMER_PHONE set — falling back to console")
            return self._console.send(to, alert)
        # the farmer-facing, action-first message (already includes the Angawatch header)
        body = alert.message or alert.short()
        sids = []
        for n in nums:                       # WhatsApp to each recipient
            try:
                msg = self._get_client().messages.create(
                    from_=self.settings.TWILIO_FROM, to=f"whatsapp:{n}", body=body)
                log.info("[LIVE] WhatsApp sent sid=%s -> %s", msg.sid, n)
                sids.append(msg.sid)
            except Exception as exc:  # noqa: BLE001
                log.warning("WhatsApp to %s failed (%s)", n, exc)
        if sids:
            return DeliveryResult(True, "live", "whatsapp",
                                  f"{len(sids)}/{len(nums)} sent ({sids[0]})")
        # Optional Twilio-SMS fallback (only if a real SMS-capable number is set)
        sms_from = self.settings.TWILIO_SMS_FROM
        if sms_from:
            for n in nums:
                try:
                    msg = self._get_client().messages.create(from_=sms_from, to=n, body=body)
                    log.info("[LIVE] SMS sent sid=%s -> %s", msg.sid, n)
                    sids.append(msg.sid)
                except Exception as exc:  # noqa: BLE001
                    log.warning("SMS to %s failed (%s)", n, exc)
            if sids:
                return DeliveryResult(True, "live", "sms", f"{len(sids)}/{len(nums)} sent")
        # Console (labeled mock) — guarantees the demo never hard-fails
        return self._console.send(", ".join(nums), alert)
