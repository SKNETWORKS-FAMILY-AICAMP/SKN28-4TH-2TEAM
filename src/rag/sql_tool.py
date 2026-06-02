from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.query_analyzer import QueryAnalysis
from src.rag.context_builder import SqlQueryResult


SUPPORTED_AI_COLLEGE_DEPT_CODES = ("aic", "ai_systems", "ai_future", "ax", "fx")

DEPT_LABELS = {
    "aic": "AI컴퓨팅학과",
    "ai_systems": "AI시스템학과",
    "ai_future": "AI미래학과",
    "fx": "AI미래학과",
    "ax": "AX학과",
}


@dataclass
class SQLToolConfig:
    """
    MySQL 대신 data/processed/csv 하위 CSV를 조회하는 설정입니다.

    기존 RagPipeline 연결부가 SQLTool 이름을 사용하므로 클래스명은 유지합니다.
    환경변수 KAIST_CSV_DATA_DIR로 CSV 경로를 바꿀 수 있습니다.
    """

    csv_data_dir: str = str(PROJECT_ROOT / "data" / "processed" / "csv")
    max_rows: int = 100

    @classmethod
    def from_env(cls) -> "SQLToolConfig":
        return cls(
            csv_data_dir=os.getenv(
                "KAIST_CSV_DATA_DIR",
                str(PROJECT_ROOT / "data" / "processed" / "csv"),
            ),
            max_rows=int(os.getenv("KAIST_SQL_MAX_ROWS", "100")),
        )


