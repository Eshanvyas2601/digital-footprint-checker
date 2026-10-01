import os
import base64
import threading
import textwrap
from datetime import datetime
from html import escape
from urllib.parse import quote
import streamlit as st
from serpapi_client import search_text, search_reverse_image, build_targeted_query, upload_image_temp, multi_query_search
from evidence_engine import build_evidence_list
from identity_clustering import cluster_identities
from risk_scorer import calculate_risk
from analyzer import generate_narrative
from pdf_generator import generate_pdf_report
from demo_data import get_demo_results
 
st.set_page_config(page_title="DigitalTrace - Footprint Checker", page_icon="🔍", layout="wide")
 
DISCLAIMER = (
    "DigitalTrace does not determine whether a person is a scammer or a threat. "
    "It identifies publicly observable signals — such as conflicting profiles or "
    "reused images — that may warrant further verification. Always confirm identity "
    "through an independent, trusted channel before acting on this report."
)
 
DEMO_NOTICE = (
    "<strong>DEMO MODE — FABRICATED DATA.</strong> The names, profiles, and links in this report are entirely "
    "fabricated. Real identities cannot be shown in this demonstration for privacy reasons. "
    "Any resemblance to a real person is coincidental."
)
 
BANNER_PATH = "assets/banner.png"
 
# (query_source key from the backend, label shown, icon). GitHub has no dedicated query source,
# so it is detected from result URLs instead (see render_platform_presence).
PLATFORM_DISPLAY = [
    ("LinkedIn", "LinkedIn", "linkedin"),
    ("Instagram", "Instagram", "instagram"),
    ("Facebook", "Facebook", "facebook"),
    ("GitHub", "GitHub", "github"),
    ("News/Articles", "News", "doc"),
    ("Other/General", "Web", "web"),
]
 
PLACEHOLDERS = {
    "Name": "Enter a full name",
    "Email": "Enter an email address",
    "Phone": "Enter a phone number",
}
 
if "history" not in st.session_state:
    st.session_state.history = []
 
 
# ----------------------------------------------------------------------------
# Icons
# ----------------------------------------------------------------------------
ICONS = {
    "linkedin": ("<path d='M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z'/>", "fill"),
    "facebook": ("<path d='M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z'/>", "fill"),
    "github": ("<path d='M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12'/>", "fill"),
    "instagram": ("<rect x='2' y='2' width='20' height='20' rx='5' ry='5'/><path d='M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z'/><line x1='17.5' y1='6.5' x2='17.51' y2='6.5'/>", "stroke"),
    "web": ("<circle cx='12' cy='12' r='10'/><line x1='2' y1='12' x2='22' y2='12'/><path d='M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z'/>", "stroke"),
    "doc": ("<path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><polyline points='14 2 14 8 20 8'/><line x1='16' y1='13' x2='8' y2='13'/><line x1='16' y1='17' x2='8' y2='17'/>", "stroke"),
    "image": ("<rect x='3' y='3' width='18' height='18' rx='2' ry='2'/><circle cx='8.5' cy='8.5' r='1.5'/><polyline points='21 15 16 10 5 21'/>", "stroke"),
    "email": ("<path d='M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z'/><polyline points='22,6 12,13 2,6'/>", "stroke"),
    "phone": ("<path d='M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z'/>", "stroke"),
    "user": ("<path d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/><circle cx='12' cy='7' r='4'/>", "stroke"),
    "search": ("<circle cx='11' cy='11' r='8'/><line x1='21' y1='21' x2='16.65' y2='16.65'/>", "stroke"),
    "lock": ("<rect x='3' y='11' width='18' height='11' rx='2' ry='2'/><path d='M7 11V7a5 5 0 0 1 10 0v4'/>", "stroke"),
    "layers": ("<polygon points='12 2 2 7 12 12 22 7 12 2'/><polyline points='2 17 12 22 22 17'/><polyline points='2 12 12 17 22 12'/>", "stroke"),
    "sliders": ("<line x1='4' y1='21' x2='4' y2='14'/><line x1='4' y1='10' x2='4' y2='3'/><line x1='12' y1='21' x2='12' y2='12'/><line x1='12' y1='8' x2='12' y2='3'/><line x1='20' y1='21' x2='20' y2='16'/><line x1='20' y1='12' x2='20' y2='3'/><line x1='1' y1='14' x2='7' y2='14'/><line x1='9' y1='8' x2='15' y2='8'/><line x1='17' y1='16' x2='23' y2='16'/>", "stroke"),
    "flag": ("<path d='M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z'/><line x1='4' y1='22' x2='4' y2='15'/>", "stroke"),
    "check": ("<path d='M22 11.08V12a10 10 0 1 1-5.93-9.14'/><polyline points='22 4 12 14.01 9 11.01'/>", "stroke"),
    "alert": ("<path d='M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z'/><line x1='12' y1='9' x2='12' y2='13'/><line x1='12' y1='17' x2='12.01' y2='17'/>", "stroke"),
    "info": ("<circle cx='12' cy='12' r='10'/><line x1='12' y1='16' x2='12' y2='12'/><line x1='12' y1='8' x2='12.01' y2='8'/>", "stroke"),
}
 
 
def icon(name, size=18):
    inner, mode = ICONS[name]
    if mode == "fill":
        attrs = "fill='currentColor'"
    else:
        attrs = "fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'"
    return (
        f"<svg class='dt-ico' width='{size}' height='{size}' viewBox='0 0 24 24' {attrs} "
        f"xmlns='http://www.w3.org/2000/svg'>{inner}</svg>"
    )
 
 
def _svg_uri(name, stroke="#000000"):
    """Data-URI version of a stroke icon, used from CSS (search-bar icon, pill icons)."""
    inner, _ = ICONS[name]
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
        f"stroke='{stroke}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{inner}</svg>"
    )
    return 'url("data:image/svg+xml;utf8,' + quote(svg) + '")'
 
 
