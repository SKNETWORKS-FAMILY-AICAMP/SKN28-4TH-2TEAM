# RAG Quality Validation

이 폴더는 챗봇 품질을 한 케이스씩 임시로 고치지 않고, 질문 분류와 답변 품질을 영역별로 검증하기 위한 작업 공간입니다.

## 목적

- 질문이 올바른 `route`로 분기되는지 확인합니다.
- 질문이 올바른 `intent`와 `department_code`로 분석되는지 확인합니다.
- `clarify`가 필요한 질문과 바로 답해야 하는 질문을 구분합니다.
- 이후 답변 품질 검증에 필요한 `required_phrases`, `forbidden_phrases` 기준을 함께 관리합니다.

## 파일

- `questions.csv`: 영역별 골든 질문 목록과 기대 분류값
- `validate_rag_quality.py`: 현재 파이프라인의 질문 분류 결과를 검증하는 실행 스크립트
- `sql_multi_intent_smoke.py`: 다중 의도 질문의 **SQL 출력단계**를 행 단위로 검증하는 결정적 스모크 테스트
- `generate_question_bank.py`: 골든 질문 은행 생성 보조 스크립트
- `targeted_regression_validation.py`: 특정 회귀 케이스 표적 검증 스크립트
- `results/`, `generated/`: 실행 결과 CSV/요약 JSON, 생성 산출물 저장 위치

## 실행

> Python은 프로젝트 환경(루트 `README.md`의 환경 설정 참조)으로 실행합니다.
> 아래는 프로젝트 루트 기준 명령입니다.

### 1) 질문 분류 검증 (API 불필요)

```powershell
python validation\rag_quality\validate_rag_quality.py
```

기본 실행은 LLM 답변 생성을 하지 않고 `classify_question()` 결과만 검증합니다. 답변 생성 전 단계의 오류를 먼저 잡기 위한 설정입니다.

### 2) SQL 다중 의도 스모크 (DB/LLM 비의존)

```powershell
python validation\rag_quality\sql_multi_intent_smoke.py
```

분류 골든은 "어떤 라벨이 붙는가"만 보지만, 보조 의도·`suppress` 플래그·context 절단의 실제 영향은 **"어떤 SQL 행이 LLM context에 실리는가"**에서 드러납니다. 이 스크립트는 CSV 경로를 강제해(DB·LLM 불필요) 그 행 단위 동작을 결정적으로 검증합니다.

현재 케이스(`ALL PASS` 기대):

```text
#37~#40  다중 의도 분기 — person/event 정당 조회·오염 차단, 입학 일정 행 보존
#41      작은 학과(person 46)는 context에 전수 + 절단 고지 없음 + 표 무손상
#42      큰 결과(AX person)는 절단 고지 보존 + 표 행 경계 무손상
#43      절단 고지의 총계 N이 SQL LIMIT 캡이 아니라 진짜 매칭 수(예: 147)
#44      여러 표가 문자 예산을 공정 분할(첫 표 독식 없음, min/max ≥ 0.7)
```

## 판정 방식

각 질문은 아래 기대값을 기준으로 판정합니다.

## 판정 방식

각 질문은 아래 기대값을 기준으로 판정합니다.

- `expected_route`
- `expected_intent`
- `expected_department_code`
- `expected_content_type`
- `expected_missing_contains`
- `expected_ambiguity`

비어 있는 기대값은 판정에서 제외합니다.
