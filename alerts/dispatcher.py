"""Build the right AlertChannel, convert a RuleResult to an Alert, send + record."""
from __future__ import annotations

from alerts.channel import Alert, AlertChannel, DeliveryResult
from alerts.console_channel import ConsoleChannel
from logging_setup import get_logger, tag

log = get_logger("alerts.dispatch")


class MultiChannel(AlertChannel):
    """Fan an alert out to several channels (e.g. WhatsApp + SMS) so the farmer gets it on
    every configured channel. Reports the channels that actually delivered live."""

    def __init__(self, channels: list[AlertChannel]) -> None:
        self.channels = channels

    @property
    def mode(self) -> str:  # type: ignore[override]
        return "live" if any(getattr(c, "mode", "mock") == "live" for c in self.channels) else "mock"

    def send(self, to: str | None, alert: Alert) -> DeliveryResult:
        results = [c.send(to, alert) for c in self.channels]
        live = [r for r in results if r.ok and r.mode == "live"]
        if live:
            providers = "+".join(sorted({r.provider for r in live}))
            detail = "; ".join(f"{r.provider}={r.detail}" for r in live)
            return DeliveryResult(True, "live", providers, detail)
        return DeliveryResult(True, "mock", "console", "no live channel — logged to console")


def build_channel(settings) -> AlertChannel:
    """WhatsApp (Twilio) and/or SMS (Africa's Talking) — both fire when both are configured."""
    channels: list[AlertChannel] = []
    if settings.alert_mode() == "live":
        from alerts.twilio_channel import TwilioChannel
        channels.append(TwilioChannel(settings))
    if settings.at_mode() == "live":
        from alerts.africas_talking_channel import AfricasTalkingChannel
        channels.append(AfricasTalkingChannel(settings))
    if not channels:
        log.info("%s alert channel: console (no Twilio / Africa's Talking creds)", tag("mock"))
        return ConsoleChannel()
    names = " + ".join(type(c).__name__.replace("Channel", "") for c in channels)
    log.info("%s alert channel(s): %s", tag("live"), names)
    return channels[0] if len(channels) == 1 else MultiChannel(channels)


def alert_from_rule(gh_id: str, result, ts: str, lead_time_hr: float = 24.0,
                    lang: str = "en") -> Alert:
    """Build the Alert with a SIMPLE, action-first farmer message (what to do), keeping the
    technical rule reason on the node for the record/explainability."""
    from comms import i18n
    message = i18n.farmer_alert(result.kind, result.level, lang, gh_id=gh_id)
    return Alert(gh_id=gh_id, kind=result.kind, level=result.level,
                 message=message, reason=result.reason, ts=ts,
                 lead_time_hr=lead_time_hr, channel="whatsapp")


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
