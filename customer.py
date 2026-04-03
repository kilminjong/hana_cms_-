# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import time
from style import inject_page_css, page_wrapper_open, page_wrapper_close, render_section_title, render_page_header
from data import get_current_df, normalize_digits, validate_customer_inputs, check_duplicates_on_register, add_fast, del_fast, update_fast, get_timeline_by_customer, get_memos_by_customer, add_memo_fast
from auth import get_user_role

BADGE_BG = {
    "개설완료":    "background-color:#dcfce7;color:#15803d;font-weight:700;",
    "개설대기":    "background-color:#fef3c7;color:#b45309;font-weight:700;",
    "정상":        "background-color:#dcfce7;color:#15803d;font-weight:700;",
    "해지":        "background-color:#fee2e2;color:#b91c1c;font-weight:700;",
    "해지예상":    "background-color:#fee2e2;color:#b91c1c;font-weight:700;",
    "취소":        "background-color:#f1f5f9;color:#64748b;font-weight:700;",
    "ERP연계완료": "background-color:#dbeafe;color:#1d4ed8;font-weight:700;",
    "ERP연계대기": "background-color:#fef3c7;color:#b45309;font-weight:700;",
    "ERP연계진행": "background-color:#e0f2fe;color:#0369a1;font-weight:700;",
    "ERP연계취소": "background-color:#f1f5f9;color:#64748b;font-weight:700;",
    "ERP 청구완료":"background-color:#dbeafe;color:#1d4ed8;font-weight:700;",
    "연계청구보류": "background-color:#fce7f3;color:#9d174d;font-weight:700;",
}

def color_cell(val):
    return BADGE_BG.get(str(val).strip(), "")

def badge_html(text):
    t = str(text).strip()
    s = BADGE_BG.get(t, "background-color:#f1f5f9;color:#64748b;")
    return f'<span style="{s}padding:3px 10px;border-radius:20px;font-size:12px;border:1px solid rgba(0,0,0,0.08);white-space:nowrap;">{t}</span>'

ERP_CO  = ["","더존비즈온","자체개발","영림원","이카운트","ORACLE","오직","디모데","지저스온","큐베이스"]
ERP_TY  = ["","amaranth10","ERP-10","옴니이솔","ICUBE","디모데","오직","자체개발","영림"]
ERP_DB  = ["","MSSQL","Oracle","Mysql","TIBERO","Maria DB","postgres"]
LNK_TY  = ["","DB to DB","RFC","SFTP","FTP","API"]
SCH_TY  = ["","Y","N"]
DEPT_TY = ["인사팀","재무팀","총무팀","IT/전산팀","기타"]
MGR_TY  = ["전준수","임인지","이수현","길민종","맹국성","이성환","기타"]
MNG_TY  = ["일반관리","중점관리","VIP","해지예상"]
OPEN_TY = ["개설완료","개설대기"]
BUILD_TY= ["신규","재계약"]
LINK_TY = ["ERP연계대기","ERP연계진행","ERP연계취소","ERP연계완료","ERP 청구완료","연계청구보류"]
BUILD_F = ["기본형","연계형","기타"]
MGMT_TY = ["정상","해지","취소"]


