from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Any, Callable, Protocol

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT_FROM_FILE = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT_FROM_FILE) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FROM_FILE))

from src.rag.query_analyzer import QueryAnalysis, QuestionAnalyzer

if TYPE_CHECKING:
    from src.rag.answer_generator import (
        AnswerGenerator,
        AnswerGeneratorConfig,
        GeneratedAnswer,
    )
    from src.rag.context_builder import (
        BuiltContext,
        ContextBuilder,
        ContextBuilderConfig,
        SqlQueryResult,
    )
    from src.rag.vector_retriever import (
        VectorRetrievalResult,
        VectorRetriever,
        VectorRetrieverConfig,
    )


SqlSearchFn = Callable[[QueryAnalysis], "SqlQueryResult"]
TokenCallback = Callable[[str], None]
StatusCallback = Callable[[str], None]


class SqlRetrieverLike(Protocol):
    def search(self, analysis: QueryAnalysis) -> SqlQueryResult:
        ...


@dataclass
class RagPipelineConfig:
    use_vector_when_sql_unavailable: bool = True
    use_vector_when_sql_empty: bool = True
    include_debug_context: bool = False
    raise_search_errors: bool = False
    raise_generation_errors: bool = False
    preload_vector_retriever: bool = False
    preload_answer_generator: bool = False
    empty_answer_message: str = (
        "제공된 자료에서 질문에 대한 충분한 근거를 찾을 수 없습니다. "
        "학과명이나 알고 싶은 정보 유형을 더 구체적으로 입력해주세요.\n\n"
        "정확하고 최신 정보는 KAIST 공식 홈페이지 또는 입학처에서 확인하는 것을 권장합니다.\n"
        "- KAIST 공식 홈페이지: https://www.kaist.ac.kr/kr/\n"
        "- KAIST 입학처: https://admission.kaist.ac.kr/home"
    )


@dataclass
class RagSearchResult:
    analysis: QueryAnalysis
    vector_result: VectorRetrievalResult | None = None
    sql_result: SqlQueryResult | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def has_vector_results(self) -> bool:
        return bool(self.vector_result and self.vector_result.results)

    @property
    def has_sql_results(self) -> bool:
        return bool(self.sql_result and not self.sql_result.is_empty())

    @property
    def has_results(self) -> bool:
        return self.has_vector_results or self.has_sql_results

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis": self.analysis.to_dict(),
            "vector_result": (
                self.vector_result.to_debug_dict()
                if self.vector_result
                else None
            ),
            "sql_result": asdict(self.sql_result) if self.sql_result else None,
            "warnings": self.warnings,
        }


@dataclass
class RagPipelineResult:
    question: str
    analysis: QueryAnalysis
    built_context: BuiltContext
    generated_answer: GeneratedAnswer
    vector_result: VectorRetrievalResult | None = None
    sql_result: SqlQueryResult | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def answer(self) -> str:
        return self.generated_answer.answer

    @property
    def route(self) -> str:
        return self.analysis.route

    @property
    def intent(self) -> str:
        return self.analysis.intent

    @property
    def department_code(self) -> str | None:
        return self.analysis.department_code

    @property
    def needs_clarification(self) -> bool:
        return self.analysis.route == "clarify"

    @property
    def sources(self) -> list[dict[str, Any]]:
        return [
            source.to_dict()
            for source in self.generated_answer.sources
        ]

    def to_dict(self, include_debug_context: bool = False) -> dict[str, Any]:
        result = {
            "question": self.question,
            "answer": self.generated_answer.answer,
            "analysis": self.analysis.to_dict(),
            "route": self.analysis.route,
            "intent": self.analysis.intent,
            "department_code": self.analysis.department_code,
            "needs_clarification": self.needs_clarification,
            "sources": self.sources,
            "warnings": self.warnings,
        }

        if include_debug_context:
            result["built_context"] = self.built_context.to_dict()
            result["vector_result"] = (
                self.vector_result.to_debug_dict()
                if self.vector_result
                else None
            )
            result["sql_result"] = (
                asdict(self.sql_result)
                if self.sql_result
                else None
            )

        return result


