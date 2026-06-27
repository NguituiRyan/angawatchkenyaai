"""Alert + AlertChannel interface."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


def split_recipients(to: str | None) -> list[str]:
    """Split a comma/space-separated phone list into clean E.164 numbers, so FARMER_PHONE
    can target several handsets at once (e.g. '+254733333147, +254753534484')."""
    if not to:
        return []
    parts = re.split(r"[,\s]+", to.replace("whatsapp:", "").strip())
    return [p for p in parts if p]


@dataclass
class Alert:
    gh_id: str
    kind: str
    level: str
    message: str                   # farmer-facing, action-first (what to do)
    ts: str
    lead_time_hr: float = 24.0
    channel: str = "whatsapp"
    delivery: str = "pending"      # live | mock | pending
    reason: str = ""               # technical rule justification (kept on the node)
    id: str | None = None

    def to_props(self) -> dict:
        d = {
            "greenhouse_id": self.gh_id, "ts": self.ts, "kind": self.kind,
            "level": self.level, "message": self.message, "channel": self.channel,
            "delivery": self.delivery, "lead_time_hr": self.lead_time_hr,
            "reason": self.reason,
        }
        if self.id:
            d["id"] = self.id
        return d

    def short(self) -> str:
        return f"[{self.level}] {self.kind}: {self.message}"


@dataclass
class DeliveryResult:
    ok: bool
    mode: str           # live | mock
    provider: str       # whatsapp | sms | console
    detail: str


class AlertChannel(ABC):
    mode: str = "mock"

    @abstractmethod
    def send(self, to: str | None, alert: Alert) -> DeliveryResult:  # noqa: D401
        ...
