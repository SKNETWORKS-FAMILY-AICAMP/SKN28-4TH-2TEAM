from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from django.conf import settings


FALLBACK_ANSWER = (
    "현재 RAG 엔진을 완전히 사용할 수 없어 임시 안내를 제공합니다. "
    "질문은 접수되었지만, 검색 근거 기반 답변 생성 중 문제가 발생했습니다. "
    "잠시 후 다시 시도하거나 학과명과 정보 유형을 더 구체적으로 입력해 주세요."
)


@dataclass
class ChatAnswer:
    answer: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    warning: str | None = None
    route: str = "blocked"
    department_code: str | None = None
    pending_clarification: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def make_title(question: str) -> str:
    normalized = " ".join(question.split())

    if len(normalized) <= 28:
        return normalized or "새 대화"

    return f"{normalized[:28]}..."


@lru_cache(maxsize=1)
def get_pipeline():
    if not settings.RAG_ENABLE_ENGINE:
        raise RuntimeError("RAG engine is disabled by settings.")

    from rag.rag_pipeline import create_default_pipeline

    return create_default_pipeline(
        include_sql=True,
        include_debug_context=False,
        preload_vector_retriever=False,
        preload_answer_generator=False,
    )


def answer_question(
    question: str,
    previous_department_code: str | None = None,
) -> ChatAnswer:
    try:
        pipeline = get_pipeline()
        result = pipeline.run(
            question=question,
            previous_department_code=previous_department_code or None,
        )
    except Exception as exc:
        return ChatAnswer(
            answer=FALLBACK_ANSWER,
            sources=[],
            warning="RAG_UNAVAILABLE",
            route="blocked",
            metadata={
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )

    warnings = list(result.warnings or [])
    warning = warnings[0] if warnings else None
    pending_clarification = {}

    if result.needs_clarification:
        pending_clarification = {
            "question": question,
            "intent": result.intent,
            "missing_fields": result.analysis.missing_fields,
        }

    return ChatAnswer(
        answer=result.answer,
        sources=format_sources(result.sources),
        warning=warning,
        route=result.route,
        department_code=result.department_code,
        pending_clarification=pending_clarification,
        metadata={
            "intent": result.intent,
            "warnings": warnings,
            "analysis": result.analysis.to_dict(),
        },
    )


def format_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted = []

    for source in sources:
        metadata = source.get("metadata", {}) or {}
        score = metadata.get("rerank_score")

        if score in ("", None):
            score = metadata.get("score")

        formatted.append(
            {
                "department": source.get("department") or metadata.get("dept") or "",
                "title": source.get("title") or source.get("source") or "Retrieved Source",
                "url": _valid_url(
                    source.get("source")
                    or metadata.get("source_url")
                    or metadata.get("url")
                    or ""
                ),
                "score": score,
            }
        )

    return formatted


def _valid_url(value: str) -> str:
    value = str(value or "")

    if value.startswith(("http://", "https://")):
        return value

    return ""
