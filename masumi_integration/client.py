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
            name="Angawatch Crop-Health Advisory Agent",
            api_url="https://angawatch.example/mip003",
            description="Graph-grounded greenhouse crop-health advisory for tomato: "
                        "triages farms at risk, diagnoses the disease by traversing an "
                        "agronomic knowledge graph, and returns a ranked, PHI-aware "
                        "treatment plan. Hired by cooperatives/off-takers; an agronomist approves.",
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

    def run_round_trip(self, report, store=None, requester: dict | None = None) -> dict:
        """Co-op discovers -> pays escrow -> agent delivers the advisory -> on-chain audit.

        `report` is an AdvisoryReport; its result_hash commits to the diagnosis + plan.
        Returns {steps, audit, registration} for the dashboard stepper.
        """
        requester = requester or {"id": "coop-1", "name": "Rift Valley Fresh Co-op",
                                  "type": "cooperative"}
        reg = self.registration()
        purchaser_id = hashlib.sha256(
            f"{requester['id']}:{report.greenhouse_id}".encode()).hexdigest()[:32]
        req = self.backend.request_service(
            reg.agent_identifier,
            input_data={"greenhouse_id": report.greenhouse_id,
                        "result_hash": report.result_hash},
            identifier_from_purchaser=purchaser_id,
        )
        escrow = self.backend.pay_escrow(req)
        submit = self.backend.submit_result(req, report.result_hash)
        audit = self.backend.get_audit_record(req, report.result_hash,
                                              requester=requester.get("name"))

        if store is not None and getattr(report, "farm_id", None):
            try:
                rec = audit.to_props()
                rec.update({"diagnosis": report.diagnosis, "priority": report.priority,
                            "greenhouse_id": report.greenhouse_id,
                            "masumi_mode": audit.mode, "stage": "masumi_audit"})
                store.add_audit_record(report.farm_id, requester, rec)
            except Exception as exc:  # noqa: BLE001  (graph write must never break the trip)
                log.warning("audit graph-write skipped: %s", exc)

        steps = [
            _step("1. Identity / registration", reg.mode, reg.proof_kind,
                  f"DID {reg.did}", reg.tx_hash, reg.explorer_url),
            _step("2. Co-op discovers & hires the agent", req.mode, "—",
                  f"job {req.job_id} · {req.amount} {req.unit}", None, None),
            _step("3. Escrow payment (USDM/ADA)", escrow.mode, escrow.proof_kind,
                  f"{escrow.status} · {escrow.amount} {escrow.unit}",
                  escrow.tx_hash, escrow.explorer_url),
            _step("4. Deliver advisory + Decision-Log hash", submit.mode, submit.proof_kind,
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
