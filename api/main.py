"""FastAPI app:  uvicorn api.main:app --reload

Mounts the ESP32 ingest endpoint and a health check. The MIP-003 agentic-service
router is mounted in Module 5.
"""
from __future__ import annotations


def create_app():
    from fastapi import FastAPI

    from services import build_services
    from sim.ingest_api import create_ingest_router

    services = build_services()
    app = FastAPI(title="Angawatch API", version="0.2")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True, "graph": services.store.mode,
                "alerts": services.channel.mode}

    app.include_router(create_ingest_router(services))

    from masumi_integration.service import create_mip003_router
    app.include_router(create_mip003_router(services))
    return app


app = create_app()
