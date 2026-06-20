from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from math import sqrt
from typing import Any, Literal


RouteType = Literal["sql", "vector", "hybrid", "clarify"]

AmbiguityType = Literal[
    "department_scope",
    "missing_department",
    "missing_intent",
    "too_broad",
    "comparison_criterion",
    "personal_recommendation",
    "unclear_reference",
    "unsupported_kaist_department",
    "unsupported_fact",
    "off_topic",
]

IntentType = Literal[
    "admission_info",
    "course_info",
    "person_info",
    "office_contact_info",
    "event_info",
    "asset_or_link_info",
    "department_overview",
    "kaist_profile_info",
    "kaist_statistics_info",
    "kaist_link_info",
    "general_info",
]

ContentType = Literal[
    "admission",
    "course",
    "person",
    "office_contact",
    "event",
    "link",
    "kaist_profile",
    "kaist_statistics",
    "mixed_media",
]


@dataclass(frozen=True)
class DepartmentInfo:
    name: str
    code: str
    keywords: list[str]


@dataclass(frozen=True)
class IntentRule:
    intent: IntentType
    content_type: ContentType | None
    description: str
    keywords: list[str]
    vector_search_terms: str
    sql_table_hint: str | None
    sql_task_hint: str | None


@dataclass(frozen=True)
class IntentExample:
    text: str
    intent: IntentType = "general_info"
    ambiguity_type: AmbiguityType | None = None


@dataclass(frozen=True)
class IntentExampleMatch:
    example: IntentExample
    score: float


@dataclass
class QueryAnalysis:
    original_question: str
    normalized_question: str

    route: RouteType
    route_reason: str

    display_question: str
    rewritten_question: str

    department_name: str | None = None
    department_code: str | None = None
    unsupported_department_name: str | None = None

    intent: IntentType = "general_info"
    intent_description: str = "일반 정보 질문"
    content_type: ContentType | None = None
    # 다중 정보유형: 주 intent 포함 전체 intent 목록(근거검사 등에서 사용). 길이 1이면 단일.
    intents: list[IntentType] = field(default_factory=list)

    metadata_filter: dict[str, Any] | None = None

    sql_table_hint: str | None = None
    sql_task_hint: str | None = None
    sql_conditions: dict[str, Any] = field(default_factory=dict)

    # 다중 정보유형 지원: 스칼라 content_type / sql_table_hint의 집합 버전.
    # 단일 intent 질문은 길이 1로 채워져 기존 동작과 동일하다(동작 보존).
    content_types: list[ContentType] = field(default_factory=list)
    sql_table_hints: list[str] = field(default_factory=list)
    sql_task_hints: list[str] = field(default_factory=list)
    # 다중 intent 질문에서는 다른 의도의 단어가 키워드 LIKE 필터를 오염시키므로
    # (예: person 조회에 '과목'이 name LIKE로 걸림) 키워드 필터를 끄고 dept만 사용한다.
    suppress_sql_keyword_filter: bool = False

    needs_sql: bool = False
    needs_vector: bool = False

    is_ambiguous: bool = False
    ambiguity_type: AmbiguityType | None = None
    missing_fields: list[str] = field(default_factory=list)
    clarifying_message: str | None = None

    matched_keywords: list[str] = field(default_factory=list)
    semantic_match_intent: str | None = None
    semantic_match_ambiguity_type: str | None = None
    semantic_match_score: float | None = None
    semantic_match_example: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEPARTMENTS = [
    DepartmentInfo(
        name="AI컴퓨팅학과",
        code="aic",
        keywords=[
            "AI컴퓨팅학과",
            "AI 컴퓨팅학과",
            "AI컴퓨팅",
            "AI 컴퓨팅",
            "AIC",
            "aic",
        ],
    ),
    DepartmentInfo(
        name="AI시스템학과",
        code="ai_systems",
        keywords=[
            "AI시스템학과",
            "AI 시스템학과",
            "AI시스템",
            "AI 시스템",
            "AI Systems",
            "AI systems",
            "ai systems",
            "ai_systems",
        ],
    ),
    DepartmentInfo(
        name="AX학과",
        code="ax",
        keywords=[
            "AX학과",
            "AX 학과",
            "AX",
            "ax",
        ],
    ),
    DepartmentInfo(
        name="AI미래학과",
        code="fx",
        keywords=[
            "AI미래학과",
            "AI 미래학과",
            "AI미래",
            "AI 미래",
            "FX",
            "fx",
        ],
    ),
]

AI_COLLEGE_SCOPE_KEYWORDS = [
    "AI대학",
    "AI 대학",
    "KAIST AI대학",
    "카이스트 AI대학",
    "AI 관련 학과",
    "AI 학과",
    "AI학과",
    "인공지능 학과",
    "인공지능학과",
    "수집된 AI 관련 학과",
    "전체 학과",
    "모든 학과",
    "각 학과",
    "학과별",
    "학과들",
    "학과들을",
]

KAIST_ACADEMIC_ORG_KEYWORDS = [
    "공과대학",
    "자연과학대학",
    "생명과학기술대학",
    "생명과학 기술대학",
    "인문사회융합과학대학",
    "인문사회 융합과학대학",
    "경영대학",
    "단과대학",
    "학과/프로그램",
    "학과 프로그램",
    "학과 목록",
    "학과 종류",
    "카이스트 학과",
    "KAIST 학과",
]

UNSUPPORTED_FACT_KEYWORDS = [
    "경쟁률",
    "등록금",
    "평균 연봉",
    "연봉",
    "취업률",
    "논문 실적",
    "논문 순위",
    "실적 순위",
    "합격 가능성",
    "합격 확률",
    "가장 합격하기 쉬운",
    "장학금 지급 금액",
    "대기업 취업 가능성",
    "외부 대학 비교",
    "타 대학 비교",
]

EXTERNAL_INSTITUTION_KEYWORDS = [
    "서울대",
    "서울대학교",
    "연세대",
    "연세대학교",
    "고려대",
    "고려대학교",
    "포스텍",
    "POSTECH",
    "postech",
    "성균관대",
    "한양대",
    "UNIST",
    "unist",
    "DGIST",
    "dgist",
    "GIST",
    "gist",
    "외부 대학",
    "타 대학",
    "다른 대학",
]

KAIST_OFFICIAL_URL = "https://www.kaist.ac.kr/kr/"
KAIST_ADMISSION_URL = "https://admission.kaist.ac.kr/home"

UNSUPPORTED_KAIST_DEPARTMENT_KEYWORDS = [
    "전산학부",
    "전기및전자공학부",
    "전기 및 전자공학부",
    "기계공학과",
    "항공우주공학과",
    "건설및환경공학과",
    "건설 및 환경공학과",
    "바이오및뇌공학과",
    "바이오 및 뇌공학과",
    "생명화학공학과",
    "신소재공학과",
    "원자력및양자공학과",
    "원자력 및 양자공학과",
    "산업및시스템공학과",
    "산업 및 시스템공학과",
    "산업디자인학과",
    "수리과학과",
    "물리학과",
    "화학과",
    "생명과학과",
    "뇌인지과학과",
    "기술경영학부",
    "경영공학부",
    "디지털인문사회과학부",
    "문화기술대학원",
    "과학기술정책대학원",
    "의과학대학원",
    "문술미래전략대학원",
    "녹색성장지속가능대학원",
]


