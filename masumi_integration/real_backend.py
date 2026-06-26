"""Real Masumi preprod backend via the `masumi` SDK (pip-masumi).

Faithful to the official crewai-masumi-quickstart-template:
  from masumi.config import Config
  from masumi.payment import Payment, Amount
  payment = Payment(agent_identifier, config, identifier_from_purchaser, input_data, network)
  await payment.create_payment_request()      -> blockchainIdentifier, payByTime, ...
  await payment.check_payment_status()
  await payment.complete_payment(payment_id, result)   # Decision Logging (hash on-chain)

Exercising this end-to-end needs a running/hosted Payment Service and a FUNDED
Cardano preprod wallet. If anything is missing, build_masumi_client() downgrades
to the labeled mock automatically.
"""
from __future__ import annotations

import asyncio

from logging_setup import get_logger
from masumi_integration.client import MasumiBackend
from masumi_integration.mock_backend import PREPROD_EXPLORER, _h
from masumi_integration.models import (AgentProfile, AuditRecord, EscrowResult,
                                       Registration, ServiceRequest, SubmitResult)

log = get_logger("masumi.real")


def _run(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:                       # already-running loop (e.g. Streamlit)
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


class RealMasumiBackend(MasumiBackend):
    mode = "live"

    def __init__(self, settings) -> None:
        from masumi.config import Config        # raises if SDK absent -> factory -> mock
        self.settings = settings
        if not (settings.PAYMENT_SERVICE_URL and settings.PAYMENT_API_KEY
                and settings.AGENT_IDENTIFIER):
            raise RuntimeError("missing PAYMENT_SERVICE_URL / PAYMENT_API_KEY / AGENT_IDENTIFIER")
        self._config = Config(payment_service_url=settings.PAYMENT_SERVICE_URL,
                              payment_api_key=settings.PAYMENT_API_KEY)
        self._payments: dict[str, object] = {}

    def register_agent(self, profile: AgentProfile) -> Registration:
        # Registration is done out-of-band (explorer.masumi.network) the night before;
        # here we surface the configured on-chain identity.
        agent_id = self.settings.AGENT_IDENTIFIER
        return Registration(agent_identifier=agent_id,
                            did="did:masumi:preprod:" + _h(agent_id, 24),
                            tx_hash=None, explorer_url=None, mode="live", proof_kind="real")

    def request_service(self, agent_identifier, input_data, identifier_from_purchaser):
        from masumi.payment import Payment
        payment = Payment(agent_identifier=agent_identifier, config=self._config,
                          identifier_from_purchaser=identifier_from_purchaser,
                          input_data=input_data, network=self.settings.NETWORK)
        resp = _run(payment.create_payment_request())
        data = resp.get("data", resp) if isinstance(resp, dict) else {}
        bid = data.get("blockchainIdentifier", _h("bid:" + identifier_from_purchaser, 40))
        job_id = "job_" + _h(bid, 16)
        self._payments[job_id] = payment
        return ServiceRequest(
            job_id=job_id, blockchain_identifier=bid,
            amount=self.settings.PAYMENT_AMOUNT, unit=self.settings.PAYMENT_UNIT,
            input_data=input_data, pay_by_time=str(data.get("payByTime")),
            submit_result_time=str(data.get("submitResultTime")),
            unlock_time=str(data.get("unlockTime")), mode="live",
        )

    def pay_escrow(self, request: ServiceRequest) -> EscrowResult:
        payment = self._payments.get(request.job_id)
        status = "awaiting"
        try:
            if payment is not None:
                st = _run(payment.check_payment_status())
                status = str((st or {}).get("data", {}).get("status", "locked"))
        except Exception as exc:  # noqa: BLE001
            log.warning("check_payment_status failed: %s", exc)
        url = PREPROD_EXPLORER + request.blockchain_identifier
        return EscrowResult(paid=status not in ("awaiting", "failed"),
                            tx_hash=request.blockchain_identifier, explorer_url=url,
                            amount=request.amount, unit=request.unit, status=status,
                            mode="live", proof_kind="real")

    def submit_result(self, request: ServiceRequest, result_hash: str) -> SubmitResult:
        payment = self._payments.get(request.job_id)
        try:
            if payment is not None:
                _run(payment.complete_payment(request.blockchain_identifier, result_hash))
        except Exception as exc:  # noqa: BLE001
            log.warning("complete_payment failed: %s", exc)
        url = PREPROD_EXPLORER + request.blockchain_identifier
        return SubmitResult(result_hash=result_hash, tx_hash=request.blockchain_identifier,
                            explorer_url=url, status="submitted", mode="live", proof_kind="real")

    def get_audit_record(self, request, result_hash, requester) -> AuditRecord:
        url = PREPROD_EXPLORER + request.blockchain_identifier
        return AuditRecord(request_id=request.job_id,
                           agent_identifier=self.settings.AGENT_IDENTIFIER,
                           result_hash=result_hash, tx_hash=request.blockchain_identifier,
                           explorer_url=url, amount=request.amount, unit=request.unit,
                           status="on-chain (preprod)", mode="live", proof_kind="real",
                           requester=requester)
