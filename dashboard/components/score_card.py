"""Render the explainable credit assessment (score, factors, bands, limits)."""
from __future__ import annotations

import streamlit as st

from dashboard import theme

_GRADE_TONE = {"A": "k-green", "B": "k-blue", "C": "k-amber", "D": "k-amber"}


def render_score_card(a) -> None:
    tone = _GRADE_TONE.get(a.credit["grade"], "k-brand")
    theme.kpis([
        {"label": "Credit score", "value": f"{a.overall_score:.0f}", "sub": "of 100", "tone": tone},
        {"label": f"Credit band {a.credit['grade']}", "value": a.credit["limit"].replace("up to ", ""),
         "sub": "recommended limit", "tone": "k-brand"},
        {"label": "Insurance", "value": a.insurance["grade"], "sub": a.insurance["note"], "tone": "k-blue"},
        {"label": "Confidence", "value": a.confidence["level"].title(),
         "sub": f"{a.confidence['value']} · {a.confidence['driver']}", "tone": "k-amber"},
    ])
    st.markdown(f"<div style='margin:8px 0 2px'>Narration {theme.pill(a.mode['narration'])} "
                f"&nbsp;·&nbsp; scorer <span class='aw-pill live'><span class='dot'></span>"
                f"DETERMINISTIC</span></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    theme.section("Why — contributing factors", "contribution = weight × sub-score", "activity")
    bars = "".join(theme.factor_bar(f.label, f.sub_score, f.weight, f.contribution)
                   for f in sorted(a.factors, key=lambda x: x.contribution, reverse=True))
    st.markdown(f"<div class='aw-card'>{bars}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    theme.section("Analyst narrative", ic="spark")
    st.markdown(f"<div class='aw-card'>{a.narrative}</div>", unsafe_allow_html=True)

    with st.expander("⚖️  Limits — human-in-the-loop (read before acting)", expanded=True):
        for lim in a.limits:
            st.markdown(f"- {lim}")

    st.caption("Reproducible result_hash (committed on-chain via Masumi):")
    st.markdown(f"<span class='aw-hash'>{a.result_hash}</span>", unsafe_allow_html=True)
