import os
import sys
from pathlib import Path

# Windows에서 hnswlib(chromadb C++ 확장)의 OpenMP 멀티스레딩 크래시 방지
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.styles import load_css
from components.layout import render_topbar, render_page_header, render_source_cards, render_back_home
from src.rag.query_analyzer import DEPARTMENTS
from src.rag.rag_pipeline import RagPipeline, create_default_pipeline

st.set_page_config(
    page_title="RAG Chatbot | KAIST AI RAG Guide",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()
render_topbar()
render_back_home()

render_page_header(
    kicker="RAG CHATBOT",
    title="KAIST AI College RAG Chatbot",
    description="입학, 연구 분야, 교수진, 교과목, 행사 정보를 검색 결과와 출처 기반으로 답변합니다.",
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "안녕하세요. KAIST AI College RAG Guide입니다. 입학, 연구 분야, 교수진, 교과목, 행사 정보에 대해 질문해보세요.",
            "sources": [],
            "warnings": [],
        }
    ]

if "previous_department_code" not in st.session_state:
    st.session_state.previous_department_code = None

if "pending_clarification" not in st.session_state:
    st.session_state.pending_clarification = None

if "answer_cache" not in st.session_state:
    st.session_state.answer_cache = {}

if "use_answer_cache" not in st.session_state:
    st.session_state.use_answer_cache = True

if "pending_user_question" not in st.session_state:
    st.session_state.pending_user_question = None

if "_answer_in_progress" not in st.session_state:
    st.session_state._answer_in_progress = False

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

# 처리 중이지 않을 때(대기 질문 없음) 자동으로 잠금 해제
if not st.session_state.get("pending_user_question") and not st.session_state.get("_answer_in_progress"):
    st.session_state.is_processing = False


@st.cache_resource(show_spinner=False)
def get_pipeline() -> RagPipeline:
    return create_default_pipeline(
        include_sql=True,
        include_debug_context=False,
        preload_vector_retriever=True,
        preload_answer_generator=False,
    )


def format_sources_for_cards(sources):
    cards = []

    for source in sources:
        metadata = source.get("metadata", {}) or {}
        department = source.get("department") or metadata.get("dept") or ""
        content_type = source.get("content_type") or metadata.get("content_type") or ""
        crawled_at = metadata.get("crawled_at") or ""
        page = metadata.get("page") or ""

        meta_parts = [
            part
            for part in [
                department,
                content_type,
                f"수집일 {crawled_at}" if crawled_at else "",
                f"p.{page}" if page else "",
            ]
            if part
        ]
        source_url = source.get("source", "")
        source_url = source_url if source_url.startswith(("http://", "https://")) else ""

        cards.append(
            {
                "title": source.get("title") or source.get("source") or "Retrieved Source",
                "meta": " · ".join(meta_parts) if meta_parts else source.get("source_type", "RAG Source"),
                "url": source_url,
            }
        )

    return cards


def find_department_in_text(text: str):
    lowered_text = text.lower()

    for department in DEPARTMENTS:
        for keyword in department.keywords:
            if keyword.lower() in lowered_text:
                return department

    return None


def is_all_departments_followup(question: str) -> bool:
    all_keywords = [
        "다",
        "전체",
        "전부",
        "모두",
        "모든",
        "각 학과",
        "학과별",
        "네 개",
        "4개",
    ]

    return any(keyword in question for keyword in all_keywords)


def remember_clarification_if_needed(result, original_question: str) -> None:
    if result.needs_clarification:
        st.session_state.pending_clarification = {
            "question": original_question,
            "intent": result.intent,
            "missing_fields": result.analysis.missing_fields,
        }
        return

    st.session_state.pending_clarification = None


def build_contextual_question(question: str) -> tuple[str, bool]:
    pending = st.session_state.pending_clarification

    if not pending:
        return question, False

    missing_fields = pending.get("missing_fields", [])

    if "department" not in missing_fields:
        return question, False

    department = find_department_in_text(question)

    if department:
        return f"{department.name} {pending['question']}", True

    return question, False


def run_for_all_departments(
    question: str,
    pending_question: str = "",
):
    pipeline = get_pipeline()
    answers = []
    all_sources = []
    all_warnings = []
    combined_question = " ".join(
        part
        for part in [pending_question, question]
        if part
    )

    for department in DEPARTMENTS:
        department_question = f"{department.name} {combined_question}"
        result = pipeline.run(department_question)

        answers.append(f"### {department.name}\n{result.answer}")
        all_sources.extend(result.sources)
        all_warnings.extend(result.warnings)

    return {
        "answer": "\n\n".join(answers),
        "sources": format_sources_for_cards(all_sources),
        "warnings": deduplicate_strings(all_warnings),
    }