INTENT_EXAMPLES = [
    IntentExample("AI컴퓨팅학과 석사 지원 자격 알려줘", "admission_info"),
    IntentExample("AX학과 입학 요건 알려줘", "admission_info"),
    # 특정 학과를 지정하지 않아도 수집된 학과사무실 목록 조회는 가능하게 처리
    IntentExample("KAIST 학과 사무실 전화번호 알려줘", "office_contact_info"),
    IntentExample("카이스트 학과사무실 연락처 알려줘", "office_contact_info"),
    IntentExample("학과사무실 전화번호 목록 보여줘", "office_contact_info"),
    IntentExample("학과 행정실 연락처 알려줘", "office_contact_info"),
    IntentExample("AI시스템학과 대학원 모집 일정 알려줘", "admission_info"),
    IntentExample("AI미래학과 제출 서류 알려줘", "admission_info"),
    IntentExample("입학 조건 알려줘", "admission_info", "missing_department"),
    IntentExample("모든 학과 입학 요건 알려줘", "admission_info", "missing_department"),
    IntentExample("AI컴퓨팅학과 교과목 목록 보여줘", "course_info"),
    IntentExample("AI시스템학과 커리큘럼 알려줘", "course_info"),
    IntentExample("AX학과 수업 과목 설명해줘", "course_info"),
    IntentExample("교과목 알려줘", "course_info", "missing_department"),
    IntentExample("AI컴퓨팅학과 교수진 알려줘", "person_info"),
    IntentExample("AX학과 교수 이메일 알려줘", "person_info"),
    IntentExample("AI미래학과 연구실 알려줘", "person_info"),
    IntentExample("지도교수 찾고 싶어", "person_info", "missing_department"),
    IntentExample("AI시스템학과 학과 사무실 전화번호", "office_contact_info"),
    IntentExample("AX학과 사무실 위치 알려줘", "office_contact_info"),
    IntentExample("AI컴퓨팅학과 설명회 일정 알려줘", "event_info"),
    IntentExample("AX학과 공지사항 알려줘", "event_info"),
    IntentExample("학과 입시설명회 정보 알려줘", "event_info", "missing_department"),
    IntentExample("AI시스템학과 자료 다운로드 링크", "asset_or_link_info"),
    IntentExample("AX학과 브로슈어 pdf", "asset_or_link_info"),
    IntentExample("AI미래학과 홈페이지 바로가기", "asset_or_link_info"),
    IntentExample("AI컴퓨팅학과 소개해줘", "department_overview"),
    IntentExample("AI시스템학과 특징 알려줘", "department_overview"),
    IntentExample("AX학과는 어떤 학과야", "department_overview"),
    IntentExample("KAIST에 AI 학과는 어떤 게 있어", "department_overview"),
    IntentExample("카이스트 AI학과 뭐 있어", "department_overview"),
    IntentExample("AI컴퓨팅학과는 어떤 분야를 다뤄", "department_overview"),
    IntentExample("AI시스템학과는 어떤 인재를 양성해", "department_overview"),
    IntentExample("AX학과 교육 목표 알려줘", "department_overview"),
    IntentExample("카이스트 학과 뭐 있어", "department_overview", "department_scope"),
    IntentExample("KAIST 전체 학과 소개해줘", "department_overview", "department_scope"),
    IntentExample("카이스트 AI 관련 학과 알려줘", "department_overview", "department_scope"),
    IntentExample("공과대학에는 어떤 학과가 있어", "department_overview"),
    IntentExample("KAIST 학과 목록 알려줘", "department_overview"),
    IntentExample("학과들 비교해줘", "general_info", "comparison_criterion"),
    IntentExample("학과 차이 알려줘", "general_info", "comparison_criterion"),
    IntentExample("다 알려줘", "general_info", "too_broad"),
    IntentExample("전체 정보 알려줘", "general_info", "too_broad"),
    IntentExample("나한테 어느 학과가 맞아", "general_info", "personal_recommendation"),
    IntentExample("어디 지원하는 게 좋아", "general_info", "personal_recommendation"),
    IntentExample("거기 교수진은", "general_info", "unclear_reference"),
    IntentExample("그 학과 입학 정보 알려줘", "general_info", "unclear_reference"),
    IntentExample("카이스트 주소 알려줘", "kaist_profile_info"),
    IntentExample("KAIST 대표 번호 알려줘", "kaist_profile_info"),
    IntentExample("카이스트 전화 알려줘", "kaist_profile_info"),
    IntentExample("카이스트 설립일 알려줘", "kaist_profile_info"),
    IntentExample("한국과학기술원 영문명 알려줘", "kaist_profile_info"),
    IntentExample("KAIST 기본 정보 알려줘", "kaist_profile_info"),
    IntentExample("카이스트 재학생 수 알려줘", "kaist_statistics_info"),
    IntentExample("KAIST 졸업생 몇 명이야", "kaist_statistics_info"),
    IntentExample("카이스트 교직원 수 알려줘", "kaist_statistics_info"),
    IntentExample("KAIST 통계 알려줘", "kaist_statistics_info"),
    IntentExample("카이스트 공식 홈페이지 링크", "kaist_link_info"),
    IntentExample("카이스트 홈페이지 알려줘", "kaist_link_info"),
    IntentExample("KAIST 입학처 링크 알려줘", "kaist_link_info"),
    IntentExample("카이스트 캠퍼스맵 보여줘", "kaist_link_info"),
    IntentExample("카이스트 도서관 링크 알려줘", "kaist_link_info"),
    IntentExample("카이스트 학사일정 어디서 봐", "kaist_link_info"),
    IntentExample("전산학부 교수진 알려줘", "general_info", "unsupported_kaist_department"),
    IntentExample("기계공학과 입학 정보 알려줘", "general_info", "unsupported_kaist_department"),
    IntentExample("산업디자인학과 소개해줘", "general_info", "unsupported_kaist_department"),
    IntentExample("수리과학과 교과목 알려줘", "general_info", "unsupported_kaist_department"),
    IntentExample("오늘 날씨 알려줘", "general_info", "off_topic"),
    IntentExample("파이썬 코드 짜줘", "general_info", "off_topic"),
    IntentExample("맛집 추천해줘", "general_info", "off_topic"),
    IntentExample("주식 가격 알려줘", "general_info", "off_topic"),
    IntentExample("영어 번역해줘", "general_info", "off_topic"),
    IntentExample("서울대 AI학과랑 비교해줘", "general_info", "unsupported_fact"),
    IntentExample("타 대학 AI학과와 비교해줘", "general_info", "unsupported_fact"),
]


