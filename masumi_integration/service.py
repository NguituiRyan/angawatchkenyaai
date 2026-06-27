"""MIP-003 agentic-service endpoints — makes the Crop-Health Advisory Agent a genuine,
discoverable Masumi service (mounted by api/main.py).

Endpoints (MIP-003): GET /availability, GET /input_schema, POST /start_job,
GET /status, POST /provide_input, GET /demo. The job's work is the graph-grounded
advisory report; its result_hash (the diagnosis + plan) is what Masumi Decision-Logs.
"""
from __future__ import annotations


def create_mip003_router(services):
    from fastapi import APIRouter
    from pydantic import BaseModel

    from agents.advisory import AdvisoryAgent

    router = APIRouter(prefix="/mip003", tags=["masumi"])
    agent = AdvisoryAgent(services.settings)
    jobs: dict[str, dict] = {}

    class StartJob(BaseModel):
        identifier_from_purchaser: str
        input_data: dict           # {"greenhouse_id": "gh-001", "requested_by": "..."}

    class ProvideInput(BaseModel):
        job_id: str
        input_data: dict

    @router.get("/availability")
    def availability() -> dict:
        return {"available": True, "agent": "Angawatch Crop-Health Advisory Agent",
                "status": "operational"}

    @router.get("/input_schema")
    def input_schema() -> dict:
        return {"input_data": {
            "greenhouse_id": {"type": "string",
                              "description": "Greenhouse id to advise, e.g. gh-001"},
            "requested_by": {"type": "string",
                             "description": "Hiring co-op / off-taker (optional)"}}}

    @router.post("/start_job")
    def start_job(body: StartJob) -> dict:
        gh_id = body.input_data.get("greenhouse_id", services.settings.DEFAULT_GREENHOUSE_ID)
        requested_by = body.input_data.get("requested_by")
        report = agent.report(services.store, gh_id, requested_by=requested_by)
        job_id = "job_" + body.identifier_from_purchaser[:16]
        jobs[job_id] = {"status": "completed", "result": report.to_dict()}
        return {"job_id": job_id, "status": "completed",
                "result_hash": report.result_hash,
                "blockchainIdentifier": body.identifier_from_purchaser}

    @router.get("/status")
    def status(job_id: str) -> dict:
        return jobs.get(job_id, {"status": "unknown", "result": None})

    @router.post("/provide_input")
    def provide_input(body: ProvideInput) -> dict:
        return {"status": "accepted", "job_id": body.job_id}

    @router.get("/demo")
    def demo() -> dict:
        r = agent.report(services.store, services.settings.DEFAULT_GREENHOUSE_ID)
        return {"example": r.to_dict()}

    return router
