# Angawatch — Demo Scripts

Two runnable demos. Both work **fully offline** (`--all-mock` / no creds) and degrade
gracefully; every step is labeled **LIVE** or **MOCK**.

Pre-flight (once):
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
python scripts/run_demo.py --all-mock      # or --prefer-live with creds
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
press **🌫️ Inject blight event** → the alert banner appears and the feed/graph update.

Punchline: *"The same event, caught early, is the difference between a 31% loss season and a 4%
loss season — which is exactly what the farmer's record shows."*

---

## B. Masumi "Business Agent" demo (≈5–7 min) — "a SACCO hires, pays, and audits an agent"

Goal: show Masumi playing a **real** role in identity, discovery, payment, and audit — over a
**verifiable, multi-factor** result recorded on-chain.

Run the dashboard: `streamlit run dashboard/app.py` (deployed link works too).

1. **Problem & record (30s)** — Tab *Farm record*: "Smallholders are invisible to lenders.
   Angawatch turns their greenhouse into a trusted, tamper-evident record." Show the graph.
2. **Hire the agent (1 min)** — Tab *Credit assessment* → **📊 Request assessment**.
   - The **deterministic 7-factor score** appears with **factor bars** (yield consistency,
     harvest trend, alert-response rate, disease handling, history, cooperative, climate).
   - Point at **confidence**, the **human-in-the-loop limits**, and the **result_hash**:
     *"never a single opaque number; reproducible; the agent recommends, a loan officer approves."*
3. **Pay via Masumi (2 min)** — **💳 Pay & deliver via Masumi**. Walk the 5-step stepper:
   - **① Identity** (DID) · **② Service request** · **③ Escrow payment** (USDM/ADA) ·
     **④ Deliver + Decision-Log hash** · **⑤ On-chain audit**.
   - Each step shows a 🟢 LIVE / 🟠 MOCK badge. In hybrid mode the audit shows a **real
     cardanoscan preprod link** (`prerecorded-real`) — *"here is the actual on-chain proof."*
4. **Why it's trustworthy (1 min)** — open `preprod.cardanoscan.io` link; explain the on-chain
   `result_hash` commits to the **numbers**, so anyone can verify the agent delivered that exact
   multi-factor result and was paid. Note the MIP-003 endpoints (`/start_job`, `/status`) make it
   a genuinely discoverable, hireable agent.
5. **Depth (optional, 1 min)** — Tab *Leaf scan & advisor*: classify a leaf photo; ask the
   GraphRAG advisor a question answered from the farmer's own record.

CLI equivalent of the finance loop:
```bash
python -m masumi_integration.demo        # 5-stage round-trip + audit
MASUMI_PRERECORDED_TX=<txhash> python -m masumi_integration.demo   # shows the real audit link
```

Rubric hits: **Problem Clarity** (record→finance), **Business Value** (a SACCO would pay for
explainable underwriting), **Agent Design** (deterministic, multi-factor, human-in-the-loop),
**Masumi Fit** (identity/discovery/escrow/audit are real, labeled), **Demo** (no hard-fail),
**Presentation** (honest mocks), and the **Sokosumi** bonus (see `docs/` + `python -m
masumi_integration.sokosumi`).

---

## Resilience cheatsheet (if something breaks on stage)
| Symptom | What happens automatically |
|---|---|
| No internet / Aura down | in-memory store, labeled `MOCK` |
| OpenRouter rate-limited | deterministic narrative, score unchanged |
| Twilio not joined | console alert with the identical message |
| Masumi preprod slow | mock round-trip + pre-recorded real tx link |
| HF model missing | labeled mock classifier |

`python scripts/run_demo.py --all-mock` is the bulletproof fallback for any venue.
```
