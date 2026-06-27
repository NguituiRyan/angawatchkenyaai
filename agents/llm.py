"""Narration layer for the Credit-Risk Agent.

The score is ALWAYS deterministic (scoring/). This module only turns those numbers
into grounded prose. Order of preference:
  live  -> OpenRouter (OpenAI-compatible) call, grounded in the exact numbers
  mock  -> deterministic template built from the factor objects
It is forbidden from inventing figures — numbers are passed in as data.
"""
from __future__ import annotations

import re

from logging_setup import get_logger

log = get_logger("agents.llm")


def clean_llm_text(text: str | None) -> str:
    """Strip special tokens some free models leak (e.g. Gemma's <pad>/<eos>)."""
    return re.sub(r"</?(pad|eos|bos|s|end_of_turn)>", "", (text or "")).strip()


def build_crewai_llm(settings):
    """A CrewAI LLM bound to OpenRouter, or None if unavailable."""
    try:
        from crewai import LLM
        return LLM(model=settings.OPENROUTER_MODEL,
                   base_url=settings.OPENROUTER_BASE_URL,
                   api_key=settings.OPENROUTER_API_KEY)
    except Exception as exc:  # noqa: BLE001
        log.warning("CrewAI LLM unavailable (%s)", exc)
        return None


def _openrouter_client(settings):
    try:
        from openai import OpenAI
        return OpenAI(api_key=settings.OPENROUTER_API_KEY,
                      base_url=settings.OPENROUTER_BASE_URL)
    except Exception as exc:  # noqa: BLE001
        log.warning("OpenRouter client unavailable (%s)", exc)
        return None


def chat(settings, messages, temperature: float = 0.2, max_tokens: int = 600,
         retries: int = 2) -> str | None:
    """Generic OpenRouter chat completion; returns cleaned text or None (caller falls back).
    Retries briefly on transient errors (free models 429 intermittently)."""
    import time
    client = _openrouter_client(settings)
    if client is None:
        return None
    model = settings.OPENROUTER_MODEL.replace("openrouter/", "")
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
            text = clean_llm_text(resp.choices[0].message.content)
            if text:
                return text
        except Exception as exc:  # noqa: BLE001
            log.warning("OpenRouter chat failed (attempt %d: %s)", attempt + 1, exc)
        if attempt < retries:
            time.sleep(1.2 * (attempt + 1))
    return None


def _facts(assessment, subgraph) -> str:
    lines = [f"Farmer: {assessment.farmer_id}",
             f"Overall score: {assessment.overall_score}/100",
             f"Credit band: {assessment.credit['grade']} ({assessment.credit['limit']})",
             f"Insurance band: {assessment.insurance['grade']}",
             f"Confidence: {assessment.confidence['level']} ({assessment.confidence['value']})"]
    for f in assessment.factors:
        lines.append(f"- {f.label}: {f.sub_score}/100 (weight {f.weight}, "
                     f"contributes {f.contribution}); evidence={f.evidence}")
    return "\n".join(lines)


PROMPT = (
    "You are a credit-risk analyst writing for a SACCO loan officer in Kenya. "
    "Using ONLY the figures below (do not invent or change any number), write a "
    "concise 4-6 sentence explanation of why this smallholder tomato farmer received "
    "this score. Name the 2 strongest factors and the main watch-out, reference the "
    "concrete evidence (yields, alert response, losses), and end with a one-line "
    "recommendation. Make clear this is a recommendation for a human loan officer, "
    "not a final decision.\n\nFIGURES:\n{facts}"
)


def openrouter_narrative(assessment, subgraph, settings) -> str | None:
    client = _openrouter_client(settings)
    if client is None:
        return None
    try:
        model = settings.OPENROUTER_MODEL.replace("openrouter/", "")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user",
                       "content": PROMPT.format(facts=_facts(assessment, subgraph))}],
            temperature=0.3, max_tokens=400,
        )
        return clean_llm_text(resp.choices[0].message.content) or None
    except Exception as exc:  # noqa: BLE001
        log.warning("OpenRouter narration failed (%s) — using template", exc)
        return None


def deterministic_narrative(assessment, subgraph) -> str:
    fs = sorted(assessment.factors, key=lambda f: f.contribution, reverse=True)
    top = fs[:2]
    weak = min(assessment.factors, key=lambda f: f.sub_score)
    farmer = (subgraph.get("farmer") or {}).get("name", assessment.farmer_id)
    ys = (next((f for f in assessment.factors if f.name == "yield_consistency"), None)
          or top[0]).evidence.get("yields_kg")
    resp = next((f for f in assessment.factors if f.name == "alert_response_rate"), None)
    parts = [
        f"{farmer} qualifies for Credit Band {assessment.credit['grade']} "
        f"({assessment.credit['limit']}) with {assessment.confidence['level']} confidence "
        f"(score {assessment.overall_score}/100).",
        f"Its strongest signals are {top[0].label.lower()} ({top[0].sub_score}/100) and "
        f"{top[1].label.lower()} ({top[1].sub_score}/100)"
        + (f", with yields of {ys} kg across recent seasons." if ys else "."),
    ]
    if resp and resp.evidence.get("alerts"):
        parts.append(f"The farmer acted on {resp.evidence.get('actioned')} of "
                     f"{resp.evidence.get('alerts')} disease alerts, a strong behavioural signal.")
    parts.append(f"Main watch-out: {weak.label.lower()} ({weak.sub_score}/100)"
                 + (f" — {weak.note}." if weak.note else "."))
    rec = {"A": "Recommend approval at the Band A limit, subject to loan-officer review.",
           "B": "Recommend a moderate facility with standard monitoring.",
           "C": "Recommend a small starter facility with close monitoring.",
           "D": "Recommend referral / a supervised micro-pilot rather than a standard loan."}
    parts.append(rec.get(assessment.credit["grade"], "Refer to a loan officer."))
    parts.append("This is a recommendation to support a human loan officer, not a final "
                 "lending decision; standard KYC applies.")
    return " ".join(parts)


def narrate(assessment, subgraph, settings) -> tuple[str, str]:
    """Return (narrative, mode). Tries OpenRouter when LLM is live, else templates."""
    if settings.llm_mode() == "live":
        text = openrouter_narrative(assessment, subgraph, settings)
        if text:
            return text, "live"
    return deterministic_narrative(assessment, subgraph), "mock"
