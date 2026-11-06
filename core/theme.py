"""Emo / gothic-rock look for the app: a black "midnight stage" dark mode and a
bone-paper "daylight" mode, with film grain, flicker and a scratch line.
Inspired by the general emo-punk style only: no band names, logos or lyrics.
Pure strings and dicts, no Streamlit calls.

Colours are kept colour-blind safe: warnings are amber (not the brand red)
and every coloured element also carries an icon or a text label.
"""
from __future__ import annotations

FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Special+Elite"
    "&family=Kanit:wght@500;700&family=Sarabun:wght@400;600&display=swap"
)

_SIDEBAR = ("repeating-linear-gradient(180deg,rgba(230,57,70,.06) 0 2px,transparent 2px 9px),"
            "linear-gradient(180deg,#151015 0%,#050505 100%)")

PALETTES = {
    "light": {  # daylight: bone paper, black ink, deep red
        "bg": "#efebe4", "surface": "rgba(255,253,249,.88)", "surface2": "#fbf9f5",
        "ink": "#121012", "muted": "#5e5659", "line": "#bdb3ab",
        "gold": "#a4161a", "accent": "#121012", "accent_ink": "#f6f2ec",
        "avoid": "#b45309", "avoid_bg": "#fdecd2", "ok": "#1d4e89", "ok_bg": "#e2ebf6",
        "sidebar": _SIDEBAR, "sidebar_ink": "#efe9e1",
        "grain": "rgba(0,0,0,.06)",
        "app_bg": ("radial-gradient(ellipse at center,transparent 55%,rgba(60,40,40,.18) 100%),"
                   "radial-gradient(ellipse 50% 35% at 85% 5%,rgba(164,22,26,.10),transparent 70%),"
                   "#efebe4"),
    },
    "dark": {  # midnight stage: black, bone white, blood red spotlight
        "bg": "#0a090b", "surface": "rgba(22,19,22,.86)", "surface2": "#1b171b",
        "ink": "#ece7e0", "muted": "#a39b9d", "line": "#3d3539",
        "gold": "#e63946", "accent": "#e63946", "accent_ink": "#0a090b",
        "avoid": "#ffb703", "avoid_bg": "#3a2a08", "ok": "#8ecae6", "ok_bg": "#10283a",
        "sidebar": _SIDEBAR, "sidebar_ink": "#ece7e0",
        "grain": "rgba(255,255,255,.05)",
        "app_bg": ("radial-gradient(ellipse 45% 35% at 50% -5%,rgba(230,57,70,.28),transparent 75%),"
                   "radial-gradient(ellipse at center,transparent 50%,rgba(0,0,0,.75) 100%),"
                   "#0a090b"),
    },
}

# Chart series per mode: protein / carbohydrate / fat (or actual / target).
SERIES = {
    "light": ["#1d4e89", "#6b6461", "#a4161a"],
    "dark": ["#8ecae6", "#e9e4dc", "#e63946"],
}

# Film grain: a fine dot pattern drawn on a fixed layer over the background.
_STAR_LAYER = ("radial-gradient(var(--grain) 1px,transparent 1.2px) 0 0/3px 3px,"
               "radial-gradient(var(--grain) 1px,transparent 1.2px) 1px 2px/5px 5px")

