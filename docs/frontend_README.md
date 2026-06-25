# 넙죽이 · KAIST 학과 안내 RAG 챗봇 — 프론트엔드

SKN28 4th · 2TEAM · 4차 프로젝트  |  팀원: 김성재, 손지은, 신혜지, 심기성  |  발표: 2026-06-26

KAIST AI대학·자연과학대학·생명과학기술대학의 교과목·교수진·입학·세미나 정보를 자연어로 질의하고,
출처와 함께 답변받는 RAG 챗봇 웹 애플리케이션의 **프론트엔드 프로토타입**입니다.
마스코트 "넙죽이"가 대화 상태(대기/검색/완료/경고)에 따라 반응합니다.

## 바로 보기 (프로토타입)

    frontend/prototype.html  ← 브라우저로 그냥 열면 동작합니다 (오프라인 가능)

하단 가운데 "화면" 바로 로그인 / 회원가입 / 채팅 / 관리자 화면을 전환할 수 있습니다.
상단 툴바의 Tweaks 토글로 색상·테마·마스코트 크기·밀도를 실시간으로 바꿀 수 있습니다.

## 폴더 구조

    frontend/
    ├── prototype.html              # 단일 파일로 동작하는 클릭 가능한 프로토타입
    ├── README.md
    ├── templates/                  # Django 템플릿 (base 상속 + 라우트별 부트)
    │   ├── base.html
    │   ├── accounts/  login.html · signup.html
    │   ├── chat/      chat.html · session_list.html · partials/*
    │   ├── dashboard/ admin_stats.html
    │   └── errors/    400.html · 403.html · 500.html
    ├── static/
    │   ├── css/   variables · base · mascot · chat · auth · dashboard · tweaks
    │   ├── js/    data · kb_data · search · mascot · chat · auth · dashboard · errors · app
    │   └── images/ logo/kaist_logo.png · mascot/nubzuki_*.png
    └── wireframes/  chat_main.md · login_signup.md · admin_dashboard.md · board.md · inquiry.md

## 동작 방식

- **데이터**: static/js/kb_data.js 에 실제 수집 데이터가 들어 있습니다
  (AI대학·자연과학대학·생명과학기술대학, 2026-06-17 크롤링).
- **검색(RAG)**: static/js/search.js 가 질문에서 학과·의도(교과목/교수/세미나/입학)를 식별하고
  kb_data 에서 관련 레코드를 검색합니다. (SRS의 FR-A 질문분석 / FR-B 검색에 대응)
- **답변 생성**: 검색된 레코드를 컨텍스트로 LLM(window.claude.complete)이 한국어 답변을 생성하고,
  LLM이 없으면 검색 결과를 그대로 렌더링합니다. (FR-C)
- **출처**: 각 답변에 학과·문서명·수집일·URL이 붙고, 클릭하면 원문이 새 탭으로 열립니다. (FR-C4)
- **경고/범위**: 수집되지 않은 학과·외부 질문은 경고 답변으로 안내합니다. (FR-A4 / FR-C5 / FR-D)
- **마스코트 상태**: idle / thinking / source / done / warning (static/js/mascot.js).

## 데이터는 모두 실데이터입니다

관리자 화면과 로그인 통계의 모든 수치(단과대학 3 · 학과 15 · 교과목 908 · 교수·연구진 607 등)는
kb_data.js 의 실제 레코드에서 집계됩니다. 임의로 만든 가짜 수치(누적 질문수·만족도 등)는 사용하지 않았습니다.

## Django 연동

1. static/ 를 STATICFILES_DIRS 에, templates/ 를 TEMPLATES DIRS 에 등록합니다.
2. base.html 은 window.ASSET_BASE 를 STATIC_URL 기준으로 설정합니다. STATIC_URL 이 /static/ 가 아니면
   base.html 의 ASSET_BASE 줄을 맞춰 주세요.
3. URL 매핑 예시 (urls.py → TemplateView):

    /            → accounts/login.html
    /signup/     → accounts/signup.html
    /chat/       → chat/chat.html
    /admin-stats/→ dashboard/admin_stats.html

   각 페이지 템플릿은 window.__ROUTE 를 설정해 해당 화면으로 부팅합니다.
4. partials/ 는 백엔드에서 서버 렌더링할 때 참고할 마크업입니다. (실시간 UI는 chat.js가 동일 구조 생성)
5. 실제 답변은 Django 백엔드의 RAG 엔진(SQL/Vector)으로 교체하고, 프론트는 /api 응답을 렌더링하면 됩니다.

## 로그인 / 소셜

- **Google 로그인**: 무료입니다(유료 API 아님). Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 만들고,
  django-allauth(google provider) 또는 google-auth로 ID 토큰을 검증하면 됩니다.
  hd=kaist.ac.kr 힌트로 KAIST Workspace 계정만 허용할 수 있습니다.
  (프로토타입의 Google 버튼은 이 흐름을 시뮬레이션합니다.)
- **KAIST SSO 버튼**: 발표 시연용으로 화면에만 두었고 동작은 하지 않습니다.

## 에셋

- 마스코트 PNG 5종은 제공된 넙죽이 스티커에서 추출했습니다.
- static/images/logo/kaist_logo.png 는 자리표시자입니다. 공식 로고로 교체해 주세요.
