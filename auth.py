# -*- coding: utf-8 -*-
"""
인증/세션 모듈
- 로그인, 로그아웃, 회원가입, 세션 관리
- 비밀번호 암호화 (bcrypt)
"""

import streamlit as st
import bcrypt
import uuid
import time
import json

from config import (
    conn, cur, SESSION_TIMEOUT_SEC, ADMIN_USERS,
    GOOGLE_SHEET_URL, SHEET_USERS, MENU_SETTINGS_KEY,
    DEFAULT_USER_MENUS, ALL_MENUS, ADMIN_ONLY_MENUS
)
from data import get_client, run_in_background, get_users


def init_session():
    """세션 초기화 - 토큰 기반 자동 로그인"""
    try:
        if hasattr(st, "query_params"):
            token = st.query_params.get("token", None)
        else:
            token = st.experimental_get_query_params().get("token", [None])[0]
    except:
        token = None

    if 'login_status' in st.session_state and st.session_state['login_status']:
        if time.time() - st.session_state.get('last_active', 0) > SESSION_TIMEOUT_SEC:
            logout_user()
        else:
            st.session_state['last_active'] = time.time()
        return

    if token:
        cur.execute("SELECT user_id, expiry FROM sessions WHERE token=?", (token,))
        row = cur.fetchone()
        if row:
            user_id, expiry = row
            if time.time() < expiry:
                st.session_state['login_status'] = True
                st.session_state['current_user'] = user_id
                st.session_state['last_active'] = time.time()
                if user_id in ADMIN_USERS:
                    st.session_state['user_role'] = "admin"
                else:
                    db = get_users()
                    st.session_state['user_role'] = db.get(str(user_id), {}).get("role", "user")
                cur.execute("UPDATE sessions SET expiry=? WHERE token=?",
                            (time.time() + SESSION_TIMEOUT_SEC, token))
                conn.commit()
            else:
                cur.execute("DELETE FROM sessions WHERE token=?", (token,))
                conn.commit()


def login_success(user_id, role="user"):
    """로그인 성공 처리"""
    token = str(uuid.uuid4())
    expiry = time.time() + SESSION_TIMEOUT_SEC
    cur.execute("INSERT OR REPLACE INTO sessions(token,user_id,expiry)VALUES(?,?,?)",
                (token, user_id, expiry))
    conn.commit()
    st.session_state['login_status'] = True
    st.session_state['current_user'] = user_id
    st.session_state['last_active'] = time.time()
    st.session_state['user_role'] = role if user_id not in ADMIN_USERS else "admin"
    if hasattr(st, "query_params"):
        st.query_params["token"] = token
    else:
        st.experimental_set_query_params(token=token)
    st.rerun()


def logout_user():
    """로그아웃"""
    try:
        if hasattr(st, "query_params"):
            st.query_params.clear()
        else:
            st.experimental_set_query_params()
    except:
        pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def hash_password(p):
    return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(p, h):
    return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))


def get_user_role():
    uid = st.session_state.get('current_user', '')
    if uid in ADMIN_USERS:
        return "admin"
    return st.session_state.get('user_role', 'user')


@st.cache_data(ttl=120, show_spinner=False)
def load_user_menu_settings():
    try:
        cl = get_client()
        if not cl:
            return DEFAULT_USER_MENUS
        ws = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_USERS)
        records = ws.get_all_records()
        for r in records:
            if str(r.get('username', '')) == MENU_SETTINGS_KEY:
                return json.loads(str(r.get('password', '')))
        return DEFAULT_USER_MENUS
    except:
        return DEFAULT_USER_MENUS


def save_user_menu_settings(ml):
    def _bg(ml2):
        try:
            cl = get_client()
            if not cl:
                return
            ws = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_USERS)
            try:
                cell = ws.find(MENU_SETTINGS_KEY, in_column=1)
                ws.update_cell(cell.row, 2, json.dumps(ml2, ensure_ascii=False))
            except:
                ws.append_row([MENU_SETTINGS_KEY, json.dumps(ml2, ensure_ascii=False), "system"])
        except:
            pass
    run_in_background(_bg, ml)
    load_user_menu_settings.clear()


def get_visible_menus():
    role = get_user_role()
    if role == "admin":
        return ALL_MENUS
    enabled = load_user_menu_settings()
    return [(i, l) for i, l in ALL_MENUS if l in enabled and l not in ADMIN_ONLY_MENUS]


def add_user(u, p, role="user"):
    if 'cached_users' not in st.session_state:
        st.session_state['cached_users'] = {}
    st.session_state['cached_users'][str(u)] = {"password": str(p), "role": role}
    def _bg(u2, p2, r2):
        try:
            cl = get_client()
            if cl:
                cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_USERS).append_row([u2, p2, r2])
        except:
            pass
    run_in_background(_bg, u, p, role)
