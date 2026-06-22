# SKN28-4TH-2TEAM

김성재, 손지은, 신혜지, 심기성

KAIST AI 관련 학과 사이트에서 수집한 데이터를 기반으로 RAG 챗봇을 구성하는 프로젝트입니다.  
Streamlit 화면에서 사용자의 질문을 받고, RAG 파이프라인이 질문 분석, SQL/Vector 검색, context 구성, LLM 답변 생성을 수행합니다.

## 현재 구현 범위

- KAIST AI 관련 학과 수집/전처리 데이터 활용
- CSV 정형 데이터와 PDF/문서 기반 비정형 데이터 분리 처리
- MySQL 적재용 CSV 생성 및 SQL 조회 구조 구성
- Chroma vectorstore 생성 및 문서 검색
- 질문 유형, 학과, route 분석
- 키워드 기반 분류와 애매한 질문용 예시 유사도 매칭
- 수집 범위 밖 KAIST 학과 및 KAIST 외 질문 분기
- SQL 검색과 Vector 검색을 함께 사용할 수 있는 hybrid RAG 구조
- SQL 검색 실패 또는 결과 부족 시 Vector 검색 fallback
- 검색 결과를 LLM 답변용 context로 구성
- LangChain `ChatOpenAI` 기반 답변 생성
- intent별 답변 포맷 지시와 안전 프롬프트
- 개인별 합격 여부, 합격 가능성, 선발 확률 질문 차단
- Streamlit 챗봇 연결, 대화 맥락 유지, 동일 질문 캐시
- 답변 streaming 출력 및 출처 카드 표시
- 첫 질문 지연 완화를 위한 RAG warm-up
- 테스트 노트북 및 챗봇 평가 결과 저장 구조 구성

## 지원 학과

현재 RAG 챗봇은 수집된 KAIST AI 관련 학과 데이터를 중심으로 답변합니다.

```text
AI컴퓨팅학과  -> aic
AI시스템학과  -> ai_systems
AX학과        -> ax
AI미래학과    -> fx
```

수집하지 않은 KAIST 학과를 물어보면 충분한 데이터가 없음을 안내하고 KAIST 공식 홈페이지 또는 입학처 확인을 권장합니다.  
KAIST와 관련 없는 질문은 챗봇 범위를 벗어난 질문으로 거절합니다.

## 지원 질문 유형

```text
admission_info        입학, 모집, 지원자격, 전형, 일정
course_info           교과목, 교육과정, 커리큘럼
person_info           교수진, 구성원, 이메일, 연구실
office_contact_info   학과 사무실, 전화번호, 위치
event_info            공지, 행사, 설명회
asset_or_link_info    링크, 자료, 다운로드, PDF
department_overview   학과 소개, 개요, 특징
kaist_profile_info    KAIST 기본 정보
kaist_statistics_info KAIST 통계 정보
kaist_link_info       KAIST 공식 링크
general_info          그 외 일반 정보
```

질문 분석 결과에 따라 route는 다음 중 하나로 결정됩니다.

```text
sql       정형 조회가 적합한 질문
vector    문서 기반 설명이 필요한 질문
hybrid    정형 조회와 문서 설명이 모두 필요한 질문
clarify   질문 정보가 부족해 추가 확인이 필요한 질문
```

## 프로젝트 구조

