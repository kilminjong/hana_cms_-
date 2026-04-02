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
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

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


def get_drive_service():
    """구글 드라이브 API 서비스 객체 반환"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return build('drive', 'v3', credentials=creds)
    except:
        pass
    if os.path.exists('service_account.json'):
        try:
            creds = Credentials.from_service_account_file('service_account.json', scopes=scopes)
            return build('drive', 'v3', credentials=creds)
        except:
            pass
    return None


def upload_bg_image_to_drive(username, image_bytes, ext):
    """배경 이미지를 구글 드라이브에 업로드하고 공개 URL 반환"""
    try:
        service = get_drive_service()
        if not service:
            return None

        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png", "webp": "image/webp"}
        mime_type = mime_map.get(ext.lower(), "image/jpeg")
        filename = f"hana_bg_{username}.{ext}"

        # 기존 파일 검색 후 삭제 (덮어쓰기 효과)
        try:
            results = service.files().list(
                q=f"name='{filename}' and trashed=false",
                fields="files(id)"
            ).execute()
            for f in results.get('files', []):
                service.files().delete(fileId=f['id']).execute()
        except:
            pass

        # 업로드
        media = MediaIoBaseUpload(
            io.BytesIO(image_bytes),
            mimetype=mime_type,
            resumable=True
        )
        file_meta = {'name': filename, 'parents': []}
        uploaded = service.files().create(
            body=file_meta,
            media_body=media,
            fields='id'
        ).execute()

        file_id = uploaded.get('id')
        if not file_id:
            return None

        # 공개 권한 설정
        service.permissions().create(
            fileId=file_id,
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()

        # 직접 접근 URL 반환
        url = f"https://drive.google.com/uc?export=view&id={file_id}"
        return url
    except Exception as e:
        return None


def delete_bg_image_from_drive(username):
    """드라이브에서 해당 유저의 배경 이미지 삭제"""
    try:
        service = get_drive_service()
        if not service:
            return
        for ext in ['jpg', 'jpeg', 'png', 'webp']:
            filename = f"hana_bg_{username}.{ext}"
            results = service.files().list(
                q=f"name='{filename}' and trashed=false",
                fields="files(id)"
            ).execute()
            for f in results.get('files', []):
                service.files().delete(fileId=f['id']).execute()
    except:
        pass


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


@st.cache_data(ttl=300, show_spinner=False)
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
        def _norm_col(h):
            h = str(h).strip()
            if h == "고객사명": h = "고객명"
            if "개설" in h and "이행" in h: h = "개설이행일"
            if "서버" in h and ("위치" in h or "pc" in h.lower()): h = "서버위치"
            if "스케줄" in h and "사용" in h: h = "스케줄사용여부"
            if h.replace(" ","") in ("ERPDB","ERP_DB","ERP/DB"): h = "ERPDB"
            if "ERP" in h and "회사" in h: h = "ERP회사"
            if "ERP" in h and "종류" in h: h = "ERP종류"
            if "고객" in h and "담당" in h and "연락" not in h: h = "고객담당자"
            if "담당" in h and "부서" in h: h = "담당부서"
            if "담당" in h and "연락" in h: h = "담당연락처"
            return h

        for h in headers:
            h = _norm_col(h)
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

def _norm_header(h):
    """구글시트 헤더 정규화 — 특수문자/공백/변형 모두 처리"""
    h = str(h).strip()
    if "개설" in h and "이행" in h: h = "개설이행일"
    if "서버" in h and ("위치" in h or "pc" in h.lower()): h = "서버위치"
    if "스케줄" in h and "사용" in h: h = "스케줄사용여부"
    if h.replace(" ","") in ("ERPDB","ERP_DB","ERP/DB"): h = "ERPDB"
    if "ERP" in h and "회사" in h: h = "ERP회사"
    if "ERP" in h and "종류" in h: h = "ERP종류"
    if "고객" in h and "담당" in h and "연락" not in h: h = "고객담당자"
    if "담당" in h and "부서" in h: h = "담당부서"
    if "담당" in h and "연락" in h: h = "담당연락처"
    return h.replace(" ", "")


def _build_row_by_headers(hr, dm):
    """헤더 순서대로 dm 값을 채워 반환 — 정확 일치 우선"""
    ch = [_norm_header(h) for h in hr]
    nr = [""] * len(hr)
    for i, cn in enumerate(ch):
        # ★ 정확 일치 우선 (부분 포함 방지 — 예: '담당자'가 '고객담당자'에 잘못 매핑되는 버그 수정)
        if cn in dm:
            nr[i] = str(dm[cn])
        else:
            # fallback: 부분 포함 (고객명, 신규접수일 등 구글시트 변형 대비)
            for k, v in dm.items():
                if k in cn:
                    nr[i] = str(v)
                    break
    return nr


def _sync_gsheet_update_bg(mode, dm):
    sheet, msg = get_data_sheet_safe()
    if not sheet:
        return
    try:
        headers = sheet.row_values(DATA_HEADER_ROW)
        ch = [_norm_header(h) for h in headers]
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
    """구글시트에서 사용자 목록 조회 + 세션 캐시 병합"""
    cached = {}
    try:
        cached = st.session_state.get('cached_users', {})
    except:
        pass
    try:
        cl = get_client()
        if not cl:
            return cached
        r = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_USERS).get_all_records()
        sheet_users = {
            str(x['username']): {
                "password": str(x['password']),
                "role": str(x.get('role', 'user')).strip() or 'user',
                "bg_color": str(x.get('bg_color', '')).strip()
            } for x in r
        }
        merged = {**cached, **sheet_users}
        return merged
    except:
        return cached


def _get_drive_client():
    """구글 드라이브 클라이언트 반환"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        try:
            creds_dict = dict(st.secrets["gcp_service_account"])
            from google.oauth2.service_account import Credentials as Creds
            creds = Creds.from_service_account_info(creds_dict, scopes=scopes)
        except:
            import os
            if os.path.exists('service_account.json'):
                from google.oauth2.service_account import Credentials as Creds
                creds = Creds.from_service_account_file('service_account.json', scopes=scopes)
            else:
                return None
        from googleapiclient.discovery import build
        return build('drive', 'v3', credentials=creds)
    except:
        return None


