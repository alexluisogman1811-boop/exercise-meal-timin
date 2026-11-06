"""Galaxy-magic look for the app: a pastel "cosmic dawn" light mode and a
deep-space nebula dark mode with twinkling stars and a shooting star.
Pure strings and dicts, no Streamlit calls.

Colours are kept colour-blind safe (blue / gold / ember differ in lightness)
and every coloured element also carries an icon or a text label.
"""
from __future__ import annotations

FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700"
    "&family=Chonburi&family=Trirong:wght@400;600&display=swap"
)

PALETTES = {
    "light": {  # cosmic dawn: pastel nebula, indigo ink, star gold
        "bg": "#f4f1ff", "surface": "rgba(255,255,255,.78)", "surface2": "#fbfaff",
        "ink": "#1b1440", "muted": "#5b5384", "line": "#c9c0f0",
        "gold": "#9a6a08", "accent": "#6d28d9", "accent_ink": "#ffffff",
        "avoid": "#b4400f", "avoid_bg": "#fde7dc", "ok": "#1d5fa8", "ok_bg": "#e3eefc",
        "sidebar": ("radial-gradient(1px 1px at 20% 30%,#fff 50%,transparent 51%),"
                    "radial-gradient(1px 1px at 70% 60%,#fff 50%,transparent 51%),"
                    "radial-gradient(1px 1px at 40% 85%,#ffe7a3 50%,transparent 51%),"
                    "linear-gradient(180deg,#2e2178 0%,#16104a 100%)"),
        "sidebar_ink": "#f1edff",
        "stars": "rgba(60,40,140,.55)",
        "app_bg": ("radial-gradient(ellipse 60% 45% at 15% 10%,rgba(196,181,253,.55),transparent 70%),"
                   "radial-gradient(ellipse 50% 40% at 85% 25%,rgba(249,168,212,.45),transparent 70%),"
                   "radial-gradient(ellipse 60% 45% at 60% 95%,rgba(125,211,252,.40),transparent 70%),"
                   "#f4f1ff"),
    },
    "dark": {  # deep space: violet / magenta / cyan nebula clouds
        "bg": "#070616", "surface": "rgba(22,18,52,.72)", "surface2": "#1c1842",
        "ink": "#ece8ff", "muted": "#a9a3d1", "line": "#3f3680",
        "gold": "#f5c96a", "accent": "#8b5cf6", "accent_ink": "#0b0820",
        "avoid": "#ff9f7a", "avoid_bg": "#3b1724", "ok": "#67d4ff", "ok_bg": "#0f2a44",
        "sidebar": ("radial-gradient(1px 1px at 20% 30%,#fff 50%,transparent 51%),"
                    "radial-gradient(1px 1px at 70% 60%,#fff 50%,transparent 51%),"
                    "radial-gradient(1.5px 1.5px at 40% 85%,#ffe7a3 50%,transparent 51%),"
                    "linear-gradient(180deg,#140f36 0%,#05040f 100%)"),
        "sidebar_ink": "#ece8ff",
        "stars": "rgba(255,255,255,.9)",
        "app_bg": ("radial-gradient(ellipse 55% 40% at 18% 15%,rgba(139,92,246,.40),transparent 70%),"
                   "radial-gradient(ellipse 45% 35% at 85% 30%,rgba(236,72,153,.28),transparent 70%),"
                   "radial-gradient(ellipse 60% 40% at 50% 100%,rgba(56,189,248,.22),transparent 70%),"
                   "#070616"),
    },
}

# Chart series per mode: protein / carbohydrate / fat (or actual / target).
SERIES = {
    "light": ["#1d5fa8", "#a0700d", "#be185d"],
    "dark": ["#67d4ff", "#f5c96a", "#f472b6"],
}

# Star field drawn on a fixed layer above the background (twinkles via CSS).
_STAR_LAYER = ",".join(
    f"radial-gradient({s}px {s}px at {x}% {y}%,var(--stars) 50%,transparent 51%)"
    for x, y, s in [(8, 12, 1), (23, 40, 1.5), (37, 8, 1), (52, 27, 1), (66, 14, 2), (81, 36, 1),
                    (93, 9, 1.5), (14, 66, 1), (29, 83, 2), (45, 58, 1), (59, 76, 1.5), (73, 62, 1),
                    (88, 81, 1), (96, 55, 2), (5, 92, 1.5), (41, 95, 1), (77, 94, 1.5), (61, 45, 1)]
)

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
    letter-spacing: .02em; text-shadow: 0 0 12px rgba(245,201,106,.35); }
.stApp h1 { border-bottom: 2px solid var(--line); padding-bottom: .4rem;
            text-shadow: 0 0 18px rgba(245,201,106,.5), 0 0 40px rgba(139,92,246,.35); }
.stApp h1::after { content: " ✧˖°"; font-size: .55em; vertical-align: middle; }

