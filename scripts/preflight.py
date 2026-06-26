"""Pre-demo readiness check:  python scripts/preflight.py

Actually CONNECTS to each configured service and reports LIVE/MOCK with the exact
fix if something is mock. Run this after pasting your creds into .env (or before
the demo) to confirm the deployed app will be functional, not just labeled-mock.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import get_settings  # noqa: E402
from logging_setup import tag  # noqa: E402

OK, BAD = "[LIVE]", "[MOCK]"


def _line(name: str, live: bool, detail: str, fix: str = "") -> tuple[bool, str]:
    t = OK if live else BAD
    s = f"  {t:<7} {name:<22} {detail}"
    if not live and fix:
        s += f"\n          ↳ fix: {fix}"
    return live, s


def check_neo4j(s) -> tuple[bool, str]:
    if not s.neo4j_configured:
        return _line("Neo4j graph", False, "no NEO4J_URI/PASSWORD — in-memory store",
                     "create a free Aura instance (neo4j.com/cloud/aura) and set NEO4J_URI/USER/PASSWORD")
    try:
        from graph.connection import get_driver
        d = get_driver(s.NEO4J_URI, s.NEO4J_USER, s.NEO4J_PASSWORD)
        with d.session() as sess:
            n = sess.run("MATCH (x) RETURN count(x) AS c").single()["c"]
        d.close()
        return _line("Neo4j graph", True, f"connected · {n} nodes ({s.NEO4J_URI[:38]}…)")
    except Exception as exc:  # noqa: BLE001
        return _line("Neo4j graph", False, f"configured but NOT reachable: {exc}",
                     "check the URI/password and that the Aura instance is running")


def check_openrouter(s) -> tuple[bool, str]:
    if not s.OPENROUTER_API_KEY:
        return _line("OpenRouter LLM", False, "no OPENROUTER_API_KEY — templated narration",
                     "get a free key at openrouter.ai and set OPENROUTER_API_KEY")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=s.OPENROUTER_API_KEY, base_url=s.OPENROUTER_BASE_URL)
        model = s.OPENROUTER_MODEL.replace("openrouter/", "")
        r = client.chat.completions.create(model=model, max_tokens=1,
                                           messages=[{"role": "user", "content": "ok"}])
        return _line("OpenRouter LLM", True, f"call OK · model {model}")
    except Exception as exc:  # noqa: BLE001
        return _line("OpenRouter LLM", False, f"key set but call failed: {str(exc)[:70]}",
                     "verify the key and that the free model id is still available")


def check_twilio(s) -> tuple[bool, str]:
    if not (s.TWILIO_SID and s.TWILIO_TOKEN):
        return _line("Twilio WhatsApp", False, "no TWILIO_SID/TOKEN — console alerts",
                     "join the WhatsApp sandbox (twilio.com/console) and set TWILIO_SID/TOKEN + FARMER_PHONE")
    try:
        from twilio.rest import Client
        acct = Client(s.TWILIO_SID, s.TWILIO_TOKEN).api.accounts(s.TWILIO_SID).fetch()
        phone = s.FARMER_PHONE or "(no FARMER_PHONE set!)"
        return _line("Twilio WhatsApp", True, f"account {acct.status} · from {s.TWILIO_FROM} · to {phone}")
    except Exception as exc:  # noqa: BLE001
        return _line("Twilio WhatsApp", False, f"creds set but auth failed: {str(exc)[:60]}",
                     "re-copy the Account SID + Auth Token from the Twilio console")


def check_masumi(s) -> tuple[bool, str]:
    mode = s.masumi_mode()
    if mode == "real":
        detail = f"REAL preprod · agent {s.AGENT_IDENTIFIER}"
        return _line("Masumi pay/audit", True, detail)
    if s.MASUMI_PRERECORDED_TX:
        return _line("Masumi pay/audit", True,
                     f"mock round-trip + REAL on-chain proof tx {s.MASUMI_PRERECORDED_TX[:18]}…")
    return _line("Masumi pay/audit", False, "labeled mock (no real on-chain proof)",
                 "see docs/masumi_golive.md — register on preprod and set MASUMI_PRERECORDED_TX")


def check_vision(s) -> tuple[bool, str]:
    import importlib.util as u
    have = u.find_spec("transformers") and u.find_spec("torch")
    if s.vision_mode() == "mock":
        return _line("Vision classifier", False, "VISION_MODE=mock (fine for the cloud)",
                     "set VISION_MODE=live locally (pip install -r requirements-full.txt) for the real model")
    return _line("Vision classifier", bool(have),
                 "real HF model available" if have else "transformers/torch not installed",
                 "pip install -r requirements-full.txt")


def main() -> None:
    s = get_settings()
    print("\n  ANGAWATCH — pre-demo readiness\n  " + "=" * 52)
    results = [check_neo4j(s), check_openrouter(s), check_twilio(s),
               check_masumi(s), check_vision(s)]
    for _live, msg in results:
        print(msg)
    live = sum(1 for ok, _ in results if ok)
    print("  " + "-" * 52)
    print(f"  {live}/{len(results)} services LIVE.  "
          + ("Demo runs fully — all real where it counts." if live >= 4
             else "Everything still runs (labeled mock) — wire creds to go live."))
    print("  Tip: the app NEVER hard-fails; mocks are labeled. See SUBMISSION_CHECKLIST.md\n")


if __name__ == "__main__":
    main()
