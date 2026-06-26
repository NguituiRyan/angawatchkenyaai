"""MasumiClient facade + backend ABC + factory + the 5-stage round-trip.

The dashboard and CLI only touch MasumiClient; they cannot tell which backend is
live. build_masumi_client() picks real vs mock and AUTO-DOWNGRADES real->mock on
any error, so the live demo can never hard-fail.
"""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

from logging_setup import get_logger, tag
from masumi_integration.models import (AgentProfile, AuditRecord, EscrowResult,
                                       Registration, ServiceRequest, SubmitResult)

log = get_logger("masumi.client")


class MasumiBackend(ABC):
    mode: str = "mock"

    @abstractmethod
    def register_agent(self, profile: AgentProfile) -> Registration: ...
    @abstractmethod
    def request_service(self, agent_identifier: str, input_data: dict,
                        identifier_from_purchaser: str) -> ServiceRequest: ...
    @abstractmethod
    def pay_escrow(self, request: ServiceRequest) -> EscrowResult: ...
    @abstractmethod
    def submit_result(self, request: ServiceRequest, result_hash: str) -> SubmitResult: ...
    @abstractmethod
    def get_audit_record(self, request: ServiceRequest, result_hash: str,
                         requester: str | None) -> AuditRecord: ...


class MasumiClient:
    def __init__(self, backend: MasumiBackend, settings) -> None:
        self.backend = backend
        self.settings = settings
        self._registration: Registration | None = None

    @property
    def mode(self) -> str:
        return self.backend.mode

    def _profile(self) -> AgentProfile:
        return AgentProfile(
            name="Angawatch Credit-Risk Agent",
            api_url="https://angawatch.example/mip003",
            description="Explainable, multi-factor smallholder agri-credit scoring "
                        "grounded in a verified Neo4j farm record. Recommends; a loan "
                        "officer approves.",
            selling_vkey=self.settings.SELLER_VKEY,
            price_amount=self.settings.PAYMENT_AMOUNT,
            price_unit=self.settings.PAYMENT_UNIT,
        )

    def registration(self) -> Registration:
        if self._registration is None:
            self._registration = self.backend.register_agent(self._profile())
            log.info("%s agent registered: %s", tag(self._registration.mode),
                     self._registration.agent_identifier)
        return self._registration

    def run_round_trip(self, assessment, store=None, lender: dict | None = None) -> dict:
        """Lender discovers -> pays escrow -> agent delivers -> on-chain audit.

        Returns {steps, audit, registration} for the dashboard stepper.
        """
        lender = lender or {"id": "lender-1", "name": "Unaitas SACCO", "type": "SACCO"}
        reg = self.registration()
        purchaser_id = hashlib.sha256(
            f"{lender['id']}:{assessment.farmer_id}".encode()).hexdigest()[:32]
        req = self.backend.request_service(
            reg.agent_identifier,
            input_data={"farmer_id": assessment.farmer_id,
                        "result_hash": assessment.result_hash},
            identifier_from_purchaser=purchaser_id,
        )
        escrow = self.backend.pay_escrow(req)
        submit = self.backend.submit_result(req, assessment.result_hash)
        audit = self.backend.get_audit_record(req, assessment.result_hash,
                                              requester=lender.get("name"))

        if store is not None:
            rec = audit.to_props()
            rec.update({"score": assessment.overall_score, "band": assessment.credit["grade"],
                        "masumi_mode": audit.mode, "stage": "masumi_audit"})
            store.add_audit_record(assessment.farmer_id, lender, rec)

        steps = [
            _step("1. Identity / registration", reg.mode, reg.proof_kind,
                  f"DID {reg.did}", reg.tx_hash, reg.explorer_url),
            _step("2. Service request (discover & hire)", req.mode, "—",
                  f"job {req.job_id} · {req.amount} {req.unit}", None, None),
            _step("3. Escrow payment (USDM/ADA)", escrow.mode, escrow.proof_kind,
                  f"{escrow.status} · {escrow.amount} {escrow.unit}",
                  escrow.tx_hash, escrow.explorer_url),
            _step("4. Deliver result + Decision-Log hash", submit.mode, submit.proof_kind,
                  f"result_hash {submit.result_hash[:16]}…", submit.tx_hash, submit.explorer_url),
            _step("5. On-chain audit trail", audit.mode, audit.proof_kind,
                  f"{audit.status}", audit.tx_hash, audit.explorer_url),
        ]
        return {"steps": steps, "audit": audit, "registration": reg}


def _step(label, mode, proof_kind, detail, tx_hash, explorer_url) -> dict:
    return {"label": label, "mode": mode, "proof_kind": proof_kind, "detail": detail,
            "tx_hash": tx_hash, "explorer_url": explorer_url}


def build_masumi_client(settings=None) -> MasumiClient:
    from config import get_settings
    settings = settings or get_settings()
    if settings.masumi_mode() == "real":
        try:
            from masumi_integration.real_backend import RealMasumiBackend
            backend = RealMasumiBackend(settings)
            log.info("%s Masumi backend: REAL preprod", tag("real"))
            return MasumiClient(backend, settings)
        except Exception as exc:  # noqa: BLE001
            log.warning("%s Masumi real backend unavailable (%s) -> MOCK", tag("mock"), exc)
    from masumi_integration.mock_backend import MockMasumiBackend
    log.info("%s Masumi backend: simulated round-trip (labeled mock)", tag("mock"))
    return MasumiClient(MockMasumiBackend(settings), settings)
