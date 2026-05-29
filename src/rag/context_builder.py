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
from src.rag.vector_retriever import VectorRetrievalResult, RetrievedVectorDocument


@dataclass
class ContextBuilderConfig:
    max_vector_docs: int = 5
    max_sql_rows: int = 30
    max_chars_per_vector_doc: int = 1500
    include_debug_info: bool = True


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context,
            "vector_context": self.vector_context,
            "sql_context": self.sql_context,
            "sources": [source.to_dict() for source in self.sources],
            "warnings": self.warnings,
        }


class ContextBuilder:
    def __init__(self, config: ContextBuilderConfig | None = None) -> None:
        self.config = config or ContextBuilderConfig()

    def build(
        self,
        analysis: QueryAnalysis,
        vector_result: VectorRetrievalResult | None = None,
        sql_result: SqlQueryResult | None = None,
    ) -> BuiltContext:
        vector_context = self._build_vector_context(vector_result)
        sql_context = self._build_sql_context(sql_result)

        warnings = self._collect_warnings(
            vector_result=vector_result,
            sql_result=sql_result,
        )

        sources = self._collect_sources(
            vector_result=vector_result,
            sql_result=sql_result,
        )

        context_parts = [
            self._build_question_context(analysis),
            sql_context,
            vector_context,
        ]

        context = "\n\n".join(
            part
            for part in context_parts
            if part.strip()
        )

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
            "[질문 분석]\n"
            f"route: {analysis.route}\n"
            f"intent: {analysis.intent}\n"
            f"department: {analysis.department_name or 'unknown'}\n"
            f"content_type: {analysis.content_type or 'unknown'}"
        )

    def _build_vector_context(
        self,
        vector_result: VectorRetrievalResult | None,
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
        item: RetrievedVectorDocument,
    ) -> str:
        document = item.document
        metadata = document.metadata

        department = metadata.get("dept_name") or metadata.get("department") or ""
        content_type = metadata.get("content_type") or metadata.get("doc_type") or ""
        title = metadata.get("title") or ""
        source = metadata.get("source") or metadata.get("source_url") or ""

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
            f"{debug_lines}"
            f"내용:\n{content}"
        )

    def _build_sql_context(
        self,
        sql_result: SqlQueryResult | None,
    ) -> str:
        if sql_result is None:
            return ""

        if sql_result.is_empty():
            return (
                "[SQL 조회 결과]\n"
                f"table: {sql_result.table_name}\n"
                "조회된 행이 없습니다."
            )

        columns = self._get_sql_columns(sql_result)
        rows = sql_result.rows[: self.config.max_sql_rows]

        lines = [
            "[SQL 조회 결과]",
            f"table: {sql_result.table_name}",
        ]

        if sql_result.conditions:
            lines.append(f"conditions: {sql_result.conditions}")

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
        vector_result: VectorRetrievalResult | None,
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
        vector_result: VectorRetrievalResult | None,
        sql_result: SqlQueryResult | None,
    ) -> list[SourceItem]:
        sources = []

        if vector_result:
            for item in vector_result.results:
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
        item: RetrievedVectorDocument,
    ) -> SourceItem:
        metadata = item.document.metadata

        return SourceItem(
            source_type="vector",
            title=str(metadata.get("title") or ""),
            source=str(metadata.get("source") or metadata.get("source_url") or ""),
            department=str(metadata.get("dept_name") or metadata.get("department") or ""),
            content_type=str(metadata.get("content_type") or metadata.get("doc_type") or ""),
            metadata={
                "search_stage": item.search_stage,
                "score": item.score,
                "rerank_score": item.rerank_score,
                "dept": metadata.get("dept"),
                "content_type": metadata.get("content_type"),
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
            )

            if key in seen:
                continue

            seen.add(key)
            results.append(source)

        return results


def run_examples() -> None:
    from src.rag.vector_retriever import VectorRetriever

    retriever = VectorRetriever()
    builder = ContextBuilder()

    question = "AI컴퓨팅학과 학과설명회 정보 알려줘"

    vector_result = retriever.retrieve(question)
    analysis = vector_result.analysis

    built_context = builder.build(
        analysis=analysis,
        vector_result=vector_result,
    )

    print(built_context.context)
    print("\n[SOURCES]")
    print([source.to_dict() for source in built_context.sources])
    print("\n[WARNINGS]")
    print(built_context.warnings)


if __name__ == "__main__":
    run_examples()