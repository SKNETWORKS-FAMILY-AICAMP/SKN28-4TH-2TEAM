from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT_FROM_FILE = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT_FROM_FILE) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FROM_FILE))

from src.rag.query_analyzer import QueryAnalysis
from src.rag.context_builder import BuiltContext, SourceItem


@dataclass
class AnswerGeneratorConfig:
    model: str = "gpt-4.1-mini"
    temperature: float = 0.0
    include_sources: bool = True
    include_warnings: bool = True


@dataclass
class GeneratedAnswer:
    answer: str
    sources: list[SourceItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "sources": [source.to_dict() for source in self.sources],
            "warnings": self.warnings,
            "raw_context": self.raw_context,
        }


class AnswerGenerator:
    def __init__(self, config: AnswerGeneratorConfig | None = None) -> None:
        load_dotenv()

        self.config = config or AnswerGeneratorConfig()
        self._validate_settings()

        self.llm = ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._system_prompt()),
                ("human", self._human_prompt()),
            ]
        )

    def generate(
        self,
        question: str,
        built_context: BuiltContext,
        analysis: QueryAnalysis | None = None,
    ) -> GeneratedAnswer:
        if analysis and analysis.route == "clarify":
            answer = analysis.clarifying_message or "질문을 조금 더 구체적으로 입력해주세요."

            return GeneratedAnswer(
                answer=answer,
                sources=built_context.sources,
                warnings=built_context.warnings,
                raw_context=built_context.context,
            )

        if not built_context.context.strip():
            return self._empty_answer(built_context)

        if built_context.context.strip() == "사용 가능한 검색 결과가 없습니다.":
            return self._empty_answer(built_context)

        messages = self.prompt.format_messages(
            question=question,
            context=built_context.context,
            sources=self._format_sources_for_prompt(built_context.sources),
            warnings=self._format_warnings(built_context.warnings),
        )

        answer = self.llm.invoke(messages).content

        return GeneratedAnswer(
            answer=answer,
            sources=built_context.sources,
            warnings=built_context.warnings,
            raw_context=built_context.context,
        )

    def _system_prompt(self) -> str:
        return """
당신은 KAIST 대학원 정보 제공 챗봇입니다.

규칙:
1. 반드시 제공된 context 안의 내용만 근거로 답변하세요.
2. context에 없는 내용은 추측하지 말고 "제공된 자료에서 확인할 수 없습니다"라고 말하세요.
3. 조건, 자격, 일정, 장소, 연락처는 문서에 적힌 그대로 답변하세요.
4. 조건부 내용은 가능하다고 단정하지 말고 제한 조건을 함께 설명하세요.
5. SQL 결과와 Vector 문서가 함께 있으면 SQL 결과는 정형 사실, Vector 문서는 설명 근거로 사용하세요.
6. warnings가 있으면 답변에 조심스럽게 반영하세요.
7. 답변은 한국어로 작성하세요.
8. 마지막에는 참고 출처를 간단히 표시하세요.
""".strip()

    def _human_prompt(self) -> str:
        return """
[사용자 질문]
{question}

[Context]
{context}

[Sources]
{sources}

[Warnings]
{warnings}

위 정보만 근거로 답변하세요.
""".strip()

    def _empty_answer(self, built_context: BuiltContext) -> GeneratedAnswer:
        answer = (
            "제공된 자료에서 질문에 대한 근거를 찾을 수 없습니다. "
            "학과명이나 알고 싶은 정보 유형을 더 구체적으로 입력해주세요."
        )

        return GeneratedAnswer(
            answer=answer,
            sources=built_context.sources,
            warnings=built_context.warnings,
            raw_context=built_context.context,
        )

    def _format_sources_for_prompt(
        self,
        sources: list[SourceItem],
    ) -> str:
        if not sources:
            return "출처 없음"

        lines = []

        for index, source in enumerate(sources, start=1):
            title = source.title or "제목 없음"
            source_path = source.source or "출처 없음"
            department = source.department or ""
            content_type = source.content_type or ""

            lines.append(
                f"{index}. title={title} | "
                f"department={department} | "
                f"content_type={content_type} | "
                f"source={source_path}"
            )

        return "\n".join(lines)

    def _format_warnings(
        self,
        warnings: list[str],
    ) -> str:
        if not warnings:
            return "경고 없음"

        return "\n".join(f"- {warning}" for warning in warnings)

    def _validate_settings(self) -> None:
        if not os.getenv("OPENAI_API_KEY"):
            raise EnvironmentError(
                "OPENAI_API_KEY가 설정되어 있지 않습니다."
            )


def run_examples() -> None:
    from src.rag.vector_retriever import VectorRetriever
    from src.rag.context_builder import ContextBuilder, ContextBuilderConfig

    question = "AI컴퓨팅학과 학과설명회 정보 알려줘"

    retriever = VectorRetriever()
    vector_result = retriever.retrieve(question)

    builder = ContextBuilder(
        ContextBuilderConfig(
            include_debug_info=False,
        )
    )

    built_context = builder.build(
        analysis=vector_result.analysis,
        vector_result=vector_result,
    )

    generator = AnswerGenerator()
    result = generator.generate(
        question=question,
        built_context=built_context,
        analysis=vector_result.analysis,
    )

    print(result.answer)
    print("\n[SOURCES]")
    print([source.to_dict() for source in result.sources])
    print("\n[WARNINGS]")
    print(result.warnings)


if __name__ == "__main__":
    run_examples()