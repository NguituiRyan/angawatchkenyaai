"""Standalone simulator demo:  python -m sim.demo

Streams a few calm readings, injects a blight event, and shows the regime change.
"""
from __future__ import annotations

from sim.generator import SensorSimulator


def _row(r) -> str:
    return (f"  {r.ts[11:16]}  T={r.temp_c:>4}C  RH={r.humidity:>4}%  "
            f"wet={r.leaf_wetness_hr:>4}h  soil={r.soil_vwc}  trap={r.trap_count}")


def main() -> None:
    sim = SensorSimulator(greenhouse_id="gh-001")
    print("\nCalm baseline:")
    for r in sim.stream(6):
        print(_row(r))

    print("\n>>> inject_event('late_blight')  — humidity climbs into the infection band\n")
    sim.inject_event("late_blight", ticks=8)
    for r in sim.stream(8):
        flag = "  <== blight regime" if r.humidity >= 92 else ""
        print(_row(r) + flag)
    print()


if __name__ == "__main__":
    main()
