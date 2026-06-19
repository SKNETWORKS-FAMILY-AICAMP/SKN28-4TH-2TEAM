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
- `results/`: 실행 결과 CSV와 요약 JSON 저장 위치

## 실행

```powershell
C:\Users\shyej\miniforge3\python.exe validation\rag_quality\validate_rag_quality.py
```

기본 실행은 LLM 답변 생성을 하지 않고 `classify_question()` 결과만 검증합니다. 답변 생성 전 단계의 오류를 먼저 잡기 위한 설정입니다.

## 판정 방식

각 질문은 아래 기대값을 기준으로 판정합니다.

- `expected_route`
- `expected_intent`
- `expected_department_code`
- `expected_content_type`
- `expected_missing_contains`
- `expected_ambiguity`

비어 있는 기대값은 판정에서 제외합니다.
