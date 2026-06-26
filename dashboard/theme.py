"""Angawatch design system for Streamlit (UI/UX Pro Max — Data-Dense Dashboard).

Dark, premium, data-dense ops aesthetic: emerald brand (agri/live), amber accent
(finance/alert), blue data, status green/amber/red. Space Grotesk + Inter +
JetBrains Mono. One inject_theme() call + reusable HTML component helpers.
"""
from __future__ import annotations

import html

import streamlit as st

# Lucide-style inline SVGs (stroke=currentColor) — no emoji as structural icons.
ICONS = {
    "leaf": '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6"/>',
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1Z"/>',
    "bank": '<path d="M3 21h18"/><path d="M5 21V9l7-5 7 5v12"/><path d="M9 21v-6h6v6"/>',
    "chip": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "scan": '<path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/>',
    "spark": '<path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>',
    "alert": '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/><path d="M12 9v4M12 17h.01"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
}


def icon(name: str, size: int = 18, cls: str = "") -> str:
    body = ICONS.get(name, "")
    return (f'<svg class="aw-ic {cls}" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round">{body}</svg>')


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root{
  --bg:#0B1220; --bg2:#0E1626; --surface:#131C2E; --surface2:#172238;
  --border:rgba(255,255,255,.08); --border-2:rgba(255,255,255,.14);
  --fg:#E8EEF6; --muted:#9AA8BD; --faint:#6B7A92;
  --brand:#22C55E; --brand-2:#16A34A; --blue:#3B82F6; --amber:#F59E0B; --amber-2:#D97706;
  --green:#22C55E; --warn:#F59E0B; --danger:#EF4444;
  --radius:16px; --radius-sm:10px;
  --shadow:0 10px 30px -12px rgba(0,0,0,.55); --shadow-lg:0 24px 60px -24px rgba(0,0,0,.7);
}

/* base */
html, body, [data-testid="stAppViewContainer"], .stApp{
  background:
    radial-gradient(1200px 600px at 12% -8%, rgba(34,197,94,.10), transparent 55%),
    radial-gradient(1000px 520px at 92% 0%, rgba(59,130,246,.10), transparent 55%),
    linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%) fixed;
  color:var(--fg);
  font-family:'Inter', system-ui, sans-serif;
}
[data-testid="stHeader"]{background:transparent;}
#MainMenu, footer, [data-testid="stToolbar"]{visibility:hidden; height:0;}
.block-container{padding-top:1.6rem; padding-bottom:3rem; max-width:1320px;}

h1,h2,h3,h4{font-family:'Space Grotesk', sans-serif!important; letter-spacing:-.02em; color:var(--fg);}
p, span, label, li, .stMarkdown{color:var(--fg);}
.mono, code, kbd{font-family:'JetBrains Mono', monospace!important; font-variant-numeric:tabular-nums;}
small, .aw-muted{color:var(--muted);}

/* hero */
.aw-hero{
  position:relative; border-radius:var(--radius); padding:26px 30px; margin-bottom:18px;
  background:linear-gradient(135deg, rgba(34,197,94,.16), rgba(59,130,246,.10) 60%, rgba(245,158,11,.10));
  border:1px solid var(--border-2); box-shadow:var(--shadow-lg); overflow:hidden;
}
.aw-hero::after{content:""; position:absolute; inset:0; background:
  radial-gradient(420px 200px at 88% -40%, rgba(245,158,11,.18), transparent 60%); pointer-events:none;}
.aw-hero h1{font-size:2.15rem; margin:0 0 6px; display:flex; align-items:center; gap:12px;}
.aw-hero .tag{color:var(--muted); font-size:1.02rem; max-width:760px; margin:0;}
.aw-logo{display:inline-grid; place-items:center; width:46px; height:46px; border-radius:13px;
  background:linear-gradient(140deg,var(--brand),var(--brand-2)); color:#04140A;
  box-shadow:0 8px 22px -6px rgba(34,197,94,.7);}
.aw-statusbar{display:flex; flex-wrap:wrap; gap:8px; margin-top:16px;}

