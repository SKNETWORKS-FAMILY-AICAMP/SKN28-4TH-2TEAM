from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.query_analyzer import QueryAnalysis
from rag.context_builder import SqlQueryResult


SUPPORTED_AI_COLLEGE_DEPT_CODES = ("aic", "ai_systems", "ai_future", "ax", "fx")

DEPT_LABELS = {
    "aic": "AI컴퓨팅학과",
    "ai_systems": "AI시스템학과",
    "ai_future": "AI미래학과",
    "fx": "AI미래학과",
    "ax": "AX학과",
}

DEPARTMENT_DISPLAY_ORDER = {
    "ai_systems": 1,
    "fx": 2,
    "ai_future": 2,
    "ax": 3,
    "aic": 4,
}

# 교수 목록 표시 순서: 전임(학과장/전임교수/교수/중점교원)을 겸임(겸직/겸임교수)보다 먼저.
# 팀 결정(2026-06-23): 전체 인원을 다 보여주되 역할 라벨 노출 + 전임을 상위에.
PERSON_ROLE_DISPLAY_ORDER = {
    "학과장": 0,
    "전임교수": 1,
    "교수": 2,
    "중점교원": 3,
    "겸직교수": 4,
    "겸임교수": 5,
}

KAIST_ACADEMIC_GROUP_ALIASES = {
    "공과대학": "공과대학",
    "자연과학대학": "자연과학대학",
    "생명과학기술대학": "생명과학기술대학",
    "생명과학 기술대학": "생명과학기술대학",
    "인문사회융합과학대학": "인문사회융합과학대학",
    "인문사회 융합과학대학": "인문사회융합과학대학",
    "경영대학": "경영대학",
}

KAIST_ACADEMIC_GROUP_ORDER = {
    "자연과학대학": 1,
    "생명과학기술대학": 2,
    "공과대학": 3,
    "AI대학": 4,
    "인문사회융합과학대학": 5,
    "경영대학": 6,
    "기타/학제 프로그램": 99,
}

KAIST_ACADEMIC_UNIT_GROUPS = {
    "물리학과": "자연과학대학",
    "수리과학과": "자연과학대학",
    "화학과": "자연과학대학",
    "양자대학원": "자연과학대학",
    "생명과학과": "생명과학기술대학",
    "의과학대학원": "생명과학기술대학",
    "뇌인지과학과": "생명과학기술대학",
    "공학생물학대학원": "생명과학기술대학",
    "줄기세포및재생생물학대학원": "생명과학기술대학",
    "기계공학과": "공과대학",
    "해양시스템대학원": "공과대학",
    "항공우주공학과": "공과대학",
    "우주탐사공학학제전공": "공과대학",
    "전기및전자공학부": "공과대학",
    "로봇공학학제전공": "공과대학",
    "미래자동차학제전공": "공과대학",
    "반도체공학대학원": "공과대학",
    "인공지능반도체대학원": "공과대학",
    "전산학부": "공과대학",
    "정보보호대학원": "공과대학",
    "건설및환경공학과": "공과대학",
    "환경에너지공학학제전공": "공과대학",
    "바이오및뇌공학과": "공과대학",
    "뇌인지공학프로그램": "공과대학",
    "산업디자인학과": "공과대학",
    "산업및시스템공학과": "공과대학",
    "데이터사이언스대학원": "공과대학",
    "생명화학공학과": "공과대학",
    "신소재공학과": "공과대학",
    "원자력및양자공학과": "공과대학",
    "조천식모빌리티대학원": "공과대학",
    "김재철AI대학원": "AI대학",
    "KAIST-KIST-AI로봇대학원프로그램": "AI대학",
    "디지털인문사회과학부": "인문사회융합과학대학",
    "문화기술대학원": "인문사회융합과학대학",
    "과학기술정책대학원": "인문사회융합과학대학",
    "경영공학부": "경영대학",
    "기술경영학부": "경영대학",
}


