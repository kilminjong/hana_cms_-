# -*- coding: utf-8 -*-
"""
데이터 로직 모듈
- 구글시트 연결, 데이터 읽기/쓰기
- 타임라인, 메모, 알림 분석
"""

import streamlit as st
import pandas as pd
import os
import re
import datetime
import threading
import gspread
from google.oauth2.service_account import Credentials

from config import (
    GOOGLE_SHEET_URL, SHEET_DATA, SHEET_MEMOS, SHEET_LOGS,
    SHEET_TIMELINE, SHEET_USERS, DATA_HEADER_ROW,
    REMINDER_DAYS_PENDING, REMINDER_DAYS_LINKAGE
)


# ══════════════════════════════════════════════════
# 구글시트 연결
# ══════════════════════════════════════════════════

def get_client():
    """구글 API 클라이언트 생성 (Streamlit Cloud Secrets 우선, 로컬은 파일 fallback)"""
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    # Streamlit Cloud: Secrets에서 인증정보 로드
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        return gspread.authorize(
            Credentials.from_service_account_info(creds_dict, scopes=scopes)
        )
    except:
        pass
    # 로컬 실행: service_account.json 파일 fallback
    if os.path.exists('service_account.json'):
        try:
            return gspread.authorize(
                Credentials.from_service_account_file('service_account.json', scopes=scopes)
            )
        except:
            pass
    return None


def run_in_background(func, *args, **kwargs):
    """백그라운드 스레드로 실행 (UI 안 멈추게)"""
    threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()


# ══════════════════════════════════════════════════
# 유틸리티
# ══════════════════════════════════════════════════

def normalize_digits(s):
    s = "" if s is None else str(s)
    return re.sub(r"[^0-9]", "", s)


def col_to_letter(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def validate_customer_inputs(cn, bn, cname):
    c = normalize_digits(cn)
    b = normalize_digits(bn)
    if not c:
        return False, "고객번호는 필수입니다."
    if not c.isdigit():
        return False, "고객번호는 숫자만 입력하세요."
    if not b:
        return False, "사업자번호는 필수입니다."
    if len(b) != 10:
        return False, "사업자번호는 10자리여야 합니다."
    if not str(cname).strip():
        return False, "고객명은 필수입니다."
    return True, "OK"


def check_duplicates_on_register(df, cn, bn):
    if df is None or df.empty:
        return True, ""
    c = str(cn).strip()
    b = normalize_digits(bn)
    if "고객번호" in df.columns:
        if df["고객번호"].astype(str).str.strip().eq(c).any():
            return False, f"중복 고객번호: {c}"
    if "사업자번호" in df.columns:
        if df["사업자번호"].astype(str).apply(normalize_digits).eq(b).any():
            return False, f"중복 사업자번호: {b}"
    return True, ""


# ══════════════════════════════════════════════════
# 데이터 읽기/쓰기
# ══════════════════════════════════════════════════

def get_data_sheet_safe():
    cl = get_client()
    if not cl:
        return None, "인증 파일 오류"
    try:
        return cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_DATA), "Success"
    except Exception as e:
        return None, f"연결 실패: {e}"


def load_data_from_sheet():
    sheet, msg = get_data_sheet_safe()
    if not sheet:
        return None, msg
    try:
        av = sheet.get_all_values()
        if len(av) < DATA_HEADER_ROW:
            return None, "데이터 부족"
        headers = av[DATA_HEADER_ROW - 1]
        data = av[DATA_HEADER_ROW:]
        ch = []
        seen = {}
        for h in headers:
            h = str(h).strip()
            if h == "고객사명":
                h = "고객명"
            if not h:
                h = f"Empty_{len(ch)}"
            if h in seen:
                seen[h] += 1
                ch.append(f"{h}_{seen[h]}")
            else:
                seen[h] = 0
                ch.append(h)
        return pd.DataFrame(data, columns=ch), "Success"
    except Exception as e:
        return None, str(e)


def get_current_df():
    if 'local_df' not in st.session_state:
        df, msg = load_data_from_sheet()
        if df is not None:
            st.session_state['local_df'] = df
        else:
            st.session_state['local_df'] = pd.DataFrame()
    return st.session_state['local_df']


