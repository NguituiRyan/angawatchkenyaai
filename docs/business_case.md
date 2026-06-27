# Angawatch — Business Agent case (Masumi bounty)

> **One-line problem.** A horticulture cooperative aggregating tomato from hundreds of
> contracted smallholder greenhouses runs a handful of field officers; blight and Tuta
> outbreaks spread in 24–48 h but officers visit on a fixed rota and diagnose by eye, so
> they reach infected farms days late — losing crop and the grade-A volume the co-op
> contracted to deliver. **Angawatch's Crop-Health Advisory Agent monitors every
> greenhouse, triages who's at risk today, diagnoses by traversing an agronomic knowledge
> graph, and prepares a ranked, pre-harvest-interval-aware treatment plan — so a few
> officers cover hundreds of farms by exception, with an auditable record of the advice.**

## Specific user & buyer
| Role | Who | Stake |
|---|---|---|
| **Buyer (pays)** | A horticulture **cooperative / off-taker** (aggregator, e.g. "Rift Valley Fresh Co-op") contracting ~400 greenhouses with ~3 field officers | Contracted supply volume + grade-A %; a lost crop is a delivery shortfall and a broken buyer contract |
| **Operator (uses it)** | The co-op's **field officer / agronomist** | Decides which farms to visit and signs off treatment advice |
| **Beneficiary** | The **smallholder farmer** | Gets a specific, timely diagnosis instead of a generic SMS |

The co-op has the budget, the workflow today (officers on a rota), and a direct financial
stake in crop survival — unlike a lender, it isn't waiting on repayment data it could get
for free.

## Manual workflow today (the pain)
1. Officers drive a **fixed fortnightly rota** — mostly visiting healthy farms.
2. Farmers **phone in** when they already see damage (often too late).
3. Diagnosis is **by eye**; advice is generic; the right product/interval is guesswork.
4. **Measurable pain:** an outbreak reaches a farm days after onset; 20–40% crop loss on
   affected houses; missed grade-A volume; 3 officers cannot meaningfully cover 400 farms.

## The agent's work (not a chatbot — it analyses, triages, prepares)
| | |
|---|---|
| **Role** | Greenhouse Crop-Health Advisor, hired per report by the co-op |
| **Inputs** | A greenhouse id + its sensor feed (temp, RH, leaf-wetness, soil, pest-trap), the co-op identity |
| **Tools / data** | Neo4j **agronomic knowledge graph** (GraphRAG traversal), the deterministic **risk engine** (Hutton/Tuta rules), an LLM **only to narrate** the graph's facts |
| **Outputs** | Per-farm **diagnosis** (disease + pathogen) · **officer-visit priority** · **ranked treatment plan** (efficacy → pre-harvest interval → cost, with beneficial-safety warnings) · a portfolio **triage list** across all farms · a reproducible **result_hash** |
| **Decision logic** | `Reading → INDICATES → Condition → FAVORS → Disease → CAUSED_BY → Pathogen` and `Disease ← CONTROLS ← Treatment`, ranked; risk level → visit priority |
| **Handoff / limits** | **Recommends; the co-op agronomist approves.** Diagnosis is from sensor microclimate + the graph, not a lab test — confirm visually. Follow label PHI + bee-safety. Efficacy/cost are regional estimates. |

## Business value
- **Reallocates scarce officers** from rota to exception: triage ranks 400 farms so the 3
  highest-risk get visited *today* instead of in two weeks.
- **Earlier intervention** → less crop lost on affected houses → more contracted grade-A
  volume delivered.
- **Right product, right interval** → fewer wasted/wrong sprays and PHI violations that
  would fail a buyer's residue check.
- **Scales advice** the co-op cannot otherwise afford (1 agronomist : hundreds of farms).

## Masumi's role (real work, not a logo)
The advisory agent is a hireable **MIP-003 service** with a Cardano **DID identity**. The
co-op **discovers** it, submits a **service request** (a greenhouse to advise), **pays per
report** (escrow, USDM/ADA on preprod), the agent **delivers** the diagnosis + plan, and
its **result_hash is Decision-Logged on-chain** (metadata label 8434, `advisory-decision-log`:
diagnosis + priority + hash). Because the hash commits to a *diagnosis a farmer acts on*
(not an opinion-score), the on-chain record does real work: an auditable trail of paid
agronomic advice — useful for the co-op's residue/traceability obligations and for paying
the agent per use without a centralized processor.

**Evidence:** a real preprod transaction carrying an Angawatch result_hash is verifiable on
cardanoscan (`MASUMI_PRERECORDED_TX` in the demo); the dashboard's Co-op tab runs the full
discover → pay → deliver → audit round-trip with LIVE/MOCK badges; `masumi_integration/`
holds the MIP-003 service, mock + real backends, and the on-chain writer. Sokosumi coworker
profile in `masumi_integration/sokosumi.py` (+10 bonus path).

## Boundaries (what it does / does not do)
- **Does:** monitor, triage, diagnose, rank treatments, prepare an officer brief, log on-chain.
- **Does not:** order or apply chemicals, decide without a human, replace lab confirmation,
  or make any financial/insurance decision.
- **Data:** synthetic/anonymized greenhouse data only.

See `docs/demo_script.md` for the 5–7 minute walkthrough and `docs/knowledge_graph.md` for
why the graph is essential.
