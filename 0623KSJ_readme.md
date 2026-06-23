# RAG 구조 개선 작업 노트 — 세션6 (김성재, 2026-06-23)

작업 브랜치: **`KSJ_4th`** · HEAD `80de89e` (+ 세션6 변경 미커밋)
업무: RAG 구조 개선 — 프롬프트 / 질문 분류 / 질문 알고리즘 (인수인계)
> 전체 맥락 요약은 [0622KSJ_readme.md](0622KSJ_readme.md), 상세 전문은 [0621KSJ_readme.md](0621KSJ_readme.md) **8.11절** 참조. 이 문서는 **세션6(팀 결정 반영)** 기록이다.

---

## 0. 이번 세션 요약 (TL;DR)
- 팀이 그간 "팀의존·보류"로 분류돼 있던 **잔존 4건**(①CSV EOL ②"교수" 질문 범위 ③답변 길이 ④내부 O(n²))에 실제 결정을 내렸다.
- 4건 중 **액션이 필요한 건 ② 하나**. 나머지 3건은 보류 유지 또는 액션 불요.
- ②를 구현하던 중, 이게 단순 정렬이 아니라 **"AX 전임 교원이 LIMIT에서 통째로 잘려나가던 버그"의 수정**임을 측정으로 확인했다.

---

## 1. 팀 결정 4건 → 처리

| # | 항목 | 분류 | 팀 결정 | 처리 |
|---|---|---|---|---|
| ① | CSV 줄바꿈(EOL) 잡음 | 팀 결정 | 지은님 방식대로 **안 건드림**. 4차 기능 끝나고 시간 남으면 검토 | 보류 유지 |
| ② | "교수" 질문 범위 | 제품 결정 | **전체 노출 + 역할 라벨 노출 + 전임교수를 상위에** | ✅ **구현** |
| ③ | 답변 길이 들쭉날쭉 | 코드 보장 어려움 | 짧아야 할 답을 억지로 늘리지 않음. **과도하게 길 때만** 조절 대상 | 액션 불요(현재 과도 사례 미관측 — 측정 시 재검토) |
| ④ | 내부 성능 정리(O(n²)) | 저우선 | 4차 끝나고 시간 남으면 개선 | 보류 유지 |

---

## 2. ② 구현 — 교수 정렬 우선순위 (전임 먼저)

### 발견 1: "역할 라벨 노출"은 이미 충족돼 있었다
- person의 `role`·`role_normalized` 컬럼은 컨텍스트 표에서 제외되는 노이즈 컬럼 목록(`_SQL_CONTEXT_NOISE_COLUMNS`)에 **없어서**, 이미 LLM 컨텍스트 표에 그대로 실리고 있었다. → 추가 작업 불요.
- 미충족이던 건 **정렬 순서**뿐이었다.

### 발견 2: 기존 정렬이 전임을 뒤로 보내고 있었다 (그리고 잘라버렸다)
- 기존 person 정렬은 `role_normalized` **문자열 가나다순**(`ORDER BY ..., base.role_normalized, ...`).
- 가나다순: `겸임교수` < `중점교원` < `학과장` → **겸임교수가 1번**으로 옴.
- **결정적 피해**: AX학과는 147명(겸임교수 139 · 중점교원 7 · 학과장 1)인데 `LIMIT 100`이 걸린다. 가나다순이면 상위 100명이 **전원 겸임교수**가 되어 **학과장·중점교원 8명이 통째로 잘려나갔다**. 즉 "AX 교수 알려줘"에 학과장도 핵심 교원도 안 보이고 겸임교수만 100명 나오던 상태.
- 측정: 수정 전 AX 상위 100 중 전임 계열 = **0명** → 수정 후 = **8명 전원 보존**.
- 100명 초과 학과는 AX뿐(나머지 46/30/23명)이라 잘림 실피해는 AX 한 곳이지만, 정렬 개선은 4학과 전체에 적용된다.

### 수정 내용 (`src/rag/sql_tool.py`)
- 모듈 상수 `PERSON_ROLE_DISPLAY_ORDER` 추가: `학과장0 · 전임교수1 · 교수2 · 중점교원3 · 겸직교수4 · 겸임교수5` (전임 계열 0–3을 겸임 계열 4–5보다 앞).
- **MySQL 경로**(`_order_sql_for_table`): `ORDER BY base.dept, CASE base.role_normalized WHEN ... END, base.name`.
- **CSV 경로**(`_sort_table`): 임시 랭크 컬럼(`_role_rank`)으로 매핑 후 `dept → _role_rank → name` 정렬, 정렬 후 랭크 컬럼 제거(raw 비파괴).
- 양 경로 모두 **정렬 → LIMIT** 순서라, 잘려도 전임이 먼저 보존된다.

