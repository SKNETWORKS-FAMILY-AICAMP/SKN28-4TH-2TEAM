from __future__ import annotations

import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT_FROM_FILE = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT_FROM_FILE) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FROM_FILE))

from src.rag.query_analyzer import QuestionAnalyzer, QueryAnalysis

if TYPE_CHECKING:
    from langchain_core.documents import Document

VectorSearchStatus = Literal[
    "searched",
    "skipped_sql_route",
    "need_clarification",
    "no_result",
    "error",
]

SearchStage = Literal[
    "strict_filter",
    "department_only",
    "content_type_only",
    "no_filter",
]

FallbackTriggerMode = Literal[
    "only_when_empty",
    "below_min_results",
]

# ============================================================
# 검색 scope 정책
# ============================================================

AI_COLLEGE_DEPT_CODES = {
    "aic",
    "ai_systems",
    "ax",
    "fx",
}

AI_COLLEGE_DEPT_NAMES = {
    "AI컴퓨팅학과",
    "AI시스템학과",
    "AX학과",
    "AI미래학과",
}

AI_COLLEGE_SCOPE_KEYWORDS = [
    "AI대학",
    "AI 대학",
    "KAIST AI대학",
    "카이스트 AI대학",
    "AI 관련 학과",
    "전체 학과",
    "모든 학과",
    "각 학과",
    "학과별",
    "학과들",
    "학과들을",
]

KAIST_GLOBAL_SOURCE_TYPES = {
    "csv_kaist_profile",
    "csv_kaist_statistics",
    "csv_kaist_link",
}

KAIST_OFFICE_SOURCE_TYPES = {
    "csv_department_office",
}

@dataclass
class VectorRetrieverConfig:
    project_root: Path = PROJECT_ROOT_FROM_FILE
    chroma_relative_dir: Path = Path("data") / "vectorstore" / "chroma_db"
    collection_name: str = "kaist_graduate_info"
    embedding_model: str = "text-embedding-3-small"

    search_k: int = 5
    fetch_k: int = 25
    candidate_multiplier: int = 4
    min_results_before_fallback: int = 2

    use_rewritten_question: bool = True
    use_fallback: bool = True
    fallback_trigger_mode: FallbackTriggerMode = "below_min_results"
    use_lightweight_reranker: bool = True

    @property
    def chroma_dir(self) -> Path:
        return self.project_root / self.chroma_relative_dir


@dataclass
class RetrievedVectorDocument:
    document: Document
    score: float | None
    search_stage: SearchStage
    rerank_score: float = 0.0

    def to_debug_dict(self) -> dict[str, Any]:
        metadata = self.document.metadata

        return {
            "score": self.score,
            "rerank_score": self.rerank_score,
            "search_stage": self.search_stage,
            "metadata": {
                "source_type": metadata.get("source_type"),
                "dept": metadata.get("dept"),
                "dept_name": metadata.get("dept_name"),
                "content_type": metadata.get("content_type"),
                "title": metadata.get("title"),
                "source": metadata.get("source") or metadata.get("source_url"),
            },
            "preview": self.document.page_content[:500],
        }


@dataclass
class SearchAttempt:
    search_stage: SearchStage
    metadata_filter: dict[str, Any] | None
    result_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VectorRetrievalResult:
    status: VectorSearchStatus
    message: str
    analysis: QueryAnalysis

    results: list[RetrievedVectorDocument] = field(default_factory=list)
    used_query: str | None = None
    used_filter: dict[str, Any] | None = None
    used_fallback: bool = False
    search_attempts: list[SearchAttempt] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def documents(self) -> list[Document]:
        return [item.document for item in self.results]

    @property
    def scores(self) -> list[float | None]:
        return [item.score for item in self.results]

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "used_query": self.used_query,
            "used_filter": self.used_filter,
            "used_fallback": self.used_fallback,
            "warnings": self.warnings,
            "search_attempts": [attempt.to_dict() for attempt in self.search_attempts],
            "analysis": self.analysis.to_dict(),
            "results": [item.to_debug_dict() for item in self.results],
        }


