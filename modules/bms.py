# -*- coding: utf-8 -*-
"""CMS 실적 확인 페이지"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import io
import plotly.express as px
from style import inject_page_css, page_wrapper_open, page_wrapper_close, render_section_title, render_page_header, render_kpi
from data import get_current_df, get_client, log_action
from config import BMS_SHEET_URL, BMS_SHEET_TAB, BMS_CELL_MAP

def render():
    inject_page_css("bms"); page_wrapper_open("bms")
    render_page_header("BMS 활동 이력 집계", "BMS 엑셀 파일 업로드 → 등록자 × 활동상세별 실적 자동 집계")
    
    if 'bms_pivot' not in st.session_state:
        st.session_state['bms_pivot'] = pd.DataFrame()
    if 'bms_files' not in st.session_state:
        st.session_state['bms_files'] = []
    
    render_section_title("엑셀 파일 업로드")
    st.info("BMS 엑셀 파일을 업로드하면 **등록자** × **활동상세** 별 건수가 자동 집계됩니다. 여러 파일을 업로드하면 누적됩니다.")
    up_bms = st.file_uploader("BMS 엑셀 파일 업로드", type=['xlsx','xls','csv'], key="bms_up", accept_multiple_files=True)
    
    if up_bms:
        new_files = [f.name for f in up_bms]
        if new_files != st.session_state.get('bms_files'):
            all_dfs = []
            for f in up_bms:
                try:
                    if f.name.endswith('.csv'):
                        df_b = pd.read_csv(f)
                    else:
                        df_b = pd.read_excel(f)
                        if '등록자' not in df_b.columns and '활동상세' not in df_b.columns:
                            df_b = pd.read_excel(f, header=1)
                    df_b.columns = [str(c).strip() for c in df_b.columns]
                    all_dfs.append(df_b)
                except Exception as e:
                    st.warning(f"⚠️ {f.name} 읽기 실패: {e}")
    
            if all_dfs:
                combined = pd.concat(all_dfs, ignore_index=True)
                if '등록자' not in combined.columns or '활동상세' not in combined.columns:
                    st.error("❌ 엑셀에 **'등록자'** 또는 **'활동상세'** 컬럼이 없습니다.")
                    st.info(f"업로드된 컬럼: {', '.join(combined.columns.tolist())}")
                else:
                    combined['등록자'] = combined['등록자'].astype(str).str.strip()
                    combined['활동상세'] = combined['활동상세'].astype(str).str.strip()
                    combined = combined[combined['등록자'].ne('') & combined['등록자'].ne('nan')]
                    combined = combined[combined['활동상세'].ne('') & combined['활동상세'].ne('nan')]
                    pivot = combined.groupby(['활동상세', '등록자']).size().unstack(fill_value=0)
                    # 활동구분 기준 방문 횟수 (등록자별)
                    visit_counts = combined[combined['활동구분'].astype(str).str.strip() == '방문'].groupby('등록자').size()
                    st.session_state['bms_pivot'] = pivot
                    st.session_state['bms_visit'] = visit_counts
                    st.session_state['bms_raw'] = combined
                    st.session_state['bms_files'] = new_files
    
    if not st.session_state['bms_pivot'].empty:
        pivot = st.session_state['bms_pivot']
        render_section_title("등록자별 실적 집계표")
        pivot_display = pivot.copy()
        pivot_display['합계'] = pivot_display.sum(axis=1)
        total_row = pivot_display.sum(axis=0); total_row.name = '합계'
        pivot_display = pd.concat([pivot_display, total_row.to_frame().T])
    
        등록자수 = len(pivot.columns); 활동상세수 = len(pivot.index); 총건수 = int(pivot.values.sum())
        k1, k2, k3 = st.columns(3)
        with k1: st.markdown(render_kpi("총 활동 건수", f"{총건수:,}"), unsafe_allow_html=True)
        with k2: st.markdown(render_kpi("등록자 수", 등록자수, unit="명", color="var(--primary)", variant="success"), unsafe_allow_html=True)
        with k3: st.markdown(render_kpi("활동상세 수", 활동상세수, unit="개", color="var(--accent)", variant="accent"), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    
        등록자_list = list(pivot.columns); 활동상세_list = list(pivot.index)
        visit_counts = st.session_state.get('bms_visit', pd.Series(dtype=int))
        header_cells = "".join(f'<th>{name}</th>' for name in 등록자_list) + '<th class="total">합계</th>'
        body_rows = ""
        for 상세 in 활동상세_list:
            row_cells = f'<td class="type-name">{상세}</td>'; row_total = 0
            for 등록자 in 등록자_list:
                val = int(pivot.loc[상세, 등록자]) if 등록자 in pivot.columns else 0; row_total += val
                cell_class = ' class="has-value"' if val > 0 else ''
                row_cells += f'<td{cell_class}>{val if val > 0 else ""}</td>'
            row_cells += f'<td class="total">{row_total}</td>'; body_rows += f'<tr>{row_cells}</tr>'
        # 방문 횟수 행 (활동구분 기준)
        visit_row = '<td class="type-name" style="background:#e8f5e9;color:#2e7d32;">방문(총횟수)</td>'; visit_total = 0
        for 등록자 in 등록자_list:
            v = int(visit_counts.get(등록자, 0)); visit_total += v
            cell_class = ' class="has-value"' if v > 0 else ''
            visit_row += f'<td{cell_class} style="background:#f1f8f1;">{v if v > 0 else ""}</td>'
        visit_row += f'<td class="total" style="background:#c8e6c9;color:#2e7d32;">{visit_total}</td>'
        body_rows += f'<tr>{visit_row}</tr>'
        # 합계 행
        total_cells = '<td class="type-name total">합계</td>'; grand_total = 0
        for 등록자 in 등록자_list:
            col_sum = int(pivot[등록자].sum()); grand_total += col_sum; total_cells += f'<td class="total">{col_sum}</td>'
        total_cells += f'<td class="total grand">{grand_total}</td>'; body_rows += f'<tr class="total-row">{total_cells}</tr>'
    
        table_html = f"""<style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Pretendard',-apple-system,'Malgun Gothic',sans-serif; }}
        .bms-table {{ width:100%; border-collapse:collapse; border:1px solid #dfe3e8; border-radius:8px; overflow:hidden; }}
        .bms-table th {{ background:#008485; color:#fff; padding:12px 14px; font-size:13px; font-weight:700; text-align:center; border:1px solid #007070; }}
        .bms-table th.corner {{ background:#006a6b; }} .bms-table th.total {{ background:#006a6b; }}
        .bms-table td {{ padding:10px 14px; text-align:center; font-size:14px; color:#4a5568; border:1px solid #e8ecf0; }}
        .bms-table td.type-name {{ text-align:left; font-weight:700; color:#1a1a2e; background:#f7f8fa; }}
        .bms-table td.has-value {{ color:#1a1a2e; font-weight:700; }}
        .bms-table td.total {{ font-weight:800; color:#008485; background:#f0f9f9; }}
        .bms-table td.grand {{ font-weight:800; color:#fff; background:#008485; font-size:15px; }}
        .bms-table tr:hover td {{ background:#f0f9f9; }} .bms-table tr:hover td.type-name {{ background:#e0f2f2; }}
        .bms-table tr.total-row td {{ background:#f0f9f9; border-top:2px solid #008485; }}
        .bms-table tr.total-row:hover td {{ background:#e0f2f2; }}
        </style><table class="bms-table"><thead><tr><th class="corner">활동상세</th>{header_cells}</tr></thead><tbody>{body_rows}</tbody></table>"""
        components.html(table_html, height=(len(활동상세_list) + 3) * 44 + 20, scrolling=False)
        st.markdown("<br>", unsafe_allow_html=True)
    
        render_section_title("등록자별 실적 차트")
        chart_data = pivot.T.copy(); chart_data.index.name = '등록자'
        fig = px.bar(chart_data.reset_index(), x='등록자', y=chart_data.columns.tolist(), barmode='group', color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', legend_title="활동상세", xaxis_title="", yaxis_title="건수", font=dict(family="Pretendard, sans-serif"))
        st.plotly_chart(fig, use_container_width=True)
    
        render_section_title("등록자별 상세 이력")
        bms_raw = st.session_state.get('bms_raw', pd.DataFrame())
        if not bms_raw.empty:
            등록자_options = sorted(bms_raw['등록자'].unique().tolist())
            sel_person = st.selectbox("조회할 등록자 선택", 등록자_options, key="bms_person_sel")
            if sel_person:
                person_df = bms_raw[bms_raw['등록자'] == sel_person].copy()
                person_types = person_df['활동상세'].value_counts()
                pk1, pk2, pk3 = st.columns(3)
                with pk1: st.markdown(render_kpi("총 활동건수", len(person_df)), unsafe_allow_html=True)
                with pk2: st.markdown(render_kpi("활동상세 수", len(person_types), unit="개", color="var(--primary)", variant="success"), unsafe_allow_html=True)
                with pk3:
                    top_type = person_types.index[0] if len(person_types) > 0 else "-"
                    st.markdown(render_kpi("최다 유형", top_type, unit="", color="var(--accent)", variant="accent"), unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                type_cards = ""
                for t_name, t_cnt in person_types.items():
                    pct = round(t_cnt / len(person_df) * 100, 1)
                    type_cards += f'<div class="type-card"><div class="type-name">{t_name}</div><div class="type-cnt">{t_cnt}건</div><div class="type-bar-bg"><div class="type-bar" style="width:{pct}%"></div></div><div class="type-pct">{pct}%</div></div>'
                type_summary_html = f"""<style>@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
                * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Pretendard',-apple-system,'Malgun Gothic',sans-serif; }}
                .type-wrap {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:10px; }}
                .type-card {{ background:#fff; padding:14px 16px; border-radius:10px; border:1px solid #dfe3e8; }}
                .type-name {{ font-size:12px; font-weight:700; color:#8c95a6; margin-bottom:4px; }}
                .type-cnt {{ font-size:20px; font-weight:800; color:#1a1a2e; margin-bottom:8px; }}
                .type-bar-bg {{ height:6px; background:#eef1f5; border-radius:3px; overflow:hidden; }}
                .type-bar {{ height:100%; background:linear-gradient(90deg,#008485,#00a8a8); border-radius:3px; }}
                .type-pct {{ font-size:11px; color:#8c95a6; margin-top:4px; text-align:right; }}
                </style><div class="type-wrap">{type_cards}</div>"""
                components.html(type_summary_html, height=((len(person_types) + 3) // 4) * 110 + 10, scrolling=False)
                st.markdown("<br>", unsafe_allow_html=True)
                render_section_title(f"{sel_person} 전체 활동 이력")
                display_cols = [c for c in person_df.columns if str(c).strip() and c != '등록자']
                st.dataframe(person_df[display_cols].reset_index(drop=True), use_container_width=True, hide_index=True, height=400)
    
        st.markdown("<br>", unsafe_allow_html=True)
        render_section_title("데이터 내보내기")
        import io
        dl_buf = io.BytesIO()
        with pd.ExcelWriter(dl_buf, engine='openpyxl') as writer:
            pivot_display.to_excel(writer, sheet_name='BMS집계')
        exp_c1, exp_c2 = st.columns(2)
        with exp_c1:
            st.download_button("📥 엑셀 다운로드", data=dl_buf.getvalue(), file_name=f"BMS_집계_{datetime.date.today().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with exp_c2:
            if st.button("📤 구글시트로 내보내기", type="primary", use_container_width=True):
                try:
                    with st.spinner("구글시트에 데이터를 입력하는 중..."):
                        cl = get_client()
                        if not cl:
                            st.error("❌ 구글 인증 실패")
                        else:
                            ws = cl.open_by_url(BMS_SHEET_URL).worksheet(BMS_SHEET_TAB)
                            updated_cells = 0; skipped = []
                            visit_counts = st.session_state.get('bms_visit', pd.Series(dtype=int))
                            for 등록자, 유형맵 in BMS_CELL_MAP.items():
                                for 항목, cell_addr in 유형맵.items():
                                    val = 0
                                    if 항목 == "방문":
                                        # 방문은 활동구분 기준 총 횟수
                                        val = int(visit_counts.get(등록자, 0))
                                    else:
                                        # 개설/연계는 활동상세 기준
                                        if 항목 in pivot.index and 등록자 in pivot.columns:
                                            val = int(pivot.loc[항목, 등록자])
                                    if val > 0: ws.update_acell(cell_addr, val); updated_cells += 1
                                    else: ws.update_acell(cell_addr, "")
                            for 등록자 in pivot.columns:
                                if 등록자 not in BMS_CELL_MAP: skipped.append(등록자)
                            st.success(f"✅ 구글시트 내보내기 완료! ({updated_cells}개 셀 업데이트)")
                            if skipped: st.warning(f"⚠️ 매핑되지 않은 등록자: {', '.join(skipped)}")
                            log_action(st.session_state.get('current_user',''), "BMS_Export", f"구글시트 내보내기 {updated_cells}셀")
                except Exception as e:
                    import traceback; st.error(f"❌ 내보내기 실패: {str(e)}"); st.code(traceback.format_exc())
    
        st.markdown("---")
        if st.button("🗑️ 집계 초기화", use_container_width=True):
            st.session_state['bms_pivot'] = pd.DataFrame(); st.session_state['bms_raw'] = pd.DataFrame(); st.session_state['bms_visit'] = pd.Series(dtype=int); st.session_state['bms_files'] = []; st.rerun()
    else:
        st.markdown("""<div style="text-align:center; padding:60px 20px; color:#8c95a6;">
            <div style="font-size:48px; margin-bottom:16px;">📂</div>
            <div style="font-size:16px; font-weight:600;">BMS 엑셀 파일을 업로드하면 집계 표가 표시됩니다</div>
            <div style="font-size:13px; margin-top:8px;">엑셀에 <b>등록자</b>, <b>활동상세</b> 컬럼이 있어야 합니다</div>
        </div>""", unsafe_allow_html=True)
    
    page_wrapper_close()
