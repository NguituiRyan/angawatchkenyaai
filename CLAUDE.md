# CLAUDE.md — engineering conventions for Angawatch

Angawatch: a smallholder tomato-greenhouse → (a) early crop-saving alerts and
(b) a **Crop-Health Advisory Agent** that traverses a Neo4j **agronomic knowledge graph**
to diagnose disease and prepare a ranked treatment plan — hired, paid per report, and
audited on-chain by a **cooperative / off-taker** through the **Masumi** network.
Submission: Kenya AI Challenge (Agriculture + Neo4j graph track + Masumi "Business Agent" bounty).

> Pivot note (2026-06): the lender-facing **credit-score** direction was dropped (see
> `archived/README.md`) — we can't get trustworthy yield/repayment data, a SACCO gets a
> better signal for free, and an on-chain audit of an opinion does no real work. The advisory
> agent uses what Angawatch owns (sensor + agronomic intelligence). Credit code lives in
> `archived/` (out of the live app; pytest ignores it).

## Non-negotiable rules
1. **All I/O goes through an interface**, never a raw driver/SDK call in feature code:
   - data → `graph.store.GraphStore` (Neo4j or in-memory mirror)
   - alerts → `alerts.channel.AlertChannel`
   - Masumi → `masumi_integration.client.MasumiClient`
2. **Every external integration degrades to a clearly-LABELED mock.** Each fallback
   sets a `mode` field on its return object and logs `[MOCK]`. Hiding mocks is a
   rubric failure; surfacing them scores points. Use `logging_setup.tag()` / `badge()`.
3. **Deterministic cores stay pure.** `risk/rules.py` and the agronomic knowledge graph
   (`graph/agronomy.py` + `graph/kg.py` traversals) take plain data in → return plain data
   out. No LLM, no network in the core. They are the verifiable, unit-tested heart — the
   LLM only *narrates* the graph's facts.
4. **No secrets in the repo.** `.env` only (gitignored). Keep `.env.example` current.
5. **Synthetic/anonymized data only.** No real personal data, ever.
6. **Human-in-the-loop.** The Advisory Agent *recommends*; the co-op agronomist approves.
   Output must always show the diagnosis evidence, confidence, and stated limits.
7. **Each module is independently runnable:** ship `python -m <pkg>.demo`
   (e.g. `python -m graph.demo`, `python -m risk.demo`, `python -m agents.demo`).
8. **If blocked >10 min on an integration, ship the labeled mock and move on.**
9. **Commit after each working checkpoint.**

## Layout
`config.py` (settings + `*_mode()` resolvers) · `logging_setup.py` (LIVE/MOCK tags) ·
`graph/` (incl. `agronomy.py` + `kg.py` knowledge graph) · `sim/` · `risk/` · `alerts/` ·
`agents/` (`advisory.py`, `agronomist.py`) · `comms/` · `vision/` · `masumi_integration/` ·
`api/` · `dashboard/` · `scripts/` (`seed_db.py`, `run_demo.py`) · `docs/` · `archived/` (deprecated credit).

## Modes (env)
`GRAPH_BACKEND=auto|neo4j|memory` · `LLM_MODE=auto|live|mock` ·
`VISION_MODE=auto|live|mock` · `MASUMI_MODE=real|mock`. `auto` = live if the
credential is present and the service reachable, else mock.

## Deploy note
Streamlit Community Cloud uses `requirements.txt` (light: NO torch/crewai). The
deployed app uses the in-process Masumi mock + a direct OpenRouter call for
narration + mock vision. The full local stack uses `requirements-full.txt`.
