# -*- coding: utf-8 -*-
"""알림센터 페이지"""

import streamlit as st
import pandas as pd

from style import render_page_header, render_kpi, render_section_title, page_wrapper_open, page_wrapper_close
from data import get_current_df, analyze_alerts
from config import REMINDER_DAYS_PENDING, REMINDER_DAYS_LINKAGE


def render():
    page_wrapper_open("alerts")
    render_page_header("알림센터", "개설 지연 · ERP 연계 정체 · 해지 위험 고객을 한눈에 확인합니다.")

    df_raw = get_current_df()
    alerts = analyze_alerts(df_raw)
    crit = alerts.get("critical", [])
    warn = alerts.get("warning", [])
    info = alerts.get("info", [])

    # KPI
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(render_kpi("긴급 (개설지연)", len(crit), color="#dc2626", variant="warning"), unsafe_allow_html=True)
    with k2:
        st.markdown(render_kpi("주의 (연계/해지)", len(warn), color="#f59e0b", variant="accent"), unsafe_allow_html=True)
    with k3:
        st.markdown(render_kpi("정보 (당일접수)", len(info), color="#008485", variant="success"), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # 긴급
    if crit:
        render_section_title(f"🔴 긴급 — 개설대기 {REMINDER_DAYS_PENDING}일 이상 ({len(crit)}건)")
        cd = pd.DataFrame(crit).rename(columns={
            "customer": "고객명", "customer_no": "고객번호", "manager": "담당자",
            "days": "경과일수", "detail": "상세", "date": "접수일"
        })
        dc = [c for c in ["고객명", "고객번호", "담당자", "경과일수", "상세", "접수일"] if c in cd.columns]
        st.dataframe(cd[dc].sort_values("경과일수", ascending=False), use_container_width=True, hide_index=True)

        if '담당자' in cd.columns:
            render_section_title("담당자별 개설 지연 현황")
            md = cd.groupby("담당자").agg(
                건수=("고객명", "count"), 평균경과일=("경과일수", "mean"), 최대경과일=("경과일수", "max")
            ).reset_index()
            md["평균경과일"] = md["평균경과일"].round(1)
            st.dataframe(md.sort_values("건수", ascending=False), use_container_width=True, hide_index=True)

    # 주의
    if warn:
        render_section_title(f"🟡 주의 — 연계 정체 / 해지 위험 ({len(warn)}건)")
        wd = pd.DataFrame(warn).rename(columns={
            "customer": "고객명", "customer_no": "고객번호", "manager": "담당자",
            "days": "경과일수", "detail": "상세", "date": "접수일", "type": "유형"
        })
        dc = [c for c in ["유형", "고객명", "고객번호", "담당자", "상세", "접수일"] if c in wd.columns]
        st.dataframe(wd[dc], use_container_width=True, hide_index=True)

    # 정보
    if info:
        render_section_title(f"🔵 정보 — 당일 신규 접수 ({len(info)}건)")
        idf = pd.DataFrame(info).rename(columns={
            "customer": "고객명", "customer_no": "고객번호", "manager": "담당자", "detail": "상세"
        })
        dc = [c for c in ["고객명", "고객번호", "담당자", "상세"] if c in idf.columns]
        st.dataframe(idf[dc], use_container_width=True, hide_index=True)

    if not crit and not warn and not info:
        st.markdown(
            '<div style="text-align:center;padding:60px 20px;color:#8c95a6;">'
            '<div style="font-size:48px;margin-bottom:16px;">✅</div>'
            '<div style="font-size:16px;font-weight:600;">확인이 필요한 알림이 없습니다</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.caption(f"⚙️ 현재 설정: 개설대기 **{REMINDER_DAYS_PENDING}일** 이상 → 긴급, ERP연계 **{REMINDER_DAYS_LINKAGE}일** 이상 → 주의")
    page_wrapper_close()