_STATIC_CSS = """
.stApp { background: var(--app-bg); background-attachment: fixed; color: var(--ink);
         font-family: 'Sarabun', sans-serif; }
[data-testid="stHeader"] { background: transparent; }
.stApp p, .stApp li, .stApp label, .stApp td, .stApp th,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stMetricLabel"],
.stApp [data-testid="stExpander"] summary, .stApp [data-testid="stText"] {
    color: var(--ink); font-family: 'Sarabun', sans-serif; }
.stApp [data-testid="stCaptionContainer"] { color: var(--muted); }
.stApp h1, .stApp h2, .stApp h3 {
    font-family: 'Special Elite', 'Kanit', sans-serif; color: var(--gold); font-weight: 700;
    letter-spacing: .03em; text-transform: uppercase; }
.stApp h1 { color: var(--ink); border-bottom: 3px double var(--gold); padding-bottom: .4rem;
            text-shadow: 2px 2px 0 var(--gold), 0 0 24px rgba(230,57,70,.35);
            animation: flicker 7s infinite; }
.stApp h1::after { content: " 🥀"; font-size: .55em; vertical-align: middle; text-shadow: none; }
@keyframes flicker { 0%, 92%, 96%, 100% { opacity: 1; } 93% { opacity: .55; } 95% { opacity: .8; } }

/* Film grain layer + an old-film scratch line sweeping down the screen */
.stApp::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background: var(--star-layer); animation: grain 1.2s steps(3) infinite; }
.stApp::after { content: ""; position: fixed; left: 0; right: 0; top: -5%; height: 2px;
    pointer-events: none; z-index: 0; opacity: 0;
    background: linear-gradient(90deg, transparent, rgba(230,57,70,.7), transparent);
    animation: scratch 9s linear infinite 2s; }
@keyframes grain { 0% { transform: translate(0,0); } 33% { transform: translate(-1px,1px); }
    66% { transform: translate(1px,-1px); } 100% { transform: translate(0,0); } }
@keyframes scratch { 0% { top: -5%; opacity: 0; } 2% { opacity: .9; }
    14% { top: 105%; opacity: 0; } 100% { top: 105%; opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .stApp::before, .stApp::after, .stApp h1 { animation: none; } }
[data-testid="stMain"], [data-testid="stSidebar"] { position: relative; z-index: 1; }

/* Tagline under each page title, typed like a torn set-list */
.spell { font-family: 'Special Elite', monospace; font-size: 1.05rem; color: var(--gold);
    margin: -.3rem 0 .8rem; letter-spacing: .08em; text-transform: uppercase; }
.spell small { font-family: 'Sarabun', sans-serif; text-transform: none; color: var(--muted);
    letter-spacing: 0; margin-left: .4rem; }
[data-testid="stMetricValue"] { color: var(--gold); font-family: 'Kanit', sans-serif; }

/* Sidebar: black set-list of quests */
[data-testid="stSidebar"] > div:first-child { background: var(--sidebar); }
.stApp [data-testid="stSidebar"] p, .stApp [data-testid="stSidebar"] label,
.stApp [data-testid="stSidebar"] span, .stApp [data-testid="stSidebar"] div,
.stApp [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
.stApp [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--sidebar-ink) !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { opacity: .8; }
.brand { font-family: 'Special Elite','Kanit',sans-serif; font-size: 1.25rem;
         text-align: center; padding: .4rem 0 .6rem; border-bottom: 1px solid rgba(230,57,70,.5);
         margin-bottom: .6rem; color: #e63946 !important; }
.quest-title { font-family: 'Kanit', sans-serif; font-size: 1.05rem; margin: .6rem 0 .3rem;
               color: #e63946 !important; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    border: 2px solid rgba(230,57,70,.55); border-left: 6px solid #e63946;
    border-radius: .6rem; padding: .55rem .7rem; margin: .28rem 0;
    background: rgba(255,255,255,.06); min-height: 2.9rem;
    box-shadow: 0 0 10px rgba(230,57,70,.25); transition: box-shadow .2s, background .2s; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover { background: rgba(230,57,70,.18);
    box-shadow: 0 0 16px rgba(230,57,70,.55); }
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
[data-testid="stSidebar"] [data-testid="stPageLink"] a[data-active="true"] {
    background: rgba(230,57,70,.28); }
[data-testid="stSidebar"] [data-testid="stPageLink"] p { font-size: 1rem; font-weight: 600; }
.quest-done p { text-decoration: line-through; opacity: .75; }

/* Inputs */
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"],
.stApp [data-baseweb="select"] > div, .stApp [data-baseweb="textarea"],
.stApp [data-testid="stTextInputRootElement"], .stApp div:has(> input:not([type="checkbox"]):not([type="radio"])),
.stApp div:has(> textarea), .stApp [data-testid="stSelectbox"] div:has(> div > input),
.stApp [data-testid="stMultiSelect"] div:has(> div > input) {
    background: var(--surface2) !important; border-color: var(--line) !important; }
.stApp input, .stApp textarea { color: var(--ink) !important; -webkit-text-fill-color: var(--ink); }
.stApp [data-baseweb="select"] div { color: var(--ink); }
.stApp .stNumberInput button { background: var(--surface) !important; color: var(--ink) !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"] {
    background: var(--surface2) !important; }
[data-baseweb="popover"] li, [role="option"] { color: var(--ink) !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] { background: var(--surface) !important; }

/* Buttons: wax seal with gold rim */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    min-height: 3rem; font-size: 1.05rem; width: 100%; font-family: 'Kanit', sans-serif;
    background: var(--surface); color: var(--ink); border: 2px solid var(--gold);
    border-radius: .8rem; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"],
.stDownloadButton > button[kind="primary"] {
    background: var(--accent); color: var(--accent-ink); border-color: var(--gold);
    box-shadow: 0 0 0 2px rgba(0,0,0,.08), 0 4px 14px rgba(0,0,0,.18); }
.stButton > button:hover, .stFormSubmitButton > button:hover { filter: brightness(1.08);
    border-color: var(--gold); color: inherit; }
.stButton > button:disabled, .stFormSubmitButton > button:disabled { opacity: .5; }

/* Cards: bordered containers, forms, expanders */
.stApp [data-testid="stVerticalBlockBorderWrapper"], .stApp [data-testid="stForm"],
.stApp [data-testid="stMain"] [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"],
.stApp [data-testid="stExpander"] details {
    background: var(--surface); border: 1px solid var(--line) !important; border-radius: .9rem;
    backdrop-filter: blur(6px); box-shadow: 0 4px 24px rgba(0,0,0,.35), inset 0 0 0 1px rgba(255,255,255,.04); }
.stApp [data-testid="stExpander"] details summary:hover { color: var(--gold); }

/* Alerts as scrolls with a coloured edge */
.stApp [data-testid="stAlert"] > div { background: var(--surface2) !important;
    border-left: 6px solid var(--gold); color: var(--ink); }
.stApp [data-testid="stAlert"]:has([data-testid="stAlertContentError"]) > div,
.stApp [data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) > div {
    border-left-color: var(--avoid); }
.stApp [data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) > div { border-left-color: var(--ok); }
.stApp [data-testid="stAlert"] p { color: var(--ink); }

/* Progress bars as golden potion levels */
.stApp [data-testid="stProgress"] [role="progressbar"] > div > div { background: var(--line); }
.stApp [data-testid="stProgress"] [role="progressbar"] > div > div > div {
    background: linear-gradient(90deg, var(--gold), var(--accent)); }

/* Plain HTML tables (st.table) */
.stApp table { background: var(--surface); border-color: var(--line); }
.stApp table th { background: var(--surface2); color: var(--gold); }
.stApp table td, .stApp table th { border-color: var(--line) !important; }

/* Menu tick boxes on the meal plan: chunky to-do rows */
.stApp [data-testid="stMain"] [data-testid="stCheckbox"] label {
    width: 100%; padding: .55rem .7rem; margin-top: .35rem; border-radius: .7rem;
    border: 2px solid var(--line); border-left: 6px solid var(--gold); background: var(--surface2); }
.stApp [data-testid="stMain"] [data-testid="stCheckbox"]:has(input:checked) label {
    background: var(--ok_bg); border-color: var(--ok); }
.stApp [data-testid="stMain"] [data-testid="stCheckbox"]:has(input:checked) p {
    text-decoration: line-through; text-decoration-color: var(--gold); }

/* Save confirmations: a big banner in the slot card and a large toast */
.saved-banner { margin: .6rem 0; padding: .9rem 1.1rem; border-radius: .8rem;
    font-family: 'Kanit', sans-serif; font-size: 1.15rem; border: 3px solid var(--gold);
    box-shadow: 0 0 0 4px rgba(230,57,70,.25), 0 6px 18px rgba(0,0,0,.2);
    animation: saved-pop .5s ease-out, saved-glow 1.6s ease-in-out 2; }
.saved-ok { background: var(--ok_bg); color: var(--ok); border-color: var(--ok); }
.saved-undo { background: var(--surface2); color: var(--ink); }
@keyframes saved-pop { from { transform: scale(.92); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes saved-glow { 50% { box-shadow: 0 0 0 8px rgba(230,57,70,.45), 0 6px 18px rgba(0,0,0,.2); } }
[data-testid="stToast"] { background: var(--accent) !important; border: 3px solid var(--gold) !important;
    border-radius: .9rem !important; box-shadow: 0 8px 28px rgba(0,0,0,.35) !important;
    min-width: 320px; padding: .9rem 1rem !important; }
[data-testid="stToast"] p, [data-testid="stToast"] [data-testid="stMarkdownContainer"] {
    color: var(--accent-ink) !important; font-size: 1.15rem !important;
    font-family: 'Kanit', sans-serif !important; }

hr { border-color: var(--line) !important; }
.chip { display:inline-block; padding:.2rem .65rem; margin:.15rem; border-radius:1rem;
        font-size:.9rem; border:2px solid; }
.chip-avoid { border-color: var(--avoid); color: var(--avoid); background: var(--avoid_bg); }
.chip-ok { border-color: var(--ok); color: var(--ok); background: var(--ok_bg); }
.footer { font-size:.8rem; color: var(--muted); border-top:1px solid var(--line);
          margin-top:2rem; padding-top:.6rem; text-align:center; }
"""


def css(dark: bool) -> str:
    """Full <style> block for the chosen mode."""
    p = PALETTES["dark" if dark else "light"]
    names = {"app_bg": "app-bg", "accent_ink": "accent-ink", "sidebar_ink": "sidebar-ink"}
    root = ";".join(f"--{names.get(k, k)}:{v}" for k, v in p.items()) + f";--star-layer:{_STAR_LAYER}"
    return (f'<style>@import url("{FONTS_URL}");'
            f":root{{{root}}}{_STATIC_CSS}</style>")


def chart_layout(dark: bool) -> dict:
    """Plotly layout values matching the mode (transparent paper, themed text)."""
    p = PALETTES["dark" if dark else "light"]
    return {
        "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Sarabun, sans-serif", "color": p["ink"]},
        "title_font": {"family": "Kanit, sans-serif", "color": p["gold"]},
        "xaxis": {"gridcolor": p["line"], "linecolor": p["line"]},
        "yaxis": {"gridcolor": p["line"], "linecolor": p["line"]},
    }