class RagPipeline:
    def __init__(
        self,
        config: RagPipelineConfig | None = None,
        analyzer: QuestionAnalyzer | None = None,
        vector_retriever: VectorRetriever | None = None,
        vector_config: VectorRetrieverConfig | None = None,
        sql_retriever: SqlSearchFn | SqlRetrieverLike | None = None,
        context_builder: ContextBuilder | None = None,
        context_config: ContextBuilderConfig | None = None,
        answer_generator: AnswerGenerator | None = None,
        answer_config: AnswerGeneratorConfig | None = None,
    ) -> None:
        self.config = config or RagPipelineConfig()

        self.analyzer = analyzer or QuestionAnalyzer()
        self.vector_config = vector_config
        self.sql_retriever = sql_retriever
        self.context_config = context_config
        self.answer_config = answer_config

        self._vector_retriever = vector_retriever
        self._context_builder = context_builder
        self._answer_generator = answer_generator
        self.last_warm_up_result: dict[str, Any] | None = None

        if (
            self.config.preload_vector_retriever
            or self.config.preload_answer_generator
        ):
            self.last_warm_up_result = self.warm_up(
                include_vector_retriever=self.config.preload_vector_retriever,
                include_answer_generator=self.config.preload_answer_generator,
                include_context_builder=False,
                raise_errors=(
                    self.config.raise_search_errors
                    or self.config.raise_generation_errors
                ),
            )

    def classify_question(
        self,
        question: str,
        previous_department_code: str | None = None,
    ) -> QueryAnalysis:
        return self.analyzer.analyze(
            question=question,
            previous_department_code=previous_department_code,
        )

    def warm_up(
        self,
        include_vector_retriever: bool = True,
        include_answer_generator: bool = False,
        include_context_builder: bool = True,
        sample_question: str | None = None,
        previous_department_code: str | None = None,
        raise_errors: bool = False,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ok": True,
            "components": {},
            "warnings": [],
        }

        def record_component(
            name: str,
            callback: Callable[[], Any],
        ) -> Any:
            started_at = perf_counter()

            try:
                value = callback()
            except Exception as exc:
                elapsed_seconds = round(perf_counter() - started_at, 3)
                message = str(exc)

                result["ok"] = False
                result["components"][name] = {
                    "ok": False,
                    "elapsed_seconds": elapsed_seconds,
                    "message": message,
                }
                result["warnings"].append(
                    f"{name} warm-up 중 오류가 발생했습니다: {message}"
                )

                if raise_errors:
                    raise

                return None

            elapsed_seconds = round(perf_counter() - started_at, 3)
            result["components"][name] = {
                "ok": True,
                "elapsed_seconds": elapsed_seconds,
            }

            return value

        vector_retriever = None

        if include_vector_retriever or sample_question:
            vector_retriever = record_component(
                "vector_retriever",
                self._get_vector_retriever,
            )

        if sample_question and vector_retriever is not None:
            def run_sample_vector_search() -> Any:
                return vector_retriever.retrieve(
                    question=sample_question,
                    previous_department_code=previous_department_code,
                    force_vector_search=True,
                )

            sample_result = record_component(
                "sample_vector_search",
                run_sample_vector_search,
            )

            if sample_result is not None:
                result["components"]["sample_vector_search"].update(
                    {
                        "status": sample_result.status,
                        "result_count": len(sample_result.results),
                    }
                )

        if include_answer_generator:
            record_component(
                "answer_generator",
                self._get_answer_generator,
            )

        if include_context_builder:
            record_component(
                "context_builder",
                self._get_context_builder,
            )

        self.last_warm_up_result = result
        return result

    def search(
        self,
        question: str,
        analysis: QueryAnalysis | None = None,
        previous_department_code: str | None = None,
    ) -> RagSearchResult:
        analysis = analysis or self.classify_question(
            question=question,
            previous_department_code=previous_department_code,
        )

        warnings: list[str] = []
        sql_result: SqlQueryResult | None = None
        vector_result: VectorRetrievalResult | None = None

        if analysis.route == "clarify":
            return RagSearchResult(
                analysis=analysis,
                warnings=warnings,
            )

        if analysis.needs_sql:
            sql_result = self._search_sql(analysis)

            if sql_result is None:
                warnings.append(
                    "SQL 검색기가 아직 연결되어 있지 않아 SQL 조회를 건너뛰었습니다."
                )
            elif sql_result.is_empty():
                warnings.append(
                    "SQL 조회 결과가 비어 있습니다."
                )

        should_search_vector = analysis.needs_vector
        force_vector_search = False

        sql_unavailable = analysis.needs_sql and sql_result is None
        sql_empty = (
            analysis.needs_sql
            and sql_result is not None
            and sql_result.is_empty()
        )

        if sql_unavailable and self.config.use_vector_when_sql_unavailable:
            should_search_vector = True
            force_vector_search = analysis.route == "sql"

        if sql_empty and self.config.use_vector_when_sql_empty:
            should_search_vector = True
            force_vector_search = analysis.route == "sql"

        if should_search_vector:
            try:
                retrieval_question = analysis.rewritten_question or question

                vector_result = self._get_vector_retriever().retrieve(
                    question=retrieval_question,
                    previous_department_code=previous_department_code,
                    force_vector_search=force_vector_search,
                )
            except Exception as exc:
                if self.config.raise_search_errors:
                    raise

                warnings.append(
                    f"Vector 검색 중 오류가 발생했습니다: {exc}"
                )

        return RagSearchResult(
            analysis=analysis,
            vector_result=vector_result,
            sql_result=sql_result,
            warnings=warnings,
        )

    def build_context(
        self,
        analysis: QueryAnalysis,
        vector_result: VectorRetrievalResult | None = None,
        sql_result: SqlQueryResult | None = None,
        warnings: list[str] | None = None,
    ) -> BuiltContext:
        built_context = self._get_context_builder().build(
            analysis=analysis,
            vector_result=vector_result,
            sql_result=sql_result,
        )

        if warnings:
            built_context.warnings = self._deduplicate_strings(
                [*warnings, *built_context.warnings]
            )

        return built_context

    def generate_answer(
        self,
        question: str,
        built_context: BuiltContext,
        analysis: QueryAnalysis,
    ) -> GeneratedAnswer:
        policy_decision = self._check_answer_policy(
            question=question,
            analysis=analysis,
        )

        if not policy_decision.allowed:
            from src.rag.answer_generator import GeneratedAnswer

            return GeneratedAnswer(
                answer=policy_decision.message,
                sources=[],
                warnings=self._deduplicate_strings(
                    [*built_context.warnings, policy_decision.reason]
                ),
                raw_context=built_context.context,
            )

        if analysis.route == "clarify":
            from src.rag.answer_generator import GeneratedAnswer

            return GeneratedAnswer(
                answer=analysis.clarifying_message
                or "질문을 조금 더 구체적으로 입력해주세요.",
                sources=built_context.sources,
                warnings=built_context.warnings,
                raw_context=built_context.context,
            )

        if not built_context.sources:
            from src.rag.answer_generator import GeneratedAnswer

            return GeneratedAnswer(
                answer=self.config.empty_answer_message,
                sources=built_context.sources,
                warnings=built_context.warnings,
                raw_context=built_context.context,
            )

        try:
            return self._get_answer_generator().generate(
                question=question,
                built_context=built_context,
                analysis=analysis,
            )
        except Exception as exc:
            if self.config.raise_generation_errors:
                raise

            built_context.warnings = self._deduplicate_strings(
                [
                    *built_context.warnings,
                    f"답변 생성 중 오류가 발생했습니다: {exc}",
                ]
            )

            from src.rag.answer_generator import GeneratedAnswer

            return GeneratedAnswer(
                answer=(
                    "답변 생성 중 오류가 발생했습니다. "
                    "검색 결과와 환경 설정을 확인해주세요."
                ),
                sources=built_context.sources,
                warnings=built_context.warnings,
                raw_context=built_context.context,
            )

    def generate_answer_streaming(
        self,
        question: str,
        built_context: BuiltContext,
        analysis: QueryAnalysis,
        on_token: TokenCallback | None = None,
    ) -> GeneratedAnswer:
        def emit(text: str) -> None:
            if on_token:
                on_token(text)

        policy_decision = self._check_answer_policy(
            question=question,
            analysis=analysis,
        )

        if not policy_decision.allowed:
            from src.rag.answer_generator import GeneratedAnswer

            emit(policy_decision.message)
            return GeneratedAnswer(
                answer=policy_decision.message,
                sources=[],
                warnings=self._deduplicate_strings(
                    [*built_context.warnings, policy_decision.reason]
                ),
                raw_context=built_context.context,
            )

        if analysis.route == "clarify":
            from src.rag.answer_generator import GeneratedAnswer

            answer = (
                analysis.clarifying_message
                or "질문을 조금 더 구체적으로 입력해주세요."
            )
            emit(answer)
            return GeneratedAnswer(
                answer=answer,
                sources=built_context.sources,
                warnings=built_context.warnings,
                raw_context=built_context.context,
            )

        if not built_context.sources:
            from src.rag.answer_generator import GeneratedAnswer

            emit(self.config.empty_answer_message)
            return GeneratedAnswer(
                answer=self.config.empty_answer_message,
                sources=built_context.sources,
                warnings=built_context.warnings,
                raw_context=built_context.context,
            )

        try:
            chunks = []

            for chunk in self._get_answer_generator().stream_generate(
                question=question,
                built_context=built_context,
                analysis=analysis,
            ):
                chunks.append(chunk)
                emit(chunk)

            answer = "".join(chunks).strip()

            if not answer:
                answer = self.config.empty_answer_message
                emit(answer)

            from src.rag.answer_generator import GeneratedAnswer

            return GeneratedAnswer(
                answer=answer,
                sources=built_context.sources,
                warnings=built_context.warnings,
                raw_context=built_context.context,
            )
        except Exception as exc:
            if self.config.raise_generation_errors:
                raise

            built_context.warnings = self._deduplicate_strings(
                [
                    *built_context.warnings,
                    f"답변 생성 중 오류가 발생했습니다: {exc}",
                ]
            )

            answer = (
                "답변 생성 중 오류가 발생했습니다. "
                "검색 결과와 환경 설정을 확인해주세요."
            )
            emit(answer)

            from src.rag.answer_generator import GeneratedAnswer

            return GeneratedAnswer(
                answer=answer,
                sources=built_context.sources,
                warnings=built_context.warnings,
                raw_context=built_context.context,
            )

    def run(
        self,
        question: str,
        previous_department_code: str | None = None,
    ) -> RagPipelineResult:
        analysis = self.classify_question(
            question=question,
            previous_department_code=previous_department_code,
        )

        policy_decision = self._check_answer_policy(
            question=question,
            analysis=analysis,
        )

        if not policy_decision.allowed:
            built_context = self.build_context(
                analysis=analysis,
                warnings=[policy_decision.reason],
            )
            generated_answer = self.generate_answer(
                question=question,
                built_context=built_context,
                analysis=analysis,
            )

            return RagPipelineResult(
                question=question,
                analysis=analysis,
                built_context=built_context,
                generated_answer=generated_answer,
                warnings=generated_answer.warnings,
            )

        search_result = self.search(
            question=question,
            analysis=analysis,
            previous_department_code=previous_department_code,
        )

        built_context = self.build_context(
            analysis=analysis,
            vector_result=search_result.vector_result,
            sql_result=search_result.sql_result,
            warnings=search_result.warnings,
        )

        generated_answer = self.generate_answer(
            question=question,
            built_context=built_context,
            analysis=analysis,
        )

        return RagPipelineResult(
            question=question,
            analysis=analysis,
            built_context=built_context,
            generated_answer=generated_answer,
            vector_result=search_result.vector_result,
            sql_result=search_result.sql_result,
            warnings=built_context.warnings,
        )

    def run_streaming(
        self,
        question: str,
        previous_department_code: str | None = None,
        on_token: TokenCallback | None = None,
        on_status: StatusCallback | None = None,
    ) -> RagPipelineResult:
        def status(message: str) -> None:
            if on_status:
                on_status(message)

        status("질문 유형을 분석하는 중입니다.")
        analysis = self.classify_question(
            question=question,
            previous_department_code=previous_department_code,
        )

        policy_decision = self._check_answer_policy(
            question=question,
            analysis=analysis,
        )

        if not policy_decision.allowed:
            status("답변 안전 정책을 적용하는 중입니다.")
            built_context = self.build_context(
                analysis=analysis,
                warnings=[policy_decision.reason],
            )
            generated_answer = self.generate_answer_streaming(
                question=question,
                built_context=built_context,
                analysis=analysis,
                on_token=on_token,
            )

            return RagPipelineResult(
                question=question,
                analysis=analysis,
                built_context=built_context,
                generated_answer=generated_answer,
                warnings=generated_answer.warnings,
            )

        status("관련 문서를 검색하는 중입니다.")
        search_result = self.search(
            question=question,
            analysis=analysis,
            previous_department_code=previous_department_code,
        )

        status("답변 context를 구성하는 중입니다.")
        built_context = self.build_context(
            analysis=analysis,
            vector_result=search_result.vector_result,
            sql_result=search_result.sql_result,
            warnings=search_result.warnings,
        )

        status("답변을 생성하는 중입니다.")
        generated_answer = self.generate_answer_streaming(
            question=question,
            built_context=built_context,
            analysis=analysis,
            on_token=on_token,
        )

        status("답변 생성이 완료되었습니다.")

        return RagPipelineResult(
            question=question,
            analysis=analysis,
            built_context=built_context,
            generated_answer=generated_answer,
            vector_result=search_result.vector_result,
            sql_result=search_result.sql_result,
            warnings=built_context.warnings,
        )

    def run_dict(
        self,
        question: str,
        previous_department_code: str | None = None,
        include_debug_context: bool | None = None,
    ) -> dict[str, Any]:
        result = self.run(
            question=question,
            previous_department_code=previous_department_code,
        )

        return result.to_dict(
            include_debug_context=(
                self.config.include_debug_context
                if include_debug_context is None
                else include_debug_context
            )
        )

    def _search_sql(self, analysis: QueryAnalysis) -> SqlQueryResult | None:
        if self.sql_retriever is None:
            return None

        try:
            if callable(self.sql_retriever):
                return self.sql_retriever(analysis)

            return self.sql_retriever.search(analysis)
        except Exception as exc:
            if self.config.raise_search_errors:
                raise

            from src.rag.context_builder import SqlQueryResult

            return SqlQueryResult(
                table_name=analysis.sql_table_hint or "unknown",
                rows=[],
                conditions=analysis.sql_conditions,
                message="SQL 검색 중 오류가 발생했습니다.",
                warnings=[f"SQL 검색 중 오류가 발생했습니다: {exc}"],
            )

    def _get_vector_retriever(self) -> VectorRetriever:
        if self._vector_retriever is None:
            from src.rag.vector_retriever import VectorRetriever

            self._vector_retriever = VectorRetriever(
                config=self.vector_config,
                question_analyzer=self.analyzer,
            )

        return self._vector_retriever

    def _get_context_builder(self) -> ContextBuilder:
        if self._context_builder is None:
            from src.rag.context_builder import ContextBuilder

            self._context_builder = ContextBuilder(
                config=self.context_config,
            )

        return self._context_builder

    def _get_answer_generator(self) -> AnswerGenerator:
        if self._answer_generator is None:
            from src.rag.answer_generator import AnswerGenerator

            self._answer_generator = AnswerGenerator(
                config=self.answer_config,
            )

        return self._answer_generator

    def _check_answer_policy(
        self,
        question: str,
        analysis: QueryAnalysis,
    ) -> Any:
        from src.rag.answer_generator import check_answer_policy

        return check_answer_policy(
            question=question,
            analysis=analysis,
        )

    def _deduplicate_strings(self, values: list[str]) -> list[str]:
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