```text
.
├─ assets/
│  └─ kaist.jpg
├─ components/
│  ├─ __init__.py
│  ├─ layout.py
│  └─ styles.py
├─ data/
│  ├─ build_vectorstore.py              # JSONL -> Chroma vectorstore 생성
│  ├─ demo_knowledge.py
│  ├─ preprocessing.py                  # 원본 CSV/PDF 전처리
│  ├─ raw_data/                         # 원본 CSV/PDF 데이터
│  │  ├─ admissions_clean.csv
│  │  ├─ assets_clean.csv
│  │  ├─ attachments_clean.csv
│  │  ├─ course_track_map.csv
│  │  ├─ courses_clean.csv
│  │  ├─ events_clean.csv
│  │  ├─ people_clean.csv
│  │  ├─ quality_report.csv
│  │  ├─ AI_Computing_Grad_Info_Session_20260320.pdf
│  │  ├─ AI_Systems_Grad_Info_20260319.pdf
│  │  ├─ KAIST AI & FUTURES STUDIES.pdf
│  │  ├─ KAIST AX (AI Transformation).pdf
│  │  ├─ 손지은_KAIST_공식홈페이지_조사 - 기본정보.csv
│  │  └─ 손지은_KAIST_공식홈페이지_조사 - 학과사무실.csv
│  ├─ processed/                        # 전처리 결과
│  │  ├─ csv/                           # SQL 적재 및 정형 조회용 CSV
│  │  │  ├─ admissions.csv
│  │  │  ├─ assets.csv
│  │  │  ├─ attachments.csv
│  │  │  ├─ courses.csv
│  │  │  ├─ course_track_map.csv
│  │  │  ├─ department_offices.csv
│  │  │  ├─ events.csv
│  │  │  ├─ kaist_links.csv
│  │  │  ├─ kaist_profile.csv
│  │  │  ├─ kaist_statistics.csv
│  │  │  ├─ people.csv
│  │  │  ├─ rag_documents.csv
│  │  │  ├─ rag_chunks.csv
│  │  │  └─ quality_report.csv
│  │  ├─ json/                          # VectorStore 적재용 문서
│  │  │  ├─ vector_documents.json
│  │  │  └─ vector_documents.jsonl
│  │  └─ reports/                       # 전처리/테스트 리포트
│  │     ├─ pdf_page_report.csv
│  │     ├─ preprocess_summary.csv
│  │     └─ rag_test_results.json
│  └─ vectorstore/                      # 로컬 Chroma DB 생성 위치, Git 업로드 제외
│     └─ chroma_db/
├─ notebooks/
│  ├─ rag_test.ipynb                    # RAG 검색/응답 실험 노트북
│  └─ chatbot_eval_outputs/
│     └─ chatbot_test_results.csv       # 챗봇 테스트 결과 저장 파일
├─ pages/
│  ├─ 1_AI_College_Intro.py
│  ├─ 2_Departments.py
│  └─ 3_RAG_Chatbot.py                  # Streamlit RAG 챗봇 페이지
├─ sql/
│  ├─ 01_schema.sql                     # MySQL 스키마 생성
│  ├─ 02_load.sql                       # data/processed/csv 기반 데이터 적재
│  ├─ 03_verify.sql                     # 적재 결과 검증
│  ├─ clean_csv.ps1
│  ├─ ERD.md
│  ├─ OPEN_ISSUES.md
│  └─ README.md
├─ src/
│  └─ rag/
│     ├─ query_analyzer.py              # 질문 의도, 학과, route 분석
│     ├─ vector_retriever.py            # Chroma 기반 vector 검색, fallback, rerank
│     ├─ sql_tool.py                    # MySQL 기반 SQL 조회
│     ├─ context_builder.py             # 검색 결과를 LLM context로 변환
│     ├─ answer_generator.py            # 프롬프트 및 LLM 답변 생성
│     ├─ rag_pipeline.py                # 분석 -> 검색 -> context -> 답변 연결
│     ├─ rag_tests.py                   # RAG 테스트 코드
│     ├─ test.py
│     └─ test.ipynb
├─ .streamlit/
│  └─ config.toml
├─ .env                                 # 로컬 환경변수, Git 업로드 제외
├─ .env.example                         # 공유용 환경변수 예시
├─ .gitignore
├─ requirements.txt
├─ streamlit_app.py                     # Streamlit 진입 파일
└─ README.md
```

## 환경 설정

Python 환경을 활성화한 뒤 프로젝트 루트에서 작업합니다.

```powershell
cd <프로젝트_루트>
```

필요 패키지 설치:

```powershell
pip install -r requirements.txt
```

필요 패키지 예시:

```powershell
pip install python-dotenv langchain-core langchain-openai langchain-chroma chromadb pandas tqdm pymupdf streamlit pymysql sqlalchemy
```

패키지 설치 여부 확인:

```powershell
python -c "import importlib.util as u; print({m: bool(u.find_spec(m)) for m in ['dotenv','langchain_core','langchain_openai','langchain_chroma','chromadb','streamlit','pymysql']})"
```

`python` 명령이 잡히지 않는 환경에서는 사용 중인 가상환경의 Python 실행 파일로 같은 명령을 실행하면 됩니다.

## 환경변수

프로젝트 루트에 `.env` 파일을 만들고 OpenAI API key와 MySQL 접속 정보를 설정합니다.

```env
# OpenAI
OPENAI_API_KEY=sk-여기에_본인_OpenAI_API_Key

# MySQL
KAIST_MYSQL_HOST=127.0.0.1
KAIST_MYSQL_PORT=3306
KAIST_MYSQL_USER=root
KAIST_MYSQL_PASSWORD=본인_mysql_비밀번호
KAIST_MYSQL_DATABASE=kaist_ai
KAIST_SQL_MAX_ROWS=100
KAIST_MYSQL_CONNECT_TIMEOUT=5
```

`.env` 파일은 개인 로컬 설정 파일이므로 Git에 업로드하지 않습니다.  
공유가 필요한 경우 `.env.example`에 키 이름만 남기고 실제 key와 password는 넣지 않습니다.

## 데이터 전처리

원본 데이터는 `data/raw_data/`에 두고, 전처리 결과는 `data/processed/` 아래에 저장합니다.

```powershell
python data\preprocessing.py
```

전처리 결과는 크게 두 종류로 나뉩니다.

```text
data/processed/csv/    MySQL 적재 및 정형 조회용 데이터
data/processed/json/   Chroma VectorStore 적재용 문서 데이터
```

전처리 후 확인할 주요 파일:

```text
data/processed/csv/admissions.csv
data/processed/csv/courses.csv
data/processed/csv/people.csv
data/processed/csv/department_offices.csv
data/processed/csv/rag_documents.csv
data/processed/csv/rag_chunks.csv
data/processed/json/vector_documents.jsonl
data/processed/reports/preprocess_summary.csv
```

## MySQL DB 생성 및 적재

`SQLTool`을 사용하는 `sql` 또는 `hybrid` route 질문을 확인하려면 MySQL DB를 먼저 생성하고 `data/processed/csv/` 데이터를 적재합니다.

```powershell
mysql -u your_user -pyour_password --local-infile=1 -e "source sql/01_schema.sql; source sql/02_load.sql; source sql/03_verify.sql"
```

MySQL 서버에서 `local_infile` 권한을 켤 수 없는 환경에서는 스키마만 만든 뒤 PyMySQL 로더를 사용합니다.

```powershell
mysql -u your_user -pyour_password -e "source sql/01_schema.sql"
python sql\load_with_pymysql.py
mysql -u your_user -pyour_password -e "source sql/03_verify.sql"
```

또는 MySQL에 접속한 뒤 순서대로 실행합니다.

```sql
source sql/01_schema.sql;
source sql/02_load.sql;
source sql/03_verify.sql;
```

적재 확인 예시:

```sql
SELECT COUNT(*) FROM admission;
SELECT COUNT(*) FROM course;
SELECT COUNT(*) FROM person;
SELECT COUNT(*) FROM rag_chunk;
```

SQL 연결이 실패하거나 SQL 결과가 부족한 경우, 파이프라인은 설정에 따라 vector 검색으로 fallback할 수 있습니다.

## Vectorstore 생성

전처리된 JSONL을 Chroma DB로 변환합니다.

기본 입력:

```text
data/processed/json/vector_documents.jsonl
```

기본 출력:

```text
data/vectorstore/chroma_db
```

실행 명령어:

```powershell
python data\build_vectorstore.py --reset --smoke-test
```

옵션을 명시해서 실행할 수도 있습니다.

```powershell
python data\build_vectorstore.py `
  --project-root "." `
  --jsonl-path "data/processed/json/vector_documents.jsonl" `
  --chroma-dir "data/vectorstore/chroma_db" `
  --embedding-model "text-embedding-3-small" `
  --reset `
  --smoke-test
```

