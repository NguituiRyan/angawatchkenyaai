"""Standalone risk-rule checks:  python -m risk.demo

Pure, no store/LLM. Verifies a sustained blight window fires HIGH, a calm
simulated night does NOT, and a high pheromone-trap count fires Tuta.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from risk.rules import early_blight, late_blight, tuta_degree_day
from sim.generator import SensorSimulator


def _window(n, temp, hum, lw, trap=1, start="2026-06-26T20:00:00"):
    t0 = datetime.fromisoformat(start)
    return [{"id": f"w{i}", "ts": (t0 + timedelta(hours=i)).isoformat(),
             "temp_c": temp, "humidity": hum, "leaf_wetness_hr": lw, "trap_count": trap}
            for i in range(n)]


def main() -> None:
    print("\n== Risk rule checks ==\n")

    blight = _window(8, temp=22, hum=94, lw=10)
    r = late_blight(blight)
    print(f"sustained blight window  -> {r.level:<4} fired={r.fired}  ({r.metrics.get('sustained_hr')}h)")
    assert r.fired and r.level == "HIGH", "expected HIGH late blight"

    sim = SensorSimulator(seed=3)
    night = [rd.to_props() | {"id": f"n{i}"} for i, rd in enumerate(sim.stream(10))]
    r2 = late_blight(night)
    print(f"calm simulated 10h       -> {r2.level:<4} fired={r2.fired}  "
          f"({r2.metrics.get('sustained_hr', 0)}h)  [should NOT be HIGH]")
    assert r2.level != "HIGH", "calm baseline should not fire HIGH late blight"

    pest = _window(6, temp=24, hum=70, lw=2, trap=7)
    r3 = tuta_degree_day(pest)
    print(f"trap=7 males/week        -> {r3.level:<4} fired={r3.fired}  "
          f"(dd={r3.metrics.get('accumulated_dd')})")
    assert r3.fired and r3.level == "HIGH", "expected HIGH Tuta"

    eb = _window(6, temp=24, hum=92, lw=7)
    r4 = early_blight(eb)
    print(f"warm wet window          -> {r4.level:<4} fired={r4.fired}")

    print("\nAll rule checks passed ✅\n")


if __name__ == "__main__":
    main()
