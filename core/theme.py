"""Fantasy "spellbook" look for the app: a parchment light mode and a
starry-night dark mode. Pure strings and dicts, no Streamlit calls.

Colours are kept colour-blind safe (blue / gold / ember differ in lightness)
and every coloured element also carries an icon or a text label.
"""
from __future__ import annotations

FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700"
    "&family=Chonburi&family=Trirong:wght@400;600&display=swap"
)

PALETTES = {
    "light": {  # aged parchment, ink and candle gold
        "bg": "#f3e9d2", "surface": "#fbf5e6", "surface2": "#fffaf0",
        "ink": "#2a1c0f", "muted": "#6b5639", "line": "#c9ad7a",
        "gold": "#9a6b12", "accent": "#7b2d26", "accent_ink": "#fff6e0",
        "avoid": "#b4400f", "avoid_bg": "#fbe3d3", "ok": "#1f5f8b", "ok_bg": "#e1edf6",
        "sidebar": "linear-gradient(180deg,#5a2a20 0%,#3d1c16 100%)",
        "sidebar_ink": "#f6e7c4",
        "app_bg": ("radial-gradient(ellipse at top,#fdf6e3 0%,transparent 60%),"
                   "radial-gradient(ellipse at bottom right,rgba(154,107,18,.18),transparent 55%),"
                   "#f3e9d2"),
    },
    "dark": {  # night sky over a castle library
        "bg": "#0f0d17", "surface": "#1d1a2b", "surface2": "#262238",
        "ink": "#efe5cc", "muted": "#b7a785", "line": "#4a3f63",
        "gold": "#e2b857", "accent": "#9b6bd3", "accent_ink": "#120f1c",
        "avoid": "#ff9d6b", "avoid_bg": "#3a1d14", "ok": "#7cc4f5", "ok_bg": "#13283a",
        "sidebar": "linear-gradient(180deg,#1b1630 0%,#0c0a14 100%)",
        "sidebar_ink": "#efe5cc",
        "app_bg": ("radial-gradient(1px 1px at 12% 18%,#fff 50%,transparent 51%),"
                   "radial-gradient(1px 1px at 72% 9%,#fff 50%,transparent 51%),"
                   "radial-gradient(1.5px 1.5px at 38% 62%,#ffe9a8 50%,transparent 51%),"
                   "radial-gradient(1px 1px at 88% 44%,#fff 50%,transparent 51%),"
                   "radial-gradient(1px 1px at 55% 85%,#fff 50%,transparent 51%),"
                   "radial-gradient(1.5px 1.5px at 6% 78%,#cdb6ff 50%,transparent 51%),"
                   "radial-gradient(ellipse at top,rgba(155,107,211,.25),transparent 60%),"
                   "#0f0d17"),
    },
}

# Chart series per mode: protein / carbohydrate / fat (or actual / target).
SERIES = {
    "light": ["#1f5f8b", "#b8860b", "#7b2d26"],
    "dark": ["#7cc4f5", "#e2b857", "#e07a6a"],
}

_STATIC_CSS = """
.stApp { background: var(--app-bg); background-attachment: fixed; color: var(--ink);
         font-family: 'Trirong', serif; }
[data-testid="stHeader"] { background: transparent; }
.stApp p, .stApp li, .stApp label, .stApp td, .stApp th,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stMetricLabel"],
.stApp [data-testid="stExpander"] summary, .stApp [data-testid="stText"] {
    color: var(--ink); font-family: 'Trirong', serif; }
.stApp [data-testid="stCaptionContainer"] { color: var(--muted); }
.stApp h1, .stApp h2, .stApp h3 {
    font-family: 'Cinzel Decorative', 'Chonburi', serif; color: var(--gold);
    letter-spacing: .02em; text-shadow: 0 1px 0 rgba(0,0,0,.15); }
.stApp h1 { border-bottom: 2px solid var(--line); padding-bottom: .4rem; }
.stApp h1::after { content: " ✦"; font-size: .6em; vertical-align: middle; }
[data-testid="stMetricValue"] { color: var(--gold); font-family: 'Chonburi', serif; }

/* Sidebar: leather-bound quest book */
[data-testid="stSidebar"] > div:first-child { background: var(--sidebar); }
.stApp [data-testid="stSidebar"] p, .stApp [data-testid="stSidebar"] label,
.stApp [data-testid="stSidebar"] span, .stApp [data-testid="stSidebar"] div,
.stApp [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
.stApp [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--sidebar-ink) !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { opacity: .8; }
.brand { font-family: 'Cinzel Decorative','Chonburi',serif; font-size: 1.25rem;
         text-align: center; padding: .4rem 0 .6rem; border-bottom: 1px solid rgba(226,184,87,.5);
         margin-bottom: .6rem; color: #e2b857 !important; }
.quest-title { font-family: 'Chonburi', serif; font-size: 1.05rem; margin: .6rem 0 .3rem;
               color: #e2b857 !important; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    border: 2px solid rgba(226,184,87,.55); border-left: 6px solid #e2b857;
    border-radius: .6rem; padding: .55rem .7rem; margin: .28rem 0;
    background: rgba(255,255,255,.06); min-height: 2.9rem; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover { background: rgba(226,184,87,.18); }
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
[data-testid="stSidebar"] [data-testid="stPageLink"] a[data-active="true"] {
    background: rgba(226,184,87,.28); }
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
    min-height: 3rem; font-size: 1.05rem; width: 100%; font-family: 'Chonburi', serif;
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
    box-shadow: 0 2px 10px rgba(0,0,0,.08); }
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
    root = ";".join(f"--{names.get(k, k)}:{v}" for k, v in p.items())
    return (f'<style>@import url("{FONTS_URL}");'
            f":root{{{root}}}{_STATIC_CSS}</style>")


def chart_layout(dark: bool) -> dict:
    """Plotly layout values matching the mode (transparent paper, themed text)."""
    p = PALETTES["dark" if dark else "light"]
    return {
        "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Trirong, serif", "color": p["ink"]},
        "title_font": {"family": "Chonburi, serif", "color": p["gold"]},
        "xaxis": {"gridcolor": p["line"], "linecolor": p["line"]},
        "yaxis": {"gridcolor": p["line"], "linecolor": p["line"]},
    }
