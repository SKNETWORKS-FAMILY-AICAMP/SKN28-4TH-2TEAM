from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed" / "csv"
OUT_DIR = CURRENT_FILE.parent / "generated"
OUT_CSV = OUT_DIR / "question_bank.csv"
OUT_SUMMARY = OUT_DIR / "question_bank_summary.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class QuestionItem:
    id: int
    category: str
    question: str
    expected_route: str
    expected_intent: str
    expected_department_code: str
    expected_content_type: str
    source_table: str
    source_id: str
    source_label: str
    notes: str = ""


def read_csv(name: str) -> list[dict[str, str]]:
    path = DATA_DIR / name
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def clean(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value.strip(" -_/|")


def normalized_question(question: str) -> str:
    return re.sub(r"\s+", " ", question).strip().lower()


def source_id(row: dict[str, str], fallback_fields: Iterable[str]) -> str:
    for field in [
        "record_id",
        "admission_id",
        "course_id",
        "course_track_id",
        "person_id",
        "event_id",
        "office_id",
    ]:
        value = clean(row.get(field))
        if value:
            return value

    values = [
        clean(row.get(field))
        for field in fallback_fields
        if clean(row.get(field))
    ]
    return " | ".join(values)


class QuestionBank:
    def __init__(self) -> None:
        self._seen: set[str] = set()
        self.items: list[QuestionItem] = []

    def add(
        self,
        category: str,
        question: str,
        expected_route: str,
        expected_intent: str,
        expected_department_code: str = "",
        expected_content_type: str = "",
        source_table: str = "",
        source_id_value: str = "",
        source_label: str = "",
        notes: str = "",
    ) -> None:
        question = clean(question)
        if not question:
            return

        key = normalized_question(question)
        if key in self._seen:
            return

        self._seen.add(key)
        self.items.append(
            QuestionItem(
                id=len(self.items) + 1,
                category=category,
                question=question,
                expected_route=expected_route,
                expected_intent=expected_intent,
                expected_department_code=expected_department_code,
                expected_content_type=expected_content_type,
                source_table=source_table,
                source_id=source_id_value,
                source_label=source_label,
                notes=notes,
            )
        )


def collect_departments(*tables: list[dict[str, str]]) -> list[tuple[str, str]]:
    departments: dict[str, str] = {}

    for rows in tables:
        for row in rows:
            dept = clean(row.get("dept"))
            dept_name = clean(row.get("dept_name"))
            if dept and dept_name:
                departments[dept] = dept_name

    preferred_order = ["aic", "ai_systems", "ax", "fx"]
    return [
        (dept, departments[dept])
        for dept in preferred_order
        if dept in departments
    ]


def add_department_overview_questions(
    bank: QuestionBank,
    departments: list[tuple[str, str]],
) -> None:
    all_names = ", ".join(name for _, name in departments)
    source_label = f"수집 학과: {all_names}"

    for question in [
        "KAIST에 AI 학과는 어떤 게 있어?",
        "AI 관련 학과 뭐가 있는지 알려줘",
        "KAIST AI대학에 속한 학과들을 정리해줘",
        "수집된 AI 관련 학과 전체를 간단히 비교해줘",
        "KAIST에서 AI 관련 전공이나 학과 종류 알려줘",
        "KAIST AI 관련 학과 목록을 보여줘",
        "AI컴퓨팅학과, AI시스템학과, AX학과, AI미래학과를 한눈에 비교해줘",
        "KAIST AI 관련 학과별 핵심 키워드를 정리해줘",
        "AI 관련 학과 중 어떤 선택지가 있는지 먼저 알려줘",
        "수집된 KAIST AI 학과 정보를 요약해줘",
    ]:
        bank.add(
            category="AI학과 기본",
            question=question,
            expected_route="vector",
            expected_intent="department_overview",
            source_table="derived_departments",
            source_id_value=";".join(dept for dept, _ in departments),
            source_label=source_label,
        )

    for dept, dept_name in departments:
        for question in [
            f"{dept_name}는 어떤 학과야?",
            f"{dept_name} 주요 특징 알려줘",
            f"{dept_name} 소개를 출처 기반으로 정리해줘",
            f"{dept_name}에서 다루는 분야는?",
            f"{dept_name} 교육 방향을 설명해줘",
            f"{dept_name} 관련 입학, 교과목, 교수진 데이터를 한눈에 정리해줘",
        ]:
            bank.add(
                category="학과 소개",
                question=question,
                expected_route="vector",
                expected_intent="department_overview",
                expected_department_code=dept,
                source_table="derived_departments",
                source_id_value=dept,
                source_label=dept_name,
            )


def add_admission_questions(bank: QuestionBank, rows: list[dict[str, str]]) -> None:
    seen_dept_type: set[tuple[str, str, str]] = set()

    for row in rows:
        dept = clean(row.get("dept"))
        dept_name = clean(row.get("dept_name"))
        title = clean(row.get("title"))
        section = clean(row.get("section_title"))
        admission_type = clean(row.get("admission_type"))
        page_title = clean(row.get("page_title"))
        row_id = source_id(row, ["dept", "section_title", "title"])
        label = " / ".join(part for part in [dept_name, section, title] if part)

        if not dept_name:
            continue

        if title:
            bank.add(
                "입학 정보",
                f"{dept_name} {title} 입학 정보 알려줘",
                "vector",
                "admission_info",
                dept,
                "admission",
                "admissions.csv",
                row_id,
                label,
            )

        if section and title and section != title:
            bank.add(
                "입학 정보",
                f"{dept_name} {section}에서 {title} 내용 알려줘",
                "vector",
                "admission_info",
                dept,
                "admission",
                "admissions.csv",
                row_id,
                label,
            )

        lowered = f"{admission_type} {section} {title} {page_title}".lower()

        if "eligibility" in lowered or "지원 자격" in lowered:
            bank.add(
                "입학 지원자격",
                f"{dept_name} {title or section} 지원 자격은?",
                "vector",
                "admission_info",
                dept,
                "admission",
                "admissions.csv",
                row_id,
                label,
            )

        if "schedule" in lowered or "일정" in lowered:
            bank.add(
                "입학 일정",
                f"{dept_name} {title or section} 일정 알려줘",
                "vector",
                "admission_info",
                dept,
                "admission",
                "admissions.csv",
                row_id,
                label,
            )

        if "scholarship" in lowered or "장학생" in lowered:
            bank.add(
                "입학 장학",
                f"{dept_name} {title or section} 장학생 정보 알려줘",
                "vector",
                "admission_info",
                dept,
                "admission",
                "admissions.csv",
                row_id,
                label,
            )

        if "advisor" in lowered or "지도교수" in lowered:
            bank.add(
                "지도교수",
                f"{dept_name} 지도교수 신청 관련 사항 알려줘",
                "vector",
                "admission_info",
                dept,
                "admission",
                "admissions.csv",
                row_id,
                label,
            )

        key = (dept, admission_type, page_title)
        if admission_type and key not in seen_dept_type:
            seen_dept_type.add(key)
            bank.add(
                "입학 정보",
                f"{dept_name} {admission_type} 유형의 입학 항목을 정리해줘",
                "vector",
                "admission_info",
                dept,
                "admission",
                "admissions.csv",
                row_id,
                label,
            )


def add_course_questions(bank: QuestionBank, rows: list[dict[str, str]]) -> None:
    for row in rows:
        dept = clean(row.get("dept"))
        dept_name = clean(row.get("dept_name"))
        course_code = clean(row.get("course_code"))
        course_name = clean(row.get("course_name"))
        course_type = clean(row.get("course_type"))
        course_level = clean(row.get("course_level"))
        row_id = source_id(row, ["dept", "course_code", "course_name"])
        label = " / ".join(part for part in [dept_name, course_code, course_name] if part)

        if not dept_name or not course_name:
            continue

        bank.add(
            "교과목",
            f"{dept_name} {course_name} 과목 정보 알려줘",
            "sql",
            "course_info",
            dept,
            "course",
            "courses.csv",
            row_id,
            label,
        )

        if course_code:
            bank.add(
                "교과목",
                f"{dept_name} {course_code} 과목명과 이수구분 알려줘",
                "sql",
                "course_info",
                dept,
                "course",
                "courses.csv",
                row_id,
                label,
            )

        if course_type:
            bank.add(
                "교과목 이수구분",
                f"{dept_name} {course_name}은 필수야 선택이야?",
                "sql",
                "course_info",
                dept,
                "course",
                "courses.csv",
                row_id,
                label,
            )

        if course_level:
            bank.add(
                "교과목 수준",
                f"{dept_name} {course_level} 과목 중 {course_name} 정보 알려줘",
                "sql",
                "course_info",
                dept,
                "course",
                "courses.csv",
                row_id,
                label,
            )


def add_track_questions(bank: QuestionBank, rows: list[dict[str, str]]) -> None:
    seen_tracks: set[tuple[str, str]] = set()

    for row in rows:
        dept = clean(row.get("dept"))
        dept_name = clean(row.get("dept_name"))
        track_name = clean(row.get("track_name"))
        course_name = clean(row.get("course_name"))
        course_code = clean(row.get("course_code"))
        course_type = clean(row.get("course_type"))
        row_id = source_id(row, ["dept", "track_name", "course_code", "course_name"])
        label = " / ".join(part for part in [dept_name, track_name, course_code, course_name] if part)

        if not dept_name or not track_name:
            continue

        track_key = (dept, track_name)
        if track_key not in seen_tracks:
            seen_tracks.add(track_key)
            bank.add(
                "트랙/교육과정",
                f"{dept_name} {track_name} 트랙 교과목 알려줘",
                "sql",
                "course_info",
                dept,
                "course",
                "course_track_map.csv",
                row_id,
                label,
            )
            bank.add(
                "트랙/교육과정",
                f"{dept_name} {track_name} 교육과정에서 어떤 과목을 보면 돼?",
                "sql",
                "course_info",
                dept,
                "course",
                "course_track_map.csv",
                row_id,
                label,
            )

        if course_name:
            bank.add(
                "트랙별 교과목",
                f"{dept_name} {track_name}에서 {course_name}은 어떤 과목이야?",
                "sql",
                "course_info",
                dept,
                "course",
                "course_track_map.csv",
                row_id,
                label,
            )

        if course_code and course_type:
            bank.add(
                "트랙별 교과목",
                f"{dept_name} {track_name}의 {course_code} 이수구분 알려줘",
                "sql",
                "course_info",
                dept,
                "course",
                "course_track_map.csv",
                row_id,
                label,
            )


def add_people_questions(bank: QuestionBank, rows: list[dict[str, str]]) -> None:
    seen_dept_role: set[tuple[str, str]] = set()

    for row in rows:
        dept = clean(row.get("dept"))
        dept_name = clean(row.get("dept_name"))
        name = clean(row.get("name"))
        role = clean(row.get("role_normalized") or row.get("role"))
        email = clean(row.get("email"))
        homepage = clean(row.get("homepage"))
        office = clean(row.get("office"))
        research_area = clean(row.get("research_area"))
        row_id = source_id(row, ["dept", "name", "email"])
        label = " / ".join(part for part in [dept_name, name, role] if part)

        if not dept_name or not name:
            continue

        bank.add(
            "교수진/구성원",
            f"{dept_name} {name} 교수 정보 알려줘",
            "sql",
            "person_info",
            dept,
            "person",
            "people.csv",
            row_id,
            label,
        )

        if email:
            bank.add(
                "교수진 이메일",
                f"{dept_name} {name} 이메일 알려줘",
                "sql",
                "person_info",
                dept,
                "person",
                "people.csv",
                row_id,
                label,
            )

        if homepage:
            bank.add(
                "교수진 홈페이지",
                f"{dept_name} {name} 홈페이지 알려줘",
                "sql",
                "person_info",
                dept,
                "person",
                "people.csv",
                row_id,
                label,
            )

        if office:
            bank.add(
                "교수진 연구실",
                f"{dept_name} {name} 연구실 위치 알려줘",
                "sql",
                "person_info",
                dept,
                "person",
                "people.csv",
                row_id,
                label,
            )

        if research_area:
            bank.add(
                "교수진 연구",
                f"{dept_name} {name} 연구분야 알려줘",
                "hybrid",
                "person_info",
                dept,
                "person",
                "people.csv",
                row_id,
                label,
            )

        role_key = (dept, role)
        if role and role_key not in seen_dept_role:
            seen_dept_role.add(role_key)
            bank.add(
                "교수진/구성원",
                f"{dept_name} {role} 명단 알려줘",
                "sql",
                "person_info",
                dept,
                "person",
                "people.csv",
                row_id,
                label,
            )


def add_asset_questions(bank: QuestionBank, rows: list[dict[str, str]]) -> None:
    useful_content_types = {
        "link",
        "attachment",
        "contact_info",
        "text",
        "table",
        "card",
        "mixed_media",
    }
    seen_topic: set[tuple[str, str, str]] = set()

    for row in rows:
        dept = clean(row.get("dept"))
        dept_name = clean(row.get("dept_name"))
        topic = clean(row.get("topic"))
        content_type = clean(row.get("content_type"))
        asset_type = clean(row.get("asset_type"))
        url = clean(row.get("url") or row.get("source_url"))
        filename = clean(row.get("filename"))
        text = clean(row.get("text"))
        row_id = source_id(row, ["dept", "topic", "url", "filename"])
        label = " / ".join(part for part in [dept_name, topic, asset_type or content_type] if part)

        if not dept_name or not topic:
            continue
        if content_type not in useful_content_types and not url and not filename:
            continue

        topic_key = (dept, topic, content_type)
        if topic_key not in seen_topic:
            seen_topic.add(topic_key)
            bank.add(
                "자료/링크",
                f"{dept_name} {topic} 관련 자료 알려줘",
                "sql",
                "asset_or_link_info",
                dept,
                "link",
                "assets.csv",
                row_id,
                label,
            )

        if url:
            bank.add(
                "자료/링크",
                f"{dept_name} {topic} 링크 알려줘",
                "sql",
                "asset_or_link_info",
                dept,
                "link",
                "assets.csv",
                row_id,
                label,
            )

        if filename:
            bank.add(
                "첨부자료",
                f"{dept_name} {filename} 자료가 어떤 내용인지 알려줘",
                "vector",
                "asset_or_link_info",
                dept,
                "link",
                "assets.csv",
                row_id,
                label,
            )

        if content_type == "contact_info" or asset_type in {"phone", "email"}:
            bank.add(
                "행정/연락처",
                f"{dept_name} {topic} 연락처 알려줘",
                "sql",
                "office_contact_info",
                dept,
                "office_contact",
                "assets.csv",
                row_id,
                label,
            )

        if text and content_type in {"text", "card", "table"}:
            bank.add(
                "학과 소개/자료",
                f"{dept_name} {topic} 내용을 요약해줘",
                "vector",
                "department_overview",
                dept,
                "",
                "assets.csv",
                row_id,
                label,
            )


def add_event_questions(bank: QuestionBank, rows: list[dict[str, str]]) -> None:
    for row in rows:
        dept = clean(row.get("dept"))
        dept_name = clean(row.get("dept_name"))
        title = clean(row.get("title"))
        event_date = clean(row.get("event_date"))
        row_id = source_id(row, ["dept", "title", "event_date"])
        label = " / ".join(part for part in [dept_name, title, event_date] if part)

        if not dept_name or not title:
            continue

        for question in [
            f"{dept_name} {title} 행사 정보 알려줘",
            f"{dept_name} {title} 일정과 장소 알려줘",
            f"{dept_name} 학과설명회 정보 알려줘",
        ]:
            bank.add(
                "행사/공지",
                question,
                "vector",
                "event_info",
                dept,
                "event",
                "events.csv",
                row_id,
                label,
            )


def add_attachment_questions(bank: QuestionBank, rows: list[dict[str, str]]) -> None:
    for row in rows:
        dept = clean(row.get("dept"))
        filename = clean(row.get("filename"))
        board = clean(row.get("board"))
        row_id = source_id(row, ["dept", "filename"])
        label = " / ".join(part for part in [dept, board, filename] if part)

        if not filename:
            continue

        for question in [
            f"{filename} 자료 요약해줘",
            f"{filename} 파일에서 확인할 수 있는 입학 정보를 알려줘",
        ]:
            bank.add(
                "첨부자료",
                question,
                "vector",
                "asset_or_link_info",
                dept,
                "link",
                "attachments.csv",
                row_id,
                label,
            )


def add_kaist_questions(
    bank: QuestionBank,
    profile_rows: list[dict[str, str]],
    stats_rows: list[dict[str, str]],
    link_rows: list[dict[str, str]],
) -> None:
    for row in profile_rows:
        item = clean(row.get("item"))
        row_id = source_id(row, ["item"])
        if not item:
            continue
        bank.add(
            "KAIST 기본",
            f"KAIST {item} 알려줘",
            "sql",
            "kaist_profile_info",
            "",
            "kaist_profile",
            "kaist_profile.csv",
            row_id,
            item,
        )

    for row in stats_rows:
        stat_group = clean(row.get("stat_group"))
        level = clean(row.get("level"))
        row_id = source_id(row, ["stat_group", "level"])
        label = " / ".join(part for part in [stat_group, level] if part)
        if not label:
            continue
        bank.add(
            "KAIST 통계",
            f"KAIST {label} 통계 알려줘",
            "sql",
            "kaist_statistics_info",
            "",
            "kaist_statistics",
            "kaist_statistics.csv",
            row_id,
            label,
        )

    for row in link_rows:
        link_name = clean(row.get("link_name"))
        row_id = source_id(row, ["link_name", "url"])
        if not link_name:
            continue
        bank.add(
            "KAIST 링크",
            f"KAIST {link_name} 링크 알려줘",
            "sql",
            "kaist_link_info",
            "",
            "link",
            "kaist_links.csv",
            row_id,
            link_name,
        )


def add_office_questions(bank: QuestionBank, rows: list[dict[str, str]]) -> None:
    for row in rows:
        program_name = clean(row.get("program_name"))
        row_id = source_id(row, ["program_name", "phone"])
        if not program_name:
            continue
        for question in [
            f"KAIST {program_name} 사무실 전화번호 알려줘",
            f"KAIST {program_name} 홈페이지 알려줘",
            f"KAIST {program_name} 사무실 위치 알려줘",
        ]:
            bank.add(
                "KAIST 학과 사무실",
                question,
                "sql",
                "office_contact_info",
                "",
                "office_contact",
                "department_offices.csv",
                row_id,
                program_name,
            )


def write_outputs(bank: QuestionBank) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(asdict(bank.items[0]).keys()) if bank.items else [],
        )
        writer.writeheader()
        for item in bank.items:
            writer.writerow(asdict(item))

    category_counts = Counter(item.category for item in bank.items)
    source_counts = Counter(item.source_table for item in bank.items)
    route_counts = Counter(item.expected_route for item in bank.items)
    intent_counts = Counter(item.expected_intent for item in bank.items)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "question_count": len(bank.items),
        "category_counts": dict(category_counts.most_common()),
        "source_table_counts": dict(source_counts.most_common()),
        "route_counts": dict(route_counts.most_common()),
        "intent_counts": dict(intent_counts.most_common()),
        "output_csv": str(OUT_CSV),
    }

    with OUT_SUMMARY.open("w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> None:
    admissions = read_csv("admissions.csv")
    assets = read_csv("assets.csv")
    attachments = read_csv("attachments.csv")
    courses = read_csv("courses.csv")
    course_track_map = read_csv("course_track_map.csv")
    department_offices = read_csv("department_offices.csv")
    events = read_csv("events.csv")
    kaist_links = read_csv("kaist_links.csv")
    kaist_profile = read_csv("kaist_profile.csv")
    kaist_statistics = read_csv("kaist_statistics.csv")
    people = read_csv("people.csv")

    departments = collect_departments(
        admissions,
        assets,
        courses,
        course_track_map,
        events,
        people,
    )

    bank = QuestionBank()
    add_department_overview_questions(bank, departments)
    add_admission_questions(bank, admissions)
    add_course_questions(bank, courses)
    add_track_questions(bank, course_track_map)
    add_people_questions(bank, people)
    add_asset_questions(bank, assets)
    add_event_questions(bank, events)
    add_attachment_questions(bank, attachments)
    add_kaist_questions(bank, kaist_profile, kaist_statistics, kaist_links)
    add_office_questions(bank, department_offices)
    write_outputs(bank)


if __name__ == "__main__":
    main()
