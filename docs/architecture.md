# Angawatch — Architecture

Angawatch has two intertwined loops on one **Neo4j** record:

1. **Guardian loop (AgriFin):** sensors/simulator → risk engine → farmer alert → graph.
2. **Advisory loop (Masumi bounty):** a co-op/off-taker hires the Crop-Health Advisory Agent →
   it triages contracted greenhouses, diagnoses the disease by traversing the agronomic
   knowledge graph, returns a PHI-aware treatment plan → pays per report → the diagnosis +
   plan hash is logged on-chain → audit.

The decision-bearing logic (risk rules + knowledge-graph traversals) is **deterministic
Python/Cypher**; the LLM only narrates the graph's facts. Every external dependency has a
**clearly-labeled mock** fallback.

> The earlier credit-score direction (a 7-factor score a lender hired/paid/audited) was
> **dropped** and moved to `archived/`: the farm data we can't yet trust, the lender already
> gets a better signal for free, and an on-chain audit of an *opinion* does no real work.
> Diagnosing disease from a traversable graph commits real, verifiable work to the chain.

## System overview

```mermaid
flowchart TD
    subgraph Field["🌫️ Greenhouse"]
        SIM["sim/ SensorSimulator<br/>(or ESP32 → POST /ingest)"]
    end
    SIM -->|reading| ING["services.ingest()"]
    ING --> RISK["risk/ engine + PURE rules<br/>late-blight · early-blight · Tuta DD"]
    RISK -->|rule fired| ALERT["alerts/ AlertChannel<br/>Twilio WhatsApp/SMS · console"]
    ALERT -->|WhatsApp| FARMER["👩🏾‍🌾 Farmer"]
    ING --> GRAPH[("graph/ Neo4j Aura<br/>(or in-memory mirror)<br/>+ agronomy ontology KG")]
    RISK --> GRAPH
    ALERT --> GRAPH

    subgraph Buyer["🛒 Co-op / Off-taker (Rift Valley Fresh Co-op)"]
        DASH["dashboard/ Streamlit"]
    end
    DASH -->|Request advisory| AGENT["agents/ Crop-Health Advisory Agent<br/>(CrewAI, triage + diagnose)"]
    AGENT -->|multi-hop traversal| KG["graph/kg.py + agronomy.py<br/>Reading→INDICATES→Condition→FAVORS→<br/>Disease→CAUSED_BY→Pathogen;<br/>Disease←CONTROLS←Treatment"]
    KG --> GRAPH
    KG --> AGENT
    AGENT --> RULES["risk/ PURE rules + KG facts<br/>diagnosis · priority · result_hash"]
    RULES --> AGENT
    AGENT -->|narrate graph facts| LLM["agents/ agronomist (GraphRAG)<br/>OpenRouter (free) or template"]
    DASH -->|Pay per report & deliver| MASUMI["masumi_integration/<br/>MasumiClient"]
    MASUMI --> CHAIN["Cardano Preprod<br/>escrow + advisory Decision-Log hash"]
    MASUMI --> GRAPH
    AGENT --> VISION["vision/ leaf classifier"]
```

## Where Masumi enters (identity · discovery · payment · audit)

```mermaid
sequenceDiagram
    participant L as Co-op / Off-taker
    participant M as Masumi Payment/Registry
    participant A as Angawatch Crop-Health Advisory Agent (MIP-003)
    participant C as Cardano Preprod

    Note over A,M: ① IDENTITY — agent registered on Registry (DID + NFT)
    L->>M: ② DISCOVERY — find agent by capability
    L->>A: ③ SERVICE REQUEST — POST /start_job {greenhouse_id}
    L->>M: ④ ESCROW PAYMENT (pay-per-report) — create_payment_request (USDM/ADA)
    M->>C: lock funds in escrow UTXO
    A->>A: traverse KG → diagnosis + PHI-aware plan (+ result_hash)
    A->>M: ⑤ DELIVER advisory — complete_payment(result_hash)  (Decision Logging)
    M->>C: write diagnosis + plan hash on-chain · release escrow
    L->>C: ⑥ AUDIT — verify tx on preprod.cardanoscan.io
```

Masumi plays a **real role** at all four points, not as a logo:
- **Identity:** `masumi_integration/` registers the agent (DID); MIP-003 endpoints in
  `masumi_integration/service.py` make it genuinely discoverable. The co-op **discovers**
  the agent and issues a service request with `{greenhouse_id}`.
- **Discovery + service request:** `/availability`, `/input_schema`, `/start_job`, `/status`,
  `/provide_input`, `/demo`. `client.run_round_trip(report)` drives the cycle; a Sokosumi
  coworker lives in `masumi_integration/sokosumi.py`.
- **Escrow payment (pay-per-report):** `RealMasumiBackend` uses the `masumi` SDK
  (`create_payment_request`, `check_payment_status`, `complete_payment`) on Cardano
  **Preprod** (USDM/ADA).
- **Audit:** the deterministic `result_hash` commits to the **diagnosis + plan** (canonical
  JSON, sha256). `masumi_integration/onchain.py` writes tx metadata (label **8434**, type
  `"advisory-decision-log"`: agent, subject, diagnosis, priority, result_hash); verifiable on
  `preprod.cardanoscan.io`. Logging a verifiable diagnosis is real work, not an opinion.

**Hybrid mode (default for the live demo):** the labeled `MockMasumiBackend` walks the same
five stages deterministically; if `MASUMI_PRERECORDED_TX` is set, the audit step shows a
**real** preprod transaction link (`proof_kind=prerecorded-real`) so judges see genuine
on-chain evidence while the live click-through never stalls on a fresh confirmation.

## Modules
| Dir | Responsibility |
|---|---|
| `config.py` | settings + `*_mode()` live/mock resolvers |
| `graph/` | Neo4j store + in-memory mirror; `agronomy.py` ontology data; `kg.py` seed + Cypher traversals + Python fallback (GraphRAG contract) |
| `sim/` | sensor simulator + injectable event + ESP32 `/ingest` |
| `risk/` | PURE agronomic rules + engine (with KG traversals, the verifiable core) |
| `alerts/` | AlertChannel (Twilio WhatsApp/SMS, console) |
| `agents/` | `advisory.py` (AdvisoryAgent + AdvisoryReport) · `agronomist.py` (GraphRAG explain) · narration |
| `vision/` | PlantVillage tomato classifier (inference) |
| `masumi_integration/` | identity/registration, MIP-003 `service.py`, `client.py`, escrow, `onchain.py` audit, `sokosumi.py` (real + labeled mock) |
| `dashboard/` | Streamlit co-op app |
| `scripts/` | `seed_db.py`, `run_demo.py` |

## Live/mock matrix
| Capability | Live when | Mock fallback (labeled) |
|---|---|---|
| Graph | `NEO4J_*` set & reachable | in-memory store |
| Narration | `OPENROUTER_API_KEY` | deterministic template |
| Alerts | `TWILIO_*` | console message |
| Vision | local HF model | deterministic stub |
| Masumi | `MASUMI_MODE=real` + funded wallet | simulated round-trip (+ optional real tx link) |

Only the **simulator + deterministic cores** are required — pure local Python, no network.
```