def create_default_pipeline(
    include_sql: bool = True,
    include_debug_context: bool = False,
    preload_vector_retriever: bool = False,
    preload_answer_generator: bool = False,
) -> RagPipeline:
    """
    앱과 테스트 코드에서 공통으로 사용할 기본 RAG Pipeline을 생성합니다.

    include_sql=True인 경우 SQLTool 연결을 시도합니다.
    SQLTool 연결 실패 시에도 Vector 기반 RAG는 계속 사용할 수 있도록 처리합니다.
    """
    sql_retriever = None

    if include_sql:
        try:
            from src.rag.sql_tool import SQLTool

            sql_retriever = SQLTool()
        except Exception:
            sql_retriever = None

    config = RagPipelineConfig(
        use_vector_when_sql_unavailable=True,
        use_vector_when_sql_empty=True,
        include_debug_context=include_debug_context,
        preload_vector_retriever=preload_vector_retriever,
        preload_answer_generator=preload_answer_generator,
    )

    return RagPipeline(
        config=config,
        sql_retriever=sql_retriever,
    )

def answer_question(
    question: str,
    previous_department_code: str | None = None,
    pipeline: RagPipeline | None = None,
) -> RagPipelineResult:
    pipeline = pipeline or create_default_pipeline()

    return pipeline.run(
        question=question,
        previous_department_code=previous_department_code,
    )


