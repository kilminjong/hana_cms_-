# -*- coding: utf-8 -*-
import streamlit as st

# ──────────────────────────────────────────────────
# 디자인 토큰
# ──────────────────────────────────────────────────
CSS_VARIABLES = """<style>
:root {
  /* 브랜드 */
  --primary: #008485;
  --primary-hover: #006a6b;
  --primary-light: #e0f7f7;

  /* 사이드바 */
  --sidebar-bg: #0f1923;
  --sidebar-hover: rgba(255,255,255,0.06);
  --sidebar-active-bg: rgba(0,132,133,0.18);
  --sidebar-active-border: #008485;
  --sidebar-text: #94a3b8;
  --sidebar-text-active: #e2e8f0;

  /* 콘텐츠 배경 */
  --bg-page: #f4f6f8;
  --bg-card: #ffffff;
  --bg-muted: #f8fafc;

  /* 텍스트 */
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;

  /* 보더 */
  --border: #e5e7eb;
  --border-focus: #008485;

  /* 상태 */
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #3b82f6;

  /* 그림자 */
  --shadow-card: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.05);

  /* 반경 */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  --font: 'Pretendard', -apple-system, 'Malgun Gothic', sans-serif;
}
</style>"""

CSS_GLOBAL = """<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"] {
  font-family: var(--font) !important;
  color-scheme: light !important;
}

/* ── UI 숨김 ── */
#MainMenu { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebarNav"] { display: none !important; }
footer { visibility: hidden !important; }
[data-testid="stHeader"] { background: transparent !important; }

/* ── 메인 콘텐츠 여백 ── */
.block-container {
  padding-top: 2rem !important;
  padding-bottom: 2rem !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  max-width: 1200px !important;
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
  background: var(--sidebar-bg) !important;
  border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding-top: 0 !important;
}
[data-testid="stSidebar"] hr {
  border-color: rgba(255,255,255,0.07) !important;
  margin: 8px 0 !important;
}

/* 사이드바 메뉴 버튼 */
[data-testid="stSidebar"] .stButton > button {
  text-align: left !important;
  justify-content: flex-start !important;
  border-radius: var(--radius-sm) !important;
  border: none !important;
  background: transparent !important;
  color: var(--sidebar-text) !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  padding: 9px 14px !important;
  transition: all .15s ease !important;
  margin-bottom: 2px !important;
  width: 100% !important;
  letter-spacing: 0 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--sidebar-hover) !important;
  color: var(--sidebar-text-active) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: var(--sidebar-active-bg) !important;
  color: #4dd8d9 !important;
  border-left: 2px solid var(--sidebar-active-border) !important;
  font-weight: 600 !important;
  padding-left: 12px !important;
}

/* ── 메인 버튼 ── */
div.stButton > button {
  border-radius: var(--radius-md) !important;
  font-weight: 500 !important;
  font-size: 13.5px !important;
  transition: all .15s ease !important;
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border) !important;
  height: 38px !important;
}
div.stButton > button[kind="primary"] {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: #ffffff !important;
}
div.stButton > button[kind="primary"]:hover {
  background: var(--primary-hover) !important;
  border-color: var(--primary-hover) !important;
}
div.stButton > button:not([kind="primary"]):hover {
  border-color: var(--primary) !important;
  color: var(--primary) !important;
}

/* ── 폼 ── */
[data-testid="stForm"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  padding: 20px !important;
}

/* ── 입력 필드 ── */
.stTextInput > div > div {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  overflow: hidden !important;
  transition: border-color .15s !important;
}
.stTextInput > div > div > input {
  background: transparent !important;
  color: var(--text-primary) !important;
  border: none !important;
  box-shadow: none !important;
  font-size: 13.5px !important;
  padding: 9px 12px !important;
  -webkit-text-fill-color: var(--text-primary) !important;
}
.stTextInput > div > div:focus-within {
  border-color: var(--border-focus) !important;
  box-shadow: 0 0 0 2px rgba(0,132,133,0.12) !important;
}
.stTextInput > div > div > input::placeholder {
  color: var(--text-muted) !important;
  -webkit-text-fill-color: var(--text-muted) !important;
}
.stTextInput > label, .stSelectbox > label,
.stMultiSelect > label, .stDateInput > label, .stTextArea > label {
  font-weight: 500 !important;
  font-size: 12.5px !important;
  color: var(--text-secondary) !important;
  margin-bottom: 4px !important;
}
.stTextInput > div > div > button {
  background: transparent !important;
  border: none !important;
  color: var(--text-muted) !important;
}
.stSelectbox > div > div {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  background: var(--bg-card) !important;
  font-size: 13.5px !important;
  color: var(--text-primary) !important;
}
.stMultiSelect > div > div {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  background: var(--bg-card) !important;
}
.stTextArea > div > div > textarea {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
  font-size: 13.5px !important;
}
.stTextArea > div > div > textarea:focus {
  border-color: var(--border-focus) !important;
  box-shadow: 0 0 0 2px rgba(0,132,133,0.12) !important;
}

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
  gap: 0 !important;
  background: var(--bg-card) !important;
  border-radius: var(--radius-md) var(--radius-md) 0 0 !important;
  padding: 0 !important;
  border-bottom: 2px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 0 !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  padding: 10px 20px !important;
  color: var(--text-secondary) !important;
  background: transparent !important;
  border-bottom: 2px solid transparent !important;
  margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
  color: var(--primary) !important;
  border-bottom: 2px solid var(--primary) !important;
  font-weight: 600 !important;
  background: transparent !important;
}

/* ── 데이터프레임 ── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  overflow: hidden !important;
}

/* ── 섹션 구분선 ── */
.crm-divider {
  height: 1px;
  background: var(--border);
  margin: 20px 0;
}

/* ── 페이지 제목 ── */
.crm-page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
  letter-spacing: -0.02em;
}
.crm-page-subtitle {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 0 24px 0;
}

/* ── 카드 ── */
.crm-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-card);
}

/* ── KPI 카드 ── */
.crm-kpi {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 22px;
  box-shadow: var(--shadow-card);
}
.crm-kpi-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.crm-kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  letter-spacing: -0.02em;
}
.crm-kpi-unit {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-left: 4px;
}

/* ── 섹션 타이틀 ── */
.crm-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 24px 0 12px 0;
  padding: 0;
  border: none;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ── 페이지 헤더 ── */
.crm-page-header {
  margin-bottom: 24px;
}
.crm-page-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 2px 0;
  letter-spacing: -0.02em;
}
.crm-page-header p {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}

/* ── 뱃지 ── */
.crm-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}

/* ── 인쇄 ── */
@media print {
  [data-testid="stSidebar"], [data-testid="stHeader"],
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
  border: 1px solid var(--border);
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
  border: 2px dashed var(--border);
  border-radius: var(--radius-md);
  padding: 48px;
  text-align: center;
}
</style>""",
    "login": """<style>
.page-login { }
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
    return (
        f'<div class="crm-kpi">'
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
