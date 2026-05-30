from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

from components.styles import load_css
from components.layout import (
    render_topbar,
    render_page_header,
    render_source_cards,
    render_back_home,
)

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.rag_pipeline import RAGPipeline


st.set_page_config(
    page_title="RAG Chatbot | KAIST AI RAG Guide",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource
def get_pipeline() -> RAGPipeline:
    return RAGPipeline()


def add_question(question: str) -> None:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
            "sources": [],
            "warnings": [],
        }
    )

    try:
        result = get_pipeline().ask(question)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result.answer,
                "sources": result.sources,
                "warnings": result.warnings,
                "debug": result.debug,
            }
        )

    except Exception as error:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "답변 생성 중 오류가 발생했습니다.\n\n"
                    f"오류 내용: `{type(error).__name__}: {error}`"
                ),
                "sources": [],
                "warnings": [],
                "debug": {},
            }
        )


load_css()
render_topbar()
render_back_home()

render_page_header(
    kicker="RAG CHATBOT",
    title="KAIST AI College RAG Chatbot",
    description="입학, 교수진, 교과목, 행사 정보를 검색하고 출처 기반으로 답변하는 RAG 챗봇입니다.",
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "안녕하세요. KAIST AI College RAG 챗봇입니다. 학과명과 함께 입학, 교수진, 교과목, 행사 정보를 질문해보세요.",
            "sources": [],
            "warnings": [],
        }
    ]

st.markdown('<div class="section-title">Quick Questions</div>', unsafe_allow_html=True)

q1, q2, q3 = st.columns(3, gap="medium")
with q1:
    if st.button("AI컴퓨팅학과 석사 지원 자격", use_container_width=True):
        add_question("AI컴퓨팅학과 석사 지원 자격은?")
        st.rerun()

with q2:
    if st.button("AI컴퓨팅학과 학과설명회", use_container_width=True):
        add_question("AI컴퓨팅학과 학과설명회 정보 알려줘")
        st.rerun()

with q3:
    if st.button("AX학과 교수 연구분야", use_container_width=True):
        add_question("AX학과 교수 연구분야도 설명해줘")
        st.rerun()

q4, q5, q6 = st.columns(3, gap="medium")
with q4:
    if st.button("AI시스템학과 교과목", use_container_width=True):
        add_question("AI시스템학과 교과목 목록과 각 과목 설명도 알려줘")
        st.rerun()

with q5:
    if st.button("AI미래학과 입학 일정", use_container_width=True):
        add_question("AI미래학과 입학 일정 알려줘")
        st.rerun()

with q6:
    if st.button("교수진 질문 테스트", use_container_width=True):
        add_question("교수진도 알려줘")
        st.rerun()

st.markdown('<div class="section-title">Chat</div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("warnings"):
            with st.expander("주의사항", expanded=False):
                for warning in message["warnings"]:
                    st.warning(warning)

        if message.get("sources"):
            render_source_cards(message["sources"])

        if message.get("debug"):
            with st.expander("Debug", expanded=False):
                st.json(message["debug"])

user_input = st.chat_input("예: AI컴퓨팅학과 석사 지원 자격은?")
if user_input:
    add_question(user_input)
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
        st.rerun()