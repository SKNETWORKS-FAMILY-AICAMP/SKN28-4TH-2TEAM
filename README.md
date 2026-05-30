# SKN28_3RD_2TEAM
김성재, 손지은, 신혜지, 심기성


KAIST AI 관련 학과 사이트에서 수집한 데이터를 기반으로 RAG 챗봇을 구성하는 프로젝트입니다.

현재 구현 범위는 다음과 같습니다.

- 학과 사이트 수집/전처리 데이터 활용
- Chroma vectorstore 생성
- 질문 유형 분석
- Vector 검색
- SQL 검색 결과를 받을 수 있는 인터페이스
- LLM 답변용 context 구성
- 프롬프트 기반 답변 생성
- 합격 여부/합격 가능성 등 개인별 판정 질문 차단

## 프로젝트 구조

```text
.
├─ data/
│  ├─ build_vectorstore.py        # JSONL -> Chroma vectorstore 생성
│  ├─ preprocssing.py             # 원본 CSV/PDF 전처리 스크립트
│  └─ raw_data/                   # 원본/전처리 데이터
├─ src/
│  └─ rag/
│     ├─ query_analyzer.py        # 질문 의도, 학과, route 분석
│     ├─ vector_retriever.py      # Chroma 기반 vector 검색
│     ├─ context_builder.py       # 검색 결과를 LLM context로 변환
│     ├─ answer_generator.py      # 프롬프트 및 LLM 답변 생성
│     ├─ rag_pipeline.py          # 분석 -> 검색 -> context -> 답변 연결
│     └─ test.py                  # 간단 동작 테스트
├─ .env                           # OpenAI API key 등 로컬 환경변수
└─ README.md
```

## 환경 설정

Python 환경을 활성화한 뒤 프로젝트 루트에서 작업합니다.

```powershell
cd E:\workspace\SKN28_3RD_2TEAM
```

필요 패키지 예시:

```powershell
pip install python-dotenv langchain-core langchain-openai langchain-chroma chromadb pandas tqdm pymupdf
```

현재 환경에 패키지가 설치되어 있는지 확인하려면:

```powershell
python -c "import importlib.util as u; print({m: bool(u.find_spec(m)) for m in ['langchain_core','langchain_openai','langchain_chroma','dotenv','chromadb']})"
```

## .env 설정

프로젝트 루트에 `.env` 파일을 만들고 OpenAI API key를 설정합니다.

```env
OPENAI_API_KEY=sk-...
```

현재 코드에서 필수로 사용하는 환경변수는 `OPENAI_API_KEY`입니다.

`.env`는 `.gitignore`에 포함되어 있으므로 업로드하지 않습니다.

## Vectorstore 생성

전처리된 JSONL 파일을 Chroma DB로 변환합니다.

기본 입력 파일:

```text
data/raw_data/processed/vectorstore/vector_documents.jsonl
```

기본 출력 폴더:

```text
data/vectorstore/chroma_db
```

생성 명령어:

```powershell
python data\build_vectorstore.py --reset --smoke-test
```

옵션을 명시해서 실행할 수도 있습니다.

```powershell
python data\build_vectorstore.py `
  --project-root "." `
  --jsonl-path "data/raw_data/processed/vectorstore/vector_documents.jsonl" `
  --chroma-dir "data/vectorstore/chroma_db" `
  --reset `
  --smoke-test
```

## 기본 사용법

파이프라인은 `RagPipeline`을 통해 실행합니다.

```python
from src.rag.rag_pipeline import RagPipeline

pipeline = RagPipeline()
result = pipeline.run("AI컴퓨팅학과 석사 지원 자격은?")