class LightweightReranker:
    STOPWORDS = {
        "알려줘", "보여줘", "정리해줘", "설명해줘",
        "정보", "관련", "대한", "어떤", "무엇", "뭐야",
        "목록", "전체", "각", "및", "그리고", "또", "도",
        "있는", "없는", "합니다", "해주세요",
    }

    def rerank(
        self,
        question: str,
        analysis: QueryAnalysis,
        items: list[RetrievedVectorDocument],
    ) -> list[RetrievedVectorDocument]:
        question_keywords = self._extract_keywords(question)

        for item in items:
            item.rerank_score = self._calculate_score(
                question_keywords=question_keywords,
                analysis=analysis,
                item=item,
            )

        return sorted(items, key=lambda item: item.rerank_score, reverse=True)

    def _calculate_score(
        self,
        question_keywords: set[str],
        analysis: QueryAnalysis,
        item: RetrievedVectorDocument,
    ) -> float:
        document = item.document
        metadata = document.metadata

        document_text = self._build_document_text(document)
        document_keywords = self._extract_keywords(document_text)

        keyword_score = self._keyword_overlap_score(
            question_keywords,
            document_keywords,
        )
        metadata_score = self._metadata_match_score(analysis, metadata)
        vector_score = self._normalized_vector_score(item.score)
        stage_score = self._stage_score(item.search_stage)

        final_score = (
            keyword_score * 0.35
            + metadata_score * 0.30
            + vector_score * 0.20
            + stage_score * 0.15
        )

        return round(final_score, 6)

    def _build_document_text(self, document: Document) -> str:
        metadata = document.metadata

        keys = [
            "dept_name", "department", "content_type", "doc_type",
            "title", "section", "admission_type",
            "course_code", "course_type", "tracks",
            "name", "role", "email", "event_date",
        ]

        metadata_text = " ".join(
            str(metadata[key])
            for key in keys
            if metadata.get(key)
        )

        return f"{metadata_text}\n{document.page_content}"

    def _extract_keywords(self, text: str) -> set[str]:
        tokens = re.findall(r"[가-힣a-zA-Z0-9_]+", text.lower())

        return {
            token
            for token in tokens
            if len(token) >= 2 and token not in self.STOPWORDS
        }

    def _keyword_overlap_score(
        self,
        question_keywords: set[str],
        document_keywords: set[str],
    ) -> float:
        if not question_keywords:
            return 0.0

        overlap = question_keywords.intersection(document_keywords)

        return len(overlap) / len(question_keywords)

    def _metadata_match_score(
        self,
        analysis: QueryAnalysis,
        metadata: dict[str, Any],
    ) -> float:
        score = 0.0
        max_score = 0.0

        if analysis.department_code:
            max_score += 1.0
            if metadata.get("dept") == analysis.department_code:
                score += 1.0

        if analysis.content_type:
            max_score += 1.0
            if metadata.get("content_type") == analysis.content_type:
                score += 1.0

        if max_score == 0:
            return 0.0

        return score / max_score

    def _normalized_vector_score(self, vector_score: float | None) -> float:
        if vector_score is None:
            return 0.0

        vector_score = max(vector_score, 0.0)

        return 1 / (1 + vector_score)

    def _stage_score(self, search_stage: SearchStage) -> float:
        scores = {
            "strict_filter": 1.0,
            "department_only": 0.65,
            "content_type_only": 0.50,
            "no_filter": 0.25,
        }

        return scores.get(search_stage, 0.0)


