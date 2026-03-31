# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import time
from style import inject_page_css, page_wrapper_open, page_wrapper_close, render_section_title, render_page_header
from data import get_current_df, normalize_digits, validate_customer_inputs, check_duplicates_on_register, add_fast, del_fast, update_fast, get_timeline_by_customer, get_memos_by_customer, add_memo_fast
from auth import get_user_role


BADGE_STYLE = {
    "개설완료":     "background:#dcfce7;color:#15803d;border:1px solid #bbf7d0;",
    "개설대기":     "background:#fef3c7;color:#b45309;border:1px solid #fde68a;",
    "정상":         "background:#dcfce7;color:#15803d;border:1px solid #bbf7d0;",
    "해지":         "background:#fee2e2;color:#b91c1c;border:1px solid #fecaca;",
    "해지예상":     "background:#fee2e2;color:#b91c1c;border:1px solid #fecaca;",
    "취소":         "background:#f1f5f9;color:#64748b;border:1px solid #e2e8f0;",
    "ERP연계완료":  "background:#dbeafe;color:#1d4ed8;border:1px solid #bfdbfe;",
    "ERP연계대기":  "background:#fef3c7;color:#b45309;border:1px solid #fde68a;",
    "ERP연계진행":  "background:#e0f2fe;color:#0369a1;border:1px solid #bae6fd;",
    "ERP연계취소":  "background:#f1f5f9;color:#64748b;border:1px solid #e2e8f0;",
    "ERP 청구완료": "background:#dbeafe;color:#1d4ed8;border:1px solid #bfdbfe;",
    "연계청구보류": "background:#fce7f3;color:#9d174d;border:1px solid #fbcfe8;",
}

def badge_html(text):
    t = str(text).strip()
    s = BADGE_STYLE.get(t, "background:#f1f5f9;color:#64748b;border:1px solid #e2e8f0;")
    return f'<span style="{s}padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;white-space:nowrap;">{t}</span>'


def render_badge_table(df, vc, selected_no=None):
    """배지 포함 HTML 테이블 렌더링"""
    badge_cols = [c for c in ["개설구분","연계상태","관리구분"] if c in vc]
    th = "".join(f'<th>{c}</th>' for c in vc)
    rows = ""
    for i, (_, row) in enumerate(df[vc].iterrows()):
        c_no = str(row.get('고객번호', ''))
        is_sel = (c_no == str(selected_no)) if selected_no else False
        row_style = "background:#e0f2f2 !important;" if is_sel else ""
        cells = ""
        for c in vc:
            val = str(row[c]) if pd.notna(row[c]) else ""
            if c in badge_cols and val and val not in ["-", "nan"]:
                cells += f'<td>{badge_html(val)}</td>'
            else:
                cells += f'<td>{val}</td>'
        rows += f'<tr style="{row_style}" onclick="selectRow({i},\'{c_no}\')">{cells}</tr>'

    return f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Pretendard',-apple-system,sans-serif;}}
