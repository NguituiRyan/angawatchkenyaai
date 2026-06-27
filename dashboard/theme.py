"""Angawatch design system for Streamlit — LIGHT agri-SaaS look (GoAgri-style).

White rounded cards + soft shadows, vibrant green brand, friendly geometric type
(Plus Jakarta Sans + Inter). Green hero conditions card, SVG gauges, green-fill
KPI cards, green charts. One inject_theme() + reusable HTML component helpers.
"""
from __future__ import annotations

import html
import math

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
    "search": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "drop": '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5S5 13 5 15a7 7 0 0 0 7 7Z"/>',
    "thermo": '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
    "bug": '<path d="m8 2 1.88 1.88M14.12 3.88 16 2M9 7.13V6a3 3 0 1 1 6 0v1.13M12 20v-9M6.53 9C4.6 8.8 3 7.1 3 5M6 13H2M3 21c0-2.1 1.7-3.9 3.8-4M20.97 5c0 2.1-1.6 3.8-3.5 4M22 13h-4M17.2 17c2.1.1 3.8 1.9 3.8 4"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
}


def icon(name: str, size: int = 18, cls: str = "") -> str:
    body = ICONS.get(name, "")
    return (f'<svg class="aw-ic {cls}" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true" focusable="false">{body}</svg>')


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root{
  --bg:#F2F5EE; --surface:#FFFFFF; --surface-2:#F8FBF5;
  --border:#E7ECE0; --border-2:#DDE6D2;
  --fg:#1B2A1F; --muted:#5C6B5E; --faint:#6E7D70;   /* AA-contrast greens on white */
  --brand:#54B435; --brand-strong:#3F9E2A; --brand-ink:#2E7321; --brand-soft:#EAF6E1;
  --hero-1:#8FD64E; --hero-2:#57B72F;
  --amber:#F2C53D; --amber-soft:#FBF1CF; --blue:#3B82F6; --danger:#E5484D; --danger-soft:#FBE7E7;
  --radius:18px; --radius-sm:13px;
  --shadow:0 12px 30px -14px rgba(46,80,40,.16); --shadow-sm:0 6px 18px -10px rgba(46,80,40,.14);
}

html, body, [data-testid="stAppViewContainer"], .stApp{
  background:var(--bg); color:var(--fg);
  font-family:'Inter', system-ui, sans-serif;
}
[data-testid="stHeader"]{background:transparent;}
#MainMenu, footer, [data-testid="stToolbar"]{visibility:hidden; height:0;}
.block-container{padding-top:1.4rem; padding-bottom:3rem; max-width:1340px;}

h1,h2,h3,h4{font-family:'Plus Jakarta Sans', sans-serif!important; color:var(--fg);
  letter-spacing:-.01em; font-weight:700;}
p, span, label, li, .stMarkdown{color:var(--fg);}
.mono, code, kbd{font-family:'JetBrains Mono', monospace!important; font-variant-numeric:tabular-nums;}
.aw-muted, small{color:var(--muted);}

/* top bar */
.aw-topbar{display:flex; align-items:center; justify-content:space-between; gap:12px;
  margin:2px 0 16px; flex-wrap:wrap;}
.aw-topbar .t h2{margin:0; font-size:1.5rem; display:flex; align-items:center; gap:10px;}
.aw-topbar .t p{margin:1px 0 0; color:var(--muted); font-size:.86rem;}
.aw-logo{display:inline-grid; place-items:center; width:38px; height:38px; border-radius:12px;
  background:linear-gradient(140deg,var(--hero-1),var(--hero-2)); color:#0d2b07;
  box-shadow:0 8px 18px -8px rgba(87,183,47,.65);}
.aw-chips{display:flex; gap:8px; align-items:center; flex-wrap:wrap;}
.aw-chip{display:inline-flex; align-items:center; gap:7px; background:var(--surface);
  border:1px solid var(--border); border-radius:11px; padding:8px 12px; font-size:.82rem;
  color:var(--muted); box-shadow:var(--shadow-sm);}
