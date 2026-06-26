"""Standalone alert demo:  python -m alerts.demo

Builds the channel from env (Twilio if creds present, else console) and sends a
sample late-blight alert. Shows the LIVE/MOCK delivery result.
"""
from __future__ import annotations

from alerts.channel import Alert
from alerts.dispatcher import build_channel
from config import get_settings
from logging_setup import tag


def main() -> None:
    settings = get_settings()
    channel = build_channel(settings)
    alert = Alert(
        gh_id="gh-001", kind="late_blight", level="HIGH",
        message="RH>=90% and 16-26C sustained ~7h. Ventilate at dawn and apply protectant.",
        ts="2026-06-26T05:00:00", lead_time_hr=30,
    )
    result = channel.send(settings.FARMER_PHONE, alert)
    print(f"\nChannel mode : {tag(channel.mode)} {channel.mode}")
    print(f"Delivery     : ok={result.ok} via={result.provider} mode={result.mode}")
    print(f"Detail       : {result.detail}\n")


if __name__ == "__main__":
    main()
