"""The Credit-Risk Agent.

Pipeline: read the farmer's subgraph (GraphRAG) -> DETERMINISTIC 7-factor score
-> grounded narration (CrewAI if available, else OpenRouter, else template) ->
write an audit record. The agent RECOMMENDS; a loan officer approves.
"""
from __future__ import annotations

from datetime import datetime

from agents.llm import build_crewai_llm, narrate
from agents.neo4j_tool import build_subgraph_tool
from logging_setup import get_logger, tag
from scoring.scorer import CreditScorer

log = get_logger("agents.credit")

DEFAULT_LENDER = {"id": "lender-1", "name": "Unaitas SACCO", "type": "SACCO"}


class CreditRiskAgent:
    role = "Agricultural Credit-Risk Analyst"

    def __init__(self, settings) -> None:
        self.settings = settings
        self.scorer = CreditScorer()

    def assess(self, store, farmer_id: str, lender: dict | None = None,
               write_audit: bool = True) -> "CreditAssessment":  # noqa: F821
        lender = lender or DEFAULT_LENDER
        subgraph = store.get_farmer_subgraph(farmer_id)
        assessment = self.scorer.score(subgraph)

        narrative, mode = None, None
        if self.settings.llm_mode() == "live":
            narrative = self._crewai_narrate(assessment, subgraph, store)
            if narrative:
                mode = "live"
                log.info("%s narration via CrewAI", tag("live"))
        if narrative is None:
            narrative, mode = narrate(assessment, subgraph, self.settings)
            log.info("%s narration via %s", tag(mode),
                     "OpenRouter" if mode == "live" else "deterministic template")

        assessment.narrative = narrative
        assessment.mode["narration"] = mode

        if write_audit:
            self._write_audit(store, farmer_id, lender, assessment)
        return assessment

    # --- CrewAI path (best-effort; falls back cleanly) ---------------------
    def _crewai_narrate(self, assessment, subgraph, store) -> str | None:
        try:
            from crewai import Agent, Crew, Task
        except Exception:  # noqa: BLE001
            return None
        llm = build_crewai_llm(self.settings)
        tool = build_subgraph_tool(store)
        if not llm or not tool:
            return None
        try:
            from agents.llm import _facts
            agent = Agent(
                role=self.role,
                goal="Explain a smallholder farmer's credit-risk score to a SACCO loan officer, "
                     "grounded strictly in the farmer's own farm record.",
                backstory="You translate verified farm-and-sensor history into clear, fair, "
                          "explainable credit recommendations. You never invent numbers and you "
                          "always state that a human approves the final decision.",
                tools=[tool], llm=llm, verbose=False, allow_delegation=False,
            )
            task = Task(
                description=(
                    f"Use the FarmerSubgraph tool with farmer_id='{assessment.farmer_id}' to "
                    "ground your explanation. Then, using ONLY these pre-computed figures "
                    "(do not change any number), write 4-6 sentences explaining the score, the "
                    "two strongest factors, the main watch-out, and a one-line recommendation. "
                    "State explicitly that this supports a loan officer and is not a final "
                    f"decision.\n\nFIGURES:\n{_facts(assessment, subgraph)}"
                ),
                expected_output="A 4-6 sentence grounded credit explanation.",
                agent=agent,
            )
            result = Crew(agents=[agent], tasks=[task], verbose=False).kickoff()
            return str(result).strip()
        except Exception as exc:  # noqa: BLE001
            log.warning("CrewAI crew failed (%s) — falling back", exc)
            return None

    # --- audit -------------------------------------------------------------
    def _write_audit(self, store, farmer_id, lender, assessment) -> str:
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "stage": "assessment",
            "requester": lender.get("name"),
            "score": assessment.overall_score,
            "band": assessment.credit["grade"],
            "result_hash": assessment.result_hash,
            "narration_mode": assessment.mode["narration"],
            "masumi_mode": "pending",     # Module 5 records the on-chain proof
            "tx_hash": None, "explorer_url": None,
        }
        audit_id = store.add_audit_record(farmer_id, lender, record)
        log.info("Audit record %s written (score=%s band=%s hash=%s)",
                 audit_id, assessment.overall_score, assessment.credit["grade"],
                 assessment.result_hash[:12])
        return audit_id
