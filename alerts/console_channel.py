"""Console alert channel — the always-available labeled-mock fallback."""
from __future__ import annotations

from alerts.channel import Alert, AlertChannel, DeliveryResult
from logging_setup import get_logger

log = get_logger("alerts.console")


class ConsoleChannel(AlertChannel):
    mode = "mock"

    def send(self, to: str | None, alert: Alert) -> DeliveryResult:
        dest = to or "farmer"
        log.warning("[MOCK ALERT -> %s] %s", dest, alert.short())
        return DeliveryResult(ok=True, mode="mock", provider="console",
                              detail=f"printed to screen (no Twilio creds) -> {dest}")
