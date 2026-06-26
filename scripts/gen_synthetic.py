"""Generate Angawatch's synthetic seed dataset (no real personal data).

Deterministic (seeded) so the demo is reproducible. Encodes a believable
smallholder arc for the hero farmer:
  Season 1: a blight alert is IGNORED  -> visible harvest loss
  Season 2: alert ACTED ON quickly     -> recovered yield
  Season 3: alert ACTED ON             -> best yield
This arc is exactly what the explainable credit score rewards.

Run:  python -m scripts.gen_synthetic        (writes data/synthetic_history.json)
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

RNG = random.Random(42)
OUT = Path(__file__).resolve().parents[1] / "data" / "synthetic_history.json"

# Three completed seasons in 2025 (today in-app is 2026-06-26).
SEASON_STARTS = ["2025-01-10", "2025-05-01", "2025-09-01"]
DAYS_PER_SEASON = 30          # representative slice
SLOTS = [(6, "morning"), (14, "midday"), (22, "night")]   # 3 readings/day


def _r(a: float, b: float, nd: int = 1) -> float:
    return round(RNG.uniform(a, b), nd)


def _reading(rid, gh, sid, ts, slot, blight=False):
    if blight and slot in ("night", "morning"):
        temp, hum, lw = _r(20, 23), _r(93, 97), _r(9, 12)
    elif slot == "morning":
        temp, hum, lw = _r(16, 19), _r(86, 95), _r(6, 9)
    elif slot == "midday":
        temp, hum, lw = _r(26, 31), _r(50, 66), _r(0, 1)
    else:  # night
        temp, hum, lw = _r(18, 21), _r(89, 97), _r(8, 11)
    return {
        "id": rid, "greenhouse_id": gh, "season_id": sid, "ts": ts,
        "temp_c": temp, "humidity": hum, "leaf_wetness_hr": lw,
        "soil_vwc": _r(0.30, 0.42, 2), "trap_count": 0, "source": "sim",
    }


def _season_readings(gh, sid, start_iso, season_idx):
    """Return (readings, blight_reading_ids). Blight stretch on days 12-14."""
    start = datetime.fromisoformat(start_iso)
    readings, blight_ids = [], []
    week_trap_base = [1, 2, 4, 3][season_idx % 4]
    for day in range(DAYS_PER_SEASON):
        in_blight = 12 <= day <= 14
        for hour, slot in SLOTS:
            ts = (start + timedelta(days=day, hours=hour)).isoformat()
            rid = f"{sid}-r{day:02d}{hour:02d}"
            rd = _reading(rid, gh, sid, ts, slot, blight=in_blight)
            # seasonal pheromone-trap pressure (males/trap this week)
            rd["trap_count"] = max(0, week_trap_base + (day // 7) + RNG.randint(-1, 1))
            readings.append(rd)
            if in_blight and slot in ("night", "morning"):
                blight_ids.append(rid)
    return readings, blight_ids


def build_synthetic() -> dict:
    farmers = [
        {"id": "Farmer-A", "name": "Farmer-A (Wanjiru)", "phone": "+254700000001",
         "county": "Nakuru", "joined_date": "2024-11-01", "gender": "F"},
        {"id": "Farmer-B", "name": "Farmer-B (Otieno)", "phone": "+254700000002",
         "county": "Kiambu", "joined_date": "2025-08-01", "gender": "M"},
        {"id": "Farmer-C", "name": "Farmer-C (Mutua)", "phone": "+254700000003",
         "county": "Kajiado", "joined_date": "2025-02-01", "gender": "M"},
    ]
    cooperatives = [{"id": "coop-1", "name": "Naivasha Greenhouse Co-op",
                     "members": 240, "region": "Rift Valley"}]
    lenders = [{"id": "lender-1", "name": "Unaitas SACCO", "type": "SACCO"},
               {"id": "insurer-1", "name": "ACRE Africa", "type": "insurer"}]
    greenhouses = [
        {"id": "gh-001", "farmer_id": "Farmer-A", "crop": "tomato", "area_m2": 240,
         "structure_type": "metal", "has_netting": True, "irrigation": "drip",
         "lat": -0.303, "lon": 36.080, "climate_resilience": 0.80},
        {"id": "gh-002", "farmer_id": "Farmer-B", "crop": "tomato", "area_m2": 180,
         "structure_type": "wooden", "has_netting": False, "irrigation": "manual",
         "lat": -1.171, "lon": 36.830, "climate_resilience": 0.45},
        {"id": "gh-003", "farmer_id": "Farmer-C", "crop": "tomato", "area_m2": 200,
         "structure_type": "wooden", "has_netting": True, "irrigation": "drip",
         "lat": -1.852, "lon": 36.776, "climate_resilience": 0.62},
    ]
    memberships = [{"farmer_id": "Farmer-A", "cooperative_id": "coop-1"},
                   {"farmer_id": "Farmer-C", "cooperative_id": "coop-1"}]
    partnerships = [{"cooperative_id": "coop-1", "lender_id": "lender-1"}]

    seasons, readings, alerts, actions, harvests = [], [], [], [], []

    # --- Hero farmer: gh-001, 3 seasons with the narrative arc ---
    # (yield_kg, expected_kg, loss_pct, grade_a, actioned, lead_time_hr)
    arc = [
        (620, 900, 31.1, 58, False, 30),   # S1 ignored -> big loss
        (815, 900, 9.4, 74, True, 28),     # S2 acted -> recovered
        (885, 920, 3.8, 82, True, 26),     # S3 acted -> best
    ]
    for idx, start in enumerate(SEASON_STARTS, start=1):
        sid = f"gh-001-s{idx}"
        end = (datetime.fromisoformat(start) + timedelta(days=120)).date().isoformat()
        seasons.append({"id": sid, "greenhouse_id": "gh-001", "index": idx,
                        "start_date": start, "end_date": end, "crop_cycle": "long"})
        rs, blight_ids = _season_readings("gh-001", sid, start, idx)
        readings.extend(rs)
        yld, exp, loss, grade, actioned, lead = arc[idx - 1]
        alert_ts = (datetime.fromisoformat(start) + timedelta(days=13, hours=6)).isoformat()
        aid = f"gh-001-s{idx}-blight"
        alerts.append({
            "id": aid, "greenhouse_id": "gh-001", "season_id": sid, "ts": alert_ts,
            "kind": "late_blight", "level": "HIGH",
            "message": "Late-blight risk HIGH: RH>=90% and 16-26C sustained overnight. "
                       "Ventilate at dawn and apply protectant fungicide.",
            "channel": "whatsapp", "delivery": "live", "lead_time_hr": lead,
            "triggered_by": blight_ids[:3],
        })
        if actioned:
            actions.append({
                "id": f"{aid}-act", "alert_id": aid,
                "ts": (datetime.fromisoformat(alert_ts) + timedelta(hours=4)).isoformat(),
                "type": "sprayed", "responded_within_hr": 4,
                "note": "Applied copper-based protectant; increased ventilation.",
            })
        harvests.append({
            "id": f"gh-001-s{idx}-h", "greenhouse_id": "gh-001", "season_id": sid,
            "ts": end, "yield_kg": yld, "expected_kg": exp, "loss_pct": loss,
            "grade_a_pct": grade,
        })

    # --- Comparison farmers (thin history) ---
    _thin_farmer("gh-002", seasons, readings, alerts, actions, harvests,
                 start="2025-08-15", idx=1, yld=430, exp=820, loss=47.5, grade=41,
                 actioned=False, lead=18)
    for j, (start, yld, exp, loss, grade, actioned) in enumerate(
            [("2025-02-10", 690, 880, 21.6, 63, True),
             ("2025-07-10", 705, 880, 19.9, 66, False)], start=1):
        _thin_farmer("gh-003", seasons, readings, alerts, actions, harvests,
                     start=start, idx=j, yld=yld, exp=exp, loss=loss, grade=grade,
                     actioned=actioned, lead=22)

    return {
        "farmers": farmers, "cooperatives": cooperatives, "lenders": lenders,
        "greenhouses": greenhouses, "seasons": seasons, "readings": readings,
        "alerts": alerts, "actions": actions, "harvests": harvests,
        "memberships": memberships, "partnerships": partnerships,
    }


def _thin_farmer(gh, seasons, readings, alerts, actions, harvests, *,
                 start, idx, yld, exp, loss, grade, actioned, lead):
    sid = f"{gh}-s{idx}"
    end = (datetime.fromisoformat(start) + timedelta(days=120)).date().isoformat()
    seasons.append({"id": sid, "greenhouse_id": gh, "index": idx,
                    "start_date": start, "end_date": end, "crop_cycle": "long"})
    rs, blight_ids = _season_readings(gh, sid, start, idx)
    readings.extend(rs)
    alert_ts = (datetime.fromisoformat(start) + timedelta(days=13, hours=6)).isoformat()
    aid = f"{sid}-blight"
    alerts.append({"id": aid, "greenhouse_id": gh, "season_id": sid, "ts": alert_ts,
                   "kind": "late_blight", "level": "HIGH",
                   "message": "Late-blight risk HIGH overnight.", "channel": "whatsapp",
                   "delivery": "live", "lead_time_hr": lead, "triggered_by": blight_ids[:3]})
    if actioned:
        actions.append({"id": f"{aid}-act", "alert_id": aid,
                        "ts": (datetime.fromisoformat(alert_ts) + timedelta(hours=6)).isoformat(),
                        "type": "sprayed", "responded_within_hr": 6, "note": "Protectant applied."})
    harvests.append({"id": f"{sid}-h", "greenhouse_id": gh, "season_id": sid, "ts": end,
                     "yield_kg": yld, "expected_kg": exp, "loss_pct": loss, "grade_a_pct": grade})


def main() -> None:
    data = build_synthetic()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    counts = {k: len(v) for k, v in data.items()}
    print(f"Wrote {OUT}")
    print("Synthetic dataset:", counts)


if __name__ == "__main__":
    main()