print(result.answer)
print(result.sources)
print(result.warnings)
```

간단한 PowerShell 실행:

```powershell
python -c "from src.rag.rag_pipeline import RagPipeline; p=RagPipeline(); r=p.run('AI컴퓨팅학과 석사 지원 자격은?'); print(r.answer); print(r.warnings)"
```

## 테스트 실행

테스트 파일:

```text
src/rag/test.py
```

실행 명령어:

```powershell
python src\rag\test.py
```

테스트 파일은 다음 질문들을 확인합니다.

```text
AI컴퓨팅학과 합격 여부 알려줘
내 GPA 3.8인데 AI컴퓨팅학과 붙을 수 있어?
AI컴퓨팅학과 합격자 발표 일정 알려줘
AI컴퓨팅학과 석사 지원 자격은?
```

예상 동작:

- `합격 여부`, `붙을 수 있어?` 같은 개인별 판정 질문은 차단됩니다.
- `합격자 발표 일정`은 공식 일정 질문이므로 차단되지 않습니다.
- vectorstore 또는 API 연결이 안 되어 있으면 warning이 출력됩니다.

## 추가된 안전 정책

`answer_generator.py`에 답변 정책이 추가되어 있습니다.

차단 대상:

```text
합격 여부
합격 가능성
합격 확률
선발 가능성
내 스펙으로 붙을지
GPA/학점/경력 기반 개인별 합격 예측
```

예시:

```text
Q. 내 GPA 3.8인데 AI컴퓨팅학과 붙을 수 있어?
A. 합격 여부, 합격 가능성, 선발 확률처럼 개인별 결과를 판정하거나 예측하는 질문에는 답변할 수 없습니다...
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
```

## 주요 모듈 설명

### `query_analyzer.py`

사용자 질문을 분석합니다.

- 학과명 추출
- 질문 intent 분류
- route 결정: `sql`, `vector`, `hybrid`, `clarify`
- metadata filter 생성
- SQL 조회 조건 생성

### `vector_retriever.py`

Chroma vectorstore에서 관련 문서를 검색합니다.

- OpenAI embedding 사용
- metadata filter 검색
- fallback 검색
- lightweight rerank

### `context_builder.py`

검색 결과를 LLM에 넣을 context로 변환합니다.

- vector 문서 포맷팅
- SQL 결과 Markdown table 변환
- source/warning 정리
- 수집일, 파일명, 페이지, section 등 metadata 포함
- context 길이 제한

### `answer_generator.py`

LLM 답변을 생성합니다.

- system/human prompt 구성
- intent별 답변 지시
- 비교 질문 지시
- 출처 및 warning 반영
- 개인별 합격 판정 질문 차단

### `rag_pipeline.py`

전체 RAG 흐름을 연결합니다.

```text
질문 입력
-> 질문 분석
-> 정책 검사
-> SQL/vector 검색
-> context 구성
-> 답변 생성
-> answer/sources/warnings 반환
```

## Streamlit 연결 예시

현재 `streamlit_app.py`와 `pages/3_RAG_Chatbot.py`는 발표용 데모 화면이며, `data.demo_knowledge.get_demo_response()`를 사용합니다. 즉, Streamlit 화면은 아직 `RagPipeline`, `answer_generator.py`, `context_builder.py` 같은 실제 RAG 함수와 직접 연결되어 있지 않습니다.

실제 RAG 답변을 Streamlit에 붙일 때는 `RagPipeline.run()`을 호출하도록 챗봇 페이지의 응답 생성 부분을 교체하면 됩니다.

아래는 실제 RAG 함수와 연결할 때 사용할 수 있는 예시입니다.

```python
import streamlit as st
from src.rag.rag_pipeline import RagPipeline

pipeline = RagPipeline()

question = st.chat_input("학과 사이트 정보에 대해 질문해 주세요.")

if question:
    result = pipeline.run(question)

    st.write(result.answer)

    if result.warnings:
        with st.expander("Warnings"):
            st.write(result.warnings)

    if result.sources:
        with st.expander("참고 출처"):
            for source in result.sources:
                st.write(source)
```

## 주의사항

- `.env` 파일은 업로드하지 않습니다.
- `data/vectorstore/`, `chroma_db/`는 로컬 생성 산출물이므로 업로드하지 않습니다.
- 실제 답변 테스트 전 `OPENAI_API_KEY`와 Chroma DB가 준비되어 있어야 합니다.
- SQL 검색기는 현재 pipeline에 연결할 수 있는 자리만 있으며, 실제 SQL 조회 구현은 별도 모듈에서 붙이면 됩니다.
- `합격 가능성` 같은 개인별 판정 질문은 검색 결과가 있어도 답변하지 않도록 정책 차단됩니다.

### Streamlit Demo 실행 방법
- Mac: python3 -m streamlit run streamlit_app.py
- Windows: python -m streamlit run streamlit_app.py
