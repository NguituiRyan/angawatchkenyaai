"""Build the right AlertChannel, convert a RuleResult to an Alert, send + record."""
from __future__ import annotations

from alerts.channel import Alert, AlertChannel, DeliveryResult
from alerts.console_channel import ConsoleChannel
from logging_setup import get_logger, tag

log = get_logger("alerts.dispatch")


def build_channel(settings) -> AlertChannel:
    if settings.alert_mode() == "live":
        from alerts.twilio_channel import TwilioChannel
        log.info("%s alert channel: Twilio WhatsApp/SMS", tag("live"))
        return TwilioChannel(settings)
    log.info("%s alert channel: console (no Twilio creds)", tag("mock"))
    return ConsoleChannel()


def alert_from_rule(gh_id: str, result, ts: str, lead_time_hr: float = 24.0) -> Alert:
    return Alert(gh_id=gh_id, kind=result.kind, level=result.level,
                 message=result.reason, ts=ts, lead_time_hr=lead_time_hr,
                 channel="whatsapp")


def send_alert(store, channel: AlertChannel, alert: Alert,
               triggered_by: list[str] | None = None,
               to: str | None = None) -> tuple[str, DeliveryResult]:
    """Send via the channel, stamp delivery mode, persist the Alert node."""
    result = channel.send(to, alert)
    alert.delivery = result.mode
    alert_id = store.add_alert(alert.gh_id, alert, triggered_by=triggered_by or [])
    alert.id = alert_id
    log.info("Alert %s recorded (delivery=%s via %s)", alert_id, result.mode, result.provider)
    return alert_id, result