INTENT_RULES = [
    IntentRule(
        intent="kaist_statistics_info",
        content_type="kaist_statistics",
        description="KAIST 통계 정보 질문",
        keywords=[
            "통계",
            "재학생",
            "졸업생",
            "교직원",
            "학생 수",
            "학생수",
            "인원",
            "몇 명",
            "몇명",
            "statistics",
        ],
        vector_search_terms="KAIST 통계 재학생 졸업생 교직원 학생 수 인원",
        sql_table_hint="kaist_statistics",
        sql_task_hint="kaist_statistics_lookup",
    ),
    IntentRule(
        intent="kaist_link_info",
        content_type="link",
        description="KAIST 공식 링크 질문",
        keywords=[
            "공식 홈페이지",
            "카이스트 홈페이지",
            "KAIST 홈페이지",
            "kaist homepage",
            "입학처",
            "캠퍼스맵",
            "셔틀버스",
            "도서관",
            "학사일정",
        ],
        vector_search_terms="KAIST 공식 홈페이지 입학처 캠퍼스맵 셔틀버스 도서관 학사일정 링크 URL",
        sql_table_hint="kaist_links",
        sql_task_hint="kaist_link_lookup",
    ),
    IntentRule(
        intent="kaist_profile_info",
        content_type="kaist_profile",
        description="KAIST 기본 정보 질문",
        keywords=[
            "카이스트 주소",
            "KAIST 주소",
            "카이스트 대표 번호",
            "KAIST 대표 번호",
            "카이스트 전화번호",
            "KAIST 전화번호",
            "대표 번호",
            "대표번호",
            "팩스",
            "약자",
            "영문약자",
            "설립일",
            "창립일",
            "영문명",
            "학교명",
            "설립이념",
            "색상",
            "카이스트 기본 정보",
            "KAIST 기본 정보",
        ],
        vector_search_terms="KAIST 기본정보 학교명 영문명 창립일 설립일 주소 대표 번호 팩스 설립이념 색상",
        sql_table_hint="kaist_profile",
        sql_task_hint="kaist_profile_lookup",
    ),
    IntentRule(
        intent="course_info",
        content_type="course",
        description="교과목/교육과정 질문",
        keywords=[
            "교과목",
            "과목",
            "강의",
            "수업",
            "커리큘럼",
            "교육과정",
            "전공필수",
            "전공선택",
            "course",
            "courses",
            "curriculum",
            "class",
        ],
        vector_search_terms="교과목 교육과정 커리큘럼 과목 코드 전공필수 전공선택",
        sql_table_hint="courses",
        sql_task_hint="course_lookup",
    ),
    IntentRule(
        intent="office_contact_info",
        content_type="office_contact",
        description="학과 사무실/전화번호/위치 질문",
        keywords=[
            "학과사무실",
            "학과 사무실",
            "사무실",
            "행정실",
            "전화번호",
            "전화",
            "연락처",
            "문의",
            "문의처",
            "행정",
            "위치",
            "건물",
            "office",
            "contact",
            "phone",
            "location",
        ],
        vector_search_terms="학과사무실 전화번호 위치 웹사이트 연락처 행정실",
        sql_table_hint="office_contacts",
        sql_task_hint="office_contact_lookup",
    ),
    IntentRule(
        intent="person_info",
        content_type="person",
        description="교수진/구성원/이메일 질문",
        keywords=[
            "교수",
            "교수진",
            "구성원",
            "연구실",
            "이메일",
            "메일",
            "홈페이지",
            "people",
            "faculty",
            "professor",
            "email",
        ],
        vector_search_terms="교수진 구성원 이름 역할 이메일 홈페이지 연구실",
        sql_table_hint="professors",
        sql_task_hint="person_lookup",
    ),
    IntentRule(
        intent="admission_info",
        content_type="admission",
        description="입학/지원자격/전형 질문",
        keywords=[
            "입학",
            "지원",
            "지원 자격",
            "지원자격",
            "전형",
            "모집",
            "석사",
            "박사",
            "석박사",
            "통합과정",
            "졸업예정자",
            "제출서류",
            "제출 서류",
            "서류",
            "접수방법",
            "접수 방법",
            "원서접수",
            "면접",
            "합격자 발표",
            "admission",
            "apply",
            "eligibility",
        ],
        vector_search_terms="대학원 입학 지원 자격 모집 전형 석사 박사 석박사 통합과정",
        sql_table_hint="admissions",
        sql_task_hint="admission_lookup",
    ),
    IntentRule(
        intent="event_info",
        content_type="event",
        description="공지/행사/설명회 질문",
        keywords=[
            "설명회",
            "학과설명회",
            "행사",
            "공지",
            "일정",
            "세미나",
            "안내",
            "event",
            "notice",
            "seminar",
        ],
        vector_search_terms="공지 행사 설명회 일정 장소 자료 세미나 안내",
        sql_table_hint="events",
        sql_task_hint="event_lookup",
    ),
    IntentRule(
        intent="asset_or_link_info",
        content_type="link",
        description="링크/자료/다운로드 질문",
        keywords=[
            "링크",
            "URL",
            "url",
            "사이트",
            "바로가기",
            "자료",
            "다운로드",
            "pdf",
            "PDF",
            "brochure",
            "download",
        ],
        vector_search_terms="홈페이지 링크 URL 자료 다운로드 PDF 브로슈어",
        sql_table_hint="assets",
        sql_task_hint="asset_lookup",
    ),
    IntentRule(
        intent="department_overview",
        content_type=None,
        description="학과 소개/개요 질문",
        keywords=[
            "학과 소개",
            "소개",
            "어떤 학과",
            "무슨 학과",
            "특징",
            "비전",
            "목표",
            "AI대학",
            "AI 대학",
            "KAIST AI대학",
            "카이스트 AI대학",
            "AI 관련 학과",
            "AI 학과",
            "AI학과",
            "인공지능 학과",
            "인공지능학과",
            "어떤 게 있어",
            "뭐 있어",
            "무엇이 있어",
            "학과별",
            "학과들",
            "학과들을",
            "전체 학과",
            "각 학과",
            "분야",
            "다뤄",
            "다루",
            "인재",
            "양성",
            "교육 목표",
            "교육목표",
            "인재상",
            "진출 분야",
            "무엇을 배우",
            "뭘 배우",
            "졸업",
            "이수",
            "수료",
            "논문",
            "요건",
            "overview",
            "about",
            "description",
        ],
        vector_search_terms="학과 소개 개요 특징 비전 목표 교육 연구",
        sql_table_hint="departments",
        sql_task_hint="department_overview",
    ),
]


# task_hint별 정보유형/테이블 매핑 — 다중 intent 질문에서 보조 task를 조회할 때
# 각 task에 맞는 content_type/table로 분석을 재구성하기 위해 사용한다.
TASK_HINT_TO_CONTENT_TYPE = {
    rule.sql_task_hint: rule.content_type
    for rule in INTENT_RULES
    if rule.sql_task_hint
}
TASK_HINT_TO_TABLE_HINT = {
    rule.sql_task_hint: rule.sql_table_hint
    for rule in INTENT_RULES
    if rule.sql_task_hint
}


SQL_STRONG_KEYWORDS = [
    "목록",
    "전체",
    "전부",
    "표로",
    "표 형식",
    "표 형태",
    "테이블",
    "리스트",
    "몇 개",
    "개수",
    "이메일",
    "전화번호",
    "연락처",
    "코드",
    "과목코드",
    "전공필수만",
    "전공선택만",
    "있는 사람",
    "없는 사람",
    "조회",
    "정렬",
]

VECTOR_STRONG_KEYWORDS = [
    "설명",
    "요약",
    "근거",
    "내용",
    "자세히",
    "무슨 뜻",
    "어떤",
    "왜",
    "차이",
    "주의사항",
    "조건",
    "자격",
    "안내",
]

HYBRID_STRONG_PATTERNS = [
    ["목록", "설명"],
    ["목록", "근거"],
    ["표", "설명"],
    ["표", "근거"],
    ["교과목", "설명"],
    ["과목", "설명"],
    ["교과목", "추천"],
    ["과목", "추천"],
    ["교수", "연구"],
    ["이메일", "연구"],
    ["입학", "표"],
    ["지원 자격", "근거"],
]

