"""Agronomic KNOWLEDGE GRAPH for greenhouse tomato — the domain ontology that makes
the graph *matter*. The agronomist agent traverses it multi-hop:

  (Reading)-[:INDICATES]->(Condition)-[:FAVORS]->(Disease)
  -[:CONTROLLED_BY]->(Treatment)-[:USES]->(active ingredient)
  (Disease)-[:CAUSED_BY]->(Pathogen)   (Pest)-[:VECTORS]->(Disease)
  (Treatment)-[:HARMFUL_TO]->(Beneficial)   (Stage)-[:SUSCEPTIBLE_TO]->(Disease)

Sourced from UC IPM, Infonet-Biovision, Koppert, Kenya PCPB/extension (see
docs/agronomy_sources.md). Numbers are first-pass and should be agronomist-reviewed.
"""
from __future__ import annotations

# --- nodes (label -> list of property dicts) --------------------------------
NODES: dict[str, list[dict]] = {
    "Crop": [{"id": "tomato", "name": "Tomato"}],
    "Condition": [
        {"id": "cool_humid_night", "name": "Cool humid night",
         "rule": "RH>=90% and 10-26C", "desc": "Sustained cool, wet leaf conditions"},
        {"id": "warm_humid", "name": "Warm + humid",
         "rule": "RH>=90% and 20-32C", "desc": "Warm humid spell with leaf wetness"},
        {"id": "prolonged_wetness", "name": "Prolonged leaf wetness",
         "rule": "leaf_wetness>=10h", "desc": "Long free-moisture window on foliage"},
        {"id": "high_humidity", "name": "High humidity (>85%)",
         "rule": "RH>=85%", "desc": "Sustained high relative humidity"},
        {"id": "hot_dry", "name": "Hot & dry",
         "rule": "RH<55% and temp>28C", "desc": "Hot dry spell (mite-favourable)"},
        {"id": "warm_season", "name": "Warm season (25-30C)",
         "rule": "25-30C", "desc": "Warm period favouring whitefly/virus"},
    ],
    "Pathogen": [
        {"id": "p_infestans", "name": "Phytophthora infestans", "kind": "oomycete"},
        {"id": "a_solani", "name": "Alternaria solani", "kind": "fungus"},
        {"id": "p_fulva", "name": "Passalora fulva", "kind": "fungus"},
        {"id": "s_lycopersici", "name": "Septoria lycopersici", "kind": "fungus"},
        {"id": "begomovirus", "name": "Begomovirus (TYLCV)", "kind": "virus"},
        {"id": "ralstonia", "name": "Ralstonia solanacearum", "kind": "bacterium"},
    ],
    "Disease": [
        {"id": "late_blight", "name": "Late blight", "severity": "high"},
        {"id": "early_blight", "name": "Early blight", "severity": "high"},
        {"id": "leaf_mould", "name": "Leaf mould", "severity": "medium"},
        {"id": "septoria", "name": "Septoria leaf spot", "severity": "medium"},
        {"id": "tylcv", "name": "Tomato Yellow Leaf Curl Virus", "severity": "high"},
        {"id": "bacterial_wilt", "name": "Bacterial wilt", "severity": "high"},
    ],
    "Symptom": [
        {"id": "water_soaked", "name": "Water-soaked leaf lesions"},
        {"id": "target_spots", "name": "Bullseye/target spots"},
        {"id": "mould_patches", "name": "Grey mould under leaves"},
        {"id": "leaf_curl", "name": "Yellow leaf curling + stunting"},
        {"id": "wilting", "name": "Sudden wilting, vascular browning"},
    ],
    "Pest": [
        {"id": "tuta", "name": "Tuta absoluta (leafminer)"},
        {"id": "whitefly", "name": "Whitefly (Bemisia tabaci)"},
        {"id": "red_spider_mite", "name": "Red spider mite"},
    ],
    "Treatment": [
        # fungicides (PHI = pre-harvest interval days)
        {"id": "metalaxyl_mancozeb", "name": "Metalaxyl + Mancozeb", "type": "chemical",
         "active": "metalaxyl+mancozeb", "phi_days": 3, "efficacy": "high", "cost_kes": 4000},
        {"id": "mancozeb", "name": "Mancozeb", "type": "chemical",
         "active": "mancozeb", "phi_days": 5, "efficacy": "medium-high", "cost_kes": 3000},
        {"id": "chlorothalonil", "name": "Chlorothalonil", "type": "chemical",
         "active": "chlorothalonil", "phi_days": 0, "efficacy": "medium", "cost_kes": 2200},
        {"id": "copper", "name": "Copper hydroxide", "type": "chemical",
         "active": "copper", "phi_days": 0, "efficacy": "medium", "cost_kes": 2800},
        {"id": "dimethomorph", "name": "Dimethomorph", "type": "chemical",
         "active": "dimethomorph", "phi_days": 3, "efficacy": "high", "cost_kes": 6500},
        {"id": "azoxystrobin", "name": "Azoxystrobin", "type": "chemical",
         "active": "azoxystrobin", "phi_days": 0, "efficacy": "medium-high", "cost_kes": 5500},
        # insecticides / bio
        {"id": "bt", "name": "Bacillus thuringiensis", "type": "biological",
         "active": "Bt kurstaki", "phi_days": 0, "efficacy": "high", "cost_kes": 3500},
        {"id": "spinosad", "name": "Spinosad", "type": "biological",
         "active": "spinosad", "phi_days": 3, "efficacy": "high", "cost_kes": 4500},
        {"id": "abamectin", "name": "Abamectin", "type": "chemical",
         "active": "abamectin", "phi_days": 7, "efficacy": "high", "cost_kes": 5000},
        {"id": "pymetrozine", "name": "Pymetrozine", "type": "chemical",
         "active": "pymetrozine", "phi_days": 3, "efficacy": "medium-high", "cost_kes": 6000},
        {"id": "neem", "name": "Neem oil", "type": "biological",
         "active": "azadirachtin", "phi_days": 0, "efficacy": "medium", "cost_kes": 2000},
        # cultural
        {"id": "ventilation", "name": "Ventilate (dawn) / HAF fans", "type": "cultural",
         "active": "-", "phi_days": 0, "efficacy": "high", "cost_kes": 0},
        {"id": "drip_irrigation", "name": "Drip irrigation (keep foliage dry)", "type": "cultural",
         "active": "-", "phi_days": 0, "efficacy": "high", "cost_kes": 0},
        {"id": "sanitation", "name": "Remove infected leaves/plants", "type": "cultural",
         "active": "-", "phi_days": 0, "efficacy": "high", "cost_kes": 0},
        {"id": "staking_pruning", "name": "Stake + prune lower leaves", "type": "cultural",
         "active": "-", "phi_days": 0, "efficacy": "medium", "cost_kes": 1000},
        {"id": "reflective_mulch", "name": "Reflective mulch", "type": "cultural",
         "active": "-", "phi_days": 0, "efficacy": "medium", "cost_kes": 3000},
        {"id": "resistant_variety", "name": "Resistant variety (Anna F1 / Prostar)", "type": "cultural",
         "active": "-", "phi_days": 0, "efficacy": "high", "cost_kes": 5000},
        # biocontrol agents
        {"id": "encarsia", "name": "Encarsia formosa (parasitoid)", "type": "biocontrol",
         "active": "-", "phi_days": 0, "efficacy": "high", "cost_kes": 9000},
        {"id": "nesidiocoris", "name": "Nesidiocoris tenuis (predator)", "type": "biocontrol",
         "active": "-", "phi_days": 0, "efficacy": "high", "cost_kes": 11000},
    ],
    "Beneficial": [
        {"id": "honeybee", "name": "Honey bee (pollinator)"},
        {"id": "encarsia_b", "name": "Encarsia formosa"},
        {"id": "nesidiocoris_b", "name": "Nesidiocoris tenuis"},
    ],
    "GrowthStage": [
        {"id": "seedling", "name": "Seedling", "order": 1},
        {"id": "vegetative", "name": "Vegetative", "order": 2},
        {"id": "flowering", "name": "Flowering", "order": 3},
        {"id": "fruiting", "name": "Fruiting", "order": 4},
        {"id": "harvest", "name": "Ripening/Harvest", "order": 5},
    ],
}

