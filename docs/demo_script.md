# Angawatch — Demo Scripts

Two runnable demos. Both work **fully offline** (`--all-mock` / no creds) and degrade
gracefully; every step is labeled **LIVE** or **MOCK**.

Pre-flight (≈30s, once):
```bash
pip install -r requirements.txt          # full local: pip install -r requirements-full.txt
cp .env.example .env                      # optional: add NEO4J/OPENROUTER/TWILIO keys
python scripts/seed_db.py                 # confirms the graph (LIVE Aura or MOCK memory)
```
If presenting with real services: pre-warm Aura, join the Twilio WhatsApp sandbox
(send the join code), and set `MASUMI_PRERECORDED_TX` to a real preprod tx for the audit link.

---

## A. AgriFin hero demo (≈3 min) — "an alert that saves the crop"

Goal: a real warning fires **before** a staged blight event, and the record is in Neo4j.

**Option 1 — narrated CLI**
```bash
python scripts/run_demo.py --all-mock      # or no flag = prefer-live with creds
```
Talk track, following the banners:
1. **Live/Mock matrix** — "everything here is honestly labeled."
2. **Farm record** — "a verified Neo4j history: readings → alerts → actions → harvests."
3. **Live sensor feed (calm)** — normal humid nights, risk LOW.
4. **Staged blight event** — `inject_event('late_blight')`; humidity climbs into the band.
5. **Risk → alert → graph** — at ~3h sustained a **MED early warning** fires; at ~6h a
   **HIGH** alert goes out (WhatsApp if live, else console) — *hours before visible damage* —
   and a new **Alert node** is written, `TRIGGERED_BY` the exact readings.

**Option 2 — dashboard** (`streamlit run dashboard/app.py`): tab **Farm record & live feed** →
press **Inject blight event** → the alert banner appears and the feed/graph update.

Punchline: *"The same event, caught early, is the difference between a 31% loss season and a 4%
loss season — which is exactly what the farm's record shows."*

---

## B. Masumi "Business Agent" demo (≈5–7 min) — "a co-op hires, pays, and audits a crop-health agent"

Goal: show Masumi playing a **real** role in identity, discovery, payment, and audit — over a
**verifiable, graph-grounded** diagnosis + treatment plan recorded on-chain. The agent is hired
not by the farmer but by the farmer's **buyer**: a horticulture cooperative / off-taker that
needs every greenhouse it contracts to stay healthy through to harvest.

Run the dashboard: `streamlit run dashboard/app.py` (deployed link works too). Follow the five
tabs; the sidebar **Demo flow** tracker lights up as you go.

### ① Problem & user (≈1 min) — tab *Farm record & live feed*
"Our user is **Rift Valley Fresh Co-op** — a buyer that contracts hundreds of smallholder tomato
greenhouses. It has only a handful of field officers, and they visit on a **rota**. Late blight
can wipe a greenhouse in days — it spreads *before* the next scheduled visit. By the time an
officer arrives, the crop the co-op pre-paid for is gone."
Show the **Verified farm record** graph (readings → alerts `TRIGGERED_BY` → actions → harvests)
and the **Advisory snapshot** card — "every contracted greenhouse is already a trusted,
tamper-evident record."

### ② Current manual workflow & business pain (≈1 min) — same tab
"Today this is **manual and reactive**: officers drive a fixed route, diagnose by eye, and guess
at sprays — often after damage, sometimes ignoring the **pre-harvest interval (PHI)** so a batch
gets rejected at intake for residue. The co-op eats crop loss, reject rates, and wasted officer-
miles. They'd happily **pay per farm** for a triage that tells them *which* greenhouse to visit
*today* and *what* to recommend — but no human can watch hundreds of microclimates at once."

### ③ The agent demo (≈2–3 min)
1. **Inject blight → early alert** — tab *Farm record & live feed*, **Live sensor feed** panel:
   press **Inject blight event**. Humidity climbs into the blight band; a **HIGH** alert fires
   (WhatsApp/SMS if live, else console) and a new **Alert node** is written to Neo4j — *hours
   before visible damage*.
2. **Crop doctor — the traversal** — tab *Crop doctor (GraphRAG)*, press
   **Explain my latest alert**. Walk the **path chain** it renders:
   **Alert → Disease → Pathogen → Treatment** — multi-hop reasoning, not a flat lookup. Point at
   the **graph evidence** chips (the microclimate conditions from the linked sensor readings), the
   **ranked treatment cards** (efficacy → PHI → cost, cultural/cheap first, with beneficial-safety
   warnings), and the **knowledge-graph subgraph** viz. Open **"Shows thinking — the Cypher
   traversal the agent ran"** — *"this is the agent's reasoning, the exact multi-hop join a graph
   does natively and a flat table can't."* (Optional: **Diagnose current conditions**.)