CSV_FIRST_INTENTS = {
    "admission_info",
    "course_info",
    "person_info",
    "office_contact_info",
    "event_info",
    "asset_or_link_info",
    "kaist_profile_info",
    "kaist_statistics_info",
    "kaist_link_info",
}

# 한 질문에 함께 요청될 수 있는 학과-범위 구조화 intent(다중 정보유형 후보).
# kaist_* 전역 intent와 overview/general_info는 제외해 보수적으로만 결합한다.
MULTI_INTENT_CANDIDATES = {
    "admission_info",
    "course_info",
    "person_info",
    "office_contact_info",
    "event_info",
    "asset_or_link_info",
}

CSV_FIRST_VECTOR_ASSIST_KEYWORDS = [
    "설명",
    "요약",
    "근거",
    "자세히",
    "차이",
    "비교",
    "정리",
    "같이",
    "함께",
]


class IntentExampleMatcher:
    def __init__(
        self,
        examples: list[IntentExample] | None = None,
        min_score: float = 0.34,
    ) -> None:
        self.examples = examples or INTENT_EXAMPLES
        self.min_score = min_score
        self._example_vectors = [
            (example, self._vectorize(example.text))
            for example in self.examples
        ]

    def match(self, question: str) -> IntentExampleMatch | None:
        question_vector = self._vectorize(question)

        if not question_vector:
            return None

        best_example = None
        best_score = 0.0

        for example, example_vector in self._example_vectors:
            score = self._cosine_similarity(
                question_vector=question_vector,
                example_vector=example_vector,
            )

            if score > best_score:
                best_score = score
                best_example = example

        if best_example is None or best_score < self.min_score:
            return None

        return IntentExampleMatch(
            example=best_example,
            score=round(best_score, 6),
        )

    def _vectorize(self, text: str) -> Counter[str]:
        normalized_text = re.sub(r"\s+", " ", text.lower()).strip()
        compact_text = re.sub(r"\s+", "", normalized_text)
        vector: Counter[str] = Counter()

        for token in re.findall(r"[가-힣a-zA-Z0-9_]+", normalized_text):
            if len(token) >= 2:
                vector[f"tok:{token}"] += 2.0

        for ngram_size in (2, 3):
            if len(compact_text) < ngram_size:
                continue

            for index in range(len(compact_text) - ngram_size + 1):
                ngram = compact_text[index : index + ngram_size]
                vector[f"char{ngram_size}:{ngram}"] += 1.0

        return vector

    def _cosine_similarity(
        self,
        question_vector: Counter[str],
        example_vector: Counter[str],
    ) -> float:
        shared_keys = set(question_vector).intersection(example_vector)
        numerator = sum(
            question_vector[key] * example_vector[key]
            for key in shared_keys
        )
        question_norm = sqrt(
            sum(value * value for value in question_vector.values())
        )
        example_norm = sqrt(
            sum(value * value for value in example_vector.values())
        )

        if question_norm == 0 or example_norm == 0:
            return 0.0

        return numerator / (question_norm * example_norm)


