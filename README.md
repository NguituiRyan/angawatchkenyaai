# 🌱 Angawatch

**Early warnings that save crops — and a verified farm record that unlocks finance.**

Angawatch turns a smallholder tomato greenhouse into two things at once:

1. **A guardian.** Sensors (or a simulator) stream temperature, humidity, leaf-wetness,
   soil-moisture and pest-trap counts. A risk engine catches blight/Tuta danger *early*
   and sends the farmer a **WhatsApp/SMS warning in time to act**.
2. **A credit history.** Every reading, alert, action and harvest is written to a
   **Neo4j** graph — the farm's trusted, tamper-evident record. On top sits a CrewAI
   **Credit-Risk Agent** that a SACCO / MFI / insurer can **discover, hire, pay (escrow),
   and audit through the [Masumi](https://www.masumi.network/) network**, turning that
   record into an *explainable, multi-factor* risk score.

> Built for the **Kenya AI Challenge** — AgriFin track + Masumi "Business Agent" bounty.

---

## Why it's trustworthy (and demo-proof)
- **Deterministic core, narrating LLM.** Risk rules and the 7-factor credit score are
  pure Python — reproducible and unit-tested. The LLM only *explains* the numbers.
- **Nothing hard-fails.** Every external service (Neo4j, OpenRouter, Twilio, the leaf
  classifier, Masumi) has a **clearly-labeled mock fallback**. Run the whole thing
  offline with `--all-mock`.
- **Honest labels.** Live vs. mock is shown in the UI and logs everywhere — hiding a
  mock is a rubric failure; we surface them.
- **Human-in-the-loop.** The agent *recommends*; a loan officer approves. Every
  assessment states its limits.

## Quickstart
```bash
# 1. install (core)            full local stack: pip install -r requirements-full.txt
pip install -r requirements.txt

# 2. configure (optional — without creds, everything runs as a labeled mock)
cp .env.example .env           # add Neo4j Aura / OpenRouter / Twilio keys if you have them

# 3. seed the farm-and-finance graph  (Module 1 checkpoint: prints node/rel stats)
python scripts/seed_db.py

# 4. run the narrated end-to-end demo (resilient; --all-mock for fully offline)
python scripts/run_demo.py --all-mock        # (coming in later modules)

# 5. lender dashboard
streamlit run dashboard/app.py                # (coming in Module 4)
```

Each module is independently runnable: `python -m graph.demo`, `python -m risk.demo`,
`python -m scoring.demo`, `python -m alerts.demo`, `python -m masumi_integration.demo`.

## Live vs. mock matrix
| Capability | Live when… | Otherwise (labeled mock) |
|---|---|---|
| Farm graph | `NEO4J_*` set & reachable | in-memory store |
| Agent narration | `OPENROUTER_API_KEY` set | deterministic templated text |
| Farmer alert | `TWILIO_*` set | console message |
| Leaf classifier | local HF model available | deterministic stub |
| Masumi pay/audit | `MASUMI_MODE=real` + keys | simulated on-chain round-trip |

## Status
- [x] Module 1 — scaffold + Neo4j/in-memory graph + synthetic seed
- [ ] Module 2 — simulator → risk engine → alert
- [ ] Module 3 — explainable Credit-Risk Agent
- [ ] Module 4 — Streamlit lender dashboard (deployed)
- [ ] Module 5 — Masumi integration (identity / request / escrow / audit)
- [ ] Module 6 — leaf classifier + GraphRAG advisory
- [ ] Module 7 — Sokosumi registration (+10)

See [`docs/architecture.md`](docs/architecture.md) and [`docs/demo_script.md`](docs/demo_script.md).