3. **Co-op triage → verified report** — tab *Co-op triage & hire* (the **buyer's** view):
   the **portfolio table** ranks every contracted greenhouse by **officer-visit priority**,
   highest risk first — "3 officers can now cover 400 farms by exception, not by rota." Pick the
   at-risk farm; the agent produces a verified **AdvisoryReport**: diagnosis, pathogen, risk,
   priority (**"Visit now — within 24h"**), confidence + its driver, and the ranked, PHI-aware
   plan. Note the **human-in-the-loop limits** panel: *"the agent recommends; a co-op agronomist
   approves before any spray."*

### ④ The Masumi role (≈1 min) — same tab, *Hire & pay the agent via Masumi*
Press **Pay & deliver via Masumi** and walk the 5-step stepper — each step shows a 🟢 LIVE / 🟠 MOCK badge:
- **① Identity / registration** — the agent has a **DID** on Masumi; it's a discoverable,
  hireable service (MIP-003 `/start_job`, `/status`).
- **② Co-op discovers & hires the agent** — the buyer finds it and opens a job.
- **③ Escrow payment** — **pay-per-report** escrow in **USDM/ADA on Cardano preprod**.
- **④ Deliver advisory + Decision-Log hash** — the agent returns the diagnosis + plan; its
  **`result_hash` commits to the diagnosis + plan** (not a score) and is Decision-Logged on-chain
  (metadata **label 8434**, type **`advisory-decision-log`**).
- **⑤ On-chain audit trail** — verify it. In hybrid mode (`MASUMI_PRERECORDED_TX` set) the audit
  shows a **real cardanoscan preprod link** (`prerecorded-real`) — open
  `preprod.cardanoscan.io` and say: *"here is the actual on-chain proof that this exact advice was
  delivered and paid for — anyone can recompute the hash and verify the agent earned its fee."*

### ⑤ Business value & next steps (≈1 min)
"Masumi turns the agent into something a co-op can **actually buy**: a metered, auditable service
with its own identity and an on-chain receipt for every recommendation. **Value:** fewer rejected
batches (PHI-aware), targeted officer visits instead of a blind rota, and a tamper-evident record
the co-op — and its own insurers/lenders — can trust. **Next:** more crops and pathogens in the
knowledge graph, a Sokosumi listing so any buyer can hire it, and feeding accepted recommendations
back to sharpen ranking."

> **Optional depth (if time)** — tab *Leaf scan & advisor*: classify a tomato leaf photo
> (PlantVillage classifier) and ask the GraphRAG advisor a question answered from the farm's own
> record. Tab *Feature phone & offline*: the same advisory over **bilingual EN/SW two-way SMS**
> (keywords **STATUS/HALI, ADVICE/USHAURI, ALERTS, HELP**) and an **offline alert box**
> (OLED + LED + buzzer) for no-signal greenhouses.

### Everything is labeled, and it runs offline
Every capability carries a **LIVE/MOCK** badge — nothing here hides a mock; that's the point.
The whole demo runs with **no internet and no keys**:
```bash
python scripts/run_demo.py --all-mock
```
This drives the full story end-to-end: **SEED → SIM → INJECT → RISK/ALERT/RECORD →
CO-OP HIRES THE ADVISORY AGENT → GRAPHRAG DIAGNOSIS + PLAN → MASUMI HIRE/PAY/DELIVER/AUDIT**,
every stage banner-labeled. CLI equivalent of just the Masumi loop:
```bash
python -m masumi_integration.demo        # co-op discovers → pays per report → deliver → audit
MASUMI_PRERECORDED_TX=<txhash> python -m masumi_integration.demo   # shows the real audit link
```

Rubric hits: **Problem Clarity** (a buyer with hundreds of farms and too few officers),
**Business Value** (a co-op would pay per report for early, PHI-aware triage), **Agent Design**
(graph-grounded, multi-hop diagnosis, ranked plan, human-in-the-loop), **Masumi Fit**
(identity/discovery/escrow/audit are real, labeled), **Demo** (no hard-fail), **Presentation**
(honest mocks), and the **Sokosumi** bonus (see `docs/` + `python -m masumi_integration.sokosumi`).

---

## Resilience cheatsheet (if something breaks on stage)
| Symptom | What happens automatically |
|---|---|
| No internet / Aura down | in-memory store, labeled `MOCK` |
| OpenRouter rate-limited | deterministic narration, diagnosis + plan unchanged |
| Twilio not joined | console alert with the identical message |
| Masumi preprod slow | mock round-trip + pre-recorded real tx link |
| HF model missing | labeled mock classifier |

`python scripts/run_demo.py --all-mock` is the bulletproof fallback for any venue.