# ══════════════════════════════════════════════════
# 로그
# ══════════════════════════════════════════════════

def log_action(user, action, detail):
    def _bg(u, a, d):
        try:
            cl = get_client()
            if cl:
                cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_LOGS).append_row(
                    [str(datetime.datetime.now())[:19], u, a, d]
                )
        except:
            pass
    run_in_background(_bg, user, action, detail)


def get_system_logs():
    try:
        cl = get_client()
        if not cl:
            return pd.DataFrame()
        return pd.DataFrame(
            cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_LOGS).get_all_records()
        )
    except:
        return pd.DataFrame()


# ══════════════════════════════════════════════════
# 타임라인 (변경 이력)
# ══════════════════════════════════════════════════

def ensure_timeline_sheet():
    try:
        cl = get_client()
        if not cl:
            return
        sp = cl.open_by_url(GOOGLE_SHEET_URL)
        try:
            sp.worksheet(SHEET_TIMELINE)
        except:
            ws = sp.add_worksheet(title=SHEET_TIMELINE, rows=1000, cols=6)
            ws.append_row(["CustomerNo", "Date", "User", "Field", "OldValue", "NewValue"])
    except:
        pass


def add_timeline_entry(cno, user, field, old_val, new_val):
    def _bg(c, u, f, ov, nv):
        try:
            cl = get_client()
            if cl:
                try:
                    ws = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_TIMELINE)
                except:
                    ensure_timeline_sheet()
                    ws = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_TIMELINE)
                ws.append_row([str(c), str(datetime.datetime.now())[:19], u, f, str(ov), str(nv)])
        except:
            pass
    run_in_background(_bg, cno, user, field, old_val, new_val)
    if 'all_timeline' in st.session_state:
        st.session_state['all_timeline'].append({
            'CustomerNo': str(cno),
            'Date': str(datetime.datetime.now())[:19],
            'User': user, 'Field': field,
            'OldValue': str(old_val), 'NewValue': str(new_val)
        })


def load_all_timeline():
    if 'all_timeline' not in st.session_state:
        try:
            cl = get_client()
            if cl:
                try:
                    ws = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_TIMELINE)
                    st.session_state['all_timeline'] = ws.get_all_records()
                except:
                    ensure_timeline_sheet()
                    st.session_state['all_timeline'] = []
            else:
                st.session_state['all_timeline'] = []
        except:
            st.session_state['all_timeline'] = []
    return st.session_state['all_timeline']


def get_timeline_by_customer(cno):
    tl = load_all_timeline()
    t = str(cno).strip()
    return [r for r in tl if str(r.get('CustomerNo', '')).strip().lstrip('0') == t.lstrip('0')]


# ══════════════════════════════════════════════════
# 메모
# ══════════════════════════════════════════════════

def add_memo_fast(cno, memo, writer):
    def _bg(c, m, w):
        try:
            cl = get_client()
            if cl:
                cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_MEMOS).append_row(
                    [str(c), m, w, str(datetime.datetime.now())[:16]]
                )
        except:
            pass
    run_in_background(_bg, cno, memo, writer)
    if 'all_memos' in st.session_state:
        st.session_state['all_memos'].append({
            'CustomerNo': str(cno), 'Memo': memo,
            'Writer': writer, 'Date': str(datetime.datetime.now())[:16]
        })
    return True


def load_all_memos():
    if 'all_memos' not in st.session_state:
        try:
            cl = get_client()
            if cl:
                st.session_state['all_memos'] = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_MEMOS).get_all_records()
            else:
                st.session_state['all_memos'] = []
        except:
            st.session_state['all_memos'] = []
    return st.session_state['all_memos']


def get_memos_by_customer(cno):
    am = load_all_memos()
    t = str(cno).strip()
    return [r for r in am if str(r.get('CustomerNo', '')).strip().lstrip('0') == t.lstrip('0')]


# ══════════════════════════════════════════════════
# 구글시트 동기화 (추가/수정/삭제)
# ══════════════════════════════════════════════════

