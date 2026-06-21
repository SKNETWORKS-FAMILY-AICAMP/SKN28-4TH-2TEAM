"""다중 의도(S5) SQL 출력단계 스모크 테스트.

분류 골든(validate_rag_quality.py)은 include_sql=False라 '어떤 라벨이 붙는가'만 본다.
하지만 보조 의도/suppress 플래그의 진짜 영향은 '어떤 SQL 행이 답변 컨텍스트에 들어가는가'에서
드러난다(예: '입학 일정이랑 제출 서류'가 면접 일정 행을 누락하던 회귀).

이 스크립트는 CSV 기반 SQLTool로 결정적으로 그 행 단위 동작을 검증한다(LLM 불필요).
실행: python validation/rag_quality/sql_multi_intent_smoke.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.context_builder import ContextBuilder
from src.rag.rag_pipeline import create_default_pipeline

_CONTEXT_BUILDER = ContextBuilder()


def tables(pipe, question: str) -> dict[str, list[dict]]:
    analysis = pipe.analyzer.analyze(question)
    out: dict[str, list[dict]] = {}
    for result in pipe._search_sql_all(analysis):
        out[result.table_name] = list(result.rows or [])
    return out


def build_context(pipe, question: str) -> str:
    """LLM에 실제로 들어가는 컨텍스트 문자열을 만든다.

    분류 골든은 라벨만, 위 tables()는 raw SQL 행만 본다. 둘 다 'raw 행이
    컨텍스트에 온전히·정직하게 실리는가'(행 경계 절단, 절단 고지, 컬럼 프루닝)는
    검증하지 못한다 — 실제로 person 46행이 컨텍스트 단계에서 30행으로 잘리던
    버그를 raw 검사가 놓쳤다. 이 헬퍼가 그 사각지대를 메운다.
    """
    analysis = pipe.analyzer.analyze(question)
    sql_results = list(pipe._search_sql_all(analysis))
    built = _CONTEXT_BUILDER.build(
        analysis,
        vector_result=None,
        sql_result=sql_results,
    )
    return built.context


def table_rows_well_formed(context: str) -> bool:
    """마크다운 표 행이 행 경계에서만 잘렸는지(중간 절단 없음)."""
    return all(
        line.rstrip().endswith("|")
        for line in context.splitlines()
        if line.startswith("|")
    )


def schedule_titles(rows: list[dict]) -> set[str]:
    return {
        row.get("title", "")
        for row in rows
        if row.get("admission_type") == "admission_schedule"
    }


def main() -> int:
    pipe = create_default_pipeline(include_sql=True)
    if pipe.sql_retriever is None:
        print("[SKIP] SQL retriever 사용 불가(CSV 경로 확인). 검증 생략.")
        return 0

    # 결정적·DB 비의존 검증을 위해 CSV 경로를 강제한다(레포 내 CSV만 사용).
    # MySQL 경로도 동일한 _specific_keywords(suppress) 계약을 공유하므로
    # CSV 통과가 MySQL 동작의 대리 검증이 된다.
    pipe.sql_retriever.config.mysql_configured = lambda: False

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str) -> None:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} — {detail}")
        if not ok:
            failures.append(name)

    # #38 '홈페이지'가 person 보조의도로 오귀속되지 않아야 → person 미조회
    t = tables(pipe, "AI컴퓨팅학과 교과목이랑 홈페이지 링크 알려줘")
    check("#38 no person", "person" not in t,
          f"person 미조회(교수 오염 차단). tables={sorted(t)}")

    # #39 '입학 일정'이 event로 오귀속되지 않고, 접속질문이라 키워드필터를 꺼
    #     입학 일정 행(원서접수+면접)을 모두 보존해야 한다.
    t = tables(pipe, "AX학과 입학 일정이랑 제출 서류 알려줘")
    titles = schedule_titles(t.get("admission", []))
    check("#39 no event", "event" not in t, f"event 미조회. tables={sorted(t)}")
    check("#39 schedules complete",
          {"원서접수(서류제출 포함)", "2단계 전형(면접)"} <= titles,
          f"입학 일정 행 보존: {sorted(titles)}")

    # #37 정당한 다중의도: person 조회 보존
    t = tables(pipe, "AI시스템학과 교수 이메일이랑 담당 과목 알려줘")
    check("#37 person retrieved", len(t.get("person", [])) > 0,
          f"person rows={len(t.get('person', []))}")

    # #40 정당한 event(설명회 단서): event 보존
    t = tables(pipe, "AX학과 설명회 일정이랑 교수 이메일 알려줘")
    check("#40 event retrieved", "event" in t, f"tables={sorted(t)}")

    # ── 컨텍스트 단계 검증(raw 행 ≠ 컨텍스트 행 사각지대) ──────────────
    # #41 작은 학과(AI시스템 person 46행)는 컨텍스트에 전수가 실려야 하고,
    #     문자 캡 안에 들어가므로 절단 고지가 없어야 한다.
    q = "AI시스템학과 교수 이메일이랑 담당 과목 알려줘"
    person_rows = tables(pipe, q).get("person", [])
    ctx = build_context(pipe, q)
    emails = [r.get("email", "") for r in person_rows if r.get("email")]
    in_ctx = sum(1 for e in emails if e and e in ctx)
    check("#41 small dept full in context",
          len(emails) > 0 and in_ctx == len(emails) and "개만 표시" not in ctx,
          f"emails {in_ctx}/{len(emails)} 컨텍스트 포함, 절단고지 없음")
    check("#41 table not mid-row truncated", table_rows_well_formed(ctx),
          "모든 표 행이 행 경계에서 종료(중간 절단 없음)")

    # #42 큰 결과(AX person)는 문자 예산으로 일부만 실리되, (a) 표가 행 중간에서
    #     깨지지 않고 (b) 절단 고지가 컨텍스트에 보존돼야 한다('부분→전체' 오인 방지).
    q = "AX학과 교수 이메일이랑 담당 과목 알려줘"
    ctx = build_context(pipe, q)
    check("#42 large result keeps notice", "개만 표시" in ctx,
          f"절단 고지 보존(ctx_len={len(ctx)})")
    check("#42 table not mid-row truncated", table_rows_well_formed(ctx),
          "표 행 경계 보존(중간 절단 없음)")

    print(f"\n[SQL MULTI-INTENT SMOKE] {'ALL PASS' if not failures else 'FAIL: ' + ', '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