# --- edges: (from_label, from_id, REL, to_label, to_id, props) ---------------
EDGES: list[tuple] = [
    # disease -> pathogen / symptom / favouring condition / crop
    ("Disease", "late_blight", "CAUSED_BY", "Pathogen", "p_infestans", {}),
    ("Disease", "late_blight", "FAVORS_REVERSE", "Condition", "cool_humid_night", {}),
    ("Disease", "late_blight", "FAVORS_REVERSE", "Condition", "prolonged_wetness", {}),
    ("Disease", "late_blight", "SHOWS", "Symptom", "water_soaked", {}),
    ("Disease", "early_blight", "CAUSED_BY", "Pathogen", "a_solani", {}),
    ("Disease", "early_blight", "FAVORS_REVERSE", "Condition", "warm_humid", {}),
    ("Disease", "early_blight", "SHOWS", "Symptom", "target_spots", {}),
    ("Disease", "leaf_mould", "CAUSED_BY", "Pathogen", "p_fulva", {}),
    ("Disease", "leaf_mould", "FAVORS_REVERSE", "Condition", "high_humidity", {}),
    ("Disease", "leaf_mould", "SHOWS", "Symptom", "mould_patches", {}),
    ("Disease", "septoria", "CAUSED_BY", "Pathogen", "s_lycopersici", {}),
    ("Disease", "septoria", "FAVORS_REVERSE", "Condition", "prolonged_wetness", {}),
    ("Disease", "tylcv", "CAUSED_BY", "Pathogen", "begomovirus", {}),
    ("Disease", "tylcv", "FAVORS_REVERSE", "Condition", "warm_season", {}),
    ("Disease", "tylcv", "SHOWS", "Symptom", "leaf_curl", {}),
    ("Disease", "bacterial_wilt", "CAUSED_BY", "Pathogen", "ralstonia", {}),
    ("Disease", "bacterial_wilt", "SHOWS", "Symptom", "wilting", {}),
    # pest -> vectors disease / damages crop
    ("Pest", "whitefly", "VECTORS", "Disease", "tylcv", {}),
    ("Pest", "tuta", "DAMAGES", "Crop", "tomato", {}),
    ("Pest", "whitefly", "DAMAGES", "Crop", "tomato", {}),
    ("Pest", "red_spider_mite", "DAMAGES", "Crop", "tomato", {}),
    ("Pest", "red_spider_mite", "FAVORS_REVERSE", "Condition", "hot_dry", {}),
    # all diseases affect tomato
    *[("Disease", d, "AFFECTS", "Crop", "tomato", {})
      for d in ("late_blight", "early_blight", "leaf_mould", "septoria", "tylcv", "bacterial_wilt")],
    # treatment -> CONTROLS disease/pest (efficacy)
    ("Treatment", "metalaxyl_mancozeb", "CONTROLS", "Disease", "late_blight", {"efficacy": "high"}),
    ("Treatment", "metalaxyl_mancozeb", "CONTROLS", "Disease", "early_blight", {"efficacy": "high"}),
    ("Treatment", "dimethomorph", "CONTROLS", "Disease", "late_blight", {"efficacy": "high"}),
    ("Treatment", "mancozeb", "CONTROLS", "Disease", "late_blight", {"efficacy": "medium-high"}),
    ("Treatment", "mancozeb", "CONTROLS", "Disease", "early_blight", {"efficacy": "medium-high"}),
    ("Treatment", "mancozeb", "CONTROLS", "Disease", "leaf_mould", {"efficacy": "medium"}),
    ("Treatment", "chlorothalonil", "CONTROLS", "Disease", "late_blight", {"efficacy": "medium"}),
    ("Treatment", "chlorothalonil", "CONTROLS", "Disease", "early_blight", {"efficacy": "medium"}),
    ("Treatment", "chlorothalonil", "CONTROLS", "Disease", "septoria", {"efficacy": "medium"}),
    ("Treatment", "copper", "CONTROLS", "Disease", "late_blight", {"efficacy": "medium"}),
    ("Treatment", "copper", "CONTROLS", "Disease", "early_blight", {"efficacy": "medium"}),
    ("Treatment", "copper", "CONTROLS", "Disease", "leaf_mould", {"efficacy": "medium"}),
    ("Treatment", "azoxystrobin", "CONTROLS", "Disease", "early_blight", {"efficacy": "medium-high"}),
    ("Treatment", "azoxystrobin", "CONTROLS", "Disease", "septoria", {"efficacy": "medium-high"}),
    ("Treatment", "bt", "CONTROLS", "Pest", "tuta", {"efficacy": "high"}),
    ("Treatment", "spinosad", "CONTROLS", "Pest", "tuta", {"efficacy": "high"}),
    ("Treatment", "spinosad", "CONTROLS", "Pest", "red_spider_mite", {"efficacy": "medium"}),
    ("Treatment", "abamectin", "CONTROLS", "Pest", "red_spider_mite", {"efficacy": "high"}),
    ("Treatment", "abamectin", "CONTROLS", "Pest", "tuta", {"efficacy": "high"}),
    ("Treatment", "pymetrozine", "CONTROLS", "Pest", "whitefly", {"efficacy": "medium-high"}),
    ("Treatment", "neem", "CONTROLS", "Pest", "whitefly", {"efficacy": "medium"}),
    ("Treatment", "neem", "CONTROLS", "Pest", "tuta", {"efficacy": "medium"}),
    ("Treatment", "encarsia", "CONTROLS", "Pest", "whitefly", {"efficacy": "high"}),
    ("Treatment", "nesidiocoris", "CONTROLS", "Pest", "whitefly", {"efficacy": "high"}),
    ("Treatment", "nesidiocoris", "CONTROLS", "Pest", "tuta", {"efficacy": "medium"}),
    # cultural controls (prevention)
    *[("Treatment", "ventilation", "CONTROLS", "Disease", d, {"efficacy": "high"})
      for d in ("late_blight", "early_blight", "leaf_mould")],
    *[("Treatment", "drip_irrigation", "CONTROLS", "Disease", d, {"efficacy": "high"})
      for d in ("late_blight", "leaf_mould", "septoria")],
    *[("Treatment", "sanitation", "CONTROLS", "Disease", d, {"efficacy": "high"})
      for d in ("late_blight", "early_blight", "septoria", "tylcv")],
    ("Treatment", "reflective_mulch", "CONTROLS", "Pest", "whitefly", {"efficacy": "medium"}),
    *[("Treatment", "resistant_variety", "CONTROLS", "Disease", d, {"efficacy": "high"})
      for d in ("early_blight", "tylcv", "bacterial_wilt")],
    # treatment HARMFUL_TO beneficials (so the agent can warn)
    ("Treatment", "abamectin", "HARMFUL_TO", "Beneficial", "honeybee", {}),
    ("Treatment", "pymetrozine", "HARMFUL_TO", "Beneficial", "encarsia_b", {}),
    ("Treatment", "abamectin", "HARMFUL_TO", "Beneficial", "nesidiocoris_b", {}),
    # growth stage susceptibility
    ("GrowthStage", "fruiting", "SUSCEPTIBLE_TO", "Disease", "late_blight", {}),
    ("GrowthStage", "fruiting", "SUSCEPTIBLE_TO", "Disease", "early_blight", {}),
    ("GrowthStage", "flowering", "SUSCEPTIBLE_TO", "Disease", "tylcv", {}),
]

