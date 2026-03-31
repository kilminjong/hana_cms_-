# -*- coding: utf-8 -*-
"""시스템 로그 페이지"""

import streamlit as st
from style import render_page_header
from data import get_system_logs


def render():
    render_page_header("시스템 활동 로그", "사용자 활동 이력 조회")
    try:
        with st.spinner("로그 조회 중..."):
            log_df = get_system_logs()
        if not log_df.empty:
            st.dataframe(log_df.iloc[::-1], use_container_width=True, height=500)
            st.download_button(
                "📥 로그 다운로드",
                data=log_df.to_csv(index=False).encode('utf-8-sig'),
                file_name="system_logs.csv", mime="text/csv"
            )
        else:
            st.info("기록된 로그가 없습니다.")
    except:
        st.error("로그를 불러오지 못했습니다.")
