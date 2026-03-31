# -*- coding: utf-8 -*-
"""메인화면 (대시보드) 페이지"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
from style import page_wrapper_open, page_wrapper_close
from data import get_current_df, analyze_alerts

def render():
    page_wrapper_open("dashboard")
    df_raw=get_current_df();td=datetime.date.today();user=st.session_state.get("current_user","")
    if df_raw is not None and not df_raw.empty:
        df_d=df_raw.copy()
        if '신규접수일' in df_d.columns:df_d['dt']=pd.to_datetime(df_d['신규접수일'].astype(str).str.replace(r'[^0-9]','',regex=True),format='%Y%m%d',errors='coerce')
        else:df_d['dt']=pd.NaT
        총고객=len(df_d);오늘인입=len(df_d[df_d['dt'].dt.date==td])
        wsw=td-datetime.timedelta(days=td.weekday());이번주=len(df_d[(df_d['dt'].dt.date>=wsw)&(df_d['dt'].dt.date<=td)])
        이번달=len(df_d[(df_d['dt'].dt.year==td.year)&(df_d['dt'].dt.month==td.month)])
        완료=len(df_d[df_d['개설구분']=='개설완료']) if '개설구분' in df_d.columns else 0
        대기=len(df_d[df_d['개설구분']=='개설대기']) if '개설구분' in df_d.columns else 0
        정상=len(df_d[df_d['관리구분']=='정상']) if '관리구분' in df_d.columns else 0
        해지=len(df_d[df_d['관리구분']=='해지']) if '관리구분' in df_d.columns else 0
    else:총고객=0;오늘인입=0;이번주=0;이번달=0;완료=0;대기=0;정상=0;해지=0;df_d=pd.DataFrame()
    hour=datetime.datetime.now().hour
    greeting="좋은 아침이에요" if hour<12 else "좋은 오후예요" if hour<18 else "수고하셨어요"
    rr=""
    if not df_d.empty and '담당자' in df_d.columns:
        dt5=df_d['담당자'].value_counts().head(5);mx=dt5.max() if len(dt5)>0 else 1;rk=1
        for n,c in dt5.items():
            md="🥇" if rk==1 else "🥈" if rk==2 else "🥉" if rk==3 else str(rk)
            rr+=f'<div class="rank-item"><div class="rank-medal">{md}</div><div class="rank-info"><div class="rank-name">{n}</div><div class="rank-bar-bg"><div class="rank-bar" style="width:{round(c/mx*100)}%;"></div></div></div><div class="rank-cnt">{c}</div></div>';rk+=1
    if not rr:rr='<div style="text-align:center;color:#8c95a6;padding:20px;">데이터 없음</div>'
    tm=정상+해지;sp=round(정상/tm*100) if tm>0 else 0;hp=round(해지/tm*100) if tm>0 else 0
    mi=f'<div class="status-item"><div class="status-dot" style="background:#16a34a;"></div><div class="status-label">정상</div><div class="status-val" style="color:#16a34a;">{정상}</div><div class="status-pct">{sp}%</div></div><div class="status-item"><div class="status-dot" style="background:#dc2626;"></div><div class="status-label">해지</div><div class="status-val" style="color:#dc2626;">{해지}</div><div class="status-pct">{hp}%</div></div>'
    gr="";rtrows="";rtth="<th>-</th>"
    if not df_d.empty and '구축형' in df_d.columns:
        vc=df_d['구축형'].value_counts();cols=['#008485','#00a8a8','#4dd0d0','#f59e0b','#6366f1'];ci=0
        for n,c in vc.items():
            p=round(c/총고객*100,1) if 총고객>0 else 0;cl=cols[ci%len(cols)]
            gr+=f'<div class="type-item"><div class="type-color" style="background:{cl};"></div><div class="type-info"><div class="type-name">{n}</div><div class="type-bar-bg"><div class="type-bar" style="width:{p}%;background:{cl};"></div></div></div><div class="type-val">{c}<span class="type-pct">{p}%</span></div></div>';ci+=1
    if not gr:gr='<div style="text-align:center;color:#8c95a6;padding:20px;">데이터 없음</div>'
    if not df_d.empty:
        rc2=[c for c in ["신규접수일","고객명","구축형","담당자","개설구분","관리구분"] if c in df_d.columns]
        rs=df_d[rc2].sort_values('신규접수일',ascending=False).head(8) if '신규접수일' in df_d.columns else df_d[rc2].head(8)
        for _,r in rs.iterrows():
            cells=""
            for c in rc2:
                vv=str(r[c]) if pd.notna(r[c]) else "";sty=""
                if c=="개설구분" and vv=="개설완료":sty=' class="badge-green"'
                elif c=="개설구분" and vv=="개설대기":sty=' class="badge-yellow"'
                elif c=="관리구분" and vv=="정상":sty=' class="badge-green"'
                elif c=="관리구분" and vv=="해지":sty=' class="badge-red"'
                cells+=f"<td><span{sty}>{vv}</span></td>" if sty else f"<td>{vv}</td>"
            rtrows+=f"<tr>{cells}</tr>"
        rtth="".join(f"<th>{c}</th>" for c in rc2)
    if not rtrows:rtrows='<tr><td style="text-align:center;color:#8c95a6;">데이터 없음</td></tr>'
    완료율=round(완료/(완료+대기)*100,1) if(완료+대기)>0 else 0
    alerts=analyze_alerts(df_raw);cc=len(alerts.get("critical",[]));wc=len(alerts.get("warning",[]))
    alert_html=""
    if cc>0 or wc>0:
        abi=""
        for a in (alerts.get("critical",[])[:3]+alerts.get("warning",[])[:3]):
            ic="🔴" if a.get("type")=="개설지연" else "🟡"
            abi+=f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;"><span>{ic}</span><b>{a["customer"]}</b><span style="color:#64748b;">— {a["detail"]}</span><span style="color:#8c95a6;font-size:12px;">(담당: {a["manager"]})</span></div>'
        alert_html=f'<div style="background:#fff;border:1px solid #fecaca;border-left:4px solid #dc2626;border-radius:14px;padding:16px 20px;margin-bottom:16px;"><div style="font-size:14px;font-weight:800;color:#dc2626;margin-bottom:8px;">⚠️ 확인 필요 알림 {cc+wc}건</div>{abi}</div>'
    dh=f'''<!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');*{{margin:0;padding:0;box-sizing:border-box;font-family:'Pretendard',-apple-system,sans-serif}}body{{background:#f4f6f9;padding:28px}}.dash-banner{{background:linear-gradient(135deg,#008485,#005f60,#003d3e);border-radius:16px;padding:28px 32px;color:#fff;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center}}.banner-left h1{{font-size:22px;font-weight:800;margin-bottom:4px}}.banner-left p{{font-size:13px;opacity:.7}}.banner-right{{display:flex;gap:20px}}.banner-stat{{text-align:center;background:rgba(255,255,255,.12);padding:14px 22px;border-radius:12px;min-width:100px}}.banner-stat .bs-label{{font-size:11px;opacity:.7}}.banner-stat .bs-val{{font-size:26px;font-weight:900}}.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}}.kpi-card{{background:#fff;border-radius:14px;padding:20px;border:1px solid #e8ecf0}}.kpi-card .kpi-icon{{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;margin-bottom:12px}}.kpi-card .kpi-label{{font-size:12px;font-weight:600;color:#8c95a6}}.kpi-card .kpi-val{{font-size:28px;font-weight:900;margin-top:4px}}.kpi-card .kpi-sub{{font-size:11px;color:#8c95a6;margin-top:6px}}.panel-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}}.panel{{background:#fff;border-radius:14px;padding:22px;border:1px solid #e8ecf0}}.panel-title{{font-size:14px;font-weight:800;color:#1a1a2e;margin-bottom:16px;display:flex;align-items:center;gap:8px}}.panel-title .pt-icon{{width:28px;height:28px;border-radius:8px;background:#f0f9f9;display:flex;align-items:center;justify-content:center;font-size:14px}}.rank-item{{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #f1f3f5}}.rank-item:last-child{{border:none}}.rank-medal{{font-size:18px;width:28px;text-align:center}}.rank-info{{flex:1}}.rank-name{{font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:5px}}.rank-bar-bg{{height:6px;background:#eef1f5;border-radius:3px;overflow:hidden}}.rank-bar{{height:100%;background:linear-gradient(90deg,#008485,#00a8a8);border-radius:3px}}.rank-cnt{{font-size:16px;font-weight:900;color:#008485;min-width:40px;text-align:right}}.status-item{{display:flex;align-items:center;gap:10px;padding:12px 0;border-bottom:1px solid #f1f3f5}}.status-item:last-child{{border:none}}.status-dot{{width:10px;height:10px;border-radius:50%}}.status-label{{flex:1;font-size:13px;font-weight:600;color:#1a1a2e}}.status-val{{font-size:18px;font-weight:900;min-width:50px;text-align:right}}.status-pct{{font-size:12px;color:#8c95a6;min-width:40px;text-align:right}}.type-item{{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #f1f3f5}}.type-item:last-child{{border:none}}.type-color{{width:8px;height:32px;border-radius:4px}}.type-info{{flex:1}}.type-name{{font-size:13px;font-weight:600;color:#1a1a2e;margin-bottom:4px}}.type-bar-bg{{height:5px;background:#eef1f5;border-radius:3px;overflow:hidden}}.type-bar{{height:100%;border-radius:3px}}.type-val{{font-size:15px;font-weight:800;color:#1a1a2e;min-width:50px;text-align:right}}.type-pct{{font-size:11px;color:#8c95a6;margin-left:4px}}.recent-tbl{{width:100%;border-collapse:collapse}}.recent-tbl th{{padding:10px 12px;font-size:11px;font-weight:700;color:#8c95a6;text-align:left;border-bottom:2px solid #e8ecf0;background:#fafbfc}}.recent-tbl td{{padding:10px 12px;font-size:13px;color:#1a1a2e;border-bottom:1px solid #f1f3f5}}.recent-tbl tr:hover td{{background:#f8f9fa}}.badge-green{{background:#dcfce7;color:#16a34a;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700}}.badge-yellow{{background:#fef3c7;color:#f59e0b;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700}}.badge-red{{background:#fecaca;color:#dc2626;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700}}.panel-full{{background:#fff;border-radius:14px;padding:22px;border:1px solid #e8ecf0}}</style></head><body><div class="dash-banner"><div class="banner-left"><h1>{greeting}, {user}님 👋</h1><p>📅 {td.strftime("%Y년 %m월 %d일")} · 하나은행 고객관리시스템</p></div><div class="banner-right"><div class="banner-stat"><div class="bs-label">오늘 인입</div><div class="bs-val">{오늘인입}</div></div><div class="banner-stat"><div class="bs-label">이번 주</div><div class="bs-val">{이번주}</div></div><div class="banner-stat"><div class="bs-label">이번 달</div><div class="bs-val">{이번달}</div></div></div></div><div class="kpi-grid"><div class="kpi-card"><div class="kpi-icon" style="background:#f0f9f9;">📊</div><div class="kpi-label">총 고객</div><div class="kpi-val" style="color:#008485;">{총고객:,}</div><div class="kpi-sub">전체 등록</div></div><div class="kpi-card"><div class="kpi-icon" style="background:#f0fdf4;">✅</div><div class="kpi-label">개설 완료</div><div class="kpi-val" style="color:#16a34a;">{완료}</div><div class="kpi-sub">구축 완료</div></div><div class="kpi-card"><div class="kpi-icon" style="background:#fffbeb;">⏳</div><div class="kpi-label">개설 대기</div><div class="kpi-val" style="color:#f59e0b;">{대기}</div><div class="kpi-sub">처리 필요</div></div><div class="kpi-card"><div class="kpi-icon" style="background:#f1f3f5;">📈</div><div class="kpi-label">완료율</div><div class="kpi-val" style="color:#1a1a2e;">{완료율}%</div><div class="kpi-sub">개설완료/전체</div></div></div>{alert_html}<div class="panel-grid"><div class="panel"><div class="panel-title"><div class="pt-icon">🏆</div> 담당자별 실적 TOP 5</div>{rr}</div><div class="panel"><div class="panel-title"><div class="pt-icon">📋</div> 관리 현황</div>{mi}<div style="margin-top:16px;padding-top:12px;border-top:1px solid #eef1f5;"><div style="font-size:12px;font-weight:700;color:#8c95a6;margin-bottom:10px;">구축형별 분포</div>{gr}</div></div></div><div class="panel-full"><div class="panel-title"><div class="pt-icon">🕐</div> 최근 접수 내역</div><table class="recent-tbl"><thead><tr>{rtth}</tr></thead><tbody>{rtrows}</tbody></table></div></body></html>'''
    components.html(dh, height=1150, scrolling=True)
    page_wrapper_close()