/* Twinkling star field + a shooting star, drawn above the nebula, below the content */
.stApp::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background: var(--star-layer); animation: twinkle 5s ease-in-out infinite alternate; }
.stApp::after { content: ""; position: fixed; top: 12%; left: -15%; width: 140px; height: 2px;
    pointer-events: none; z-index: 0; border-radius: 2px; opacity: 0;
    background: linear-gradient(90deg, transparent, var(--gold), #fff);
    transform: rotate(18deg); animation: shooting 11s linear infinite 3s; }
@keyframes twinkle { 0% { opacity: .35; } 50% { opacity: 1; } 100% { opacity: .55; } }
@keyframes shooting { 0% { left: -15%; top: 8%; opacity: 0; } 3% { opacity: 1; }
    12% { left: 110%; top: 38%; opacity: 0; } 100% { left: 110%; top: 38%; opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .stApp::before, .stApp::after { animation: none; } }
[data-testid="stMain"], [data-testid="stSidebar"] { position: relative; z-index: 1; }

/* Spell incantation under each page title */
.spell { font-family: 'Cinzel Decorative', serif; font-style: italic; font-size: 1.05rem;
    color: var(--gold); margin: -.3rem 0 .8rem; letter-spacing: .06em;
    animation: spell-glow 3s ease-in-out infinite; }
.spell small { font-family: 'Trirong', serif; font-style: normal; color: var(--muted);
    letter-spacing: 0; margin-left: .4rem; }
@keyframes spell-glow { 50% { text-shadow: 0 0 10px rgba(245,201,106,.8), 0 0 22px rgba(139,92,246,.6); } }
[data-testid="stMetricValue"] { color: var(--gold); font-family: 'Chonburi', serif; }

/* Sidebar: star chart of quests */
[data-testid="stSidebar"] > div:first-child { background: var(--sidebar); }
.stApp [data-testid="stSidebar"] p, .stApp [data-testid="stSidebar"] label,
.stApp [data-testid="stSidebar"] span, .stApp [data-testid="stSidebar"] div,
.stApp [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
.stApp [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--sidebar-ink) !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { opacity: .8; }
.brand { font-family: 'Cinzel Decorative','Chonburi',serif; font-size: 1.25rem;
         text-align: center; padding: .4rem 0 .6rem; border-bottom: 1px solid rgba(245,201,106,.5);
         margin-bottom: .6rem; color: #f5c96a !important; }
.quest-title { font-family: 'Chonburi', serif; font-size: 1.05rem; margin: .6rem 0 .3rem;
               color: #f5c96a !important; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    border: 2px solid rgba(245,201,106,.55); border-left: 6px solid #f5c96a;
    border-radius: .6rem; padding: .55rem .7rem; margin: .28rem 0;
    background: rgba(255,255,255,.06); min-height: 2.9rem;
    box-shadow: 0 0 10px rgba(139,92,246,.25); transition: box-shadow .2s, background .2s; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover { background: rgba(245,201,106,.18);
    box-shadow: 0 0 16px rgba(245,201,106,.55); }
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"],
[data-testid="stSidebar"] [data-testid="stPageLink"] a[data-active="true"] {
    background: rgba(245,201,106,.28); }
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
    backdrop-filter: blur(6px); box-shadow: 0 4px 24px rgba(76,29,149,.18), inset 0 0 0 1px rgba(255,255,255,.04); }
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
    font-family: 'Chonburi', serif; font-size: 1.15rem; border: 3px solid var(--gold);
    box-shadow: 0 0 0 4px rgba(245,201,106,.25), 0 6px 18px rgba(0,0,0,.2);
    animation: saved-pop .5s ease-out, saved-glow 1.6s ease-in-out 2; }
.saved-ok { background: var(--ok_bg); color: var(--ok); border-color: var(--ok); }
.saved-undo { background: var(--surface2); color: var(--ink); }
@keyframes saved-pop { from { transform: scale(.92); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes saved-glow { 50% { box-shadow: 0 0 0 8px rgba(245,201,106,.45), 0 6px 18px rgba(0,0,0,.2); } }
[data-testid="stToast"] { background: var(--accent) !important; border: 3px solid var(--gold) !important;
    border-radius: .9rem !important; box-shadow: 0 8px 28px rgba(0,0,0,.35) !important;
    min-width: 320px; padding: .9rem 1rem !important; }
[data-testid="stToast"] p, [data-testid="stToast"] [data-testid="stMarkdownContainer"] {
    color: var(--accent-ink) !important; font-size: 1.15rem !important;
    font-family: 'Chonburi', serif !important; }

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
        "font": {"family": "Trirong, serif", "color": p["ink"]},
        "title_font": {"family": "Chonburi, serif", "color": p["gold"]},
        "xaxis": {"gridcolor": p["line"], "linecolor": p["line"]},
        "yaxis": {"gridcolor": p["line"], "linecolor": p["line"]},
    }
