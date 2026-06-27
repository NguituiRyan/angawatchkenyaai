# Angawatch — Masumi Track submission (Kenya AI Challenge)

> Paste each numbered section into the Oxbridge form. Fill the two `[ ]` placeholders
> (your deployed Streamlit URL and demo video URL) before submitting.
> Repo: https://github.com/NguituiRyan/angawatchkenyaai · App: `[your Streamlit Cloud URL]` · Video: `[your 5–7 min video URL]`

---

## 1. Problem Statement

A horticulture **cooperative / off-taker** that aggregates tomato from **hundreds of
contracted smallholder greenhouses** runs only a **handful of field officers**. Late
blight and Tuta absoluta outbreaks spread in **24–48 hours**, but officers visit on a
**fixed fortnightly rota** and diagnose **by eye** — so they reach an infected farm
**days to weeks late**, after **20–40% of that crop** is already lost. That means supply
shortfalls, missed **grade-A** volume, and broken delivery contracts for the co-op.

**Angawatch's Crop-Health Advisory Agent** monitors every greenhouse's sensor feed,
**triages which farms are at risk today**, **diagnoses the disease by traversing an
agronomic knowledge graph**, and prepares a **ranked, pre-harvest-interval (PHI)-aware
treatment plan** plus an **officer-visit priority list** — so a few officers cover
hundreds of farms **by exception, not by rota**, and the co-op gets an auditable record
of the advice acted on. A co-op agronomist approves before any spray.

**Success metric:** outbreaks reached within 24–48 h instead of 1–3 weeks; % of at-risk
farms an officer visits before crop loss; grade-A volume protected per season.

---

## 2. Current Manual Workflow and Measurable Pain

**Today, without the agent:**
1. Field officers drive a **fixed fortnightly rota**, mostly visiting healthy farms.
2. Farmers **phone in** only once they already see damage — usually too late.
3. Diagnosis is **by eye**; advice is generic; the right product, rate and pre-harvest
   interval are guesswork.

**Measurable pain (modeled on synthetic data for a ~400-greenhouse co-op with 3 officers):**
- A farm is visited **~once every 3–4 weeks**; an outbreak that starts mid-cycle festers
  for **1–3 weeks** before an officer arrives.
- Affected houses lose **~20–40% of yield**; if even **~25% of houses** are hit per season
  at ~30% loss, that is **tens of tonnes of grade-A tomato lost**.
- At **~KES 80–120/kg** farmgate, protecting even half of that by catching outbreaks
  1–2 weeks earlier is a **six-figure-KES seasonal saving** for the co-op.
- Wrong product / ignored PHI also causes **residue rejections** at the buyer's grading.
- **3 officers cannot meaningfully cover 400 farms** on a rota — the work doesn't scale.

---

## 3. Target User and Buyer

| Role | Who | Why they care |
|---|---|---|
| **Buyer (pays / sponsors)** | The horticulture **cooperative / off-taker** (synthetic example: "Rift Valley Fresh Co-op") | Contracted supply volume + grade-A %; a lost crop is a delivery shortfall and a broken buyer contract. Has the budget and the workflow today. |
| **Operator (uses it)** | The co-op's **field officer / agronomist** | Decides which farms to visit and signs off the treatment advice. |
| **Beneficiary** | The **smallholder farmer** | Gets a specific, timely diagnosis (over WhatsApp/SMS) instead of a generic message. |

The co-op pays **per advisory report** via Masumi. Unlike a lender, it has a *direct*
financial stake in crop survival and is not waiting on data it could get for free.

---

## 4. Agent Description

**Role:** a graph-grounded **Crop-Health Advisory Agent** the co-op hires per report.

- **Inputs:** a greenhouse id + its sensor feed (temperature, relative humidity,
  leaf-wetness, soil moisture, pest-trap counts) + the hiring co-op's identity.
- **Outputs:** per-farm **diagnosis** (disease + pathogen) · **risk level** ·
  **officer-visit priority** ("Visit now — within 24h") · a **ranked treatment plan**
  (ordered by efficacy → pre-harvest interval → cost, with beneficial/bee-safety
  warnings) · a co-op-wide **triage list** across all farms · a reproducible
  **`result_hash`** · a plain-language **WhatsApp/SMS alert** for the farmer.
- **Tools / data sources:**
  - A **Neo4j agronomic knowledge graph** (GraphRAG): `Crop · Condition · Pathogen ·
    Disease · Symptom · Pest · Treatment · Beneficial · GrowthStage`, with sensor data
    linked in (`Reading-[:INDICATES]->Condition`, `Alert-[:FOR_DISEASE]->Disease`,
    `Action-[:APPLIED]->Treatment`). Treatments carry active ingredient, PHI, efficacy
    and cost, sourced from UC IPM / Koppert / Kenya PCPB.
  - A **deterministic risk engine** (late-blight Hutton, early-blight, Tuta degree-day
    rules) — the verifiable core.
  - An **LLM (OpenRouter)** that **only narrates** the graph's facts.
  - **Twilio** WhatsApp/SMS for farmer alerts; a HF **leaf-image classifier**.
