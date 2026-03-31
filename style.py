# -*- coding: utf-8 -*-
import streamlit as st

CSS_VARIABLES = """<style>
:root {
  --primary:#008485; --primary-light:#e0f2f2; --primary-dark:#006a6b;
  --accent:#E90061;
  --bg-app:#f0f2f5; --bg-card:#ffffff; --bg-muted:#f7f8fa; --bg-section:#f4f6f9;
  --border-light:#e2e6ea; --border-medium:#c4cdd5; --border-input:#c1c9d2;
  --text-primary:#1a1a2e; --text-secondary:#4a5568; --text-muted:#8c95a6;
  --text-sidebar:#dce4f0;
  --color-success:#0d9f6e; --color-warning:#e67e22; --color-danger:#dc3545;
  --sp-xs:4px; --sp-sm:8px; --sp-md:16px; --sp-lg:24px; --sp-xl:32px; --sp-2xl:48px;
  --radius-sm:6px; --radius-md:10px; --radius-lg:14px;
  --shadow-sm:0 1px 3px rgba(0,0,0,0.06); --shadow-md:0 2px 8px rgba(0,0,0,0.08);
  --shadow-lg:0 8px 24px rgba(0,0,0,0.12); --shadow-card:0 1px 4px rgba(0,0,0,0.06);
  --font-main:'Pretendard',-apple-system,'Malgun Gothic',sans-serif;
}
</style>"""

