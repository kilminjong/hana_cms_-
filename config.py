# -*- coding: utf-8 -*-
"""
설정값 모듈
- 구글시트 URL, 인증코드, 상수값 등을 여기서 관리합니다.
- 수정이 필요한 설정값은 이 파일만 고치면 됩니다.
"""

import sqlite3

# ── 회사/인증 코드 ──
COMPANY_CODE = "333546"
ADMIN_CODE = "ADMIN777"

# ── 세션 설정 ──
SESSION_TIMEOUT_SEC = 3600
ADMIN_USERS = []

# ── 메뉴 설정 ──
ALL_MENUS = [
    ("▪", "메인화면"),
    ("▪", "고객 관리"),
    ("▪", "알림센터"),
    ("▪", "나의 실적"),
    ("▪", "CMS 실적 확인"),
    ("▪", "종합 보고서"),
    ("▪", "로그 분석"),
    ("▪", "시스템 로그"),
    ("▪", "사용자 관리"),
]
ADMIN_ONLY_MENUS = ["시스템 로그", "사용자 관리"]
DEFAULT_USER_MENUS = ["메인화면", "고객 관리", "알림센터", "나의 실적", "CMS 실적 확인", "종합 보고서"]
MENU_SETTINGS_KEY = "__menu_settings__"

# ── 구글시트 설정 ──
SHEET_USERS = "users"
SHEET_DATA = "고객원장"
SHEET_MEMOS = "memos"
SHEET_LOGS = "logs"
SHEET_TIMELINE = "timeline"
DATA_HEADER_ROW = 3

HANA_LOGO_URL = "logo.png"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1btxxNGPw-SLEnhvWSyyDbSHf-SniXZDS4IJit3wiqXE/edit?gid=0#gid=0"

# ── BMS 설정 ──
BMS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1a0UJx9cQfuxEFciUTHq_2uswwvZ3Hz_Ha6in3SZlWfo/edit"
BMS_SHEET_TAB = "기준표 및 작성"
BMS_CELL_MAP = {
    "이성환": {"개설": "J6", "연계": "J7", "방문": "J8"},
    "임인지": {"개설": "K6", "연계": "K7", "방문": "K8"},
    "전준수": {"개설": "L6", "연계": "L7", "방문": "L8"},
    "이수현": {"개설": "M6", "연계": "M7", "방문": "M8"},
    "길민종": {"개설": "N6", "연계": "N7", "방문": "N8"},
    "하성춘": {"개설": "O6", "연계": "O7", "방문": "O8"},
}

# ── 알림 설정 ──
REMINDER_DAYS_PENDING = 7
REMINDER_DAYS_LINKAGE = 14

# ── SQLite (세션 저장용) ──
import os as _os
import tempfile as _tempfile
_db_dir = _os.path.dirname(_os.path.abspath(__file__))
if not _os.access(_db_dir, _os.W_OK):
    _db_dir = _tempfile.gettempdir()
DB_FILE = _os.path.join(_db_dir, "hana_cache.db")
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id TEXT, expiry REAL)")
conn.commit()