- **Decision logic (it does real WORK, not chat):** it **monitors → triages → diagnoses →
  prepares**. The agent *chooses* which graph tools to run in a thought→action→observation
  loop (it can even compose its own read-only Cypher), and exposes that **decision trace**.
  The multi-hop path: `Reading → Condition → Disease → Pathogen` and
  `Disease ← Treatment`, ranked. It also ties the **live sensor reading → microclimate
  constraint → treatment window** ("Hutton risk active: RH≥90% with 10–26°C → spray window
  open now").
- **Handoffs:** agent → **field officer** (visit priority) → **co-op agronomist approves**
  → **farmer acts** (WhatsApp/SMS; reply ADVICE for the full plan).
- **Limits (what it cannot do):** it **recommends; a human approves** before any spray.
  Diagnosis is from sensor microclimate + the graph, **not a lab test** — confirm visually.
  Follow label rate, **PHI** and bee-safety windows. Efficacy/cost are regional estimates.
  **Synthetic / anonymized data only.** No financial/medical/legal final decisions.

---

## 5. Prototype or Demo

- **Deployed, runnable app:** `[your Streamlit Cloud URL]` (Streamlit Community Cloud).
- **5–7 min video walkthrough:** `[your video URL]` — follows the recommended flow
  (problem → manual pain → agent demo → Masumi role → value).
- **What the demo shows, with LIVE / MOCK labels on every capability:**
  - Inject a staged blight event → an **early WhatsApp/SMS alert** fires to the farmer's
    real phone (Twilio **LIVE**) with simple, action-first advice.
  - **Crop doctor (GraphRAG):** "Explain my latest alert" shows the multi-hop traversal
    path + the **actual Cypher** the agent ran; "Ask the agent" shows the **decision
    trace** (tools it chose).
  - **Co-op triage:** the buyer's portfolio of greenhouses ranked by visit priority → a
    verified advisory report → **"Pay & deliver via Masumi"** (round-trip + on-chain audit).
  - Honest mode badges throughout; runs fully offline via `python scripts/run_demo.py --all-mock`.
- **Live vs mock vs planned (stated up front):**
  - **LIVE:** Neo4j Aura graph · OpenRouter narration · Twilio WhatsApp alert · a **real
    Cardano preprod on-chain Decision-Log tx** · HF vision.
  - **MOCK by default (real code present):** the Masumi escrow round-trip runs the labeled
    mock backend; `RealMasumiBackend` (Masumi SDK) is wired and runnable with a funded
    wallet + Payment Service.
  - **LIVE:** Sokosumi marketplace **discovery** (real `GET /v1/agents`, 20 coworkers).
  - **PLANNED:** listing *our* agent on Sokosumi (needs DID + listing form); full
    Payment-Service escrow per run.

---

## 6. Business Value

**Field-validated (pilot):** before the co-op feature, we placed one hardware node in a real
smallholder greenhouse. The farmer (Baba Neema, Nakuru) got a blight alert **~2 days before
visible symptoms**, ventilated + sprayed in time, and **saved a crop he'd have lost ~50% of**
the prior season — and asked for a node on his second tunnel. The co-op model scales exactly
this farmer benefit across hundreds of greenhouses. (See `docs/testimonials.md`.)

- **Reallocates scarce officers from rota to exception:** triage ranks ~400 farms so the
  ~5–15 at HIGH risk **today** get visited first, instead of once every 3–4 weeks.
- **Earlier intervention → less crop lost:** outbreaks reached in **24–48 h** instead of
  1–3 weeks → a large share of the **20–40% per-house loss** is avoided → on the synthetic
  400-farm model, a **six-figure-KES seasonal saving** vs a per-report fee of a few KES.
- **More contracted grade-A volume delivered** (fewer houses lost; correct, PHI-compliant
  treatment → fewer residue rejections at grading).
- **Right product, right interval → fewer wasted/wrong sprays** and PHI violations.
- **Scales advice the co-op can't otherwise afford** (1 agronomist : hundreds of farms),
  and reaches farmers on **basic phones** (bilingual EN/Kiswahili SMS + offline box).
- **ROI:** the agent pays for itself if it saves **a single crop** in a season.

---

## 7. Masumi Evidence  *(Strong)*

Masumi is the **hire-and-pay-and-audit rail** for the agent — not a logo:

- **Identity:** the agent is registered with a Cardano **DID** (`agent_angawatch_advisory`);
  see `masumi_integration/client.py` (`_profile` / `registration`).
- **Discovery + service request:** a real **MIP-003 agentic service** —
  `GET /availability`, `/input_schema`, `POST /start_job`, `GET /status`,
  `/provide_input`, `/demo` — in `masumi_integration/service.py` (input: `greenhouse_id`;
  output: the advisory + `result_hash`).
- **Payment:** **pay-per-report** escrow (USDM/ADA on Cardano preprod). The 5-stage
  round-trip (discover → escrow → deliver → audit) is in `client.run_round_trip`;
  `RealMasumiBackend` (Masumi SDK `complete_payment`) is coded in
  `masumi_integration/real_backend.py`.
- **Auditability — REAL on-chain transaction (verifiable now):** the agent commits its
  **`result_hash` (the diagnosis + plan)** to Cardano preprod tx metadata (label `8434`,
  type `advisory-decision-log`):
  - **Tx:** `d7c8c82b7c74aac960daf20f7d4ce1f17278332e4753c4453b423412b5f6aca8`
  - **Explorer:** https://preprod.cardanoscan.io/transaction/d7c8c82b7c74aac960daf20f7d4ce1f17278332e4753c4453b423412b5f6aca8
  - **Commits result_hash:** `3a01387698c761c941b1736b5c999e84de437adc22580cb2c8712098461406e9`
  - Code: `masumi_integration/onchain.py`. With `MASUMI_ONCHAIN_LIVE=1` the app submits a
    **fresh** on-chain Decision-Log per round-trip.
- **Agent-to-agent coordination:** after diagnosing, the Advisory Agent becomes a **buyer**
  on Masumi and **hires a second DID-identified agent** — the **AgroInput Price Agent**
  (`agents/input_price.py`) — to source the recommended product's price/availability
  (`client.hire_agent`, shown in the Co-op tab).
- **Honest labeling:** the live demo's escrow click-through runs the labeled mock; the
  on-chain audit is a real, verifiable tx. Nothing hides a mock.

**Architecture (where Masumi enters):**
`Co-op → discover (DID) → service request (greenhouse_id) → escrow pay-per-report →
agent runs GraphRAG → deliver advisory → on-chain Decision-Log of result_hash →
[A2A] agent hires AgroInput Price Agent`. See `docs/architecture.md`.

---

## 8. Sokosumi Coworker Bonus  *(optional, +10)*

- **LIVE marketplace discovery (working):** with our `SOKOSUMI_API_KEY`,
  `python -m masumi_integration.sokosumi` makes a real authenticated call to the Sokosumi
  API (`GET /v1/agents`) and **discovers the 20 agent coworkers currently on the
  marketplace** (Deepfake Detector, Company Researcher, Google Maps Intelligence, …) with
  their credit pricing. This is shown live in the dashboard's Co-op tab. (Code:
  `masumi_integration/sokosumi.py`.) An **agent-discovery demo is "strong" Sokosumi evidence.**
