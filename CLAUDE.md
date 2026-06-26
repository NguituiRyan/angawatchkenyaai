# CLAUDE.md — engineering conventions for Angawatch

Angawatch: a smallholder tomato-greenhouse → (a) early crop-saving alerts and
(b) a verified Neo4j farm record that lenders/insurers price risk against via a
CrewAI Credit-Risk Agent hired, paid, and audited through the **Masumi** network.
Submission: Kenya AI Challenge (AgriFin track + Masumi "Business Agent" bounty).

## Non-negotiable rules
1. **All I/O goes through an interface**, never a raw driver/SDK call in feature code:
   - data → `graph.store.GraphStore` (Neo4j or in-memory mirror)
   - alerts → `alerts.channel.AlertChannel`
   - Masumi → `masumi_integration.client.MasumiClient`
2. **Every external integration degrades to a clearly-LABELED mock.** Each fallback
   sets a `mode` field on its return object and logs `[MOCK]`. Hiding mocks is a
   rubric failure; surfacing them scores points. Use `logging_setup.tag()` / `badge()`.
3. **Deterministic cores stay pure.** `risk/rules.py` and `scoring/factors.py` take
   plain data in → return plain data out. No LLM, no network. They are the
   verifiable, unit-tested heart — the LLM only *narrates* their numbers.
4. **No secrets in the repo.** `.env` only (gitignored). Keep `.env.example` current.
5. **Synthetic/anonymized data only.** No real personal data, ever.
6. **Human-in-the-loop.** The Credit-Risk Agent *recommends*; a loan officer approves.
   Output must always show factors, confidence, and stated limits.
7. **Each module is independently runnable:** ship `python -m <pkg>.demo`
   (e.g. `python -m graph.demo`, `python -m risk.demo`, `python -m scoring.demo`).
8. **If blocked >10 min on an integration, ship the labeled mock and move on.**
9. **Commit after each working checkpoint.**

## Layout
`config.py` (settings + `*_mode()` resolvers) · `logging_setup.py` (LIVE/MOCK tags) ·
`graph/` · `sim/` · `risk/` · `alerts/` · `scoring/` · `agents/` · `vision/` ·
`masumi_integration/` · `api/` · `dashboard/` · `scripts/` (`seed_db.py`, `run_demo.py`) · `docs/`.

## Modes (env)
`GRAPH_BACKEND=auto|neo4j|memory` · `LLM_MODE=auto|live|mock` ·
`VISION_MODE=auto|live|mock` · `MASUMI_MODE=real|mock`. `auto` = live if the
credential is present and the service reachable, else mock.

## Deploy note
Streamlit Community Cloud uses `requirements.txt` (light: NO torch/crewai). The
deployed app uses the in-process Masumi mock + a direct OpenRouter call for
narration + mock vision. The full local stack uses `requirements-full.txt`.
