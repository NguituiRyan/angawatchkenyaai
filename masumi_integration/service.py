"""MIP-003 agentic-service endpoints — makes the Credit-Risk Agent a genuine,
discoverable Masumi service (mounted by api/main.py).

Endpoints (MIP-003): GET /availability, GET /input_schema, POST /start_job,
GET /status, POST /provide_input, GET /demo. The job's work is the deterministic
credit assessment; its result_hash is what Masumi Decision-Logs on-chain.
"""
from __future__ import annotations


def create_mip003_router(services):
    from fastapi import APIRouter
    from pydantic import BaseModel

    from agents.credit_crew import CreditRiskAgent

    router = APIRouter(prefix="/mip003", tags=["masumi"])
    agent = CreditRiskAgent(services.settings)
    jobs: dict[str, dict] = {}

    class StartJob(BaseModel):
        identifier_from_purchaser: str
        input_data: dict           # {"farmer_id": "Farmer-A"}

    class ProvideInput(BaseModel):
        job_id: str
        input_data: dict

    @router.get("/availability")
    def availability() -> dict:
        return {"available": True, "agent": "Angawatch Credit-Risk Agent",
                "status": "operational"}

    @router.get("/input_schema")
    def input_schema() -> dict:
        return {"input_data": {"farmer_id": {"type": "string",
                "description": "Farmer id to assess, e.g. Farmer-A"}}}

    @router.post("/start_job")
    def start_job(body: StartJob) -> dict:
        farmer_id = body.input_data.get("farmer_id", services.settings.DEFAULT_FARMER_ID)
        assessment = agent.assess(services.store, farmer_id)
        job_id = "job_" + body.identifier_from_purchaser[:16]
        jobs[job_id] = {"status": "completed", "result": assessment.to_dict()}
        return {"job_id": job_id, "status": "completed",
                "result_hash": assessment.result_hash,
                "blockchainIdentifier": body.identifier_from_purchaser}

    @router.get("/status")
    def status(job_id: str) -> dict:
        return jobs.get(job_id, {"status": "unknown", "result": None})

    @router.post("/provide_input")
    def provide_input(body: ProvideInput) -> dict:
        return {"status": "accepted", "job_id": body.job_id}

    @router.get("/demo")
    def demo() -> dict:
        a = agent.assess(services.store, services.settings.DEFAULT_FARMER_ID, write_audit=False)
        return {"example": a.to_dict()}

    return router