class SQLTool:
    """
    KAIST AI College RAG Agent용 CSV 조회 도구입니다.

    역할:
    - QueryAnalysis.sql_task_hint에 따라 data/processed/csv/*.csv 조회
    - 조회 결과를 ContextBuilder가 받을 수 있는 SqlQueryResult 형태로 반환
    - RagPipeline에서는 기존처럼 sql_retriever=SQLTool() 형태로 연결 가능

    주의:
    - 이름은 SQLTool이지만 실제 연결은 MySQL이 아니라 CSV입니다.
    """

    FILE_MAP = {
        "admission": ("admissions.csv", "admissions_clean.csv"),
        "asset": ("assets.csv", "assets_clean.csv"),
        "attachment": ("attachments.csv", "attachments_clean.csv"),
        "course": ("course_track_map.csv", "courses.csv", "courses_clean.csv"),
        "course_track": ("course_track_map.csv",),
        "department": ("department_offices.csv",),
        "event": ("events.csv", "events_clean.csv"),
        "kaist_links": ("kaist_links.csv",),
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
        task_hint = getattr(analysis, "sql_task_hint", None)
        table_name = self.TASK_TABLE_MAP.get(task_hint)

        if not table_name:
            table_hint = getattr(analysis, "sql_table_hint", None)
            table_name = self.TABLE_HINT_MAP.get(table_hint, table_hint)

        if not table_name:
            return self._unsupported_task_result(analysis)

        try:
            if table_name == "course":
                return self._query_courses(analysis)

            if table_name == "office_contacts":
                return self._query_office_contacts(analysis)

            return self._query_table(table_name, analysis)

        except Exception as error:
            return SqlQueryResult(
                table_name=str(table_name),
                rows=[],
                columns=[],
                conditions=getattr(analysis, "sql_conditions", {}),
                message="CSV 조회 중 오류가 발생했습니다.",
                warnings=[f"{type(error).__name__}: {error}"],
            )

    # ============================================================
    # CSV helpers
    # ============================================================

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

            return df

        if "dept" in df.columns:
            return df[df["dept"].astype(str).isin(SUPPORTED_AI_COLLEGE_DEPT_CODES)].copy()

        if "dept_name" in df.columns:
            allowed_names = set(DEPT_LABELS.values())
            return df[df["dept_name"].astype(str).isin(allowed_names)].copy()

        return df

    def _keywords_from_analysis(self, analysis: QueryAnalysis) -> list[str]:
        values: list[str] = []

        for attr in ("keywords", "search_keywords", "entities"):
            item = getattr(analysis, attr, None)
            if isinstance(item, str):
                values.append(item)
            elif isinstance(item, (list, tuple, set)):
                values.extend(str(value) for value in item)

        conditions = getattr(analysis, "sql_conditions", {}) or {}
        if isinstance(conditions, dict):
            for value in conditions.values():
                if isinstance(value, str):
                    values.append(value)
                elif isinstance(value, (list, tuple, set)):
                    values.extend(str(v) for v in value)

        normalized_question = getattr(analysis, "normalized_question", "")
        if normalized_question:
            values.extend(
                [
                    token
                    for token in str(normalized_question).replace("?", " ").replace(",", " ").split()
                    if len(token) >= 2
                ]
            )

        # 너무 일반적인 토큰은 CSV 필터링을 오히려 방해하므로 제외합니다.
        stopwords = {
            "알려줘",
            "보여줘",
            "궁금해",
            "무엇",
            "어떤",
            "kaist",
            "KAIST",
            "학과",
            "정보",
            "목록",
            "관련",
        }

        deduped = []
        seen = set()

        for value in values:
            value = str(value).strip()
            if not value or value in stopwords or value in seen:
                continue
            seen.add(value)
            deduped.append(value)

        return deduped

    def _filter_keywords(self, df: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
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
        return filtered if not filtered.empty else df

    def _sort_table(self, table_name: str, df: pd.DataFrame) -> pd.DataFrame:
        preferred = {
            "admission": ["dept", "admission_type", "title"],
            "asset": ["dept", "asset_type", "topic"],
            "attachment": ["dept", "title"],
            "course": ["dept", "course_code", "course_name", "track_name"],
            "course_track": ["dept", "course_code", "track_name"],
            "department": ["dept", "dept_name"],
            "event": ["dept", "event_date", "title"],
            "kaist_links": ["link_name"],
            "kaist_profile": ["item"],
            "kaist_statistics": ["stat_group", "level"],
            "office_contacts": ["dept", "dept_name"],
            "person": ["dept", "role_normalized", "name"],
        }

        columns = [column for column in preferred.get(table_name, []) if column in df.columns]

        if columns:
            return df.sort_values(columns, kind="stable")

        return df

    # ============================================================
    # Query methods
    # ============================================================

    def _query_table(self, table_name: str, analysis: QueryAnalysis) -> SqlQueryResult:
        df = self._read_csv(table_name)

        if df.empty:
            return self._missing_file_result(table_name, analysis)

        df = self._ensure_department_name(df)
        df = self._filter_department(df, analysis)
        df = self._filter_keywords(df, self._keywords_from_analysis(analysis))
        df = self._sort_table(table_name, df).head(self._limit())

        return self._result(
            table_name=table_name,
            rows=df.to_dict("records"),
            columns=list(df.columns),
            analysis=analysis,
            message=f"{table_name} CSV 조회가 완료되었습니다.",
        )

    def _query_courses(self, analysis: QueryAnalysis) -> SqlQueryResult:
        """
        교과목 조회.

        우선 course_track_map.csv를 사용합니다.
        이 파일에는 course_code, course_name, dept_name, track_name, course_type이 함께 들어 있어
        UI와 RAG SQL 컨텍스트 모두에서 더 정보성이 좋습니다.
        """
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
        df = self._filter_keywords(df, self._keywords_from_analysis(analysis))

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

        df = (
            df.drop_duplicates(
                subset=[
                    column
                    for column in ["dept_name", "course_code", "course_name", "track_name", "course_type"]
                    if column in df.columns
                ]
            )
            .pipe(lambda x: self._sort_table("course", x))
            .head(self._limit())
        )

        return self._result(
            table_name="course",
            rows=df.to_dict("records"),
            columns=list(df.columns),
            analysis=analysis,
            message="교과목 CSV 조회가 완료되었습니다.",
        )

    def _query_office_contacts(self, analysis: QueryAnalysis) -> SqlQueryResult:
        office_df = self._read_csv("office_contacts")
        person_df = self._read_csv("person")
        asset_df = self._read_csv("asset")

        frames: list[pd.DataFrame] = []

        if not office_df.empty:
            office_df = self._ensure_department_name(office_df.copy())
            office_df["result_source"] = "department_offices"
            frames.append(office_df)

        if not asset_df.empty:
            asset_df = self._ensure_department_name(asset_df.copy())
            text = asset_df.astype(str).agg(" ".join, axis=1)
            mask = text.str.contains(
                "전화|연락처|사무실|행정실|위치|office|contact|phone|email",
                regex=True,
                case=False,
                na=False,
            )
            contact_assets = asset_df[mask].copy()
            if not contact_assets.empty:
                contact_assets["result_source"] = "asset"
                frames.append(contact_assets)

        if not person_df.empty:
            person_df = self._ensure_department_name(person_df.copy())
            contact_columns = [column for column in ["email", "phone", "office"] if column in person_df.columns]
            if contact_columns:
                mask = person_df[contact_columns].astype(str).agg(" ".join, axis=1).str.strip() != ""
                contact_people = person_df[mask].copy()
                if not contact_people.empty:
                    contact_people["result_source"] = "person"
                    frames.append(contact_people)

        if not frames:
            return self._missing_file_result("office_contacts/person/asset", analysis)

        df = pd.concat(frames, ignore_index=True, sort=False).fillna("")
        df = self._ensure_department_name(df)
        df = self._filter_department(df, analysis)
        df = self._filter_keywords(df, self._keywords_from_analysis(analysis))
        df = self._sort_table("office_contacts", df).head(self._limit())

        return self._result(
            table_name="office_contacts",
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
    ) -> SqlQueryResult:
        final_warnings = list(warnings or [])

        if not rows and getattr(analysis, "department_code", None):
            final_warnings.append(
                f"{table_name} CSV에서 dept='{analysis.department_code}' 조건에 맞는 행이 없습니다."
            )

        return SqlQueryResult(
            table_name=table_name,
            rows=rows,
            columns=columns,
            conditions=getattr(analysis, "sql_conditions", {}),
            message=message,
            warnings=final_warnings,
        )

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
            table_name=self._table_name_from_analysis(analysis),
            rows=[],
            columns=[],
            conditions=getattr(analysis, "sql_conditions", {}),
            message="지원하지 않는 CSV 조회 유형입니다.",
            warnings=[
                f"sql_task_hint={getattr(analysis, 'sql_task_hint', None)}",
                f"sql_table_hint={getattr(analysis, 'sql_table_hint', None)}",
            ],
        )

    def _table_name_from_analysis(self, analysis: QueryAnalysis) -> str:
        table_hint = getattr(analysis, "sql_table_hint", None)

        if not table_hint:
            return "unknown"

        return self.TABLE_HINT_MAP.get(table_hint, table_hint)


def run_examples() -> None:
    from src.rag.query_analyzer import QuestionAnalyzer

    analyzer = QuestionAnalyzer()
    sql_tool = SQLTool()

    questions = [
        "AI시스템학과 교과목 알려줘",
        "AX학과 교수진 이메일 목록 보여줘",
        "KAIST 학과 사무실 전화번호 알려줘",
        "자료 다운로드 링크 알려줘",
        "AI컴퓨팅학과 입학 정보 알려줘",
        "AI컴퓨팅학과 학과설명회 일정 알려줘",
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
