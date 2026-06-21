"""다중 의도(S5) SQL 출력단계 스모크 테스트.

분류 골든(validate_rag_quality.py)은 include_sql=False라 '어떤 라벨이 붙는가'만 본다.
하지만 보조 의도/suppress 플래그의 진짜 영향은 '어떤 SQL 행이 답변 컨텍스트에 들어가는가'에서
드러난다(예: '입학 일정이랑 제출 서류'가 면접 일정 행을 누락하던 회귀).

이 스크립트는 CSV 기반 SQLTool로 결정적으로 그 행 단위 동작을 검증한다(LLM 불필요).
실행: python validation/rag_quality/sql_multi_intent_smoke.py
"""
from __future__ import annotations

import re
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


def sql_results(pipe, question: str) -> list:
    analysis = pipe.analyzer.analyze(question)
    return list(pipe._search_sql_all(analysis))


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

    # #43 절단 고지의 총계(N)는 SQL LIMIT으로 잘린 수가 아니라 진짜 매칭 수여야 한다.
    #     AX person은 캡(100)을 초과하므로 total_available>100이고, 컨텍스트 고지의
    #     N이 그 진짜 총계와 같아야 한다('총 100개'라 거짓 단정하던 ① 회귀 방지).
    q = "AX학과 교수 이메일이랑 담당 과목 알려줘"
    person = next((r for r in sql_results(pipe, q) if r.table_name == "person"), None)
    ctx = build_context(pipe, q)
    person_notice = [
        int(n)
        for n, _ in re.findall(r"총 (\d+)개 중 (\d+)개만 표시", ctx)
    ]
    true_total = getattr(person, "total_available", None) if person else None
    cap = pipe.sql_retriever._limit()
    check("#43 notice reports true total, not SQL cap",
          true_total is not None
          and true_total > cap
          and true_total in person_notice
          and cap not in person_notice,
          f"total_available={true_total} > cap={cap}, 고지 N={person_notice} (캡 아님)")

    # #44 두 큰 표(person 147 + course 145)가 예산을 공정하게 나눠야 한다.
    #     과거엔 첫 표(course)가 독식해 person이 굶었다(② 불공정). 섹션 문자 길이
    #     비율이 균형(min/max ≥ 0.7)이면 어느 표도 굶지 않은 것 — 첫 표 독식이
    #     재발하면 비율이 크게 떨어져 잡힌다.
    sql_ctx = _CONTEXT_BUILDER.build(
        pipe.analyzer.analyze(q), vector_result=None, sql_result=sql_results(pipe, q)
    ).sql_context
    sections = [
        len(sec)
        for sec in sql_ctx.split("[SQL 조회 결과]")
        if "raw_table" in sec
    ]
    ratio = (min(sections) / max(sections)) if len(sections) >= 2 else 1.0
    check("#44 budget split is fair across tables",
          len(sections) >= 2 and ratio >= 0.7,
          f"섹션 문자 길이 {sections}, min/max={ratio:.2f} (≥0.7=굶주림 없음)")

    # #45~ total_available 정확성을 person(#43) 외 경로(course/asset)까지 잠근다.
    #     오라클: SQL 캡(max_rows)을 크게 올려 다시 조회한 uncapped 행수 = 캡 전 진짜
    #     매칭 수. 절단된 결과의 total_available이 이 값과 같아야 한다(데이터값 하드코딩·
    #     내부 dedup/합산 로직 복제 없이 경로별 총계 계산을 검증). ①을 모든 경로로 일반화.
    def total_available_matches_true_count(table: str, question: str) -> tuple[bool, str]:
        analysis = pipe.analyzer.analyze(question)
        capped = next((r for r in pipe._search_sql_all(analysis) if r.table_name == table), None)
        if capped is None:
            return False, f"{table} 미조회(질문 부적합)"
        old_max = pipe.sql_retriever.config.max_rows
        pipe.sql_retriever.config.max_rows = 100_000
        try:
            uncapped = next(
                (r for r in pipe._search_sql_all(analysis) if r.table_name == table), None
            )
        finally:
            pipe.sql_retriever.config.max_rows = old_max
        true_count = len(uncapped.rows) if uncapped else 0
        truncated = len(capped.rows) < true_count
        ok = truncated and capped.total_available == true_count
        return ok, (
            f"total_available={capped.total_available} == uncapped 진짜수={true_count}, "
            f"capped_rows={len(capped.rows)}, 절단={truncated}"
        )

    for case_no, (table, question) in enumerate(
        [
            ("course", "AX학과 교수 이메일이랑 담당 과목 알려줘"),
            ("asset", "AX학과 자료 링크 알려줘"),
        ],
        start=45,
    ):
        ok, detail = total_available_matches_true_count(table, question)
        check(f"#{case_no} {table} total_available == 진짜 매칭 수(캡 전)", ok, detail)

    print(f"\n[SQL MULTI-INTENT SMOKE] {'ALL PASS' if not failures else 'FAIL: ' + ', '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
