"""Sokosumi coworker registration (stretch, +10 bonus).

Sokosumi is the marketplace on top of Masumi where businesses discover & hire AI
agent "coworkers". This builds the coworker profile for the Angawatch Credit-Risk
Agent and registers it — REAL against the preprod API when SOKOSUMI_API_KEY is
set, otherwise a clearly-LABELED mock that prints the exact payload + manual steps
(app.sokosumi.com). Run:  python -m masumi_integration.sokosumi
"""
from __future__ import annotations

from config import get_settings
from logging_setup import get_logger, tag

log = get_logger("sokosumi")

MANUAL_STEPS = [
    "Deploy the MIP-003 service (api/main.py -> /mip003/*) at a public URL.",
    "Register the agent on Masumi preprod (explorer.masumi.network/?network=preprod) -> DID.",
    "Sign in at app.sokosumi.com, create an organization, 'Add agent'.",
    "Paste the endpoint, input/output schema and price below; Sokosumi syncs from the Masumi registry.",
]


def build_coworker_profile(settings) -> dict:
    return {
        "name": "Angawatch Credit-Risk Agent",
        "description": "Explainable, multi-factor agri-credit scoring for smallholder tomato "
                       "farmers, grounded in a verified Neo4j farm record. Recommends; a loan "
                       "officer approves.",
        "endpoint": settings.AGENT_API_URL,
        "agent_identifier": settings.AGENT_IDENTIFIER or "<register-on-masumi-preprod>",
        "network": settings.NETWORK,
        "input_schema": {"farmer_id": {"type": "string", "example": "Farmer-A"}},
        "output_schema": {
            "overall_score": {"type": "number"},
            "credit_band": {"type": "string"},
            "insurance_band": {"type": "string"},
            "confidence": {"type": "string"},
            "factors": {"type": "array"},
            "result_hash": {"type": "string"},
        },
        "price": {"amount": settings.PAYMENT_AMOUNT, "unit": settings.PAYMENT_UNIT},
        "tags": ["agri-finance", "credit-scoring", "kenya", "explainable", "human-in-the-loop"],
    }


def register_coworker(settings=None) -> dict:
    settings = settings or get_settings()
    profile = build_coworker_profile(settings)
    if settings.sokosumi_mode() == "live":
        try:
            import requests
            resp = requests.post(
                f"{settings.SOKOSUMI_API_URL.rstrip('/')}/agents",
                headers={"Authorization": f"Bearer {settings.SOKOSUMI_API_KEY}"},
                json=profile, timeout=20,
            )
            resp.raise_for_status()
            log.info("%s registered on Sokosumi preprod", tag("live"))
            return {"mode": "live", "status": "registered", "response": resp.json(),
                    "profile": profile}
        except Exception as exc:  # noqa: BLE001
            log.warning("%s Sokosumi API failed (%s) -> mock", tag("mock"), exc)
    return {"mode": "mock", "status": "prepared (labeled mock — no SOKOSUMI_API_KEY)",
            "profile": profile, "manual_steps": MANUAL_STEPS}


def main() -> None:
    import json
    result = register_coworker()
    print(f"\nSokosumi coworker registration  —  {tag(result['mode'])} {result['mode']}")
    print(f"Status: {result['status']}\n")
    print("Coworker profile:")
    print(json.dumps(result["profile"], indent=2))
    if result.get("manual_steps"):
        print("\nTo go live (real):")
        for i, s in enumerate(result["manual_steps"], 1):
            print(f"  {i}. {s}")
    print()


if __name__ == "__main__":
    main()