`--reset` 옵션은 기존 Chroma DB를 지우고 새로 생성합니다.  
이미 생성된 DB를 유지하면서 테스트만 하고 싶다면 `--reset`을 빼고 실행합니다.

## RAG 파이프라인 흐름

```text
사용자 질문
-> QueryAnalyzer
-> 답변 정책 검사
-> SQL 검색 또는 Vector 검색
-> SQL 실패/결과 부족 시 fallback 검색
-> ContextBuilder
-> AnswerGenerator
-> answer, sources, warnings 반환
```

질문 route에 따른 동작은 다음과 같습니다.

```text
sql
  정형 데이터 조회가 적합한 질문입니다.
  예: 특정 학과 교수 목록, 연락처, 과목명, 일정 등

vector
  문서 기반 설명이 필요한 질문입니다.
  예: 학과 소개, 모집 요강 설명, PDF 기반 상세 안내 등

hybrid
  SQL 조회와 문서 설명이 모두 필요한 질문입니다.
  예: 학과별 교과목 목록과 교육과정 설명을 함께 묻는 질문

clarify
  학과명, 질문 대상, 조건 등이 부족해 바로 검색하기 어려운 질문입니다.
```

SQL 검색기는 `src/rag/sql_tool.py`의 `SQLTool`을 통해 MySQL과 연결됩니다.  
`create_default_pipeline(include_sql=True)`를 사용하면 SQLTool 연결을 시도하고, SQL 결과가 없거나 SQL 연결이 실패한 경우 설정에 따라 Vector 검색으로 fallback합니다.

## 기본 사용법

파이프라인은 `RagPipeline` 또는 `create_default_pipeline()`을 통해 실행합니다.

```python
from src.rag.rag_pipeline import create_default_pipeline

pipeline = create_default_pipeline(include_sql=True)
result = pipeline.run("AI컴퓨팅학과 석사 지원 자격은?")

print(result.answer)
print(result.sources)
print(result.warnings)
```

PowerShell에서 간단 실행:

```powershell
python -c "from src.rag.rag_pipeline import create_default_pipeline; p=create_default_pipeline(include_sql=True); r=p.run('AI컴퓨팅학과 석사 지원 자격은?'); print(r.answer); print(r.warnings)"
```

질문 분류만 확인:

```powershell
python -c "from src.rag.rag_pipeline import create_default_pipeline; p=create_default_pipeline(include_sql=True); a=p.classify_question('교수진도 알려줘'); print(a.to_dict())"
```

첫 질문 응답 지연을 줄이려면 앱 시작 시점에 vector retriever를 미리 초기화할 수 있습니다.

```python
from src.rag.rag_pipeline import create_default_pipeline

pipeline = create_default_pipeline(include_sql=True)
warm_up_result = pipeline.warm_up(
    sample_question="AI컴퓨팅학과 입학 정보",
)
```

`sample_question`을 넣으면 Chroma 연결뿐 아니라 첫 vector 검색까지 미리 실행합니다. 따라서 실제 첫 사용자 질문에서는 retriever 초기화 비용이 덜 걸립니다.

## 테스트 실행

테스트 노트북:

```text
notebooks/rag_test.ipynb
```

챗봇 평가 결과 저장 파일:

```text
notebooks/chatbot_eval_outputs/chatbot_test_results.csv
```

테스트 파일은 다음 질문들을 확인합니다.

```text
AI컴퓨팅학과 합격 여부 알려줘
내 GPA 3.8인데 AI컴퓨팅학과 붙을 수 있어?
AI컴퓨팅학과 합격자 발표 일정 알려줘
AI컴퓨팅학과 석사 지원 자격은?
교수진도 알려줘
AI컴퓨팅학과 사무실 연락처 알려줘
```

예상 동작:

