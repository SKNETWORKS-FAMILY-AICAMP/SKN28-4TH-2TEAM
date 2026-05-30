from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.query_analyzer import QuestionAnalyzer, QueryAnalysis
from src.rag.vector_retriever import VectorRetriever, VectorRetrievalResult
from src.rag.context_builder import ContextBuilder, ContextBuilderConfig, BuiltContext
from src.rag.answer_generator import AnswerGenerator, GeneratedAnswer


@dataclass
class RAGPipelineResponse:
    answer: str
    route: str
    status: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    debug: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RAGPipeline:
    def __init__(
        self,
        analyzer: QuestionAnalyzer | None = None,
        retriever: VectorRetriever | None = None,
        context_builder: ContextBuilder | None = None,
        answer_generator: AnswerGenerator | None = None,
    ) -> None:
        self.analyzer = analyzer or QuestionAnalyzer()
        self.retriever = retriever or VectorRetriever()
        self.context_builder = context_builder or ContextBuilder(
            ContextBuilderConfig(include_debug_info=False)
        )
        self.answer_generator = answer_generator or AnswerGenerator()

    def ask(
        self,
        question: str,
        previous_department_code: str | None = None,
    ) -> RAGPipelineResponse:
        analysis = self.analyzer.analyze(
            question=question,
            previous_department_code=previous_department_code,
        )

        if analysis.route == "clarify":
            return self._clarify_response(analysis)

        if analysis.route == "sql":
            return self._sql_not_connected_response(analysis)

        vector_result = self.retriever.retrieve(
            question=question,
            previous_department_code=previous_department_code,
        )

        built_context = self.context_builder.build(
            analysis=vector_result.analysis,
            vector_result=vector_result,
            sql_result=None,
        )

        generated = self.answer_generator.generate(
            question=question,
            built_context=built_context,
            analysis=vector_result.analysis,
        )

        return self._build_response(
            analysis=vector_result.analysis,
            vector_result=vector_result,
            built_context=built_context,
            generated=generated,
        )

    def _clarify_response(self, analysis: QueryAnalysis) -> RAGPipelineResponse:
        return RAGPipelineResponse(
            answer=analysis.clarifying_message or "질문을 조금 더 구체적으로 입력해주세요.",
            route=analysis.route,
            status="need_clarification",
            sources=[],
            warnings=[],
            debug={"analysis": analysis.to_dict()},
        )

    def _sql_not_connected_response(self, analysis: QueryAnalysis) -> RAGPipelineResponse:
        table_hint = analysis.sql_table_hint or "unknown"

        answer = (
            "이 질문은 정형 데이터 조회가 더 적합합니다.\n\n"
            f"- 예상 조회 테이블: `{table_hint}`\n"
            f"- 조회 조건: `{analysis.sql_conditions}`\n\n"
            "현재 Streamlit 화면에는 SQL 조회 모듈이 아직 연결되지 않았습니다. "
            "SQL 담당 모듈이 연결되면 해당 데이터를 표 형태로 보여줄 수 있습니다."
        )

        return RAGPipelineResponse(
            answer=answer,
            route=analysis.route,
            status="sql_not_connected",
            sources=[],
            warnings=["SQL 조회 모듈이 아직 연결되지 않았습니다."],
            debug={"analysis": analysis.to_dict()},
        )

    def _build_response(
        self,
        analysis: QueryAnalysis,
        vector_result: VectorRetrievalResult,
        built_context: BuiltContext,
        generated: GeneratedAnswer,
    ) -> RAGPipelineResponse:
        return RAGPipelineResponse(
            answer=generated.answer,
            route=analysis.route,
            status=vector_result.status,
            sources=self._format_sources_for_streamlit(generated.sources),
            warnings=generated.warnings,
            debug={
                "analysis": analysis.to_dict(),
                "vector_result": vector_result.to_debug_dict(),
                "context_warnings": built_context.warnings,
            },
        )

    def _format_sources_for_streamlit(
        self,
        sources,
    ) -> list[dict[str, str]]:
        formatted_sources = []

        for source in sources:
            title = source.title or "출처"
            url = source.source or ""
            department = source.department or ""
            content_type = source.content_type or ""

            meta_parts = [
                part
                for part in [department, content_type, source.source_type]
                if part
            ]

            formatted_sources.append(
                {
                    "title": title,
                    "meta": " · ".join(meta_parts),
                    "url": url,
                }
            )

        return formatted_sources