CSS_GLOBAL = """<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

/* ── 라이트모드 강제 ── */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main, .block-container {
  background-color: #f0f2f5 !important;
  color: #1a1a2e !important;
  color-scheme: light !important;
}

html, body, [class*="css"] { font-family: var(--font-main) !important; }

/* ── UI 숨김 ── */
#MainMenu { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebarNav"] { display: none !important; }
footer { visibility: hidden !important; }

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #1a2332 0%, #141c28 100%) !important;
  border-right: none !important;
}
[data-testid="stSidebar"] * { color: var(--text-sidebar) !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.07) !important; }

[data-testid="stSidebar"] .stButton > button {
  text-align: left !important;
  justify-content: flex-start !important;
  border-radius: var(--radius-sm) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  background: rgba(255,255,255,0.03) !important;
  color: #94a3b8 !important;
  font-weight: 500 !important;
  font-size: 13.5px !important;
  padding: 10px 16px !important;
  transition: all .18s ease !important;
  margin-bottom: 4px !important;
  width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255,255,255,0.07) !important;
  color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: rgba(0,132,133,0.2) !important;
  color: #4dd8d9 !important;
  border: 1px solid rgba(0,132,133,0.4) !important;
  border-left: 3px solid #008485 !important;
  font-weight: 700 !important;
  padding-left: 13px !important;
}

/* ── 메인 버튼 ── */
div.stButton > button {
  border-radius: var(--radius-sm) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  transition: all .18s ease !important;
  background-color: #ffffff !important;
  color: #1a1a2e !important;
  border: 1px solid #e2e6ea !important;
}
div.stButton > button[kind="primary"] {
  background-color: #008485 !important;
  border-color: #008485 !important;
  color: #ffffff !important;
}
div.stButton > button[kind="primary"]:hover {
  background-color: #006a6b !important;
  border-color: #006a6b !important;
}
div.stButton > button[kind="secondary"]:hover {
  border-color: #008485 !important;
  color: #008485 !important;
}

/* ── 폼 배경 ── */
[data-testid="stForm"] {
  background: #ffffff !important;
  border: 1px solid #e2e6ea !important;
  border-radius: var(--radius-md) !important;
  padding: 24px !important;
}

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
  gap: 2px !important;
  background: #ffffff !important;
  border-radius: var(--radius-md) var(--radius-md) 0 0 !important;
  padding: 4px !important;
  border: 1px solid #e2e6ea !important;
  border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: var(--radius-sm) !important;
  font-weight: 600 !important;
  font-size: 13.5px !important;
  padding: 9px 18px !important;
  color: #4a5568 !important;
  background: transparent !important;
}
.stTabs [aria-selected="true"] {
  background: #008485 !important;
  color: #ffffff !important;
}

/* ── 입력 필드 ── */
.stTextInput > div > div > input {
  border: 1.5px solid #c1c9d2 !important;
  border-radius: var(--radius-sm) !important;
  padding: 10px 14px !important;
  font-size: 14px !important;
  background: #ffffff !important;
  color: #1a1a2e !important;
  -webkit-text-fill-color: #1a1a2e !important;
  height: 44px !important;
  box-sizing: border-box !important;
}
/* 비밀번호 눈 아이콘 포함 wrapper */
.stTextInput > div > div {
  background: #ffffff !important;
  border: 1.5px solid #c1c9d2 !important;
  border-radius: var(--radius-sm) !important;
  overflow: hidden !important;
}
.stTextInput > div > div > input {
  border: none !important;
  box-shadow: none !important;
}
.stTextInput > div > div:focus-within {
  border-color: #008485 !important;
  box-shadow: 0 0 0 3px rgba(0,132,133,0.1) !important;
}
/* 눈 아이콘 버튼 */
.stTextInput > div > div > button {
  background: transparent !important;
  border: none !important;
  color: #8c95a6 !important;
  padding: 0 10px !important;
}

.stTextInput > div > div > input::placeholder {
  color: #8c95a6 !important;
  -webkit-text-fill-color: #8c95a6 !important;
}
.stTextInput > label, .stSelectbox > label,
.stMultiSelect > label, .stDateInput > label, .stTextArea > label {
  font-weight: 600 !important;
  font-size: 13px !important;
  color: #4a5568 !important;
}
.stSelectbox > div > div, .stMultiSelect > div > div {
  border: 1.5px solid #c1c9d2 !important;
  border-radius: var(--radius-sm) !important;
  background: #ffffff !important;
  color: #1a1a2e !important;
}
.stTextArea > div > div > textarea {
  border: 1.5px solid #c1c9d2 !important;
  border-radius: var(--radius-sm) !important;
  background: #ffffff !important;
  color: #1a1a2e !important;
}
.stTextArea > div > div > textarea:focus {
  border-color: #008485 !important;
  box-shadow: 0 0 0 3px rgba(0,132,133,0.1) !important;
}

/* ── 섹션 타이틀 ── */
.crm-section-title {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 32px 0 16px 0;
  padding: 9px 16px;
  background: #f4f6f9;
  border-left: 3px solid #008485;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

/* ── 페이지 헤더 ── */
.crm-page-header {
  background: #ffffff;
  padding: 18px 24px;
  border-radius: var(--radius-md);
  border: 1px solid #e2e6ea;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
}
.crm-page-header h1 {
  font-size: 20px;
  font-weight: 800;
  color: #1a1a2e;
  margin: 0 0 3px 0;
}
.crm-page-header p { font-size: 13px; color: #8c95a6; margin: 0; }

/* ── KPI 카드 ── */
.crm-kpi {
  background: #ffffff;
  border-radius: var(--radius-md);
  padding: 18px 22px;
  border: 1px solid #e2e6ea;
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
}
.crm-kpi::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: #008485;
}
.crm-kpi-label {
  font-size: 11px;
  color: #8c95a6;
  margin-bottom: 8px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.crm-kpi-value { font-size: 26px; font-weight: 800; color: #1a1a2e; line-height: 1.1; }
.crm-kpi-unit { font-size: 13px; font-weight: 500; color: #8c95a6; margin-left: 3px; }
.crm-kpi--accent::before { background: #E90061; }
.crm-kpi--success::before { background: #0d9f6e; }
.crm-kpi--warning::before { background: #e67e22; }

/* ── 데이터프레임 ── */
[data-testid="stDataFrame"] {
  border: 1px solid #e2e6ea !important;
  border-radius: var(--radius-md) !important;
  overflow: hidden !important;
}
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] th { color: #1a1a2e !important; }

/* ── 인쇄 ── */
@media print {
  [data-testid="stSidebar"], [data-testid="stHeader"],
  .stButton, .no-print { display: none !important; }
  .stApp, .block-container {
    background: white !important; margin: 0 !important;
    padding: 0 !important; max-width: 100% !important;
  }
}
</style>"""

CSS_PAGES = {
    "customer": """<style>
.page-customer .memo-item {
  background: #ffffff; padding: 14px 18px; margin-bottom: 8px;
  border-radius: 10px; border: 1px solid #e2e6ea; border-left: 3px solid #008485;
}
</style>""",
    "report": """<style>
.page-report .report-wrap {
  background: #ffffff; padding: 40px; border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
@media print { .page-report .report-wrap { box-shadow: none; padding: 0; } }
</style>""",
    "bms": """<style>
.page-bms .upload-zone {
  background: #ffffff; border: 2px dashed #c4cdd5;
  border-radius: 10px; padding: 48px; text-align: center;
}
</style>""",
    "login": """<style>
.page-login [data-testid="stForm"] {
  background: #ffffff !important;
  border: 1px solid #e2e6ea !important;
  border-radius: 14px !important;
  padding: 44px 36px 32px !important;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12) !important;
  max-width: 420px !important;
  margin: 0 auto !important;
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
    st.markdown(f'<div class="crm-page-header"><h1>{title}</h1>{d}</div>', unsafe_allow_html=True)


def render_section_title(text):
    st.markdown(f'<div class="crm-section-title">{text}</div>', unsafe_allow_html=True)