- `합격 여부`, `붙을 수 있어?` 같은 개인별 판정 질문은 차단됩니다.
- `합격자 발표 일정`은 공식 일정 질문이므로 차단되지 않습니다.
- 학과명이 생략된 후속 질문은 이전 대화 맥락의 학과 정보를 활용할 수 있습니다.
- SQL 연결이 준비되어 있으면 정형 데이터 질문은 SQL 결과를 우선 활용합니다.
- vectorstore 또는 API 연결이 안 되어 있으면 warning이 출력됩니다.

### 회귀 검증 스위트 (결정적, DB/LLM 비의존)

질문 분류와 SQL 출력단계를 케이스 단위로 고정해 회귀를 잡는 검증 하니스입니다. 코드 수정 후 빠르게 돌려 회귀를 확인합니다. 상세는 [`validation/rag_quality/README.md`](validation/rag_quality/README.md) 참조.

```powershell
python validation\rag_quality\validate_rag_quality.py     # 질문 분류 골든 (API 불필요)
python validation\rag_quality\sql_multi_intent_smoke.py   # SQL 다중 의도 행 단위 스모크 (DB/LLM 비의존)
```

## 주요 모듈

### `src/rag/query_analyzer.py`

사용자 질문을 분석합니다.

- 학과명 추출
- 질문 intent 분류
- 애매한 질문에 대한 예시 유사도 매칭
- route 결정: `sql`, `vector`, `hybrid`, `clarify`
- metadata filter 생성
- SQL 조회 조건 생성
- 수집 범위 밖 KAIST 학과, KAIST 외 질문, 너무 넓은 질문 처리

### `src/rag/vector_retriever.py`

Chroma vectorstore에서 관련 문서를 검색합니다.

- OpenAI embedding 사용
- metadata filter 검색
- 학과/intent 기반 필터링
- 검색 결과가 부족할 때 fallback 검색
- 점수 기반 lightweight rerank
- LLM context에 넣기 좋은 검색 결과 형태로 정리

### `src/rag/sql_tool.py`

MySQL에 적재된 정형 데이터를 조회합니다.

- 학과별 입학 정보 조회
- 학과별 교과목 조회
- 교수진/구성원 정보 조회
- 학과 사무실, 연락처, 위치 조회
- 공식 링크 및 기본 정보 조회
- SQL 결과 row 수 제한
- SQL 연결 실패 시 warning 반환

### `src/rag/context_builder.py`

검색 결과를 LLM에 넣을 context로 변환합니다.

- vector 문서 포맷팅
- SQL 결과 Markdown table 변환
- source/warning 정리
- 수집일, 파일명, 페이지, section 등 metadata 포함
- context 길이 제한
- SQL 결과와 vector 문서를 함께 사용할 수 있는 hybrid context 구성

### `src/rag/answer_generator.py`

LLM 답변을 생성합니다.

- system/human prompt 구성
- intent별 답변 지시
- 비교 질문 지시
- 애매한 질문 유형별 안내 지시
- 출처 및 warning 반영
- 개인별 합격 판정 질문 차단
- streaming 답변 생성

### `src/rag/rag_pipeline.py`

전체 RAG 흐름을 연결합니다.

```text
질문 입력
-> 질문 분석
-> 정책 검사
-> SQL/vector 검색
-> fallback 검색
-> context 구성
-> 답변 생성
-> answer/sources/warnings 반환
```

주요 메서드:

```text
classify_question()
warm_up()
search()
build_context()
generate_answer()
generate_answer_streaming()
run()
run_streaming()
run_dict()
```

## Streamlit 실행

Streamlit 진입 파일은 `streamlit_app.py`입니다.

Windows:

```powershell
python -m streamlit run streamlit_app.py
```

Mac/Linux:

```bash
python3 -m streamlit run streamlit_app.py
```

프로젝트 루트에서 실행하면 `.streamlit/config.toml` 설정이 자동 적용됩니다. 현재 설정은 Streamlit 파일 감시기를 끄도록 되어 있어, 응답 생성 중 `Accessing __path__ from .models.aria.image_processing_aria` 경고 이후 로컬 서버 연결이 끊기는 문제를 피합니다.

설정을 명령어에 직접 명시해야 하는 경우:

```powershell
python -m streamlit run streamlit_app.py --server.fileWatcherType none
```

## Streamlit RAG 연결

