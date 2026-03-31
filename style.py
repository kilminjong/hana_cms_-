# -*- coding: utf-8 -*-
"""CSS 및 UI 헬퍼 - 개선된 버전"""
import streamlit as st

CSS_VARIABLES = """<style>
:root {
  --primary:#008485; --primary-light:#e0f2f2; --primary-dark:#006a6b;
  --accent:#E90061; --accent-light:#fff0f5;
  --bg-app:#f0f2f5; --bg-card:#ffffff; --bg-muted:#f7f8fa;
  --bg-sidebar:#1a2332; --bg-section:#f4f6f9;
  --border-light:#e2e6ea; --border-medium:#c4cdd5; --border-input:#c1c9d2;
  --text-primary:#1a1a2e; --text-secondary:#4a5568; --text-muted:#8c95a6;
  --text-inverse:#ffffff; --text-sidebar:#dce4f0;
  --color-success:#0d9f6e; --color-success-bg:#ecfdf5;
  --color-warning:#e67e22; --color-warning-bg:#fffbeb;
  --color-danger:#dc3545; --color-danger-bg:#fef2f2;
  --color-info:#3b82f6; --color-info-bg:#eff6ff;
  --sp-xs:4px; --sp-sm:8px; --sp-md:16px; --sp-lg:24px; --sp-xl:32px; --sp-2xl:48px;
  --radius-sm:6px; --radius-md:10px; --radius-lg:14px; --radius-full:9999px;
  --shadow-sm:0 1px 3px rgba(0,0,0,0.06); --shadow-md:0 2px 8px rgba(0,0,0,0.08);
  --shadow-lg:0 8px 24px rgba(0,0,0,0.12); --shadow-card:0 1px 4px rgba(0,0,0,0.06);
  --font-main:'Pretendard',-apple-system,'Malgun Gothic',sans-serif;
  --font-mono:'Consolas','Courier New',monospace;
}
</style>"""

CSS_GLOBAL = """<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"] { font-family: var(--font-main) !important; }

/* ── 라이트 모드 강제 적용 ── */
.stApp { background-color: #f0f2f5 !important; color: #1a1a2e !important; }
.main .block-container { background-color: #f0f2f5 !important; }

/* 다크모드 override */
div[data-baseweb="select"] { background-color: #ffffff !important; color: #1a1a2e !important; }
div[data-baseweb="select"] * { color: #1a1a2e !important; }
div[data-baseweb="popover"] { background-color: #ffffff !important; }
div[data-baseweb="popover"] * { color: #1a1a2e !important; }
[data-baseweb="tab-panel"] { background-color: #ffffff !important; }
[data-testid="stExpander"] { background-color: #ffffff !important; border: 1px solid #e2e6ea !important; border-radius: 10px !important; }
[data-testid="stExpander"] * { color: #1a1a2e !important; }
[data-testid="collapsedControl"] { display: none !important; }

.stApp { background-color: var(--bg-app); }
#MainMenu { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebarNav"] { display: none !important; }
footer { visibility: hidden !important; }

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #1a2332 0%, #141c28 100%) !important;
  border-right: none !important;
}
[data-testid="stSidebar"] * { color: var(--text-sidebar) !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.07) !important; }

[data-testid="stSidebar"] .stButton > button {
  text-align: left;
  justify-content: flex-start;
  border-radius: var(--radius-sm);
  border: none !important;
  background: transparent !important;
  color: #94a3b8 !important;
  font-weight: 500;
  font-size: 13.5px;
  padding: 10px 16px;
  transition: all .18s ease;
  margin-bottom: 1px;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255,255,255,0.07) !important;
  color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: rgba(0,132,133,0.18) !important;
  color: #4dd8d9 !important;
  border-left: 3px solid #008485 !important;
  font-weight: 700;
  padding-left: 13px;
}

div.stButton > button {
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 14px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  transition: all .18s ease;
}
div.stButton > button[kind="primary"] {
  background: #008485 !important;
  border-color: #008485 !important;
  color: white !important;
}
div.stButton > button[kind="primary"]:hover {
  background: #006a6b !important;
  border-color: #006a6b !important;
  box-shadow: 0 2px 8px rgba(0,132,133,0.3) !important;
}
div.stButton > button[kind="secondary"]:hover {
  border-color: #008485 !important;
  color: #008485 !important;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 2px;
  background: var(--bg-card);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  padding: 4px;
  border: 1px solid var(--border-light);
  border-bottom: none;
}
.stTabs [data-baseweb="tab"] {
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 13.5px;
  padding: 9px 18px;
}
.stTabs [aria-selected="true"] {
  background: #008485 !important;
  color: white !important;
}

.stTextInput > div > div > input {
  border: 1.5px solid var(--border-input) !important;
  border-radius: var(--radius-sm) !important;
  padding: 10px 14px !important;
  font-size: 14px !important;
  background: var(--bg-card) !important;
  color: #1a1a2e !important;
  -webkit-text-fill-color: #1a1a2e !important;
}
.stTextInput > div > div > input:focus {
  border-color: #008485 !important;
  box-shadow: 0 0 0 3px rgba(0,132,133,0.1) !important;
}
.stTextInput > div > div > input::placeholder {
  color: #8c95a6 !important;
  -webkit-text-fill-color: #8c95a6 !important;
}
.stTextInput > label, .stSelectbox > label,
.stMultiSelect > label, .stDateInput > label, .stTextArea > label {
  font-weight: 600 !important;
  font-size: 13px !important;
  color: var(--text-secondary) !important;
}
.stSelectbox > div > div, .stMultiSelect > div > div {
  border: 1.5px solid var(--border-input) !important;
  border-radius: var(--radius-sm) !important;
}
.stTextArea > div > div > textarea {
  border: 1.5px solid var(--border-input) !important;
  border-radius: var(--radius-sm) !important;
  background: var(--bg-card) !important;
}
.stTextArea > div > div > textarea:focus {
  border-color: #008485 !important;
  box-shadow: 0 0 0 3px rgba(0,132,133,0.1) !important;
}

[data-testid="stForm"] {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 24px;
}

.crm-section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin: var(--sp-xl) 0 var(--sp-md) 0;
  padding: 9px 16px;
  background: var(--bg-section);
  border-left: 3px solid var(--primary);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  letter-spacing: 0.01em;
}

.crm-page-header {
  background: var(--bg-card);
  padding: 18px 24px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
}
.crm-page-header h1 {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 3px 0;
}
.crm-page-header p {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}

.crm-kpi {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 18px 22px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
}
.crm-kpi::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--primary);
}
.crm-kpi-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 8px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.crm-kpi-value {
  font-size: 26px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.1;
}
.crm-kpi-unit {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  margin-left: 3px;
}
.crm-kpi--accent::before { background: var(--accent); }
.crm-kpi--success::before { background: var(--color-success); }
.crm-kpi--warning::before { background: var(--color-warning); }

[data-testid="stDataFrame"] {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] th { color: #1a1a2e !important; }

@media print {
  [data-testid="stSidebar"],
  [data-testid="stHeader"],
  .stButton, .no-print { display: none !important; }
  .stApp, .block-container {
    background: white !important;
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100% !important;
  }
}
</style>"""

