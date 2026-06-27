# Angawatch — Submission Readiness Checklist

Goal for tomorrow: a **functional** (not mock-only) demo + every required deliverable.
The app already never hard-fails; this checklist turns the labeled mocks into the real thing
where it counts, and lists the artifacts to submit.

Verify any time with: `python scripts/preflight.py` (connects to each service, prints LIVE/MOCK).

---

## TIER 1 — Make the live demo functional (~25 min, your accounts)
Paste these into **Streamlit Cloud → your app → ⋮ → Settings → Secrets** (private; never in the repo).
Format = the flat keys in [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example).

- [ ] **Neo4j Aura (free)** — neo4j.com/cloud/aura → create instance → copy `NEO4J_URI` (neo4j+s://…),
      `NEO4J_PASSWORD`. → the graph becomes a **real, persistent** record. *(seed it once:
      run `python scripts/seed_db.py` locally with the same creds, or it auto-seeds on first load.)*
- [ ] **OpenRouter (free)** — openrouter.ai → create key → `OPENROUTER_API_KEY`. → real LLM
      narration + GraphRAG crop-health advisory (instead of templates).
- [ ] **Twilio WhatsApp sandbox** — twilio.com/console → Messaging → Try it out → WhatsApp →
      send the `join <code>` from your phone → set `TWILIO_SID`, `TWILIO_TOKEN`,
      `TWILIO_FROM=whatsapp:+14155238886`, `FARMER_PHONE=+2547…` (the phone that joined).
      → the **Inject blight** button sends a **real WhatsApp** to your phone on stage. 🔥
- [ ] Keep `VISION_MODE=mock`, `MASUMI_MODE=mock` in the cloud (keeps the build light/reliable).
- [ ] Re-deploy, then open the app → the sidebar pills should read 🟢 **LIVE** for Graph/Alerts/LLM.
- [ ] Run `python scripts/preflight.py` locally with the same `.env` → aim for **4/5 LIVE**.

## TIER 2 — Real Masumi on-chain proof (~20 min) → the bounty differentiator
This flips "Masumi Fit" from mock to a **verifiable on-chain transaction**. The
Crop-Health Advisory Agent is hired and paid per report by the **Rift Valley Fresh Co-op**:
a **MIP-003 service** (input `greenhouse_id`; output a `result_hash` that commits to the
diagnosis + treatment plan), a **DID** identity, **pay-per-report escrow** (USDM/ADA on
Cardano preprod), and an on-chain **Decision-Log** (tx metadata label `8434`, type
`advisory-decision-log`: agent, subject, diagnosis, priority, `result_hash`). Full runbook:
[`docs/masumi_golive.md`](docs/masumi_golive.md). Short version:
- [ ] Create a Cardano **Preprod** wallet (Eternl/Lace), fund via the testnet faucet.
- [ ] Register the agent on **explorer.masumi.network/?network=preprod** → get a DID + a real tx.
- [ ] Set `MASUMI_PRERECORDED_TX=<that tx hash>` in secrets → the Decision-Log step shows a
      **real cardanoscan preprod link** (labeled `prerecorded-real`) while the live
      click-through stays safe.

## TIER 3 — Required submission artifacts
- [ ] **Pitch deck** (5–7 slides) — *ask me to generate it (`pptx`), or use the outline in
      [`docs/demo_script.md`](docs/demo_script.md).* Host on Google Slides ("anyone with link") or PDF.
- [ ] **Presentation video** (≤3 min) — screen-record the demo following the script in
      [`docs/demo_script.md`](docs/demo_script.md) (Loom/OBS). Upload to YouTube/Loom (public).
- [ ] **Deployed product link** — your Streamlit URL (must be a *working deployment*, which it is).
- [ ] **Form text** — paste the brief title / 50-word explanation / 200-word solution already drafted.
- [ ] **Problem statement** — [`docs/business_case.md`](docs/business_case.md) frames the
      co-op / off-taker problem the advisory agent solves; [`docs/knowledge_graph.md`](docs/knowledge_graph.md)
      is the "Graph Matters" artifact.
- [ ] **Sokosumi (+10)** — optional: `python -m masumi_integration.sokosumi` prints the coworker
      profile + steps; list at app.sokosumi.com if time allows.

## TIER 4 — Final rehearsal (do this last)
- [ ] `python scripts/run_demo.py --all-mock` → confirms the whole loop offline (bulletproof backup).
- [ ] `python scripts/run_demo.py` (with creds) → real WhatsApp + real graph write.
- [ ] Pre-warm the Aura instance ~10 min before (free tier can cold-start).
- [ ] Click through the dashboard once: Inject blight → Request advisory → Pay per report via Masumi.
- [ ] Have `--all-mock` ready as the no-wifi fallback.

---

## What's already done ✅
Working hero loop (sim → risk → alert → graph), agronomic **knowledge graph** + **Crop-Health
Advisory Agent** (traverses the KG → ranked, PHI-aware treatment plan + officer-visit priority;
a co-op agronomist approves), **co-op triage** of at-risk greenhouses, CrewAI + GraphRAG, MIP-003
agentic service, Masumi round-trip (mock + hybrid real-tx), **feature-phone SMS (EN/SW) + offline
box**, leaf classifier, light dashboard, 20 passing tests, docs (architecture + demo script),
repo pushed. *(Credit code archived to `archived/`, kept for reference; pytest ignores it.)*

## Honest labeling = points
Every mock is visibly labeled (🟠) in the UI and logs. Lead the demo with that — judges reward it.
