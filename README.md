# 🌱 Angawatch

**Early warnings that save crops — and a graph-grounded crop-health advisory a co-op hires via Masumi.**

Angawatch turns a smallholder tomato greenhouse into two things at once:

1. **A guardian.** Sensors (or a simulator) stream temperature, humidity, leaf-wetness,
   soil-moisture and pest-trap counts. A risk engine catches blight/Tuta danger *early*
   and sends the farmer a **WhatsApp/SMS warning in time to act**.
2. **A hireable agronomist.** Every reading, alert, action and harvest is written to a
   **Neo4j** graph that is joined to an **agronomic knowledge graph** (crop ↔ disease ↔
   microclimate ↔ treatment). On top sits a **Crop-Health Advisory Agent** that a
   horticulture **cooperative / off-taker** can **discover, hire, pay per report (escrow),
   and audit through the [Masumi](https://www.masumi.network/) network** — it triages which
   farms are at risk, diagnoses by **traversing the graph**, and returns a ranked,
   pre-harvest-interval-aware treatment plan. A co-op agronomist approves.

> Built for the **Kenya AI Challenge** — Agriculture + Neo4j graph track + Masumi "Business Agent" bounty.
> See [`docs/business_case.md`](docs/business_case.md) for the named buyer, workflow, pain, value and Masumi role.

---

## Why it's trustworthy (and demo-proof)
- **Deterministic core, narrating LLM.** The risk rules and the agronomic knowledge-graph
  traversals are pure Python — reproducible and unit-tested. The LLM only *narrates* the
  graph's facts; the diagnosis + ranked plan come from the graph.
- **Nothing hard-fails.** Every external service (Neo4j, OpenRouter, Twilio, the leaf
  classifier, Masumi) has a **clearly-labeled mock fallback**. Run the whole thing
  offline with `--all-mock`.
- **Honest labels.** Live vs. mock is shown in the UI and logs everywhere — hiding a
  mock is a rubric failure; we surface them.
- **Human-in-the-loop.** The agent *recommends*; the co-op agronomist approves. Every
  report states its evidence, confidence and limits.

## Quickstart
```bash
# 1. install (core)            full local stack: pip install -r requirements-full.txt
pip install -r requirements.txt

# 2. configure (optional — without creds, everything runs as a labeled mock)
cp .env.example .env           # add Neo4j Aura / OpenRouter / Twilio keys if you have them

# 3. seed the farm-and-finance graph  (Module 1 checkpoint: prints node/rel stats)
python scripts/seed_db.py

# 4. run the narrated end-to-end demo (resilient; --all-mock for fully offline)
python scripts/run_demo.py --all-mock        # blight -> alert -> graph -> advisory -> on-chain audit

# 5. dashboard (the submission link)
streamlit run dashboard/app.py
```

Each module is independently runnable:
```bash
python -m graph.demo          # seeded graph + Farmer-A subgraph
python -m sim.demo            # sensor stream + injected blight
python -m risk.demo           # pure rule checks
python -m alerts.demo         # alert channel (WhatsApp/console)
python -m agents.demo         # Crop-Health Advisory Agent (diagnosis + ranked plan + hash)
python -m masumi_integration.demo      # 5-stage Masumi round-trip + audit
python -m masumi_integration.sokosumi  # Sokosumi coworker registration (+10)
python -m vision.demo         # leaf classifier (mock; VISION_MODE=live for the HF model)
```
Run the tests: `python -m pytest -q` (20 tests — rules, knowledge-graph traversal, advisory, dashboard smoke).

**Going live for the demo:** `python scripts/preflight.py` connects to each service and reports
LIVE/MOCK with the exact fix. See [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) (what to wire +
artifacts to submit) and [`docs/masumi_golive.md`](docs/masumi_golive.md) (real on-chain proof).

## Deploy to Streamlit Community Cloud (the submission link)
1. Push this repo to GitHub (done).
2. On [share.streamlit.io](https://share.streamlit.io) → **New app** → pick this repo,
   branch `main`, file `dashboard/app.py`.
3. **Advanced settings → Secrets**: paste the keys from
   [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example) (Neo4j Aura is needed
   so the cloud app has a database; keep `VISION_MODE=mock`, `MASUMI_MODE=mock`).
4. Deploy. The cloud build uses the light `requirements.txt` (no torch/CrewAI) for reliability.

## Live vs. mock matrix
| Capability | Live when… | Otherwise (labeled mock) |
|---|---|---|
| Farm graph | `NEO4J_*` set & reachable | in-memory store |
| Agent narration | `OPENROUTER_API_KEY` set | deterministic templated text |
| Farmer alert | `TWILIO_*` set | console message |
| Leaf classifier | local HF model available | deterministic stub |
| Masumi pay/audit | `MASUMI_MODE=real` + keys | simulated on-chain round-trip |

## Status
- [x] Scaffold + Neo4j/in-memory graph + synthetic seed
- [x] Simulator → risk engine → early WhatsApp/SMS alert (crop-saving hero loop)
- [x] **Agronomic knowledge graph** (crop ↔ disease ↔ microclimate ↔ treatment) joined to the farm record
- [x] **Crop-Health Advisory Agent** — GraphRAG diagnosis + ranked, PHI-aware plan + co-op triage
- [x] Streamlit dashboard (deployable): Farm record · Crop doctor (GraphRAG) · Co-op triage & hire · Leaf scan · Feature phone
- [x] Masumi integration — DID identity / discover / pay-per-report (escrow) / on-chain audit; MIP-003 service
- [x] Feature-phone reach — bilingual EN/SW two-way SMS + offline alert box
- [x] Sokosumi coworker profile (+10)
- [~] Credit-score direction **dropped** → `archived/` (see [`archived/README.md`](archived/README.md))

See [`docs/business_case.md`](docs/business_case.md) (buyer/value/Masumi),
[`docs/knowledge_graph.md`](docs/knowledge_graph.md) (why the graph matters),
[`docs/architecture.md`](docs/architecture.md) and
[`docs/demo_script.md`](docs/demo_script.md) (click-by-click).