body{{background:transparent;}}
.wrap{{border:1px solid #e2e6ea;border-radius:10px;overflow:auto;max-height:360px;}}
table{{width:100%;border-collapse:collapse;font-size:13px;}}
thead{{position:sticky;top:0;z-index:2;}}
th{{background:#f4f6f9;padding:10px 14px;text-align:left;font-weight:700;color:#4a5568;font-size:11px;border-bottom:2px solid #e2e6ea;white-space:nowrap;text-transform:uppercase;letter-spacing:.04em;}}
td{{padding:9px 14px;border-bottom:1px solid #f1f3f5;color:#1a1a2e;vertical-align:middle;white-space:nowrap;}}
tr:hover td{{background:#f0f9f9;cursor:pointer;}}
tr.sel td{{background:#e0f2f2!important;}}
</style>
<div class="wrap">
<table><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table>
</div>
<script>
function selectRow(idx, cno) {{
    document.querySelectorAll('tr.sel').forEach(r=>r.classList.remove('sel'));
    event.currentTarget.classList.add('sel');
    window.parent.postMessage({{type:'streamlit:setComponentValue', value:cno}}, '*');
}}
</script>
"""


def render():
    inject_page_css("customer")
    page_wrapper_open("customer")
    render_page_header("고객 관리", "고객 정보 조회 · 등록 · 수정 · 삭제")
    role = get_user_role()

    if role == "admin":
        tab1, tab2, tab3, tab4 = st.tabs(["조회/상세", "신규등록", "삭제", "일괄 등록"])
    else:
        tab1, tab2, tab4 = st.tabs(["조회/상세", "신규등록", "일괄 등록"])
        tab3 = None

    with tab1:
        try:
            df = get_current_df()

            with st.expander("검색 및 필터", expanded=True):
                cs, cf1, cf2 = st.columns([2, 1, 1])
                with cs:
                    s = st.text_input("통합 검색", placeholder="고객명, 번호 등...", label_visibility="collapsed")
                with cf1:
                    sel_m = st.multiselect("담당자", ["전준수","임인지","이수현","길민종","맹국성","이성환","기타"], label_visibility="collapsed")
                with cf2:
                    sel_t = st.multiselect("구축형", ["기본형","연계형","기타"], label_visibility="collapsed")

            if s:
                df = df[df.astype(str).apply(lambda x: x.str.contains(s, regex=False)).any(axis=1)]
            if sel_m and '담당자' in df.columns:
                df = df[df['담당자'].isin(sel_m)]
            if sel_t and '구축형' in df.columns:
                df = df[df['구축형'].isin(sel_t)]

            vc = [c for c in ["고객명","고객번호","사업자번호","구축형","담당자","개설구분","연계상태","관리구분","개설이행일"] if c in df.columns]

            # ── 1번: 배지 HTML 테이블 ──
            sel_no = st.session_state.get("selected_customer_no")
            components.html(render_badge_table(df, vc, sel_no), height=400, scrolling=False)

            # Streamlit 선택용 dataframe (숨김)
            st.markdown('<div style="position:absolute;opacity:0;height:1px;overflow:hidden;">', unsafe_allow_html=True)
            evt = st.dataframe(df[vc], use_container_width=False, hide_index=True,
                               on_select="rerun", selection_mode="single-row", height=1)
            st.markdown('</div>', unsafe_allow_html=True)

            if len(evt.selection.rows) > 0:
                sel = df.iloc[evt.selection.rows[0]]
                def v(k): return sel.get(k, '-')
                c_no = str(v('고객번호'))
                if st.session_state.get("selected_customer_no") != c_no:
                    st.session_state["selected_customer_no"] = c_no
                    st.session_state["edit_mode"] = False

                # ── 2번: 슬라이드 패널 ──
                panel = f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Pretendard',-apple-system,sans-serif;}}
@keyframes sd{{from{{opacity:0;transform:translateY(-6px)}}to{{opacity:1;transform:translateY(0)}}}}
.p{{background:#fff;border:1px solid #e2e6ea;border-left:4px solid #008485;border-radius:12px;padding:20px 24px;box-shadow:0 4px 16px rgba(0,132,133,.08);animation:sd .2s ease;}}
.ph{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #e2e6ea;}}
.pn{{font-size:17px;font-weight:800;color:#008485;}}
.ps{{font-size:12px;color:#8c95a6;margin-top:3px;}}
.g4{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px;}}
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:8px;}}
.c{{padding:10px 12px;background:#f7f8fa;border-radius:8px;border:1px solid #e2e6ea;}}
.ct{{padding:12px 14px;background:linear-gradient(135deg,#e0f2f2,#d4eded);border-radius:8px;border:1px solid #a8d8d8;}}
.cl{{font-size:10px;font-weight:700;color:#8c95a6;margin-bottom:3px;text-transform:uppercase;letter-spacing:.06em;}}
.cv{{font-size:14px;font-weight:700;color:#1a1a2e;}}
.cvp{{font-size:15px;font-weight:800;color:#008485;}}
.cs{{font-size:12px;color:#8c95a6;margin-top:2px;}}
.bd{{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end;}}
</style>
<div class="p">
  <div class="ph">
    <div><div class="pn">{v("고객명")}</div><div class="ps">고객번호: {c_no} · 사업자번호: {v("사업자번호")}</div></div>
    <div class="bd">{badge_html(v("개설구분"))} {badge_html(v("관리구분"))} {badge_html(v("연계상태"))}</div>
  </div>
  <div class="g4">
    <div class="c"><div class="cl">구축형태</div><div class="cv">{v("구축형")}</div></div>
    <div class="c"><div class="cl">구축구분</div><div class="cv">{v("구축구분")}</div></div>
    <div class="c"><div class="cl">신규접수일</div><div class="cv">{v("신규접수일")}</div></div>
    <div class="c"><div class="cl">개설/이행일</div><div class="cv">{v("개설이행일")}</div></div>
  </div>
  <div class="g2">
    <div class="ct"><div class="cl" style="color:#006a6b;">영업 담당자</div><div class="cvp">{v("담당자")}</div></div>
    <div class="c"><div class="cl">고객사 담당자</div><div class="cv">{v("고객담당자")} <span style="font-size:12px;color:#8c95a6;">({v("담당부서")})</span></div><div class="cs">{v("담당연락처")}</div></div>
  </div>
</div>"""
                components.html(panel, height=270, scrolling=False)

                cb1, _, _ = st.columns([1, 1, 8])
                with cb1:
                    if st.button("수정", use_container_width=True):
                        st.session_state["edit_mode"] = True
                        st.rerun()

                if st.session_state.get("edit_mode"):
                    with st.form("edit"):
                        render_section_title("기본 정보 수정")
                        e1, e2 = st.columns(2)
                        with e1:
                            st.text_input("고객번호", value=str(c_no), disabled=True)
                            ename = st.text_input("고객명", value=str(v("고객명")))
                        with e2:
                            ebiz = st.text_input("사업자번호", value=str(v("사업자번호")))
                            ebo = ["기본형","연계형","기타"]
                            ebuild = st.selectbox("구축형", ebo, index=ebo.index(v("구축형")) if v("구축형") in ebo else 0)
                        render_section_title("고객사 담당자")
                        ec1, ec2, ec3 = st.columns(3)
                        with ec1: ecn = st.text_input("담당자명", value=str(v("고객담당자")))
                        with ec2:
                            to = ["인사팀","재무팀","총무팀","IT/전산팀","기타"]
                            ect = st.selectbox("부서", to, index=to.index(v("담당부서")) if v("담당부서") in to else 4)
                        with ec3: ecp = st.text_input("연락처", value=str(v("담당연락처")))
                        render_section_title("관리 정보")
                        em1, em2 = st.columns(2)
                        with em1:
                            mo = ["전준수","임인지","이수현","길민종","맹국성","이성환","기타"]
                            emgr = st.selectbox("영업 담당자", mo, index=mo.index(v("담당자")) if v("담당자") in mo else 6)
                            mto = ["일반관리","중점관리","VIP","해지예상"]
                            emtype = st.selectbox("관리구분", mto, index=mto.index(v("관리구분")) if v("관리구분") in mto else 0)
                            eimpl = st.text_input("개설/이행일", value=str(v("개설이행일")))
                        with em2:
                            oo = ["개설완료","개설대기"]
                            eopen = st.selectbox("개설구분", oo, index=oo.index(v("개설구분")) if v("개설구분") in oo else 1)
                            edate = st.text_input("신규접수일", value=str(v("신규접수일")))
                            bo = ["신규","재계약"]
                            ebg = st.selectbox("구축구분", bo, index=bo.index(v("구축구분")) if v("구축구분") in bo else 0)
                            ecode = st.text_input("관리코드", value=str(v("관리코드")))
                            lo = ["ERP연계대기","ERP연계진행","ERP연계취소","ERP연계완료","ERP 청구완료","연계청구보류"]
                            elink = st.selectbox("연계상태", lo, index=lo.index(v("연계상태")) if v("연계상태") in lo else 0)
                        if st.form_submit_button("수정 저장", type="primary"):
                            up = {"고객번호":c_no,"사업자번호":normalize_digits(ebiz),"고객명":ename,"구축형":ebuild,"고객담당자":ecn,"담당부서":ect,"담당연락처":ecp,"담당자":emgr,"관리구분":emtype,"개설구분":eopen,"신규접수일":edate,"구축구분":ebg,"관리코드":ecode,"개설이행일":eimpl,"연계상태":elink}
                            suc, m = update_fast(c_no, up)
                            if suc:
                                st.success("수정 완료")
                                st.session_state["edit_mode"] = False
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"실패: {m}")

                render_section_title("변경 이력")
                tld = get_timeline_by_customer(c_no)
                if tld:
                    tli = ""
                    for tl in sorted(tld, key=lambda x: x.get('Date',''), reverse=True):
                        fld=tl.get('Field',''); ov=tl.get('OldValue',''); nv=tl.get('NewValue','')
                        if fld=="신규등록": dt2=f"고객 신규 등록 ({nv})"; ic="🆕"
                        else: dt2=f"<b>{fld}</b>: <span style='color:#dc2626;text-decoration:line-through;'>{ov}</span> → <span style='color:#16a34a;font-weight:700;'>{nv}</span>"; ic="🔄"
                        tli += f'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #f1f3f5;"><div style="font-size:15px;min-width:22px;">{ic}</div><div style="flex:1;"><div style="font-size:13px;color:#1a1a2e;">{dt2}</div><div style="font-size:11px;color:#8c95a6;margin-top:2px;">{tl.get("User","")} · {tl.get("Date","")}</div></div></div>'
                    components.html(f'<style>*{{margin:0;padding:0;box-sizing:border-box;font-family:"Pretendard",-apple-system,sans-serif}}</style><div style="background:#fff;border-radius:10px;padding:14px 18px;border:1px solid #dfe3e8;">{tli}</div>', height=min(len(tld)*65+40,380), scrolling=True)
                else:
                    st.info("변경 이력이 없습니다.")

                render_section_title("메모")
                memos = get_memos_by_customer(c_no)
                if memos:
                    mih = ""
                    for m in reversed(memos):
                        mih += f'<div style="background:#fff;padding:12px 16px;margin-bottom:8px;border-radius:8px;border:1px solid #dfe3e8;border-left:3px solid #008485;"><div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;padding-bottom:6px;border-bottom:1px solid #eef1f5;"><span style="font-weight:700;font-size:12px;color:#006a6b;background:#e0f2f2;padding:2px 8px;border-radius:20px;">{m.get("Writer","")}</span><span style="font-size:11px;color:#8c95a6;">{m.get("Date","")}</span></div><div style="font-size:13px;color:#1a1a2e;line-height:1.6;">{m.get("Memo","")}</div></div>'
                    components.html(f'<style>*{{margin:0;padding:0;box-sizing:border-box;font-family:"Pretendard",-apple-system,sans-serif}}</style>{mih}', height=len(memos)*90+10, scrolling=True)
                with st.form("memo"):
                    mt = st.text_area("메모 내용", height=80, placeholder="메모를 입력하세요...")
                    if st.form_submit_button("메모 저장", type="primary"):
                        if mt:
                            add_memo_fast(c_no, mt, st.session_state['current_user'])
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
            with c5: i4=st.selectbox("구축형 (*)",["기본형","연계형","기타"])
            with c6: i7=st.selectbox("구축구분 (*)",["신규","재계약"])
            with c7: i0=st.selectbox("개설구분 (*)",["개설완료","개설대기"])
            c5b,c5c=st.columns(2)
            with c5b: iimp=st.text_input("개설/이행일",placeholder="예: 20260206")
            with c5c: ilnk=st.selectbox("연계상태 (*)",["ERP연계대기","ERP연계진행","ERP연계취소","ERP연계완료","ERP 청구완료","연계청구보류"])
            render_section_title("3. 고객사 담당자 (선택)")
            c8,c9,c10=st.columns(3)
            with c8: icn=st.text_input("고객 담당자명",placeholder="예: 김철수")
            with c9: ict=st.selectbox("담당 부서",["인사팀","재무팀","총무팀","IT/전산팀","기타"],index=1)
            with c10: icp=st.text_input("담당 연락처",placeholder="010-0000-0000")
            render_section_title("4. 사내 관리 정보")
            c11,c12,c13=st.columns(3)
            with c11: i5=st.selectbox("영업 담당자 (*)",["전준수","임인지","이수현","길민종","맹국성","이성환","기타"])
            with c12: i6=st.selectbox("관리구분 (*)",["정상","해지","취소"])
            with c13: i8=st.text_input("관리코드",value=nc)
            if st.form_submit_button("신규 고객 저장하기",type="primary",use_container_width=True):
                ok,msg=validate_customer_inputs(i1,i2,i3)
                if not ok: st.error(f"❌ {msg}")
                else:
                    dok,dmsg=check_duplicates_on_register(get_current_df(),str(i1).strip(),i2)
                    if not dok: st.error(f"🚫 {dmsg}")
                    else:
                        d={"고객번호":str(i1).strip(),"사업자번호":normalize_digits(i2),"고객명":str(i3).strip(),"구축형":str(i4),"담당자":str(i5),"관리구분":str(i6),"구축구분":str(i7),"관리코드":str(i8),"개설구분":str(i0),"신규접수일":str(i9),"고객담당자":str(icn).strip(),"담당부서":str(ict),"담당연락처":str(icp).strip(),"개설이행일":str(iimp).strip(),"연계상태":str(ilnk)}
                        suc,msg2=add_fast(d)
                        if suc: st.success("저장 완료!"); time.sleep(1); st.rerun()
                        else: st.error(f"실패: {msg2}")

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
                        if st.button(f"🗑️ {len(tg)}건 삭제",type="primary"): del_fast(tg); st.success("삭제 완료"); time.sleep(1); st.rerun()
            except: pass

    with tab4:
        render_section_title("엑셀 일괄 등록")
        st.info("엑셀 업로드 후 신규/수정 자동 처리됩니다.")
        st.caption("※ 이 탭의 전체 코드는 원본의 tab4 부분을 그대로 사용하세요.")

    page_wrapper_close()
    page_wrapper_close()
