from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT_FROM_FILE = CURRENT_FILE.parents[3]
SRC_DIR = CURRENT_FILE.parents[2]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from kaist_rag.rag.query_analyzer import QueryAnalysis


# LLM 답변 생성에 무의미한 메타/식별자 컬럼.
# 토큰만 소모하고 표 가독성을 떨어뜨린다(예: person 18컬럼 중 절반이 메타라
# 학과 교수 46명이 12000자 문자 캡에 걸려 30명으로 잘렸다). raw rows/columns
# 원본은 보존하고, LLM 컨텍스트 문자열을 만들 때만 제외한다.
# `*_id`(내부 PK)는 패턴으로 별도 처리한다.
_SQL_CONTEXT_NOISE_COLUMNS = frozenset(
    {
        "source_url",
        "crawled_at",
        "missing_fields",
        "image_url",
        "dept",  # dept_name과 중복(코드)
        "raw_values",  # courses 원시 덤프
    }
)


@dataclass
class ContextBuilderConfig:
    max_vector_docs: int = 5
    # 행 개수 캡은 조잡한 프록시다. 실질 절단은 문자 예산(max_total_context_chars)을
    # 행 경계에서 적용하는 _build_sql_context가 담당한다(중간 절단 방지 + 고지 보존).
    # 행 캡은 SQL 단(sql_tool.max_rows=100)과 정합하는 상한으로만 둔다.
    max_sql_rows: int = 100
    max_chars_per_vector_doc: int = 1500
    max_total_context_chars: int = 12000
    include_debug_info: bool = False
    include_question_analysis: bool = False


@dataclass
class SqlQueryResult:
    table_name: str
    rows: list[dict[str, Any]]
    columns: list[str] = field(default_factory=list)
    conditions: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    warnings: list[str] = field(default_factory=list)
    # LIMIT(SQL 캡)을 적용하기 전의 진짜 매칭 행 수. None이면 미상 → 절단 고지는
    # len(rows)로 후퇴한다. 이 값이 있으면 고지가 "총 N개 중 M개"의 N을 캡으로
    # 잘린 수가 아니라 실제 총계로 말한다(SQL 캡 침묵까지 정직하게 드러냄).
    total_available: int | None = None

    def is_empty(self) -> bool:
        return len(self.rows) == 0


@dataclass
class SourceItem:
    source_type: str
    title: str = ""
    source: str = ""
    department: str = ""
    content_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BuiltContext:
    context: str
    vector_context: str = ""
    sql_context: str = ""
    sources: list[SourceItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_evidence(self) -> bool:
        return bool(self.sources)

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context,
            "vector_context": self.vector_context,
            "sql_context": self.sql_context,
            "sources": [source.to_dict() for source in self.sources],
            "warnings": self.warnings,
            "has_evidence": self.has_evidence,
        }