# --- operational data -> ontology links -------------------------------------
ALERT_TO_TARGET = {           # alert.kind -> (label, id)
    "late_blight": ("Disease", "late_blight"),
    "early_blight": ("Disease", "early_blight"),
    "tuta": ("Pest", "tuta"),
}
ACTION_TO_TREATMENT = {       # action.type -> treatment id
    "sprayed": "mancozeb",
    "ventilated": "ventilation",
    "removed_leaves": "sanitation",
}
EFFICACY_RANK = {"high": 3, "medium-high": 2, "medium": 1, "low": 0}


def conditions_for_reading(r: dict) -> list[str]:
    """Which Conditions a sensor reading INDICATES (Reading -> Condition edge)."""
    rh = r.get("humidity", 0) or 0
    t = r.get("temp_c", 0) or 0
    lw = r.get("leaf_wetness_hr", 0) or 0
    out = []
    if rh >= 90 and 10 <= t <= 26:
        out.append("cool_humid_night")
    if rh >= 90 and 20 <= t <= 32:
        out.append("warm_humid")
    if rh >= 85:
        out.append("high_humidity")
    if lw >= 10:
        out.append("prolonged_wetness")
    if rh < 55 and t > 28:
        out.append("hot_dry")
    if 25 <= t <= 30:
        out.append("warm_season")
    return out
