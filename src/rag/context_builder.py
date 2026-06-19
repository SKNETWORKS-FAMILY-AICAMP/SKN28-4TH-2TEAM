from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT_FROM_FILE = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT_FROM_FILE) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FROM_FILE))

from src.rag.query_analyzer import QueryAnalysis


@dataclass
class ContextBuilderConfig:
    max_vector_docs: int = 5
    max_sql_rows: int = 30
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
        sql_result: SqlQueryResult | None = None,
    ) -> BuiltContext:
        vector_context = self._build_vector_context(vector_result)
        sql_context = self._build_sql_context(sql_result)
        warnings = self._collect_warnings(
            vector_result=vector_result,
            sql_result=sql_result,
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
            sql_result=sql_result,
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

    def _build_sql_context(
        self,
        sql_result: SqlQueryResult | None,
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

        columns = self._get_sql_columns(sql_result)
        rows = sql_result.rows[: self.config.max_sql_rows]

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

        for row in rows:
            values = [
                self._safe_cell(row.get(column, ""))
                for column in columns
            ]
            lines.append("| " + " | ".join(values) + " |")

        if len(sql_result.rows) > self.config.max_sql_rows:
            lines.append(
                f"\n...총 {len(sql_result.rows)}개 중 "
                f"{self.config.max_sql_rows}개만 표시"
            )

        return "\n".join(lines)

    def _get_sql_columns(
        self,
        sql_result: SqlQueryResult,
    ) -> list[str]:
        if sql_result.columns:
            return sql_result.columns

        ordered_columns = []

        for row in sql_result.rows:
            for key in row.keys():
                if key not in ordered_columns:
                    ordered_columns.append(key)

        return ordered_columns

    def _safe_cell(self, value: Any) -> str:
        if value is None:
            return ""

        text = str(value)
        text = text.replace("\n", " ").replace("|", "/")

        return text.strip()

    def _collect_warnings(
        self,
        vector_result: Any | None,
        sql_result: SqlQueryResult | None,
    ) -> list[str]:
        warnings = []

        if vector_result:
            warnings.extend(vector_result.warnings)

            if vector_result.used_fallback:
                warnings.append(
                    "Vector 검색에서 fallback이 사용되었습니다. "
                    "일부 문서는 원 질문의 문서유형과 다를 수 있습니다."
                )

        if sql_result:
            warnings.extend(sql_result.warnings)

        return self._deduplicate_strings(warnings)

    def _collect_sources(
        self,
        vector_result: Any | None,
        sql_result: SqlQueryResult | None,
    ) -> list[SourceItem]:
        sources = []

        if vector_result:
            for item in vector_result.results[: self.config.max_vector_docs]:
                sources.append(
                    self._source_from_vector_item(item)
                )

        if sql_result and not sql_result.is_empty():
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

