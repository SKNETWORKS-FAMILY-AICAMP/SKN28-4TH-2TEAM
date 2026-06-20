from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
DEFAULT_QUESTIONS_PATH = CURRENT_FILE.parent / "questions.csv"
DEFAULT_RESULTS_DIR = CURRENT_FILE.parent / "results"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.rag_pipeline import create_default_pipeline


@dataclass
class ValidationCase:
    id: str
    category: str
    question: str
    previous_department_code: str
    expected_route: str
    expected_intent: str
    expected_department_code: str
    expected_content_type: str
    expected_intents: str
    expected_missing_contains: str
    expected_ambiguity: str
    required_phrases: str
    forbidden_phrases: str
    notes: str


@dataclass
class ValidationResult:
    id: str
    category: str
    question: str
    previous_department_code: str
    expected_route: str
    actual_route: str
    route_ok: bool | None
    expected_intent: str
    actual_intent: str
    intent_ok: bool | None
    expected_department_code: str
    actual_department_code: str
    department_ok: bool | None
    expected_content_type: str
    actual_content_type: str
    content_type_ok: bool | None
    expected_intents: str
    actual_intents: str
    intents_ok: bool | None
    expected_missing_contains: str
    actual_missing_fields: str
    missing_ok: bool | None
    expected_ambiguity: str
    actual_ambiguity: str
    ambiguity_ok: bool | None
    status: str
    failure_reasons: str
    route_reason: str
    metadata_filter: str
    sql_table_hint: str
    sql_task_hint: str
    notes: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate RAG question classification quality."
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=DEFAULT_QUESTIONS_PATH,
        help="CSV file containing validation questions.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Directory to store validation results.",
    )
    return parser.parse_args()


def load_cases(path: Path) -> list[ValidationCase]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [
            ValidationCase(
                id=row.get("id", "").strip(),
                category=row.get("category", "").strip(),
                question=row.get("question", "").strip(),
                previous_department_code=row.get("previous_department_code", "").strip(),
                expected_route=row.get("expected_route", "").strip(),
                expected_intent=row.get("expected_intent", "").strip(),
                expected_department_code=row.get("expected_department_code", "").strip(),
                expected_content_type=row.get("expected_content_type", "").strip(),
                expected_intents=row.get("expected_intents", "").strip(),
                expected_missing_contains=row.get("expected_missing_contains", "").strip(),
                expected_ambiguity=row.get("expected_ambiguity", "").strip(),
                required_phrases=row.get("required_phrases", "").strip(),
                forbidden_phrases=row.get("forbidden_phrases", "").strip(),
                notes=row.get("notes", "").strip(),
            )
            for row in reader
        ]


def split_expected(value: str) -> list[str]:
    return [
        item.strip()
        for item in value.split(";")
        if item.strip()
    ]


def check_expected(expected: str, actual: str | None) -> bool | None:
    if not expected:
        return None
    return (actual or "") == expected


def check_missing_fields(expected: str, actual_missing_fields: list[str]) -> bool | None:
    expected_fields = split_expected(expected)
    if not expected_fields:
        return None
    actual_set = set(actual_missing_fields)
    return all(field in actual_set for field in expected_fields)


def check_intents(expected: str, actual_intents: list[str]) -> bool | None:
    # 다중 정보유형(intents) 집합을 순서 무관하게 정확히 일치 검사한다.
    expected_set = set(split_expected(expected))
    if not expected_set:
        return None
    return expected_set == set(actual_intents)


def collect_failure_reasons(
    checks: list[tuple[str, bool | None]],
) -> list[str]:
    return [
        name
        for name, passed in checks
        if passed is False
    ]


