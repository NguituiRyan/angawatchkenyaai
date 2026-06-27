"""GraphRAG Agronomist agent — answers by TRAVERSING the agronomic knowledge graph
multi-hop, and shows its reasoning (the path + the Cypher), grounded in graph facts.

This is what makes the graph *matter*: the answer to "why was I warned and what do I
do" is a 5-hop walk Alert -> Disease -> Pathogen / Conditions / Treatments, ranked by
efficacy + pre-harvest interval + cost, with a beneficial-safety check — not a flat lookup.
"""
from __future__ import annotations

from agents.llm import _openrouter_client, clean_llm_text
from graph import kg
from logging_setup import get_logger

log = get_logger("agents.agronomist")

EXPLAIN_CYPHER = (
    "MATCH (a:Alert {id:$id})-[:FOR_DISEASE]->(d:Disease)-[:CAUSED_BY]->(p:Pathogen)\n"
    "OPTIONAL MATCH (a)-[:TRIGGERED_BY]->(r:Reading)-[:INDICATES]->(c:Condition)\n"
    "MATCH (t:Treatment)-[ctl:CONTROLS]->(d)\n"
    "OPTIONAL MATCH (t)-[:HARMFUL_TO]->(b:Beneficial)\n"
    "RETURN d, p, collect(DISTINCT c.name) AS conditions,\n"
    "       collect(DISTINCT {t:t, efficacy:ctl.efficacy, harms:b.name}) AS treatments\n"
    "ORDER BY ctl.efficacy DESC, t.phi_days ASC, t.cost_kes ASC"
)


def _efficacy_label(t: dict) -> str:
    return t.get("edge_efficacy") or t.get("efficacy") or "—"


def _facts(path: dict) -> str:
    d = path.get("disease") or {}
    lines = [f"Alert: {path['alert'].get('kind')} ({path['alert'].get('level')})",
             f"Diagnosis: {d.get('name')} caused by {path.get('pathogen')}",
             f"Indicated conditions: {', '.join(path.get('conditions') or []) or 'n/a'}"]
    for t in path.get("treatments", [])[:5]:
        warn = f"; HARMFUL to {', '.join(t['harmful_to'])}" if t.get("harmful_to") else ""
        lines.append(f"- {t['name']} ({t.get('type')}, {t.get('active')}): "
                     f"efficacy {_efficacy_label(t)}, PHI {t.get('phi_days')}d, "
                     f"~KES {t.get('cost_kes')}{warn}")
    return "\n".join(lines)


PROMPT = (
    "You are an agronomist advising a Kenyan smallholder tomato grower. Using ONLY the "
    "graph facts below (do not invent), write 3-5 short sentences: name the disease and what "
    "drove the diagnosis (the conditions), then the recommended actions in order (cheap/"
    "cultural first, then chemical), noting any pre-harvest-interval or beneficial-safety "
    "warning. Be practical.\n\nGRAPH FACTS:\n{facts}"
)


def _template(path: dict) -> str:
    """Deterministic narration from the graph facts (no LLM)."""
    d = path.get("disease") or {}
    conds = ", ".join(path.get("conditions") or []) or "the recent conditions"
    tops = path.get("treatments", [])[:3]
    rec = "; ".join(f"{t['name']} (PHI {t.get('phi_days')}d)" for t in tops)
    warn = next((t for t in path.get("treatments", []) if t.get("harmful_to")), None)
    txt = (f"{d.get('name','This problem')} (caused by {path.get('pathogen')}) is indicated by "
           f"{conds}. Recommended, in order: {rec}. Start with cultural/cheap controls before "
           "spraying.")
    if warn:
        txt += f" Note: {warn['name']} is harmful to {', '.join(warn['harmful_to'])} — avoid near flowering."
    return txt


def _narrate(path: dict, settings) -> tuple[str, str]:
    facts = _facts(path)
    if settings.llm_mode() == "live":
        client = _openrouter_client(settings)
        if client is not None:
            try:
                model = settings.OPENROUTER_MODEL.replace("openrouter/", "")
                r = client.chat.completions.create(
                    model=model, temperature=0.3, max_tokens=320,
                    messages=[{"role": "user", "content": PROMPT.format(facts=facts)}])
                return clean_llm_text(r.choices[0].message.content), "live"
            except Exception as exc:  # noqa: BLE001
                log.warning("agronomist narration failed (%s) — template", exc)
    return _template(path), "mock"


class AgronomistAgent:
    def __init__(self, settings) -> None:
        self.settings = settings

    def explain_alert(self, store, alert_id: str, narrate: bool = True) -> dict | None:
        path = kg.explain_alert(store, alert_id)
        if not path:
            return None
        narrative, mode = _narrate(path, self.settings) if narrate else (_template(path), "mock")
        path["narrative"] = narrative
        path["narration_mode"] = mode
        path["cypher"] = EXPLAIN_CYPHER
        path["backend"] = store.mode
        return path

    def diagnose(self, store, gh_id: str) -> dict:
        d = kg.diagnose(store, gh_id)
        # attach ranked treatments for the top disease
        if d["diseases"]:
            top = d["diseases"][0]
            d["treatments"] = kg.treatments_for(store, "Disease", top["id"])
        return d
