# -*- coding: utf-8 -*-
"""고객 관리 페이지"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import time
from style import inject_page_css, page_wrapper_open, page_wrapper_close, render_section_title, render_page_header
from data import get_current_df, normalize_digits, validate_customer_inputs, check_duplicates_on_register, add_fast, del_fast, update_fast, get_timeline_by_customer, get_memos_by_customer, add_memo_fast
from auth import get_user_role

def render():
    inject_page_css("customer");page_wrapper_open("customer")
    render_page_header("고객 관리","고객 정보 조회 · 등록 · 수정 · 삭제")
    role=get_user_role()
    if role=="admin":tab1,tab2,tab3,tab4=st.tabs(["📋 조회/상세","✍️ 신규등록","🗑️ 삭제","📂 일괄 등록"])
    else:tab1,tab2,tab4=st.tabs(["📋 조회/상세","✍️ 신규등록","📂 일괄 등록"]);tab3=None
    with tab1:
        try:
            df=get_current_df()
            with st.expander("🔍 검색 및 필터",expanded=True):
                cs,cf1,cf2=st.columns([2,1,1])
                with cs:s=st.text_input("통합 검색",placeholder="고객명, 번호 등...",label_visibility="collapsed")
                with cf1:sel_m=st.multiselect("담당자",["전준수","임인지","이수현","길민종","맹국성","이성환","기타"],label_visibility="collapsed")
                with cf2:sel_t=st.multiselect("구축형",["기본형","연계형","기타"],label_visibility="collapsed")
            if s:df=df[df.astype(str).apply(lambda x:x.str.contains(s,regex=False)).any(axis=1)]
            if sel_m and '담당자' in df.columns:df=df[df['담당자'].isin(sel_m)]
            if sel_t and '구축형' in df.columns:df=df[df['구축형'].isin(sel_t)]
            vc=[c for c in ["고객명","고객번호","사업자번호","구축형","담당자","연계상태","개설이행일","고객담당자","담당부서"] if c in df.columns]
            evt=st.dataframe(df[vc],use_container_width=True,hide_index=True,on_select="rerun",selection_mode="single-row",height=400)
            if len(evt.selection.rows)>0:
                sel=df.iloc[evt.selection.rows[0]]
                def v(k):return sel.get(k,'-')
                c_no=v('고객번호')
                if st.session_state.get("selected_customer_no")!=c_no:st.session_state["selected_customer_no"]=c_no;st.session_state["edit_mode"]=False
                dh=f'''<style>@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');*{{margin:0;padding:0;box-sizing:border-box;font-family:'Pretendard',-apple-system,sans-serif}}.card{{background:#fff;padding:28px 32px;border-radius:12px;border:1px solid #dfe3e8;box-shadow:0 2px 8px rgba(0,0,0,.06)}}.card-header{{font-size:18px;font-weight:800;color:#008485;padding-bottom:14px;border-bottom:2px solid #008485;margin-bottom:24px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}}.grid-item{{padding:14px 16px;background:#f7f8fa;border-radius:8px;border:1px solid #dfe3e8}}.grid-item .label{{font-size:11px;font-weight:700;color:#8c95a6;margin-bottom:6px}}.grid-item .value{{font-size:15px;font-weight:700;color:#1a1a2e}}.contact{{background:linear-gradient(135deg,#e0f2f2,#d4eded);padding:18px 22px;border-radius:10px;margin-bottom:20px;border:1px solid #a8d8d8}}.contact-title{{font-size:12px;font-weight:800;color:#006a6b;margin-bottom:12px}}.contact-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.highlight{{color:#008485;font-weight:700}}</style><div class="card"><div class="card-header">📋 {v("고객명")} 상세 정보</div><div class="grid"><div class="grid-item"><div class="label">고객번호</div><div class="value">{c_no}</div></div><div class="grid-item"><div class="label">사업자번호</div><div class="value">{v("사업자번호")}</div></div><div class="grid-item"><div class="label">구축형태</div><div class="value">{v("구축형")}</div></div><div class="grid-item"><div class="label">신규접수일</div><div class="value">{v("신규접수일")}</div></div></div><div class="contact"><div class="contact-title">고객사 담당자</div><div class="contact-grid"><div class="grid-item"><div class="label">성명</div><div class="value">{v("고객담당자")}</div></div><div class="grid-item"><div class="label">부서</div><div class="value">{v("담당부서")}</div></div><div class="grid-item"><div class="label">연락처</div><div class="value">{v("담당연락처")}</div></div></div></div><div class="grid"><div class="grid-item"><div class="label">영업담당</div><div class="value highlight">{v("담당자")}</div></div><div class="grid-item"><div class="label">관리구분</div><div class="value">{v("관리구분")}</div></div><div class="grid-item"><div class="label">구축구분</div><div class="value">{v("구축구분")}</div></div><div class="grid-item"><div class="label">개설구분</div><div class="value">{v("개설구분")}</div></div></div><div class="grid"><div class="grid-item"><div class="label">개설/이행일</div><div class="value">{v("개설이행일")}</div></div><div class="grid-item"><div class="label">연계상태</div><div class="value highlight">{v("연계상태")}</div></div></div></div>'''
                components.html(dh,height=490,scrolling=False)
                cb1,_,_=st.columns([1,1,8])
                with cb1:
                    if st.button("✏️ 수정",use_container_width=True):st.session_state["edit_mode"]=True;st.rerun()
                if st.session_state.get("edit_mode"):
                    with st.form("edit"):
                        render_section_title("기본 정보 수정")
                        e1,e2=st.columns(2)
                        with e1:st.text_input("고객번호",value=str(c_no),disabled=True);ename=st.text_input("고객명",value=str(v("고객명")))
                        with e2:
                            ebiz=st.text_input("사업자번호",value=str(v("사업자번호")))
                            ebo=["기본형","연계형","기타"];cub=v("구축형") if v("구축형") in ebo else "기본형";ebuild=st.selectbox("구축형",ebo,index=ebo.index(cub))
                        render_section_title("고객사 담당자")
                        ec1,ec2,ec3=st.columns(3)
                        with ec1:ecn=st.text_input("담당자명",value=str(v("고객담당자")))
                        with ec2:to=["인사팀","재무팀","총무팀","IT/전산팀","기타"];ct=v("담당부서") if v("담당부서") in to else "기타";ect=st.selectbox("부서",to,index=to.index(ct))
                        with ec3:ecp=st.text_input("연락처",value=str(v("담당연락처")))
                        render_section_title("관리 정보")
                        em1,em2=st.columns(2)
                        with em1:
                            mo=["전준수","임인지","이수현","길민종","맹국성","이성환","기타"];cm=v("담당자") if v("담당자") in mo else "기타";emgr=st.selectbox("영업 담당자",mo,index=mo.index(cm))
                            mto=["일반관리","중점관리","VIP","해지예상"];cmt=v("관리구분") if v("관리구분") in mto else "일반관리";emtype=st.selectbox("관리구분",mto,index=mto.index(cmt))
                            eimpl=st.text_input("개설/이행일",value=str(v("개설이행일")))
                        with em2:
                            oo=["개설완료","개설대기"];co=v("개설구분") if v("개설구분") in oo else "개설대기";eopen=st.selectbox("개설구분",oo,index=oo.index(co))
                            edate=st.text_input("신규접수일",value=str(v("신규접수일")))
                            bo=["신규","재계약"];cb2=v("구축구분") if v("구축구분") in bo else "신규";ebg=st.selectbox("구축구분",bo,index=bo.index(cb2))
                            ecode=st.text_input("관리코드",value=str(v("관리코드")))
                            lo=["ERP연계대기","ERP연계진행","ERP연계취소","ERP연계완료","ERP 청구완료","연계청구보류"];cl2=v("연계상태") if v("연계상태") in lo else "ERP연계대기";elink=st.selectbox("연계상태",lo,index=lo.index(cl2))
                        if st.form_submit_button("✅ 수정 저장",type="primary"):
                            up={"고객번호":c_no,"사업자번호":normalize_digits(ebiz),"고객명":ename,"구축형":ebuild,"고객담당자":ecn,"담당부서":ect,"담당연락처":ecp,"담당자":emgr,"관리구분":emtype,"개설구분":eopen,"신규접수일":edate,"구축구분":ebg,"관리코드":ecode,"개설이행일":eimpl,"연계상태":elink}
                            suc,m=update_fast(c_no,up)
                            if suc:st.success("수정 완료");st.session_state["edit_mode"]=False;time.sleep(0.5);st.rerun()
                            else:st.error(f"실패: {m}")
                # ★ 타임라인
                render_section_title("📜 변경 이력 (타임라인)")
                tld=get_timeline_by_customer(c_no)
                if tld:
                    tli=""
                    tls=sorted(tld,key=lambda x:x.get('Date',''),reverse=True)
                    for tl in tls:
                        fld=tl.get('Field','');ov=tl.get('OldValue','');nv=tl.get('NewValue','')
                        if fld=="신규등록":dt2=f"고객 신규 등록 ({nv})";ic="🆕"
                        else:dt2=f"<b>{fld}</b>: <span style='color:#dc2626;text-decoration:line-through;'>{ov}</span> → <span style='color:#16a34a;font-weight:700;'>{nv}</span>";ic="🔄"
                        tli+=f'<div style="display:flex;gap:16px;padding:12px 0;border-bottom:1px solid #f1f3f5;"><div style="font-size:16px;min-width:24px;text-align:center;">{ic}</div><div style="flex:1;"><div style="font-size:13px;color:#1a1a2e;line-height:1.5;">{dt2}</div><div style="font-size:11px;color:#8c95a6;margin-top:4px;">{tl.get("User","")} · {tl.get("Date","")}</div></div></div>'
                    tlh=f'<style>@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendart.css");*{{margin:0;padding:0;box-sizing:border-box;font-family:"Pretendard",-apple-system,sans-serif}}</style><div style="background:#fff;border-radius:10px;padding:16px 20px;border:1px solid #dfe3e8;">{tli}</div>'
                    components.html(tlh,height=min(len(tls)*75+40,500),scrolling=True)
                else:st.info("변경 이력이 없습니다. 수정 시 자동 기록됩니다.")
                render_section_title("📝 메모")
                memos=get_memos_by_customer(c_no)
                if memos:
                    mih=""
                    for m in reversed(memos):mih+=f'<div style="background:#fff;padding:16px 20px;margin-bottom:10px;border-radius:10px;border:1px solid #dfe3e8;border-left:4px solid #008485;"><div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #eef1f5;"><span style="font-weight:700;font-size:13px;color:#006a6b;background:#e0f2f2;padding:3px 12px;border-radius:20px;">{m.get("Writer","")}</span><span style="font-size:12px;color:#8c95a6;">{m.get("Date","")}</span></div><div style="font-size:14px;color:#1a1a2e;line-height:1.7;">{m.get("Memo","")}</div></div>'
                    components.html(f'<style>*{{margin:0;padding:0;box-sizing:border-box;font-family:"Pretendard",-apple-system,sans-serif}}</style>{mih}',height=len(memos)*95+10,scrolling=True)
                with st.form("memo"):
                    mt=st.text_area("메모 내용",height=80,placeholder="메모를 입력하세요...")
                    if st.form_submit_button("💾 메모 저장",type="primary"):
                        if mt:add_memo_fast(c_no,mt,st.session_state['current_user']);st.rerun()
        except Exception:st.rerun()
    with tab2:
        render_section_title("신규 고객 등록")
        cdf=get_current_df();nc="3000"
        if not cdf.empty and "관리코드" in cdf.columns:
            try:
                ncc=pd.to_numeric(cdf["관리코드"],errors='coerce').dropna()
                if not ncc.empty:nc=str(int(ncc.max())+1)
            except:pass
        st.info(f"필수 항목(*)을 입력해 주세요. 관리코드는 **{nc}**번으로 자동 배정됩니다.")
        with st.form("reg"):
            render_section_title("1. 고객사 기본 정보")
            c1,c2=st.columns([2,1])
            with c1:i3=st.text_input("고객명 (*)",placeholder="예: (주)하나상사")
            with c2:i2=st.text_input("사업자번호 (*)",placeholder="숫자 10자리")
            c3,c4=st.columns(2)
            with c3:i1=st.text_input("고객번호 (*)",placeholder="은행 부여 번호")
            with c4:i9=st.date_input("신규접수일",value=datetime.date.today())
            render_section_title("2. 구축 및 계약 상세")
            c5,c6,c7=st.columns(3)
            with c5:i4=st.selectbox("구축형 (*)",["기본형","연계형","기타"])
            with c6:i7=st.selectbox("구축구분 (*)",["신규","재계약"])
            with c7:i0=st.selectbox("개설구분 (*)",["개설완료","개설대기"])
            c5b,c5c=st.columns(2)
            with c5b:iimp=st.text_input("개설/이행일",placeholder="예: 20260206")
            with c5c:ilnk=st.selectbox("연계상태 (*)",["ERP연계대기","ERP연계진행","ERP연계취소","ERP연계완료","ERP 청구완료","연계청구보류"])
            render_section_title("3. 고객사 담당자 (선택)")
            c8,c9,c10=st.columns(3)
            with c8:icn=st.text_input("고객 담당자명",placeholder="예: 김철수")
            with c9:ict=st.selectbox("담당 부서",["인사팀","재무팀","총무팀","IT/전산팀","기타"],index=1)
            with c10:icp=st.text_input("담당 연락처",placeholder="010-0000-0000")
            render_section_title("4. 사내 관리 정보")
            c11,c12,c13=st.columns(3)
            with c11:i5=st.selectbox("영업 담당자 (*)",["전준수","임인지","이수현","길민종","맹국성","이성환","기타"])
            with c12:i6=st.selectbox("관리구분 (*)",["정상","해지","취소"])
            with c13:i8=st.text_input("관리코드",value=nc)
            if st.form_submit_button("✨ 신규 고객 저장하기",type="primary",use_container_width=True):
                ok,msg=validate_customer_inputs(i1,i2,i3)
                if not ok:st.error(f"❌ {msg}")
                else:
                    dok,dmsg=check_duplicates_on_register(get_current_df(),str(i1).strip(),i2)
                    if not dok:st.error(f"🚫 {dmsg}")
                    else:
                        d={"고객번호":str(i1).strip(),"사업자번호":normalize_digits(i2),"고객명":str(i3).strip(),"구축형":str(i4),"담당자":str(i5),"관리구분":str(i6),"구축구분":str(i7),"관리코드":str(i8),"개설구분":str(i0),"신규접수일":str(i9),"고객담당자":str(icn).strip(),"담당부서":str(ict),"담당연락처":str(icp).strip(),"개설이행일":str(iimp).strip(),"연계상태":str(ilnk)}
                        suc,msg2=add_fast(d)
                        if suc:st.success("✅ 저장 완료!");time.sleep(1);st.rerun()
                        else:st.error(f"실패: {msg2}")
    if tab3 is not None:
      with tab3:
        render_section_title("고객 삭제")
        try:
            df=get_current_df();sd=st.text_input("삭제 검색",placeholder="고객명 등...")
            if sd:df=df[df.astype(str).apply(lambda x:x.str.contains(sd,regex=False)).any(axis=1)]
            cols=[c for c in ["고객번호","고객명","사업자번호","연계상태","개설이행일"] if c in df.columns]
            sel=st.dataframe(df[cols],use_container_width=True,hide_index=True,on_select="rerun",selection_mode="multi-row")
            if len(sel.selection.rows)>0:
                col=next((c for c in df.columns if "고객번호" in c),None)
                if col:
                    tg=df.iloc[sel.selection.rows][col].tolist()
                    if st.button(f"🗑️ {len(tg)}건 삭제",type="primary"):del_fast(tg);st.success("삭제 완료");time.sleep(1);st.rerun()
        except:pass
    with tab4:
        render_section_title("엑셀 일괄 등록")
        st.info("원본 코드의 일괄 등록 탭과 동일합니다. 엑셀 업로드 후 신규/수정 자동 처리됩니다.")
        st.caption("※ 이 탭의 전체 코드는 원본의 tab4 부분을 그대로 사용하세요.")
    page_wrapper_close()
    page_wrapper_close()
