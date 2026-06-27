# Angawatch knowledge graph — why the graph matters

Angawatch is two graphs in one Neo4j database, joined where they meet:

1. **The farm record** (operational): `Farmer → Greenhouse → Season → Reading / Alert
   (TRIGGERED_BY readings, RESPONDED_WITH actions) → Harvest`, plus `Cooperative`,
   `Lender`, `AuditRecord`. This is the verified history a SACCO prices risk against.
2. **The agronomic ontology** (domain knowledge): `Crop, Condition, Pathogen, Disease,
   Symptom, Pest, Treatment, Beneficial, GrowthStage` connected by typed relationships.

The agent doesn't read a row — it **traverses** the join between them.

## Ontology schema

```
(Disease)-[:CAUSED_BY]->(Pathogen)
(Disease)-[:FAVORS_REVERSE]->(Condition)        # microclimate that favours the disease
(Disease)-[:SHOWS]->(Symptom)
(Disease)-[:AFFECTS]->(Crop)
(Pest)-[:VECTORS]->(Disease)                    # whitefly -> TYLCV
(Pest)-[:DAMAGES]->(Crop)
(Treatment)-[:CONTROLS {efficacy}]->(Disease|Pest)
(Treatment)-[:HARMFUL_TO]->(Beneficial)         # abamectin -> honey bee
(GrowthStage)-[:SUSCEPTIBLE_TO]->(Disease)
```

`Treatment` nodes carry the attributes the agent reasons over: `type` (cultural /
chemical / biological / biocontrol), `active` (active ingredient), `phi_days`
(pre-harvest interval), `efficacy`, `cost_kes`.

## The operational data is LINKED into the ontology

This is the part that makes it one graph, not two:

```
(Reading)-[:INDICATES]->(Condition)             # sensor RH/temp/wetness -> microclimate
(Alert)-[:FOR_DISEASE]->(Disease)               # the alert is about a disease
(Alert)-[:FOR_PEST]->(Pest)
(Action)-[:APPLIED]->(Treatment)                # what the farmer actually did
```

So a real sensor reading is two hops from a disease and three from a ranked treatment.

## Showcase traversal — "Why was I warned, and what do I do?"

The Crop-doctor tab runs this on the live graph:

```cypher
MATCH (a:Alert {id:$id})-[:FOR_DISEASE]->(d:Disease)-[:CAUSED_BY]->(p:Pathogen)
OPTIONAL MATCH (a)-[:TRIGGERED_BY]->(r:Reading)-[:INDICATES]->(c:Condition)
MATCH (t:Treatment)-[ctl:CONTROLS]->(d)
OPTIONAL MATCH (t)-[:HARMFUL_TO]->(b:Beneficial)
RETURN d, p, collect(DISTINCT c.name) AS conditions,
       collect(DISTINCT {t:t, efficacy:ctl.efficacy, harms:b.name}) AS treatments
ORDER BY ctl.efficacy DESC, t.phi_days ASC, t.cost_kes ASC
```

One query joins the alert, its triggering sensor readings, the microclimate they
indicate, the disease, its pathogen, and every treatment that controls it — ranked by
efficacy → pre-harvest interval → cost, with a beneficial-safety check. A flat table
can't express that; a graph does it natively. The agent shows this query and the path
it walked (the "shows thinking" artifact).

## Other graph-native questions the model answers

- **Diagnose from current conditions:** latest `Reading`s → `INDICATES` → `Condition` →
  `FAVORS` → likely `Disease`, each disease citing the conditions that implicated it.
- **Treatment appropriateness (credit signal):** did the farmer's `Action -[:APPLIED]->
  Treatment` actually `CONTROLS` the `Disease` their `Alert` was `FOR_DISEASE`, within the
  pre-harvest interval before `Harvest`? That's a relational question feeding the score.
- **Vector risk:** `Pest -[:VECTORS]-> Disease` lets the agent warn that a whitefly trap
  count is a TYLCV risk, not just a pest count.

## Fallback

All traversals run as **Cypher on Neo4j** (the live demo) and have a **Python fallback**
over the same ontology for the in-memory store, so the app works offline. Both paths are
covered by `tests/test_agronomy_kg.py`.

## Sources

Disease/condition/treatment data is first-pass and agronomist-review-flagged, compiled
from: UC IPM (tomato late/early blight), Infonet-Biovision, UMN/NC State/Rutgers
extension, Koppert (biocontrol), and Kenya-specific PCPB / extension material on
registered products and pre-harvest intervals. See `graph/agronomy.py` header.
