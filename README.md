<div align="center">

# 🐢 넙죽이 — KAIST AI 학과 안내 RAG 챗봇

**흩어진 KAIST AI 학과 정보를, 출처와 함께 대화로 답하는 웹 애플리케이션**

[![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django_6.x-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)](https://developer.mozilla.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)](https://platform.openai.com/)
[![Chroma](https://img.shields.io/badge/Chroma-FF6F61?style=flat&logo=databricks&logoColor=white)](https://www.trychroma.com/)
[![MySQL](https://img.shields.io/badge/MySQL_8.x-4479A1?style=flat&logo=mysql&logoColor=white)](https://www.mysql.com/)

SKN28 4기 · 2팀 · 4차 프로젝트 · 발표일 2026-06-26

</div>

---

## 📑 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [팀 소개](#2-팀-소개)
3. [기술 스택](#3-기술-스택)
4. [요구사항 정의서](#4-요구사항-정의서)
5. [화면설계서](#5-화면설계서)
6. [주요 기능](#6-주요-기능)
7. [테스트 계획 및 결과](#7-테스트-계획-및-결과)
8. [로컬 실행 방법](#8-로컬-실행-방법)
9. [프로젝트 산출물](#9-프로젝트-산출물)

---

## 1. 프로젝트 소개

> KAIST AI 관련 학과(AI컴퓨팅학과 · AI시스템학과 · AX학과 · AI미래학과)의 입학·교과목·교수진·사무실 정보는 여러 공식 페이지와 PDF에 흩어져 있어 한 번에 찾기 어렵습니다.

**넙죽이**는 흩어진 내·외부 문서를 수집·전처리하여 **SQL(정형) + Vector(비정형) 하이브리드 검색**과 **LLM RAG 파이프라인**으로 연동하고, 사용자의 자연어 질문에 **근거(출처)와 함께** 답변하는 웹 애플리케이션입니다. 단순 질의응답을 넘어 **대화 기록·답변 피드백·운영 통계·보완 Q&A 게시판**까지 서비스 운영 관점의 기능을 제공합니다.

**핵심 가치**
- 🔎 **출처 기반 답변** — 모든 답변에 학과·문서·URL 출처 카드를 함께 제시
- 🧭 **하이브리드 검색** — 구조화 데이터(MySQL)와 의미 검색(Chroma)을 결합
- 💬 **대화형 경험** — 마스코트 '넙죽이'와 세션 기반 대화, 답변 피드백
- 🗂️ **운영 기능** — 게시판/문의, 답변 상태 관리, 수집 데이터 통계 대시보드

---

## 2. 팀 소개

| <div align="center">김성재</div> | <div align="center">손지은</div> | <div align="center">신혜지</div> | <div align="center">심기성</div> |
|:---:|:---:|:---:|:---:|
| [@hippo2coding](https://github.com/hippo2coding) | [@yjson616](https://github.com/yjson616) | [@HyejiShin-20](https://github.com/HyejiShin-20) | [@sim2084](https://github.com/sim2084) |
|  |  |  |  |

---

## 3. 기술 스택

| 분류 | 기술 |
|---|---|
| **Frontend** | ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white) ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black) |
| **Backend** | ![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat&logo=python&logoColor=white) ![Django](https://img.shields.io/badge/Django_6.x-092E20?style=flat&logo=django&logoColor=white) |
| **AI / RAG** | ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat&logo=langchain&logoColor=white) ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white) ![Chroma](https://img.shields.io/badge/Chroma-FF6F61?style=flat&logoColor=white) |
| **Database** | ![MySQL](https://img.shields.io/badge/MySQL_8.x-4479A1?style=flat&logo=mysql&logoColor=white) ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white) |
| **Data** | ![pandas](https://img.shields.io/badge/pandas-150458?style=flat&logo=pandas&logoColor=white) ![PyMuPDF](https://img.shields.io/badge/PyMuPDF-EE3322?style=flat&logoColor=white) |
| **Tooling** | ![uv](https://img.shields.io/badge/uv-DE5FE9?style=flat&logo=astral&logoColor=white) ![Git](https://img.shields.io/badge/Git-F05032?style=flat&logo=git&logoColor=white) ![VSCode](https://img.shields.io/badge/VS_Code-007ACC?style=flat&logo=visualstudiocode&logoColor=white) |

---

## 4. 요구사항 정의서

전체 명세는 **[docs/요구사항정의서.md](docs/요구사항정의서.md)** (+ PDF). 핵심 요구사항 요약:

| 구분 | ID | 요구사항 | 유형 |
|---|---|---|---|
| 인증 | AUTH | 회원가입·로그인·로그아웃, 세션 기반 인증 | 기능 |
| 채팅 | CHAT | 자연어 질문 → 출처 포함 RAG 답변, 대화 세션·기록 | 기능 |
| 검색 | RAG | SQL(정형)+Vector(비정형) 하이브리드 검색, 범위 밖/되묻기 처리 | 기능 |
| 피드백 | FB | 답변 👍/👎 피드백, 실패 질문 로그 | 기능 |
| 커뮤니티 | COMM | 보완 Q&A 게시판·문의, 댓글, 공지/비공개/차단 | 기능 |
| 운영 | ADMIN | 수집 데이터 통계 대시보드, 문의 답변 상태 관리 | 기능 |
| 비기능 | NFR | 응답 안정성, 입력 검증, 보안(CSRF·세션), 로컬·클라우드 실행 | 비기능 |

---

## 5. 화면설계서

실제 화면에 번호 마커(①②③)를 표기하고, 번호별 화면 요소·동작을 설명합니다. 화면별 상세 설계는 `docs/frontend_wireframes_*.md` 참고.

### 5.1 로그인 / 회원가입
| 로그인 | 회원가입 |
|:---:|:---:|
| ![로그인](docs/images/screens/annotated/login.png) | ![회원가입](docs/images/screens/annotated/signup.png) |

이메일/비밀번호 인증, 비밀번호 표시 토글, 실데이터 통계 노출. 상세: [login_signup](docs/frontend_wireframes_login_signup.md)

### 5.2 채팅 (메인 기능)
![채팅](docs/images/screens/annotated/chat.png)

세션 레일, 질문 입력, 넙죽이 답변 + 출처 카드(학과·문서·URL), 피드백/복사/재생성, 마스코트 상태 전이. 상세: [chat_main](docs/frontend_wireframes_chat_main.md)

### 5.3 게시판 (커뮤니티)
| 게시판 목록 | 게시글 상세 |
|:---:|:---:|
| ![게시판 목록](docs/images/screens/annotated/board_list.png) | ![게시글 상세](docs/images/screens/annotated/board_detail.png) |

카테고리·검색·공지 고정, 글 작성/상세, 댓글·대댓글, 작성자 수정·삭제 권한. 상세: [board](docs/frontend_wireframes_board.md)

### 5.4 문의 / 관리자 통계
| 문의 게시판 | 수집 데이터 현황(관리자) |
|:---:|:---:|
| ![문의](docs/images/screens/annotated/inquiry_list.png) | ![관리자](docs/images/screens/annotated/admin.png) |

문의 상태(대기/처리중/완료)·비공개·운영자 답변, 관리자 수집 통계 대시보드(차트·학과별 표). 상세: [inquiry](docs/frontend_wireframes_inquiry.md) · [admin_dashboard](docs/frontend_wireframes_admin_dashboard.md)

---

## 6. 주요 기능

| 기능 | 설명 |
|---|---|
| 🔐 **인증** | 회원가입·로그인·로그아웃, 세션/CSRF 보안, 본인 글 관리 권한 |
| 💬 **RAG 채팅** | 질문→하이브리드 검색→출처 포함 답변, 세션별 대화 기록, 되묻기(clarify)/범위밖(blocked) 처리 |
| 📚 **출처 카드** | 답변 근거를 학과·문서명·URL로 제시, 클릭 시 원문 이동 |
| 📝 **게시판** | 학사 보완 Q&A — 카테고리·검색·공지·댓글, 작성자/관리자 권한 |
| 📨 **문의** | 운영자 문의 — 유형·비공개·답변 상태(대기/처리중/완료) |
| 📊 **관리자 통계** | 수집 데이터 현황(단과대학·학과·교과목·교수), 차트·학과별 표 |

---

## 7. 테스트 계획 및 결과

로컬 실행 환경(Django + MySQL `kaist_ai`)에서 핵심 기능을 End-to-End로 검증했습니다.

**요약**

| 총 항목 | ✅ Pass | ❌ Fail | 비고 |
|:---:|:---:|:---:|---|
| 9 | 9 | 0 | 정상 흐름 + 예외 처리 검증 |

**상세 결과**

| ID | 항목 | 방법 | 기대 결과 | 결과 |
|---|---|---|---|---|
| T-01 | 페이지 라우트 | `/login` `/signup` `/chat` `/board` `/inquiry` `/admin-stats` 응답 | 200(관리자 302 리다이렉트) | ✅ |
| T-02 | 정적 자산 | community.css·js, app.js, chat.js 로드 | 200 | ✅ |
| T-03 | 회원가입 | `POST /api/auth/signup` | 201 + 세션 로그인 | ✅ |
| T-04 | 로그인 상태 | `GET /api/auth/me` | `authenticated: true` | ✅ |
| T-05 | 게시글 작성 | `POST /api/community/posts` (CSRF) | 201, DB 저장 | ✅ |
| T-06 | 목록 반영 | `GET /api/community/posts` | 작성 글 count 반영 | ✅ |
| T-07 | DB 연동 | MySQL `kaist_ai` 마이그레이션·조회 | 22개 수집 테이블 + 앱 테이블 | ✅ |
| T-08 | 예외 — 빈 입력 | 카테고리/제목/본문 누락 | 400 + 안내 메시지 | ✅ |
| T-09 | 예외 — RAG 불가 | 엔진/키 미구성 시 채팅 | FALLBACK 안내(서버 무중단) | ✅ |

> 발견/개선: ① OAuth(Google·KAIST SSO)는 시연용 버튼으로 미동작 — 실연동 예정. ② Chroma 벡터 인덱스 미구축 시 채팅은 폴백 응답 — 인덱스 빌드 후 정식 답변. (상세 빌드: `scripts/data/build_vectorstore.py`)

---

## 8. 로컬 실행 방법

> 요구: Python 3.12, MySQL 8.x, (선택) OpenAI API 키

```bash
# 1) 가상환경 + 의존성
uv venv && uv pip install -r requirements.txt

# 2) 환경변수 — .env 작성
#   KAIST_MYSQL_USER / KAIST_MYSQL_PASSWORD / KAIST_MYSQL_DATABASE=kaist_ai
#   OPENAI_API_KEY=sk-...
#   (MySQL 없이 빠르게: DJANGO_USE_SQLITE=true)

# 3) DB 마이그레이션
python manage.py migrate

# 4) 서버 실행
python manage.py runserver 127.0.0.1:8000
```

브라우저에서 **http://127.0.0.1:8000/login/** 접속.
데이터 적재(크롤링 데이터 → MySQL)는 **[docs/sql_README.md](docs/sql_README.md)** / `scripts/sql/` 참고.

---

## 9. 프로젝트 산출물

| 산출물 | 위치 |
|---|---|
| 요구사항 정의서 | [docs/요구사항정의서.md](docs/요구사항정의서.md) · PDF |
| 화면설계서 | [docs/frontend_wireframes_*.md](docs/) + `docs/images/screens/` |
| ERD | [docs/sql_ERD.md](docs/sql_ERD.md) |
| LLM 연동 웹 앱 | `src/kaist_rag/` (Django + RAG) |
| 데이터 적재 가이드 | [docs/sql_README.md](docs/sql_README.md) |

<div align="center">

**SKN28 4기 2팀** · 김성재 · 손지은 · 신혜지 · 심기성

</div>
