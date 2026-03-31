# -*- coding: utf-8 -*-
"""
고객 관리 시스템 - 메인 진입점
각 메뉴의 코드는 modules/ 폴더 안에 있습니다.
"""
import streamlit as st
import datetime
import time
import pandas as pd

from config import COMPANY_CODE, ADMIN_CODE
from style import inject_all_css, inject_page_css, page_wrapper_open, page_wrapper_close
from auth import (
    init_session, login_success, logout_user,
    hash_password, check_password, get_user_role, get_visible_menus, add_user
)
from data import get_current_df, load_data_from_sheet, analyze_alerts, get_users, log_action

# ── 각 메뉴 페이지 ──
from pages import dashboard as page_dashboard
from pages import customer as page_customer
from pages import alerts as page_alerts
from pages import my_stats as page_my_stats
from pages import bms as page_bms
from pages import report as page_report
from pages import log_analysis as page_log_analysis
from pages import system_log as page_system_log
from pages import user_mgmt as page_user_mgmt

# ══════════════════════════════════════════════════
# 페이지 설정
# ══════════════════════════════════════════════════
st.set_page_config(
    page_title="고객 관리 시스템",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={}
)
st.markdown("""<style>
#MainMenu {visibility: hidden !important;}
.stDeployButton {display: none !important;}
[data-testid="manage-app-button"] {display: none !important;}
button[kind="header"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
.stAppDeployButton {display: none !important;}
header [data-testid="stToolbarActions"] > div:last-child {display: none !important;}
footer {visibility: hidden !important;}
[data-testid="stSidebarNav"] {display: none !important;}
section[data-testid="stSidebarNav"] {display: none !important;}
[data-testid="collapsedControl"] {display: none !important;}
</style>""", unsafe_allow_html=True)

inject_all_css()
init_session()

