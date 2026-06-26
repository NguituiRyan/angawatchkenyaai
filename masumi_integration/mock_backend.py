"""Deterministic, clearly-LABELED Masumi mock.

Walks the SAME five lifecycle stages as the real backend so the demo narrative is
identical except for the badge. Honest about being fake: simulated tx hashes are
prefixed 'MOCK-' and carry no explorer link. HYBRID: if MASUMI_PRERECORDED_TX is
set (a real preprod tx captured beforehand), the audit shows that real tx + a real
cardanoscan link, labeled 'prerecorded-real'.
"""
from __future__ import annotations

import hashlib

from masumi_integration.client import MasumiBackend
from masumi_integration.models import (AgentProfile, AuditRecord, EscrowResult,
                                       Registration, ServiceRequest, SubmitResult)

PREPROD_EXPLORER = "https://preprod.cardanoscan.io/transaction/"


def _h(s: str, n: int = 56) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:n]


class MockMasumiBackend(MasumiBackend):
    mode = "mock"

    def __init__(self, settings) -> None:
        self.settings = settings
        self.prerecorded = (settings.MASUMI_PRERECORDED_TX or "").strip() or None

    def _proof(self, seed: str) -> tuple[str, str | None, str]:
        """(tx_hash, explorer_url, proof_kind)."""
        if self.prerecorded:
            return self.prerecorded, PREPROD_EXPLORER + self.prerecorded, "prerecorded-real"
        return "MOCK-" + _h(seed), None, "simulated"

    def register_agent(self, profile: AgentProfile) -> Registration:
        agent_id = self.settings.AGENT_IDENTIFIER or f"agent_angawatch_{_h(profile.name, 16)}"
        did = "did:masumi:preprod:" + _h(profile.name, 24)
        tx, url, kind = self._proof("register:" + profile.name)
        return Registration(agent_identifier=agent_id, did=did, tx_hash=tx,
                            explorer_url=url, mode="mock", proof_kind=kind)

    def request_service(self, agent_identifier, input_data, identifier_from_purchaser):
        seed = agent_identifier + identifier_from_purchaser + str(input_data.get("result_hash", ""))
        return ServiceRequest(
            job_id="job_" + _h(seed, 16),
            blockchain_identifier=_h("bid:" + seed, 40),
            amount=self.settings.PAYMENT_AMOUNT, unit=self.settings.PAYMENT_UNIT,
            input_data=input_data, mode="mock",
        )

    def pay_escrow(self, request: ServiceRequest) -> EscrowResult:
        tx, url, kind = self._proof("escrow:" + request.blockchain_identifier)
        return EscrowResult(paid=True, tx_hash=tx, explorer_url=url,
                            amount=request.amount, unit=request.unit,
                            status="locked→released", mode="mock", proof_kind=kind)

    def submit_result(self, request: ServiceRequest, result_hash: str) -> SubmitResult:
        tx, url, kind = self._proof("submit:" + result_hash)
        return SubmitResult(result_hash=result_hash, tx_hash=tx, explorer_url=url,
                            status="submitted", mode="mock", proof_kind=kind)

    def get_audit_record(self, request, result_hash, requester) -> AuditRecord:
        tx, url, kind = self._proof("audit:" + request.blockchain_identifier + result_hash)
        status = "verified (prerecorded on-chain)" if self.prerecorded else "verified (simulated)"
        return AuditRecord(
            request_id=request.job_id, agent_identifier=self.settings.AGENT_IDENTIFIER
            or "agent_angawatch_mock", result_hash=result_hash, tx_hash=tx,
            explorer_url=url, amount=request.amount, unit=request.unit, status=status,
            mode="mock", proof_kind=kind, requester=requester,
        )