def validate_cases(cases: list[ValidationCase]) -> list[ValidationResult]:
    pipeline = create_default_pipeline(include_sql=False)
    results: list[ValidationResult] = []

    for case in cases:
        previous_department_code = case.previous_department_code or None
        analysis = pipeline.classify_question(
            case.question,
            previous_department_code=previous_department_code,
        )

        route_ok = check_expected(case.expected_route, analysis.route)
        intent_ok = check_expected(case.expected_intent, analysis.intent)
        department_ok = check_expected(
            case.expected_department_code,
            analysis.department_code,
        )
        content_type_ok = check_expected(
            case.expected_content_type,
            analysis.content_type,
        )
        intents_ok = check_intents(
            case.expected_intents,
            analysis.intents,
        )
        missing_ok = check_missing_fields(
            case.expected_missing_contains,
            analysis.missing_fields,
        )
        ambiguity_ok = check_expected(
            case.expected_ambiguity,
            analysis.ambiguity_type,
        )

        checks = [
            ("route", route_ok),
            ("intent", intent_ok),
            ("department_code", department_ok),
            ("content_type", content_type_ok),
            ("intents", intents_ok),
            ("missing_fields", missing_ok),
            ("ambiguity_type", ambiguity_ok),
        ]
        failure_reasons = collect_failure_reasons(checks)
        status = "PASS" if not failure_reasons else "FAIL"

        results.append(
            ValidationResult(
                id=case.id,
                category=case.category,
                question=case.question,
                previous_department_code=case.previous_department_code,
                expected_route=case.expected_route,
                actual_route=analysis.route,
                route_ok=route_ok,
                expected_intent=case.expected_intent,
                actual_intent=analysis.intent,
                intent_ok=intent_ok,
                expected_department_code=case.expected_department_code,
                actual_department_code=analysis.department_code or "",
                department_ok=department_ok,
                expected_content_type=case.expected_content_type,
                actual_content_type=analysis.content_type or "",
                content_type_ok=content_type_ok,
                expected_intents=case.expected_intents,
                actual_intents=";".join(analysis.intents),
                intents_ok=intents_ok,
                expected_missing_contains=case.expected_missing_contains,
                actual_missing_fields=";".join(analysis.missing_fields),
                missing_ok=missing_ok,
                expected_ambiguity=case.expected_ambiguity,
                actual_ambiguity=analysis.ambiguity_type or "",
                ambiguity_ok=ambiguity_ok,
                status=status,
                failure_reasons=";".join(failure_reasons),
                route_reason=analysis.route_reason,
                metadata_filter=json.dumps(
                    analysis.metadata_filter,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                sql_table_hint=analysis.sql_table_hint or "",
                sql_task_hint=analysis.sql_task_hint or "",
                notes=case.notes,
            )
        )

    return results


def build_summary(results: list[ValidationResult]) -> dict[str, Any]:
    total = len(results)
    failed = [result for result in results if result.status == "FAIL"]
    by_category: dict[str, dict[str, int]] = {}
    by_failure_reason: dict[str, int] = {}

    for result in results:
        category_summary = by_category.setdefault(
            result.category,
            {"total": 0, "pass": 0, "fail": 0},
        )
        category_summary["total"] += 1
        category_summary["pass" if result.status == "PASS" else "fail"] += 1

        for reason in split_expected(result.failure_reasons):
            by_failure_reason[reason] = by_failure_reason.get(reason, 0) + 1

    return {
        "total": total,
        "pass": total - len(failed),
        "fail": len(failed),
        "pass_rate": round((total - len(failed)) / total, 4) if total else 0.0,
        "by_category": by_category,
        "by_failure_reason": by_failure_reason,
        "failed_cases": [
            {
                "id": result.id,
                "category": result.category,
                "question": result.question,
                "failure_reasons": result.failure_reasons,
                "expected_route": result.expected_route,
                "actual_route": result.actual_route,
                "expected_intent": result.expected_intent,
                "actual_intent": result.actual_intent,
            }
            for result in failed
        ],
    }


def write_results(
    results: list[ValidationResult],
    summary: dict[str, Any],
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = out_dir / f"classification_results_{timestamp}.csv"
    summary_path = out_dir / f"classification_summary_{timestamp}.json"

    with results_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(asdict(results[0]).keys()) if results else [],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))

    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    return results_path, summary_path


def print_summary(
    summary: dict[str, Any],
    results_path: Path,
    summary_path: Path,
) -> None:
    print("[RAG CLASSIFICATION VALIDATION]")
    print(f"total={summary['total']} pass={summary['pass']} fail={summary['fail']} pass_rate={summary['pass_rate']}")
    print(f"results={results_path}")
    print(f"summary={summary_path}")

    if summary["failed_cases"]:
        print("\n[FAILED CASES]")
        for case in summary["failed_cases"]:
            print(
                f"- #{case['id']} {case['category']} | "
                f"{case['failure_reasons']} | {case['question']} | "
                f"route {case['expected_route']} -> {case['actual_route']} | "
                f"intent {case['expected_intent']} -> {case['actual_intent']}"
            )


def main() -> None:
    args = parse_args()
    cases = load_cases(args.questions)
    results = validate_cases(cases)
    summary = build_summary(results)
    results_path, summary_path = write_results(results, summary, args.out_dir)
    print_summary(summary, results_path, summary_path)


if __name__ == "__main__":
    main()