.aw-chip svg{color:var(--brand-strong);}
.aw-chip .nbadge{display:inline-grid;place-items:center;min-width:18px;height:18px;border-radius:9px;
  background:var(--danger);color:#fff;font-size:.66rem;font-weight:700;padding:0 5px;}

/* pills / badges */
.aw-pill{display:inline-flex; align-items:center; gap:7px; font-size:.72rem; font-weight:600;
  padding:5px 11px; border-radius:999px; font-family:'JetBrains Mono',monospace;
  letter-spacing:.01em; white-space:nowrap; border:1px solid transparent;}
.aw-pill .dot{width:7px;height:7px;border-radius:999px;}
.aw-pill.live{background:var(--brand-soft); color:var(--brand-ink); border-color:#C9E8B8;}
.aw-pill.live .dot{background:var(--brand); box-shadow:0 0 0 3px rgba(84,180,53,.18);}
.aw-pill.mock{background:var(--amber-soft); color:#9A7B12; border-color:#F0E0A0;}
.aw-pill.mock .dot{background:var(--amber); box-shadow:0 0 0 3px rgba(242,197,61,.22);}

/* cards */
.aw-card{background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
  padding:20px 22px; box-shadow:var(--shadow-sm);}
.aw-section{display:flex; align-items:center; gap:12px; margin:4px 0 14px;}
.aw-section .ic{display:grid; place-items:center; width:38px; height:38px; border-radius:12px;
  background:var(--brand-soft); border:1px solid #D7EDC8; color:var(--brand-strong);}
.aw-section h3{margin:0; font-size:1.16rem;}
.aw-section p{margin:1px 0 0; font-size:.84rem; color:var(--muted);}

/* hero conditions (green gradient card) */
.aw-hero{position:relative; border-radius:24px; padding:26px 28px; overflow:hidden; color:#08230a;
  background:linear-gradient(135deg,var(--hero-1) 0%,var(--hero-2) 70%, #3FA026 100%);
  box-shadow:0 22px 44px -22px rgba(64,140,40,.6); margin-bottom:8px;}
.aw-hero::after{content:""; position:absolute; right:-40px; top:-40px; width:280px; height:280px;
  border-radius:50%; background:radial-gradient(circle, rgba(255,255,255,.28), transparent 65%);}
.aw-hero .h-top{display:flex; justify-content:space-between; align-items:center; position:relative; z-index:1;}
.aw-hero .h-loc{display:flex; align-items:center; gap:9px; font-weight:600; font-size:.92rem;}
.aw-hero .h-date{background:rgba(255,255,255,.35); border-radius:10px; padding:6px 12px;
  font-size:.78rem; font-weight:600; backdrop-filter:blur(4px);}
.aw-hero .h-temp{font-family:'Plus Jakarta Sans',sans-serif; font-size:4rem; font-weight:800;
  line-height:1; margin:14px 0 2px; position:relative; z-index:1;}
.aw-hero .h-cond{font-weight:600; opacity:.85; position:relative; z-index:1;}
.aw-hero .h-status{display:inline-flex; align-items:center; gap:7px; margin-top:12px; position:relative;
  z-index:1; background:rgba(255,255,255,.9); color:#1c4a12; border-radius:999px; padding:6px 13px;
  font-size:.8rem; font-weight:700;}
.aw-hero .h-status .dot{width:8px;height:8px;border-radius:999px;}
.aw-hero .h-mini{display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:20px;
  position:relative; z-index:1;}
.aw-hero .h-mini .m{background:rgba(255,255,255,.42); border-radius:14px; padding:11px 13px;
  backdrop-filter:blur(4px);}
.aw-hero .h-mini .m .ml{font-size:.7rem; font-weight:600; opacity:.8; display:flex; gap:5px; align-items:center;}
.aw-hero .h-mini .m .mv{font-family:'Plus Jakarta Sans',sans-serif; font-size:1.3rem; font-weight:800;
  margin-top:2px; font-variant-numeric:tabular-nums;}
.aw-plant{position:absolute; right:18px; bottom:8px; opacity:.9; z-index:1;}

/* KPI */
.aw-kpis{display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:13px;}
.aw-kpi{background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm);
  padding:15px 17px; box-shadow:var(--shadow-sm); transition:transform .18s ease, box-shadow .18s ease;}
.aw-kpi:hover{transform:translateY(-2px); box-shadow:var(--shadow);}
.aw-kpi .k-label{font-size:.72rem; text-transform:uppercase; letter-spacing:.05em; color:var(--faint);
  font-weight:600; display:flex; align-items:center; gap:6px;}
.aw-kpi .k-val{font-family:'Plus Jakarta Sans',sans-serif; font-size:1.7rem; font-weight:800; margin-top:4px;
  font-variant-numeric:tabular-nums; line-height:1.1; color:var(--fg);}
.aw-kpi .k-sub{font-size:.76rem; color:var(--muted); margin-top:2px;}
.aw-kpi.fill{background:linear-gradient(140deg,var(--hero-1),var(--brand-strong)); border:none; color:#0a2409;}
.aw-kpi.fill .k-label{color:rgba(8,36,9,.7);} .aw-kpi.fill .k-val{color:#0a2409;}
.aw-kpi.fill .k-sub{color:rgba(8,36,9,.72);}
.aw-kpi .k-label svg{color:var(--brand-strong);} .aw-kpi.fill .k-label svg{color:#0a2409;}

/* gauge */
.aw-gauge{display:flex; align-items:center; gap:18px;}
.aw-gauge .g-meta .gl{font-size:.74rem; text-transform:uppercase; letter-spacing:.05em;
  color:var(--faint); font-weight:600;}
.aw-gauge .g-meta .gv{font-family:'Plus Jakarta Sans',sans-serif; font-size:1.5rem; font-weight:800;}
.aw-gauge .g-meta .gs{font-size:.82rem; color:var(--muted);}

/* factor bars */
.aw-factor{margin:11px 0;}
.aw-factor .row{display:flex; justify-content:space-between; align-items:baseline; gap:8px;}
.aw-factor .lbl{font-size:.92rem; font-weight:600;}
.aw-factor .ctr{font-family:'JetBrains Mono',monospace; color:var(--brand-strong); font-weight:700;}
.aw-factor .meta{font-size:.72rem; color:var(--faint); font-family:'JetBrains Mono',monospace; margin-top:3px;}
.aw-bar{height:9px; border-radius:999px; background:#EEF3E8; margin-top:7px; overflow:hidden;}
.aw-bar > span{display:block; height:100%; border-radius:999px;
  background:linear-gradient(90deg,var(--hero-1),var(--brand-strong));
  animation:grow .7s cubic-bezier(.2,.7,.2,1) both;}
@keyframes grow{from{width:0 !important;}}

/* masumi stepper */
.aw-steps{position:relative; margin:4px 0;}
.aw-step{display:flex; gap:15px; padding:11px 0; position:relative;}
.aw-step:not(:last-child)::before{content:""; position:absolute; left:15px; top:34px; bottom:-4px;
  width:2px; background:var(--border-2);}
.aw-step .node{flex:0 0 auto; width:32px; height:32px; border-radius:999px; display:grid; place-items:center;
  font-size:.82rem; font-weight:800; font-family:'Plus Jakarta Sans',sans-serif;
  background:var(--surface); border:2px solid var(--border-2); color:var(--muted); z-index:1;}
.aw-step.live .node{border-color:var(--brand); color:var(--brand-ink); background:var(--brand-soft);}
.aw-step.mock .node{border-color:var(--amber); color:#9A7B12; background:var(--amber-soft);}
.aw-step .body{flex:1;}
.aw-step .t{font-weight:700; font-size:.95rem; display:flex; align-items:center; gap:8px; flex-wrap:wrap;
  font-family:'Plus Jakarta Sans',sans-serif;}
.aw-step .d{font-size:.82rem; color:var(--muted); margin-top:2px;}
.aw-step .tx{font-family:'JetBrains Mono',monospace; font-size:.74rem; color:var(--faint); margin-top:3px;}
.aw-step .tx a{color:var(--blue); text-decoration:none;} .aw-step .tx a:hover{text-decoration:underline;}

/* alert banner */
.aw-alert{display:flex; gap:13px; padding:15px 17px; border-radius:var(--radius-sm); margin:2px 0 14px;
  border:1px solid; align-items:flex-start; animation:fadeUp .35s ease both;}
.aw-alert.high{background:var(--danger-soft); border-color:#F3C9C9;}
.aw-alert.med{background:var(--amber-soft); border-color:#F0E0A0;}
.aw-alert .ai{flex:0 0 auto; margin-top:1px;} .aw-alert.high .ai{color:var(--danger);} .aw-alert.med .ai{color:#C99A12;}
.aw-alert .at{font-weight:800; font-family:'Plus Jakarta Sans',sans-serif; display:flex; gap:8px; align-items:center;}
.aw-alert .am{font-size:.87rem; color:var(--fg); opacity:.92; margin-top:2px;}
@keyframes fadeUp{from{opacity:0; transform:translateY(8px);} to{opacity:1; transform:none;}}

.aw-hash{font-family:'JetBrains Mono',monospace; font-size:.74rem; color:var(--muted);
  background:var(--surface-2); border:1px solid var(--border); border-radius:9px;
  padding:6px 10px; word-break:break-all; display:inline-block;}

/* guided flow tracker */
.aw-flow{display:flex; gap:10px; margin:8px 0 18px; flex-wrap:wrap;}
.aw-fstep{display:flex; align-items:center; gap:11px; padding:13px 16px; background:var(--surface);
  border:1px solid var(--border); flex:1; min-width:170px; border-radius:14px; box-shadow:var(--shadow-sm);
  transition:all .2s ease;}
.aw-fstep .n{width:26px;height:26px;border-radius:999px;display:grid;place-items:center;font-size:.78rem;
  font-weight:800;font-family:'Plus Jakarta Sans',monospace;background:#EEF3E8;
  border:1px solid var(--border-2);color:var(--muted); flex:0 0 auto;}
.aw-fstep .l{font-size:.86rem;color:var(--muted);font-weight:600;line-height:1.2;}
.aw-fstep.done{background:var(--brand-soft); border-color:#C9E8B8;}
.aw-fstep.done .n{background:var(--brand);color:#fff;border-color:transparent;}
.aw-fstep.done .l{color:var(--brand-ink);}
.aw-fstep.active{background:#fff; border-color:var(--amber); box-shadow:0 0 0 3px rgba(242,197,61,.15);}
.aw-fstep.active .n{background:var(--amber);color:#1a1206;border-color:transparent;}
.aw-fstep.active .l{color:var(--fg);}
.aw-flow-v{flex-direction:column; gap:8px;}
.aw-flow-v .aw-fstep{min-width:0; width:100%; border-radius:12px; padding:11px 13px;}
.aw-flow-v .aw-fstep .l{font-size:.82rem;}

/* footer */
.aw-footer{margin-top:30px; padding:18px 4px 4px; border-top:1px solid var(--border);
  color:var(--faint); font-size:.8rem; display:flex; justify-content:space-between;
  flex-wrap:wrap; gap:10px; align-items:center;}

/* native widget theming */
.stButton > button{border-radius:12px!important; border:1px solid var(--border)!important;
  font-weight:700!important; font-family:'Plus Jakarta Sans',sans-serif!important;
  transition:all .18s ease!important; background:var(--surface)!important; color:var(--fg)!important;
  box-shadow:var(--shadow-sm)!important;}
.stButton > button:hover{transform:translateY(-1px); border-color:var(--brand)!important; color:var(--brand-ink)!important;}
.stButton > button[kind="primary"]{background:linear-gradient(135deg,var(--hero-1),var(--brand-strong))!important;
  color:#0a2409!important; border:none!important; box-shadow:0 10px 22px -10px rgba(84,180,53,.6)!important;}
.stButton > button[kind="primary"]:hover{filter:brightness(1.04); color:#0a2409!important;}

[data-testid="stMetric"]{background:var(--surface); border:1px solid var(--border);
  border-radius:var(--radius-sm); padding:15px 17px; box-shadow:var(--shadow-sm);}
[data-testid="stMetricValue"]{font-family:'Plus Jakarta Sans',sans-serif; font-variant-numeric:tabular-nums;}
[data-testid="stMetricLabel"] p{color:var(--faint); text-transform:uppercase; letter-spacing:.05em; font-size:.72rem;}

/* primary navigation — the hero element: big, elevated segmented control */
.stTabs [data-baseweb="tab-list"]{gap:10px; border-bottom:none; background:var(--surface);
  padding:9px; border-radius:20px; border:1px solid var(--border); box-shadow:var(--shadow);
  margin:2px 0 16px;}
.stTabs [data-baseweb="tab"]{flex:1; justify-content:center; background:var(--surface-2);
  border-radius:14px; padding:16px 14px; color:var(--muted); font-weight:800; font-size:1.05rem;
  font-family:'Plus Jakarta Sans',sans-serif; border:1px solid var(--border);
  transition:transform .16s ease, box-shadow .16s ease, background .16s ease;}
.stTabs [data-baseweb="tab"]:hover{background:var(--brand-soft); color:var(--brand-ink);
  border-color:#cfe9bf;}
.stTabs [aria-selected="true"]{border:none!important;
  background:linear-gradient(135deg,var(--hero-1),var(--brand-strong))!important;
  color:#0a2409!important; box-shadow:0 12px 26px -10px rgba(84,180,53,.65); transform:translateY(-2px);}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{display:none!important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:4px;}

[data-testid="stSidebar"]{background:var(--surface); border-right:1px solid var(--border);}
[data-testid="stSidebar"] *{color:var(--fg);}

[data-testid="stDataFrame"]{border:1px solid var(--border); border-radius:13px; overflow:hidden;}
[data-testid="stExpander"]{border:1px solid var(--border)!important; border-radius:13px!important;
  background:var(--surface)!important; box-shadow:var(--shadow-sm);}
.stAlert{border-radius:13px!important;}
hr{border-color:var(--border)!important;}
::-webkit-scrollbar{width:9px; height:9px;} ::-webkit-scrollbar-thumb{background:#D6DFCC; border-radius:9px;}

/* offline alert box (simulated ESP32 + OLED + LED + buzzer) */
.aw-device{background:linear-gradient(180deg,#1b2430,#0f1722); border-radius:18px; padding:15px;
  border:1px solid #2a3950; box-shadow:var(--shadow); max-width:340px;}
.aw-dev-top{display:flex; justify-content:space-between; align-items:center; color:#9fb0c4;
  font-size:.68rem; font-family:'JetBrains Mono',monospace; margin-bottom:11px;}
.aw-dev-led{width:14px;height:14px;border-radius:999px; box-shadow:0 0 12px 2px currentColor;}
.aw-oled{background:#04130b; border:1px solid #13241a; border-radius:10px; padding:14px;
  min-height:74px; box-shadow:inset 0 0 18px rgba(0,255,120,.06);}
.aw-oled .ol1{font-family:'JetBrains Mono',monospace; font-weight:700; font-size:.98rem; line-height:1.3;
  display:flex; gap:7px; align-items:center;}
.aw-oled .ol2{font-family:'JetBrains Mono',monospace; font-size:.8rem; opacity:.95; margin-top:5px;}
.aw-dev-bot{color:#9fb0c4; font-size:.72rem; margin-top:11px; font-family:'JetBrains Mono',monospace;}

/* SMS thread (feature phone) */
.aw-phone{background:#e7e0d8; border-radius:16px; padding:12px; border:1px solid var(--border);}
.aw-sms{display:flex; flex-direction:column; gap:8px;}
.aw-bub{max-width:88%; padding:9px 13px; border-radius:14px; font-size:.9rem; line-height:1.35;
  white-space:pre-line; box-shadow:0 1px 2px rgba(0,0,0,.08);}
.aw-bub.out{align-self:flex-end; background:#d6f5c2; color:#13280c; border-bottom-right-radius:4px;}
.aw-bub.in{align-self:flex-start; background:#fff; color:#1b2a1f; border-bottom-left-radius:4px;}
.aw-bub .who{display:block; font-size:.64rem; color:var(--faint); margin-bottom:2px;
  font-family:'JetBrains Mono',monospace;}

/* accessibility: visible keyboard focus on all interactive elements */
.stButton > button:focus-visible, .stTabs [data-baseweb="tab"]:focus-visible,
[data-testid="stSidebar"] *:focus-visible, a:focus-visible, summary:focus-visible,
input:focus-visible, select:focus-visible, textarea:focus-visible,
[role="radio"]:focus-visible, [role="tab"]:focus-visible{
  outline:3px solid var(--brand-strong)!important; outline-offset:2px!important;
  border-radius:8px;
}
.aw-step .tx a, .aw-footer a{text-decoration:underline;}   /* links not colour-only */
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
    state = "live" if live else "mock"
    return (f'<span class="aw-pill {cls}" role="status" aria-label="{html.escape(text)} ({state})">'
            f'<span class="dot" aria-hidden="true"></span>{html.escape(text)}</span>')


def topbar(title: str, subtitle: str, date_label: str, alerts: int = 0) -> None:
    st.markdown(
        f'<div class="aw-topbar"><div class="t"><h2><span class="aw-logo">{icon("leaf",20)}</span>'
        f'{html.escape(title)}</h2><p>{html.escape(subtitle)}</p></div>'
        f'<div class="aw-chips">'
        f'<span class="aw-chip">{icon("search",15)} Search farm record</span>'
        f'<span class="aw-chip">{icon("sun",15)} {html.escape(date_label)}</span>'
        f'<span class="aw-chip">{icon("bell",15)} Alerts '
        + (f'<span class="nbadge">{alerts}</span>' if alerts else "")
        + '</span></div></div>', unsafe_allow_html=True)


_PLANT_SVG = (
    '<svg width="120" height="96" viewBox="0 0 120 96" fill="none">'
    '<ellipse cx="60" cy="88" rx="42" ry="7" fill="rgba(8,35,10,.12)"/>'
    '<path d="M60 86V44" stroke="#1c4a12" stroke-width="4" stroke-linecap="round"/>'
    '<path d="M60 56C60 56 44 54 38 40c14-2 22 6 22 16Z" fill="#2f7a1d"/>'
    '<path d="M60 50C60 50 76 46 82 32c-14 0-22 8-22 18Z" fill="#3a8f24"/>'
    '<path d="M60 66C60 66 42 66 34 52c14-3 26 4 26 14Z" fill="#43a229"/>'
    '<path d="M60 60C60 60 80 58 88 44c-15 0-28 6-28 16Z" fill="#54b435"/>'
    '<path d="M52 86h16l-3 8H55Z" fill="#b07a3c"/></svg>')


def hero_conditions(gh_id: str, location: str, latest: dict, date_label: str,
                    risk_level: str, risk_kind: str) -> None:
    def _i(v):
        return f"{v:.0f}" if isinstance(v, (int, float)) else "—"
    temp = _i(latest.get("temp_c"))
    hum = _i(latest.get("humidity"))
    lw = _i(latest.get("leaf_wetness_hr"))
    trap = latest.get("trap_count", "—")
    risk_color = {"HIGH": "#E5484D", "MED": "#E8A317"}.get(risk_level, "#54B435")
    risk_text = {"HIGH": "HIGH blight risk", "MED": "Moderate risk"}.get(risk_level, "Conditions normal")
    _h = latest.get("humidity")
    cond = "Cloudy · humid" if isinstance(_h, (int, float)) and _h >= 85 else "Mild · clear"

    def mini(ic, label, val):
        return (f'<div class="m"><div class="ml">{icon(ic,13)} {label}</div>'
                f'<div class="mv">{val}</div></div>')

    st.markdown(
        f'<div class="aw-hero">'
        f'<div class="h-top"><span class="h-loc">{icon("leaf",18)} Greenhouse {html.escape(gh_id)} · '
        f'{html.escape(location)}</span><span class="h-date">{html.escape(date_label)}</span></div>'
        f'<div class="h-temp">{temp}°C</div>'
        f'<div class="h-cond">{cond} · live sensor feed</div>'
        f'<div class="h-status"><span class="dot" style="background:{risk_color}"></span>{risk_text}</div>'
        f'<div class="aw-plant">{_PLANT_SVG}</div>'
        f'<div class="h-mini">'
        + mini("drop", "Humidity", f"{hum}%")
        + mini("thermo", "Air temp", f"{temp}°C")
        + mini("sun", "Leaf wet", f"{lw}h")
        + mini("bug", "Pest trap", f"{trap}")
        + '</div></div>', unsafe_allow_html=True)


def section(title: str, subtitle: str = "", ic: str = "activity") -> None:
    st.markdown(
        f'<div class="aw-section"><span class="ic">{icon(ic,18)}</span>'
        f'<div><h3>{html.escape(title)}</h3>'
        + (f'<p>{html.escape(subtitle)}</p>' if subtitle else "")
        + '</div></div>', unsafe_allow_html=True)


def kpis(items: list[dict]) -> None:
    cards = ""
    for it in items:
        cls = "fill" if it.get("tone") == "fill" else ""
        ic = f'{icon(it["icon"],13)} ' if it.get("icon") else ""
        cards += (f'<div class="aw-kpi {cls}">'
                  f'<div class="k-label">{ic}{html.escape(str(it["label"]))}</div>'
                  f'<div class="k-val">{html.escape(str(it["value"]))}</div>'
                  f'<div class="k-sub">{html.escape(str(it.get("sub","")))}</div></div>')
    st.markdown(f'<div class="aw-kpis">{cards}</div>', unsafe_allow_html=True)


def gauge(value: float, label: str, sub: str = "", maximum: float = 100.0,
          suffix: str = "") -> str:
    r, cx, cy = 52, 64, 64
    circ = 2 * math.pi * r
    frac = max(0, min(1, value / maximum))
    dash = circ * frac
    return (
        f'<div class="aw-gauge"><svg width="128" height="128" viewBox="0 0 128 128">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#EEF3E8" stroke-width="13"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#gg)" stroke-width="13" '
        f'stroke-linecap="round" stroke-dasharray="{dash:.1f} {circ:.1f}" '
        f'transform="rotate(-90 {cx} {cy})"/>'
        f'<defs><linearGradient id="gg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#8FD64E"/><stop offset="1" stop-color="#3F9E2A"/>'
        f'</linearGradient></defs>'
        f'<text x="{cx}" y="{cy-2}" text-anchor="middle" font-family="Plus Jakarta Sans" '
        f'font-size="26" font-weight="800" fill="#1B2A1F">{value:.0f}{suffix}</text>'
        f'<text x="{cx}" y="{cy+18}" text-anchor="middle" font-family="Inter" font-size="10" '
        f'fill="#6E7D70">of {maximum:.0f}</text></svg>'
        f'<div class="g-meta"><div class="gl">{html.escape(label)}</div>'
        f'<div class="gv">{value:.0f}{suffix}</div>'
        + (f'<div class="gs">{html.escape(sub)}</div>' if sub else "")
        + '</div></div>')


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
        proof_html = pill(s["mode"]) + (
            f' <span class="aw-muted" style="font-size:.72rem">{html.escape(proof)}</span>'
            if proof and proof not in ("—", "simulated") else "")
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


def flow_steps(steps: list[tuple[str, str]], vertical: bool = False) -> None:
    cells = ""
    for i, (label, state) in enumerate(steps, 1):
        mark = icon("check", 14) if state == "done" else str(i)
        cells += (f'<div class="aw-fstep {state}"><span class="n">{mark}</span>'
                  f'<span class="l">{html.escape(label)}</span></div>')
    cls = "aw-flow aw-flow-v" if vertical else "aw-flow"
    st.markdown(f'<div class="{cls}">{cells}</div>', unsafe_allow_html=True)


def feed_chart(df):
    """Light green/amber line chart of humidity + air temp over recent readings."""
    data = (df[["humidity", "temp_c"]]
            .rename(columns={"humidity": "Humidity %", "temp_c": "Air temp °C"})
            .reset_index(drop=True))
    data.index.name = "reading"
    st.line_chart(data, color=["#54B435", "#E8A317"], height=240, use_container_width=True)


def yield_bars(seasons: list[int], yields: list[float]):
    """Green gradient bar chart of harvest yields per season (GoAgri-style)."""
    import pandas as pd
    data = pd.DataFrame({"Season": [f"S{s}" for s in seasons], "Yield (kg)": yields}).set_index("Season")
    st.bar_chart(data, color="#54B435", height=220, use_container_width=True)


def footer() -> None:
    st.markdown(
        '<div class="aw-footer"><span>Angawatch · Kenya AI Challenge — AgriFin track + '
        'Masumi Business-Agent bounty</span>'
        '<span class="aw-pill live"><span class="dot"></span>Deterministic core · '
        'labeled mocks · human-in-the-loop</span></div>', unsafe_allow_html=True)


def offline_device(box: dict) -> str:
    color = box["led"]
    return (f'<div class="aw-device"><div class="aw-dev-top">'
            f'<span>ESP32 · OLED · ESP-NOW (no internet)</span>'
            f'<span class="aw-dev-led" style="background:{color};color:{color}"></span></div>'
            f'<div class="aw-oled"><div class="ol1" style="color:{color}">{icon(box["icon"],16)} '
            f'{html.escape(box["line1"])}</div>'
            f'<div class="ol2" style="color:{color}">{html.escape(box["line2"])}</div></div>'
            f'<div class="aw-dev-bot">🔊 buzzer: {html.escape(box["buzzer"])} &nbsp;·&nbsp; '
            f'LED {html.escape(box["level"])}</div></div>')


def sms_thread(messages: list[tuple[str, str, str]]) -> str:
    """messages = [(who, side, text)] where side in {'in','out'}."""
    bubs = "".join(
        f'<div class="aw-bub {side}"><span class="who">{html.escape(who)}</span>'
        f'{html.escape(text)}</div>' for who, side, text in messages)
    return f'<div class="aw-phone"><div class="aw-sms">{bubs}</div></div>'


def alert_card(level: str, kind: str, message: str, delivery: str, provider: str) -> None:
    cls = "high" if level == "HIGH" else "med"
    st.markdown(
        f'<div class="aw-alert {cls}"><span class="ai">{icon("alert",22)}</span><div>'
        f'<div class="at">{html.escape(kind)} · {level} '
        f'<span class="aw-muted" style="font-size:.74rem;font-weight:500">'
        f'{html.escape(delivery.upper())} via {html.escape(provider)}</span></div>'
        f'<div class="am">{html.escape(message)}</div></div></div>', unsafe_allow_html=True)