def _build_row_by_headers(hr, dm):
    ch = [str(h).strip().replace(" ", "") for h in hr]
    nr = [""] * len(hr)
    for i, cn in enumerate(ch):
        val = ""
        for k, v in dm.items():
            if k in cn:
                val = v
                break
        if "고객명" in cn and not val:
            val = dm.get("고객명", "")
        if "신규접수" in cn and not val:
            val = dm.get("신규접수일", "")
        nr[i] = str(val)
    return nr


def _sync_gsheet_update_bg(mode, dm):
    sheet, msg = get_data_sheet_safe()
    if not sheet:
        return
    try:
        headers = sheet.row_values(DATA_HEADER_ROW)
        ch = [str(h).strip().replace(" ", "") for h in headers]
        di = 1
        ci = (ch.index("고객번호") + 1) if "고객번호" in ch else None
        bi = (ch.index("사업자번호") + 1) if "사업자번호" in ch else None

        if mode == "add":
            nr = _build_row_by_headers(headers, dm)
            nr[di - 1] = ""
            sheet.append_row(nr, value_input_option="USER_ENTERED")
            if ci and bi:
                target = str(dm.get("고객번호", "")).strip()
                try:
                    cell = sheet.find(target, in_column=ci)
                except:
                    cell = sheet.find(target)
                if cell:
                    sheet.update_cell(cell.row, di,
                                      f"={col_to_letter(ci)}{cell.row}&{col_to_letter(bi)}{cell.row}")

        elif mode == "del":
            if "고객번호" not in ch:
                return
            col_idx = ch.index("고객번호") + 1
            cv = sheet.col_values(col_idx)
            rd = []
            ts = set(str(x).strip() for x in dm)
            for i, val in enumerate(cv):
                if i >= DATA_HEADER_ROW and str(val).strip() in ts:
                    rd.append(i + 1)
            for r in sorted(list(set(rd)), reverse=True):
                sheet.delete_rows(r)

        elif mode == "update":
            if "고객번호" not in dm or "고객번호" not in ch:
                return
            tn = str(dm["고객번호"]).strip()
            cidx = ch.index("고객번호") + 1
            try:
                cell = sheet.find(tn, in_column=cidx)
                if cell:
                    nr = _build_row_by_headers(headers, dm)
                    sc = di + 1
                    ec = len(headers)
                    sheet.update(
                        f"{col_to_letter(sc)}{cell.row}:{col_to_letter(ec)}{cell.row}",
                        [nr[sc - 1:ec]], value_input_option="USER_ENTERED"
                    )
            except:
                pass
    except:
        pass


def add_fast(data):
    df = st.session_state.get('local_df', pd.DataFrame())
    ndf = pd.DataFrame([data])
    if not df.empty:
        st.session_state['local_df'] = pd.concat([df, ndf], ignore_index=True)
    else:
        st.session_state['local_df'] = ndf
    run_in_background(_sync_gsheet_update_bg, "add", data)
    log_action(st.session_state.get('current_user', ''), "Add", f"등록: {data.get('고객명')}")
    add_timeline_entry(data.get('고객번호', ''), st.session_state.get('current_user', ''),
                       "신규등록", "-", data.get('고객명', ''))
    return True, "저장 완료"


def del_fast(tl):
    df = st.session_state.get('local_df', pd.DataFrame())
    if not df.empty and '고객번호' in df.columns:
        st.session_state['local_df'] = df[
            ~df['고객번호'].astype(str).str.strip().isin(set(str(x).strip() for x in tl))
        ]
    run_in_background(_sync_gsheet_update_bg, "del", tl)
    log_action(st.session_state.get('current_user', ''), "Delete", f"{len(tl)}건 삭제")
    return True, "삭제 완료"


def update_fast(cno, um):
    df = st.session_state.get('local_df', pd.DataFrame())
    cn = str(cno).strip()
    if "고객번호" not in df.columns:
        return False, "컬럼 없음"
    mask = df["고객번호"].astype(str).str.strip().eq(cn)
    if mask.any():
        old = df.loc[mask].iloc[0]
        user = st.session_state.get('current_user', '')
        # 변경 이력 추적
        for fld in ["개설구분", "관리구분", "연계상태", "담당자", "구축형", "구축구분"]:
            if fld in um and fld in old.index:
                ov = str(old[fld]).strip()
                nv = str(um[fld]).strip()
                if ov != nv:
                    add_timeline_entry(cn, user, fld, ov, nv)
        for k, v in um.items():
            if k in df.columns:
                df.loc[mask, k] = str(v)
        st.session_state["local_df"] = df
        run_in_background(_sync_gsheet_update_bg, "update", um)
        log_action(user, "Update", f"수정: {um.get('고객명')}")
        return True, "수정 완료"
    return False, "대상 없음"


