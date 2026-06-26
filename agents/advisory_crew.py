"""GraphRAG advisory agent: answers a farmer's question grounded in THEIR own
Neo4j subgraph (not generic text). Live via OpenRouter; otherwise a labeled
deterministic answer built from the farmer's record.
"""
from __future__ import annotations

import json

from agents.llm import _openrouter_client
from logging_setup import get_logger

log = get_logger("agents.advisory")

PROMPT = (
    "You are Angawatch, an agronomy + farm-finance advisor for a Kenyan smallholder "
    "tomato grower. Answer the farmer's question in 3-5 short sentences, grounded ONLY "
    "in their farm record below (cite their own numbers: yields, alerts, losses, "
    "greenhouse). Be practical and encouraging. If finance is asked, note that a loan "
    "officer makes the final decision.\n\nFARM RECORD (JSON):\n{record}\n\n"
    "QUESTION: {question}"
)


def _summary(sub: dict) -> str:
    g = sub.get("greenhouse") or {}
    hs = sub.get("harvests", [])
    ys = [h.get("yield_kg") for h in hs]
    losses = [h.get("loss_pct") for h in hs]
    coop = (sub.get("cooperative") or {}).get("name")
    bits = [f"{len(sub.get('seasons', []))} seasons on record"]
    if ys:
        bits.append(f"yields {ys} kg")
    if losses:
        bits.append(f"losses {losses}%")
    bits.append(f"acted on {sub.get('action_count')}/{sub.get('alert_count')} disease alerts")
    if g:
        bits.append(f"{g.get('structure_type')} greenhouse, "
                    f"{'netted' if g.get('has_netting') else 'no net'}, "
                    f"{g.get('irrigation')} irrigation")
    if coop:
        bits.append(f"member of {coop}")
    return "; ".join(bits)


def _template_answer(sub: dict, question: str) -> str:
    s = _summary(sub)
    q = question.lower()
    if any(k in q for k in ("blight", "spray", "fungicide", "disease")):
        tip = ("On humid nights (RH>=90%, 16-26C) ventilate at dawn and apply a protectant "
               "fungicide early — your record shows acting fast cut losses sharply.")
    elif any(k in q for k in ("loan", "credit", "finance", "borrow")):
        tip = ("Your improving, consistent yields strengthen your credit profile; a loan "
               "officer reviews the agent's recommendation before any decision.")
    elif any(k in q for k in ("water", "irrigat", "soil")):
        tip = "Keep soil VWC ~0.30-0.42; drip irrigation plus netting improves resilience."
    else:
        tip = "Keep logging readings and acting on alerts — it builds both yield and credit."
    return f"Based on your record ({s}). {tip}"


def answer(settings, store, farmer_id: str, question: str) -> dict:
    sub = store.get_farmer_subgraph(farmer_id)
    if not sub.get("farmer"):
        return {"answer": "No record found for this farmer.", "mode": "mock",
                "grounded_on": farmer_id}
    if settings.llm_mode() == "live":
        client = _openrouter_client(settings)
        if client is not None:
            try:
                model = settings.OPENROUTER_MODEL.replace("openrouter/", "")
                resp = client.chat.completions.create(
                    model=model, temperature=0.4, max_tokens=350,
                    messages=[{"role": "user", "content": PROMPT.format(
                        record=json.dumps(sub, default=str), question=question)}])
                return {"answer": resp.choices[0].message.content.strip(),
                        "mode": "live", "grounded_on": farmer_id}
            except Exception as exc:  # noqa: BLE001
                log.warning("advisory live failed (%s) — template", exc)
    return {"answer": _template_answer(sub, question), "mode": "mock", "grounded_on": farmer_id}