현재 `pages/3_RAG_Chatbot.py`는 `RagPipeline.run_streaming()`을 호출해 실제 RAG 흐름과 연결되어 있습니다.

Streamlit 챗봇 페이지는 사용자 질문을 받아 질문 분석, 검색, context 구성, 답변 생성을 실행하고 답변, 출처, warning을 화면에 표시합니다. 답변 생성 중에는 진행 상태를 보여주고, LLM 답변은 가능한 경우 streaming 방식으로 화면에 순차 출력합니다.

한 대화 세션 안에서는 이전 학과 맥락을 유지합니다. 예를 들어 처음에 `AI컴퓨팅학과 입학 정보`를 물은 뒤 `교수진도 알려줘`처럼 후속 질문을 하면 최근 학과 정보를 활용할 수 있습니다.

동일 질문 캐시를 사용할 수 있습니다. Streamlit 화면의 `동일 질문 캐시` 토글을 끄면 테스트 중 같은 질문도 다시 검색하고 답변을 생성합니다. `캐시 비우기` 버튼을 누르면 현재 세션에 저장된 캐시가 삭제됩니다.

첫 질문 지연을 줄이기 위해 Streamlit의 `get_pipeline()`은 `st.cache_resource`로 캐시되며, 생성 시점에 `pipeline.warm_up(sample_question="AI컴퓨팅학과 입학 정보")`를 실행합니다.

핵심 연결 구조는 다음과 같습니다.

```python
@st.cache_resource(show_spinner="RAG 검색기를 초기화하는 중입니다...")
def get_pipeline() -> RagPipeline:
    pipeline = create_default_pipeline(include_sql=True)
    pipeline.warm_up(sample_question="AI컴퓨팅학과 입학 정보")
    return pipeline
```

## 답변 안전 정책

다음 질문은 검색 결과가 있더라도 답변하지 않습니다.

```text
합격 여부
합격 가능성
합격 확률
선발 가능성
내 스펙으로 붙을지
GPA, 학점, 경력 기반 개인별 합격 예측
```

허용 대상:

```text
지원 자격
전형 절차
모집 일정
합격자 발표 일정
제출서류
학과별 교과목
교수진/연락처 정보
자료 링크
```

## 수정 후 확인 기준

코드 수정 후에는 아래 순서로 확인합니다.

```powershell
python -m compileall src
python src\rag\test.py
python -m streamlit run streamlit_app.py
```

VectorStore를 새로 만든 경우에는 먼저 smoke test를 실행합니다.

```powershell
python data\build_vectorstore.py --reset --smoke-test
```

SQL을 수정한 경우에는 DB 적재 검증을 먼저 수행합니다.

```powershell
mysql -u your_user -pyour_password --local-infile=1 -e "source sql/03_verify.sql"
```

Git commit 전 확인:

```powershell
git status
git diff --stat
```

## 주의사항

- `.env` 파일은 업로드하지 않습니다.
- OpenAI API key, MySQL password는 README나 코드에 직접 작성하지 않습니다.
- `data/vectorstore/`, `chroma_db/`는 로컬 생성 산출물이므로 Git 업로드에서 제외합니다.
- 실제 답변 테스트 전 `OPENAI_API_KEY`와 Chroma DB가 준비되어 있어야 합니다.
- SQL 검색을 사용하려면 MySQL DB 생성, CSV 적재, `.env` 접속 정보 설정이 필요합니다.
- SQL 연결이 안 된 상태에서도 vector 검색 기반 답변은 동작할 수 있도록 fallback 구조를 유지합니다.
- `합격 가능성` 같은 개인별 판정 질문은 검색 결과가 있어도 답변하지 않도록 정책 차단됩니다.
- 프롬프트, 검색, context 구성을 수정한 뒤 답변 변화를 확인할 때는 Streamlit의 `동일 질문 캐시` 토글을 끄거나 `캐시 비우기`를 누른 뒤 테스트합니다.
- 노트북과 평가 결과 CSV는 테스트 산출물이므로 main에 올릴지 여부를 commit 전에 확인합니다.