- **Our coworker, ready to list:** the Angawatch Crop-Health Advisory Agent's coworker
  profile (name, input/output schema, transparent per-report pricing, tags) is built.
- **Plan to list it:** register the agent on the Masumi registry → DID, deploy the MIP-003
  endpoint publicly, submit the Sokosumi listing form (tally.so/r/nPLBaV) → the coworker
  appears on app.sokosumi.com for co-ops to discover, hire and pay.

---

## Appendix — how this maps to the 100-pt rubric (and where to push)

| Category | Pts | We have | To max the score |
|---|---|---|---|
| **Problem Clarity** | 20 | Named co-op buyer, manual rota workflow, numeric pain, success metric | Lead with the one-sentence strong statement + the numbers above |
| **Business Value** | 20 | KES/grade-A/officer-time impact (synthetic model) | Keep the numbers concrete; say "modeled on synthetic data" |
| **Agent Design** | 20 | Inputs/outputs/tools/logic/handoffs/limits; agentic (tool-choice + decision trace), not chat | Stress it *triages/diagnoses/prepares* + the human-approve step |
| **Masumi Fit** | 15 | DID, MIP-003 service, pay-per-report, **real on-chain tx**, A2A call | Show the Explorer link + the A2A call in the video |
| **Prototype/Demo** | 15 | Deployed app + 5–7 min video, LIVE/MOCK labels | Make sure the video labels live vs mock on screen |
| **Presentation** | 10 | This doc + deck + clear limits | State limits + Masumi role explicitly on a slide |
| **Sokosumi bonus** | +10 | **Live marketplace discovery (20 agents)** + coworker profile + listing plan | Show the live discovery in the video |
