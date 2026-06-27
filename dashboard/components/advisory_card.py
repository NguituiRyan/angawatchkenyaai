"""Render the Crop-Health Advisory report — the deliverable the co-op pays for."""
from __future__ import annotations

import html

import streamlit as st

from dashboard import theme

_RISK_TONE = {"HIGH": "#E5484D", "MED": "#E8A317", "LOW": "#54B435"}


def render_advisory_report(r) -> None:
    tone = _RISK_TONE.get(r.risk_level, "#54B435")
    st.markdown(
        f'<div class="aw-card" style="border-left:5px solid {tone}">'
        f'<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;align-items:center">'
        f'<div><div style="font-size:.72rem;color:var(--faint);font-family:JetBrains Mono,monospace">'
        f'ADVISORY · greenhouse {html.escape(r.greenhouse_id)} · for {html.escape(r.requested_by)}</div>'
        f'<div style="font-size:1.45rem;font-weight:800;color:var(--fg)">{html.escape(r.diagnosis)}</div>'
        f'<div style="color:var(--muted);font-size:.85rem">{("caused by "+html.escape(r.pathogen)) if r.pathogen else ""}</div>'
        f'</div>'
        f'<div style="text-align:right"><span style="background:{tone};color:#fff;border-radius:10px;'
        f'padding:7px 13px;font-weight:700;font-size:.85rem">{html.escape(r.priority)}</span></div>'
        f'</div></div>', unsafe_allow_html=True)

    theme.kpis([
        {"label": "Risk", "value": r.risk_level, "icon": "alert", "tone": "fill",
         "sub": "from sensor + rules"},
        {"label": "Confidence", "value": r.confidence["level"].title(), "icon": "spark",
         "sub": f"{r.confidence['value']} · {r.confidence['driver']}"},
        {"label": "Actions", "value": str(len(r.recommended_actions)), "icon": "check",
         "sub": "ranked, PHI-aware"},
        {"label": "Narration", "value": r.narration_mode.title(), "icon": "activity",
         "sub": f"graph backend {r.backend}"},
    ])

    if r.conditions:
        chips = " ".join(f'<span class="aw-tag phi">{html.escape(c)}</span>' for c in r.conditions)
        n_r = len(r.trigger_readings or [])
        st.markdown(f'<div style="margin:8px 0 6px"><span style="color:var(--muted);font-size:.8rem">'
                    f'graph evidence — favoured by {n_r} linked reading(s): </span>{chips}</div>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    pcol, ncol = st.columns([1, 1], gap="large")
    with pcol:
        theme.section("Treatment plan — ranked", "efficacy → pre-harvest interval → cost", "check")
        st.markdown(theme.treatment_list(r.recommended_actions, n=6), unsafe_allow_html=True)
    with ncol:
        theme.section("Advisor note", "grounded in the graph traversal", "spark")
        narr = (r.narrative or "").replace("**", "").replace("*", "")
        st.markdown(f"<div class='aw-card'>{html.escape(narr)}</div>", unsafe_allow_html=True)
        with st.expander("⚖️  Limits — human-in-the-loop (read before acting)", expanded=True):
            for lim in r.limits:
                st.markdown(f"- {lim}")

    st.caption("Reproducible result_hash (committed on-chain via Masumi — commits to the diagnosis + plan):")
    st.markdown(f"<span class='aw-hash'>{r.result_hash}</span>", unsafe_allow_html=True)
