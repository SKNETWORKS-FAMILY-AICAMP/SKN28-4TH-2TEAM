from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT_FROM_FILE = CURRENT_FILE.parents[2]

if str(PROJECT_ROOT_FROM_FILE) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FROM_FILE))

from src.rag.context_builder import SqlQueryResult
from src.rag.query_analyzer import QueryAnalysis


class CsvSqlRetriever:
    def __init__(
        self,
        sql_dir: Path | None = None,
    ) -> None:
        self.sql_dir = (
            sql_dir
            or PROJECT_ROOT_FROM_FILE
            / "data"
            / "raw_data"
            / "processed"
            / "sql"
        )
        self._tables: dict[str, pd.DataFrame] = {}

    def search(self, analysis: QueryAnalysis) -> SqlQueryResult:
        table_name = analysis.sql_table_hint or ""

        if table_name in {
            "kaist_profile",
            "kaist_statistics",
            "kaist_links",
        }:
            return self._search_kaist_basic_table(
                table_name=table_name,
                question=analysis.normalized_question,
                conditions=analysis.sql_conditions,
            )

        return SqlQueryResult(
            table_name=table_name or "unknown",
            rows=[],
            conditions=analysis.sql_conditions,
            message="CSV SQL retriever does not support this table.",
        )

    def _search_kaist_basic_table(
        self,
        table_name: str,
        question: str,
        conditions: dict[str, Any],
    ) -> SqlQueryResult:
        dataframe = self._load_table(table_name)
        rows = self._filter_rows(
            dataframe=dataframe,
            table_name=table_name,
            question=question,
        )

        return SqlQueryResult(
            table_name=table_name,
            rows=rows,
            columns=list(dataframe.columns),
            conditions=conditions,
        )

    def _load_table(self, table_name: str) -> pd.DataFrame:
        if table_name not in self._tables:
            table_path = self.sql_dir / f"{table_name}.csv"

            if not table_path.exists():
                raise FileNotFoundError(f"CSV table not found: {table_path}")

            self._tables[table_name] = pd.read_csv(
                table_path,
                dtype=str,
                keep_default_na=False,
                encoding="utf-8-sig",
            )

        return self._tables[table_name]

    def _filter_rows(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
        question: str,
    ) -> list[dict[str, Any]]:
        lowered_question = question.lower()

        if table_name == "kaist_profile":
            return self._filter_by_alias(
                dataframe=dataframe,
                question=lowered_question,
                key_column="item",
                aliases={
                    "학교명": ["학교명", "이름", "한국과학기술원"],
                    "영문약자": ["영문약자", "약자"],
                    "영문명": ["영문명", "영어 이름", "영어명", "korea advanced"],
                    "창립일": ["창립일", "설립일", "개교일", "언제 설립"],
                    "색상": ["색상", "상징색", "컬러"],
                    "주소": ["주소", "위치", "어디"],
                    "대표 번호": ["대표 번호", "대표번호", "전화", "전화번호"],
                    "대표 팩스번호": ["팩스", "팩스번호"],
                    "설립이념": ["설립이념", "이념", "역사", "설립 배경"],
                },
            )

        if table_name == "kaist_statistics":
            return self._filter_statistics(
                dataframe=dataframe,
                question=lowered_question,
            )

        if table_name == "kaist_links":
            return self._filter_by_alias(
                dataframe=dataframe,
                question=lowered_question,
                key_column="link_name",
                aliases={
                    "URL": ["공식 홈페이지", "홈페이지", "url", "웹사이트"],
                    "캠퍼스맵": ["캠퍼스맵", "캠퍼스 맵", "지도"],
                    "셔틀버스 실시간 위치 확인": ["셔틀버스", "셔틀", "버스"],
                    "도서관": ["도서관", "library"],
                    "문화행사": ["문화행사", "행사"],
                    "홍보동영상(2분, 2025)": ["홍보동영상", "동영상", "영상"],
                    "학사일정": ["학사일정", "일정", "캘린더"],
                },
            )

        return dataframe.to_dict("records")

    def _filter_by_alias(
        self,
        dataframe: pd.DataFrame,
        question: str,
        key_column: str,
        aliases: dict[str, list[str]],
    ) -> list[dict[str, Any]]:
        matched_keys = [
            key
            for key, keywords in aliases.items()
            if any(keyword.lower() in question for keyword in keywords)
        ]

        if not matched_keys:
            return dataframe.to_dict("records")

        rows = dataframe[dataframe[key_column].isin(matched_keys)]

        return rows.to_dict("records")

    def _filter_statistics(
        self,
        dataframe: pd.DataFrame,
        question: str,
    ) -> list[dict[str, Any]]:
        group_aliases = {
            "졸업생": ["졸업생", "졸업자", "동문"],
            "재학생": ["재학생", "학생 수", "학생수", "재학"],
            "교직원": ["교직원", "교수", "직원"],
        }
        level_aliases = {
            "전체": ["전체", "총", "모두"],
            "학사": ["학사", "학부"],
            "석사": ["석사"],
            "석박통합": ["석박통합", "석박사통합"],
            "박사": ["박사"],
            "교수": ["교수"],
            "직원": ["직원"],
        }

        groups = self._matched_alias_keys(question, group_aliases)
        levels = self._matched_alias_keys(question, level_aliases)

        rows = dataframe

        if groups:
            rows = rows[rows["stat_group"].isin(groups)]

        if levels:
            rows = rows[rows["level"].isin(levels)]

        if rows.empty and groups:
            rows = dataframe[dataframe["stat_group"].isin(groups)]

        return rows.to_dict("records")

    def _matched_alias_keys(
        self,
        question: str,
        aliases: dict[str, list[str]],
    ) -> list[str]:
        normalized_question = re.sub(r"\s+", "", question)

        return [
            key
            for key, keywords in aliases.items()
            if any(
                keyword.lower() in question
                or re.sub(r"\s+", "", keyword.lower()) in normalized_question
                for keyword in keywords
            )
        ]
