import streamlit as st

from ui.components.styles import load_css
from ui.components.layout import render_topbar, render_page_header, render_info_card, render_back_home
from ui.demo_knowledge import get_data_summary

st.set_page_config(
    page_title="AI College Intro | KAIST AI RAG Guide",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()
render_topbar()
render_back_home()

render_page_header(
    kicker="ABOUT KAIST AI COLLEGE",
    title="KAIST AI College 소개",
    description="KAIST AI College 정보를 예비 지원자 관점에서 탐색할 수 있도록 구성한 문서 기반 안내 서비스입니다.",
)

render_info_card(
    "서비스 목적",
    "대학원 지원자는 공식 홈페이지, 모집요강, 교수진 소개, 연구실 페이지, 교과목 정보 등 여러 문서에 흩어진 정보를 직접 찾아야 합니다. 이 프로젝트는 이러한 정보를 질문 기반 인터페이스로 탐색하는 경험을 제공합니다.",
)

st.markdown('<div class="section-title">Core Experience</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    render_info_card("Education", "AI 핵심 이론과 응용 역량을 함께 다루는 교육 정보를 탐색합니다.")
with c2:
    render_info_card("Research", "기계학습, 자연어처리, 컴퓨터비전, 로보틱스 등 연구 분야 탐색을 지원합니다.")
with c3:
    render_info_card("Guidance", "입학, 교수진, 교과목, 연구 분야 정보를 질문 형태로 확인합니다.")

summary = get_data_summary()

st.markdown('<div class="section-title">Demo Data Overview</div>', unsafe_allow_html=True)
st.markdown('<div class="metric-wrap">', unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("Admissions", summary.get("admissions", 0))
with m2:
    st.metric("Courses", summary.get("courses", 0))
with m3:
    st.metric("People", summary.get("people", 0))
with m4:
    st.metric("Events", summary.get("events", 0))
with m5:
    st.metric("RAG Chunks", summary.get("rag_chunks", 0))
st.markdown('</div>', unsafe_allow_html=True)