CSS_PAGES = {
    "customer": """<style>
.page-customer .memo-item {
  background: var(--bg-card);
  padding: 14px 18px;
  margin-bottom: 8px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  border-left: 3px solid var(--primary);
}
</style>""",
    "report": """<style>
.page-report .report-wrap {
  background: var(--bg-card);
  padding: 40px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}
@media print {
  .page-report .report-wrap { box-shadow: none; padding: 0; }
}
</style>""",
    "bms": """<style>
.page-bms .upload-zone {
  background: var(--bg-card);
  border: 2px dashed var(--border-medium);
  border-radius: var(--radius-md);
  padding: var(--sp-2xl);
  text-align: center;
}
</style>""",
    "login": """<style>
.page-login [data-testid="stForm"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius-lg) !important;
  padding: 44px 36px 32px !important;
  box-shadow: var(--shadow-lg) !important;
  max-width: 420px;
  margin: 0 auto;
}
.page-login .login-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: var(--text-muted);
}
</style>"""
}


def inject_all_css():
    st.markdown(CSS_VARIABLES, unsafe_allow_html=True)
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


def inject_page_css(k):
    css = CSS_PAGES.get(k, "")
    if css:
        st.markdown(css, unsafe_allow_html=True)


def page_wrapper_open(k):
    st.markdown(f'<div class="page-{k}">', unsafe_allow_html=True)


def page_wrapper_close():
    st.markdown('</div>', unsafe_allow_html=True)


def render_kpi(label, value, unit="건", color=None, variant=""):
    cs = f'color:{color};' if color else ''
    vc = f' crm-kpi--{variant}' if variant else ''
    return (
        f'<div class="crm-kpi{vc}">'
        f'<div class="crm-kpi-label">{label}</div>'
        f'<div class="crm-kpi-value" style="{cs}">{value}'
        f'<span class="crm-kpi-unit">{unit}</span></div>'
        f'</div>'
    )


def render_page_header(title, desc=""):
    d = f'<p>{desc}</p>' if desc else ''
    st.markdown(
        f'<div class="crm-page-header"><h1>{title}</h1>{d}</div>',
        unsafe_allow_html=True
    )


def render_section_title(text):
    st.markdown(
        f'<div class="crm-section-title">{text}</div>',
        unsafe_allow_html=True
    )
