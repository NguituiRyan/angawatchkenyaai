"""Masumi flow data models (shared by the real + mock backends)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class AgentProfile:
    name: str
    api_url: str
    description: str
    selling_vkey: str | None = None
    price_amount: str = "5000000"
    price_unit: str = "lovelace"


@dataclass
class Registration:
    agent_identifier: str
    did: str
    tx_hash: str | None
    explorer_url: str | None
    mode: str                       # live | mock
    proof_kind: str = "simulated"   # real | prerecorded-real | simulated


@dataclass
class ServiceRequest:
    job_id: str
    blockchain_identifier: str
    amount: str
    unit: str
    input_data: dict = field(default_factory=dict)
    pay_by_time: str | None = None
    submit_result_time: str | None = None
    unlock_time: str | None = None
    mode: str = "mock"


@dataclass
class EscrowResult:
    paid: bool
    tx_hash: str | None
    explorer_url: str | None
    amount: str
    unit: str
    status: str                     # locked | confirmed | failed
    mode: str = "mock"
    proof_kind: str = "simulated"


@dataclass
class SubmitResult:
    result_hash: str
    tx_hash: str | None
    explorer_url: str | None
    status: str                     # submitted | confirmed
    mode: str = "mock"
    proof_kind: str = "simulated"


@dataclass
class AuditRecord:
    request_id: str
    agent_identifier: str
    result_hash: str
    tx_hash: str | None
    explorer_url: str | None
    amount: str
    unit: str
    status: str
    mode: str = "mock"
    proof_kind: str = "simulated"
    requester: str | None = None

    def to_props(self) -> dict:
        return asdict(self)