class VectorRetriever:
    def __init__(
        self,
        config: VectorRetrieverConfig | None = None,
        question_analyzer: QuestionAnalyzer | None = None,
        reranker: LightweightReranker | None = None,
    ) -> None:
        load_dotenv()

        self.config = config or VectorRetrieverConfig()
        self.question_analyzer = question_analyzer or QuestionAnalyzer()
        self.reranker = reranker or LightweightReranker()

        self._validate_settings()

        from langchain_chroma import Chroma
        from langchain_openai import OpenAIEmbeddings

        self.embedding_model = OpenAIEmbeddings(
            model=self.config.embedding_model,
            request_timeout=30,
            max_retries=2,
        )

        self.vectorstore = Chroma(
            collection_name=self.config.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=str(self.config.chroma_dir),
        )

    def retrieve(
        self,
        question: str,
        previous_department_code: str | None = None,
        force_vector_search: bool = False,
    ) -> VectorRetrievalResult:
        analysis = self.question_analyzer.analyze(
            question=question,
            previous_department_code=previous_department_code,
        )

        if analysis.route == "clarify":
            return VectorRetrievalResult(
                status="need_clarification",
                message="질문에 필요한 정보가 부족해서 추가 질문이 필요합니다.",
                analysis=analysis,
                used_filter=analysis.metadata_filter,
            )

        if analysis.route == "sql" and not force_vector_search:
            return VectorRetrievalResult(
                status="skipped_sql_route",
                message="SQL 조회가 더 적합한 질문이므로 vector 검색을 생략했습니다.",
                analysis=analysis,
                used_filter=analysis.metadata_filter,
            )

        search_query = self._select_search_query(analysis)
        search_plan = self._build_search_plan(analysis)

        items, attempts, used_fallback, warnings = self._search_with_fallback(
            search_query=search_query,
            search_plan=search_plan,
            analysis=analysis,
            question=analysis.normalized_question,
        )

        if not items:
            return VectorRetrievalResult(
                status="no_result",
                message="Vectorstore에서 관련 문서를 찾지 못했습니다.",
                analysis=analysis,
                used_query=search_query,
                used_filter=analysis.metadata_filter,
                used_fallback=used_fallback,
                search_attempts=attempts,
                warnings=warnings,
            )

        reranked_items = self._rerank_results(
            question=analysis.normalized_question,
            analysis=analysis,
            items=items,
        )

        final_items = self._select_final_results(
            analysis=analysis,
            question=analysis.normalized_question,
            items=reranked_items,
        )

        return VectorRetrievalResult(
            status="searched",
            message="Vectorstore 검색이 완료되었습니다.",
            analysis=analysis,
            results=final_items,
            used_query=search_query,
            used_filter=analysis.metadata_filter,
            used_fallback=used_fallback,
            search_attempts=attempts,
            warnings=warnings,
        )

    def retrieve_documents(
        self,
        question: str,
        previous_department_code: str | None = None,
        force_vector_search: bool = False,
    ) -> list[Document]:
        result = self.retrieve(
            question=question,
            previous_department_code=previous_department_code,
            force_vector_search=force_vector_search,
        )

        return result.documents

    def format_documents_for_context(
        self,
        documents: list[Document],
        max_chars_per_doc: int = 1500,
    ) -> str:
        blocks = []

        for index, document in enumerate(documents, start=1):
            metadata = document.metadata

            department = metadata.get("dept_name") or metadata.get("department") or ""
            content_type = metadata.get("content_type") or metadata.get("doc_type") or ""
            title = metadata.get("title") or ""
            source = metadata.get("source") or metadata.get("source_url") or ""

            content = document.page_content

            if len(content) > max_chars_per_doc:
                content = content[:max_chars_per_doc].rstrip() + "\n...[중략]"

            blocks.append(
                f"[문서 {index}]\n"
                f"학과: {department}\n"
                f"문서유형: {content_type}\n"
                f"제목: {title}\n"
                f"출처: {source}\n"
                f"내용:\n{content}"
            )

        return "\n\n".join(blocks)

    def _validate_settings(self) -> None:
        chroma_dir = self.config.chroma_dir

        if not chroma_dir.exists():
            raise FileNotFoundError(
                f"Chroma DB 폴더를 찾을 수 없습니다: {chroma_dir}\n"
                "먼저 아래 명령어로 vectorstore를 생성하세요:\n"
                "python data/build_vectorstore.py --reset --smoke-test"
            )

        if not any(chroma_dir.iterdir()):
            raise FileNotFoundError(
                f"Chroma DB 폴더가 비어 있습니다: {chroma_dir}\n"
                "먼저 아래 명령어로 vectorstore를 생성하세요:\n"
                "python data/build_vectorstore.py --reset --smoke-test"
            )

        if not os.getenv("OPENAI_API_KEY"):
            raise EnvironmentError(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. "
                ".env 파일 또는 환경변수에 OPENAI_API_KEY를 설정하세요."
            )

    def _select_search_query(self, analysis: QueryAnalysis) -> str:
        if self.config.use_rewritten_question:
            return analysis.rewritten_question

        return analysis.normalized_question

    def _build_search_plan(
        self,
        analysis: QueryAnalysis,
    ) -> list[tuple[SearchStage, dict[str, Any] | None]]:
        plan: list[tuple[SearchStage, dict[str, Any] | None]] = []

        strict_filter = analysis.metadata_filter

        department_filter = None
        if analysis.department_code:
            department_filter = {
                "dept": {"$eq": analysis.department_code}
            }

        content_type_filter = None
        if analysis.content_type:
            content_type_filter = {
                "content_type": {"$eq": analysis.content_type}
            }

        if strict_filter:
            plan.append(("strict_filter", strict_filter))

        if department_filter and department_filter != strict_filter:
            plan.append(("department_only", department_filter))

        if content_type_filter and content_type_filter != strict_filter:
            plan.append(("content_type_only", content_type_filter))

        plan.append(("no_filter", None))

        return plan

    def _is_ai_college_scope_question(self, question: str) -> bool:
        question = str(question)

        return any(
            keyword in question
            for keyword in AI_COLLEGE_SCOPE_KEYWORDS
        )

    def _is_kaist_global_question(self, question: str) -> bool:
        question = str(question)

        kaist_keywords = [
            "KAIST",
            "카이스트",
            "한국과학기술원",
        ]

        global_info_keywords = [
            "대표 번호",
            "대표번호",
            "주소",
            "영문명",
            "영문약자",
            "설립일",
            "재학생",
            "졸업생",
            "교직원",
            "공식 홈페이지",
            "입학처",
            "캠퍼스맵",
            "도서관",
            "학사일정",
        ]

        return (
            any(keyword in question for keyword in kaist_keywords)
            and any(keyword in question for keyword in global_info_keywords)
        )

    def _is_kaist_office_question(self, question: str) -> bool:
        question = str(question)

        kaist_keywords = [
            "KAIST",
            "카이스트",
            "한국과학기술원",
        ]

        office_keywords = [
            "전체 학과사무실",
            "전체 학과 사무실",
            "학과사무실 목록",
            "학과 사무실 목록",
            "모든 학과 사무실",
            "학과별 사무실",
            "학과별 연락처",
        ]

        return (
            any(keyword in question for keyword in kaist_keywords)
            and any(keyword in question for keyword in office_keywords)
        )

    def _is_allowed_item_for_question(
        self,
        item: RetrievedVectorDocument,
        analysis: QueryAnalysis,
        question: str,
    ) -> bool:
        """
        vectorstore에는 KAIST 전체 데이터가 들어 있을 수 있다.
        따라서 질문 scope에 따라 답변 context에 넣을 문서를 제한한다.
        """

        metadata = item.document.metadata or {}

        dept = str(metadata.get("dept", "") or "").strip()
        dept_name = str(metadata.get("dept_name", "") or "").strip()
        department_code_meta = str(metadata.get("department_code", "") or "").strip()
        department = str(metadata.get("department", "") or "").strip()
        source_type = str(metadata.get("source_type", "") or "").strip()

        # 1. 특정 학과 질문이면 해당 학과 문서만 허용
        if analysis.department_code:
            return (
                dept == analysis.department_code
                or department_code_meta == analysis.department_code
            )

        # 2. KAIST 전체 학과사무실 질문이면 학과사무실 데이터 허용
        if self._is_kaist_office_question(question):
            return source_type in KAIST_OFFICE_SOURCE_TYPES

        # 3. KAIST 기본정보 질문이면 KAIST 기본정보/통계/링크만 허용
        if self._is_kaist_global_question(question):
            return source_type in KAIST_GLOBAL_SOURCE_TYPES

        # 4. AI대학 전체 질문이면 AI대학 4개 학과 문서만 허용
        if self._is_ai_college_scope_question(question):
            if dept in AI_COLLEGE_DEPT_CODES:
                return True

            if department_code_meta in AI_COLLEGE_DEPT_CODES:
                return True

            if dept_name in AI_COLLEGE_DEPT_NAMES:
                return True

            if department in AI_COLLEGE_DEPT_NAMES:
                return True

            # AI대학 질문 중 홈페이지/입학처/링크/주소 같은 보조 정보는
            # KAIST 기본정보 문서를 허용한다.
            if source_type in KAIST_GLOBAL_SOURCE_TYPES:
                if any(
                    keyword in question
                    for keyword in ["홈페이지", "입학처", "링크", "URL", "주소"]
                ):
                    return True

            return False

        # 5. 일반 질문은 기존 검색 결과 허용
        return True

    def _filter_items_for_question(
        self,
        items: list[RetrievedVectorDocument],
        analysis: QueryAnalysis,
        question: str,
    ) -> list[RetrievedVectorDocument]:
        return [
            item
            for item in items
            if self._is_allowed_item_for_question(
                item=item,
                analysis=analysis,
                question=question,
            )
        ]

    def _search_with_fallback(
        self,
        search_query: str,
        search_plan: list[tuple[SearchStage, dict[str, Any] | None]],
        analysis: QueryAnalysis,
        question: str,
    ) -> tuple[
        list[RetrievedVectorDocument],
        list[SearchAttempt],
        bool,
        list[str],
    ]:
        results: list[RetrievedVectorDocument] = []
        attempts: list[SearchAttempt] = []
        seen_keys: set[str] = set()
        warnings: list[str] = []

        used_fallback = False

        for stage_index, (search_stage, metadata_filter) in enumerate(search_plan):
            if stage_index > 0:
                used_fallback = True

            stage_results = self._search_chroma_once(
                search_query=search_query,
                metadata_filter=metadata_filter,
                search_stage=search_stage,
            )

            stage_results = self._filter_items_for_question(
            items=stage_results,
            analysis=analysis,
            question=question,
            )

            attempts.append(
                SearchAttempt(
                    search_stage=search_stage,
                    metadata_filter=metadata_filter,
                    result_count=len(stage_results),
                )
            )

            for item in stage_results:
                key = self._make_document_key(item.document)

                if key in seen_keys:
                    continue

                seen_keys.add(key)
                results.append(item)

                if len(results) >= self._candidate_limit():
                    break

            if self._should_stop_search(
                stage_index=stage_index,
                current_result_count=len(results),
            ):
                break

        if used_fallback:
            warnings.append(
                "strict_filter 검색 결과가 부족하여 fallback 검색이 사용되었습니다. "
                "fallback 결과에는 원래 content_type과 다른 문서가 포함될 수 있습니다."
            )

        return results, attempts, used_fallback, warnings

    def _should_stop_search(
        self,
        stage_index: int,
        current_result_count: int,
    ) -> bool:
        if not self.config.use_fallback:
            return True

        if current_result_count >= self._candidate_limit():
            return True

        if self.config.fallback_trigger_mode == "only_when_empty":
            if current_result_count > 0:
                return True

            return False

        if self.config.fallback_trigger_mode == "below_min_results":
            if current_result_count >= self.config.min_results_before_fallback:
                return True

            return False

        return False

    def _rerank_results(
        self,
        question: str,
        analysis: QueryAnalysis,
        items: list[RetrievedVectorDocument],
    ) -> list[RetrievedVectorDocument]:
        if self.config.use_lightweight_reranker:
            return self.reranker.rerank(
                question=question,
                analysis=analysis,
                items=items,
            )

        return sorted(
            items,
            key=lambda item: item.score if item.score is not None else float("inf"),
        )

    def _candidate_limit(self) -> int:
        multiplier = max(self.config.candidate_multiplier, 1)

        return max(
            self.config.search_k,
            min(self.config.fetch_k, self.config.search_k * multiplier),
        )

    def _select_final_results(
        self,
        analysis: QueryAnalysis,
        question: str,
        items: list[RetrievedVectorDocument],
    ) -> list[RetrievedVectorDocument]:
        if analysis.intent != "admission_info":
            return items[: self.config.search_k]

        return self._diversify_admission_results(
            question=question,
            items=items,
        )

    def _diversify_admission_results(
        self,
        question: str,
        items: list[RetrievedVectorDocument],
    ) -> list[RetrievedVectorDocument]:
        selected: list[RetrievedVectorDocument] = []
        selected_keys: set[tuple[str, str, str]] = set()
        ranked_items = self._rank_admission_items_for_question(
            question=question,
            items=items,
        )

        priority_types = [
            "eligibility",
            "schedule",
            "advisor_matching",
            "scholarship",
        ]

        for admission_type in priority_types:
            for item in ranked_items:
                metadata = item.document.metadata

                if metadata.get("admission_type") != admission_type:
                    continue

                key = self._make_admission_selection_key(item)

                if key in selected_keys:
                    continue

                selected.append(item)
                selected_keys.add(key)
                break

        for item in ranked_items:
            if len(selected) >= self.config.search_k:
                break

            key = self._make_admission_selection_key(item)

            if key in selected_keys:
                continue

            selected.append(item)
            selected_keys.add(key)

        return selected[: self.config.search_k]

    def _rank_admission_items_for_question(
        self,
        question: str,
        items: list[RetrievedVectorDocument],
    ) -> list[RetrievedVectorDocument]:
        original_rank = {
            id(item): index
            for index, item in enumerate(items)
        }

        return sorted(
            items,
            key=lambda item: (
                self._admission_question_match_score(question, item),
                -original_rank[id(item)],
            ),
            reverse=True,
        )

    def _admission_question_match_score(
        self,
        question: str,
        item: RetrievedVectorDocument,
    ) -> float:
        metadata = item.document.metadata
        title = str(metadata.get("title") or "")
        section = str(metadata.get("section") or "")
        admission_type = str(metadata.get("admission_type") or "")

        score = 0.0

        if "석사" in question:
            if title == "석사과정":
                score += 5.0
            elif "석박사" in title or "석·박" in title:
                score += 2.0
            elif "박사" in title:
                score -= 3.0

        if "박사" in question and "석사" not in question and "박사" in title:
            score += 3.0

        if any(keyword in question for keyword in ["지원 자격", "지원자격", "자격"]):
            if admission_type == "eligibility" or section == "지원 자격":
                score += 2.0

        if any(keyword in question for keyword in ["일정", "접수", "전형"]):
            if admission_type == "schedule":
                score += 2.0

        if item.rerank_score:
            score += item.rerank_score
        elif item.score is not None:
            score += 1 / (1 + max(item.score, 0.0))

        return score

    def _make_admission_selection_key(
        self,
        item: RetrievedVectorDocument,
    ) -> tuple[str, str, str]:
        metadata = item.document.metadata

        return (
            str(metadata.get("admission_type") or ""),
            str(metadata.get("section") or ""),
            str(metadata.get("title") or ""),
        )
    
    def _search_chroma_once(
        self,
        search_query: str,
        metadata_filter: dict[str, Any] | None,
        search_stage: SearchStage,
    ) -> list[RetrievedVectorDocument]:
        search_kwargs: dict[str, Any] = {
            "query": search_query,
            "k": self.config.fetch_k,
        }

        if metadata_filter:
            search_kwargs["filter"] = metadata_filter

        raw_results = self.vectorstore.similarity_search_with_score(**search_kwargs)

        return [
            RetrievedVectorDocument(
                document=document,
                score=score,
                search_stage=search_stage,
            )
            for document, score in raw_results
        ]

    def _make_document_key(self, document: Document) -> str:
        metadata = document.metadata

        return str(
            metadata.get("content_hash")
            or metadata.get("original_id")
            or hash(document.page_content)
        )


def run_examples() -> None:
    config = VectorRetrieverConfig(
        search_k=3,
        fetch_k=10,
        min_results_before_fallback=2,
        use_rewritten_question=True,
        use_fallback=True,
        fallback_trigger_mode="below_min_results",
        use_lightweight_reranker=True,
    )

    retriever = VectorRetriever(config=config)

    example_questions = [
        "AI컴퓨팅학과 석사 지원 자격은?",
        "AI시스템학과 교과목 알려줘",
        "AI시스템학과 교과목 목록과 각 과목 설명도 알려줘",
        "AX학과 교수진 이메일 목록 보여줘",
        "AX학과 교수 연구분야도 설명해줘",
        "KAIST 학과 사무실 전화번호 알려줘",
        "AI컴퓨팅학과 학과설명회 정보 알려줘",
        "교수진도 알려줘",
    ]

    for question in example_questions:
        result = retriever.retrieve(
            question,
            force_vector_search=True,
        )

        print("=" * 100)
        print(f"질문: {question}")
        print(result.to_debug_dict())

        if result.documents:
            context = retriever.format_documents_for_context(result.documents)
            print("\n[Context Preview]")
            print(context[:1000])


if __name__ == "__main__":
    run_examples()