class QuestionAnalyzer:
    def __init__(
        self,
        departments: list[DepartmentInfo] | None = None,
        intent_rules: list[IntentRule] | None = None,
        example_matcher: IntentExampleMatcher | None = None,
    ) -> None:
        self.departments = departments or DEPARTMENTS
        self.intent_rules = intent_rules or INTENT_RULES
        self.example_matcher = example_matcher or IntentExampleMatcher()

    def analyze(
        self,
        question: str,
        previous_department_code: str | None = None,
    ) -> QueryAnalysis:
        original_question = question
        normalized_question = self._normalize_question(question)
        lowered_question = normalized_question.lower()

        matched_departments = self._find_all_departments(
            normalized_question=normalized_question
        )

        if len(matched_departments) == 1:
            department = matched_departments[0]
        elif len(matched_departments) >= 2:
            department = None
        else:
            department = self._find_department(
                normalized_question=normalized_question,
                previous_department_code=previous_department_code,
            )

        unsupported_department_name = self._find_unsupported_department_name(
            normalized_question=normalized_question,
            matched_department=department,
        )

        intent_rule, matched_keywords = self._find_intent_rule(
            normalized_question=normalized_question,
        )

        example_match = self._find_semantic_intent_match(
            normalized_question=normalized_question,
            intent_rule=intent_rule,
            department=department,
            unsupported_department_name=unsupported_department_name,
        )

        forced_ambiguity_type = None

        if example_match:
            example = example_match.example

            if (
                example.ambiguity_type == "unsupported_kaist_department"
                and not unsupported_department_name
            ):
                example_match = None
            else:
                forced_ambiguity_type = example.ambiguity_type

                if example.intent != "general_info":
                    matched_intent_rule = self._get_intent_rule_by_intent(
                        example.intent,
                    )

                    if matched_intent_rule:
                        intent_rule = matched_intent_rule

                matched_keywords = [
                    *matched_keywords,
                    f"semantic:{example.intent}:{example_match.score}",
                ]

        department_name = department.name if department else None
        department_code = department.code if department else None

        intent = intent_rule.intent if intent_rule else "general_info"
        intent_description = (
            intent_rule.description
            if intent_rule
            else "일반 정보 질문"
        )
        content_type = intent_rule.content_type if intent_rule else None

        # 다중 정보유형(예: "교수 이메일이랑 담당 과목")을 위해 주 intent 외에
        # 명확히 함께 요청된 보조 intent를 보수적으로 수집한다.
        additional_intent_rules = self._find_additional_intent_rules(
            normalized_question=normalized_question,
            primary_rule=intent_rule,
        )

        route, route_reason = self._decide_route(
            normalized_question=normalized_question,
            intent_rule=intent_rule,
        )

        metadata_filter = self._build_metadata_filter(
            department_code=department_code,
            content_type=content_type,
        )

        sql_conditions = self._build_sql_conditions(
            department_code=department_code,
            content_type=content_type,
        )

        missing_fields = self._find_missing_fields(
            normalized_question=normalized_question,
            department_code=department_code,
            content_type=content_type,
            intent=intent,
        )

        ambiguity_type = self._find_ambiguity_type(
            normalized_question=normalized_question,
            department_code=department_code,
            content_type=content_type,
            intent=intent,
            missing_fields=missing_fields,
            unsupported_department_name=unsupported_department_name,
            forced_ambiguity_type=forced_ambiguity_type,
        )

        missing_fields = self._enrich_missing_fields(
            missing_fields=missing_fields,
            ambiguity_type=ambiguity_type,
        )

        is_ambiguous = len(missing_fields) > 0
        clarifying_message = None

        if is_ambiguous:
            route = "clarify"
            route_reason = "질문 처리에 필요한 정보가 부족합니다."
            clarifying_message = self._build_clarifying_message(
                missing_fields=missing_fields,
                ambiguity_type=ambiguity_type,
                unsupported_department_name=unsupported_department_name,
            )

        rewritten_question = self._build_rewritten_question(
            normalized_question=normalized_question,
            department_name=department_name,
            intent_rule=intent_rule,
        )

        display_question = self._build_display_question(
            normalized_question=normalized_question,
            department_name=department_name,
            intent_description=intent_description,
            route=route,
        )

        primary_and_additional = (
            [intent_rule, *additional_intent_rules] if intent_rule else []
        )
        intents_list = self._dedup_preserve(
            [rule.intent for rule in primary_and_additional]
        )
        content_types_list = self._dedup_preserve(
            [rule.content_type for rule in primary_and_additional if rule.content_type]
        )
        sql_table_hints_list = self._dedup_preserve(
            [rule.sql_table_hint for rule in primary_and_additional if rule.sql_table_hint]
        )
        sql_task_hints_list = self._dedup_preserve(
            [rule.sql_task_hint for rule in primary_and_additional if rule.sql_task_hint]
        )

        return QueryAnalysis(
            original_question=original_question,
            normalized_question=normalized_question,
            route=route,
            route_reason=route_reason,
            display_question=display_question,
            rewritten_question=rewritten_question,
            department_name=department_name,
            department_code=department_code,
            unsupported_department_name=unsupported_department_name,
            intent=intent,
            intent_description=intent_description,
            content_type=content_type,
            metadata_filter=metadata_filter,
            sql_table_hint=(
                intent_rule.sql_table_hint
                if intent_rule
                else None
            ),
            sql_task_hint=(
                intent_rule.sql_task_hint
                if intent_rule
                else None
            ),
            sql_conditions=sql_conditions,
            intents=intents_list,
            content_types=content_types_list,
            sql_table_hints=sql_table_hints_list,
            sql_task_hints=sql_task_hints_list,
            suppress_sql_keyword_filter=len(sql_task_hints_list) > 1,
            needs_sql=route in {"sql", "hybrid"},
            needs_vector=route in {"vector", "hybrid"},
            is_ambiguous=is_ambiguous,
            ambiguity_type=ambiguity_type,
            missing_fields=missing_fields,
            clarifying_message=clarifying_message,
            matched_keywords=matched_keywords,
            semantic_match_intent=(
                example_match.example.intent
                if example_match
                else None
            ),
            semantic_match_ambiguity_type=(
                example_match.example.ambiguity_type
                if example_match
                else None
            ),
            semantic_match_score=(
                example_match.score
                if example_match
                else None
            ),
            semantic_match_example=(
                example_match.example.text
                if example_match
                else None
            ),
        )

    def _normalize_question(self, question: str) -> str:
        text = question.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def _find_department(
        self,
        normalized_question: str,
        previous_department_code: str | None,
    ) -> DepartmentInfo | None:
        lowered_question = normalized_question.lower()

        for department in self.departments:
            for keyword in department.keywords:
                if keyword.lower() in lowered_question:
                    return department

        if previous_department_code:
            return self._get_department_by_code(previous_department_code)

        return None

    def _find_unsupported_department_name(
        self,
        normalized_question: str,
        matched_department: DepartmentInfo | None = None,
    ) -> str | None:
        if matched_department:
            return None

        lowered_question = normalized_question.lower()

        for department_name in UNSUPPORTED_KAIST_DEPARTMENT_KEYWORDS:
            if department_name.lower() in lowered_question:
                return department_name

        generic_department_pattern = re.compile(
            r"([가-힣A-Za-z0-9&·\-\s]{2,30}(?:학과|학부|대학원|전공|프로그램))"
        )
        ignored_terms = {
            "어느 학과",
            "어떤 학과",
            "무슨 학과",
            "전체 학과",
            "모든 학과",
            "각 학과",
            "그 학과",
            "해당 학과",
            "학과",
        }

        for match in generic_department_pattern.finditer(normalized_question):
            candidate = re.sub(r"\s+", " ", match.group(1)).strip()

            if candidate in ignored_terms:
                continue

            if any(term in candidate for term in ignored_terms):
                continue

            return candidate

        return None

    def _get_department_by_code(
        self,
        department_code: str,
    ) -> DepartmentInfo | None:
        for department in self.departments:
            if department.code == department_code:
                return department

        return None

    def _get_intent_rule_by_intent(
        self,
        intent: IntentType,
    ) -> IntentRule | None:
        for rule in self.intent_rules:
            if rule.intent == intent:
                return rule

        return None

    def _find_additional_intent_rules(
        self,
        normalized_question: str,
        primary_rule: IntentRule | None,
    ) -> list[IntentRule]:
        """
        주 intent 외에 같은 질문에서 명확히 함께 요청된 보조 intent를 보수적으로 찾는다.
        - 주 intent가 학과-범위 구조화 intent일 때만 동작(overview/general/kaist_* 제외)
        - 보조 후보도 같은 후보군으로 제한
        - 해당 intent의 키워드가 실제 질문에 등장할 때만 채택
        예: "교수 이메일이랑 담당 과목" → 주=course, 보조=person
        """
        if primary_rule is None or primary_rule.intent not in MULTI_INTENT_CANDIDATES:
            return []

        lowered_question = normalized_question.lower()
        additional_rules: list[IntentRule] = []

        for rule in self.intent_rules:
            if rule.intent == primary_rule.intent:
                continue

            if rule.intent not in MULTI_INTENT_CANDIDATES:
                continue

            if any(keyword.lower() in lowered_question for keyword in rule.keywords):
                additional_rules.append(rule)

        return additional_rules

    def _dedup_preserve(self, values: list[Any]) -> list[Any]:
        seen = set()
        result = []

        for value in values:
            if value in seen:
                continue

            seen.add(value)
            result.append(value)

        return result

    def _find_intent_rule(
        self,
        normalized_question: str,
    ) -> tuple[IntentRule | None, list[str]]:
        lowered_question = normalized_question.lower()

        if "홈페이지" in lowered_question:
            if any(
                keyword in lowered_question
                for keyword in ["kaist", "카이스트", "한국과학기술원"]
            ):
                kaist_link_rule = self._get_intent_rule_by_intent(
                    "kaist_link_info"
                )

                if kaist_link_rule:
                    return kaist_link_rule, ["카이스트 홈페이지"]

            person_specific_keywords = [
                "교수",
                "교수진",
                "구성원",
                "연구실",
                "지도교수",
                "faculty",
                "professor",
            ]

            if not any(
                keyword in lowered_question
                for keyword in person_specific_keywords
            ):
                asset_rule = self._get_intent_rule_by_intent(
                    "asset_or_link_info"
                )

                if asset_rule:
                    return asset_rule, ["홈페이지"]

        for rule in self.intent_rules:
            matched_keywords = [
                keyword
                for keyword in rule.keywords
                if keyword.lower() in lowered_question
            ]

            if matched_keywords:
                return rule, matched_keywords

        if self._is_compare_question(lowered_question):
            overview_rule = self._get_intent_rule_by_intent(
                "department_overview"
            )

            if overview_rule:
                return overview_rule, ["comparison"]

        if self._is_interest_based_recommendation_question(lowered_question):
            overview_rule = self._get_intent_rule_by_intent(
                "department_overview"
            )

            if overview_rule:
                return overview_rule, ["recommendation"]

        return None, []

    def _find_semantic_intent_match(
        self,
        normalized_question: str,
        intent_rule: IntentRule | None,
        department: DepartmentInfo | None,
        unsupported_department_name: str | None,
    ) -> IntentExampleMatch | None:
        if not self._should_use_semantic_match(
            normalized_question=normalized_question,
            intent_rule=intent_rule,
            department=department,
            unsupported_department_name=unsupported_department_name,
        ):
            return None

        return self.example_matcher.match(normalized_question)

    def _should_use_semantic_match(
        self,
        normalized_question: str,
        intent_rule: IntentRule | None,
        department: DepartmentInfo | None,
        unsupported_department_name: str | None,
    ) -> bool:
        if unsupported_department_name:
            return True

        if intent_rule is None:
            return True

        if intent_rule.intent in {
            "kaist_profile_info",
            "kaist_statistics_info",
            "kaist_link_info",
        }:
            return False

        lowered_question = normalized_question.lower()

        if intent_rule.intent in {
            "kaist_profile_info",
            "kaist_statistics_info",
            "kaist_link_info",
        }:
            return False

        has_kaist_keyword = any(
            keyword in lowered_question
            for keyword in ["kaist", "카이스트", "한국과학기술원"]
        )

        if has_kaist_keyword and department is None:
            # 이미 명확한 KAIST 기본/통계/링크/학과사무실 질문으로 분류된 경우
            # semantic example matching이 department_scope로 덮어쓰지 않도록 막는다.
            if intent_rule and intent_rule.intent in {
                "kaist_profile_info",
                "kaist_statistics_info",
                "kaist_link_info",
                "office_contact_info",
            }:
                return False

            return True

        broad_words = [
            "정보",
            "알려줘",
            "소개",
            "홈페이지",
            "링크",
            "어디",
            "뭐",
            "다",
            "전체",
            "모든",
            "추천",
            "맞아",
            "거기",
            "그 학과",
        ]

        # 이미 명확한 intent가 잡힌 질문은 semantic example이
        # too_broad 등으로 덮어쓰지 않도록 제한한다.
        if intent_rule.intent in {
            "course_info",
            "person_info",
            "admission_info",
            "event_info",
            "office_contact_info",
        }:
            return False

        return (
            department is None
            and any(word in lowered_question for word in broad_words)
            and intent_rule.intent
            in {
                "department_overview",
                "asset_or_link_info",
                "general_info",
            }
        )

    def _decide_route(
        self,
        normalized_question: str,
        intent_rule: IntentRule | None,
    ) -> tuple[RouteType, str]:
        if intent_rule is None:
            return "clarify", "질문 의도를 분류하지 못했습니다."

        lowered_question = normalized_question.lower()

        if self._is_compare_question(lowered_question):
            if intent_rule.intent in {
                "course_info",
                "person_info",
                "office_contact_info",
                "admission_info",
                "event_info",
                "asset_or_link_info",
                "kaist_profile_info",
                "kaist_statistics_info",
                "kaist_link_info",
            }:
                return "hybrid", "비교 질문이므로 정형 데이터와 문서 근거를 함께 확인합니다."

            if intent_rule.intent == "department_overview":
                return "vector", "학과 소개/특징 비교는 문서 기반 설명이 적합합니다."

        if (
            intent_rule.intent == "department_overview"
            and self._is_all_ai_department_scope_question(lowered_question)
        ):
            return (
                "hybrid",
                "AI 관련 학과 목록은 정형 학과 마스터를 우선 확인하고 문서 근거를 함께 사용합니다.",
            )

        if (
            intent_rule.intent == "department_overview"
            and self._is_kaist_academic_org_question(lowered_question)
        ):
            return "sql", "KAIST 학과/프로그램 조직 목록은 정형 데이터 조회가 적합합니다."

        if self._has_hybrid_pattern(lowered_question):
            return "hybrid", "정형 데이터와 문서 설명이 함께 필요한 질문입니다."

        if intent_rule.intent in CSV_FIRST_INTENTS:
            if self._needs_vector_assist_for_csv_first(lowered_question):
                return (
                    "hybrid",
                    "CSV/MySQL 정형 데이터를 먼저 확인하고 문서 근거를 보조로 사용합니다.",
                )

            return "sql", "CSV/MySQL 정형 데이터에서 먼저 확인할 수 있는 질문입니다."

        has_sql_signal = self._contains_any(lowered_question, SQL_STRONG_KEYWORDS)
        has_vector_signal = self._contains_any(lowered_question, VECTOR_STRONG_KEYWORDS)

        if has_sql_signal and has_vector_signal:
            return "hybrid", "SQL 조회와 문서 기반 설명이 모두 필요한 질문입니다."

        if has_sql_signal:
            return "sql", "정확한 목록, 표, 연락처, 조건 조회가 필요한 질문입니다."

        if has_vector_signal:
            return "vector", "문서 기반 설명이나 근거가 필요한 질문입니다."

        if intent_rule.intent in CSV_FIRST_INTENTS:
            return "sql", "정확한 정형 데이터 조회가 적합한 질문입니다."

        if intent_rule.intent in {
            "event_info",
            "department_overview",
        }:
            return "vector", "문서 내용과 설명 근거가 중요한 질문입니다."

        return "vector", "일반 문서 검색이 적합한 질문입니다."

    def _has_hybrid_pattern(self, lowered_question: str) -> bool:
        return any(
            all(keyword.lower() in lowered_question for keyword in pattern)
            for pattern in HYBRID_STRONG_PATTERNS
        )

    def _needs_vector_assist_for_csv_first(self, lowered_question: str) -> bool:
        return any(
            keyword.lower() in lowered_question
            for keyword in CSV_FIRST_VECTOR_ASSIST_KEYWORDS
        )

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        return any(keyword.lower() in text for keyword in keywords)

    def _build_rewritten_question(
        self,
        normalized_question: str,
        department_name: str | None,
        intent_rule: IntentRule | None,
    ) -> str:
        parts = [normalized_question]
    
        lowered_question = normalized_question.lower()
        matched_departments = self._find_all_departments(normalized_question)
    
        if department_name and department_name not in normalized_question:
            parts.append(department_name)
    
        if len(matched_departments) >= 2:
            parts.extend(department.name for department in matched_departments)
    
        if not department_name and self._is_all_ai_department_scope_question(lowered_question):
            parts.extend(department.name for department in self.departments)
    
        if intent_rule:
            parts.append(intent_rule.vector_search_terms)
    
        return re.sub(r"\s+", " ", " ".join(parts)).strip()

    def _build_display_question(
        self,
        normalized_question: str,
        department_name: str | None,
        intent_description: str,
        route: RouteType,
    ) -> str:
        if department_name:
            return f"[{route.upper()}] {department_name}에 대한 {intent_description}: {normalized_question}"

        return f"[{route.upper()}] {intent_description}: {normalized_question}"

    def _build_metadata_filter(
        self,
        department_code: str | None,
        content_type: ContentType | None,
    ) -> dict[str, Any] | None:
        conditions = []

        if department_code:
            conditions.append({"dept": {"$eq": department_code}})

        if content_type:
            conditions.append({"content_type": {"$eq": content_type}})

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}

    def _build_sql_conditions(
        self,
        department_code: str | None,
        content_type: ContentType | None,
    ) -> dict[str, Any]:
        conditions = {}

        if department_code:
            conditions["dept"] = department_code

        if content_type:
            conditions["content_type"] = content_type

        return conditions

    def _find_missing_fields(
        self,
        normalized_question: str,
        department_code: str | None,
        content_type: ContentType | None,
        intent: IntentType,
    ) -> list[str]:
        missing_fields = []

        lowered_question = normalized_question.lower()

        scope_resolved = (
            self._is_all_ai_department_scope_question(lowered_question)
            or self._is_kaist_academic_org_question(lowered_question)
            or self._is_multi_department_question(normalized_question)
        )

        if intent == "general_info" and content_type is None:
            if not scope_resolved:
                missing_fields.append("intent_or_content_type")

        if content_type in {"course", "person", "admission", "event"}:
            if department_code is None and not scope_resolved:
                missing_fields.append("department")

        if intent == "department_overview" and department_code is None:
            if not scope_resolved:
                missing_fields.append("department")

        return missing_fields

    def _find_ambiguity_type(
        self,
        normalized_question: str,
        department_code: str | None,
        content_type: ContentType | None,
        intent: IntentType,
        missing_fields: list[str],
        unsupported_department_name: str | None = None,
        forced_ambiguity_type: AmbiguityType | None = None,
    ) -> AmbiguityType | None:
        lowered_question = normalized_question.lower()

        scope_resolved = (
            self._is_all_ai_department_scope_question(lowered_question)
            or self._is_kaist_academic_org_question(lowered_question)
            or self._is_multi_department_question(normalized_question)
        )

        # 문서에 없을 가능성이 높은 정량/외부 정보는 too_broad가 아니라 unsupported_fact로 처리
        if self._is_unsupported_fact_question(lowered_question):
            return "unsupported_fact"

        # semantic matcher가 too_broad로 잘못 강제하는 것을 방지
        if forced_ambiguity_type and not scope_resolved:
            return forced_ambiguity_type

        if unsupported_department_name:
            return "unsupported_kaist_department"

        if self._is_off_topic_question(
            lowered_question=lowered_question,
            intent=intent,
        ):
            return "off_topic"

        if self._is_unclear_reference_question(lowered_question, department_code):
            return "unclear_reference"

        # 비교 대상이 명확하거나 전체 학과 비교면 되묻지 않음
        if self._is_compare_question(lowered_question):
            if not scope_resolved and not self._has_comparison_criterion(lowered_question):
                return "comparison_criterion"

        if self._is_too_broad_question(lowered_question):
            if not scope_resolved:
                return "too_broad"

        if self._is_department_scope_question(lowered_question, department_code):
            if not scope_resolved:
                return "department_scope"

        if "department" in missing_fields:
            return "missing_department"

        if intent == "general_info" and content_type is None:
            if not scope_resolved:
                return "missing_intent"

        return None

    def _enrich_missing_fields(
        self,
        missing_fields: list[str],
        ambiguity_type: AmbiguityType | None,
    ) -> list[str]:
        enriched_fields = list(missing_fields)

        field_by_ambiguity_type = {
            "department_scope": "department",
            "missing_department": "department",
            "missing_intent": "intent_or_content_type",
            "too_broad": "scope",
            "comparison_criterion": "comparison_criterion",
            "personal_recommendation": "personal_goal_or_interest",
            "unclear_reference": "department",
            "unsupported_kaist_department": "supported_data_scope",
            "unsupported_fact": "unsupported_fact",
            "off_topic": "domain",
        }

        field = field_by_ambiguity_type.get(ambiguity_type)

        if field and field not in enriched_fields:
            enriched_fields.append(field)

        return enriched_fields

    def _find_all_departments(
        self,
        normalized_question: str,
    ) -> list[DepartmentInfo]:
        lowered_question = normalized_question.lower()
        matched_departments = []
    
        for department in self.departments:
            if any(keyword.lower() in lowered_question for keyword in department.keywords):
                matched_departments.append(department)
    
        return matched_departments
    
    
    def _is_all_ai_department_scope_question(
        self,
        lowered_question: str,
    ) -> bool:
        return any(keyword.lower() in lowered_question for keyword in AI_COLLEGE_SCOPE_KEYWORDS)

    def _is_kaist_academic_org_question(
        self,
        lowered_question: str,
    ) -> bool:
        if any(keyword.lower() in lowered_question for keyword in KAIST_ACADEMIC_ORG_KEYWORDS):
            return True

        has_kaist = any(keyword in lowered_question for keyword in ["kaist", "카이스트", "한국과학기술원"])
        has_department_word = any(keyword in lowered_question for keyword in ["학과", "학부", "대학원", "프로그램"])
        has_list_word = any(keyword in lowered_question for keyword in ["뭐 있어", "어떤", "목록", "종류", "정리", "알려줘"])

        return has_kaist and has_department_word and has_list_word
    
    
    def _is_multi_department_question(
        self,
        normalized_question: str,
    ) -> bool:
        return len(self._find_all_departments(normalized_question)) >= 2
    
    
    def _is_unsupported_fact_question(
        self,
        lowered_question: str,
    ) -> bool:
        if any(keyword in lowered_question for keyword in UNSUPPORTED_FACT_KEYWORDS):
            return True

        has_external_institution = any(
            keyword.lower() in lowered_question
            for keyword in EXTERNAL_INSTITUTION_KEYWORDS
        )

        return has_external_institution and self._is_compare_question(lowered_question)
    
    
    def _is_interest_based_recommendation_question(
        self,
        lowered_question: str,
    ) -> bool:
        recommendation_keywords = [
            "적합",
            "맞아",
            "맞을까",
            "추천",
            "관심",
            "되고 싶은",
            "목표",
            "진로",
        ]
    
        ai_college_keywords = [
            "AI대학",
            "AI 대학",
            "학과",
            "AI컴퓨팅",
            "AI시스템",
            "AX",
            "AI미래",
        ]
    
        return (
            any(keyword.lower() in lowered_question for keyword in recommendation_keywords)
            and any(keyword.lower() in lowered_question for keyword in ai_college_keywords)
        )

    def _is_department_scope_question(
        self,
        lowered_question: str,
        department_code: str | None,
    ) -> bool:
        if department_code:
            return False

        # 학과사무실/연락처 질문은 "카이스트 학과"라는 표현이 있어도
        # 학과 범위 질문이 아니라 office_contact_info로 처리해야 한다.
        office_contact_keywords = [
            "학과사무실",
            "학과 사무실",
            "행정실",
            "전화번호",
            "전화",
            "연락처",
            "위치",
            "건물",
            "office",
            "contact",
            "phone",
            "location",
        ]

        if any(keyword in lowered_question for keyword in office_contact_keywords):
            return False

        scope_keywords = [
            "학과 소개",
            "학과 알려",
            "학과들",
            "학과 목록",
            "어떤 학과",
            "무슨 학과",
            "ai 학과",
            "ai학과",
            "인공지능 학과",
            "인공지능학과",
            "카이스트 학과",
            "kaist 학과",
        ]

        return any(keyword in lowered_question for keyword in scope_keywords)

    def _is_too_broad_question(self, lowered_question: str) -> bool:
        broad_keywords = [
            "다 알려",
            "전부 알려",
            "전체 알려",
            "모두 알려",
            "모든 정보",
            "싹 알려",
            "전부 설명",
            "전체 설명",
        ]

        return any(keyword in lowered_question for keyword in broad_keywords)

    def _is_compare_question(self, lowered_question: str) -> bool:
        compare_keywords = [
            "비교",
            "차이",
            "공통점",
            "다른 점",
            "뭐가 달라",
            "무슨 차이",
            "어디가 달라",
        ]

        return any(keyword in lowered_question for keyword in compare_keywords)

    def _has_comparison_criterion(self, lowered_question: str) -> bool:
        criterion_keywords = [
            "입학",
            "지원",
            "교수",
            "교수진",
            "교과",
            "과목",
            "연구",
            "분야",
            "사무실",
            "전화",
            "위치",
            "설명회",
            "행사",
            "공지",
            "커리큘럼",
            "교육과정",
        ]

        return any(keyword in lowered_question for keyword in criterion_keywords)

    def _is_personal_recommendation_question(self, lowered_question: str) -> bool:
        personal_keywords = [
            "나한테",
            "내게",
            "저한테",
            "어디 지원",
            "어느 학과가 맞",
            "추천",
            "가야 할",
            "가면 좋",
            "맞을까",
        ]
        department_choice_keywords = [
            "학과",
            "지원",
            "진학",
            "입학",
            "연구실",
            "교수",
        ]

        return (
            any(keyword in lowered_question for keyword in personal_keywords)
            and any(keyword in lowered_question for keyword in department_choice_keywords)
        )

    def _is_unclear_reference_question(
        self,
        lowered_question: str,
        department_code: str | None,
    ) -> bool:
        if department_code:
            return False

        reference_keywords = [
            "거기",
            "그 학과",
            "그쪽",
            "거긴",
            "해당 학과",
            "그럼 거기",
        ]

        return any(keyword in lowered_question for keyword in reference_keywords)

    def _is_off_topic_question(
        self,
        lowered_question: str,
        intent: IntentType,
    ) -> bool:
        if intent != "general_info":
            return False

        domain_keywords = [
            "kaist",
            "카이스트",
            "한국과학기술원",
            "학과",
            "대학원",
            "입학",
            "입시",
            "지원",
            "전형",
            "교수",
            "교수진",
            "연구",
            "교과",
            "과목",
            "커리큘럼",
            "학사일정",
            "캠퍼스",
            "셔틀",
            "도서관",
            "재학생",
            "졸업생",
            "교직원",
        ]

        return not any(keyword in lowered_question for keyword in domain_keywords)

    def _build_clarifying_message(
        self,
        missing_fields: list[str],
        ambiguity_type: AmbiguityType | None = None,
        unsupported_department_name: str | None = None,
    ) -> str:
        if ambiguity_type == "unsupported_kaist_department":
            department_text = (
                f"'{unsupported_department_name}'"
                if unsupported_department_name
                else "해당 학과"
            )
            return (
                f"현재 수집된 자료에는 {department_text}에 대해 답변할 만큼 충분한 정보가 없습니다.\n\n"
                "이 챗봇은 수집된 KAIST AI 관련 학과 자료를 중심으로 답변합니다. "
                "정확하고 최신 정보는 KAIST 공식 홈페이지나 입학처에서 확인하거나, 학과명을 포함해 직접 검색해 주세요.\n\n"
                f"- KAIST 공식 홈페이지: {KAIST_OFFICIAL_URL}\n"
                f"- KAIST 입학처: {KAIST_ADMISSION_URL}"
            )

        if ambiguity_type == "off_topic":
            return (
                "이 챗봇은 수집된 KAIST 및 KAIST AI 관련 학과 자료를 바탕으로 답변합니다.\n\n"
                "KAIST와 관련 없는 질문에는 답변할 수 없습니다. "
                "KAIST 학과, 입학, 교수진, 교과목, 연구 분야, 캠퍼스 기본 정보에 대해 질문해주세요."
            )

        if ambiguity_type == "department_scope":
            examples = ", ".join(department.name for department in self.departments)
            return (
                "현재 이 챗봇은 KAIST 전체 학과가 아니라, 수집된 KAIST AI 관련 학과 정보만 안내할 수 있습니다.\n\n"
                f"안내 가능한 학과: {examples}\n\n"
                "특정 학과 소개를 원하시나요, 아니면 수집된 AI 관련 학과 전체를 간단히 비교해드릴까요?"
            )

        if ambiguity_type == "too_broad":
            return (
                "질문 범위가 넓어서 한 번에 모두 답하면 부정확할 수 있습니다.\n\n"
                "원하는 범위를 골라 질문해주세요. 예: 전체 학과 간단 비교, 입학 정보, 교수진, 교과목, 연구 분야"
            )

        if ambiguity_type == "comparison_criterion":
            return (
                "어떤 기준으로 비교할까요?\n\n"
                "예: 입학 정보, 연구 분야, 교과목, 교수진, 학과 소개/특징"
            )

        if ambiguity_type == "personal_recommendation":
            return (
                "개인에게 특정 학과를 단정적으로 추천하거나 합격 가능성을 판단할 수는 없습니다.\n\n"
                "다만 관심 분야나 목표를 알려주시면, 수집된 학과 자료를 기준으로 관련 학과의 연구 분야, 교과목, 입학 정보를 비교해드릴 수 있습니다."
            )

        if ambiguity_type == "unclear_reference":
            return (
                "이전 대화에서 어떤 학과를 말하는지 확인하기 어렵습니다. 학과명을 다시 알려주세요.\n\n"
                "예: AI컴퓨팅학과 교수진, AX학과 입학 정보"
            )
        
        if ambiguity_type == "unsupported_fact":
            return (
                "제공된 문서에서 해당 정보는 확인되지 않습니다.\n\n"
                "이 챗봇은 수집된 KAIST AI 관련 학과 자료를 바탕으로 답변합니다. "
                "경쟁률, 등록금, 취업률, 평균 연봉, 합격 가능성, 외부 대학 비교처럼 "
                "문서에 근거가 없는 정보는 추측해서 답변하지 않습니다."
            )

        if "department" in missing_fields:
            examples = ", ".join(department.name for department in self.departments)
            return (
                f"어느 학과에 대한 질문인지 알려주세요. 예: {examples}\n\n"
                "또는 '전체 학과'라고 입력하면 수집된 AI 관련 학과 기준으로 정리해드릴 수 있습니다."
            )

        if "intent_or_content_type" in missing_fields:
            return (
                "어떤 정보를 알고 싶은지 조금 더 구체적으로 질문해주세요. "
                "예: 입학 정보, 교과목, 교수진, 학과 사무실, 설명회 정보"
            )

        return "질문을 조금 더 구체적으로 입력해주세요."


def run_examples() -> None:
    analyzer = QuestionAnalyzer()

    questions = [
        "AI컴퓨팅학과 석사 지원 자격은?",
        "AI시스템학과 교과목 알려줘",
        "AI시스템학과 교과목 목록과 각 과목 설명도 알려줘",
        "AX학과 교수진 이메일 목록 보여줘",
        "AX학과 교수 연구분야도 설명해줘",

        # office_contact_info 테스트
        "KAIST 학과 사무실 전화번호 알려줘",
        "학과사무실 전화번호 목록 보여줘",
        "카이스트 학과 행정실 연락처 알려줘",
        "AI시스템학과 학과 사무실 전화번호 알려줘",

        "AI컴퓨팅학과 학과설명회 정보 알려줘",
        "교수진도 알려줘",
        "자료 다운로드 링크 알려줘",
    ]

    for question in questions:
        analysis = analyzer.analyze(question)
        print("=" * 100)
        print(f"질문: {question}")
        print(analysis.to_dict())


if __name__ == "__main__":
    run_examples()
