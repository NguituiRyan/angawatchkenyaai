"""Sokosumi marketplace integration (+10 bonus).

Sokosumi (https://www.sokosumi.com) is the marketplace on top of Masumi where businesses
DISCOVER and HIRE AI agent "coworkers". With SOKOSUMI_API_KEY set we make a REAL, live
call to the Sokosumi API (`GET /v1/agents`) to discover the agents on the marketplace —
an agent-discovery demo, the "strong" Sokosumi evidence — and we publish the Angawatch
Crop-Health Advisory Agent's coworker profile + the listing plan. No key -> a clearly
LABELED mock.  Run:  python -m masumi_integration.sokosumi
"""
from __future__ import annotations

from config import get_settings
from logging_setup import get_logger, tag

log = get_logger("sokosumi")

# Listing OUR coworker requires a Masumi DID + the Sokosumi listing form; the LIVE proof
# here is the working marketplace discovery call (the key authenticates end-to-end).
LISTING_PLAN = [
    "Register the agent on the Masumi registry -> W3C DID / identity NFT (MIP-002).",
    "Deploy the MIP-003 service (api/main.py -> /mip003/*) at a public URL.",
    "Submit the Sokosumi listing form (https://tally.so/r/nPLBaV) with the DID + endpoint.",
    "The coworker then appears on app.sokosumi.com for co-ops to discover, hire and pay.",
]


def build_coworker_profile(settings) -> dict:
    return {
        "name": "Angawatch Crop-Health Advisory Agent",
        "description": "Graph-grounded greenhouse crop-health advisory for tomato: triages "
                       "farms at risk, diagnoses the disease by traversing an agronomic "
                       "knowledge graph, and returns a ranked, PHI-aware treatment plan. "
                       "Hired by cooperatives/off-takers; an agronomist approves.",
        "endpoint": settings.AGENT_API_URL,
        "agent_identifier": settings.AGENT_IDENTIFIER or "<register-on-masumi>",
        "network": settings.NETWORK,
        "input_schema": {"greenhouse_id": {"type": "string", "example": "gh-001"},
                         "requested_by": {"type": "string", "example": "Rift Valley Fresh Co-op"}},
        "output_schema": {
            "diagnosis": {"type": "string"}, "pathogen": {"type": "string"},
            "risk_level": {"type": "string"}, "priority": {"type": "string"},
            "recommended_actions": {"type": "array"}, "confidence": {"type": "string"},
            "result_hash": {"type": "string"},
        },
        "price": {"amount": settings.PAYMENT_AMOUNT, "unit": settings.PAYMENT_UNIT},
        "tags": ["agriculture", "crop-health", "advisory", "kenya", "graphrag",
                 "human-in-the-loop"],
    }


def list_marketplace_agents(settings) -> list[dict]:
    """LIVE: discover the agents currently listed on the Sokosumi marketplace
    (GET /v1/agents). Proves the integration end-to-end. Raises on transport/auth error."""
    import requests
    base = settings.SOKOSUMI_API_URL.rstrip("/")
    resp = requests.get(
        f"{base}/v1/agents",
        headers={"Authorization": f"Bearer {settings.SOKOSUMI_API_KEY}", "Accept": "application/json"},
        timeout=20)
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("data", data if isinstance(data, list) else [])
    out = []
    for a in rows:
        author = a.get("author")
        out.append({
            "id": a.get("id"), "name": a.get("name"), "credits": a.get("credits"),
            "summary": (a.get("summary") or a.get("description") or "")[:140],
            "author": author.get("name") if isinstance(author, dict) else author,
            "categories": a.get("categories") or [],
        })
    return out


def sokosumi_status(settings=None) -> dict:
    """{mode, marketplace_count, marketplace[], profile, listing_plan} — live or labeled mock."""
    settings = settings or get_settings()
    profile = build_coworker_profile(settings)
    if settings.sokosumi_mode() == "live":
        try:
            agents = list_marketplace_agents(settings)
            log.info("%s Sokosumi marketplace: %d agents discoverable", tag("live"), len(agents))
            return {"mode": "live", "marketplace_count": len(agents), "marketplace": agents,
                    "profile": profile, "listing_plan": LISTING_PLAN}
        except Exception as exc:  # noqa: BLE001
            log.warning("%s Sokosumi API failed (%s) -> mock", tag("mock"), exc)
    return {"mode": "mock", "marketplace_count": 0, "marketplace": [],
            "profile": profile, "listing_plan": LISTING_PLAN}


# backwards-compatible alias
def register_coworker(settings=None) -> dict:
    return sokosumi_status(settings)


def main() -> None:
    import json
    r = sokosumi_status()
    print(f"\nSokosumi marketplace  —  {tag(r['mode'])} {r['mode']}")
    if r["mode"] == "live":
        print(f"Connected: {r['marketplace_count']} agent coworkers discoverable on the marketplace.\n")
        for a in r["marketplace"][:8]:
            cred = f"{a['credits']} credits" if a.get("credits") is not None else "—"
            print(f"  • {a['name']:<34} {cred:<14} {a.get('author') or ''}")
    else:
        print("(labeled mock — set SOKOSUMI_API_KEY for the live discovery call)\n")
    print("\nOur coworker profile (to list):")
    print(json.dumps(r["profile"], indent=2))
    print("\nTo list our agent on the marketplace:")
    for i, s in enumerate(r["listing_plan"], 1):
        print(f"  {i}. {s}")
    print()


if __name__ == "__main__":
    main()
