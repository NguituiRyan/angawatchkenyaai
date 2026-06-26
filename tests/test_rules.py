"""Unit tests for the pure agronomic risk rules."""
from datetime import datetime, timedelta

from risk.rules import late_blight, tuta_degree_day


def _win(n, temp, hum, lw, trap=1):
    t0 = datetime(2026, 6, 26, 20, 0, 0)
    return [{"id": f"w{i}", "ts": (t0 + timedelta(hours=i)).isoformat(),
             "temp_c": temp, "humidity": hum, "leaf_wetness_hr": lw, "trap_count": trap}
            for i in range(n)]


def test_late_blight_fires_high_on_sustained_favourable():
    r = late_blight(_win(8, temp=18, hum=95, lw=10))
    assert r.fired and r.level == "HIGH"
    assert r.metrics["sustained_hr"] >= 6
    assert r.contributing_reading_ids


def test_late_blight_moderate_between_3_and_6h():
    r = late_blight(_win(4, temp=18, hum=95, lw=10))
    assert r.fired and r.level == "MED"


def test_late_blight_not_high_when_dry():
    r = late_blight(_win(8, temp=18, hum=70, lw=1))
    assert r.level != "HIGH"


def test_late_blight_not_high_when_too_hot():
    r = late_blight(_win(8, temp=30, hum=95, lw=10))
    assert r.level != "HIGH"   # 30C is outside the 10-26C band


def test_tuta_high_on_heavy_trap_catch():
    r = tuta_degree_day(_win(6, temp=24, hum=70, lw=2, trap=7))
    assert r.fired and r.level == "HIGH"


def test_tuta_quiet_on_low_pressure():
    r = tuta_degree_day(_win(6, temp=20, hum=60, lw=1, trap=0))
    assert not r.fired