/* pills / badges */
.aw-pill{display:inline-flex; align-items:center; gap:7px; font-size:.74rem; font-weight:600;
  padding:5px 11px; border-radius:999px; border:1px solid var(--border-2);
  font-family:'JetBrains Mono',monospace; letter-spacing:.02em; white-space:nowrap;}
.aw-pill .dot{width:7px;height:7px;border-radius:999px; box-shadow:0 0 0 3px rgba(255,255,255,.05);}
.aw-pill.live{background:rgba(34,197,94,.12); color:#7ef0a8; border-color:rgba(34,197,94,.35);}
.aw-pill.live .dot{background:var(--green); box-shadow:0 0 10px 1px var(--green);}
.aw-pill.mock{background:rgba(245,158,11,.12); color:#ffd27a; border-color:rgba(245,158,11,.35);}
.aw-pill.mock .dot{background:var(--amber); box-shadow:0 0 10px 1px var(--amber);}

/* cards */
.aw-card{background:linear-gradient(180deg,var(--surface),var(--surface2));
  border:1px solid var(--border); border-radius:var(--radius); padding:18px 20px;
  box-shadow:var(--shadow); backdrop-filter:blur(6px);}
.aw-section{display:flex; align-items:center; gap:11px; margin:6px 0 12px;}
.aw-section .ic{display:grid; place-items:center; width:34px; height:34px; border-radius:10px;
  background:rgba(255,255,255,.05); border:1px solid var(--border); color:var(--brand);}
.aw-section h3{margin:0; font-size:1.12rem;}
.aw-section p{margin:1px 0 0; font-size:.82rem; color:var(--muted);}

/* KPI */
.aw-kpis{display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px;}
.aw-kpi{background:linear-gradient(180deg,var(--surface),var(--surface2)); border:1px solid var(--border);
  border-radius:var(--radius-sm); padding:14px 16px; position:relative; overflow:hidden;
  transition:transform .2s ease, border-color .2s ease;}
.aw-kpi:hover{transform:translateY(-2px); border-color:var(--border-2);}
.aw-kpi .k-label{font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; color:var(--faint);}
.aw-kpi .k-val{font-family:'Space Grotesk',sans-serif; font-size:1.7rem; font-weight:700; margin-top:3px;
  font-variant-numeric:tabular-nums; line-height:1.1;}
.aw-kpi .k-sub{font-size:.76rem; color:var(--muted); margin-top:2px;}
.aw-kpi .k-edge{position:absolute; left:0; top:0; bottom:0; width:4px;}
.k-brand .k-edge{background:var(--brand);} .k-blue .k-edge{background:var(--blue);}
.k-amber .k-edge{background:var(--amber);} .k-green .k-val{color:#7ef0a8;}

/* factor bars */
.aw-factor{margin:9px 0;}
.aw-factor .row{display:flex; justify-content:space-between; align-items:baseline; gap:8px;}
.aw-factor .lbl{font-size:.9rem;} .aw-factor .ctr{font-family:'JetBrains Mono',monospace; color:var(--brand); font-weight:600;}
.aw-factor .meta{font-size:.72rem; color:var(--faint); font-family:'JetBrains Mono',monospace;}
.aw-bar{height:8px; border-radius:999px; background:rgba(255,255,255,.06); margin-top:6px; overflow:hidden;}
.aw-bar > span{display:block; height:100%; border-radius:999px;
  background:linear-gradient(90deg,var(--brand-2),var(--brand)); box-shadow:0 0 12px rgba(34,197,94,.4);
  animation:grow .7s cubic-bezier(.2,.7,.2,1) both;}
@keyframes grow{from{width:0 !important;} }

/* masumi stepper */
.aw-steps{position:relative; margin:6px 0; padding-left:10px;}
.aw-step{display:flex; gap:14px; padding:10px 0; position:relative;}
.aw-step:not(:last-child)::before{content:""; position:absolute; left:13px; top:30px; bottom:-6px;
  width:2px; background:linear-gradient(180deg,var(--border-2),transparent);}
.aw-step .node{flex:0 0 auto; width:28px; height:28px; border-radius:999px; display:grid; place-items:center;
  font-size:.78rem; font-weight:700; font-family:'JetBrains Mono',monospace;
  background:var(--surface2); border:1px solid var(--border-2); color:var(--fg); z-index:1;}
.aw-step.live .node{border-color:rgba(34,197,94,.5); color:#7ef0a8; box-shadow:0 0 0 4px rgba(34,197,94,.08);}
.aw-step.mock .node{border-color:rgba(245,158,11,.5); color:#ffd27a; box-shadow:0 0 0 4px rgba(245,158,11,.08);}
.aw-step .body{flex:1;}
.aw-step .t{font-weight:600; font-size:.94rem; display:flex; align-items:center; gap:8px; flex-wrap:wrap;}
.aw-step .d{font-size:.8rem; color:var(--muted); margin-top:1px;}
.aw-step .tx{font-family:'JetBrains Mono',monospace; font-size:.74rem; color:var(--faint); margin-top:3px;}
.aw-step .tx a{color:var(--blue); text-decoration:none;} .aw-step .tx a:hover{text-decoration:underline;}

/* alert banner */
.aw-alert{display:flex; gap:13px; padding:14px 16px; border-radius:var(--radius-sm); margin:4px 0 12px;
  border:1px solid; align-items:flex-start; animation:fadeUp .35s ease both;}
.aw-alert.high{background:rgba(239,68,68,.10); border-color:rgba(239,68,68,.4);}
.aw-alert.med{background:rgba(245,158,11,.10); border-color:rgba(245,158,11,.4);}
.aw-alert .ai{flex:0 0 auto; margin-top:1px;} .aw-alert.high .ai{color:var(--danger);} .aw-alert.med .ai{color:var(--amber);}
.aw-alert .at{font-weight:700; font-family:'Space Grotesk',sans-serif; display:flex; gap:8px; align-items:center;}
.aw-alert .am{font-size:.86rem; color:var(--fg); opacity:.92; margin-top:2px;}
@keyframes fadeUp{from{opacity:0; transform:translateY(8px);} to{opacity:1; transform:none;}}

.aw-hash{font-family:'JetBrains Mono',monospace; font-size:.74rem; color:var(--faint);
  background:rgba(255,255,255,.04); border:1px solid var(--border); border-radius:8px;
  padding:6px 10px; word-break:break-all; display:inline-block;}

/* native widget theming */
.stButton > button{border-radius:11px!important; border:1px solid var(--border-2)!important;
  font-weight:600!important; font-family:'Inter',sans-serif!important; transition:all .18s ease!important;
  background:var(--surface2)!important; color:var(--fg)!important;}
.stButton > button:hover{transform:translateY(-1px); border-color:var(--brand)!important;
  box-shadow:0 8px 20px -10px rgba(34,197,94,.5)!important;}
.stButton > button[kind="primary"]{background:linear-gradient(135deg,var(--brand),var(--brand-2))!important;
  color:#04140A!important; border:none!important; box-shadow:0 10px 24px -10px rgba(34,197,94,.7)!important;}
.stButton > button[kind="primary"]:hover{filter:brightness(1.05);}

[data-testid="stMetric"]{background:linear-gradient(180deg,var(--surface),var(--surface2));
  border:1px solid var(--border); border-radius:var(--radius-sm); padding:14px 16px; box-shadow:var(--shadow);}
[data-testid="stMetricValue"]{font-family:'Space Grotesk',sans-serif; font-variant-numeric:tabular-nums;}
[data-testid="stMetricLabel"] p{color:var(--faint); text-transform:uppercase; letter-spacing:.06em; font-size:.72rem;}

.stTabs [data-baseweb="tab-list"]{gap:6px; border-bottom:1px solid var(--border);}
.stTabs [data-baseweb="tab"]{background:transparent; border-radius:10px 10px 0 0; padding:9px 16px;
  color:var(--muted); font-weight:600;}
.stTabs [aria-selected="true"]{background:rgba(255,255,255,.04); color:var(--fg);
  border-bottom:2px solid var(--brand);}

[data-testid="stSidebar"]{background:linear-gradient(180deg,#0C1424,#0A1120); border-right:1px solid var(--border);}
[data-testid="stSidebar"] *{color:var(--fg);}

[data-testid="stDataFrame"]{border:1px solid var(--border); border-radius:12px; overflow:hidden;}
hr{border-color:var(--border)!important;}
::-webkit-scrollbar{width:9px; height:9px;} ::-webkit-scrollbar-thumb{background:var(--border-2); border-radius:9px;}

/* guided flow tracker */
.aw-flow{display:flex; gap:0; margin:4px 0 20px; flex-wrap:wrap;}
.aw-fstep{display:flex; align-items:center; gap:10px; padding:10px 16px; background:var(--surface);
  border:1px solid var(--border); flex:1; min-width:165px; transition:all .2s ease;}
.aw-fstep:first-child{border-radius:12px 0 0 12px;}
.aw-fstep:last-child{border-radius:0 12px 12px 0;}
.aw-fstep .n{width:24px;height:24px;border-radius:999px;display:grid;place-items:center;font-size:.76rem;
  font-weight:700;font-family:'JetBrains Mono',monospace;background:var(--surface2);
  border:1px solid var(--border-2);color:var(--muted); flex:0 0 auto;}
.aw-fstep .l{font-size:.84rem;color:var(--muted);font-weight:500;line-height:1.2;}
.aw-fstep.done{background:rgba(34,197,94,.08); border-color:rgba(34,197,94,.3);}
.aw-fstep.done .n{background:var(--brand);color:#04140A;border-color:transparent;}
.aw-fstep.done .l{color:var(--fg);}
.aw-fstep.active{background:rgba(245,158,11,.10); border-color:rgba(245,158,11,.45);}
.aw-fstep.active .n{background:var(--amber);color:#1a1206;border-color:transparent;
  box-shadow:0 0 0 4px rgba(245,158,11,.12);}
.aw-fstep.active .l{color:var(--fg);}

/* footer */
.aw-footer{margin-top:34px; padding:18px 4px 4px; border-top:1px solid var(--border);
  color:var(--faint); font-size:.8rem; display:flex; justify-content:space-between;
  flex-wrap:wrap; gap:10px; align-items:center;}
.aw-footer .aw-pill{font-size:.7rem;}

[data-testid="stExpander"]{border:1px solid var(--border)!important; border-radius:12px!important;
  background:var(--surface)!important;}
.stAlert{border-radius:12px!important;}

@media (prefers-reduced-motion: reduce){*{animation:none!important; transition:none!important;}}
</style>
"""


def inject_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


# --------------------------------------------------------------- components --
def _is_live(mode: str) -> bool:
    return str(mode).lower() in ("live", "neo4j", "real")


def pill(mode: str, label: str | None = None) -> str:
    live = _is_live(mode)
    cls = "live" if live else "mock"
    text = label or ("LIVE" if live else "MOCK")
    return f'<span class="aw-pill {cls}"><span class="dot"></span>{html.escape(text)}</span>'


def hero(status: dict) -> None:
    chips = "".join(pill(m, f"{name} · {m}") for name, m in status.items())
    st.markdown(
        f'<div class="aw-hero"><h1><span class="aw-logo">{icon("leaf",24)}</span>Angawatch</h1>'
        f'<p class="tag">Early crop-saving alerts <b>and</b> a verified farm record that lenders '
        f'price risk against — sensors → risk engine → farmer alert → Neo4j record → a Masumi-hired, '
        f'explainable Credit-Risk Agent.</p>'
        f'<div class="aw-statusbar">{chips}</div></div>', unsafe_allow_html=True)


def section(title: str, subtitle: str = "", ic: str = "activity") -> None:
    st.markdown(
        f'<div class="aw-section"><span class="ic">{icon(ic,18)}</span>'
        f'<div><h3>{html.escape(title)}</h3>'
        + (f'<p>{html.escape(subtitle)}</p>' if subtitle else "")
        + '</div></div>', unsafe_allow_html=True)


def kpis(items: list[dict]) -> None:
    cards = ""
    for it in items:
        tone = it.get("tone", "k-brand")
        cards += (f'<div class="aw-kpi {tone}"><span class="k-edge"></span>'
                  f'<div class="k-label">{html.escape(str(it["label"]))}</div>'
                  f'<div class="k-val">{html.escape(str(it["value"]))}</div>'
                  f'<div class="k-sub">{html.escape(str(it.get("sub","")))}</div></div>')
    st.markdown(f'<div class="aw-kpis">{cards}</div>', unsafe_allow_html=True)


def factor_bar(label: str, sub_score: float, weight: float, contribution: float) -> str:
    pct = max(0, min(100, sub_score))
    return (f'<div class="aw-factor"><div class="row"><span class="lbl">{html.escape(label)}</span>'
            f'<span class="ctr">+{contribution:.1f}</span></div>'
            f'<div class="aw-bar"><span style="width:{pct:.0f}%"></span></div>'
            f'<div class="meta">{sub_score:.0f}/100 · weight {weight}</div></div>')


def stepper(steps: list[dict]) -> str:
    rows = ""
    for i, s in enumerate(steps, 1):
        cls = "live" if _is_live(s["mode"]) else "mock"
        proof = s.get("proof_kind")
        proof_html = (f'{pill(s["mode"])}' +
                      (f' <span class="aw-muted" style="font-size:.72rem">{html.escape(proof)}</span>'
                       if proof and proof not in ("—", "simulated") else ""))
        tx = ""
        if s.get("tx_hash"):
            short = html.escape(s["tx_hash"][:30]) + "…"
            if s.get("explorer_url"):
                tx = f'<div class="tx">tx <a href="{html.escape(s["explorer_url"])}" target="_blank">{short}</a> ↗</div>'
            else:
                tx = f'<div class="tx">tx {short} (simulated — no on-chain link)</div>'
        rows += (f'<div class="aw-step {cls}"><div class="node">{i}</div><div class="body">'
                 f'<div class="t">{html.escape(s["label"])} {proof_html}</div>'
                 f'<div class="d">{html.escape(s.get("detail",""))}</div>{tx}</div></div>')
    return f'<div class="aw-steps">{rows}</div>'


def flow_steps(steps: list[tuple[str, str]]) -> None:
    """steps = [(label, state)] where state in {'done','active',''}."""
    cells = ""
    for i, (label, state) in enumerate(steps, 1):
        mark = icon("check", 14) if state == "done" else str(i)
        cells += (f'<div class="aw-fstep {state}"><span class="n">{mark}</span>'
                  f'<span class="l">{html.escape(label)}</span></div>')
    st.markdown(f'<div class="aw-flow">{cells}</div>', unsafe_allow_html=True)


def feed_chart(df):
    """Dark feed chart: humidity + air temp over time, themed green/amber.

    Uses Streamlit's native chart (sizes reliably) with a step index so repeated
    times-of-day don't collapse. The 90% blight threshold is noted in the caption.
    """
    data = (df[["humidity", "temp_c"]]
            .rename(columns={"humidity": "Humidity %", "temp_c": "Air temp °C"})
            .reset_index(drop=True))
    data.index.name = "reading"
    st.line_chart(data, color=["#34D399", "#FBBF24"], height=240, use_container_width=True)


def footer() -> None:
    st.markdown(
        '<div class="aw-footer"><span>Angawatch · Kenya AI Challenge — AgriFin track + '
        'Masumi Business-Agent bounty</span>'
        '<span class="aw-pill live"><span class="dot"></span>Deterministic core · '
        'labeled mocks · human-in-the-loop</span></div>', unsafe_allow_html=True)


def alert_card(level: str, kind: str, message: str, delivery: str, provider: str) -> None:
    cls = "high" if level == "HIGH" else "med"
    st.markdown(
        f'<div class="aw-alert {cls}"><span class="ai">{icon("alert",22)}</span><div>'
        f'<div class="at">{html.escape(kind)} · {level} '
        f'<span class="aw-muted" style="font-size:.74rem;font-weight:400">'
        f'{html.escape(delivery.upper())} via {html.escape(provider)}</span></div>'
        f'<div class="am">{html.escape(message)}</div></div></div>', unsafe_allow_html=True)