# ----------------------------------------------------------------------------
# HTML helper — this is the fix for the raw <div> code showing on screen.
# Markdown treats any line indented 4+ spaces as a code block, and f-string
# fragments joined together end up with mixed indentation. Stripping every line
# and dropping blank lines guarantees the HTML is parsed as HTML.
# ----------------------------------------------------------------------------
def render_html(markup: str):
    cleaned = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)
 
 
def _log(step):
    """Prints progress to the terminal so we can see exactly where a scan stops."""
    print(f"[DigitalTrace] {step}", flush=True)
 
 
def _get_banner_base64():
    if not os.path.exists(BANNER_PATH):
        return None
    with open(BANNER_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()
 
 
# ----------------------------------------------------------------------------
# Theme
# ----------------------------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
 
:root {
    --dt-text: #e6eaf5;
    --dt-muted: #8b93b0;
    --dt-cyan: #38bdf8;
    --dt-cyan-soft: #7dd3fc;
    --dt-purple: #8b5cf6;
    --dt-purple-soft: #c4b5fd;
    --dt-border: rgba(148,163,255,0.14);
}
 
/* ---------- Page background: navy/charcoal, faint blue-purple gradient, soft radial glow ---------- */
.stApp {
    background:
        radial-gradient(1100px 620px at 50% 20%, rgba(56,189,248,0.09), transparent 62%),
        radial-gradient(800px 520px at 90% -5%, rgba(139,92,246,0.13), transparent 60%),
        radial-gradient(760px 520px at 4% 105%, rgba(99,102,241,0.09), transparent 60%),
        linear-gradient(165deg, #0b1020 0%, #0e1226 50%, #110f28 100%);
    background-attachment: fixed;
    color: var(--dt-text);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"], #MainMenu, footer { display: none !important; }
[data-testid="stMainBlockContainer"], .block-container { max-width: 1120px; padding-top: 1.2rem; padding-bottom: 3rem; }
 
.stApp, .stApp p, .stApp li, .stApp label, .stApp button, .stApp input, .stApp textarea,
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif !important;
}
.stApp h2, .stApp h3 { letter-spacing: -0.01em; font-weight: 700; color: var(--dt-text); }
.stApp hr { border-color: rgba(148,163,255,0.12); }
[data-testid="stCaptionContainer"] { color: var(--dt-muted); }
 
/* ---------- Glass surfaces ---------- */
.dt-glass, .dt-card, .dt-panel, .dt-trust-item, .dt-step {
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    border: 1px solid var(--dt-border);
    border-radius: 16px;
    box-shadow: 0 10px 34px rgba(3,6,20,0.45), inset 0 1px 0 rgba(255,255,255,0.05);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
}
.dt-panel { border-radius: 18px; padding: 20px 22px; margin-bottom: 14px; }
.dt-panel-title { color: var(--dt-text); font-weight: 700; font-size: 1.02rem; margin-bottom: 14px; }
.dt-ico { display: block; flex-shrink: 0; }
 
/* ---------- Top navigation ---------- */
.dt-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 20px; border-radius: 16px; margin-bottom: 8px;
    background: rgba(255,255,255,0.035); border: 1px solid var(--dt-border);
    backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
}
.dt-logo { display: flex; align-items: center; gap: 10px; font-weight: 800; letter-spacing: 0.16em; font-size: 0.92rem; color: var(--dt-text); }
.dt-logo-mark {
    width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--dt-cyan);
    background: radial-gradient(circle, var(--dt-purple) 0 34%, transparent 38%);
    box-shadow: 0 0 14px rgba(56,189,248,0.55);
}
.dt-nav-links { display: flex; gap: 6px; }
.dt-nav-links a {
    color: var(--dt-muted) !important; text-decoration: none !important; font-size: 0.88rem; font-weight: 500;
    padding: 6px 14px; border-radius: 999px; transition: color .15s, background .15s;
}
.dt-nav-links a:hover { color: var(--dt-text) !important; background: rgba(255,255,255,0.05); }
.dt-nav-links a.active { color: var(--dt-cyan-soft) !important; background: rgba(56,189,248,0.10); }
 