def answer_question_dict(
    question: str,
    previous_department_code: str | None = None,
    pipeline: RagPipeline | None = None,
    include_debug_context: bool | None = None,
) -> dict[str, Any]:
    pipeline = pipeline or create_default_pipeline(
        include_debug_context=bool(include_debug_context),
    )

    return pipeline.run_dict(
        question=question,
        previous_department_code=previous_department_code,
        include_debug_context=include_debug_context,
    )

def run_examples() -> None:
    pipeline = create_default_pipeline(
        include_sql=True,
        include_debug_context=True,
        preload_vector_retriever=False,
        preload_answer_generator=False,
    )

    questions = [
        "AI컴퓨팅학과 석사 지원 자격 알려줘",
        "AX학과 교수 이메일 알려줘",
        "AI시스템학과 교과목 설명해줘",
        "KAIST 학과사무실 전화번호 알려줘",
    ]

    for question in questions:
        print("=" * 100)
        print(f"질문: {question}")

        result = pipeline.run_dict(
            question=question,
            include_debug_context=True,
        )

        print("route:", result["route"])
        print("intent:", result["intent"])
        print("department_code:", result["department_code"])
        print("answer:", result["answer"][:500])
        print("sources:", result["sources"][:3])
        print("warnings:", result["warnings"])


if __name__ == "__main__":
    run_examples()