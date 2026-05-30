import streamlit as st

from components.styles import load_css
from components.layout import render_topbar, render_page_header, render_info_card, render_back_home
from data.demo_knowledge import get_departments, get_representative_courses, get_representative_people

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

if departments:
    for dept in departments:
        st.markdown(
            f"""
            <div class="info-card">
                <h3>{dept.get('dept_name', 'Department')}</h3>
                <p>{dept.get('summary', '소개 데이터가 준비 중입니다.')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("학과 소개 데이터를 찾을 수 없습니다. data/raw 폴더에 CSV 파일을 넣어주세요.")

st.markdown('<div class="section-title">Representative Faculty</div>', unsafe_allow_html=True)
people = get_representative_people(limit=6)
if people:
    cols = st.columns(3, gap="medium")
    for idx, person in enumerate(people):
        with cols[idx % 3]:
            name = person.get("name", "")
            dept_name = person.get("dept_name", "")
            role = person.get("role", "")
            research_area = person.get("research_area", "")
            homepage = person.get("homepage", "") or person.get("source_url", "")
            title = f'<a href="{homepage}" target="_blank">{name}</a>' if homepage else name
            st.markdown(
                f"""
                <div class="info-card">
                    <h3>{title}</h3>
                    <p><strong>{dept_name}</strong><br>{role}<br>{research_area if research_area else 'Research area data is not available.'}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("교수진 데이터를 찾을 수 없습니다.")

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
