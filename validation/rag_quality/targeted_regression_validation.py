from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
RESULTS_DIR = CURRENT_FILE.parent / "results"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.rag_pipeline import create_default_pipeline


@dataclass(frozen=True)
class Case:
    category: str
    question: str
    expected_route: str
    expected_intent: str
    expected_department_code: str = ""
    expected_ambiguity: str = ""
    expect_evidence: bool = True
    note: str = ""


CASES = [
    Case(
        "기본 AI학과 목록",
        "KAIST에 AI 학과는 어떤 게 있어?",
        "hybrid",
        "department_overview",
        note="AI 학과 표현이 clarify/general_info로 빠지지 않아야 함",
    ),
    Case(
        "학과 소개-분야",
        "AI시스템학과는 어떤 분야를 다뤄?",
        "vector",
        "department_overview",
        "ai_systems",
        note="분야/다뤄 표현을 소개 질문으로 잡아야 함",
    ),
    Case(
        "학과 소개-인재",
        "AI미래학과는 어떤 인재를 양성?",
        "vector",
        "department_overview",
        "fx",
        note="인재/양성 표현을 소개 질문으로 잡아야 함",
    ),
    Case(
        "학과 소개-교육목표",
        "AX학과 교육 목표 알려줘",
        "vector",
        "department_overview",
        "ax",
        note="교육 목표 표현을 소개 질문으로 잡아야 함",
    ),
    Case(
        "교과목 기본",
        "AI컴퓨팅학과 교과목 목록 보여줘",
        "sql",
        "course_info",
        "aic",
        note="정형 교과목 목록은 SQL 근거가 잡혀야 함",
    ),
    Case(
        "교과목 데이터 부재",
        "AI시스템학과 교과목 목록 보여줘",
        "sql",
        "course_info",
        "ai_systems",
        expect_evidence=False,
        note="AI시스템학과 교과목은 데이터 부재 케이스",
    ),
    Case(
        "교과목 비교",
        "학과별 교과목 비교해줘",
        "hybrid",
        "course_info",
        note="비교 질문이 SQL로만 과하게 가지 않아야 함",
    ),
    Case(
        "입학 지원자격",
        "AI컴퓨팅학과 석사 지원 자격은?",
        "sql",
        "admission_info",
        "aic",
        note="PDF 입학 본문이 vector 근거로 잡혀야 함",
    ),
    Case(
        "입학 제출서류",
        "AX학과 제출 서류 알려줘",
        "sql",
        "admission_info",
        "ax",
        note="제출서류 표현을 입학 질문으로 잡아야 함",
    ),
    Case(
        "교수진 이메일",
        "AX학과 교수진 이메일 목록 보여줘",
        "sql",
        "person_info",
        "ax",
        note="목록형 교수진 정보는 SQL 근거가 잡혀야 함",
    ),
    Case(
        "행정 연락처",
        "KAIST AI학과 연락처 알려줘",
        "sql",
        "office_contact_info",
        note="연락처가 person_info가 아니라 office_contact_info여야 함",
    ),
    Case(
        "자료 PDF 링크",
        "AX학과 브로슈어 pdf 링크 알려줘",
        "sql",
        "asset_or_link_info",
        "ax",
        note="첨부 PDF 링크가 asset 조회에 포함되어야 함",
    ),
    Case(
        "KAIST 통계",
        "카이스트 재학생 수 알려줘",
        "sql",
        "kaist_statistics_info",
        note="KAIST 기본 통계 CSV/MySQL 조회",
    ),
    Case(
        "KAIST 전체 학과/프로그램",
        "KAIST 학과 목록 알려줘",
        "sql",
        "department_overview",
        note="KAIST 전체 학과/프로그램 목록은 학과사무실 CSV/MySQL 기반으로 조회",
    ),
    Case(
        "단과대학별 학과/프로그램",
        "공과대학에는 어떤 학과가 있어?",
        "sql",
        "department_overview",
        note="단과대학별 학과/프로그램 질문도 정형 조직 목록에서 먼저 조회",
    ),
    Case(
        "정책-경쟁률",
        "경쟁률 알려줘",
        "clarify",
        "general_info",
        expected_ambiguity="unsupported_fact",
        expect_evidence=False,
        note="문서 근거 없는 경쟁률은 추측 금지",
    ),
    Case(
        "정책-외부대학",
        "서울대 AI학과랑 비교해줘",
        "clarify",
        "department_overview",
        expected_ambiguity="unsupported_fact",
        expect_evidence=False,
        note="외부 대학 비교는 지원 범위 밖으로 처리",
    ),
]