if 'login_status' not in st.session_state:
    st.session_state['login_status'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = ""

# 로그인 상태에 따라 사이드바 제어
if not st.session_state['login_status']:
    st.markdown("""<style>
    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    .main .block-container {max-width: 100% !important; padding: 0 !important;}
    </style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>
    [data-testid="stSidebar"] {display: flex !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    </style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# 로그인 화면
# ══════════════════════════════════════════════════
if not st.session_state['login_status']:
    inject_page_css("login")
    page_wrapper_open("login")
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'login'
    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    with c2:
        st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
        if st.session_state['auth_mode'] == 'login':
            with st.form("login_form"):
                st.markdown('<div style="text-align:center;margin-bottom:28px;"><div style="font-size:36px;margin-bottom:10px;">📋</div><div style="font-size:24px;font-weight:800;color:#008485;">고객 관리 시스템</div><div style="font-size:13px;color:#8c95a6;margin-top:6px;">업무를 위해 로그인해 주세요</div></div>', unsafe_allow_html=True)
                id_ = st.text_input("아이디", placeholder="아이디를 입력하세요")
                pw_ = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
                if st.form_submit_button("로그인", type="primary", use_container_width=True):
                    with st.spinner("🔐 로그인 중..."):
                        db = get_users()
                        if str(id_) in db and check_password(pw_, db[str(id_)]["password"]):
                            login_success(str(id_), db[str(id_)].get("role", "user"))
                            log_action(str(id_), "Login", "접속")
                        else:
                            st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
            st.markdown('<div class="login-footer" style="text-align:center;margin-top:20px;font-size:13px;color:#8c95a6;">계정이 없으신가요?</div>', unsafe_allow_html=True)
            if st.button("회원가입", use_container_width=True):
                st.session_state['auth_mode'] = 'join'; st.rerun()
        else:
            with st.form("join_form"):
                st.markdown('<div style="text-align:center;margin-bottom:28px;"><div style="font-size:36px;margin-bottom:10px;">📋</div><div style="font-size:24px;font-weight:800;color:#008485;">회원가입</div><div style="font-size:13px;color:#8c95a6;margin-top:6px;">관리자에게 인증코드를 발급받은 후 가입하세요</div></div>', unsafe_allow_html=True)
                n1 = st.text_input("아이디", placeholder="사용할 아이디")
                n2 = st.text_input("비밀번호", type="password", placeholder="비밀번호")
                n3 = st.text_input("인증코드", placeholder="관리자 발급 코드")
                if st.form_submit_button("가입하기", type="primary", use_container_width=True):
                    if n1 and n2:
                        if n3 == ADMIN_CODE:
                            add_user(n1, hash_password(n2), "admin"); st.success("관리자 가입 완료!"); time.sleep(0.8); st.session_state['auth_mode'] = 'login'; st.rerun()
                        elif n3 == COMPANY_CODE:
                            add_user(n1, hash_password(n2), "user"); st.success("가입 완료!"); time.sleep(0.8); st.session_state['auth_mode'] = 'login'; st.rerun()
                        else:
                            st.error("인증코드가 올바르지 않습니다.")
                    else:
                        st.error("아이디와 비밀번호를 입력해 주세요.")
            st.markdown('<div style="text-align:center;margin-top:20px;font-size:13px;color:#8c95a6;">이미 계정이 있으신가요?</div>', unsafe_allow_html=True)
            if st.button("로그인으로 돌아가기", use_container_width=True):
                st.session_state['auth_mode'] = 'login'; st.rerun()
    page_wrapper_close()

# ══════════════════════════════════════════════════
# 로그인 후 - 사이드바 + 메뉴 라우팅
# ══════════════════════════════════════════════════
else:
    if 'local_df' not in st.session_state or st.session_state.get('local_df') is None or (isinstance(st.session_state.get('local_df'), pd.DataFrame) and st.session_state['local_df'].empty):
        lp = st.empty()
        lp.markdown('<div style="display:flex;flex-direction:column;align-items:center;padding:80px 20px;text-align:center;"><div style="width:60px;height:60px;border:4px solid #e0f2f2;border-top:4px solid #008485;border-radius:50%;animation:spin .8s linear infinite;margin-bottom:24px;"></div><div style="font-size:18px;font-weight:700;color:#008485;">데이터를 불러오는 중입니다</div></div><style>@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>', unsafe_allow_html=True)
        df0, msg0 = load_data_from_sheet()
        if df0 is not None:
            st.session_state['local_df'] = df0
        else:
            st.error(f"데이터 로드 실패: {msg0}")
        lp.empty()

    if 'menu_selection' not in st.session_state:
        st.session_state['menu_selection'] = "메인화면"

    def set_menu(m):
        st.session_state['menu_selection'] = m

    # ── 사이드바 ──
    with st.sidebar:
        role = get_user_role()
        uid = st.session_state.get('current_user', '')
        rl = "🔑 관리자" if role == "admin" else "👤 사용자"
        rc = "#5ef0f1" if role == "admin" else "#e2e8f0"
        rb = "rgba(0,132,133,0.25)" if role == "admin" else "rgba(255,255,255,0.08)"
        rbd = "rgba(0,132,133,0.4)" if role == "admin" else "rgba(255,255,255,0.1)"

        st.markdown(f'<div style="text-align:center;padding:24px 0 12px;"><div style="width:44px;height:44px;background:linear-gradient(135deg,#008485,#006a6b);border-radius:12px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:22px;">📋</div><div style="font-size:15px;font-weight:700;color:#e2e8f0!important;">고객 관리 시스템</div></div><div style="margin:8px 12px 4px;padding:14px 16px;background:{rb};border-radius:10px;border:1px solid {rbd};"><div style="display:flex;align-items:center;justify-content:space-between;"><div style="font-size:18px;font-weight:800;color:{rc}!important;">{uid}</div><div style="font-size:11px;font-weight:600;color:rgba(255,255,255,0.5)!important;background:rgba(255,255,255,0.08);padding:3px 10px;border-radius:20px;">{rl}</div></div></div>', unsafe_allow_html=True)

        try:
            sdf = st.session_state.get('local_df', pd.DataFrame())
            tc = len(sdf) if not sdf.empty else 0
            tdc = 0
            if not sdf.empty and '신규접수일' in sdf.columns:
                tdc = sdf['신규접수일'].astype(str).str.strip().eq(str(datetime.date.today())).sum()
            ad = analyze_alerts(sdf)
            at = len(ad.get("critical", [])) + len(ad.get("warning", []))
        except:
            tc, tdc, at = 0, 0, 0

        ab = (f'<span style="background:#E90061;color:#fff;font-size:10px;font-weight:800;padding:2px 6px;border-radius:10px;margin-left:4px;">{at}</span>') if at > 0 else ''
        st.markdown(f'<div style="margin:6px 12px 4px;display:flex;gap:8px;"><div style="flex:1;padding:10px 12px;background:rgba(255,255,255,0.06);border-radius:8px;border:1px solid rgba(255,255,255,0.08);"><div style="font-size:10px;font-weight:600;color:rgba(255,255,255,0.4)!important;">총 고객수</div><div style="font-size:17px;font-weight:800;color:#5ef0f1!important;">{tc:,}</div></div><div style="flex:1;padding:10px 12px;background:rgba(255,255,255,0.06);border-radius:8px;border:1px solid rgba(255,255,255,0.08);"><div style="font-size:10px;font-weight:600;color:rgba(255,255,255,0.4)!important;">알림 {ab}</div><div style="font-size:17px;font-weight:800;color:#f0c05e!important;">{tdc} <span style="font-size:11px;color:rgba(255,255,255,0.35)!important;">당일</span></div></div></div>', unsafe_allow_html=True)
        st.markdown("---")

        for icon, label in get_visible_menus():
            bl = f"{icon}  {label}"
            if label == "알림센터" and at > 0:
                bl = f"{icon}  {label} ({at})"
            if st.button(bl, use_container_width=True, type="primary" if st.session_state['menu_selection'] == label else "secondary"):
                set_menu(label); st.rerun()

        st.markdown("---")
        if st.button("🔄  데이터 최신화", use_container_width=True):
            st.cache_data.clear()
            for k in ['local_df', 'all_memos', 'all_timeline']:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
        if st.button("🚪  로그아웃", use_container_width=True):
            logout_user()

    # ── 메뉴 라우팅 ──
    menu = st.session_state['menu_selection']

    if menu == "메인화면":
        page_dashboard.render()
    elif menu == "고객 관리":
        page_customer.render()
    elif menu == "알림센터":
        page_alerts.render()
    elif menu == "나의 실적":
        page_my_stats.render()
    elif menu == "CMS 실적 확인":
        page_bms.render()
    elif menu == "종합 보고서":
        page_report.render()
    elif menu == "로그 분석":
        page_log_analysis.render()
    elif menu == "시스템 로그":
        page_system_log.render()
    elif menu == "사용자 관리":
        page_user_mgmt.render()
