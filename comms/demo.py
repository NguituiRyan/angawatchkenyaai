"""Standalone feature-phone demo:  python -m comms.demo

Simulates two-way SMS (bilingual) + the offline alert box, using the REAL risk
engine + Credit-Risk score on the seeded farmer.
"""
from __future__ import annotations

from comms.offline_box import box_for_greenhouse
from comms.sms import handle_inbound
from services import build_services


def _sms(services, fid, text):
    r = handle_inbound(services, fid, text)
    print(f"\n  FARMER texts: \"{text}\"  [{r['lang']}]")
    for line in r["reply"].split("\n"):
        print(f"  ANGAWATCH SMS> {line}")


def main() -> None:
    services = build_services()
    fid = services.settings.DEFAULT_FARMER_ID
    gh = services.settings.DEFAULT_GREENHOUSE_ID

    # stage a blight event so there's something to report
    services.inject(gh, "late_blight", ticks=10)
    for _ in range(8):
        services.tick_and_ingest(gh)

    print("\n== Two-way SMS (feature phone) ==")
    _sms(services, fid, "SW")        # switch to Kiswahili
    _sms(services, fid, "HALI")      # status (Swahili)
    _sms(services, fid, "MKOPO")     # loan (Swahili)
    _sms(services, fid, "EN")        # switch to English
    _sms(services, fid, "STATUS")    # status (English)
    _sms(services, fid, "LOAN")      # loan (English)
    _sms(services, fid, "HELP")

    print("\n== Offline alert box (ESP-NOW, no internet) ==")
    for lang in ("en", "sw"):
        b = box_for_greenhouse(services, gh, lang)
        print(f"\n  [{lang}] LED {b['led']}  buzzer: {b['buzzer']}")
        print(f"  ┌──────────────────────────────┐")
        print(f"  │ {b['line1'][:28]:<28} │")
        print(f"  │ {b['line2'][:28]:<28} │")
        print(f"  └──────────────────────────────┘")
    print()


if __name__ == "__main__":
    main()
