# -*- coding: utf-8 -*-
"""종합 보고서 페이지"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
from style import inject_page_css, page_wrapper_open, page_wrapper_close, render_page_header
from data import get_current_df

def render():
    inject_page_css("report"); page_wrapper_open("report")
    render_page_header("종합 보고서", "일일 / 주간 / 월간 실적 보고서를 생성하고 인쇄할 수 있습니다.")
    tab_d, tab_w, tab_m = st.tabs(["📋 일일 보고서","📊 주간 보고서","📈 월간 보고서"])
    df_raw = get_current_df()
    if df_raw is None or df_raw.empty: st.warning("데이터가 없습니다."); st.stop()
    df_all = df_raw.copy()
    if '신규접수일' in df_all.columns:
        df_all['dt'] = pd.to_datetime(df_all['신규접수일'].astype(str).str.replace(r'[^0-9]','',regex=True), format='%Y%m%d', errors='coerce')
    else: df_all['dt'] = pd.NaT
    
    def build_report_html(mode):
        td = datetime.date.today()
        user = st.session_state.get("current_user","Admin")
        if mode == "daily":
            rdf = df_all[df_all['dt'].dt.date == td]; title = "일일 실적 보고서"; period = td.strftime('%Y년 %m월 %d일')
        elif mode == "weekly":
            sw = td - datetime.timedelta(days=td.weekday()); ew = sw + datetime.timedelta(days=6)
            rdf = df_all[(df_all['dt'].dt.date >= sw) & (df_all['dt'].dt.date <= ew)]
            title = "주간 실적 보고서"; period = f"{sw.strftime('%Y.%m.%d')} ~ {ew.strftime('%Y.%m.%d')}"
        else:
            rdf = df_all[(df_all['dt'].dt.year == td.year) & (df_all['dt'].dt.month == td.month)]
            title = "월간 실적 보고서"; period = td.strftime('%Y년 %m월')
    
        total = len(rdf)
        완료 = len(rdf[rdf['개설구분']=='개설완료']) if '개설구분' in rdf.columns else 0
        대기 = len(rdf[rdf['개설구분']=='개설대기']) if '개설구분' in rdf.columns else 0
        rate = round(완료/total*100,1) if total > 0 else 0
    
        # 구축형별
        구축형_html = ""
        if not rdf.empty and '구축형' in rdf.columns:
            vc = rdf['구축형'].value_counts()
            for name, cnt in vc.items():
                pct = round(cnt/total*100,1)
                구축형_html += "<tr><td>" + str(name) + "</td><td class=\"num\">" + str(cnt) + "</td><td class=\"num\">" + str(pct) + "%</td></tr>"
        if not 구축형_html: 구축형_html = '<tr><td colspan="3" style="text-align:center;color:#8c95a6;">데이터 없음</td></tr>'
    
        # 관리구분별
        관리_html = ""
        if not rdf.empty and '관리구분' in rdf.columns:
            vc2 = rdf['관리구분'].value_counts()
            for name, cnt in vc2.items():
                pct = round(cnt/total*100,1)
                color = "#16a34a" if name=="정상" else "#dc2626" if name=="해지" else "#f59e0b"
                관리_html += "<tr><td><span style=\"color:" + color + ";font-weight:700;\">●</span> " + str(name) + "</td><td class=\"num\">" + str(cnt) + "</td><td class=\"num\">" + str(pct) + "%</td></tr>"
        if not 관리_html: 관리_html = '<tr><td colspan="3" style="text-align:center;color:#8c95a6;">데이터 없음</td></tr>'
    
        # 담당자별
        담당_html = ""
        if not rdf.empty and '담당자' in rdf.columns:
            담당g = rdf.groupby('담당자').size().reset_index(name='건수').sort_values('건수', ascending=False)
            rank = 1
            for _, r in 담당g.iterrows():
                완료c = len(rdf[(rdf['담당자']==r['담당자']) & (rdf['개설구분']=='개설완료')]) if '개설구분' in rdf.columns else 0
                대기c = int(r['건수']) - 완료c
                rt = round(완료c/int(r['건수'])*100,1) if int(r['건수']) > 0 else 0
                bar_w = min(rt, 100)
                medal = "🥇" if rank==1 else "🥈" if rank==2 else "🥉" if rank==3 else str(rank)
                bar_html = '<div style="display:flex;align-items:center;gap:8px;justify-content:flex-end;"><div style="width:60px;height:8px;background:#eef1f5;border-radius:4px;overflow:hidden;"><div style="width:' + str(bar_w) + '%;height:100%;background:#008485;border-radius:4px;"></div></div><span>' + str(rt) + '%</span></div>'
                담당_html += "<tr><td style=\"text-align:center;\">" + medal + "</td><td style=\"font-weight:700;\">" + str(r['담당자']) + "</td><td class=\"num\">" + str(int(r['건수'])) + "</td><td class=\"num\">" + str(완료c) + "</td><td class=\"num\">" + str(대기c) + "</td><td class=\"num\">" + bar_html + "</td></tr>"
                rank += 1
        if not 담당_html: 담당_html = '<tr><td colspan="6" style="text-align:center;color:#8c95a6;">데이터 없음</td></tr>'
    
        # 연계상태
        연계_html = ""
        if not rdf.empty and '연계상태' in rdf.columns:
            vl = rdf['연계상태'].dropna(); vl = vl[vl != '']
            if len(vl) > 0:
                vc3 = vl.value_counts()
                for name, cnt in vc3.items():
                    연계_html += "<tr><td>" + str(name) + "</td><td class=\"num\">" + str(cnt) + "</td></tr>"
        if not 연계_html: 연계_html = '<tr><td colspan="2" style="text-align:center;color:#8c95a6;">데이터 없음</td></tr>'
    
        # 최근 접수 내역
        내역_html = ""; 내역_th = ""
        if not rdf.empty:
            cols = [c for c in ["신규접수일","고객명","구축형","담당자","개설구분","연계상태","관리구분"] if c in rdf.columns]
            show = rdf[cols].sort_values('신규접수일', ascending=False).head(15) if '신규접수일' in rdf.columns else rdf[cols].head(15)
            내역_th = "".join("<th>" + c + "</th>" for c in cols)
            for _, r in show.iterrows():
                cells = ""
                for c in cols:
                    v = str(r[c]) if pd.notna(r[c]) else ""
                    style = ""
                    if c == "개설구분" and v == "개설완료": style = ' style="color:#008485;font-weight:700;"'
                    elif c == "개설구분" and v == "개설대기": style = ' style="color:#f59e0b;font-weight:700;"'
                    elif c == "관리구분" and v == "정상": style = ' style="color:#16a34a;font-weight:700;"'
                    elif c == "관리구분" and v == "해지": style = ' style="color:#dc2626;font-weight:700;"'
                    cells += "<td" + style + ">" + v + "</td>"
                내역_html += "<tr>" + cells + "</tr>"
        else:
            내역_th = "<th>-</th>"; 내역_html = '<tr><td style="text-align:center;color:#8c95a6;">데이터 없음</td></tr>'
    
        now_time = datetime.datetime.now().strftime('%H:%M')
    
        html = """<!DOCTYPE html><html><head><meta charset="utf-8">
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        @page { size: A4; margin: 15mm; }
        @media print {
            body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
            .no-print { display: none !important; }
        }
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Pretendard',-apple-system,'Malgun Gothic',sans-serif; }
        body { padding: 32px; color: #1a1a2e; font-size: 13px; line-height: 1.6; background: #fff; }
        .rpt-header { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:3px solid #008485; padding-bottom:16px; margin-bottom:24px; }
        .rpt-title { font-size:24px; font-weight:900; color:#008485; }
        .rpt-sub { font-size:13px; color:#64748b; margin-top:4px; }
        .approval { border:1px solid #ccc; border-collapse:collapse; }
        .approval th { background:#f1f3f5; padding:6px 14px; font-size:11px; color:#64748b; border:1px solid #ccc; }
        .approval td { padding:6px 14px; font-size:12px; text-align:center; border:1px solid #ccc; height:36px; min-width:60px; }
        .kpi-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:16px 0 24px; }
        .kpi { text-align:center; padding:18px 12px; border-radius:10px; border:1px solid #eef1f5; }
        .kpi-label { font-size:11px; color:#8c95a6; font-weight:600; margin-bottom:4px; }
        .kpi-val { font-size:28px; font-weight:900; }
        .kpi-note { font-size:11px; color:#8c95a6; margin-top:2px; }
        .sec-title { font-size:15px; font-weight:800; color:#1a1a2e; padding:10px 0 8px; border-bottom:2px solid #008485; margin:20px 0 12px; }
        .two-col { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:8px; }
        .tbl { width:100%; border-collapse:collapse; margin-bottom:12px; }
        .tbl th { background:#f7f8fa; padding:8px 12px; font-size:11px; color:#64748b; font-weight:700; text-align:left; border-bottom:2px solid #dfe3e8; }
        .tbl td { padding:8px 12px; font-size:13px; border-bottom:1px solid #eef1f5; }
        .tbl td.num { text-align:right; font-weight:600; }
        .tbl tr:hover td { background:#f9fafb; }
        .tbl-label { font-size:12px; font-weight:700; color:#64748b; margin-bottom:6px; }
        .print-btn { background:#008485; color:#fff; border:none; padding:12px 28px; border-radius:8px; font-size:14px; font-weight:700; cursor:pointer; display:inline-flex; align-items:center; gap:6px; }
        .print-btn:hover { background:#006a6b; }
        .pdf-btn { background:#1e2a3a; color:#fff; border:none; padding:12px 28px; border-radius:8px; font-size:14px; font-weight:700; cursor:pointer; display:inline-flex; align-items:center; gap:6px; }
        .pdf-btn:hover { background:#0f172a; }
        .rpt-footer { margin-top:30px; padding-top:12px; border-top:1px solid #dfe3e8; font-size:11px; color:#8c95a6; display:flex; justify-content:space-between; }
        </style></head><body>
    
        <div class="rpt-header">
            <div>
                <div class="rpt-title">""" + title + """</div>
                <div class="rpt-sub">보고 기간: """ + period + """ &nbsp;|&nbsp; 작성일: """ + td.strftime('%Y-%m-%d') + """ &nbsp;|&nbsp; 작성자: """ + user + """</div>
            </div>
            <table class="approval">
                <tr><th>작성</th><th>검토</th><th>승인</th></tr>
                <tr><td>""" + user + """</td><td></td><td></td></tr>
            </table>
        </div>
    
        <div class="kpi-row">
            <div class="kpi" style="background:#f0f9f9;"><div class="kpi-label">총 접수</div><div class="kpi-val" style="color:#008485;">""" + str(total) + """</div><div class="kpi-note">건</div></div>
            <div class="kpi" style="background:#f0fdf4;"><div class="kpi-label">개설 완료</div><div class="kpi-val" style="color:#16a34a;">""" + str(완료) + """</div><div class="kpi-note">건</div></div>
            <div class="kpi" style="background:#fffbeb;"><div class="kpi-label">개설 대기</div><div class="kpi-val" style="color:#f59e0b;">""" + str(대기) + """</div><div class="kpi-note">건</div></div>
            <div class="kpi" style="background:#f1f3f5;"><div class="kpi-label">완료율</div><div class="kpi-val" style="color:#1a1a2e;">""" + str(rate) + """%</div><div class="kpi-note">&nbsp;</div></div>
        </div>
    
        <div class="sec-title">1. 구분별 현황</div>
        <div class="two-col">
            <div><div class="tbl-label">▸ 구축형별</div><table class="tbl"><thead><tr><th>구축형</th><th style="text-align:right;">건수</th><th style="text-align:right;">비율</th></tr></thead><tbody>""" + 구축형_html + """</tbody></table></div>
            <div><div class="tbl-label">▸ 관리구분별</div><table class="tbl"><thead><tr><th>관리구분</th><th style="text-align:right;">건수</th><th style="text-align:right;">비율</th></tr></thead><tbody>""" + 관리_html + """</tbody></table></div>
        </div>
    
        <div class="sec-title">2. 담당자별 실적</div>
        <table class="tbl"><thead><tr><th style="text-align:center;width:45px;">순위</th><th>담당자</th><th style="text-align:right;">총건수</th><th style="text-align:right;">완료</th><th style="text-align:right;">대기</th><th style="text-align:right;width:140px;">완료율</th></tr></thead><tbody>""" + 담당_html + """</tbody></table>
    
        <div class="sec-title">3. ERP 연계 현황</div>
        <table class="tbl" style="max-width:400px;"><thead><tr><th>연계상태</th><th style="text-align:right;">건수</th></tr></thead><tbody>""" + 연계_html + """</tbody></table>
    
        <div class="sec-title">4. 최근 접수 내역</div>
        <table class="tbl"><thead><tr>""" + 내역_th + """</tr></thead><tbody>""" + 내역_html + """</tbody></table>
    
        <div class="rpt-footer"><span>하나은행 고객관리시스템 · 종합 보고서</span><span>출력일시: """ + td.strftime('%Y-%m-%d') + " " + now_time + """</span></div>
    
        <div style="text-align:center;margin-top:24px;" class="no-print">
            <button class="print-btn" onclick="window.print();">🖨️ 보고서 인쇄</button>
            &nbsp;&nbsp;
            <button class="pdf-btn" onclick="savePDF();">📄 PDF 저장</button>
            <script>
            function savePDF(){
                var orig = document.title;
                document.title = '""" + title.replace("'","\\\\'") + "_" + td.strftime('%Y%m%d') + """';
                window.print();
                setTimeout(function(){ document.title = orig; }, 1000);
            }
            </script>
        </div>
    
        </body></html>"""
        return html, total
    
    def render_report(mode):
        html, total = build_report_html(mode)
        h = max(1200, total * 30 + 900)
        components.html(html, height=h, scrolling=True)
    
    with tab_d: render_report("daily")
    with tab_w: render_report("weekly")
    with tab_m: render_report("monthly")
    page_wrapper_close()
    page_wrapper_close()