---

## 3. 검증 (적대적 재검토 2회)

| 검증 항목 | 결과 |
|---|---|
| person이 generic ORDER 경로(`_build_mysql_select`)를 타는가 | ✅ dedicated 메서드 없음 → `_order_sql_for_table` 사용 |
| 정렬이 LIMIT **전**인가 | ✅ MySQL `ORDER BY…LIMIT`, CSV `_sort_table().head()` |
| `role_normalized` 전 값이 매핑되는가 | ✅ 6개 값 전부 매핑, 미매핑·NaN **0건**(ELSE 6/fillna는 방어용) |
| 4학과 전수 순서 | ✅ ai_systems[전임→겸직] · aic[학과장→교수→중점] · ax[학과장→중점→겸임] · fx[교수] |
| 전체 혼합 쿼리(학과 미지정) | ✅ 각 학과 내 role 랭크 단조 비감소 |
| edge case (빈 df · 단일행 · 컬럼 부재) | ✅ 전부 안전(fallback) |
| `_role_rank` raw 누출 | ✅ 컬럼·행수 보존, 누출 없음 |
| 실제 LLM 컨텍스트 렌더 | ✅ AX 표가 학과장→중점교원→겸임교수 순 |
| 회귀 | ✅ 분류 **40/40**, 스모크 **#37~#46 ALL PASS** |

### 정직한 한계 1건
- 이 머신은 `mysql_configured()=False`라 **실제 런타임이 CSV 경로**다. 모든 실행 검증은 CSV로 했다.
- MySQL `CASE` 정렬식은 **구문은 표준 유효**(charset utf8mb4)하나, 라이브 MySQL이 없어 **실제 실행 검증은 못 했다**. → MySQL 환경 있는 팀원/배포에서 1회 확인 시 완결.

---

## 4. 현재 상태
- **✅ 세션6 완료**: ② 교수 전임 우선 정렬(+ AX 잘림 버그 수정). 코드 변경 = `src/rag/sql_tool.py` 1파일.
- **스모크 #37~#46 ALL PASS**, 분류 40/40, CSV 경로 출력·edge case 전수 검증.
- **변경 미커밋**: `src/rag/sql_tool.py`. (CSV 5개 EOL churn은 8.7대로 의도적 미커밋.)

### 잔존 (사유 명시)
- **① CSV EOL** — 팀 결정으로 보류(4차 후 여유 시).
- **③ 답변 길이** — 액션 불요(과도하게 길 때만 향후 측정 재검토).
- **④ O(n²)** — 보류(4차 후 여유 시).
- **frontend ↔ RAG 백엔드 연동** — 머지는 트리 통합까지, 실제 배선은 팀 작업(8.10).
- **(선택) #47 회귀 가드** — "전임 먼저"는 이제 제품 요구사항이고 조용히 깨지면 핵심 교원이 잘린다. CSV 경로 결정적 가드(AX 상위 100에 전임 ≥1·겸임보다 앞) 추가 가능. 미착수.

---

## 5. 재현 방법
```powershell
# env: miniforge pystudy_env (PATH python은 더미 — LOCAL_NOTES.md 참고)
python validation\rag_quality\validate_rag_quality.py     # 분류 40/40
python validation\rag_quality\sql_multi_intent_smoke.py   # #37~#46 ALL PASS

# ② 검증: AX 교수 정렬 — 전임 계열이 상위에 오는지
python -c "import sys; sys.path.insert(0,'.'); from src.rag.sql_tool import SQLTool, SQLToolConfig; t=SQLTool(SQLToolConfig()); df=t._read_csv('person'); ax=df[df['dept']=='ax']; print(list(t._sort_table('person',ax)['role_normalized'].drop_duplicates()))"
# 기대: ['학과장', '중점교원', '겸임교수']  (겸임교수가 마지막)
```

---

## 6. 교훈
1. **"라벨 노출"과 "정렬"은 별개** — 팀이 한 덩어리로 본 요구(②)를 코드에서 분해하니 라벨은 이미 충족, 실제 작업은 정렬뿐이었다.
2. **정렬 버그가 잘림 버그로 번진다** — `LIMIT`이 걸리는 큰 결과(AX 147)에선 정렬 순서가 곧 "무엇이 보이느냐"다. 가나다순이 핵심 교원을 100% 잘라내고 있었다. [[feedback_verify_at_output_level]] — 출력(잘린 후)으로 봐야 드러난다.
3. **검증 경로를 명시하라** — 이 머신은 CSV, 배포는 MySQL일 수 있다. "검증했다"가 어느 경로인지 적지 않으면 거짓 안심이 된다.
