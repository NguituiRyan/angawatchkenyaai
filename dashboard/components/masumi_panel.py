"""Render the Masumi round-trip as a styled vertical stepper with LIVE/MOCK badges."""
from __future__ import annotations

import streamlit as st

from dashboard import theme


def render_masumi(trip: dict, client_mode: str) -> None:
    st.markdown(f"Backend {theme.pill(client_mode)}", unsafe_allow_html=True)
    st.caption("A SACCO discovers the agent, pays escrow (USDM/ADA on Cardano preprod), the agent "
               "delivers, and the result hash is Decision-Logged on-chain for audit.")

    st.markdown(f"<div class='aw-card'>{theme.stepper(trip['steps'])}</div>", unsafe_allow_html=True)

    audit = trip["audit"]
    if audit.explorer_url:
        st.success(f"On-chain audit available ({audit.proof_kind}) — "
                   f"[view transaction]({audit.explorer_url}) ↗")
    else:
        st.warning("Audit is a labeled simulation (no funded preprod wallet). Set "
                   "`MASUMI_PRERECORDED_TX` or `MASUMI_MODE=real` for a real cardanoscan link.")