@dataclass
class SQLToolConfig:
    """MySQL 우선, CSV fallback 선택 지원 설정."""

    host: str = "127.0.0.1"
    port: int = 3306
    user: str = ""
    password: str = ""
    database: str = "kaist_ai"
    connect_timeout: int = 5
    max_rows: int = 100
    csv_data_dir: str = str(PROJECT_ROOT / "data" / "processed" / "csv")
    fallback_to_csv: bool = True

    @classmethod
    def from_env(cls) -> "SQLToolConfig":
        load_dotenv()

        return cls(
            host=os.getenv("KAIST_MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("KAIST_MYSQL_PORT", "3306")),
            user=os.getenv("KAIST_MYSQL_USER", ""),
            password=os.getenv("KAIST_MYSQL_PASSWORD", ""),
            database=os.getenv("KAIST_MYSQL_DATABASE", "kaist_ai"),
            connect_timeout=int(os.getenv("KAIST_MYSQL_CONNECT_TIMEOUT", "5")),
            max_rows=int(os.getenv("KAIST_SQL_MAX_ROWS", "100")),
            csv_data_dir=os.getenv(
                "KAIST_CSV_DATA_DIR",
                str(PROJECT_ROOT / "data" / "processed" / "csv"),
            ),
            fallback_to_csv=os.getenv(
                "KAIST_SQL_FALLBACK_TO_CSV",
                "true",
            ).lower() not in {"0", "false", "no"},
        )

    def mysql_configured(self) -> bool:
        return bool(self.host and self.user and self.database)


class SQLTool:
    """
    KAIST AI College RAG Agent용 정형 데이터 조회 도구.

    기본 동작은 MySQL 조회입니다. 로컬 개발 환경에서 MySQL 접속 정보가 없거나
    연결에 실패하면 CSV fallback으로 같은 형태의 SqlQueryResult를 반환합니다.
    """

    FILE_MAP = {
        "admission": ("admissions.csv", "admissions_clean.csv"),
        "asset": ("assets.csv", "assets_clean.csv"),
        "attachment": ("attachments.csv", "attachments_clean.csv"),
        "course": ("course_track_map.csv", "courses.csv", "courses_clean.csv"),
        "course_track": ("course_track_map.csv",),
        "department": ("people.csv", "admissions.csv", "courses.csv", "assets.csv", "course_track_map.csv", "rag_documents.csv"),
        "department_office": ("department_offices.csv",),
        "event": ("events.csv", "events_clean.csv"),
        "kaist_links": ("kaist_links.csv",),
        "kaist_link": ("kaist_links.csv",),
        "kaist_profile": ("kaist_profile.csv",),
        "kaist_statistics": ("kaist_statistics.csv",),
        "office_contacts": ("department_offices.csv",),
        "person": ("people.csv", "people_clean.csv"),
        "quality_report": ("quality_report.csv",),
    }

    TABLE_HINT_MAP = {
        "courses": "course",
        "professors": "person",
        "people": "person",
        "office_contacts": "office_contacts",
        "admissions": "admission",
        "events": "event",
        "assets": "asset",
        "departments": "department",
        "kaist_profile": "kaist_profile",
        "kaist_statistics": "kaist_statistics",
        "kaist_links": "kaist_links",
    }

    TASK_TABLE_MAP = {
        "course_lookup": "course",
        "person_lookup": "person",
        "office_contact_lookup": "office_contacts",
        "admission_lookup": "admission",
        "event_lookup": "event",
        "asset_lookup": "asset",
        "department_overview": "department",
        "kaist_profile_lookup": "kaist_profile",
        "kaist_statistics_lookup": "kaist_statistics",
        "kaist_link_lookup": "kaist_links",
    }

    MYSQL_TABLE_NAMES = {
        "admission": "admission",
        "asset": "asset",
        "course": "course",
        "department": "department",
        "department_office": "department_office",
        "event": "event",
        "kaist_links": "kaist_link",
        "kaist_link": "kaist_link",
        "kaist_profile": "kaist_profile",
        "kaist_statistics": "kaist_statistics",
        "office_contacts": "department_office",
        "person": "person",
    }

    # LIMIT 전 진짜 매칭 수를 SELECT에 심는 윈도우 컬럼 별칭.
    # `_`로 시작해 표시 컬럼과 충돌하지 않고, _split_total_count가 회수·제거한다.
    _TOTAL_COUNT_ALIAS = "_total_count"

    def __init__(self, config: SQLToolConfig | None = None) -> None:
        self.config = config or SQLToolConfig.from_env()
        self.csv_data_dir = Path(self.config.csv_data_dir)

    # ============================================================
    # RagPipeline 연결용 인터페이스
    # ============================================================

    def search(self, analysis: QueryAnalysis) -> SqlQueryResult:
        return self.query(analysis)

    def __call__(self, analysis: QueryAnalysis) -> SqlQueryResult:
        return self.query(analysis)

    # ============================================================
    # Query router
    # ============================================================

    def query(self, analysis: QueryAnalysis) -> SqlQueryResult:
        table_name = self._table_name_from_analysis(analysis)

        if not table_name:
            return self._unsupported_task_result(analysis)

        if self.config.mysql_configured():
            try:
                return self._query_mysql(table_name, analysis)
            except Exception as error:
                if not self.config.fallback_to_csv:
                    return SqlQueryResult(
                        table_name=table_name,
                        rows=[],
                        columns=[],
                        conditions=getattr(analysis, "sql_conditions", {}),
                        message="MySQL 조회 중 오류가 발생했습니다.",
                        warnings=[f"{type(error).__name__}: {error}"],
                    )

                csv_result = self._query_csv(table_name, analysis)
                csv_result.warnings = [
                    f"MySQL 조회 실패로 CSV fallback을 사용했습니다: {type(error).__name__}: {error}",
                    *csv_result.warnings,
                ]
                return csv_result

        if self.config.fallback_to_csv:
            csv_result = self._query_csv(table_name, analysis)
            csv_result.warnings = [
                "MySQL 접속 정보가 설정되지 않아 CSV fallback을 사용했습니다. "
                "KAIST_MYSQL_HOST/USER/PASSWORD/DATABASE 환경변수를 확인하세요.",
                *csv_result.warnings,
            ]
            return csv_result

        return SqlQueryResult(
            table_name=table_name,
            rows=[],
            columns=[],
            conditions=getattr(analysis, "sql_conditions", {}),
            message="MySQL 접속 정보가 설정되지 않았습니다.",
            warnings=["KAIST_MYSQL_USER 또는 KAIST_MYSQL_DATABASE 값이 비어 있습니다."],
        )

    def _table_name_from_analysis(self, analysis: QueryAnalysis) -> str | None:
        task_hint = getattr(analysis, "sql_task_hint", None)
        table_name = self.TASK_TABLE_MAP.get(task_hint)

        if table_name:
            return table_name

        table_hint = getattr(analysis, "sql_table_hint", None)
        return self.TABLE_HINT_MAP.get(table_hint, table_hint)

    # ============================================================
    # MySQL 조회
    # ============================================================

    def _connect(self):
        import pymysql
        from pymysql.cursors import DictCursor

        return pymysql.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            charset="utf8mb4",
            cursorclass=DictCursor,
            connect_timeout=self.config.connect_timeout,
            read_timeout=max(self.config.connect_timeout, 5),
        )

    def _query_mysql(self, table_name: str, analysis: QueryAnalysis) -> SqlQueryResult:
        if table_name == "department":
            return self._query_mysql_departments(analysis)

        if table_name == "course":
            return self._query_mysql_courses(analysis)

        if table_name == "office_contacts":
            return self._query_mysql_office_contacts(analysis)

        if table_name == "asset":
            return self._query_mysql_assets(analysis)

        mysql_table = self.MYSQL_TABLE_NAMES.get(table_name)

        if not mysql_table:
            return self._unsupported_task_result(analysis)

        sql, params = self._build_mysql_select(mysql_table, table_name, analysis)
        rows = self._fetch_mysql_rows(sql, params)
        rows, total_available = self._split_total_count(rows)

        return self._result(
            table_name=mysql_table,
            rows=rows,
            columns=self._columns_from_rows(rows),
            analysis=analysis,
            message=f"{mysql_table} MySQL 조회가 완료되었습니다.",
            total_available=total_available,
        )

    def _query_mysql_departments(self, analysis: QueryAnalysis) -> SqlQueryResult:
        if not self._is_ai_department_master_question(analysis):
            office_rows = self._fetch_mysql_rows(
                """
                SELECT
                    program_name,
                    phone,
                    website,
                    building_location,
                    source,
                    source_page
                FROM department_office
                ORDER BY program_name
                """,
                [],
            )
            rows = self._build_academic_unit_rows(office_rows, analysis)

            return self._result(
                table_name="department",
                rows=rows,
                columns=[
                    "college",
                    "unit_type",
                    "program_name",
                    "phone",
                    "website",
                    "building_location",
                    "source",
                ],
                analysis=analysis,
                message="department_office 기반 KAIST 학과/프로그램 목록 조회가 완료되었습니다.",
            )

        supported_codes = ["ai_systems", "fx", "ax", "aic"]
        placeholders = ", ".join(["%s"] * len(supported_codes))

        sql = f"""
            SELECT
                dept,
                dept_name,
                'AI대학 4개 학과' AS scope,
                CASE dept
                    WHEN 'ai_systems' THEN 1
                    WHEN 'fx' THEN 2
                    WHEN 'ai_future' THEN 2
                    WHEN 'ax' THEN 3
                    WHEN 'aic' THEN 4
                    ELSE 99
                END AS display_order
            FROM department
            WHERE dept IN ({placeholders})
            ORDER BY display_order, dept_name
        """
        rows = self._fetch_mysql_rows(sql, supported_codes)

        return self._result(
            table_name="department",
            rows=rows,
            columns=["display_order", "dept", "dept_name", "scope"],
            analysis=analysis,
            message="department MySQL 조회가 완료되었습니다.",
        )

    def _is_ai_department_master_question(self, analysis: QueryAnalysis) -> bool:
        question = str(getattr(analysis, "normalized_question", "") or "").lower()
        return any(
            keyword.lower() in question
            for keyword in [
                "ai대학",
                "ai 대학",
                "ai 학과",
                "ai학과",
                "ai 관련",
                "인공지능 학과",
                "인공지능학과",
            ]
        )

    def _query_mysql_courses(self, analysis: QueryAnalysis) -> SqlQueryResult:
        where, params = self._mysql_department_where("c", analysis)
        keyword_clause, keyword_params = self._mysql_keyword_clause(
            columns=["c.course_code", "c.course_name", "c.course_type", "c.course_description", "t.track_name"],
            keywords=self._specific_keywords(
                analysis,
                generic_words={
                    "교과목", "과목", "강의", "수업", "목록", "설명",
                    "학과별", "비교", "비교해줘", "전체",
                },
            ),
        )

        if keyword_clause:
            where.append(keyword_clause)
            params.extend(keyword_params)

        sql = f"""
            SELECT
                c.record_id,
                COALESCE(d.dept_name, c.dept) AS dept_name,
                c.dept,
                c.course_level,
                c.course_code,
                c.course_name,
                c.course_type,
                c.credit,
                c.course_description,
                GROUP_CONCAT(DISTINCT t.track_name ORDER BY t.track_name SEPARATOR ', ') AS track_name,
                c.source_url,
                c.crawled_at,
                COUNT(*) OVER() AS {self._TOTAL_COUNT_ALIAS}
            FROM course c
            LEFT JOIN department d ON d.dept = c.dept
            LEFT JOIN course_track ct ON ct.course_id = c.record_id
            LEFT JOIN track t ON t.track_id = ct.track_id
            {self._where_sql(where)}
            GROUP BY
                c.record_id, d.dept_name, c.dept, c.course_level, c.course_code,
                c.course_name, c.course_type, c.credit, c.course_description,
                c.source_url, c.crawled_at
            ORDER BY c.dept, c.course_code, c.course_name
            LIMIT {self._limit()}
        """
        rows = self._fetch_mysql_rows(sql, params)
        rows, total_available = self._split_total_count(rows)

        return self._result(
            table_name="course",
            rows=rows,
            columns=self._columns_from_rows(rows),
            analysis=analysis,
            message="course MySQL 조회가 완료되었습니다.",
            total_available=total_available,
        )

    def _query_mysql_office_contacts(self, analysis: QueryAnalysis) -> SqlQueryResult:
        where: list[str] = []
        params: list[Any] = []
        dept_name = DEPT_LABELS.get(str(getattr(analysis, "department_code", "") or ""))

        if dept_name:
            where.append("program_name = %s")
            params.append(dept_name)

        sql = f"""
            SELECT
                office_id,
                program_name,
                phone,
                website,
                building_location,
                source,
                source_page
            FROM department_office
            {self._where_sql(where)}
            ORDER BY program_name
            LIMIT {self._limit()}
        """
        rows = self._fetch_mysql_rows(sql, params)

        return self._result(
            table_name="department_office",
            rows=rows,
            columns=self._columns_from_rows(rows),
            analysis=analysis,
            message="department_office MySQL 조회가 완료되었습니다.",
        )

    def _query_mysql_assets(self, analysis: QueryAnalysis) -> SqlQueryResult:
        asset_where, asset_params = self._mysql_department_where("a", analysis)
        attachment_where, attachment_params = self._mysql_department_where("att", analysis)

        keywords = self._specific_keywords(
            analysis,
            generic_words=self._generic_words_for_table("asset"),
        )

        asset_keyword_clause, asset_keyword_params = self._mysql_keyword_clause(
            columns=["a.category", "a.topic", "a.content_type", "a.asset_type", "a.text", "a.url", "a.filename"],
            keywords=keywords,
        )
        if asset_keyword_clause:
            asset_where.append(asset_keyword_clause)
            asset_params.extend(asset_keyword_params)

        attachment_keyword_clause, attachment_keyword_params = self._mysql_keyword_clause(
            columns=["att.board", "att.post_id", "att.filename", "att.url", "att.ext", "att.content_type"],
            keywords=keywords,
        )
        if attachment_keyword_clause:
            attachment_where.append(attachment_keyword_clause)
            attachment_params.extend(attachment_keyword_params)

        asset_sql = f"""
            SELECT
                'asset' AS result_source,
                a.record_id AS record_id,
                a.dept,
                d.dept_name,
                a.category,
                a.topic,
                a.content_type,
                a.asset_type,
                a.text,
                a.url,
                a.filename,
                a.source_url,
                a.crawled_at,
                COUNT(*) OVER() AS {self._TOTAL_COUNT_ALIAS}
            FROM asset a
            LEFT JOIN department d ON d.dept = a.dept
            {self._where_sql(asset_where)}
            ORDER BY a.dept, a.asset_type, a.topic
            LIMIT {self._limit()}
        """
        attachment_sql = f"""
            SELECT
                'attachment' AS result_source,
                CAST(att.attachment_id AS CHAR) AS record_id,
                att.dept,
                d.dept_name,
                att.board AS category,
                att.post_id AS topic,
                att.content_type,
                att.ext AS asset_type,
                att.filename AS text,
                att.url,
                att.filename,
                att.url AS source_url,
                att.crawled_at,
                COUNT(*) OVER() AS {self._TOTAL_COUNT_ALIAS}
            FROM attachment att
            LEFT JOIN department d ON d.dept = att.dept
            {self._where_sql(attachment_where)}
            ORDER BY att.dept, att.filename
            LIMIT {self._limit()}
        """

        asset_rows, asset_total = self._split_total_count(
            self._fetch_mysql_rows(asset_sql, asset_params)
        )
        attachment_rows, attachment_total = self._split_total_count(
            self._fetch_mysql_rows(attachment_sql, attachment_params)
        )
        # 두 쿼리를 합쳐 캡으로 자른다. 진짜 총계도 두 매칭 수의 합이다
        # (둘 다 None이면 미상 유지 → 고지는 len(rows)로 후퇴).
        rows = [*asset_rows, *attachment_rows][: self._limit()]
        if asset_total is None and attachment_total is None:
            total_available = None
        else:
            total_available = (asset_total or 0) + (attachment_total or 0)

        return self._result(
            table_name="asset",
            rows=rows,
            columns=self._columns_from_rows(rows),
            analysis=analysis,
            message="asset/attachment MySQL 조회가 완료되었습니다.",
            total_available=total_available,
        )

    def _build_mysql_select(
        self,
        mysql_table: str,
        logical_table: str,
        analysis: QueryAnalysis,
    ) -> tuple[str, list[Any]]:
        params: list[Any] = []
        where: list[str] = []

        department_alias = "base"
        if logical_table in {"admission", "asset", "event", "person"}:
            where, params = self._mysql_department_where(department_alias, analysis)

        if not getattr(analysis, "suppress_sql_keyword_filter", False):
            keyword_columns = self._keyword_columns_for_mysql_table(logical_table)
            generic_words = self._generic_words_for_table(logical_table)
            keywords = self._specific_keywords(analysis, generic_words=generic_words)
            keyword_clause, keyword_params = self._mysql_keyword_clause(keyword_columns, keywords)

            if keyword_clause:
                where.append(keyword_clause)
                params.extend(keyword_params)

        select_sql = self._select_sql_for_table(mysql_table, logical_table)

        sql = f"""
            {select_sql}
            {self._where_sql(where)}
            {self._order_sql_for_table(logical_table)}
            LIMIT {self._limit()}
        """

        return sql, params

    def _select_sql_for_table(self, mysql_table: str, logical_table: str) -> str:
        # COUNT(*) OVER()는 WHERE/JOIN 적용 후·LIMIT 적용 전의 전체 행 수다.
        # person→department는 다대일이라 JOIN이 행을 부풀리지 않으므로 매칭 인원과 같다.
        total_col = f", COUNT(*) OVER() AS {self._TOTAL_COUNT_ALIAS}"

        if logical_table in {"admission", "asset", "event", "person"}:
            return f"""
                SELECT base.*, d.dept_name{total_col}
                FROM {mysql_table} base
                LEFT JOIN department d ON d.dept = base.dept
            """

        return f"SELECT base.*{total_col} FROM {mysql_table} base"

    def _order_sql_for_table(self, logical_table: str) -> str:
        order_map = {
            "admission": "ORDER BY base.dept, base.admission_type, base.schedule_date, base.title",
            "asset": "ORDER BY base.dept, base.asset_type, base.topic",
            "event": "ORDER BY base.dept, base.event_date, base.title",
            "kaist_links": "ORDER BY base.link_name",
            "kaist_link": "ORDER BY base.link_name",
            "kaist_profile": "ORDER BY base.item",
            "kaist_statistics": "ORDER BY base.stat_group, base.level",
            "person": (
                "ORDER BY base.dept, "
                "CASE base.role_normalized "
                "WHEN '학과장' THEN 0 "
                "WHEN '전임교수' THEN 1 "
                "WHEN '교수' THEN 2 "
                "WHEN '중점교원' THEN 3 "
                "WHEN '겸직교수' THEN 4 "
                "WHEN '겸임교수' THEN 5 "
                "ELSE 6 END, "
                "base.name"
            ),
        }

        return order_map.get(logical_table, "")

    def _mysql_department_where(
        self,
        alias: str,
        analysis: QueryAnalysis,
    ) -> tuple[list[str], list[Any]]:
        department_code = getattr(analysis, "department_code", None)

        if not department_code:
            return [], []

        return [f"{alias}.dept = %s"], [department_code]

    def _mysql_keyword_clause(
        self,
        columns: list[str],
        keywords: list[str],
    ) -> tuple[str, list[Any]]:
        if not columns or not keywords:
            return "", []

        parts = []
        params: list[Any] = []

        for keyword in keywords:
            keyword = str(keyword).strip()
            if not keyword:
                continue

            like_value = f"%{keyword}%"
            per_keyword = []

            for column in columns:
                per_keyword.append(f"COALESCE(CAST({column} AS CHAR), '') LIKE %s")
                params.append(like_value)

            if per_keyword:
                parts.append("(" + " OR ".join(per_keyword) + ")")

        if not parts:
            return "", []

        return "(" + " OR ".join(parts) + ")", params

    def _keyword_columns_for_mysql_table(self, logical_table: str) -> list[str]:
        columns = {
            "admission": ["base.admission_type", "base.page_title", "base.section_title", "base.title", "base.content"],
            "asset": ["base.category", "base.topic", "base.content_type", "base.asset_type", "base.text", "base.url", "base.filename"],
            "event": ["base.event_type", "base.page_title", "base.title", "base.content"],
            "kaist_links": ["base.link_name", "base.url", "base.note"],
            "kaist_link": ["base.link_name", "base.url", "base.note"],
            "kaist_profile": ["base.item", "base.content", "base.note"],
            "kaist_statistics": ["base.stat_group", "base.level", "base.note"],
            "person": ["base.name", "base.name_ko", "base.name_en", "base.role", "base.email", "base.research_area", "base.homepage"],
        }

        return columns.get(logical_table, [])

    def _generic_words_for_table(self, logical_table: str) -> set[str]:
        common = {
            "정보", "알려줘", "보여줘", "정리해줘", "목록", "명단", "명부",
            "리스트", "전체", "전부",
            "kaist", "KAIST", "카이스트", "학과", "대학", "관련",
        }
        table_specific = {
            "admission": {"입학", "지원", "전형", "모집", "대학원"},
            "asset": {"링크", "url", "URL", "사이트", "자료", "다운로드"},
            "event": {"행사", "공지", "설명회", "일정"},
            "kaist_links": {"링크", "홈페이지"},
            "kaist_link": {"링크", "홈페이지"},
            "kaist_profile": {"기본", "기본정보"},
            "kaist_statistics": {"통계", "수", "몇", "몇명", "몇 명"},
            # 호칭/역할 단어는 이름 필터가 아니다. 누락된 존칭형("교수님",
            # "교수님들")이 키워드로 살아남으면 name/email LIKE가 0행을 만들어
            # 학과 교수 전수 질문이 빈 결과가 된다(특정 이름·연구분야 키워드는 보존).
            "person": {
                "교수", "교수님", "교수님들", "교수진", "교원",
                "구성원", "이메일", "메일",
            },
        }

        return common | table_specific.get(logical_table, set())

    def _fetch_mysql_rows(self, sql: str, params: list[Any]) -> list[dict[str, Any]]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def _where_sql(self, where: list[str]) -> str:
        if not where:
            return ""

        return "WHERE " + " AND ".join(where)

    # ============================================================
    # CSV fallback 조회
    # ============================================================

    def _query_csv(self, table_name: str, analysis: QueryAnalysis) -> SqlQueryResult:
        try:
            if table_name == "department":
                return self._query_csv_departments(analysis)

            if table_name == "course":
                return self._query_csv_courses(analysis)

            if table_name == "office_contacts":
                return self._query_csv_office_contacts(analysis)

            if table_name == "asset":
                return self._query_csv_assets(analysis)

            return self._query_csv_table(table_name, analysis)

        except Exception as error:
            return SqlQueryResult(
                table_name=str(table_name),
                rows=[],
                columns=[],
                conditions=getattr(analysis, "sql_conditions", {}),
                message="CSV 조회 중 오류가 발생했습니다.",
                warnings=[f"{type(error).__name__}: {error}"],
            )

    def _limit(self) -> int:
        return max(1, int(self.config.max_rows))

    def _read_csv(self, table_name: str) -> pd.DataFrame:
        for filename in self.FILE_MAP.get(table_name, ()):
            path = self.csv_data_dir / filename
            if path.exists():
                return pd.read_csv(path).fillna("")
        return pd.DataFrame()

    def _read_first_existing(self, filenames: tuple[str, ...]) -> pd.DataFrame:
        for filename in filenames:
            path = self.csv_data_dir / filename
            if path.exists():
                return pd.read_csv(path).fillna("")
        return pd.DataFrame()

    def _ensure_department_name(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        if "dept_name" not in df.columns and "dept" in df.columns:
            df = df.copy()
            df["dept_name"] = df["dept"].astype(str).map(DEPT_LABELS).fillna(df["dept"].astype(str))

        return df.fillna("")

    def _filter_department(self, df: pd.DataFrame, analysis: QueryAnalysis) -> pd.DataFrame:
        if df.empty:
            return df

        department_code = getattr(analysis, "department_code", None)

        if department_code:
            if "dept" in df.columns:
                return df[df["dept"].astype(str) == str(department_code)].copy()

            dept_name = DEPT_LABELS.get(str(department_code), "")
            if dept_name and "dept_name" in df.columns:
                return df[df["dept_name"].astype(str) == dept_name].copy()

            if dept_name and "program_name" in df.columns:
                return df[df["program_name"].astype(str) == dept_name].copy()

            return df

        if "dept" in df.columns:
            return df[df["dept"].astype(str).isin(SUPPORTED_AI_COLLEGE_DEPT_CODES)].copy()

        return df

    def _keywords_from_analysis(self, analysis: QueryAnalysis) -> list[str]:
        normalized_question = getattr(analysis, "normalized_question", "") or ""
        tokens = re.findall(r"[가-힣a-zA-Z0-9_.+-]+", normalized_question)

        return self._dedupe_keywords(tokens, analysis)

    def _specific_keywords(
        self,
        analysis: QueryAnalysis,
        generic_words: set[str] | None = None,
    ) -> list[str]:
        # 다중 요청(접속) 질문에서 키워드 LIKE 필터는 토큰 합집합으로 관련 행을
        # 오히려 잘라낸다(예: '입학 일정이랑 제출 서류'가 면접 일정 행을 누락).
        # MySQL 경로(_build_mysql_select)는 suppress_sql_keyword_filter로 이를 이미
        # 끄지만 CSV 경로는 빠져 있었다. 여기서 키워드를 비워 두 경로를 일치시킨다.
        if getattr(analysis, "suppress_sql_keyword_filter", False):
            return []

        keywords = self._keywords_from_analysis(analysis)
        generic_words = generic_words or set()

        return [
            keyword
            for keyword in keywords
            if keyword not in generic_words
        ]

    def _dedupe_keywords(
        self,
        values: list[str],
        analysis: QueryAnalysis,
    ) -> list[str]:
        stopwords = {
            "알려줘", "보여줘", "궁금해", "무엇", "어떤", "정보", "목록",
            "관련", "학과", "KAIST", "kaist", "카이스트", "전체", "전부",
            "각", "및", "그리고", "대한", "대해", "있는", "없는",
            "link", "links",
        }
        department_terms = {
            "AI컴퓨팅학과", "AI컴퓨팅", "AI시스템학과", "AI시스템",
            "AX학과", "AX", "AI미래학과", "AI미래",
            "aic", "ai_systems", "ax", "fx",
        }

        if getattr(analysis, "department_name", None):
            department_terms.add(str(analysis.department_name))
        if getattr(analysis, "department_code", None):
            department_terms.add(str(analysis.department_code))

        deduped = []
        seen = set()

        for value in values:
            value = str(value).strip()
            if not value or len(value) < 2:
                continue
            if value in stopwords or value in department_terms:
                continue
            if value.lower() in {word.lower() for word in stopwords | department_terms}:
                continue
            if value in seen:
                continue
            seen.add(value)
            deduped.append(value)

        return deduped

    def _filter_keywords(
        self,
        df: pd.DataFrame,
        keywords: list[str],
        require_match: bool = False,
    ) -> pd.DataFrame:
        if df.empty or not keywords:
            return df

        text_columns = [
            column
            for column in df.columns
            if df[column].dtype == object or str(df[column].dtype).startswith("string")
        ]

        if not text_columns:
            return df

        combined = df[text_columns].astype(str).agg(" ".join, axis=1).str.lower()
        mask = pd.Series(False, index=df.index)

        for keyword in keywords:
            keyword = str(keyword).strip().lower()
            if keyword:
                mask = mask | combined.str.contains(keyword, regex=False, na=False)

        filtered = df[mask].copy()
        if filtered.empty and not require_match:
            return df

        return filtered

    def _sort_table(self, table_name: str, df: pd.DataFrame) -> pd.DataFrame:
        preferred = {
            "admission": ["dept", "admission_type", "title"],
            "asset": ["dept", "asset_type", "topic"],
            "course": ["dept", "course_code", "course_name", "track_name"],
            "department": ["program_name"],
            "department_office": ["program_name"],
            "event": ["dept", "event_date", "title"],
            "kaist_links": ["link_name"],
            "kaist_link": ["link_name"],
            "kaist_profile": ["item"],
            "kaist_statistics": ["stat_group", "level"],
            "office_contacts": ["program_name"],
        }

        if table_name == "person" and "role_normalized" in df.columns:
            df = df.copy()
            df["_role_rank"] = df["role_normalized"].map(PERSON_ROLE_DISPLAY_ORDER)
            df["_role_rank"] = df["_role_rank"].fillna(len(PERSON_ROLE_DISPLAY_ORDER))
            sort_columns = [c for c in ["dept"] if c in df.columns] + ["_role_rank"]
            if "name" in df.columns:
                sort_columns.append("name")
            return df.sort_values(sort_columns, kind="stable").drop(columns="_role_rank")

        columns = [column for column in preferred.get(table_name, []) if column in df.columns]

        if columns:
            return df.sort_values(columns, kind="stable")

        return df

    def _query_csv_departments(self, analysis: QueryAnalysis) -> SqlQueryResult:
        if not self._is_ai_department_master_question(analysis):
            office_df = self._read_csv("department_office")

            if office_df.empty:
                return self._missing_file_result("department_office", analysis)

            rows = self._build_academic_unit_rows(
                office_df.to_dict("records"),
                analysis,
            )

            return self._result(
                table_name="department",
                rows=rows,
                columns=[
                    "college",
                    "unit_type",
                    "program_name",
                    "phone",
                    "website",
                    "building_location",
                    "source",
                ],
                analysis=analysis,
                message="department_offices.csv 기반 KAIST 학과/프로그램 목록 조회가 완료되었습니다.",
            )

        rows_by_dept: dict[str, dict[str, Any]] = {}

        for filename in self.FILE_MAP["department"]:
            path = self.csv_data_dir / filename
            if not path.exists():
                continue

            try:
                df = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
            except Exception:
                continue

            if "dept" not in df.columns:
                continue

            df = self._ensure_department_name(df)
            df = df[df["dept"].astype(str).isin(SUPPORTED_AI_COLLEGE_DEPT_CODES)]

            for _, row in df.iterrows():
                dept = str(row.get("dept", "")).strip()
                dept_name = str(row.get("dept_name", "")).strip() or DEPT_LABELS.get(dept, dept)
                if not dept:
                    continue

                item = rows_by_dept.setdefault(
                    dept,
                    {
                        "display_order": DEPARTMENT_DISPLAY_ORDER.get(dept, 99),
                        "dept": dept,
                        "dept_name": dept_name,
                        "scope": "AI대학 4개 학과",
                        "source_tables": set(),
                    },
                )
                item["source_tables"].add(filename)

        rows = []
        for item in rows_by_dept.values():
            row = dict(item)
            row["source_tables"] = ", ".join(sorted(row["source_tables"]))
            rows.append(row)

        rows = sorted(rows, key=lambda row: (row["display_order"], row["dept_name"]))

        return self._result(
            table_name="department",
            rows=rows,
            columns=["display_order", "dept", "dept_name", "scope", "source_tables"],
            analysis=analysis,
            message="department CSV 조회가 완료되었습니다.",
        )

    def _build_academic_unit_rows(
        self,
        source_rows: list[dict[str, Any]],
        analysis: QueryAnalysis,
    ) -> list[dict[str, Any]]:
        college_filter = self._college_filter_from_question(analysis)
        rows: list[dict[str, Any]] = []

        for row in source_rows:
            program_name = str(row.get("program_name", "") or "").strip()
            if not program_name:
                continue

            college = KAIST_ACADEMIC_UNIT_GROUPS.get(
                program_name,
                "기타/학제 프로그램",
            )

            if college_filter and college != college_filter:
                continue

            rows.append({
                "college": college,
                "unit_type": self._academic_unit_type(program_name),
                "program_name": program_name,
                "phone": row.get("phone"),
                "website": row.get("website"),
                "building_location": row.get("building_location"),
                "source": row.get("source"),
                "_college_order": KAIST_ACADEMIC_GROUP_ORDER.get(college, 99),
            })

        rows.sort(key=lambda row: (row["_college_order"], str(row["program_name"])))

        for row in rows:
            row.pop("_college_order", None)

        return rows[: self._limit()]

    def _college_filter_from_question(self, analysis: QueryAnalysis) -> str | None:
        question = str(getattr(analysis, "normalized_question", "") or "")
        lowered_question = question.lower()

        if self._is_ai_department_master_question(analysis):
            return "AI대학"

        for keyword, college in KAIST_ACADEMIC_GROUP_ALIASES.items():
            if keyword.lower() in lowered_question:
                return college

        return None

    def _academic_unit_type(self, program_name: str) -> str:
        if "학과" in program_name:
            return "학과"
        if "학부" in program_name:
            return "학부"
        if "대학원" in program_name:
            return "대학원"
        if "전공" in program_name:
            return "학제전공"
        if "프로그램" in program_name:
            return "프로그램"

        return "기타"

    def _query_csv_table(self, table_name: str, analysis: QueryAnalysis) -> SqlQueryResult:
        csv_table_name = "kaist_link" if table_name == "kaist_links" else table_name
        df = self._read_csv(table_name)

        if df.empty:
            return self._missing_file_result(table_name, analysis)

        df = self._ensure_department_name(df)
        df = self._filter_department(df, analysis)

        keywords = self._specific_keywords(
            analysis,
            generic_words=self._generic_words_for_table(table_name),
        )
        require_match = table_name in {"asset", "kaist_links", "kaist_link"} and bool(keywords)
        df = self._filter_keywords(df, keywords, require_match=require_match)
        total_available = len(df)  # head(limit) 캡 전 진짜 매칭 수
        df = self._sort_table(table_name, df).head(self._limit())

        return self._result(
            table_name=csv_table_name,
            rows=df.to_dict("records"),
            columns=list(df.columns),
            analysis=analysis,
            message=f"{table_name} CSV 조회가 완료되었습니다.",
            total_available=total_available,
        )

    def _query_csv_courses(self, analysis: QueryAnalysis) -> SqlQueryResult:
        df = self._read_first_existing(("course_track_map.csv",))

        if df.empty:
            df = self._read_first_existing(("courses.csv", "courses_clean.csv"))

        if df.empty:
            return self._missing_file_result("course", analysis)

        df = self._ensure_department_name(df)

        for column in ["track_name", "course_type", "source_url"]:
            if column not in df.columns:
                df[column] = ""

        df = self._filter_department(df, analysis)
        keywords = self._specific_keywords(
            analysis,
            generic_words={
                "교과목", "과목", "강의", "수업", "커리큘럼", "교육과정",
                "목록", "설명", "학과별", "비교", "비교해줘", "전체",
            },
        )
        df = self._filter_keywords(df, keywords, require_match=False)

        keep_columns = [
            "dept",
            "dept_name",
            "course_code",
            "course_name",
            "track_name",
            "course_type",
            "course_description",
            "source_url",
            "record_id",
        ]
        keep_columns = [column for column in keep_columns if column in df.columns]

        if keep_columns:
            df = df[keep_columns]

        deduped = (
            df.drop_duplicates(
                subset=[
                    column
                    for column in ["dept_name", "course_code", "course_name", "track_name", "course_type"]
                    if column in df.columns
                ]
            )
            .pipe(lambda x: self._sort_table("course", x))
        )
        total_available = len(deduped)  # head(limit) 캡 전 진짜 매칭 수
        df = deduped.head(self._limit())

        return self._result(
            table_name="course",
            rows=df.to_dict("records"),
            columns=list(df.columns),
            analysis=analysis,
            message="교과목 CSV 조회가 완료되었습니다.",
            total_available=total_available,
        )

    def _query_csv_assets(self, analysis: QueryAnalysis) -> SqlQueryResult:
        asset_df = self._read_csv("asset")
        attachment_df = self._read_csv("attachment")

        frames = []

        if not asset_df.empty:
            asset_df = self._ensure_department_name(asset_df.copy())
            asset_df["result_source"] = "asset"
            frames.append(asset_df)

        if not attachment_df.empty:
            attachment_df = self._ensure_department_name(attachment_df.copy())
            attachment_df["result_source"] = "attachment"
            attachment_df["asset_type"] = attachment_df.get("ext", "")
            attachment_df["text"] = attachment_df.get("filename", "")
            attachment_df["source_url"] = attachment_df.get("url", "")
            frames.append(attachment_df)

        if not frames:
            return self._missing_file_result("asset", analysis)

        df = pd.concat(frames, ignore_index=True, sort=False).fillna("")
        df = self._filter_department(df, analysis)

        keywords = self._specific_keywords(
            analysis,
            generic_words=self._generic_words_for_table("asset"),
        )
        df = self._filter_keywords(df, keywords, require_match=bool(keywords))
        total_available = len(df)  # head(limit) 캡 전 진짜 매칭 수
        df = self._sort_table("asset", df).head(self._limit())

        return self._result(
            table_name="asset",
            rows=df.to_dict("records"),
            columns=list(df.columns),
            analysis=analysis,
            message="자료/링크 CSV 조회가 완료되었습니다.",
            total_available=total_available,
        )

    def _query_csv_office_contacts(self, analysis: QueryAnalysis) -> SqlQueryResult:
        office_df = self._read_csv("office_contacts")

        if office_df.empty:
            return self._missing_file_result("office_contacts", analysis)

        df = self._filter_department(office_df.fillna(""), analysis)
        df = self._sort_table("office_contacts", df).head(self._limit())

        return self._result(
            table_name="department_office",
            rows=df.to_dict("records"),
            columns=list(df.columns),
            analysis=analysis,
            message="학과 사무실/연락처 CSV 조회가 완료되었습니다.",
        )

    # ============================================================
    # Result helpers
    # ============================================================

    def _result(
        self,
        table_name: str,
        rows: list[dict[str, Any]],
        columns: list[str],
        analysis: QueryAnalysis,
        message: str,
        warnings: list[str] | None = None,
        total_available: int | None = None,
    ) -> SqlQueryResult:
        final_warnings = list(warnings or [])

        if not rows and getattr(analysis, "department_code", None):
            final_warnings.append(
                f"{table_name}에서 dept='{analysis.department_code}' 조건에 맞는 행이 없습니다."
            )

        return SqlQueryResult(
            table_name=table_name,
            rows=rows,
            columns=columns,
            conditions=getattr(analysis, "sql_conditions", {}),
            message=message,
            warnings=final_warnings,
            total_available=total_available,
        )

    def _columns_from_rows(self, rows: list[dict[str, Any]]) -> list[str]:
        columns: list[str] = []

        for row in rows:
            for key in row.keys():
                if key not in columns:
                    columns.append(key)

        return columns

    def _split_total_count(
        self,
        rows: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], int | None]:
        """`COUNT(*) OVER() AS _total_count` 윈도우 컬럼을 행에서 떼어낸다.

        LIMIT 전 진짜 매칭 수를 단일 쿼리로 구하려고 SELECT에 심은 보조 컬럼이다.
        값을 회수하고 행에서는 제거해 표/컬럼에 섞이지 않게 한다(미존재 시 None).
        """
        total: int | None = None
        cleaned: list[dict[str, Any]] = []

        for row in rows:
            if self._TOTAL_COUNT_ALIAS in row:
                row = dict(row)
                value = row.pop(self._TOTAL_COUNT_ALIAS)
                if total is None and value is not None:
                    try:
                        total = int(value)
                    except (TypeError, ValueError):
                        total = None
            cleaned.append(row)

        return cleaned, total

    def _missing_file_result(self, table_name: str, analysis: QueryAnalysis) -> SqlQueryResult:
        filenames = ", ".join(self.FILE_MAP.get(table_name, (str(table_name),)))

        return SqlQueryResult(
            table_name=str(table_name),
            rows=[],
            columns=[],
            conditions=getattr(analysis, "sql_conditions", {}),
            message=f"CSV 파일을 찾을 수 없습니다: {filenames}",
            warnings=[f"확인 경로: {self.csv_data_dir}"],
        )

    def _unsupported_task_result(self, analysis: QueryAnalysis) -> SqlQueryResult:
        return SqlQueryResult(
            table_name=str(getattr(analysis, "sql_table_hint", None) or "unknown"),
            rows=[],
            columns=[],
            conditions=getattr(analysis, "sql_conditions", {}),
            message="지원하지 않는 SQL 조회 유형입니다.",
            warnings=[
                f"sql_task_hint={getattr(analysis, 'sql_task_hint', None)}",
                f"sql_table_hint={getattr(analysis, 'sql_table_hint', None)}",
            ],
        )


def run_examples() -> None:
    from rag.query_analyzer import QuestionAnalyzer

    analyzer = QuestionAnalyzer()
    sql_tool = SQLTool()

    questions = [
        "AI시스템학과 교과목 알려줘",
        "AX학과 교수진 이메일 목록 보여줘",
        "KAIST 학과 사무실 전화번호 알려줘",
        "카이스트 재학생 수 알려줘",
        "AI컴퓨팅학과 제출서류 알려줘",
        "AX학과 브로슈어 pdf 링크 알려줘",
    ]

    for question in questions:
        analysis = analyzer.analyze(question)
        result = sql_tool.query(analysis)

        print("=" * 100)
        print("질문:", question)
        print("route:", analysis.route)
        print("task:", analysis.sql_task_hint)
        print("table:", result.table_name)
        print("message:", result.message)
        print("warnings:", result.warnings)
        print("row_count:", len(result.rows))
        print("columns:", result.columns)
        print("rows_preview:", result.rows[:3])


if __name__ == "__main__":
    run_examples()