def bool_ok(expected: str, actual: str | None) -> bool:
    return not expected or (actual or "") == expected


def run() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = RESULTS_DIR / f"targeted_regression_results_{timestamp}.csv"
    json_path = RESULTS_DIR / f"targeted_regression_summary_{timestamp}.json"

    pipeline = create_default_pipeline(include_sql=True)
    rows: list[dict[str, Any]] = []

    for index, case in enumerate(CASES, start=1):
        started_at = perf_counter()
        search_result = pipeline.search(case.question)
        context = pipeline.build_context(
            analysis=search_result.analysis,
            vector_result=search_result.vector_result,
            sql_result=search_result.sql_result,
            warnings=search_result.warnings,
        )
        elapsed_ms = round((perf_counter() - started_at) * 1000)

        analysis = search_result.analysis
        vector_count = (
            len(search_result.vector_result.results)
            if search_result.vector_result
            else 0
        )
        sql_count = (
            len(search_result.sql_result.rows)
            if search_result.sql_result
            else 0
        )
        source_count = len(context.sources)

        route_ok = bool_ok(case.expected_route, analysis.route)
        intent_ok = bool_ok(case.expected_intent, analysis.intent)
        department_ok = bool_ok(
            case.expected_department_code,
            analysis.department_code,
        )
        ambiguity_ok = bool_ok(case.expected_ambiguity, analysis.ambiguity_type)
        evidence_ok = (
            source_count > 0
            if case.expect_evidence
            else True
        )

        checks = {
            "route": route_ok,
            "intent": intent_ok,
            "department": department_ok,
            "ambiguity": ambiguity_ok,
            "evidence": evidence_ok,
        }
        failed = [name for name, ok in checks.items() if not ok]

        rows.append({
            "id": index,
            "category": case.category,
            "question": case.question,
            "expected_route": case.expected_route,
            "actual_route": analysis.route,
            "expected_intent": case.expected_intent,
            "actual_intent": analysis.intent,
            "expected_department_code": case.expected_department_code,
            "actual_department_code": analysis.department_code or "",
            "expected_ambiguity": case.expected_ambiguity,
            "actual_ambiguity": analysis.ambiguity_type or "",
            "sql_table_hint": analysis.sql_table_hint or "",
            "sql_task_hint": analysis.sql_task_hint or "",
            "vector_count": vector_count,
            "sql_count": sql_count,
            "source_count": source_count,
            "warnings": " | ".join(context.warnings),
            "status": "PASS" if not failed else "FAIL",
            "failed_checks": ";".join(failed),
            "elapsed_ms": elapsed_ms,
            "note": case.note,
        })

    fieldnames = list(rows[0].keys())
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    passed = sum(1 for row in rows if row["status"] == "PASS")
    summary = {
        "total": total,
        "pass": passed,
        "fail": total - passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "result_csv": str(csv_path),
        "failed_cases": [
            {
                "id": row["id"],
                "category": row["category"],
                "question": row["question"],
                "failed_checks": row["failed_checks"],
                "actual_route": row["actual_route"],
                "actual_intent": row["actual_intent"],
                "actual_department_code": row["actual_department_code"],
                "actual_ambiguity": row["actual_ambiguity"],
                "vector_count": row["vector_count"],
                "sql_count": row["sql_count"],
                "source_count": row["source_count"],
            }
            for row in rows
            if row["status"] == "FAIL"
        ],
    }

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\n[case results]")
    for row in rows:
        print(
            f"{row['id']:02d}. {row['status']} | {row['category']} | "
            f"{row['actual_route']}/{row['actual_intent']} | "
            f"dept={row['actual_department_code'] or '-'} | "
            f"sql={row['sql_count']} vector={row['vector_count']} "
            f"sources={row['source_count']} | {row['question']}"
        )

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(run())