/* ---------- Hero ---------- */
.dt-hero { position: relative; text-align: center; padding: 46px 0 22px 0; }
.dt-hero::before {
    content: ""; position: absolute; left: 50%; top: 50%; width: 760px; height: 340px; transform: translate(-50%, -55%);
    background: radial-gradient(closest-side, rgba(56,189,248,0.14), rgba(139,92,246,0.06) 60%, transparent 100%);
    pointer-events: none;
}
.dt-hero-bg {
    position: absolute; inset: -10px -6%; background-size: cover; background-position: center; opacity: 0.10; pointer-events: none;
    -webkit-mask-image: radial-gradient(closest-side, #000 25%, transparent 100%);
    mask-image: radial-gradient(closest-side, #000 25%, transparent 100%);
}
.dt-hero h1 {
    position: relative; margin: 0; padding: 0; font-size: 2.9rem; line-height: 1.1; font-weight: 800; letter-spacing: -0.02em; color: #f3f6ff;
}
.dt-hero h1 span {
    background: linear-gradient(90deg, var(--dt-cyan) 0%, #818cf8 60%, var(--dt-purple) 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent; -webkit-text-fill-color: transparent;
}
.dt-hero-sub { position: relative; color: #c3cae3; font-size: 1.1rem; margin: 18px 0 4px 0; }
.dt-hero-note { position: relative; color: var(--dt-muted); font-size: 0.86rem; margin: 0; }
.dt-hero-compact { padding: 22px 0 6px 0; }
.dt-hero-compact h1 { font-size: 1.7rem; }
.dt-hero-compact h1 span, .dt-hero-compact br { display: none; }
.dt-hero-compact::before { height: 160px; }
 
/* ---------- Search bar ---------- */
[data-testid="stTextInput"] [data-baseweb="input"] {
    background: rgba(255,255,255,0.045) !important;
    border: 1px solid rgba(148,163,255,0.22) !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 30px rgba(3,6,20,0.35);
    transition: border-color .15s, box-shadow .15s;
}
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
    border-color: rgba(56,189,248,0.65) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.14), 0 8px 30px rgba(3,6,20,0.35);
}
[data-testid="stTextInput"] [data-baseweb="base-input"] { background: transparent !important; border: none !important; }
[data-testid="stTextInput"] input {
    height: 54px; font-size: 1.02rem; color: var(--dt-text) !important; background-color: transparent !important;
    padding-left: 50px !important;
    background-image: __ICON_SEARCH__; background-repeat: no-repeat; background-position: 18px center; background-size: 20px 20px;
}
[data-testid="stTextInput"] input::placeholder { color: #6b7594; opacity: 1; }
 
[data-testid="stFileUploader"] section {
    background: rgba(255,255,255,0.04); border: 1px dashed rgba(148,163,255,0.30); border-radius: 16px;
}
[data-testid="stFileUploader"] section:hover { border-color: rgba(56,189,248,0.6); }
 
/* ---------- Type pills (radio restyled) ---------- */
[data-testid="stRadio"] > div { justify-content: center; }
div[role="radiogroup"] { justify-content: center; gap: 10px; }
div[role="radiogroup"] label[data-baseweb="radio"] {
    display: flex; align-items: center; margin: 0; padding: 8px 20px; cursor: pointer;
    background: rgba(255,255,255,0.04); border: 1px solid rgba(148,163,255,0.16); border-radius: 999px;
    transition: border-color .15s, background .15s, box-shadow .15s;
}
div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child { display: none; }
div[role="radiogroup"] label[data-baseweb="radio"] p { margin: 0; color: #c3cae3; font-weight: 600; font-size: 0.9rem; }
div[role="radiogroup"] label[data-baseweb="radio"]::before {
    content: ""; width: 16px; height: 16px; margin-right: 8px; flex-shrink: 0; background-color: #94a3b8;
    -webkit-mask: var(--ico) center / contain no-repeat; mask: var(--ico) center / contain no-repeat;
}
div[role="radiogroup"] label[data-baseweb="radio"]:nth-of-type(1) { --ico: __ICON_USER__; }
div[role="radiogroup"] label[data-baseweb="radio"]:nth-of-type(2) { --ico: __ICON_EMAIL__; }
div[role="radiogroup"] label[data-baseweb="radio"]:nth-of-type(3) { --ico: __ICON_PHONE__; }
div[role="radiogroup"] label[data-baseweb="radio"]:nth-of-type(4) { --ico: __ICON_IMAGE__; }
div[role="radiogroup"] label[data-baseweb="radio"]:hover { border-color: rgba(56,189,248,0.5); }
div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
    background: rgba(56,189,248,0.14); border-color: rgba(56,189,248,0.6); box-shadow: 0 0 18px rgba(56,189,248,0.16);
}
div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked)::before { background-color: var(--dt-cyan-soft); }
div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) p { color: #e0f2fe; }
 
/* ---------- Buttons ---------- */
[data-testid="stButton"] { display: flex; justify-content: center; }
button[kind="primary"], button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, #22d3ee 0%, #3b82f6 60%, #7c3aed 100%) !important;
    border: none !important; color: #ffffff !important; border-radius: 999px !important; padding: 0.7rem 2.8rem !important;
    box-shadow: 0 10px 30px rgba(59,130,246,0.35), inset 0 0 0 1px rgba(255,255,255,0.10);
    transition: transform .15s, box-shadow .15s;
}
button[kind="primary"] p, button[data-testid="stBaseButton-primary"] p { font-weight: 700; letter-spacing: 0.12em; color: #ffffff !important; }
button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-1px); box-shadow: 0 14px 38px rgba(59,130,246,0.5), inset 0 0 0 1px rgba(255,255,255,0.14);
}
[data-testid="stDownloadButton"] button {
    background: rgba(139,92,246,0.12) !important; border: 1px solid rgba(139,92,246,0.40) !important;
    color: #ddd6fe !important; border-radius: 12px !important; font-weight: 600;
}
[data-testid="stDownloadButton"] button:hover { border-color: rgba(56,189,248,0.6) !important; color: #e0f2fe !important; }
 
[data-testid="stCheckbox"], [data-testid="stToggle"] { display: flex; justify-content: center; }
[data-testid="stCheckbox"] p, [data-testid="stToggle"] p { color: var(--dt-muted); font-size: 0.86rem; }
 
/* ---------- Expanders ---------- */
[data-testid="stExpander"] details {
    background: rgba(255,255,255,0.035); border: 1px solid var(--dt-border) !important; border-radius: 14px !important;
}
[data-testid="stExpander"] summary:hover { color: var(--dt-cyan-soft); }
 
/* ---------- Notices ---------- */
.dt-notice {
    display: flex; gap: 12px; align-items: flex-start; padding: 14px 16px; margin: 10px 0; border-radius: 14px;
    border: 1px solid; font-size: 0.9rem; line-height: 1.55;
}
.dt-notice-ico { margin-top: 2px; }
.dt-notice-info   { background: rgba(56,189,248,0.07);  border-color: rgba(56,189,248,0.25);  color: #bae6fd; }
.dt-notice-warn   { background: rgba(245,183,74,0.08);  border-color: rgba(245,183,74,0.30);  color: #fcd9a0; }
.dt-notice-danger { background: rgba(251,113,133,0.08); border-color: rgba(251,113,133,0.30); color: #fecdd3; }
.dt-notice-demo   { background: rgba(139,92,246,0.10);  border-color: rgba(139,92,246,0.38);  color: #ddd6fe; }
 
/* ---------- Landing: platforms, trust, steps ---------- */
.dt-platforms { display: flex; flex-wrap: wrap; justify-content: center; gap: 12px 30px; margin-top: 34px; }
.dt-platform { display: flex; align-items: center; gap: 8px; color: var(--dt-muted); font-size: 0.9rem; font-weight: 500; transition: color .15s; }
.dt-platform:hover { color: var(--dt-cyan-soft); }
 
.dt-trust { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; margin-top: 30px; }
.dt-trust-item { display: flex; gap: 14px; align-items: flex-start; padding: 16px 18px; }
.dt-trust-icon {
    width: 38px; height: 38px; border-radius: 11px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    color: var(--dt-cyan-soft); background: rgba(56,189,248,0.10); border: 1px solid rgba(56,189,248,0.28);
}
.dt-trust-title { color: var(--dt-text); font-weight: 600; font-size: 0.93rem; }
.dt-trust-desc { color: var(--dt-muted); font-size: 0.82rem; margin-top: 3px; line-height: 1.45; }
 
.dt-section-title { color: var(--dt-text); font-weight: 700; font-size: 1.05rem; margin: 40px 0 14px 0; }
.dt-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; }
.dt-step { border-radius: 14px; padding: 16px; }
.dt-step-num {
    background: linear-gradient(135deg, var(--dt-cyan), var(--dt-purple)); color: #ffffff; width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.82rem; margin-bottom: 10px;
}
.dt-step-title { color: var(--dt-text); font-weight: 600; font-size: 0.92rem; }
.dt-step-desc { color: var(--dt-muted); font-size: 0.8rem; margin-top: 4px; line-height: 1.45; }
 
/* ---------- Report ---------- */
.dt-report-title { color: #f3f6ff; font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em; margin: 26px 0 4px 0; }
.dt-input-line { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; color: var(--dt-muted); font-size: 0.92rem; margin: 6px 0 14px 0; }
.dt-input-line strong { color: var(--dt-text); font-weight: 600; }
.dt-tag { padding: 2px 10px; border-radius: 999px; font-size: 0.72rem; font-weight: 600; border: 1px solid; }
.dt-tag-demo { background: rgba(139,92,246,0.16); color: #ddd6fe; border-color: rgba(139,92,246,0.40); }
.dt-tag-live { background: rgba(56,189,248,0.12); color: #bae6fd; border-color: rgba(56,189,248,0.32); }
 
.dt-card { padding: 18px 20px; height: 100%; }
.dt-card-top { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; color: var(--dt-cyan-soft); }
.dt-card-label { color: var(--dt-muted); font-size: 0.85rem; }
.dt-card-value { font-size: 2.3rem; font-weight: 800; color: #f3f6ff; line-height: 1.1; font-variant-numeric: tabular-nums; }
 
.dt-donut-wrap { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 24px 16px; }
.dt-donut { width: 172px; height: 172px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
.dt-donut-inner {
    width: 140px; height: 140px; border-radius: 50%; background: #0c1226; border: 1px solid rgba(148,163,255,0.10);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.dt-donut-score { font-size: 3.1rem; font-weight: 800; color: #ffffff; line-height: 1; font-variant-numeric: tabular-nums; letter-spacing: -0.03em; text-shadow: 0 0 24px rgba(125,211,252,0.35); }
.dt-donut-sub { font-size: 0.74rem; color: var(--dt-muted); margin-top: 4px; }
.dt-level-pill { padding: 6px 16px; border-radius: 999px; font-weight: 600; font-size: 0.88rem; display: inline-block; }
 
.dt-badges { display: flex; flex-wrap: wrap; gap: 8px; }
.dt-badge { display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 999px; font-size: 0.86rem; font-weight: 500; }
.dt-badge-state { font-size: 0.74rem; opacity: 0.8; }
.dt-badge-found { background: rgba(56,189,248,0.12); border: 1px solid rgba(56,189,248,0.40); color: #bae6fd; }
.dt-badge-missing { background: rgba(255,255,255,0.03); border: 1px solid rgba(148,163,255,0.14); color: #6b7594; }
 
.dt-history-row { display: flex; justify-content: space-between; align-items: center; padding: 11px 0; border-bottom: 1px solid rgba(148,163,255,0.10); }
.dt-history-row:last-child { border-bottom: none; }
.dt-history-name { color: var(--dt-text); font-size: 0.92rem; font-weight: 600; }
.dt-history-meta { display: flex; align-items: center; gap: 8px; color: var(--dt-muted); font-size: 0.78rem; margin-top: 4px; }
.dt-history-score { font-weight: 700; font-size: 0.85rem; padding: 4px 12px; border-radius: 999px; font-variant-numeric: tabular-nums; }
.dt-empty { color: var(--dt-muted); font-size: 0.86rem; }
 
.dt-footer-note { color: #6b7594; font-size: 0.82rem; text-align: center; margin-top: 12px; line-height: 1.5; }
.dt-footer { margin-top: 48px; padding-top: 22px; border-top: 1px solid rgba(148,163,255,0.10); }
.dt-footer-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }
.dt-footer-title { color: var(--dt-text); font-weight: 700; font-size: 0.95rem; margin-bottom: 6px; }
.dt-footer-block p { color: var(--dt-muted); font-size: 0.85rem; line-height: 1.6; margin: 0; }
 
@media (max-width: 720px) {
    .dt-hero h1 { font-size: 2rem; }
    .dt-nav-links a { padding: 6px 9px; }
}
</style>
"""
 
THEME_CSS = (
    THEME_CSS
    .replace("__ICON_SEARCH__", _svg_uri("search", "#94a3b8"))
    .replace("__ICON_USER__", _svg_uri("user"))
    .replace("__ICON_EMAIL__", _svg_uri("email"))
    .replace("__ICON_PHONE__", _svg_uri("phone"))
    .replace("__ICON_IMAGE__", _svg_uri("image"))
)
 
st.markdown(THEME_CSS, unsafe_allow_html=True)
 
 
# ----------------------------------------------------------------------------
# Shared header / notices
# ----------------------------------------------------------------------------
def render_nav():
    render_html("""
    <div id="dt-top"></div>
    <div class="dt-nav">
        <div class="dt-logo"><span class="dt-logo-mark"></span><span>DIGITALTRACE</span></div>
        <div class="dt-nav-links">
            <a href="#dt-top" target="_self" class="active">Dashboard</a>
            <a href="#about" target="_self">About</a>
            <a href="#help" target="_self">Help</a>
        </div>
    </div>
    """)
 
 
def render_hero(compact=False):
    banner_b64 = _get_banner_base64()
    bg_style = f"background-image: url('data:image/png;base64,{banner_b64}');" if banner_b64 else ""
    cls = "dt-hero dt-hero-compact" if compact else "dt-hero"
    extra = "" if compact else (
        '<p class="dt-hero-sub">Discover where your identity appears online.</p>'
        '<p class="dt-hero-note">For self-verification and citizen awareness only.</p>'
    )
    render_html(f"""
    <div class="{cls}">
        <div class="dt-hero-bg" style="{bg_style}"></div>
        <h1>YOUR DIGITAL FOOTPRINT<br><span>STARTS WITH ONE SEARCH</span></h1>
        {extra}
    </div>
    """)
 
 
def render_notice(message_html, kind="info"):
    icon_name = "info" if kind in ("info", "demo") else "alert"
    render_html(
        f'<div class="dt-notice dt-notice-{kind}">'
        f'<span class="dt-notice-ico">{icon(icon_name, 18)}</span>'
        f'<div>{message_html}</div>'
        '</div>'
    )
 
 
# ----------------------------------------------------------------------------
# Landing sections
# ----------------------------------------------------------------------------
def render_platform_strip():
    items = [
        ("linkedin", "LinkedIn"), ("instagram", "Instagram"), ("facebook", "Facebook"),
        ("github", "GitHub"), ("web", "News & Web"),
    ]
    chips = "".join(f'<div class="dt-platform">{icon(n, 18)}<span>{label}</span></div>' for n, label in items)
    render_html(f'<div class="dt-platforms">{chips}</div>')
 
 
def render_trust_row():
    items = [
        ("doc", "Evidence-backed analysis", "Every flag links to the exact source that triggered it."),
        ("sliders", "No AI guessing", "The score is rule-based. Gemini only explains it."),
        ("lock", "Privacy-first", "Public sources only, built for self-verification."),
        ("layers", "Multi-platform search", "LinkedIn, Instagram, Facebook, news and the wider web."),
    ]
    cells = "".join(
        f'<div class="dt-trust-item"><div class="dt-trust-icon">{icon(n, 18)}</div>'
        f'<div><div class="dt-trust-title">{title}</div><div class="dt-trust-desc">{desc}</div></div></div>'
        for n, title, desc in items
    )
    render_html(f'<div class="dt-trust">{cells}</div>')
 
 
def render_how_it_works():
    steps = [
        ("1", "Enter details", "Provide a name, email, phone, or photo."),
        ("2", "Search across platforms", "SerpApi fetches evidence from multiple public sources."),
        ("3", "Analyze and score", "Rule-based scoring with traceable evidence."),
        ("4", "View results", "See your exposure score, flags, and exact sources."),
    ]
    cells = "".join(
        f'<div class="dt-step"><div class="dt-step-num">{num}</div>'
        f'<div class="dt-step-title">{title}</div><div class="dt-step-desc">{desc}</div></div>'
        for num, title, desc in steps
    )
    render_html(f'<div class="dt-section-title">How it works</div><div class="dt-steps">{cells}</div>')
 
 
# ----------------------------------------------------------------------------
# Report pieces
# ----------------------------------------------------------------------------
def parse_narrative(narrative_text):
    summary, actions = narrative_text, []
    if "RECOMMENDED ACTIONS:" in narrative_text:
        parts = narrative_text.split("RECOMMENDED ACTIONS:")
        summary = parts[0].replace("SUMMARY:", "").strip()
        actions = [line.strip("- ").strip() for line in parts[1].strip().split("\n") if line.strip()]
    else:
        summary = narrative_text.replace("SUMMARY:", "").strip()
    if not actions:
        actions = ["Verify identity through an independent channel before trusting it."]
    return summary, actions
 
 
def _level_colors(level):
    # (ring colour, pill background, pill text)
    return {
        "LOW": ("#38bdf8", "rgba(56,189,248,0.14)", "#7dd3fc"),
        "MEDIUM": ("#f5b74a", "rgba(245,183,74,0.14)", "#fcd48a"),
        "HIGH": ("#fb7185", "rgba(251,113,133,0.14)", "#fda4af"),
    }.get(level, ("#38bdf8", "rgba(56,189,248,0.14)", "#7dd3fc"))
 
 
def render_score_donut(score, level):
    ring_color, pill_bg, pill_text = _level_colors(level)
    angle = min(max(score, 0), 100) * 3.6
    render_html(f"""
    <div class="dt-glass dt-donut-wrap">
        <div class="dt-donut" style="background: conic-gradient({ring_color} {angle}deg, rgba(148,163,255,0.14) {angle}deg); box-shadow: 0 0 46px {ring_color}33;">
            <div class="dt-donut-inner">
                <div class="dt-donut-score">{score}</div>
                <div class="dt-donut-sub">out of 100</div>
            </div>
        </div>
        <span class="dt-level-pill" style="background:{pill_bg}; color:{pill_text};">{level} exposure</span>
    </div>
    """)
 
 
def render_metric_card(label, value, icon_name):
    render_html(
        f'<div class="dt-card"><div class="dt-card-top">{icon(icon_name, 16)}'
        f'<span class="dt-card-label">{label}</span></div>'
        f'<div class="dt-card-value">{value}</div></div>'
    )
 
 
def render_platform_presence(evidence_list):
    present = {key: False for key, _, _ in PLATFORM_DISPLAY}
    for ev in evidence_list:
        src = ev.get("query_source")
        if src in present:
            present[src] = True
        if "github.com" in (ev.get("url") or "").lower():
            present["GitHub"] = True
 
    badges = ""
    for key, label, icon_name in PLATFORM_DISPLAY:
        if present[key]:
            badges += f'<span class="dt-badge dt-badge-found">{icon(icon_name, 16)}<span>{label}</span><span class="dt-badge-state">Found</span></span>'
        else:
            badges += f'<span class="dt-badge dt-badge-missing">{icon(icon_name, 16)}<span>{label}</span><span class="dt-badge-state">Not found</span></span>'
 
    render_html(
        '<div class="dt-panel">'
        '<div class="dt-panel-title">Platform presence</div>'
        f'<div class="dt-badges">{badges}</div>'
        '</div>'
    )
 
 
def render_recent_searches():
    if not st.session_state.history:
        return
    rows = []
    for entry in reversed(st.session_state.history[-5:]):
        _, pill_bg, pill_text = _level_colors(entry["level"])
        tag_cls, tag = ("dt-tag-demo", "Demo") if entry["demo"] else ("dt-tag-live", "Live")
        rows.append(
            '<div class="dt-history-row">'
            '<div>'
            f'<div class="dt-history-name">{escape(str(entry["input"]))}</div>'
            f'<div class="dt-history-meta"><span class="dt-tag {tag_cls}">{tag}</span>'
            f'<span>{escape(entry["time"])} · {escape(entry["type"])}</span></div>'
            '</div>'
            f'<div class="dt-history-score" style="background:{pill_bg}; color:{pill_text};">{entry["score"]}/100</div>'
            '</div>'
        )
    render_html(
        '<div class="dt-section-title">Recent searches</div>'
        '<div class="dt-panel">' + "".join(rows) + '</div>'
    )
 
 
def render_footer():
    render_html(f"""
    <div class="dt-footer">
        <div class="dt-footer-grid">
            <div id="about" class="dt-footer-block">
                <div class="dt-footer-title">About</div>
                <p>DigitalTrace shows where a name, email, phone number or photo appears in public search results, and flags signals such as conflicting profiles or reused images. Scores are rule-based and every flag links to its source.</p>
            </div>
            <div id="help" class="dt-footer-block">
                <div class="dt-footer-title">Help</div>
                <p>Use a full name for the best results. Email and phone searches look for public pages containing that exact value. Image search finds other places a photo appears. Turn on demo mode to try a sample report with a fictional name.</p>
            </div>
        </div>
        <div class="dt-footer-note">{DISCLAIMER}</div>
    </div>
    """)
 
 
def pdf_download_button(pdf_bytes, file_name, key):
    """PDF download button. on_click="ignore" stops Streamlit rerunning the page when it is
    clicked (which would wipe the report from the screen); older Streamlit versions fall back."""
    if pdf_bytes is None:
        render_html('<div class="dt-empty" style="padding-top:8px;">PDF unavailable</div>')
        return
    kwargs = dict(
        label="📄 Download PDF report", data=pdf_bytes, file_name=file_name,
        mime="application/pdf", key=key,
    )
    try:
        st.download_button(on_click="ignore", **kwargs)
    except TypeError:
        st.download_button(**kwargs)
 
 
_PDF_REPLACEMENTS = {
    "\u2014": "-", "\u2013": "-", "\u2022": "*", "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2192": "->", "\u26a0": "!", "\u2610": "[ ]",
}
 
 
def _pdf_text(value):
    """Make text safe for the built-in Helvetica font (Latin-1 only)."""
    text = str(value)
    for old, new in _PDF_REPLACEMENTS.items():
        text = text.replace(old, new)
    text = text.encode("latin-1", "replace").decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
 
 
def build_simple_pdf(input_type, input_value, risk, summary, actions, evidence_list, demo_mode):
    """Dependency-free, plain-layout PDF. Used only if the standard PDF builder fails or gets stuck,
    so the download button always works."""
    blocks = [("DigitalTrace - Identity Verification Report", 16, True)]
    if demo_mode:
        blocks.append(("DEMO MODE - FABRICATED DATA. Names, profiles and links below are fictional.", 9, True))
    blocks += [
        (f"Input ({input_type}): {input_value}", 11, False),
        (f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", 9, False),
        ("", 6, False),
        (f"Exposure score: {risk['score']}/100 ({risk['level']})", 13, True),
        (f"Sources checked: {len(evidence_list)}   Signals: {len(risk['signals'])}   "
         f"Consistent references: {risk['consistent_count']}   Needs verification: {risk['ambiguous_count']}", 10, False),
        ("", 6, False),
        ("Summary", 12, True),
        (summary, 10, False),
        ("", 6, False),
        ("Findings", 12, True),
    ]
    if not risk["signals"]:
        blocks.append(("No specific risk signals were detected in the available public results.", 10, False))
    for signal in risk["signals"]:
        blocks.append((f"- {signal['label']} ({signal['points']} points): {signal['reason']}", 10, True))
        for ev in signal["evidence"]:
            blocks.append((f"    [{ev['source_type']}] {ev['title']} - {ev['url']}", 8, False))
    blocks += [("", 6, False), ("Sources", 12, True)]
    seen = set()
    for ev in evidence_list[:15]:
        if ev["url"] and ev["url"] not in seen:
            blocks.append((f"- {ev['title']} - {ev['url']}", 8, False))
            seen.add(ev["url"])
    blocks += [("", 6, False), ("What to do next", 12, True)]
    for action in actions:
        blocks.append((f"[ ] {action}", 10, False))
    blocks += [("", 6, False), (DISCLAIMER, 8, False)]
 
    width, height, margin = 595, 842, 50
    pages, y = [[]], height - margin
    for text, size, bold in blocks:
        lead = size * 1.35
        max_chars = max(10, int((width - 2 * margin) / (size * 0.52)))
        clean = str(text)
        for key, new in _PDF_REPLACEMENTS.items():
            clean = clean.replace(key, new)
        clean = clean.encode("latin-1", "replace").decode("latin-1")
        for line in (textwrap.wrap(clean, max_chars, break_long_words=True) or [""]):
            if y - lead < margin:
                pages.append([])
                y = height - margin
            y -= lead
            pages[-1].append((y, size, bold, line))
 
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
 
    def add(body):
        offsets.append(len(out))
        out.extend(f"{len(offsets)} 0 obj\n".encode())
        out.extend(body)
        out.extend(b"\nendobj\n")
 
    add(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{5 + 2 * i} 0 R" for i in range(len(pages)))
    add(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode())
    add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    for i, lines in enumerate(pages):
        parts = []
        for (ly, size, bold, line) in lines:
            parts.append(f"BT /{'F2' if bold else 'F1'} {size} Tf {margin} {ly:.1f} Td ({_pdf_text(line)}) Tj ET")
        content = "\n".join(parts).encode("latin-1", "replace")
        add(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {6 + 2 * i} 0 R >>".encode()
        )
        add(f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream")
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets) + 1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(f"trailer\n<< /Size {len(offsets) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode())
    return bytes(out)
 
 
def build_pdf_with_timeout(input_type, input_value, risk, summary, actions, evidence_list, demo_mode, timeout=12):
    """Runs the standard generate_pdf_report in a background thread with a time limit. If it fails or
    gets stuck, a simple built-in PDF is created instead so the button always works.
    Returns (pdf_bytes, warning_message); the warning is None when the standard PDF worked."""
    reason = None
    if st.session_state.get("pdf_main_hung"):
        reason = "the standard PDF builder got stuck earlier in this session"
    else:
        result = {}
 
        def worker():
            try:
                result["bytes"] = generate_pdf_report(
                    input_type, input_value, risk, summary, actions, evidence_list, demo_mode=demo_mode
                )
            except Exception as exc:
                result["error"] = f"{type(exc).__name__}: {exc}"
 
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            st.session_state["pdf_main_hung"] = True
            reason = f"it took longer than {timeout} seconds"
        elif "error" in result:
            reason = result["error"]
        else:
            return result.get("bytes"), None
 
    try:
        data = build_simple_pdf(input_type, input_value, risk, summary, actions, evidence_list, demo_mode)
        return data, f"The standard PDF layout could not be used ({reason}), so a simplified PDF was created instead."
    except Exception as exc:
        return None, f"The PDF report could not be generated: {reason}; the simplified PDF also failed ({type(exc).__name__}: {exc})"
 
 
def render_dashboard(input_type, input_value, risk, narrative, evidence_list, demo_mode=False, clusters=None):
    summary, actions = parse_narrative(narrative)
 
    st.session_state.history.append({
        "input": input_value, "type": input_type, "score": risk["score"],
        "level": risk["level"], "demo": demo_mode, "time": datetime.now().strftime("%d %b, %H:%M"),
    })
 
    # The report is drawn FIRST. The PDF is built at the very end (with a time limit), and its
    # button is dropped into this reserved slot at the top, so a slow PDF can never hide results.
    pdf_name = f"digitaltrace_report_{input_type}{'_DEMO' if demo_mode else ''}.pdf"
 
    head_left, head_right = st.columns([3, 1.2])
    with head_left:
        render_html('<div class="dt-report-title">Identity verification report</div>')
    with head_right:
        render_html('<div style="height:26px"></div>')
        pdf_slot = st.empty()
        pdf_slot.markdown('<div class="dt-empty" style="padding-top:8px;">Preparing PDF...</div>', unsafe_allow_html=True)
 
    if demo_mode:
        render_notice(DEMO_NOTICE, "demo")
    render_notice(DISCLAIMER, "info")
 
    tag_html = '<span class="dt-tag dt-tag-demo">fabricated demo name</span>' if demo_mode else ""
    render_html(
        f'<div class="dt-input-line"><span>Input</span><strong>{escape(str(input_value))}</strong>{tag_html}</div>'
    )
 
    col_donut, col_grid = st.columns([1, 1.4])
    with col_donut:
        render_score_donut(risk["score"], risk["level"])
    with col_grid:
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            render_metric_card("Sources checked", len(evidence_list), "web")
        with r1c2:
            render_metric_card("Signals detected", len(risk["signals"]), "flag")
        st.write("")
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            render_metric_card("Consistent references", risk["consistent_count"], "check")
        with r2c2:
            render_metric_card("Needs verification", risk["ambiguous_count"], "alert")
 
    st.write("")
    st.caption(
        "This score measures how easily this identity could be confused with others online, "
        "or how exposed its public information is — it is not a judgment of danger or wrongdoing. "
        "\"Needs verification\" means results involved in a flagged signal, not proof of a problem on their own."
    )
    st.divider()
 
    if input_type == "name" and not demo_mode:
        render_platform_presence(evidence_list)
        st.divider()
 
    st.subheader("Summary")
    st.write(summary)
    st.divider()
 
    if clusters:
        profile_clusters = [c for c in clusters if any(e.get("is_profile") for e in c)]
        if profile_clusters:
            st.subheader(f"Identity clusters found ({len(profile_clusters)})")
            st.caption("Each group below is a likely-distinct person sharing this name, based on their own profile pages.")
            for i, cluster in enumerate(profile_clusters, 1):
                lead = next((e for e in cluster if e.get("is_profile")), cluster[0])
                with st.expander(f"Cluster {i}: {lead['title']}"):
                    for ev in cluster:
                        tag = "profile" if ev.get("is_profile") else ev["source_type"]
                        st.write(f"[{tag}] {ev['title']}")
                        st.write(ev["url"])
            st.divider()
 
    st.subheader("Findings")
    if not risk["signals"]:
        st.write("No specific risk signals were detected in the available public results.")
    else:
        for signal in risk["signals"]:
            with st.expander(f"⚠ {signal['label']} — {signal['points']} points ({len(signal['evidence'])} supporting source(s))"):
                st.write(f"**Why was this flagged?** {signal['reason']}")
                st.write("**Evidence:**")
                for i, ev in enumerate(signal["evidence"], 1):
                    st.markdown(f"*Evidence {i}* — [{ev['source_type']}] {ev['title']}")
                    st.write(ev["url"])
    st.divider()
 
    st.subheader("Sources")
    if demo_mode:
        st.caption("These links are fictional placeholders generated for the demo. They do not point to real people.")
    seen = set()
    for ev in evidence_list[:15]:
        if ev["url"] and ev["url"] not in seen:
            st.write(f"- [{ev['title']}]({ev['url']})")
            seen.add(ev["url"])
    st.divider()
 
    st.subheader("What to do next")
    for a in actions:
        st.write(f"☐ {a}")
 
    st.write("")
    _log("report drawn, building PDF")
    pdf_bytes, pdf_warning = build_pdf_with_timeout(
        input_type, input_value, risk, summary, actions, evidence_list, demo_mode
    )
    _log(f"PDF step done (warning: {pdf_warning})")
    with pdf_slot.container():
        pdf_download_button(pdf_bytes, pdf_name, "pdf_top")
    if pdf_warning:
        render_notice(escape(pdf_warning), "warn")
    pdf_download_button(pdf_bytes, pdf_name, "pdf_bottom")
    render_html('<div class="dt-footer-note">Based on public search results only. Not proof of identity or wrongdoing.</div>')
    _log("dashboard done")
 
 
# ----------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------
render_nav()
 
# Widget values are already in session_state at the top of a rerun, so we can tell
# whether this run was triggered by the scan button and shrink the hero accordingly.
scanning = bool(st.session_state.get("scan_btn", False))
render_hero(compact=scanning)
 
input_value = ""
uploaded_file = None
 
_, mid_col, _ = st.columns([1, 3.4, 1])
with mid_col:
    current_type = st.session_state.get("type_pick", "Name")
 
    if current_type == "Image":
        uploaded_file = st.file_uploader(
            "Upload an image", type=["jpg", "jpeg", "png"],
            label_visibility="collapsed", key="image_upload",
        )
    else:
        input_value = st.text_input(
            f"Enter the {current_type.lower()}",
            placeholder=PLACEHOLDERS[current_type],
            label_visibility="collapsed", key="query_text",
        )
 
    type_label = st.radio(
        "What are you checking?", ["Name", "Email", "Phone", "Image"],
        horizontal=True, label_visibility="collapsed", key="type_pick",
    )
    input_type = type_label.lower()
 
    search_clicked = st.button("START SCAN  →", type="primary", key="scan_btn")
 
    demo_mode = st.toggle(
        "Demo mode — use fabricated sample data (name searches only)",
        value=False, key="demo_toggle",
        help="Real identities can't be shown in a public demo for privacy reasons, so this mode generates entirely fabricated results.",
    )
    if demo_mode:
        render_notice(
            "<strong>DEMO MODE IS ON.</strong> Name-search results will be entirely fabricated sample data, because real "
            "identities cannot be shown here for privacy reasons. Enter a fictional name, not a real person's.",
            "demo",
        )
    if demo_mode and input_type != "name":
        render_notice("Demo mode only applies to name searches. This search will use live data.", "info")
 
if not search_clicked:
    render_platform_strip()
    render_trust_row()
    render_how_it_works()
 
if search_clicked:
    _log(f"scan started: {input_type}, demo={demo_mode}")
    if input_type == "image":
        if uploaded_file is None:
            render_notice("Please upload an image first.", "warn")
        else:
            with st.spinner("Uploading image and analyzing — this can take a moment..."):
                public_url = upload_image_temp(uploaded_file)
                if not public_url:
                    render_notice("Image upload failed. Please try again.", "danger")
                    st.stop()
                results = search_reverse_image(public_url)
                image_matches = results.get("image_results", [])
                evidence_list = build_evidence_list(image_matches)
                risk = calculate_risk(evidence_list, "image", clusters=None, image_matches=image_matches)
                narrative = generate_narrative("image", "uploaded photo", risk)
            render_dashboard("image", "Uploaded photo", risk, narrative, evidence_list)
 
    elif input_type == "name":
        if not input_value.strip():
            render_notice("Please enter a name first.", "warn")
        else:
            with st.spinner("Investigating — running searches, scoring evidence, and generating explanation..."):
                failed_sources = []
                if demo_mode:
                    results = get_demo_results(input_value)
                else:
                    results, failed_sources = multi_query_search(input_value, return_status=True)
                _log(f"searches finished (failed sources: {failed_sources})")
 
                evidence_list = build_evidence_list(results)
                name_lower = input_value.lower()
                evidence_list = [ev for ev in evidence_list if name_lower in f"{ev['title']} {ev['snippet']}".lower()]
                _log(f"evidence built: {len(evidence_list)} items")
                clusters = cluster_identities(evidence_list)
                _log("clusters built")
                risk = calculate_risk(evidence_list, "name", clusters=clusters)
                _log(f"risk scored: {risk['score']}")
 
                profile_clusters = [c for c in clusters if any(e.get("is_profile") for e in c)]
                context = (
                    f"There are {len(profile_clusters)} likely distinct identity clusters found "
                    f"(based on actual profile pages, not third-party posts mentioning the name)."
                )
                if demo_mode:
                    context += (
                        " IMPORTANT: this is a demonstration using entirely fabricated sample data, not real "
                        "people, because real identities cannot be shown for privacy reasons. State this "
                        "clearly in the summary."
                    )
                if failed_sources:
                    context += " NOTE: the evidence is incomplete because some search sources did not respond."
 
                _log("calling Gemini")
                narrative = generate_narrative(input_type, input_value, risk, extra_context=context)
                _log("Gemini step finished")
 
            if failed_sources:
                render_notice(
                    "Some searches did not respond in time (" + escape(", ".join(failed_sources)) + "), "
                    "so this report is based on partial evidence. Run it again for a fuller result.",
                    "warn",
                )
 
            _log("rendering dashboard")
            render_dashboard(input_type, input_value, risk, narrative, evidence_list, demo_mode=demo_mode, clusters=clusters)
 
    else:
        if not input_value.strip():
            render_notice("Please enter a value first.", "warn")
        else:
            with st.spinner("Investigating — searching and analyzing..."):
                query = build_targeted_query(input_value, input_type)
                results = search_text(query)
                evidence_list = build_evidence_list(results.get("organic_results", []))
                value_lower = input_value.lower()
                evidence_list = [ev for ev in evidence_list if value_lower in f"{ev['title']} {ev['snippet']}".lower()]
                risk = calculate_risk(evidence_list, input_type, clusters=None)
                narrative = generate_narrative(input_type, input_value, risk)
            render_dashboard(input_type, input_value, risk, narrative, evidence_list)
 
render_recent_searches()
render_footer()