def detail_page(sel, df, role):
    def v(k): return str(sel.get(k, '') or '').strip() or '-'
    c_no = v('고객번호')
    edit = st.session_state.get("edit_mode", False)

    # 뒤로가기
    col_back, col_edit = st.columns([1, 9])
    with col_back:
        if st.button("← 목록으로", key="back_btn"):
            st.session_state["selected_customer_no"] = None
            st.session_state["edit_mode"] = False
            st.rerun()
    with col_edit:
        if not edit:
            if st.button("✏️ 수정", key="edit_toggle", type="primary"):
                st.session_state["edit_mode"] = True
                st.rerun()
        else:
            if st.button("✕ 수정 취소", key="edit_cancel"):
                st.session_state["edit_mode"] = False
                st.rerun()

    # ── 조회 모드 ──
    if not edit:
        st.markdown(f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
.dw * {{ font-family:'Pretendard',-apple-system,sans-serif !important; }}
.sb {{ background:#fff;border:1px solid #e2e6ea;border-radius:10px;padding:16px 20px;margin-bottom:12px; }}
.st {{ font-size:13px;font-weight:800;color:#008485;border-bottom:2px solid #008485;padding-bottom:8px;margin-bottom:14px; }}
.it {{ width:100%;border-collapse:collapse;font-size:13px; }}
.it td {{ padding:7px 12px;border:1px solid #e2e6ea;color:#1a1a2e;vertical-align:middle; }}
.it td.lb {{ background:#f4f6f9;font-weight:700;color:#4a5568;width:120px;white-space:nowrap; }}
.it td.vl {{ background:#fff; }}
.it td.vh {{ background:#fff;font-weight:700;color:#008485; }}
</style>
<div class="dw">
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
  <div class="sb">
    <div class="st">고객 정보</div>
    <table class="it">
      <tr><td class="lb">고객명</td><td class="vh" colspan="3">{v("고객명")}</td></tr>
      <tr><td class="lb">고객번호</td><td class="vl">{c_no}</td><td class="lb">사업자번호</td><td class="vl">{v("사업자번호")}</td></tr>
      <tr><td class="lb">구축형</td><td class="vl">{v("구축형")}</td><td class="lb">구축구분</td><td class="vl">{v("구축구분")}</td></tr>
      <tr><td class="lb">관리코드</td><td class="vl">{v("관리코드")}</td><td class="lb">관리구분</td><td class="vl">{v("관리구분")}</td></tr>
      <tr><td class="lb">신규접수일</td><td class="vl">{v("신규접수일")}</td><td class="lb">개설/이행일</td><td class="vl">{v("개설이행일")}</td></tr>
      <tr><td class="lb">개설구분</td><td class="vl">{badge_html(v("개설구분"))}</td><td class="lb">연계상태</td><td class="vl">{badge_html(v("연계상태"))}</td></tr>
    </table>
  </div>
  <div class="sb">
    <div class="st">담당자 정보</div>
    <table class="it">
      <tr><td class="lb">영업 담당자</td><td class="vh" colspan="3">{v("담당자")}</td></tr>
      <tr><td class="lb">고객사 담당자</td><td class="vl">{v("고객담당자")}</td><td class="lb">부서</td><td class="vl">{v("담당부서")}</td></tr>
      <tr><td class="lb">연락처</td><td class="vl" colspan="3">{v("담당연락처")}</td></tr>
    </table>
  </div>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
  <div class="sb">
    <div class="st">ERP 정보</div>
    <table class="it">
      <tr><td class="lb">ERP 회사</td><td class="vl">{v("ERP회사")}</td><td class="lb">ERP 종류</td><td class="vl">{v("ERP종류")}</td></tr>
      <tr><td class="lb">ERP DB</td><td class="vl">{v("ERPDB")}</td><td class="lb">연계방식</td><td class="vl">{v("연계방식")}</td></tr>
      <tr><td class="lb">스케줄 사용</td><td class="vl" colspan="3">{v("스케줄사용여부")}</td></tr>
    </table>
  </div>
  <div class="sb">
    <div class="st">서버 정보</div>
    <table class="it">
      <tr><td class="lb">서버 위치</td><td class="vl" colspan="3">{v("서버위치")}</td></tr>
    </table>
  </div>
</div>
</div>
""", unsafe_allow_html=True)

    # ── 수정 모드 — 각 섹션 박스에서 인라인으로 수정 ──
    else:
        with st.form("inline_edit"):
            # 고객 정보 섹션
            st.markdown('<div style="background:#fff;border:1px solid #e2e6ea;border-radius:10px;padding:16px 20px;margin-bottom:12px;"><div style="font-size:13px;font-weight:800;color:#008485;border-bottom:2px solid #008485;padding-bottom:8px;margin-bottom:14px;">고객 정보</div>', unsafe_allow_html=True)
            r1c1, r1c2 = st.columns(2)
            with r1c1:
                st.text_input("고객번호", value=c_no, disabled=True)
                ename = st.text_input("고객명", value=v("고객명"))
            with r1c2:
                ebiz = st.text_input("사업자번호", value=v("사업자번호"))
                ebuild = st.selectbox("구축형", BUILD_F, index=BUILD_F.index(v("구축형")) if v("구축형") in BUILD_F else 0)
            r2c1, r2c2 = st.columns(2)
            with r2c1:
                ecode = st.text_input("관리코드", value=v("관리코드"))
                edate = st.text_input("신규접수일", value=v("신규접수일"))
                eopen = st.selectbox("개설구분", OPEN_TY, index=OPEN_TY.index(v("개설구분")) if v("개설구분") in OPEN_TY else 0)
            with r2c2:
                emtype_opt = ["정상","해지","취소","일반관리","중점관리","VIP","해지예상"]
                emtype = st.selectbox("관리구분", emtype_opt, index=emtype_opt.index(v("관리구분")) if v("관리구분") in emtype_opt else 0)
                eimpl = st.text_input("개설/이행일", value=v("개설이행일"))
                elink = st.selectbox("연계상태", LINK_TY, index=LINK_TY.index(v("연계상태")) if v("연계상태") in LINK_TY else 0)
            st.markdown('<div style="background:#f0fafa;border-radius:6px;padding:2px 0 6px 0;margin-bottom:4px;"><div style="font-size:12px;color:#8c95a6;padding:4px 8px;">구축구분</div>', unsafe_allow_html=True)
            ebg = st.selectbox("구축구분", BUILD_TY, index=BUILD_TY.index(v("구축구분")) if v("구축구분") in BUILD_TY else 0, label_visibility="collapsed")
            st.markdown('</div></div>', unsafe_allow_html=True)

            # 담당자 정보 섹션
            st.markdown('<div style="background:#fff;border:1px solid #e2e6ea;border-radius:10px;padding:16px 20px;margin-bottom:12px;"><div style="font-size:13px;font-weight:800;color:#008485;border-bottom:2px solid #008485;padding-bottom:8px;margin-bottom:14px;">담당자 정보</div>', unsafe_allow_html=True)
            dc1, dc2, dc3 = st.columns(3)
            with dc1: emgr = st.selectbox("영업 담당자", MGR_TY, index=MGR_TY.index(v("담당자")) if v("담당자") in MGR_TY else 6)
            with dc2: ecn = st.text_input("고객사 담당자", value=v("고객담당자"))
            with dc3:
                ect = st.selectbox("부서", DEPT_TY, index=DEPT_TY.index(v("담당부서")) if v("담당부서") in DEPT_TY else 4)
            ecp = st.text_input("연락처", value=v("담당연락처"))
            st.markdown('</div>', unsafe_allow_html=True)

            # ERP 정보 섹션
            st.markdown('<div style="background:#fff;border:1px solid #e2e6ea;border-radius:10px;padding:16px 20px;margin-bottom:12px;"><div style="font-size:13px;font-weight:800;color:#008485;border-bottom:2px solid #008485;padding-bottom:8px;margin-bottom:14px;">ERP 및 서버 정보</div>', unsafe_allow_html=True)
            ec1, ec2, ec3 = st.columns(3)
            with ec1: eerpc = st.selectbox("ERP 회사", ERP_CO, index=ERP_CO.index(v("ERP회사")) if v("ERP회사") in ERP_CO else 0)
            with ec2: eerpt = st.selectbox("ERP 종류", ERP_TY, index=ERP_TY.index(v("ERP종류")) if v("ERP종류") in ERP_TY else 0)
            with ec3: eerpdb = st.selectbox("ERP DB", ERP_DB, index=ERP_DB.index(v("ERPDB")) if v("ERPDB") in ERP_DB else 0)
            ec4, ec5, ec6 = st.columns(3)
            with ec4: elnk = st.selectbox("연계방식", LNK_TY, index=LNK_TY.index(v("연계방식")) if v("연계방식") in LNK_TY else 0)
            with ec5: esched = st.selectbox("스케줄 사용여부", SCH_TY, index=SCH_TY.index(v("스케줄사용여부")) if v("스케줄사용여부") in SCH_TY else 0)
            with ec6: esvr = st.text_input("서버 위치", value=v("서버위치") if v("서버위치") != "-" else "")
            st.markdown('</div>', unsafe_allow_html=True)

            # 저장 버튼
            if st.form_submit_button("✅ 수정 저장", type="primary", use_container_width=True):
                up = {
                    "고객번호":c_no, "사업자번호":normalize_digits(ebiz), "고객명":ename,
                    "구축형":ebuild, "고객담당자":ecn, "담당부서":ect, "담당연락처":ecp,
                    "담당자":emgr, "관리구분":emtype, "개설구분":eopen,
                    "신규접수일":edate, "구축구분":ebg, "관리코드":ecode,
                    "개설이행일":eimpl, "연계상태":elink,
                    "ERP회사":eerpc, "ERP종류":eerpt, "ERPDB":eerpdb,
                    "연계방식":elnk, "스케줄사용여부":esched, "서버위치":esvr
                }
                suc, m = update_fast(c_no, up)
                if suc:
                    st.success("✅ 수정 완료! 구글시트에 저장 중...")
                    st.session_state["edit_mode"] = False
                    # 세션 데이터 갱신
                    for k in ['local_df']:
                        if k in st.session_state:
                            del st.session_state[k]
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"실패: {m}")

    # 메모 + 타임라인
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    col_memo, col_timeline = st.columns([1, 1])

    with col_memo:
        render_section_title("메모")
        memos = get_memos_by_customer(c_no)
        if memos:
            mih = ""
            for m in reversed(memos):
                mih += f'<div style="background:#fff;padding:12px 16px;margin-bottom:8px;border-radius:8px;border:1px solid #dfe3e8;border-left:3px solid #008485;"><div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><span style="font-weight:700;font-size:12px;color:#006a6b;background:#e0f2f2;padding:2px 8px;border-radius:20px;">{m.get("Writer","")}</span><span style="font-size:11px;color:#8c95a6;">{m.get("Date","")}</span></div><div style="font-size:13px;color:#1a1a2e;line-height:1.6;">{m.get("Memo","")}</div></div>'
            components.html(f'<style>*{{margin:0;padding:0;box-sizing:border-box;font-family:"Pretendard",-apple-system,sans-serif}}</style>{mih}', height=min(len(memos)*100+20, 300), scrolling=True)
        with st.form("memo_form"):
            mt = st.text_area("메모 입력", height=80, placeholder="메모를 입력하세요...", label_visibility="collapsed")
            if st.form_submit_button("메모 저장", type="primary", use_container_width=True):
                if mt:
                    add_memo_fast(c_no, mt, st.session_state['current_user'])
                    st.rerun()

    with col_timeline:
        render_section_title("변경 이력")
        tld = get_timeline_by_customer(c_no)
        if tld:
            tli = ""
            for tl in sorted(tld, key=lambda x: x.get('Date',''), reverse=True):
                fld=tl.get('Field',''); ov=tl.get('OldValue',''); nv=tl.get('NewValue','')
                if fld=="신규등록": dt2=f"고객 신규 등록 ({nv})"; ic="🆕"
                else: dt2=f"<b>{fld}</b>: <span style='color:#dc2626;text-decoration:line-through;'>{ov}</span> → <span style='color:#16a34a;font-weight:700;'>{nv}</span>"; ic="🔄"
                tli += f'<div style="display:flex;gap:10px;padding:9px 0;border-bottom:1px solid #f1f3f5;"><div style="font-size:14px;min-width:20px;">{ic}</div><div style="flex:1;"><div style="font-size:12px;color:#1a1a2e;">{dt2}</div><div style="font-size:11px;color:#8c95a6;margin-top:2px;">{tl.get("User","")} · {tl.get("Date","")}</div></div></div>'
            components.html(f'<style>*{{margin:0;padding:0;box-sizing:border-box;font-family:"Pretendard",-apple-system,sans-serif}}</style><div style="background:#fff;border-radius:8px;padding:12px 16px;border:1px solid #dfe3e8;">{tli}</div>', height=min(len(tld)*60+30, 300), scrolling=True)
        else:
            st.info("변경 이력이 없습니다.")


def render():
    inject_page_css("customer")
    page_wrapper_open("customer")
    role = get_user_role()

    # 상세 페이지 모드
    if st.session_state.get("selected_customer_no"):
        df = get_current_df()
        c_no = st.session_state["selected_customer_no"]
        if '고객번호' in df.columns:
            match = df[df['고객번호'].astype(str).str.strip() == str(c_no).strip()]
            if not match.empty:
                render_page_header("고객 상세", f"{match.iloc[0].get('고객명','')} · {c_no}")
                detail_page(match.iloc[0], df, role)
                page_wrapper_close()
                return

    # 목록 페이지 모드
    render_page_header("고객 관리", "고객 정보 조회 · 등록 · 수정 · 삭제")

    # 탭 인덱스 session_state 초기화
    if 'customer_tab' not in st.session_state:
        st.session_state['customer_tab'] = 0

    if role == "admin":
        tab_labels = ["조회/상세", "신규등록", "삭제", "일괄 등록"]
        tab1, tab2, tab3, tab4 = st.tabs(tab_labels)
    else:
        tab_labels = ["조회/상세", "신규등록", "일괄 등록"]
        tab1, tab2, tab4 = st.tabs(tab_labels)
        tab3 = None

    # JS로 탭 강제 이동
    target_tab = st.session_state.get('customer_tab', 0)
    if target_tab > 0:
        st.session_state['customer_tab'] = 0
        st.markdown(f"""<script>
        window.addEventListener('load', function() {{
            setTimeout(function() {{
                var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
                if (tabs.length > {target_tab - 1}) tabs[0].click();
            }}, 100);
        }});
        </script>""", unsafe_allow_html=True)

    with tab1:
        try:
            df = get_current_df()
            with st.expander("검색 및 필터", expanded=True):
                cs, cf1, cf2 = st.columns([2, 1, 1])
                with cs:
                    s = st.text_input("통합 검색", placeholder="고객명, 번호 등...", label_visibility="collapsed")
                with cf1:
                    sel_m = st.multiselect("담당자", MGR_TY, label_visibility="collapsed", placeholder="담당자 선택")
                with cf2:
                    sel_t = st.multiselect("구축형", ["기본형","연계형","기타"], label_visibility="collapsed", placeholder="구축형 선택")

            if s:
                df = df[df.astype(str).apply(lambda x: x.str.contains(s, regex=False)).any(axis=1)]
            if sel_m and '담당자' in df.columns:
                df = df[df['담당자'].isin(sel_m)]
            if sel_t and '구축형' in df.columns:
                df = df[df['구축형'].isin(sel_t)]

            vc = [c for c in ["고객명","고객번호","사업자번호","구축형","담당자","개설구분","연계상태","관리구분","개설이행일"] if c in df.columns]
            badge_cols = [c for c in ["개설구분","연계상태","관리구분"] if c in vc]

            df_display = df[vc].copy()
            for col in badge_cols:
                df_display[col] = df_display[col].replace('', '미설정').fillna('미설정')

            styled = df_display.style.map(color_cell, subset=badge_cols)
            st.caption("행을 클릭하면 고객 상세 페이지로 이동합니다.")
            evt = st.dataframe(styled, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", height=500)

            if len(evt.selection.rows) > 0:
                sel = df.iloc[evt.selection.rows[0]]
                c_no = str(sel.get('고객번호', '')).strip()
                if c_no:
                    st.session_state["selected_customer_no"] = c_no
                    st.session_state["edit_mode"] = False
                    st.rerun()
        except Exception:
            st.rerun()

    with tab2:
        render_section_title("신규 고객 등록")
        cdf = get_current_df(); nc = "3000"
        if not cdf.empty and "관리코드" in cdf.columns:
            try:
                ncc = pd.to_numeric(cdf["관리코드"], errors='coerce').dropna()
                if not ncc.empty: nc = str(int(ncc.max())+1)
            except: pass
        st.info(f"필수 항목(*)을 입력해 주세요. 관리코드는 **{nc}**번으로 자동 배정됩니다.")
        with st.form("reg"):
            render_section_title("1. 고객사 기본 정보")
            c1,c2=st.columns([2,1])
            with c1: i3=st.text_input("고객명 (*)",placeholder="예: (주)하나상사")
            with c2: i2=st.text_input("사업자번호 (*)",placeholder="숫자 10자리")
            c3,c4=st.columns(2)
            with c3: i1=st.text_input("고객번호 (*)",placeholder="은행 부여 번호")
            with c4: i9=st.date_input("신규접수일",value=datetime.date.today())
            render_section_title("2. 구축 및 계약 상세")
            c5,c6,c7=st.columns(3)
            with c5: i4=st.selectbox("구축형 (*)",BUILD_F)
            with c6: i7=st.selectbox("구축구분 (*)",BUILD_TY)
            with c7: i0=st.selectbox("개설구분 (*)",OPEN_TY)
            c5b,c5c=st.columns(2)
            with c5b: iimp=st.text_input("개설/이행일",placeholder="예: 20260206")
            with c5c: ilnk=st.selectbox("연계상태 (*)",LINK_TY)
            render_section_title("3. ERP 및 서버 정보 (선택)")
            ex1,ex2,ex3=st.columns(3)
            with ex1: i_erpc=st.selectbox("ERP 회사",ERP_CO)
            with ex2: i_erpt=st.selectbox("ERP 종류",ERP_TY)
            with ex3: i_erpdb=st.selectbox("ERP DB",ERP_DB)
            ex4,ex5,ex6=st.columns(3)
            with ex4: i_lnk=st.selectbox("연계방식",LNK_TY)
            with ex5: i_sched=st.selectbox("스케줄 사용여부",SCH_TY)
            with ex6: i_svr=st.text_input("서버 위치",placeholder="서버 상세 위치 직접 입력")
            render_section_title("4. 고객사 담당자 (선택)")
            c8,c9,c10=st.columns(3)
            with c8: icn=st.text_input("고객 담당자명",placeholder="예: 김철수")
            with c9: ict=st.selectbox("담당 부서",DEPT_TY,index=1)
            with c10: icp=st.text_input("담당 연락처",placeholder="010-0000-0000")
            render_section_title("5. 사내 관리 정보")
            c11,c12,c13=st.columns(3)
            with c11: i5=st.selectbox("영업 담당자 (*)",MGR_TY)
            with c12: i6=st.selectbox("관리구분 (*)",MGMT_TY)
            with c13: i8=st.text_input("관리코드",value=nc)
            if st.form_submit_button("신규 고객 저장하기",type="primary",use_container_width=True):
                ok,msg=validate_customer_inputs(i1,i2,i3)
                if not ok: st.error(f"❌ {msg}")
                else:
                    dok,dmsg=check_duplicates_on_register(get_current_df(),str(i1).strip(),i2)
                    if not dok: st.error(f"🚫 {dmsg}")
                    else:
                        d={"고객번호":str(i1).strip(),"사업자번호":normalize_digits(i2),"고객명":str(i3).strip(),"구축형":str(i4),"담당자":str(i5),"관리구분":str(i6),"구축구분":str(i7),"관리코드":str(i8),"개설구분":str(i0),"신규접수일":str(i9),"고객담당자":str(icn).strip(),"담당부서":str(ict),"담당연락처":str(icp).strip(),"개설이행일":str(iimp).strip(),"연계상태":str(ilnk),"ERP회사":str(i_erpc),"ERP종류":str(i_erpt),"ERPDB":str(i_erpdb),"연계방식":str(i_lnk),"스케줄사용여부":str(i_sched),"서버위치":str(i_svr).strip()}
                        suc,msg2=add_fast(d)
                        if suc:
                            st.success("✅ 등록 완료! 조회/상세 탭으로 이동합니다.")
                            time.sleep(1)
                            st.session_state['customer_tab'] = 0
                            st.rerun()
                        else:
                            st.error(f"실패: {msg2}")

    if tab3 is not None:
        with tab3:
            render_section_title("고객 삭제")
            try:
                df=get_current_df(); sd=st.text_input("삭제 검색",placeholder="고객명 등...")
                if sd: df=df[df.astype(str).apply(lambda x:x.str.contains(sd,regex=False)).any(axis=1)]
                cols=[c for c in ["고객번호","고객명","사업자번호","연계상태","개설이행일"] if c in df.columns]
                sel=st.dataframe(df[cols],use_container_width=True,hide_index=True,on_select="rerun",selection_mode="multi-row")
                if len(sel.selection.rows)>0:
                    col=next((c for c in df.columns if "고객번호" in c),None)
                    if col:
                        tg=df.iloc[sel.selection.rows][col].tolist()
                        if st.button(f"🗑️ {len(tg)}건 삭제", type="primary"):
                            del_fast(tg)
                            st.success("✅ 삭제 완료! 조회/상세 탭으로 이동합니다.")
                            time.sleep(1)
                            st.session_state['customer_tab'] = 0
                            st.rerun()
            except: pass

    with tab4:
        render_section_title("엑셀 일괄 등록")
        st.info("엑셀 업로드 후 신규/수정 자동 처리됩니다.")
        st.caption("※ 이 탭의 전체 코드는 원본의 tab4 부분을 그대로 사용하세요.")

    page_wrapper_close()
    page_wrapper_close()
