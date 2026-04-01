# -*- coding: utf-8 -*-
import streamlit as st
import datetime
import time
import pandas as pd
import base64

from config import COMPANY_CODE, ADMIN_CODE
from style import inject_all_css, inject_page_css, page_wrapper_open, page_wrapper_close
from auth import (
    init_session, login_success, logout_user,
    hash_password, check_password, get_user_role, get_visible_menus, add_user
)
from data import (
    get_current_df, load_data_from_sheet, analyze_alerts,
    get_users, log_action, save_user_bg, get_user_bg,
    upload_bg_image_to_drive, delete_bg_image_from_drive
)

from pages import dashboard as page_dashboard
from pages import customer as page_customer
from pages import alerts as page_alerts
from pages import my_stats as page_my_stats
from pages import bms as page_bms
from pages import report as page_report
from pages import log_analysis as page_log_analysis
from pages import system_log as page_system_log
from pages import user_mgmt as page_user_mgmt

st.set_page_config(
    page_title="고객 관리 시스템",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# ── 공통 숨김 CSS (배경색 없음 — 동적 적용)
st.markdown("""
<style>
html, body, .stApp { color: #1a1a2e !important; color-scheme: light !important; }
#MainMenu { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebarNav"] { display: none !important; }
footer { visibility: hidden !important; }
[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 3.5rem !important; padding-bottom: 1rem !important; }
[data-testid="stSidebar"] > div:first-child { padding-top: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)

inject_all_css()
init_session()

if 'login_status' not in st.session_state:
    st.session_state['login_status'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = ""


# ══════════════════════════════════════════════════
# 배경 적용 함수 — sidebar 블록 밖에서 호출
# ══════════════════════════════════════════════════
def apply_background(uid):
    bg_key = f"bg_{uid}"
    bg_val = st.session_state.get(bg_key, "#f0f2f5")

    # 드라이브 URL이거나 색상값
    if bg_val.startswith("http"):
        bg_css = f"""
            background-image: url('{bg_val}') !important;
            background-size: cover !important;
            background-attachment: fixed !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-color: transparent !important;"""
        transition = ""
    elif bg_val.startswith("data:image"):
        # base64는 세션에만 임시 적용 (드라이브 업로드 완료 전)
        bg_css = f"""
            background-image: url('{bg_val}') !important;
            background-size: cover !important;
            background-attachment: fixed !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-color: transparent !important;"""
        transition = ""
    else:
        bg_css = f"background-color: {bg_val} !important;"
        transition = "transition: background-color 0.3s ease !important;"

    st.markdown(f"""<style>
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main,
[data-testid="stAppViewContainer"] > section:not([data-testid="stSidebar"]) {{
    {bg_css}
    {transition}
}}
.block-container, [data-testid="block-container"] {{
    background: transparent !important;
    background-color: transparent !important;
}}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
    background: linear-gradient(180deg, #1a2332 0%, #141c28 100%) !important;
}}
</style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# 로그인 화면
# ══════════════════════════════════════════════════
if not st.session_state['login_status']:
    st.markdown("""<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%) !important;
    min-height: 100vh !important;
}
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stHeader"] { display: none !important; }
.block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
[data-testid="stForm"] {
    background: rgba(255,255,255,0.97) !important;
    border-radius: 20px !important;
    padding: 44px 40px 36px !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.35) !important;
    border: none !important;
}
.stTextInput > div > div {
    background: #f8fafc !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
.stTextInput > div > div > input {
    background: transparent !important;
    color: #1a1a2e !important;
    border: none !important;
    padding: 11px 14px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    -webkit-text-fill-color: #1a1a2e !important;
}
.stTextInput > div > div:focus-within {
    border-color: #008485 !important;
    box-shadow: 0 0 0 3px rgba(0,132,133,0.12) !important;
    background: #ffffff !important;
}
.stTextInput > label { font-size: 13px !important; font-weight: 600 !important; color: #4a5568 !important; }
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #008485, #006a6b) !important;
    border: none !important; border-radius: 10px !important;
    padding: 12px !important; font-size: 15px !important;
    font-weight: 700 !important; letter-spacing: 0.02em !important;
    box-shadow: 0 4px 15px rgba(0,132,133,0.4) !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(0,132,133,0.5) !important;
}
div.stButton > button[kind="secondary"] {
    background: #f8fafc !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important;
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
div.stButton > button[kind="secondary"]:hover {
    background: #f0f4f8 !important;
    border-color: #008485 !important;
    color: #008485 !important;
}
</style>""", unsafe_allow_html=True)

    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'login'

    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    with c2:
        st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
        if st.session_state['auth_mode'] == 'login':
            with st.form("login_form"):
                st.markdown('''<div style="text-align:center;margin-bottom:32px;">
  <div style="width:56px;height:56px;background:linear-gradient(135deg,#008485,#006a6b);border-radius:16px;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:26px;box-shadow:0 8px 24px rgba(0,132,133,0.35);">📋</div>
  <div style="font-size:22px;font-weight:800;color:#1a1a2e;letter-spacing:-0.02em;">고객 관리 시스템</div>
  <div style="font-size:13px;color:#8c95a6;margin-top:6px;font-weight:500;">하나은행 CMS · 업무를 위해 로그인해 주세요</div>
</div>''', unsafe_allow_html=True)
                id_ = st.text_input("아이디", placeholder="아이디를 입력하세요", autocomplete="username")
                pw_ = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", autocomplete="current-password")
                if st.form_submit_button("로그인", type="primary", use_container_width=True):
                    with st.spinner("로그인 중..."):
                        db = get_users()
                        if str(id_) in db and check_password(pw_, db[str(id_)]["password"]):
                            login_success(str(id_), db[str(id_)].get("role", "user"))
                            log_action(str(id_), "Login", "접속")
                            # ★ 구글시트에서 저장된 배경 불러오기
                            saved_bg = get_user_bg(str(id_))
                            if saved_bg:
                                st.session_state[f"bg_{str(id_)}"] = saved_bg
                            else:
                                st.session_state[f"bg_{str(id_)}"] = "#f0f2f5"
                            st.rerun()
                        else:
                            st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
            st.markdown('''
<div style="margin-top:20px;padding-top:18px;border-top:1px solid #f0f0f0;text-align:center;">
  <span style="font-size:13px;color:#8c95a6;">계정이 없으신가요?</span>
</div>''', unsafe_allow_html=True)
            if st.button("회원가입하기", use_container_width=True, key="goto_join"):
                st.session_state['auth_mode'] = 'join'
                st.rerun()
        else:
            with st.form("join_form"):
                st.markdown('''<div style="text-align:center;margin-bottom:32px;">
  <div style="width:56px;height:56px;background:linear-gradient(135deg,#008485,#006a6b);border-radius:16px;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:26px;box-shadow:0 8px 24px rgba(0,132,133,0.35);">📋</div>
  <div style="font-size:22px;font-weight:800;color:#1a1a2e;letter-spacing:-0.02em;">회원가입</div>
  <div style="font-size:13px;color:#8c95a6;margin-top:6px;font-weight:500;">관리자에게 인증코드를 발급받은 후 가입하세요</div>
</div>''', unsafe_allow_html=True)
                n1 = st.text_input("아이디", placeholder="사용할 아이디", autocomplete="off")
                n2 = st.text_input("비밀번호", type="password", placeholder="영문+숫자 8자리 이상", autocomplete="new-password")
                n3 = st.text_input("인증코드", placeholder="관리자 발급 코드", autocomplete="off")
                if st.form_submit_button("가입하기", type="primary", use_container_width=True):
                    import re as _re
                    def validate_pw(pw):
                        if len(pw) < 8: return False, "비밀번호는 8자리 이상이어야 합니다."
                        if not _re.search(r'[A-Za-z]', pw): return False, "비밀번호에 영문자가 포함되어야 합니다."
                        if not _re.search(r'[0-9]', pw): return False, "비밀번호에 숫자가 포함되어야 합니다."
                        return True, "OK"
                    if not n1 or not n2:
                        st.error("아이디와 비밀번호를 입력해 주세요.")
                    else:
                        pw_ok, pw_msg = validate_pw(n2)
                        if not pw_ok:
                            st.error(pw_msg)
                        elif n3 == ADMIN_CODE:
                            add_user(n1, hash_password(n2), "admin")
                            st.success("관리자 가입 완료!")
                            time.sleep(0.8)
                            st.session_state['auth_mode'] = 'login'
                            st.rerun()
                        elif n3 == COMPANY_CODE:
                            add_user(n1, hash_password(n2), "user")
                            st.success("가입 완료!")
                            time.sleep(0.8)
                            st.session_state['auth_mode'] = 'login'
                            st.rerun()
                        else:
                            st.error("인증코드가 올바르지 않습니다.")
            st.markdown('''
<div style="margin-top:20px;padding-top:18px;border-top:1px solid #f0f0f0;text-align:center;">
  <span style="font-size:13px;color:#8c95a6;">이미 계정이 있으신가요?</span>
</div>''', unsafe_allow_html=True)
            if st.button("로그인으로 돌아가기", use_container_width=True, key="goto_login"):
                st.session_state['auth_mode'] = 'login'
                st.rerun()

# ══════════════════════════════════════════════════
# 로그인 후
# ══════════════════════════════════════════════════
else:
    uid = st.session_state.get('current_user', '')
    bg_key = f"bg_{uid}"

    # ★ 배경 CSS — sidebar 블록 밖에서 가장 먼저 적용
    apply_background(uid)

    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: flex !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    if 'local_df' not in st.session_state or st.session_state.get('local_df') is None or (
            isinstance(st.session_state.get('local_df'), pd.DataFrame) and st.session_state['local_df'].empty):
        lp = st.empty()
        lp.markdown('<div style="display:flex;flex-direction:column;align-items:center;padding:60px 20px;text-align:center;"><div style="width:50px;height:50px;border:4px solid #e0f2f2;border-top:4px solid #008485;border-radius:50%;animation:spin .8s linear infinite;margin-bottom:20px;"></div><div style="font-size:16px;font-weight:700;color:#008485;">데이터를 불러오는 중입니다</div></div><style>@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>', unsafe_allow_html=True)
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
        rl = "관리자" if role == "admin" else "사용자"
        rc = "#5ef0f1" if role == "admin" else "#e2e8f0"
        rb = "rgba(0,132,133,0.25)" if role == "admin" else "rgba(255,255,255,0.08)"
        rbd = "rgba(0,132,133,0.4)" if role == "admin" else "rgba(255,255,255,0.1)"

        st.markdown(f'''
        <div style="padding:12px 0 8px;text-align:center;">
          <div style="width:38px;height:38px;background:linear-gradient(135deg,#008485,#006a6b);border-radius:10px;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;font-size:18px;">📋</div>
          <div style="font-size:13px;font-weight:700;color:#e2e8f0!important;">고객 관리 시스템</div>
        </div>
        <div style="margin:4px 10px 6px;padding:10px 12px;background:{rb};border-radius:8px;border:1px solid {rbd};">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div style="font-size:15px;font-weight:800;color:{rc}!important;">{uid}</div>
            <div style="font-size:10px;color:rgba(255,255,255,0.5)!important;background:rgba(255,255,255,0.08);padding:2px 7px;border-radius:20px;">{rl}</div>
          </div>
        </div>
        ''', unsafe_allow_html=True)

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
        st.markdown(f'''
        <div style="margin:4px 10px 6px;display:flex;gap:6px;">
          <div style="flex:1;padding:8px 10px;background:rgba(255,255,255,0.06);border-radius:8px;border:1px solid rgba(255,255,255,0.08);">
            <div style="font-size:9px;font-weight:600;color:rgba(255,255,255,0.4)!important;text-transform:uppercase;">총 고객수</div>
            <div style="font-size:15px;font-weight:800;color:#5ef0f1!important;">{tc:,}</div>
          </div>
          <div style="flex:1;padding:8px 10px;background:rgba(255,255,255,0.06);border-radius:8px;border:1px solid rgba(255,255,255,0.08);">
            <div style="font-size:9px;font-weight:600;color:rgba(255,255,255,0.4)!important;text-transform:uppercase;">알림 {ab}</div>
            <div style="font-size:15px;font-weight:800;color:#f0c05e!important;">{tdc} <span style="font-size:10px;color:rgba(255,255,255,0.35)!important;">당일</span></div>
          </div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown("---")

        for icon, label in get_visible_menus():
            bl = f"{icon}  {label}"
            if label == "알림센터" and at > 0:
                bl = f"{icon}  {label} ({at})"
            if st.button(bl, use_container_width=True,
                         type="primary" if st.session_state['menu_selection'] == label else "secondary"):
                set_menu(label)
                st.rerun()

        st.markdown("---")

        # ── 배경 선택 UI ──
        current_bg = st.session_state.get(bg_key, "#f0f2f5")

        with st.expander("🎨  배경 선택"):
            PRESETS = [
                ("#f0f2f5", "기본"), ("#ffffff", "흰색"),
                ("#dbeafe", "하늘"), ("#dcfce7", "민트"),
                ("#fef3c7", "크림"), ("#f3e8ff", "라벤더"),
                ("#1e293b", "다크"), ("#0f172a", "딥다크"),
            ]
            st.markdown('<p style="color:rgba(255,255,255,0.7);font-size:11px;margin:0 0 6px;">프리셋 색상</p>', unsafe_allow_html=True)
            cols_a = st.columns(4)
            cols_b = st.columns(4)
            for i, (color, name) in enumerate(PRESETS):
                col = cols_a[i] if i < 4 else cols_b[i - 4]
                selected = (current_bg == color)
                border_style = "border:2px solid #5ef0f1;" if selected else "border:1px solid rgba(255,255,255,0.2);"
                with col:
                    st.markdown(
                        f'<div style="height:28px;background:{color};border-radius:5px;{border_style}margin-bottom:2px;"></div>'
                        f'<p style="color:rgba(255,255,255,0.55);font-size:9px;text-align:center;margin:0 0 3px;">{name}</p>',
                        unsafe_allow_html=True
                    )
                    if st.button("✓", key=f"bgp_{i}", use_container_width=True, help=name):
                        st.session_state[bg_key] = color
                        save_user_bg(uid, color)  # 구글시트에 저장
                        st.rerun()

            # 직접 색상
            st.markdown('<p style="color:rgba(255,255,255,0.7);font-size:11px;margin:10px 0 4px;">직접 색상 선택</p>', unsafe_allow_html=True)
            safe_color = current_bg if (current_bg.startswith("#") and len(current_bg) == 7) else "#f0f2f5"
            pc, bc = st.columns([3, 2])
            with pc:
                picked = st.color_picker("색상", value=safe_color, label_visibility="collapsed")
            with bc:
                if st.button("적용", key="apply_color", use_container_width=True):
                    st.session_state[bg_key] = picked
                    save_user_bg(uid, picked)  # 구글시트에 저장
                    st.rerun()

            # ★ 이미지 업로드 — 구글 드라이브에 저장
            st.markdown('<p style="color:rgba(255,255,255,0.7);font-size:11px;margin:10px 0 4px;">이미지 업로드</p>', unsafe_allow_html=True)
            st.markdown('<p style="color:rgba(255,255,255,0.4);font-size:10px;margin:0 0 6px;">구글 드라이브에 저장 → 어느 기기에서도 유지됩니다</p>', unsafe_allow_html=True)

            uploaded = st.file_uploader(
                "이미지", type=["png", "jpg", "jpeg", "webp"],
                label_visibility="collapsed", key="bg_uploader"
            )
            if uploaded is not None:
                if st.session_state.get("bg_uploader_name") != uploaded.name:
                    with st.spinner("드라이브에 업로드 중..."):
                        raw = uploaded.read()
                        ext = uploaded.name.rsplit(".", 1)[-1].lower()
                        # 구글 드라이브에 업로드
                        drive_url = upload_bg_image_to_drive(uid, raw, ext)
                        if drive_url:
                            # 구글시트에 URL 저장
                            saved = save_user_bg(uid, drive_url)
                            st.session_state[bg_key] = drive_url
                            st.session_state["bg_uploader_name"] = uploaded.name
                            if saved:
                                st.success("✅ 저장 완료! 로그인 후에도 유지됩니다")
                            else:
                                err = st.session_state.get('_bg_save_error', '알 수 없음')
                                st.warning(f"⚠️ 드라이브 업로드는 성공했으나 시트 저장 실패: {err}")
                            st.rerun()
                        else:
                            # 드라이브 실패 시 세션에만 임시 적용
                            b64 = base64.b64encode(raw).decode()
                            img_url = f"data:image/{ext};base64,{b64}"
                            st.session_state[bg_key] = img_url
                            st.session_state["bg_uploader_name"] = uploaded.name
                            st.warning("⚠️ 드라이브 업로드 실패. 현재 세션에만 적용됩니다.")
                            st.rerun()

            # 초기화
            if current_bg != "#f0f2f5":
                st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                if st.button("기본으로 초기화", key="reset_bg", use_container_width=True):
                    # 드라이브 이미지도 삭제
                    if current_bg.startswith("http"):
                        delete_bg_image_from_drive(uid)
                    st.session_state[bg_key] = "#f0f2f5"
                    save_user_bg(uid, "#f0f2f5")  # 구글시트 초기화
                    st.rerun()

        st.markdown("---")
        if st.button("데이터 최신화", use_container_width=True):
            st.cache_data.clear()
            for k in ['local_df', 'all_memos', 'all_timeline']:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
        if st.button("로그아웃", use_container_width=True):
            logout_user()

    # ── 메뉴 라우팅 ──
    menu = st.session_state['menu_selection']
    if menu == "메인화면":        page_dashboard.render()
    elif menu == "고객 관리":     page_customer.render()
    elif menu == "알림센터":      page_alerts.render()
    elif menu == "나의 실적":     page_my_stats.render()
    elif menu == "CMS 실적 확인": page_bms.render()
    elif menu == "종합 보고서":   page_report.render()
    elif menu == "로그 분석":     page_log_analysis.render()
    elif menu == "시스템 로그":   page_system_log.render()
    elif menu == "사용자 관리":   page_user_mgmt.render()
