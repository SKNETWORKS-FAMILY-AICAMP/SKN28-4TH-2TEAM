import streamlit as st

from components.styles import load_css
from components.layout import render_topbar, render_page_header, render_info_card, render_back_home
from data.demo_knowledge import get_departments, get_representative_courses, get_department_heads

st.set_page_config(
    page_title="Departments | KAIST AI RAG Guide",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()
render_topbar()
render_back_home()

render_page_header(
    kicker="DEPARTMENTS & RESEARCH AREAS",
    title="Departments 소개",
    description="KAIST AI College의 학과, 연구 분야, 교수진, 교과목 데이터를 사용자 친화적인 카드형 화면으로 재구성했습니다.",
)

st.markdown('<div class="section-title">Department Overview</div>', unsafe_allow_html=True)
departments = get_departments()

DEPT_ICONS = {
    "AI컴퓨팅학과": "🖥️",
    "AI시스템학과": "⚙️",
    "AI미래학과": "🔭",
    "AX학과": "🔄",
}

if departments:
    col_a, col_b = st.columns(2, gap="medium")
    for idx, dept in enumerate(departments):
        col = col_a if idx % 2 == 0 else col_b
        dept_name = dept.get("dept_name", "Department")
        icon = DEPT_ICONS.get(dept_name, "🎓")
        summary = dept.get("summary", "소개 데이터가 준비 중입니다.")
        source_url = dept.get("source_url", "")
        link = f'<a href="{source_url}" target="_blank" style="font-size:0.8rem;">홈페이지 바로가기 →</a>' if source_url else ""
        with col:
            st.markdown(
                f"""
                <div class="info-card start-card">
                    <div style="font-size:2rem; margin-bottom:8px;">{icon}</div>
                    <h3 style="margin-bottom:6px;">{dept_name}</h3>
                    <p style="margin-bottom:10px;">{summary}</p>
                    {link}
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("학과 소개 데이터를 찾을 수 없습니다.")

st.markdown('<div class="section-title">Representative Faculty</div>', unsafe_allow_html=True)
heads = get_department_heads()
if heads:
    cols = st.columns(len(heads), gap="medium")
    for idx, person in enumerate(heads):
        with cols[idx]:
            name = person.get("name_ko", "")
            dept_name = person.get("dept_name", "")
            homepage = person.get("homepage", "")
            role_label = person.get("role_normalized", "교수")
            title = f'<a href="{homepage}" target="_blank">{name}</a>' if homepage else name
            st.markdown(
                f"""
                <div class="info-card start-card">
                    <div style="font-size:0.75rem; color:#2563eb; font-weight:600; margin-bottom:6px;">{dept_name}</div>
                    <h3 style="margin-bottom:4px;">{title}</h3>
                    <p style="margin:0; font-size:0.85rem; color:#6b7280;">{role_label}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("교수진 정보를 확인할 수 없습니다.")

st.markdown('<div class="section-title">Representative Courses</div>', unsafe_allow_html=True)
courses = get_representative_courses(limit=6)
if courses:
    for course in courses:
        dept_name = course.get("dept_name", "")
        course_level = course.get("course_level", "")
        course_code = course.get("course_code", "")
        course_name = course.get("course_name", "")
        course_type = course.get("course_type", "")
        credit = course.get("credit", "")
        source_url = course.get("source_url", "")
        title = f'<a href="{source_url}" target="_blank">{course_code} {course_name}</a>' if source_url else f"{course_code} {course_name}"
        st.markdown(
            f"""
            <div class="info-card">
                <h3>{title}</h3>
                <p>{dept_name} · {course_level} · {course_type} · {credit} credits</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("교과목 데이터를 찾을 수 없습니다.")

st.markdown('<div class="section-title">How This Connects to RAG</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2, gap="medium")
with c1:
    render_info_card("검색 대상 문서", "학과 소개, 교수진 정보, 교과목 안내, 연구 키워드 데이터는 RAG 검색의 문서 후보로 활용됩니다.")
with c2:
    render_info_card("사용자 질문 예시", "예비 지원자는 “NLP 연구를 하는 교수님은?”, “AI시스템 관련 과목은?”처럼 질문할 수 있습니다.")