def deduplicate_strings(values):
    seen = set()
    results = []

    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        results.append(value)

    return results


def build_cache_key(
    question: str,
    previous_department_code: str | None = None,
    scope: str = "single",
) -> str:
    normalized_question = " ".join(question.split())
    previous_department_code = previous_department_code or ""

    return f"{scope}|dept={previous_department_code}|q={normalized_question}"


def result_to_message_payload(result):
    return {
        "role": "assistant",
        "content": result.answer,
        "sources": format_sources_for_cards(result.sources),
        "warnings": result.warnings,
        "cached": False,
    }


def get_cached_payload(cache_key: str):
    if not st.session_state.use_answer_cache:
        return None

    cached = st.session_state.answer_cache.get(cache_key)

    if not cached:
        return None

    return {
        **cached,
        "cached": True,
    }


def remember_payload(cache_key: str, payload: dict) -> dict:
    if not st.session_state.use_answer_cache:
        return payload

    cache_payload = {
        "role": payload["role"],
        "content": payload["content"],
        "sources": payload.get("sources", []),
        "warnings": payload.get("warnings", []),
        "state": payload.get("state", {}),
    }
    st.session_state.answer_cache[cache_key] = cache_payload

    return payload


def attach_current_state(payload: dict) -> dict:
    payload["state"] = {
        "previous_department_code": st.session_state.previous_department_code,
        "pending_clarification": st.session_state.pending_clarification,
    }

    return payload


def apply_cached_state(payload: dict) -> None:
    state = payload.get("state", {}) or {}

    if "previous_department_code" in state:
        st.session_state.previous_department_code = state["previous_department_code"]

    if "pending_clarification" in state:
        st.session_state.pending_clarification = state["pending_clarification"]


def should_answer_all_departments(question: str, pending: dict | None) -> bool:
    if find_department_in_text(question):
        return False

    if not is_all_departments_followup(question):
        return False

    if pending and "department" in pending.get("missing_fields", []):
        return True

    analysis = get_pipeline().classify_question(question)

    return (
        analysis.intent != "general_info"
        and "department" in analysis.missing_fields
    )


def build_answer_payload(question: str):
    pipeline = get_pipeline()

    pending = st.session_state.pending_clarification

    if should_answer_all_departments(question, pending):
        pending_question = pending["question"] if pending else ""
        cache_key = build_cache_key(
            question=" ".join(
                part
                for part in [pending_question, question]
                if part
            ),
            scope="all_departments",
        )
        cached_payload = get_cached_payload(cache_key)

        if cached_payload:
            apply_cached_state(cached_payload)
            st.session_state.pending_clarification = None
            st.session_state.previous_department_code = None
            return cached_payload

        result_payload = run_for_all_departments(
            question=question,
            pending_question=pending_question,
        )
        st.session_state.pending_clarification = None
        st.session_state.previous_department_code = None

        return remember_payload(
            cache_key=cache_key,
            payload=attach_current_state(
                {
                    "role": "assistant",
                    "content": result_payload["answer"],
                    "sources": result_payload["sources"],
                    "warnings": result_payload["warnings"],
                    "cached": False,
                }
            ),
        )

    effective_question, used_pending_context = build_contextual_question(question)
    previous_department_code = st.session_state.previous_department_code
    cache_key = build_cache_key(
        question=effective_question,
        previous_department_code=previous_department_code,
    )
    cached_payload = get_cached_payload(cache_key)

    if cached_payload:
        apply_cached_state(cached_payload)
        return cached_payload

    result = pipeline.run(
        effective_question,
        previous_department_code=previous_department_code,
    )
    if result.department_code:
        st.session_state.previous_department_code = result.department_code

    remember_clarification_if_needed(
        result=result,
        original_question=effective_question if used_pending_context else question,
    )

    return remember_payload(
        cache_key=cache_key,
        payload=attach_current_state(result_to_message_payload(result)),
    )


def render_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("cached"):
            st.caption("이전 동일 질문의 답변을 다시 사용했습니다.")
        if message.get("warnings"):
            with st.expander("Warnings"):
                for warning in message["warnings"]:
                    st.write(warning)
        if message.get("sources"):
            render_source_cards(message["sources"])