class ContextBuilder:
    def __init__(self, config: ContextBuilderConfig | None = None) -> None:
        self.config = config or ContextBuilderConfig()

    def build(
        self,
        analysis: QueryAnalysis,
        vector_result: Any | None = None,
        sql_result: SqlQueryResult | list[SqlQueryResult] | None = None,
    ) -> BuiltContext:
        sql_results = self._normalize_sql_results(sql_result)

        vector_context = self._build_vector_context(vector_result)
        # SQL은 구조화 근거라 문자 예산을 우선 배정한다. 표를 행 경계에서 자르고
        # 고지를 보존하려면 각 표가 '남은 예산'을 알아야 한다. SQL 섹션은 context에서
        # vector보다 앞에 놓이므로(아래 context_parts), 최후 안전망 _limit_context가
        # 잘라도 SQL 표와 고지는 보존된다.
        sql_context = "\n\n".join(self._build_sql_contexts_fair(sql_results))
        warnings = self._collect_warnings(
            vector_result=vector_result,
            sql_results=sql_results,
        )
        # fallback으로 가져온 vector 문서는 원래 질문 의도와 다를 수 있으므로
        # warning 목록뿐 아니라 실제 LLM context에도 명시한다.
        if vector_result and getattr(vector_result, "used_fallback", False):
            vector_context = self._prepend_fallback_warning_to_context(
                vector_context=vector_context,
                analysis=analysis,
            )
        sources = self._collect_sources(
            vector_result=vector_result,
            sql_results=sql_results,
        )
        context_parts = []
        if self.config.include_question_analysis:
            context_parts.append(self._build_question_context(analysis))
        context_parts.extend([sql_context, vector_context])
        context = "\n\n".join(
            part
            for part in context_parts
            if part.strip()
        )
        context = self._limit_context(context)
        if not context.strip():
            context = "사용 가능한 검색 결과가 없습니다."
        return BuiltContext(
            context=context,
            vector_context=vector_context,
            sql_context=sql_context,
            sources=sources,
            warnings=warnings,
        )

    def _build_question_context(self, analysis: QueryAnalysis) -> str:
        return (
            "<internal_question_analysis>\n"
            "이 블록은 라우팅과 답변 형식 결정을 위한 내부 분석입니다.\n"
            "사실 근거로 사용하지 마세요.\n"
            f"route: {analysis.route}\n"
            f"intent: {analysis.intent}\n"
            f"department: {analysis.department_name or 'unknown'}\n"
            f"content_type: {analysis.content_type or 'unknown'}\n"
            "</internal_question_analysis>"
        )

    def _prepend_fallback_warning_to_context(
        self,
        vector_context: str,
        analysis: QueryAnalysis,
    ) -> str:
        if not vector_context.strip():
            return vector_context

        expected_content_type = analysis.content_type or "unknown"

        warning = (
            "[검색 주의]\n"
            f"원래 질문에서 기대한 문서유형은 '{expected_content_type}'입니다.\n"
            "하지만 해당 조건과 정확히 일치하는 검색 결과가 부족하여 fallback 검색 결과가 포함되었습니다.\n"
            "아래 Vector 문서는 보조 참고 자료일 수 있으며, 질문과 직접 관련 없는 문서유형이 섞여 있을 수 있습니다.\n"
            "답변을 생성할 때는 원 질문과 직접 관련된 근거만 사용하고, 근거가 부족하면 부족하다고 명시하세요."
        )

        return f"{warning}\n\n{vector_context}"

    def _build_vector_context(
        self,
        vector_result: Any | None,
    ) -> str:
        if vector_result is None:
            return ""

        if not vector_result.results:
            return "[Vector 검색 결과]\n검색된 문서가 없습니다."

        blocks = ["[Vector 검색 결과]"]

        selected_items = vector_result.results[: self.config.max_vector_docs]

        for index, item in enumerate(selected_items, start=1):
            blocks.append(
                self._format_vector_item(
                    index=index,
                    item=item,
                )
            )

        return "\n\n".join(blocks)

    def _format_vector_item(
        self,
        index: int,
        item: Any,
    ) -> str:
        document = item.document
        metadata = document.metadata

        department = metadata.get("dept_name") or metadata.get("department") or ""
        content_type = metadata.get("content_type") or metadata.get("doc_type") or ""
        title = metadata.get("title") or ""
        source = metadata.get("source_url") or metadata.get("source") or metadata.get("url") or ""
        crawled_at = metadata.get("crawled_at") or ""

        content = document.page_content

        if len(content) > self.config.max_chars_per_vector_doc:
            content = (
                content[: self.config.max_chars_per_vector_doc]
                .rstrip()
                + "\n...[중략]"
            )

        debug_lines = ""

        if self.config.include_debug_info:
            debug_lines = (
                f"검색단계: {item.search_stage}\n"
                f"vector_score: {item.score}\n"
                f"rerank_score: {item.rerank_score}\n"
            )

        return (
            f"[문서 {index}]\n"
            f"학과: {department}\n"
            f"문서유형: {content_type}\n"
            f"제목: {title}\n"
            f"출처: {source}\n"
            f"수집일: {crawled_at or 'unknown'}\n"
            f"{self._format_optional_metadata(metadata)}"
            f"{debug_lines}"
            f"내용:\n{content}"
        )

    def _format_optional_metadata(
        self,
        metadata: dict[str, Any],
    ) -> str:
        field_map = [
            ("file_name", "파일명"),
            ("section", "섹션"),
            ("page", "페이지"),
            ("chunk_index", "청크"),
            ("course_code", "과목코드"),
            ("course_type", "이수구분"),
            ("role", "역할"),
            ("email", "이메일"),
            ("homepage", "홈페이지"),
            ("event_date", "행사일"),
        ]

        lines = []

        for key, label in field_map:
            value = metadata.get(key)

            if value:
                lines.append(f"{label}: {value}")

        if not lines:
            return ""

        return "\n".join(lines) + "\n"

    def _get_sql_table_label(self, table_name: str) -> str:
        table_name_map = {
            "admissions": "입학 정보",
            "admission": "입학 정보",
            "courses": "교과목 정보",
            "course": "교과목 정보",
            "course_track_map": "교과목-트랙 매핑 정보",
            "department": "KAIST 학과/프로그램 목록",
            "people": "교수진/구성원 정보",
            "professors": "교수진/구성원 정보",
            "person": "교수진/구성원 정보",
            "office_contacts": "학과 사무실 연락처",
            "department_offices": "학과 사무실 연락처",
            "department_office": "학과 사무실 연락처",
            "events": "행사/공지 정보",
            "event": "행사/공지 정보",
            "assets": "자료/링크 정보",
            "asset": "자료/링크 정보",
            "attachment": "첨부파일/PDF 정보",
            "attachments": "첨부파일/PDF 정보",
            "kaist_profile": "KAIST 기본 정보",
            "kaist_statistics": "KAIST 통계 정보",
            "kaist_links": "KAIST 공식 링크 정보",
            "kaist_link": "KAIST 공식 링크 정보",
        }

        return table_name_map.get(table_name, table_name)

    def _build_sql_contexts_fair(
        self,
        sql_results: list[SqlQueryResult],
    ) -> list[str]:
        """여러 SQL 표에 문자 예산을 공정하게 배분해 컨텍스트 조각들을 만든다.

        과거에는 첫 표가 예산을 독식해(_search_sql_all이 먼저 주는 표가 이김)
        뒤 표가 굶었다(예: course가 person을 42행으로 굶김 — 사용자가 '이메일'을
        먼저 말해도). 여기서는 **작은 표부터** `남은예산 // 남은표수`로 할당한다:
        작은 표가 남긴 예산이 큰 표로 흘러 어느 표도 굶지 않고, 배분이 순서에
        의존하지 않는다(표시는 원래 순서를 유지해 배분 공정성과 표시순서를 분리).

        빈 결과('조회된 행 없음')는 작으니 먼저 렌더해 공정 몫에서 제외한다.
        """
        parts_by_index: dict[int, str] = {}
        remaining = self.config.max_total_context_chars
        gap = len("\n\n")

        indexed = list(enumerate(sql_results))
        empty = [(i, r) for i, r in indexed if r is None or r.is_empty()]
        nonempty = [(i, r) for i, r in indexed if r is not None and not r.is_empty()]

        for i, result in empty:
            part = self._build_sql_context(result, char_budget=max(remaining, 0))
            parts_by_index[i] = part
            if part.strip():
                remaining -= len(part) + gap

        # 작은 표부터: 적게 쓰고 남긴 몫이 뒤(큰 표)의 분모에서 더 큰 1인분이 된다.
        for position, (i, result) in enumerate(
            sorted(nonempty, key=lambda pair: len(pair[1].rows))
        ):
            tables_left = len(nonempty) - position
            share = max(remaining, 0) // tables_left if tables_left else max(remaining, 0)
            part = self._build_sql_context(result, char_budget=share)
            parts_by_index[i] = part
            if part.strip():
                remaining -= len(part) + gap

        return [
            parts_by_index[i]
            for i in sorted(parts_by_index)
            if parts_by_index[i].strip()
        ]

    # 절단 고지가 문자 예산 경계에서 잘려나가지 않도록 떼어 두는 여유분.
    _SQL_NOTICE_RESERVE_CHARS = 90

    def _build_sql_context(
        self,
        sql_result: SqlQueryResult | None,
        char_budget: int | None = None,
    ) -> str:
        if sql_result is None:
            return ""

        if sql_result.is_empty():
            table_label = self._get_sql_table_label(sql_result.table_name)

            return (
                "[SQL 조회 결과]\n"
                f"table: {table_label}\n"
                f"raw_table: {sql_result.table_name}\n"
                "조회된 행이 없습니다."
            )

        if char_budget is None or char_budget <= 0:
            char_budget = self.config.max_total_context_chars

        columns = self._get_sql_columns(sql_result)
        capped_rows = sql_result.rows[: self.config.max_sql_rows]

        table_label = self._get_sql_table_label(sql_result.table_name)

        lines = [
            "[SQL 조회 결과]",
            f"table: {table_label}",
            f"raw_table: {sql_result.table_name}",
        ]

        if sql_result.conditions:
            lines.append(f"조회 조건: {sql_result.conditions}")

        lines.append("")
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("| " + " | ".join(["---"] * len(columns)) + " |")

        # 행은 반드시 행 경계에서만 자른다(마크다운 표 중간 절단 금지). 문자 예산을
        # 넘으면 거기서 멈추고, 잘린 경우 고지를 표 직후에 남겨 '부분→전체' 오인을
        # 막는다. 최소 1행은 보장한다(빈 표 방지).
        displayed = 0
        for row in capped_rows:
            row_line = "| " + " | ".join(
                self._safe_cell(row.get(column, ""))
                for column in columns
            ) + " |"

            projected = len("\n".join(lines)) + 1 + len(row_line)

            if displayed > 0 and (
                projected + self._SQL_NOTICE_RESERVE_CHARS > char_budget
            ):
                break

            lines.append(row_line)
            displayed += 1

        # 고지의 N은 '문자 예산으로 잘린 수(len(rows))'가 아니라 'SQL LIMIT 전
        # 진짜 매칭 수'여야 한다. total_available이 있으면 그걸 쓴다 → displayed가
        # SQL 캡(100)과 같아도 total>displayed면 고지가 남아 캡 침묵을 드러낸다.
        # (안전망: total_available이 표시 행수보다 작게 들어오면 len(rows)로 보정)
        total = max(sql_result.total_available or 0, len(sql_result.rows))

        if displayed < total:
            lines.append(
                f"\n...총 {total}개 중 {displayed}개만 표시"
                "(길이 제한 — 학과/조건을 좁혀 다시 물으면 전체를 볼 수 있습니다)"
            )

        return "\n".join(lines)

    def _get_sql_columns(
        self,
        sql_result: SqlQueryResult,
    ) -> list[str]:
        if sql_result.columns:
            ordered_columns = list(sql_result.columns)
        else:
            ordered_columns = []

            for row in sql_result.rows:
                for key in row.keys():
                    if key not in ordered_columns:
                        ordered_columns.append(key)

        pruned = [
            column
            for column in ordered_columns
            if not self._is_context_noise_column(column)
        ]

        # 전부 메타로 걸러지면(이론상) 원본을 그대로 쓴다.
        return pruned or ordered_columns

    def _is_context_noise_column(self, column: str) -> bool:
        if column == "record_id" or column.endswith("_id"):
            return True

        return column in _SQL_CONTEXT_NOISE_COLUMNS

    def _safe_cell(self, value: Any) -> str:
        if value is None:
            return ""

        text = str(value)
        text = text.replace("\n", " ").replace("|", "/")

        return text.strip()

    def _normalize_sql_results(
        self,
        sql_result: SqlQueryResult | list[SqlQueryResult] | None,
    ) -> list[SqlQueryResult]:
        if sql_result is None:
            return []

        if isinstance(sql_result, list):
            return [result for result in sql_result if result is not None]

        return [sql_result]

    def _collect_warnings(
        self,
        vector_result: Any | None,
        sql_results: list[SqlQueryResult],
    ) -> list[str]:
        warnings = []

        if vector_result:
            warnings.extend(vector_result.warnings)

            if vector_result.used_fallback:
                warnings.append(
                    "Vector 검색에서 fallback이 사용되었습니다. "
                    "일부 문서는 원 질문의 문서유형과 다를 수 있습니다."
                )

        for sql_result in sql_results:
            warnings.extend(sql_result.warnings)

        return self._deduplicate_strings(warnings)

    def _collect_sources(
        self,
        vector_result: Any | None,
        sql_results: list[SqlQueryResult],
    ) -> list[SourceItem]:
        sources = []

        if vector_result:
            for item in vector_result.results[: self.config.max_vector_docs]:
                sources.append(
                    self._source_from_vector_item(item)
                )

        for sql_result in sql_results:
            if sql_result.is_empty():
                continue

            sources.append(
                SourceItem(
                    source_type="sql",
                    title=sql_result.table_name,
                    source=sql_result.table_name,
                    metadata={
                        "table_name": sql_result.table_name,
                        "conditions": sql_result.conditions,
                        "row_count": len(sql_result.rows),
                    },
                )
            )

        return self._deduplicate_sources(sources)

    def _source_from_vector_item(
        self,
        item: Any,
    ) -> SourceItem:
        metadata = item.document.metadata

        return SourceItem(
            source_type="vector",
            title=str(metadata.get("title") or ""),
            source=str(
                metadata.get("source_url")
                or metadata.get("source")
                or metadata.get("url")
                or ""
            ),
            department=str(metadata.get("dept_name") or metadata.get("department") or ""),
            content_type=str(metadata.get("content_type") or metadata.get("doc_type") or ""),
            metadata={
                "search_stage": item.search_stage,
                "score": item.score,
                "rerank_score": item.rerank_score,
                "dept": metadata.get("dept"),
                "content_type": metadata.get("content_type"),
                "crawled_at": metadata.get("crawled_at"),
                "page": metadata.get("page"),
                "file_name": metadata.get("file_name"),
                "section": metadata.get("section"),
                "chunk_index": metadata.get("chunk_index"),
                "source_url": metadata.get("source_url"),
            },
        )

    def _deduplicate_strings(
        self,
        values: list[str],
    ) -> list[str]:
        seen = set()
        results = []

        for value in values:
            if not value:
                continue

            if value in seen:
                continue

            seen.add(value)
            results.append(value)

        return results

    def _deduplicate_sources(
        self,
        sources: list[SourceItem],
    ) -> list[SourceItem]:
        seen = set()
        results = []

        for source in sources:
            key = (
                source.source_type,
                source.title,
                source.source,
                source.department,
                source.content_type,
                source.metadata.get("page"),
                source.metadata.get("chunk_index"),
            )

            if key in seen:
                continue

            seen.add(key)
            results.append(source)

        return results

    def _limit_context(self, context: str) -> str:
        if self.config.max_total_context_chars <= 0:
            return context

        if len(context) <= self.config.max_total_context_chars:
            return context

        return (
            context[: self.config.max_total_context_chars]
            .rstrip()
            + "\n...[전체 context 길이 제한으로 중략]"
        )

