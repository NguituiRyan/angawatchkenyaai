"""HTTP ingest endpoint — the clean contract a real ESP32 feed will POST to.

POST /ingest with a sensor reading -> stores it, runs the risk engine, and (if a
rule fires) dispatches the alert. Returns the reading id and any alert. The same
Services.ingest() pipeline backs the simulator, this endpoint and the dashboard.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ReadingIn(BaseModel):
    greenhouse_id: str = Field(..., examples=["gh-001"])
    ts: str | None = None
    temp_c: float
    humidity: float
    leaf_wetness_hr: float = 0.0
    soil_vwc: float = 0.35
    trap_count: int = 0
    source: str = "esp32"


def create_ingest_router(services):
    from datetime import datetime

    from fastapi import APIRouter

    router = APIRouter()

    @router.post("/ingest")
    def ingest(reading: ReadingIn) -> dict:
        data = reading.model_dump()
        if not data.get("ts"):
            data["ts"] = datetime.now().isoformat()
        return services.ingest(data, gh_id=data["greenhouse_id"])

    return router
