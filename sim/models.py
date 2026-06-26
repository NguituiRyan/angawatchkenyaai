"""Sensor reading model + realistic Kenyan-highland greenhouse ranges."""
from __future__ import annotations

from dataclasses import dataclass

# Realistic ranges (see docs/architecture.md citations): air temp day 22-32 /
# night 14-20C; RH day 50-85 / night 85-99%; high night leaf wetness; soil VWC
# 0.30-0.44; pheromone-trap 1-8 males/week.


@dataclass
class Reading:
    greenhouse_id: str
    ts: str                       # ISO 8601
    temp_c: float
    humidity: float
    leaf_wetness_hr: float
    soil_vwc: float
    trap_count: int
    source: str = "sim"           # sim | esp32 | mock
    id: str | None = None
    season_id: str | None = None

    def to_props(self) -> dict:
        d = {
            "greenhouse_id": self.greenhouse_id, "ts": self.ts,
            "temp_c": self.temp_c, "humidity": self.humidity,
            "leaf_wetness_hr": self.leaf_wetness_hr, "soil_vwc": self.soil_vwc,
            "trap_count": self.trap_count, "source": self.source,
        }
        if self.id:
            d["id"] = self.id
        if self.season_id:
            d["season_id"] = self.season_id
        return d
