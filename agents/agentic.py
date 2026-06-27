"""Agentic agronomist — the agent DECIDES which graph tools to call to answer a
free-form question, in a thought -> action -> observation loop, and returns the full
decision trace (so judges can see it reasoning, not just narrate a canned query).

- LIVE: an LLM plans each step, choosing among the Cypher-backed tools in graph_tools
  (including composing its own read-only Cypher via `ask_graph` = guarded text2cypher).
- MOCK / fallback: a deterministic multi-step plan (diagnose -> explain -> treatments)
  so the demo is bulletproof and STILL shows a real multi-tool trace.

This is what makes it an agent, not a GraphRAG lookup: the traversal path is chosen at
run time, and every step is auditable.
"""
from __future__ import annotations

import json
import re

from agents import graph_tools as gt
from agents.llm import chat, clean_llm_text
from logging_setup import get_logger

log = get_logger("agents.agentic")

SYSTEM = (
    "You are an agronomist AGENT for a Kenyan greenhouse-tomato cooperative. Answer the "
    "user's question by REASONING over a Neo4j agronomic knowledge graph using TOOLS. Think "
    "step by step and call ONE tool at a time; use the observations to decide the next step.\n\n"
    "TOOLS:\n{tools}\n\n{schema}\n\n"
    "Respond with ONE JSON object per turn, nothing else. To use a tool:\n"
    '  {{"thought": "<why this step>", "tool": "<tool_name>", "args": {{...}}}}\n'
    "When you have enough to answer:\n"
    '  {{"thought": "<wrap-up>", "final_answer": "<concise, practical advice for a field '
    "officer; name the disease, the evidence, and the ranked actions cheapest/cultural first; "
    'note any pre-harvest-interval or bee-safety warning>"}}\n'
    "Prefer the typed tools; use ask_graph only for questions they cannot answer. "
    "Take at most {max_steps} tool steps."
)


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    text = clean_llm_text(text)
    # strip code fences
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.I | re.M).strip()
    try:
        return json.loads(text)
    except Exception:  # noqa: BLE001
        pass
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e > s:
        try:
            return json.loads(text[s:e + 1])
        except Exception:  # noqa: BLE001
            return None
    return None


class AgenticAgronomist:
    def __init__(self, settings) -> None:
        self.settings = settings

    def answer(self, store, gh_id: str, question: str, max_steps: int = 4) -> dict:
        if self.settings.llm_mode() == "live":
            out = self._react(store, gh_id, question, max_steps)
            if out:
                return out
        return self._fallback(store, gh_id, question)

    # ---- live LLM planning loop -------------------------------------------
    def _react(self, store, gh_id, question, max_steps) -> dict | None:
        sys = SYSTEM.format(tools=gt.tool_catalog(), schema=gt.SCHEMA_HINT, max_steps=max_steps)
        messages = [{"role": "system", "content": sys},
                    {"role": "user", "content": f"Greenhouse: {gh_id}\nQuestion: {question}"}]
        trace, cyphers, tools_used = [], [], []
        for step in range(max_steps):
            # retries=1 keeps the interactive loop snappy — fail over to the
            # question-aware deterministic plan fast if the free model is down.
            raw = chat(self.settings, messages, temperature=0.2, max_tokens=500, retries=1)
            move = _extract_json(raw)
            if not move:
                break
            if move.get("final_answer"):
                return {"question": question, "answer": move["final_answer"], "trace": trace,
                        "mode": "live", "tools_used": tools_used, "cyphers": cyphers}
            tool, args = move.get("tool"), move.get("args") or {}
            if tool not in gt.TOOLS:
                messages.append({"role": "user", "content": f"Observation: no such tool '{tool}'. "
                                 f"Choose from: {', '.join(gt.TOOLS)}."})
                continue
            res = gt.run_tool(tool, store, self.settings, gh_id, **args)
            tools_used.append(tool)
            if res.get("cypher"):
                cyphers.append(res["cypher"])
            trace.append({"step": step + 1, "thought": move.get("thought", ""), "tool": tool,
                          "args": args, "observation": res["observation"], "cypher": res.get("cypher")})
            messages.append({"role": "assistant", "content": json.dumps(move)})
            messages.append({"role": "user", "content": f"Observation: {res['observation']}"})
        # ran out of steps -> synthesize from what we have
        if trace:
            ans = self._synthesize(question, trace)
            return {"question": question, "answer": ans, "trace": trace, "mode": "live",
                    "tools_used": tools_used, "cyphers": cyphers}
        return None

    # ---- deterministic plan (no LLM) — still QUESTION-AWARE tool selection -
    def _fallback(self, store, gh_id, question) -> dict:
        q = (question or "").lower()
        named = gt._resolve_target(q)        # did the user name a disease/pest?
        plan = []
        if any(w in q for w in ("whitefly", "virus", "vector", "tylcv", "transmit", "spread")):
            plan.append(("pest_vector_risk", {}, "The question is about a vector/virus — check pest→disease links."))
        if named:
            disp = gt.kg._node(named[0], named[1])["name"]
            plan.append(("knowledge_lookup", {"name": disp}, f"The user named {disp} — look it up."))
            plan.append(("treatments_for", {"target": disp}, f"List the ranked controls for {disp}."))
        if any(w in q for w in ("why", "alert", "warned", "warning", "fired")):
            plan.append(("explain_latest_alert", {}, "The user asks why they were warned — trace the alert."))
        if not plan or any(w in q for w in ("risk", "wrong", "should i do", "treat", "spray", "control", "now")):
            # default diagnostic path
            plan.insert(0, ("diagnose_conditions", {}, "Diagnose likely disease from current sensor conditions."))
            if not named:
                plan.append(("explain_latest_alert", {}, "Confirm against the latest fired alert."))

        trace, tools_used = [], []
        alert_disease, cond_disease = None, None
        seen = set()
        for tool, args, thought in plan:
            key = (tool, tuple(sorted(args.items())))
            if key in seen:
                continue
            seen.add(key)
            res = gt.run_tool(tool, store, self.settings, gh_id, **args)
            tools_used.append(tool)
            trace.append({"step": len(trace) + 1, "thought": thought, "tool": tool, "args": args,
                          "observation": res["observation"], "cypher": res.get("cypher")})
            data = res.get("data") or {}
            if tool == "explain_latest_alert" and isinstance(data, dict):
                alert_disease = (data.get("disease") or {}).get("name")   # the CONFIRMED fired alert
            if tool == "diagnose_conditions" and data.get("diseases"):
                cond_disease = data["diseases"][0]["name"]
        disease = alert_disease or cond_disease   # prefer the confirmed alert over a conditions guess
        # if we diagnosed but never fetched controls for it, do so
        if disease and not any(t["tool"] == "treatments_for" for t in trace):
            res = gt.run_tool("treatments_for", store, self.settings, gh_id, target=disease)
            tools_used.append("treatments_for")
            trace.append({"step": len(trace) + 1, "thought": f"Get ranked controls for {disease}.",
                          "tool": "treatments_for", "args": {"target": disease},
                          "observation": res["observation"], "cypher": None})
        return {"question": question, "answer": self._synthesize(question, trace), "trace": trace,
                "mode": "mock", "tools_used": tools_used, "cyphers": []}

    @staticmethod
    def _synthesize(question: str, trace: list[dict]) -> str:
        if not trace:
            return "No graph evidence was available to answer this."
        bits = [t["observation"] for t in trace if t.get("observation")]
        return (" ".join(bits) + " — start with the cheapest/cultural controls and have a field "
                "officer confirm before spraying.")
