import streamlit as st

from components.styles import load_css
from components.layout import render_topbar, render_page_header, render_source_cards, render_back_home
from data.demo_knowledge import get_demo_response

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
    kicker="RAG CHATBOT DEMO",
    title="KAIST AI College RAG Chatbot",
    description="입학, 연구 분야, 교수진, 교과목, 행사 정보를 질문 형태로 탐색하는 발표용 챗봇입니다.",
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "안녕하세요. KAIST AI College RAG Guide입니다. 입학, 연구 분야, 교수진, 교과목, 행사 정보에 대해 질문해보세요.",
            "sources": [],
        }
    ]


def add_question(question: str):
    result = get_demo_response(question)
    st.session_state.messages.append({"role": "user", "content": question, "sources": []})
    st.session_state.messages.append({"role": "assistant", "content": result["answer"], "sources": result["sources"]})

st.markdown('<div class="section-title">Quick Questions</div>', unsafe_allow_html=True)
q1, q2, q3 = st.columns(3, gap="medium")
with q1:
    if st.button("입학 서류가 궁금해요", use_container_width=True):
        add_question("KAIST AI대학원 지원 시 어떤 서류가 필요한가요?")
        st.rerun()
with q2:
    if st.button("연구 분야 알려줘", use_container_width=True):
        add_question("KAIST AI College에는 어떤 연구 분야가 있나요?")
        st.rerun()
with q3:
    if st.button("교수님 찾는 기준은?", use_container_width=True):
        add_question("관심 교수님을 고를 때 어떤 기준으로 보면 좋나요?")
        st.rerun()

q4, q5, q6 = st.columns(3, gap="medium")
with q4:
    if st.button("교과목 정보 알려줘", use_container_width=True):
        add_question("KAIST AI College 교과목에는 어떤 것들이 있나요?")
        st.rerun()
with q5:
    if st.button("설명회나 행사가 있나요?", use_container_width=True):
        add_question("KAIST AI College 관련 설명회나 행사가 있나요?")
        st.rerun()
with q6:
    if st.button("RAG 서비스 설명해줘", use_container_width=True):
        add_question("이 RAG 챗봇 서비스는 어떤 방식으로 작동하나요?")
        st.rerun()

st.markdown('<div class="section-title">Chat</div>', unsafe_allow_html=True)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            render_source_cards(message["sources"])

user_input = st.chat_input("KAIST AI College에 대해 질문해보세요.")
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
            }
        ]
        st.rerun()
