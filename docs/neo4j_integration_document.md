# Neo4j Integration Document — Kenya AI Challenge (Neo4j Track)

> Copy this into a Google Doc or export a PDF (1 page, 2 max), then paste its public link
> into the Oxbridge form. Fill **Team Name**. Do not include passwords/keys/credentials.

**Project Name:** Angawatch

**Team Name:** [your team name]

**Selected Challenge Brief:** Team-defined AgriFin problem — early crop-disease detection
and advisory to protect smallholder income and cooperative supply.

---

## 1. How We Used Neo4j
Neo4j Aura is the reasoning core of our solution. It stores two graphs joined into one: **(a)
the operational farm record** — `Farmer, Greenhouse, Season, Reading` (sensor), `Alert,
Action, Harvest, Cooperative` — and **(b) a hand-built agronomic knowledge graph** — `Crop,
Condition` (microclimate), `Pathogen, Disease, Symptom, Pest, Treatment, Beneficial,
GrowthStage`. Live sensor readings are linked into the ontology
(`Reading-[:INDICATES]->Condition`, `Alert-[:FOR_DISEASE]->Disease`,
`Action-[:APPLIED]->Treatment`). Our Crop-Health Advisory Agent answers *"why was I warned
and what do I do?"* by **traversing this graph multi-hop** — sensor reading → microclimate
condition → disease → pathogen, and disease ← controlled-by ← treatment — to diagnose the
problem and return a treatment plan ranked by efficacy, pre-harvest interval and cost. This is
**GraphRAG**: Neo4j retrieves the grounded facts; an LLM only narrates them.

## 2. Why Neo4j Matters
Crop-health is inherently relational. A disease is **favoured by** specific microclimate
conditions, **caused by** a pathogen, **shows** symptoms, and is **controlled by** treatments
with different efficacy, cost and pre-harvest intervals; pests **vector** diseases; and some
treatments are **harmful to** pollinators. Answering *"given these sensor readings, what is
wrong and what is the safest, cheapest, in-time treatment?"* is a multi-hop join across all of
that — something a flat table or plain vector search cannot express, but a graph does natively
in one Cypher query. The graph also makes the agent **explainable** (we show the traversed
path and the Cypher), **grounds the LLM** so it cannot invent a treatment, and lets a
cooperative **triage hundreds of farms** by querying which greenhouses' readings indicate
which diseases — turning rota visits into visit-by-exception.

## 3. Graph Model

**Main Nodes**

| Node type | What it represents |
|---|---|
| Greenhouse | A smallholder tomato greenhouse (the farm unit) |
| Reading | A timestamped sensor reading (temp, humidity, leaf-wetness, soil, pest-trap) |
| Alert | An early disease/pest warning fired by the risk engine |
| Disease | A tomato disease (e.g. Late blight) |
| Pathogen | The causal agent (e.g. Phytophthora infestans) |
| Condition | A microclimate band the readings indicate (e.g. Cool humid night) |
| Treatment | A control (chemical/cultural/biological) with active ingredient, PHI, efficacy, cost |

*(Also: Farmer, Season, Harvest, Cooperative, Pest, Symptom, Beneficial, GrowthStage, Action.)*

**Main Relationships**

| Relationship | What it means |
|---|---|
| `(Greenhouse)-[:RECORDED]->(Reading)` | the farm logged a sensor reading |
| `(Reading)-[:INDICATES]->(Condition)` | the reading puts the crop in a microclimate band |
| `(Disease)-[:FAVORS_REVERSE]->(Condition)` | that condition favours the disease |
| `(Alert)-[:FOR_DISEASE]->(Disease)` | the alert is about a disease |
| `(Disease)-[:CAUSED_BY]->(Pathogen)` | the disease's causal pathogen |
| `(Treatment)-[:CONTROLS]->(Disease)` | the treatment controls the disease (with efficacy) |
| `(Treatment)-[:HARMFUL_TO]->(Beneficial)` | the treatment harms a pollinator/beneficial |
| `(Pest)-[:VECTORS]->(Disease)` | the pest transmits the disease |

**Optional properties:** `Treatment.phi_days`, `Treatment.efficacy`, `Treatment.cost_kes`,
`Reading.humidity`, `Disease.severity`, `Alert.level`, `Greenhouse.county`.

## 4. Architecture / Integration
**Architecture flow:** Streamlit dashboard / FastAPI service → Python advisory agent →
**Neo4j Aura (Cypher GraphRAG traversal)** → ranked diagnosis + treatment plan shown to the
cooperative and the farmer (WhatsApp/SMS).

**Integration status:** **Fully working.**

**Short explanation:** The deployed app connects to a live Neo4j Aura instance over the
official Neo4j driver; every diagnosis runs real Cypher traversals against ~793 nodes /
~2,218 relationships. A labelled in-memory mirror gives an offline fallback for the demo, but
the deployed app uses live Aura.

## 5. Current Status
**Working:** live Aura connection; the full agronomic knowledge graph + farm record seeded;
multi-hop GraphRAG diagnosis (alert → disease → pathogen → ranked treatments), sensor →
condition → disease diagnosis, pest-vector and beneficial-safety queries; the dashboard
renders the traversed subgraph and the exact Cypher.

**Incomplete or simulated:** the sensor hardware feed is simulated for the demo (a sensor
simulator generates readings ingested through the same pipeline); the agronomic ontology is
hand-curated and first-pass (agronomist review pending).

**Next improvement:** ingest a larger, expert-validated agronomic ontology and connect real
IoT sensor streams; add growth-stage-gated treatment validity.
