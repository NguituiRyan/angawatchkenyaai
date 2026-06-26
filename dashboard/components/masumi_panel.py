"""Render the Masumi round-trip as a 5-step stepper with LIVE/MOCK badges."""
from __future__ import annotations

import streamlit as st

from logging_setup import badge


def render_masumi(trip: dict, client_mode: str) -> None:
    st.markdown(f"**Masumi round-trip** — backend: {badge(client_mode)} `{client_mode}`")
    st.caption("A SACCO discovers the agent, pays escrow (USDM/ADA on Cardano preprod), the "
               "agent delivers, and the result hash is Decision-Logged on-chain for audit.")

    for s in trip["steps"]:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{s['label']}**")
            c1.caption(s["detail"])
            c2.markdown(badge(s["mode"]))
            if s["proof_kind"] and s["proof_kind"] not in ("—", "simulated"):
                c2.caption(s["proof_kind"])
            if s["tx_hash"]:
                if s["explorer_url"]:
                    c1.markdown(f"tx [`{s['tx_hash'][:28]}…`]({s['explorer_url']}) "
                                f"↗ cardano preprod")
                else:
                    c1.caption(f"tx `{s['tx_hash'][:28]}…` (simulated — no on-chain link)")

    audit = trip["audit"]
    if audit.explorer_url:
        st.success(f"On-chain audit available ({audit.proof_kind}): "
                   f"[view transaction]({audit.explorer_url}) ↗")
    else:
        st.warning("Audit is a labeled simulation (no funded preprod wallet). Set "
                   "`MASUMI_PRERECORDED_TX` or `MASUMI_MODE=real` for a real cardanoscan link.")
