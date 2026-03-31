# -*- coding: utf-8 -*-
"""사용자 관리 페이지"""

import streamlit as st
import pandas as pd
import json
import time

from style import render_page_header, render_section_title
from data import get_client, log_action
from auth import load_user_menu_settings, save_user_menu_settings
from config import GOOGLE_SHEET_URL, SHEET_USERS, MENU_SETTINGS_KEY, ALL_MENUS, ADMIN_ONLY_MENUS


def render():
    render_page_header("사용자 관리", "등록된 사용자 조회 및 역할 관리")
    try:
        if 'user_mgmt_data' not in st.session_state or st.session_state.get('user_mgmt_refresh', False):
            cl = get_client()
            if cl:
                ws = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_USERS)
                st.session_state['user_mgmt_ws'] = ws
                st.session_state['user_mgmt_data'] = ws.get_all_records()
            else:
                st.session_state['user_mgmt_data'] = []
            st.session_state['user_mgmt_refresh'] = False

        ur = st.session_state['user_mgmt_data']
        ws = st.session_state.get('user_mgmt_ws')
        ru = [r for r in ur if str(r.get('username', '')).strip() != MENU_SETTINGS_KEY]

        if ru:
            render_section_title("등록된 사용자 목록")
            udf = pd.DataFrame(ru)
            dc = [c for c in udf.columns if c != 'password']
            st.dataframe(udf[dc], use_container_width=True, hide_index=True)

            render_section_title("역할 변경")
            uc1, uc2, uc3 = st.columns([2, 1, 1])
            with uc1:
                uns = [str(r.get('username', '')) for r in ru]
                su = st.selectbox("사용자 선택", uns)
            with uc2:
                nr = st.selectbox("변경할 역할", ["user", "admin"])
            with uc3:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("✅ 역할 변경", type="primary", use_container_width=True):
                    try:
                        cell = ws.find(su, in_column=1)
                        if cell:
                            ws.update_cell(cell.row, 3, nr)
                            st.cache_data.clear()
                            st.session_state['user_mgmt_refresh'] = True
                            st.success(f"'{su}' → '{nr}' 변경 완료")
                            log_action(st.session_state.get('current_user', ''), "RoleChange", f"{su}→{nr}")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"변경 실패: {e}")

        render_section_title("일반 사용자 메뉴 설정")
        st.info("체크된 메뉴만 일반 사용자에게 표시됩니다.")
        cs = load_user_menu_settings()
        tgm = [(i, l) for i, l in ALL_MENUS if l not in ADMIN_ONLY_MENUS]
        ns = []
        cols = st.columns(len(tgm))
        for i, (icon, label) in enumerate(tgm):
            with cols[i]:
                ck = st.checkbox(f"{icon} {label}", value=(label in cs), key=f"mt_{label}")
                if ck:
                    ns.append(label)

        if st.button("💾 메뉴 설정 저장", type="primary"):
            if not ns:
                st.error("최소 1개 이상 선택해 주세요.")
            else:
                save_user_menu_settings(ns)
                st.success(f"{len(ns)}개 메뉴 저장 완료!")
                time.sleep(1)
                st.rerun()

        st.markdown("---")
        if st.button("🔄 사용자 목록 새로고침", use_container_width=True):
            st.session_state['user_mgmt_refresh'] = True
            st.rerun()

    except Exception as e:
        st.error(f"오류: {e}")
