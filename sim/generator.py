"""SensorSimulator — believable time-series with an injectable blight/Tuta event.

Ticks hourly so the risk engine accumulates 'sustained hours' naturally. Leaves a
clean ingest path (sim.ingest_api) so a real ESP32 feed can replace this later.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from sim.models import Reading

DEMO_START = datetime(2026, 6, 26, 5, 0, 0)   # fixed -> reproducible demo


class SensorSimulator:
    def __init__(self, greenhouse_id: str = "gh-001", start: datetime | None = None,
                 step_hours: int = 1, seed: int = 7) -> None:
        self.gh_id = greenhouse_id
        self.clock = start or DEMO_START
        self.step = step_hours
        self.rng = random.Random(seed)
        self.regime: str | None = None      # None | late_blight | tuta
        self._event_ticks = 0
        self._trap = 1                       # current pheromone-trap weekly count

    # --- event injection ---------------------------------------------------
    def inject_event(self, kind: str = "late_blight", ticks: int = 12) -> None:
        """Stage a blight or Tuta event for the next `ticks` hours."""
        kind = kind.lower()
        if kind in ("late_blight", "blight", "early_blight"):
            self.regime = "late_blight"
        elif kind in ("tuta", "pest"):
            self.regime = "tuta"
        else:
            self.regime = kind
        self._event_ticks = ticks

    def clear_event(self) -> None:
        self.regime = None
        self._event_ticks = 0

    # --- sampling ----------------------------------------------------------
    def _r(self, a: float, b: float, nd: int = 1) -> float:
        return round(self.rng.uniform(a, b), nd)

    def _baseline(self, hour: int) -> tuple[float, float, float]:
        """(temp_c, humidity, leaf_wetness_hr) for a calm day, by hour-of-day.

        Night RH hovers just under the 90% blight threshold so calm nights produce
        only short, broken favourable runs (no sustained 6h) — an INJECTED event
        sits solidly at 92-97% and is what drives a clean HIGH.
        """
        if 5 <= hour < 10:        # morning: cool, damp
            return self._r(16, 19), self._r(80, 90), self._r(4, 7)
        if 10 <= hour < 17:       # midday: warm, dry
            return self._r(26, 31), self._r(48, 64), self._r(0, 1)
        if 17 <= hour < 21:       # evening: cooling
            return self._r(20, 24), self._r(66, 82), self._r(2, 4)
        return self._r(16, 20), self._r(83, 91), self._r(6, 9)    # night: humid

    def tick(self) -> Reading:
        self.clock += timedelta(hours=self.step)
        hour = self.clock.hour
        temp, hum, lw = self._baseline(hour)
        trap = max(0, self._trap + self.rng.randint(-1, 1))

        if self.regime == "late_blight" and self._event_ticks > 0:
            # Late blight = COOL + wet: RH>=90, ~16-19C (below early-blight's 20-32C
            # band, so this fires late blight cleanly), with sustained leaf wetness.
            temp = self._r(16, 19)
            hum = self._r(92, 97)
            lw = self._r(9, 12)
        elif self.regime == "tuta" and self._event_ticks > 0:
            self._trap = min(12, self._trap + 2)
            trap = self._trap

        if self._event_ticks > 0:
            self._event_ticks -= 1
            if self._event_ticks == 0:
                self.regime = None

        return Reading(
            greenhouse_id=self.gh_id, ts=self.clock.isoformat(),
            temp_c=temp, humidity=hum, leaf_wetness_hr=lw,
            soil_vwc=self._r(0.30, 0.42, 2), trap_count=trap, source="sim",
        )

    def stream(self, n: int) -> list[Reading]:
        return [self.tick() for _ in range(n)]
