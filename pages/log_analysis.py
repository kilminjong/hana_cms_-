# -*- coding: utf-8 -*-
"""로그 분석 페이지"""
import streamlit as st
import pandas as pd
import re
from collections import Counter
import plotly.express as px
from style import inject_page_css, page_wrapper_open, page_wrapper_close, render_section_title, render_page_header, render_kpi
from data import get_current_df

def render():
    inject_page_css("loganalysis"); page_wrapper_open("loganalysis")
    render_page_header("CMS 스케줄러 로그 분석기", "로그 파일(.log, .txt)을 업로드하면 오류를 자동 진단합니다.")
    
    up_log = st.file_uploader("로그 파일 업로드", type=['txt','log'], key="log_up")
    
    if up_log:
        try:
            raw = up_log.read()
            # 인코딩 자동 감지
            for enc in ['utf-8', 'euc-kr', 'cp949', 'latin-1']:
                try:
                    content = raw.decode(enc); break
                except: continue
            else:
                content = raw.decode('utf-8', errors='ignore')
    
            all_lines = content.split('\n')
            total_lines = len(all_lines)
    
            import re
            from collections import Counter
    
            # ── 1. 오류 패턴 감지 ──
            CMS_ERROR_PATTERNS = {
                "WAIT_TIMEOUT": {
                    "keywords": ["WAIT_TIMEOUT"],
                    "severity": "info",
                    "desc": "세션 타이머 만료 (정상 주기 갱신)",
                    "action": "정상 동작입니다. 스케줄러가 주기적으로 세션을 갱신하는 과정에서 발생합니다."
                },
                "CONNECTION_LOST": {
                    "keywords": ["hsDisconnected", "Disconnected", "Connection refused"],
                    "severity": "warning",
                    "desc": "서버 연결 끊김",
                    "action": "CMS Agent 서비스 상태를 확인하세요. 방화벽 또는 네트워크 이슈일 수 있습니다."
                },
                "SOCKET_ERROR": {
                    "keywords": ["EIdSocketError", "Socket Error", "10054", "10053"],
                    "severity": "error",
                    "desc": "소켓 통신 오류 (연결 강제 종료)",
                    "action": "원격 서버가 연결을 강제 종료했습니다. 서버 상태, 방화벽, 네트워크 점검이 필요합니다. 10054=원격서버 강제종료, 10053=로컬 네트워크 끊김."
                },
                "CONNECTION_CLOSED": {
                    "keywords": ["EIdConnClosedGracefully", "Connection Closed Gracefully"],
                    "severity": "warning",
                    "desc": "연결 정상 종료 (Gracefully Closed)",
                    "action": "서버가 정상적으로 연결을 끊었습니다. 빈번하면 KeepAlive 설정을 점검하세요."
                },
                "JSON_SYNTAX_ERROR": {
                    "keywords": ["TJSONSyntaxError", "Unexpected token ILLEGAL"],
                    "severity": "error",
                    "desc": "JSON 파싱 오류 (잘못된 응답 데이터)",
                    "action": "CMS Agent 서버 응답이 올바른 JSON 형식이 아닙니다. 서버 로그를 확인하세요. 서버 재시작으로 해결되는 경우가 많습니다."
                },
                "JSON_PARSE_ERROR": {
                    "keywords": ["EJSONParseException", "not a valid JSON"],
                    "severity": "error",
                    "desc": "JSON 변환 실패 (응답 데이터 손상)",
                    "action": "서버 응답을 JSON으로 변환할 수 없습니다. 네트워크 불안정으로 데이터가 잘린 경우 발생합니다. 재시도하거나 서버 로그를 확인하세요."
                },
                "DB_NULL_ERROR": {
                    "keywords": ["does not allow nulls", "Cannot insert the value NULL"],
                    "severity": "error",
                    "desc": "DB NULL 제약조건 위반",
                    "action": "필수 컬럼에 NULL 값을 넣으려 했습니다. 해당 테이블의 컬럼 설정과 데이터 입력값을 확인하세요."
                },
                "DB_GENERAL_ERROR": {
                    "keywords": ["EDatabaseError", "EMSSQLNativeException", "SQL Server]"],
                    "severity": "error",
                    "desc": "데이터베이스 오류",
                    "action": "DB 쿼리 실행 중 오류가 발생했습니다. SQL 구문, 테이블 존재 여부, DB 연결 상태를 확인하세요."
                },
                "FILE_OPEN_ERROR": {
                    "keywords": ["EFOpenError", "Cannot open file"],
                    "severity": "error",
                    "desc": "파일 열기 실패",
                    "action": "설정 파일(FIF.ini 등)을 찾을 수 없거나 접근 권한이 없습니다. 파일 경로와 권한을 확인하세요. CMS 재설치가 필요할 수 있습니다."
                },
                "ACCESS_VIOLATION": {
                    "keywords": ["EAccessViolation", "Access violation at address"],
                    "severity": "critical",
                    "desc": "메모리 접근 위반 (프로그램 크래시)",
                    "action": "프로그램이 잘못된 메모리에 접근했습니다. CMS Agent 재시작이 필요하며, 지속 발생 시 개발팀 문의가 필요합니다."
                },
                "FIELD_NOT_FOUND": {
                    "keywords": ["not found", "Field '"],
                    "severity": "warning",
                    "desc": "DB 필드 정보 누락",
                    "action": "테이블 스키마 정보를 가져오는 중 필드를 찾지 못했습니다. DB 버전 호환성 또는 테이블 구조 변경을 확인하세요."
                },
                "SCHEDULE_ERROR": {
                    "keywords": ["ScheduleRun error", "Schedule_Exception"],
                    "severity": "error",
                    "desc": "스케줄러 실행 오류",
                    "action": "예약 작업 실행 중 오류가 발생했습니다. 스케줄 설정과 대상 작업의 상태를 확인하세요."
                },
                "AUTH_FAILURE": {
                    "keywords": ["401 Unauthorized", "Access denied", "Login failed"],
                    "severity": "error",
                    "desc": "인증 실패",
                    "action": "OAuth 토큰 만료 또는 계정 정보 오류입니다. 서비스 재시작 또는 인증정보를 확인하세요."
                },
                "MEMORY_WARNING": {
                    "keywords": ["uFrame.SQL.Utility/BEF/ERROR", "uFrame.SQL.Utility/AFT/ERROR"],
                    "severity": "info",
                    "desc": "메모리 사용량 로깅 (ERROR 표기지만 정상)",
                    "action": "메모리 뷰어 로그입니다. 메모리가 지속 증가하면 서비스 재시작을 권장합니다."
                },
                "REQUEST_FAIL": {
                    "keywords": ["Result : False", "Result [False]"],
                    "severity": "error",
                    "desc": "REST API 요청 실패",
                    "action": "CMS Agent 서버 응답이 실패했습니다. 서버 상태 및 API 엔드포인트를 확인하세요."
                },
                "SERVER_ERROR": {
                    "keywords": ["State Code : 5", "State Code : 4", "500 Internal"],
                    "severity": "error",
                    "desc": "서버 내부 오류 (HTTP 5xx/4xx)",
                    "action": "CMS Agent 서버에서 오류가 발생했습니다. 서버 로그를 함께 확인하세요."
                },
            }
    
            detected = {}  # {pattern_name: [lines...]}
            for i, line in enumerate(all_lines):
                for pname, pinfo in CMS_ERROR_PATTERNS.items():
                    for kw in pinfo["keywords"]:
                        if kw in line:
                            if pname not in detected: detected[pname] = []
                            detected[pname].append({"line": i+1, "text": line.strip()[:200]})
                            break
    
            # ── 2. 시간대 추출 ──
            time_pattern = re.findall(r'(\d{2}:\d{2}):\d{2}:\d{3}', content)
            time_dist = Counter(time_pattern)
    
            # ── 3. 메모리 추이 ──
            mem_vals = re.findall(r'(\d+\.\d+)\s*MB', content)
            mem_floats = [float(m) for m in mem_vals]
    
            # ── 4. 모듈별 로그 수 ──
            module_pattern = re.findall(r'\d+ / \d{2}:\d{2}:\d{2}:\d{3} (\w+)/', content)
            module_counts = Counter(module_pattern).most_common(10)
    
            # ── 5. 통신 결과 ──
            results_true = content.count('Result : True') + content.count('Result [True]')
            results_false = content.count('Result : False') + content.count('Result [False]')
    
            # ══ 결과 렌더링 ══
            # 파일 정보
            render_section_title("📁 파일 정보")
            fi1, fi2, fi3, fi4 = st.columns(4)
            with fi1: st.markdown(render_kpi("파일명", up_log.name, unit=""), unsafe_allow_html=True)
            with fi2: st.markdown(render_kpi("총 라인 수", f"{total_lines:,}"), unsafe_allow_html=True)
            with fi3: st.markdown(render_kpi("파일 크기", f"{len(raw)/1024:.1f}", unit="KB"), unsafe_allow_html=True)
            with fi4: st.markdown(render_kpi("통신 성공률", f"{round(results_true/(results_true+results_false)*100,1) if (results_true+results_false)>0 else 0}%", unit=""), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
    
            # 진단 결과 요약
            render_section_title("🔍 진단 결과")
            error_count = sum(len(v) for k, v in detected.items() if CMS_ERROR_PATTERNS[k]["severity"] in ["error","critical"])
            warn_count = sum(len(v) for k, v in detected.items() if CMS_ERROR_PATTERNS[k]["severity"] == "warning")
            info_count = sum(len(v) for k, v in detected.items() if CMS_ERROR_PATTERNS[k]["severity"] == "info")
    
            if error_count == 0 and warn_count == 0:
                st.success("✅ 정상 — 심각한 오류가 발견되지 않았습니다.")
            elif error_count > 0:
                st.error(f"🚨 오류 {error_count}건 감지! 아래 상세 내역을 확인하세요.")
            else:
                st.warning(f"⚠️ 경고 {warn_count}건 감지. 확인이 필요합니다.")
    
            # 감지된 패턴별 상세
            if detected:
                for pname, items in detected.items():
                    pinfo = CMS_ERROR_PATTERNS[pname]
                    sev = pinfo["severity"]
                    if sev == "critical": icon = "🔴"; color = "#dc2626"
                    elif sev == "error": icon = "🟠"; color = "#f59e0b"
                    elif sev == "warning": icon = "🟡"; color = "#eab308"
                    else: icon = "🔵"; color = "#008485"
    
                    with st.expander(f"{icon} {pinfo['desc']} — {len(items)}건", expanded=(sev in ["error","critical"])):
                        st.markdown(f"**원인:** {pinfo['desc']}")
                        st.markdown(f"**조치:** {pinfo['action']}")
                        st.markdown(f"**발생 건수:** `{len(items)}건`")
                        if len(items) <= 10:
                            for it in items:
                                st.code(f"Line {it['line']}: {it['text']}", language=None)
                        else:
                            for it in items[:5]:
                                st.code(f"Line {it['line']}: {it['text']}", language=None)
                            st.caption(f"... 외 {len(items)-5}건 더 있음")
    
            st.markdown("<br>", unsafe_allow_html=True)
    
            # 시간대별 로그 차트
            render_section_title("⏰ 시간대별 로그 분포")
            if time_dist:
                time_df = pd.DataFrame(sorted(time_dist.items()), columns=['시간','건수'])
                fig_t = px.bar(time_df, x='시간', y='건수', color_discrete_sequence=['#008485'])
                fig_t.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=250, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="")
                st.plotly_chart(fig_t, use_container_width=True)
            else:
                st.info("시간 정보를 추출할 수 없습니다.")
    
            # 메모리 추이
            if mem_floats:
                render_section_title("💾 메모리 사용량 추이")
                mem_c1, mem_c2, mem_c3 = st.columns(3)
                with mem_c1: st.markdown(render_kpi("최소", f"{min(mem_floats):.1f}", unit="MB"), unsafe_allow_html=True)
                with mem_c2: st.markdown(render_kpi("최대", f"{max(mem_floats):.1f}", unit="MB", color="var(--accent)", variant="accent"), unsafe_allow_html=True)
                with mem_c3: st.markdown(render_kpi("평균", f"{sum(mem_floats)/len(mem_floats):.1f}", unit="MB", color="var(--primary)", variant="success"), unsafe_allow_html=True)
                mem_df = pd.DataFrame({"순서": range(len(mem_floats)), "MB": mem_floats})
                fig_m = px.line(mem_df, x="순서", y="MB", color_discrete_sequence=['#008485'])
                fig_m.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=200, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="MB", showlegend=False)
                st.plotly_chart(fig_m, use_container_width=True)
    
            # 모듈별 로그
            if module_counts:
                render_section_title("📦 모듈별 로그 비율")
                mod_df = pd.DataFrame(module_counts, columns=['모듈','건수'])
                fig_mod = px.bar(mod_df, x='건수', y='모듈', orientation='h', color_discrete_sequence=['#008485'])
                fig_mod.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=max(len(module_counts)*35, 200), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="", yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_mod, use_container_width=True)
    
            # 원본 로그 미리보기
            render_section_title("📄 원본 로그 미리보기")
            st.text_area("", content[:3000], height=200, disabled=True)
    
        except Exception as e:
            import traceback; st.error(f"분석 오류: {str(e)}"); st.code(traceback.format_exc())
    else:
        st.markdown("""<div style="text-align:center; padding:60px 20px; color:#8c95a6;">
            <div style="font-size:48px; margin-bottom:16px;">📂</div>
            <div style="font-size:16px; font-weight:600;">로그 파일을 업로드하면 자동 분석이 시작됩니다</div>
            <div style="font-size:13px; margin-top:8px;">.log 또는 .txt 파일을 지원합니다</div>
        </div>""", unsafe_allow_html=True)
    
    page_wrapper_close()
    page_wrapper_close()