def upload_bg_to_drive(username, image_bytes, mime_type, filename):
    """이미지를 구글 드라이브에 업로드하고 공개 URL 반환"""
    try:
        from googleapiclient.http import MediaIoBaseUpload
        import io
        drive = _get_drive_client()
        if not drive:
            return None
        # 폴더 찾기 또는 생성
        folder_name = "hana_cms_backgrounds"
        res = drive.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id)"
        ).execute()
        if res.get('files'):
            folder_id = res['files'][0]['id']
        else:
            folder_meta = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
            folder = drive.files().create(body=folder_meta, fields='id').execute()
            folder_id = folder['id']
        # 기존 유저 배경 이미지 삭제
        old_res = drive.files().list(
            q=f"name='{username}_bg' and '{folder_id}' in parents and trashed=false",
            fields="files(id)"
        ).execute()
        for f in old_res.get('files', []):
            drive.files().delete(fileId=f['id']).execute()
        # 새 이미지 업로드
        file_meta = {'name': f'{username}_bg', 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype=mime_type)
        uploaded = drive.files().create(body=file_meta, media_body=media, fields='id').execute()
        file_id = uploaded['id']
        # 공개 접근 권한 설정
        drive.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        # 직접 이미지 URL 반환
        img_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        return img_url
    except Exception as e:
        return None


def save_user_bg(username, bg_value):
    """사용자 배경 설정을 구글시트 users 시트에 저장"""
    val_to_save = str(bg_value)
    # base64 raw 이미지는 저장 불가 (크기 초과) — URL만 저장
    if val_to_save.startswith("data:image"):
        return False
    try:
        cl = get_client()
        if not cl:
            return False
        ws = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_USERS)
        # RAW로 헤더 읽기
        all_vals = ws.get_all_values()
        if not all_vals:
            return False
        headers = [str(h).strip() for h in all_vals[0]]
        # bg_color 컬럼 없으면 추가
        if 'bg_color' not in headers:
            new_col = len(headers) + 1
            ws.update_cell(1, new_col, 'bg_color')
            headers.append('bg_color')
        bg_col_idx = headers.index('bg_color') + 1  # 1-based
        user_col_idx = headers.index('username') if 'username' in headers else 0
        # 해당 유저 행 찾기
        for i, row in enumerate(all_vals[1:], start=2):
            if len(row) > user_col_idx and str(row[user_col_idx]).strip() == str(username).strip():
                cell_addr = f"{col_to_letter(bg_col_idx)}{i}"
                ws.update(cell_addr, [[val_to_save]], value_input_option='RAW')
                return True
        return False
    except Exception as e:
        import streamlit as _st
        try:
            _st.session_state['_bg_save_error'] = str(e)
        except:
            pass
        return False


def get_user_bg(username):
    """구글시트에서 특정 사용자의 배경색 직접 조회 (RAW, 캐시 무시)"""
    try:
        cl = get_client()
        if not cl:
            return ""
        ws = cl.open_by_url(GOOGLE_SHEET_URL).worksheet(SHEET_USERS)
        # get_all_values로 RAW 값 읽기 (하이퍼링크 자동변환 방지)
        all_values = ws.get_all_values()
        if not all_values:
            return ""
        headers = [str(h).strip() for h in all_values[0]]
        if 'username' not in headers or 'bg_color' not in headers:
            return ""
        user_col = headers.index('username')
        bg_col = headers.index('bg_color')
        for row in all_values[1:]:
            if len(row) > user_col and str(row[user_col]).strip() == str(username).strip():
                val = str(row[bg_col]).strip() if len(row) > bg_col else ""
                return val
        return ""
    except:
        return ""


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
