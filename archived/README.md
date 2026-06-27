# archived/ — deprecated credit-scoring direction

This folder holds the **credit-scoring** code that Angawatch no longer ships. It is kept
on disk for reference and reversibility; nothing in the live app imports it, and pytest
ignores it (`conftest.py: collect_ignore_glob = ["archived/*"]`).

## Why it was dropped
Turning the farm record into a lender-facing **credit score** failed on five fronts at
once and we cut it deliberately:

- **Data** — sensors give microclimate, not yield/loss; the financially-meaningful factors
  are self-reported (untrusted), and an append-only graph proves *no-edit*, not *true*.
- **Model** — even with perfect data it measures capacity to *produce*, not willingness to
  *repay*, and has zero repayment history (the most predictive variable). It's pre-screening.
- **Customer** — a SACCO solves cold-start cheaply (starter loan + guarantors) and gets the
  better signal (repayment history) for free within a year, so we'd charge for a worse one.
- **Financing** — every bundle (free kit + loan, alert→micro-loan, deduct-at-source) leaked.
- **Masumi fit** — a score is an opinion; an on-chain audit of an opinion does little real work.

## What replaced it
A **Crop-Health Advisory Agent** (`agents/advisory.py`) hired by a **cooperative / off-taker**
via Masumi — pay-per-report for a graph-grounded diagnosis + ranked treatment plan, with the
result hash (the *diagnosis*, real work) Decision-Logged on-chain. See `docs/business_case.md`.

## Contents
- `scoring/` — deterministic 7-factor `CreditScorer` + models.
- `credit_crew.py` — the `CreditRiskAgent` (score + LLM narration + audit write).
- `score_card.py` — the Streamlit credit score-card component.
- `test_scoring.py` — the scorer unit tests.

## Restore (if ever needed)
`git mv archived/scoring scoring && git mv archived/credit_crew.py agents/credit_crew.py`
(and the rest), then re-wire the dashboard/Masumi calls. Git history is preserved.
