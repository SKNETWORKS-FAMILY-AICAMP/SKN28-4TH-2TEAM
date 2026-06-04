# 2026-06-04 작업 내역 (KIM)

## 수정 사항

### 1. `sql/02_load.sql` 버그 수정
- STEP 2 주석 아래에 잘못 삽입된 `SET utf8mb4 FIELDS TERMINATED BY ...` 구문 제거
- `UNIONLOAD DATA LOCAL INFILE 'csv/_clean/people_clean.csv'` 오타 수정
  - `UNION`과 `LOAD DATA`가 붙어있던 문제 해결
  - 잘못된 파일 경로(`csv/_clean/`) 참조 제거
  - `INSERT INTO department` 쿼리가 세미콜론으로 정상 종결되도록 수정

### 2. Quick Questions 버튼 텍스트 변경 (`streamlit_app.py`, `pages/3_RAG_Chatbot.py`)
| 변경 전 | 변경 후 |
|---|---|
| 입학 서류가 궁금해요 | AI컴퓨팅학과 석사 지원 자격은? |
| 연구 분야 알려줘 | AI컴퓨팅학과 교과목과 설명 알려줘 |
| 교수님 찾는 기준은? | AX학과 교수진 이메일 목록 보여줘 |

### 4. Quick Questions 2번 질문 재수정 (`streamlit_app.py`, `pages/3_RAG_Chatbot.py`)
- `AI시스템학과 교과목과 설명 알려줘` → `AI컴퓨팅학과 교과목과 설명 알려줘` 로 변경

### 3. 전처리 데이터 업데이트 (`data/processed/`)
- `preprocessing.py` 재실행으로 CSV 파일 최신화
  - `assets.csv`, `course_track_map.csv`, `people.csv` 등 업데이트
  - `preprocess_summary.csv` 리포트 갱신

## 실행 순서 (초기 세팅)

```bash
# 1. 전처리
python data/preprocessing.py

# 2. VectorStore 생성
python data/build_vectorstore.py

# 3. MySQL 스키마 및 데이터 적재
mysql -u practice -ppractice kaist_ai < sql/01_schema.sql
mysql -u practice -ppractice --local-infile=1 kaist_ai < sql/02_load.sql
mysql -u practice -ppractice kaist_ai < sql/03_verify.sql

# 4. Streamlit 실행
streamlit run streamlit_app.py
```

## 참고
- `.env` 파일은 gitignore 처리되어 있음 — clone 후 직접 생성 필요
- `OPENAI_API_KEY`, `MYSQL_HOST/USER/PASSWORD/DATABASE` 설정 필요