# ══════════════════════════════════════════════════
# 사용자 관리
# ══════════════════════════════════════════════════

@st.cache_data(ttl=600, show_spinner=False)
def get_users():
    try:
        cl = get_client()
        if not cl:
            return {}
        r = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_USERS).get_all_records()
        return {
            str(x['username']): {
                "password": str(x['password']),
                "role": str(x.get('role', 'user')).strip() or 'user'
            } for x in r
        }
    except:
        return {}


# ══════════════════════════════════════════════════
# 알림 분석
# ══════════════════════════════════════════════════

def analyze_alerts(df):
    """고객 데이터를 분석하여 알림 생성"""
    alerts = {"critical": [], "warning": [], "info": []}
    if df is None or df.empty:
        return alerts
    td = datetime.date.today()

    # 개설대기 지연
    if '개설구분' in df.columns and '신규접수일' in df.columns:
        pend = df[df['개설구분'].astype(str).str.strip() == '개설대기'].copy()
        if not pend.empty:
            pend['dt'] = pd.to_datetime(
                pend['신규접수일'].astype(str).str.replace(r'[^0-9]', '', regex=True),
                format='%Y%m%d', errors='coerce'
            )
            for _, row in pend.iterrows():
                if pd.notna(row['dt']):
                    d = (td - row['dt'].date()).days
                    if d >= REMINDER_DAYS_PENDING:
                        alerts["critical"].append({
                            "type": "개설지연",
                            "customer": str(row.get('고객명', '')),
                            "customer_no": str(row.get('고객번호', '')),
                            "manager": str(row.get('담당자', '')),
                            "days": d,
                            "detail": f"개설대기 {d}일 경과",
                            "date": str(row.get('신규접수일', ''))
                        })

    # ERP 연계 지연
    if '연계상태' in df.columns and '신규접수일' in df.columns:
        lw = df[df['연계상태'].astype(str).str.strip().isin(['ERP연계대기', 'ERP연계진행'])].copy()
        if not lw.empty:
            lw['dt'] = pd.to_datetime(
                lw['신규접수일'].astype(str).str.replace(r'[^0-9]', '', regex=True),
                format='%Y%m%d', errors='coerce'
            )
            for _, row in lw.iterrows():
                if pd.notna(row['dt']):
                    d = (td - row['dt'].date()).days
                    if d >= REMINDER_DAYS_LINKAGE:
                        alerts["warning"].append({
                            "type": "연계지연",
                            "customer": str(row.get('고객명', '')),
                            "customer_no": str(row.get('고객번호', '')),
                            "manager": str(row.get('담당자', '')),
                            "days": d,
                            "detail": f"{row.get('연계상태', '')} {d}일 경과",
                            "date": str(row.get('신규접수일', ''))
                        })

    # 당일 접수
    if '신규접수일' in df.columns:
        tdf = df[df['신규접수일'].astype(str).str.strip() == str(td)]
        for _, row in tdf.iterrows():
            alerts["info"].append({
                "type": "당일접수",
                "customer": str(row.get('고객명', '')),
                "customer_no": str(row.get('고객번호', '')),
                "manager": str(row.get('담당자', '')),
                "days": 0,
                "detail": "오늘 신규 접수",
                "date": str(td)
            })

    # 해지 위험
    if '관리구분' in df.columns:
        cdf = df[df['관리구분'].astype(str).str.strip().isin(['해지', '해지예상', '취소'])]
        for _, row in cdf.iterrows():
            alerts["warning"].append({
                "type": "해지위험",
                "customer": str(row.get('고객명', '')),
                "customer_no": str(row.get('고객번호', '')),
                "manager": str(row.get('담당자', '')),
                "days": 0,
                "detail": f"관리구분: {row.get('관리구분', '')}",
                "date": str(row.get('신규접수일', ''))
            })

    return alerts