def queue_question(question: str) -> None:
    st.session_state.pending_user_question = question
    st.session_state.is_processing = True


def process_pending_question(question: str) -> None:
    st.session_state._answer_in_progress = True
    user_message = {"role": "user", "content": question, "sources": [], "warnings": []}
    st.session_state.messages.append(user_message)
    render_message(user_message)

    with st.chat_message("assistant"):
        with st.spinner("답변을 생성하는 중입니다..."):
            try:
                payload = build_answer_payload(question=question)
            except BaseException as exc:
                exc_type = type(exc).__name__
                exc_mod = type(exc).__module__ or ""
                if "streamlit" in exc_mod.lower() or exc_type in (
                    "RerunException", "StopException", "StreamlitStopException",
                    "RerunData", "StopExecutionException",
                ):
                    st.session_state._answer_in_progress = False
                    raise
                payload = {
                    "role": "assistant",
                    "content": "답변 생성 중 오류가 발생했습니다. 환경 설정과 vectorstore 상태를 확인해주세요.",
                    "sources": [],
                    "warnings": [str(exc)],
                }

        st.markdown(payload["content"])

        if payload.get("cached"):
            st.caption("이전 동일 질문의 답변을 다시 사용했습니다.")

        if payload.get("warnings"):
            with st.expander("오류 내용"):
                for w in payload["warnings"]:
                    st.write(w)

        if payload.get("sources"):
            render_source_cards(payload["sources"])

        st.session_state.messages.append(payload)

    # 처리 완료: 플래그 초기화 후 rerun → chat_input이 disabled=False로 재렌더링됨
    st.session_state._answer_in_progress = False
    st.session_state.is_processing = False
    st.rerun()

st.markdown('<div class="section-title">Quick Questions</div>', unsafe_allow_html=True)
control_col, spacer_col = st.columns([1, 3])
with control_col:
    st.toggle("동일 질문 캐시", key="use_answer_cache")
with spacer_col:
    if st.button("캐시 비우기", use_container_width=False):
        st.session_state.answer_cache = {}
        st.rerun()

q1, q2, q3 = st.columns(3, gap="medium")
with q1:
    if st.button("입학 서류가 궁금해요", use_container_width=True, disabled=st.session_state.is_processing):
        queue_question("KAIST AI대학원 지원 시 어떤 서류가 필요한가요?")
        st.rerun()
with q2:
    if st.button("연구 분야 알려줘", use_container_width=True, disabled=st.session_state.is_processing):
        queue_question("KAIST AI College에는 어떤 연구 분야가 있나요?")
        st.rerun()
with q3:
    if st.button("교수님 찾는 기준은?", use_container_width=True, disabled=st.session_state.is_processing):
        queue_question("관심 교수님을 고를 때 어떤 기준으로 보면 좋나요?")
        st.rerun()

q4, q5, q6 = st.columns(3, gap="medium")
with q4:
    if st.button("교과목 정보 알려줘", use_container_width=True, disabled=st.session_state.is_processing):
        queue_question("KAIST AI College 교과목에는 어떤 것들이 있나요?")
        st.rerun()
with q5:
    if st.button("설명회나 행사가 있나요?", use_container_width=True, disabled=st.session_state.is_processing):
        queue_question("KAIST AI College 관련 설명회나 행사가 있나요?")
        st.rerun()
with q6:
    if st.button("RAG 서비스 설명해줘", use_container_width=True, disabled=st.session_state.is_processing):
        queue_question("이 RAG 챗봇 서비스는 어떤 방식으로 작동하나요?")
        st.rerun()

st.markdown('<div class="section-title">Chat</div>', unsafe_allow_html=True)
for message in st.session_state.messages:
    render_message(message)

pending_user_question = st.session_state.pending_user_question

if pending_user_question:
    st.session_state.pending_user_question = None
    process_pending_question(pending_user_question)

user_input = st.chat_input("KAIST AI College에 대해 질문해보세요.", disabled=st.session_state.is_processing)
if user_input:
    queue_question(user_input)
    st.rerun()

st.divider()
center = st.columns([1, 1, 1])[1]
with center:
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "대화가 초기화되었습니다. 다시 질문해보세요.",
                "sources": [],
                "warnings": [],
            }
        ]
        st.session_state.previous_department_code = None
        st.session_state.pending_clarification = None
        st.session_state.pending_user_question = None
        st.session_state.answer_cache = {}
        st.rerun()
