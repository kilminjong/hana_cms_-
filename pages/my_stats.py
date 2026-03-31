# -*- coding: utf-8 -*-
"""나의 실적 (담당자별 대시보드) 페이지"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import io

from style import render_page_header, render_kpi, render_section_title, page_wrapper_open, page_wrapper_close
from data import get_current_df
from auth import get_user_role


def render():
    page_wrapper_open("mydash")
    render_page_header("나의 실적", "담당 고객 현황 및 실적을 확인합니다.")

    df_raw = get_current_df()
    td = datetime.date.today()
    user = st.session_state.get("current_user", "")
    role = get_user_role()

    # 담당자 선택
    if not df_raw.empty and '담당자' in df_raw.columns:
        ml = sorted(df_raw['담당자'].dropna().unique().tolist())
    else:
        ml = []

    if role == "admin":
        sel_mgr = st.selectbox("담당자 선택", ["전체"] + ml, index=0)
    else:
        if user in ml:
            sel_mgr = user
            st.info(f"👤 **{user}** 님의 실적을 표시합니다.")
        else:
            sel_mgr = st.selectbox("담당자 선택", ml if ml else ["전체"], index=0)

    if df_raw is not None and not df_raw.empty:
        dm = df_raw.copy()
        if sel_mgr != "전체" and '담당자' in dm.columns:
            dm = dm[dm['담당자'].astype(str).str.strip() == sel_mgr]

        if '신규접수일' in dm.columns:
            dm['dt'] = pd.to_datetime(
                dm['신규접수일'].astype(str).str.replace(r'[^0-9]', '', regex=True),
                format='%Y%m%d', errors='coerce'
            )
        else:
            dm['dt'] = pd.NaT

        총건 = len(dm)
        이번달 = len(dm[(dm['dt'].dt.year == td.year) & (dm['dt'].dt.month == td.month)]) if 'dt' in dm.columns else 0
        완료 = len(dm[dm['개설구분'] == '개설완료']) if '개설구분' in dm.columns else 0
        대기 = len(dm[dm['개설구분'] == '개설대기']) if '개설구분' in dm.columns else 0
        완료율 = round(완료 / (완료 + 대기) * 100, 1) if (완료 + 대기) > 0 else 0
        해지 = len(dm[dm['관리구분'].isin(['해지', '해지예상', '취소'])]) if '관리구분' in dm.columns else 0

        # KPI
        st.markdown("<br>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(render_kpi("담당 고객", 총건, color="#008485"), unsafe_allow_html=True)
        with k2:
            st.markdown(render_kpi("이번달 접수", 이번달, color="#6366f1", variant="accent"), unsafe_allow_html=True)
        with k3:
            st.markdown(render_kpi("개설 완료율", f"{완료율}%", unit="", color="#16a34a", variant="success"), unsafe_allow_html=True)
        with k4:
            st.markdown(render_kpi("해지/위험", 해지, color="#dc2626", variant="warning"), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # 차트
        ca, cb = st.columns(2)
        with ca:
            render_section_title("개설 현황")
            fig = go.Figure(data=[go.Pie(
                labels=["개설완료", "개설대기"], values=[완료, 대기], hole=0.5,
                marker=dict(colors=["#008485", "#f59e0b"]), textinfo="label+value"
            )])
            fig.update_layout(height=280, margin=dict(t=20, b=20, l=20, r=20), showlegend=False,
                              font=dict(family="Pretendard"), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        with cb:
            render_section_title("월별 접수 추이")
            if 'dt' in dm.columns and not dm['dt'].isna().all():
                mo = dm.set_index('dt').resample('M').size().reset_index(name='건수')
                mo['월'] = mo['dt'].dt.strftime('%Y-%m')
                fig2 = px.bar(mo.tail(6), x='월', y='건수', color_discrete_sequence=['#008485'])
                fig2.update_layout(height=280, margin=dict(t=20, b=20, l=20, r=20),
                                   paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                   xaxis_title="", yaxis_title="")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("날짜 데이터가 부족합니다.")

        # 처리 필요
        render_section_title("⏳ 처리 필요 — 개설대기 고객")
        if '개설구분' in dm.columns:
            pf = dm[dm['개설구분'].astype(str).str.strip() == '개설대기']
            if not pf.empty:
                pc = [c for c in ["고객명", "고객번호", "구축형", "신규접수일", "연계상태"] if c in pf.columns]
                st.dataframe(pf[pc], use_container_width=True, hide_index=True)
            else:
                st.success("개설대기 고객이 없습니다. 👏")

        # ERP 연계
        if '연계상태' in dm.columns:
            render_section_title("🔗 ERP 연계 현황")
            lv = dm['연계상태'].value_counts()
            fig3 = px.bar(x=lv.index, y=lv.values, color_discrete_sequence=['#008485'],
                          labels={"x": "연계상태", "y": "건수"})
            fig3.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10),
                               paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               xaxis_title="", yaxis_title="")
            st.plotly_chart(fig3, use_container_width=True)

        # 전체 목록
        render_section_title("📋 전체 담당 고객 목록")
        ac = [c for c in ["고객명", "고객번호", "사업자번호", "구축형", "개설구분", "관리구분", "연계상태", "신규접수일"] if c in dm.columns]
        st.dataframe(dm[ac], use_container_width=True, hide_index=True, height=400)

        # 엑셀 다운로드
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            dm[ac].to_excel(w, index=False, sheet_name='나의실적')
        st.download_button(
            "📥 엑셀 다운로드", data=buf.getvalue(),
            file_name=f"나의실적_{sel_mgr}_{td.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("데이터가 없습니다.")

    page_wrapper_close()
