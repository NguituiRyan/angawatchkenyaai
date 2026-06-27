"""AgroInput Price Agent — a SECOND agent the Crop-Health Advisory Agent hires over
Masumi (agent-to-agent). Given a recommended treatment, it returns a product, a Kenyan
agro-dealer, a price and availability — work the advisory agent pays another agent for,
rather than doing itself. Its quote carries its own reproducible result_hash.

Synthetic agro-dealer catalogue (no real personal/business data).
"""
from __future__ import annotations

import hashlib
import json

# treatment id -> a representative Kenya-available product (PCPB-registered names)
CATALOG = {
    "metalaxyl_mancozeb": ("Agrilax 72 WP", "Nakuru Agrovet Ltd", "250 g", 1.10),
    "mancozeb": ("Dithane M-45", "Rift Agro Supplies", "500 g", 1.12),
    "chlorothalonil": ("Bravo 720 SC", "Nakuru Agrovet Ltd", "250 ml", 1.15),
    "copper": ("Kocide 3000", "Greenlife Crop Protection", "250 g", 1.10),
    "dimethomorph": ("Zampro 525 SC", "Rift Agro Supplies", "100 ml", 1.18),
    "azoxystrobin": ("Quadris 250 SC", "Nakuru Agrovet Ltd", "100 ml", 1.20),
    "bt": ("Bt kurstaki (DiPel)", "Real IPM Kenya", "250 g", 1.10),
    "spinosad": ("Tracer 480 SC", "Greenlife Crop Protection", "30 ml", 1.15),
    "abamectin": ("Acramite / Abamectin 1.8 EC", "Rift Agro Supplies", "100 ml", 1.15),
    "pymetrozine": ("Chess 50 WG", "Nakuru Agrovet Ltd", "100 g", 1.18),
    "neem": ("Nimbecidine (neem oil)", "Real IPM Kenya", "1 L", 1.05),
}

PROFILE = {
    "name": "Angawatch AgroInput Price Agent",
    "description": "Returns Kenya agro-dealer product, price and availability for a recommended "
                   "crop treatment. Hired agent-to-agent by the Crop-Health Advisory Agent.",
}


def quote(treatment: dict) -> dict:
    """Price/availability for a single recommended treatment (the one a farmer would buy)."""
    tid = treatment.get("id", "")
    name = treatment.get("name", tid)
    base = treatment.get("cost_kes", 0) or 0
    product, supplier, pack, markup = CATALOG.get(
        tid, (name, "Local agrovet", "unit", 1.15))
    price = int(round(base * markup)) if base else 0
    out = {
        "treatment_id": tid,
        "treatment": name,
        "product": product,
        "supplier": supplier,
        "pack_size": pack,
        "price_kes": price,
        "availability": "in stock" if base else "no purchase needed (cultural control)",
        "lead_time_days": 1 if treatment.get("type") == "cultural" else 2,
    }
    payload = json.dumps({k: out[k] for k in ("treatment_id", "product", "supplier", "price_kes")},
                         sort_keys=True, separators=(",", ":"))
    out["result_hash"] = hashlib.sha256(payload.encode()).hexdigest()
    return out


class AgroInputPriceAgent:
    role = "AgroInput Price Agent"

    def quote_for_report(self, report) -> dict | None:
        """Quote the top PURCHASABLE treatment in an advisory report (skip free cultural ones)."""
        actions = report.recommended_actions if hasattr(report, "recommended_actions") else []
        target = next((t for t in actions if (t.get("cost_kes") or 0) > 0),
                      actions[0] if actions else None)
        return quote(target) if target else None
