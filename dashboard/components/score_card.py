"""Render the explainable credit assessment (score, factors, bands, limits)."""
from __future__ import annotations

import streamlit as st

from logging_setup import badge

_GRADE_COLOR = {"A": "green", "B": "blue", "C": "orange", "D": "red"}


def render_score_card(a) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Credit score", f"{a.overall_score:.0f}/100")
    c2.metric(f"Credit band {a.credit['grade']}", a.credit["limit"])
    c3.metric("Insurance", a.insurance["grade"], a.insurance["note"])

    grade = a.credit["grade"]
    st.markdown(f"**Recommendation:** :{_GRADE_COLOR.get(grade,'gray')}[Band {grade}] · "
                f"confidence **{a.confidence['level']}** ({a.confidence['value']}) — "
                f"{a.confidence['driver']}")
    st.caption(f"Narration: {badge(a.mode['narration'])}  ·  scorer: deterministic")

    st.markdown("**Why — contributing factors** (contribution = weight × sub-score)")
    for f in sorted(a.factors, key=lambda x: x.contribution, reverse=True):
        left, right = st.columns([3, 1])
        left.write(f"{f.label}")
        left.progress(min(1.0, f.sub_score / 100))
        right.write(f"**+{f.contribution:.1f}**")
        right.caption(f"{f.sub_score:.0f}/100 ×{f.weight}")

    st.markdown("**Analyst narrative**")
    st.write(a.narrative)

    with st.expander("⚖️ Limits — human-in-the-loop (read before acting)", expanded=True):
        for lim in a.limits:
            st.write(f"• {lim}")

    st.caption(f"Reproducible result_hash (committed on-chain via Masumi): `{a.result_hash}`")
