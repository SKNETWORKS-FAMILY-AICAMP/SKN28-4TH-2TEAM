# KAIST AI대학 데이터 — MySQL 적재 가이드

KAIST AI대학 4개 학과(AIC·AX·AI Systems·FX) 크롤링 데이터를 MySQL에 적재하는 SQL 스크립트 모음입니다.

---

## 파일 구성

| 파일 | 역할 |
|------|------|
| `01_schema.sql` | DB·테이블 생성 (스키마 정의, PK/FK/INDEX) |
| `02_load.sql` | CSV → 스테이징 → 정규화 테이블 적재 (ETL) |
| `03_verify.sql` | 적재 결과 검증 쿼리 모음 |
| `load_with_pymysql.py` | MySQL `local_infile` 권한이 없을 때 쓰는 PyMySQL 적재 스크립트 |
| `ERD.md` | 개체-관계 다이어그램 (Mermaid) |
| `clean_csv.ps1` | 구버전 원본 CSV 내부 줄바꿈 제거용 보조 스크립트 |

실행 순서: `01` → `02` → `03`

---

## 설계 원칙 (요약)

자세한 다이어그램·설명은 [`ERD.md`](ERD.md) 참고. 핵심만 요약하면:

- **주제 영역 4분할** — ① 업무 도메인(department·person·course·track·course_track·admission·event) ② 수집/자원(asset·attachment) ③ KAIST 기본 정보(kaist_profile·kaist_statistics·kaist_link·department_office) ④ RAG(rag_document·rag_chunk). ERD도 영역별 도표로 나눠 발표 자료에 담기 쉽게 했습니다.
- **키 전략 통일** — 크롤링이 준 고유 ID가 있으면 자연키 PK(VARCHAR: `record_id`/`doc_id`/`chunk_id`), 없는 파생 엔터티만 인조키(`BIGINT AUTO_INCREMENT`: `track_id`/`attachment_id`) + `UNIQUE` 로 업무 고유성 보장.
- **정규화(3NF)** — `dept_name` 을 `department` 한 곳으로 모으고, `rag_chunk` 의 문서 메타(dept·title·source_url 등 6컬럼, 523행 전수 중복)는 `rag_document` 와 이행적 종속이라 제거. 학과·제목은 `doc_id` 로 JOIN 해서 얻습니다.
- **참조 명확화** — `attachment` 의 실제 부모는 게시글(post)이며 `board` 로 admission/event 가 갈립니다(`(dept,board,post_id)` UNIQUE 로 식별). 교수↔과목 M:N 은 크롤링 데이터에 연결 정보가 없어 **데이터 갭**으로 남겨두었습니다.

---

## 환경 설정

### 요구사항
- MySQL 8.x (서비스 실행 중)
- 저장소를 **어느 경로에 클론해도 무관**합니다. 단, 실행은 반드시 **프로젝트 루트(저장소 최상위 폴더)에서** 해야 합니다.

> `02_load.sql`의 CSV 경로는 프로젝트 루트 기준 **상대경로**(`data/processed/csv/...`)로 작성되어 있어, 팀원이 경로를 별도 수정할 필요가 없습니다.

### MySQL 권한 설정 (root로 1회 실행)

아래 `'your_user'`를 **본인 MySQL 계정명**으로 바꿔서 실행하세요.

```sql
-- kaist_ai DB 및 LOAD DATA 권한 부여
GRANT ALL PRIVILEGES ON kaist_ai.* TO 'your_user'@'localhost';
GRANT FILE ON *.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;

-- LOAD DATA LOCAL INFILE 서버 측 활성화
SET GLOBAL local_infile = 1;
```

> 예) 계정이 `root`이면 `'root'@'localhost'`, `practice`이면 `'practice'@'localhost'`

---

## 실행 명령어

**반드시 프로젝트 루트로 먼저 이동한 뒤** 실행하세요. `-u` 뒤에 본인 계정, `-p` 뒤에 본인 비밀번호를 붙입니다.

```bash
# 0단계: 프로젝트 루트로 이동 (각자 클론한 경로로 변경)
cd /path/to/skn28-3RD-2TEAM

# 1단계: 테이블 생성
mysql -u your_user -pyour_password --local-infile=1 -e "source sql/01_schema.sql"

# 2단계: 데이터 적재
mysql -u your_user -pyour_password --local-infile=1 -e "source sql/02_load.sql"

# 3단계: 검증
mysql -u your_user -pyour_password --local-infile=1 -e "source sql/03_verify.sql"
```

> - `-p` 바로 뒤에 비밀번호를 붙입니다 (띄어쓰기 없음). 예: `-proot1234`
> - `--local-infile=1` 플래그 없이 실행하면 `02_load.sql`의 `LOAD DATA LOCAL INFILE`이 실패합니다.
> - Windows에서 `mysql`을 찾지 못하면 전체 경로로 실행하세요: `"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"`

### local_infile 권한이 없을 때

MySQL 서버에서 `SET GLOBAL local_infile = 1` 권한이 없으면 `02_load.sql`의 `LOAD DATA LOCAL INFILE`이 막힐 수 있습니다. 이때는 스키마만 만든 뒤 PyMySQL 로더로 같은 데이터를 적재합니다.

```powershell
mysql -u your_user -pyour_password -e "source sql/01_schema.sql"
python sql\load_with_pymysql.py
mysql -u your_user -pyour_password -e "source sql/03_verify.sql"
```

---

## CSV 전처리

SQL 적재 입력은 `data/processed/csv/`입니다. 원본 크롤링 데이터나 PDF 설정을 바꿨다면 먼저 전처리를 다시 실행해 이 폴더를 갱신하세요.

```powershell
python data\preprocessing.py
```

---

## 적재 후 기대 행 수

| 테이블 | 행 수 | 비고 |
|--------|-------|------|
| department | 4 | 학과 마스터 |
| person | 246 | 교수/구성원 |
| course | 109 | 교과목 |
| track | 21 | 트랙 마스터 (자동 추출) |
| course_track | 109 | 과목↔트랙 교차 엔터티 |
| admission | 74 | 입학 정보 |
| event | 4 | 행사 |
| asset | 270 | 링크·이미지 (원본 494행, 중복 224행 제거) |
| attachment | 4 | PDF 첨부파일 |
| department_office | 41 | KAIST 학과사무실/행정실 연락처 |
| kaist_profile | 9 | KAIST 기본 정보 |
| kaist_statistics | 12 | KAIST 통계 정보 |
| kaist_link | 7 | KAIST 공식 링크 |
| rag_document | 577 | 문서 메타데이터 |
| rag_chunk | 778 | RAG 검색용 청크 (PDF 본문 포함, 문서 메타는 rag_document 에서 JOIN) |
| quality_report | 14 | 검산 지표 (독립 테이블) |

---

## ERD 미리보기

VS Code에서 `ERD.md`를 열고 `Ctrl+Shift+V`로 Markdown Preview를 열면 Mermaid 다이어그램을 볼 수 있습니다.  
(Mermaid 미리보기 확장 설치 필요)
