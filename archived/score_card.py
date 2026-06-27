"""Render the explainable credit assessment — gauge, factors, harvest bars, limits."""
from __future__ import annotations

import streamlit as st

from dashboard import theme


def _yields(a):
    f = next((x for x in a.factors if x.name == "yield_consistency"), None)
    ys = (f.evidence.get("yields_kg") if f else None) or []
    return list(range(1, len(ys) + 1)), ys


def render_score_card(a) -> None:
    gcol, kcol = st.columns([1, 2], gap="large")
    with gcol:
        st.markdown(
            f'<div class="aw-card">{theme.gauge(a.overall_score, "Credit band " + a.credit["grade"], a.credit["limit"])}'
            f'<div style="margin-top:12px">Narration {theme.pill(a.mode["narration"])} '
            f'<span class="aw-pill live"><span class="dot"></span>SCORER · DETERMINISTIC</span></div>'
            f'</div>', unsafe_allow_html=True)
    with kcol:
        theme.kpis([
            {"label": f"Credit band {a.credit['grade']}", "icon": "bank",
             "value": a.credit["limit"].replace("up to ", ""), "sub": "recommended limit", "tone": "fill"},
            {"label": "Insurance", "value": a.insurance["grade"], "icon": "shield", "sub": a.insurance["note"]},
            {"label": "Confidence", "value": a.confidence["level"].title(), "icon": "spark",
             "sub": f"{a.confidence['value']} · {a.confidence['driver']}"},
        ])

    st.markdown("<br>", unsafe_allow_html=True)
    fcol, hcol = st.columns([3, 2], gap="large")
    with fcol:
        theme.section("Why — contributing factors", "contribution = weight × sub-score", "activity")
        bars = "".join(theme.factor_bar(f.label, f.sub_score, f.weight, f.contribution)
                       for f in sorted(a.factors, key=lambda x: x.contribution, reverse=True))
        st.markdown(f"<div class='aw-card'>{bars}</div>", unsafe_allow_html=True)
    with hcol:
        theme.section("Harvest history", "yield per season (kg)", "leaf")
        seasons, ys = _yields(a)
        if ys:
            theme.yield_bars(seasons, ys)
        else:
            st.caption("No harvest history.")

    st.markdown("<br>", unsafe_allow_html=True)
    theme.section("Analyst narrative", ic="spark")
    st.markdown(f"<div class='aw-card'>{a.narrative}</div>", unsafe_allow_html=True)

    with st.expander("⚖️  Limits — human-in-the-loop (read before acting)", expanded=True):
        for lim in a.limits:
            st.markdown(f"- {lim}")

    st.caption("Reproducible result_hash (committed on-chain via Masumi):")
    st.markdown(f"<span class='aw-hash'>{a.result_hash}</span>", unsafe_allow_html=True)
