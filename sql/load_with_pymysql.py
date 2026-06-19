from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pymysql
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = PROJECT_ROOT / "data" / "processed" / "csv"


def connect():
    load_dotenv(PROJECT_ROOT / ".env")

    return pymysql.connect(
        host=os.getenv("KAIST_MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("KAIST_MYSQL_PORT", "3306")),
        user=os.getenv("KAIST_MYSQL_USER", ""),
        password=os.getenv("KAIST_MYSQL_PASSWORD", ""),
        database=os.getenv("KAIST_MYSQL_DATABASE", "kaist_ai"),
        charset="utf8mb4",
        autocommit=False,
    )


def clean_value(value: Any) -> Any:
    if value is None:
        return None

    if pd.isna(value):
        return None

    text = str(value)

    if text.strip().lower() in {"", "nan", "none", "null"}:
        return None

    return text


def read_csv(filename: str) -> pd.DataFrame:
    return pd.read_csv(CSV_DIR / filename, dtype=str, encoding="utf-8-sig").where(pd.notna, None)


def rows_from_df(df: pd.DataFrame, columns: list[str]) -> list[tuple[Any, ...]]:
    return [
        tuple(clean_value(row.get(column)) for column in columns)
        for _, row in df.iterrows()
    ]


def insert_rows(
    cursor,
    table: str,
    columns: list[str],
    rows: list[tuple[Any, ...]],
    ignore: bool = True,
) -> None:
    if not rows:
        return

    verb = "INSERT IGNORE" if ignore else "INSERT"
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(f"`{column}`" for column in columns)
    sql = f"{verb} INTO `{table}` ({column_sql}) VALUES ({placeholders})"
    cursor.executemany(sql, rows)


def load_department(cursor, frames: dict[str, pd.DataFrame]) -> None:
    dept_rows = []

    for name in ["people", "courses", "admissions", "events", "assets", "course_track_map"]:
        df = frames[name]
        if "dept" not in df.columns or "dept_name" not in df.columns:
            continue

        for _, row in df[["dept", "dept_name"]].drop_duplicates().iterrows():
            dept = clean_value(row.get("dept"))
            dept_name = clean_value(row.get("dept_name"))

            if dept and dept_name:
                dept_rows.append((dept, dept_name))

    insert_rows(cursor, "department", ["dept", "dept_name"], sorted(set(dept_rows)))


def load_course_track(cursor, course_track_map: pd.DataFrame) -> None:
    track_rows = []

    for _, row in course_track_map.iterrows():
        dept = clean_value(row.get("dept"))
        track_name = clean_value(row.get("track_name"))

        if dept and track_name:
            track_rows.append((dept, track_name))

    insert_rows(cursor, "track", ["dept", "track_name"], sorted(set(track_rows)))

    cursor.execute("SELECT track_id, dept, track_name FROM track")
    tracks = {
        (dept, track_name): track_id
        for track_id, dept, track_name in cursor.fetchall()
    }

    cursor.execute("SELECT record_id FROM course")
    course_ids = {row[0] for row in cursor.fetchall()}

    course_track_rows = []

    for _, row in course_track_map.iterrows():
        course_id = clean_value(row.get("record_id"))
        dept = clean_value(row.get("dept"))
        track_name = clean_value(row.get("track_name"))
        track_id = tracks.get((dept, track_name))

        if course_id in course_ids and track_id:
            course_track_rows.append((course_id, track_id, clean_value(row.get("course_type"))))

    insert_rows(
        cursor,
        "course_track",
        ["course_id", "track_id", "course_type"],
        sorted(set(course_track_rows)),
    )


def load_rag(cursor, rag_documents: pd.DataFrame, rag_chunks: pd.DataFrame) -> None:
    doc_columns = [
        "doc_id", "dept", "source_type", "title", "source_url",
        "source_board", "crawled_at", "chunk_count",
    ]
    doc_rows = []

    for _, row in rag_documents.iterrows():
        chunk_count = clean_value(row.get("chunk_count"))
        doc_rows.append((
            clean_value(row.get("doc_id")),
            clean_value(row.get("dept")),
            clean_value(row.get("source_type")),
            clean_value(row.get("title")),
            clean_value(row.get("source_url")),
            clean_value(row.get("source_board")),
            clean_value(row.get("crawled_at")),
            int(float(chunk_count)) if chunk_count else None,
        ))

    insert_rows(cursor, "rag_document", doc_columns, doc_rows)

    chunk_columns = [
        "chunk_id", "doc_id", "section_path", "chunk_text",
        "source_record_id", "missing_fields", "metadata_json",
    ]
    chunk_rows = [
        (
            clean_value(row.get("chunk_id")),
            clean_value(row.get("doc_id")),
            clean_value(row.get("section_path")),
            clean_value(row.get("chunk_text")),
            clean_value(row.get("source_record_id")),
            clean_value(row.get("missing_fields")),
            clean_value(row.get("metadata_json")),
        )
        for _, row in rag_chunks.iterrows()
    ]
    insert_rows(cursor, "rag_chunk", chunk_columns, chunk_rows)


def main() -> int:
    frames = {
        "people": read_csv("people.csv"),
        "courses": read_csv("courses.csv"),
        "admissions": read_csv("admissions.csv"),
        "events": read_csv("events.csv"),
        "assets": read_csv("assets.csv"),
        "attachments": read_csv("attachments.csv"),
        "course_track_map": read_csv("course_track_map.csv"),
        "department_offices": read_csv("department_offices.csv"),
        "kaist_profile": read_csv("kaist_profile.csv"),
        "kaist_statistics": read_csv("kaist_statistics.csv"),
        "kaist_links": read_csv("kaist_links.csv"),
        "rag_documents": read_csv("rag_documents.csv"),
        "rag_chunks": read_csv("rag_chunks.csv"),
        "quality_report": read_csv("quality_report.csv"),
    }

    with connect() as connection:
        cursor = connection.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        load_department(cursor, frames)

        insert_rows(cursor, "person", [
            "record_id", "dept", "name", "name_ko", "name_en", "role",
            "role_normalized", "faculty_group", "email", "phone", "office",
            "research_area", "homepage", "image_url", "source_url", "crawled_at",
            "missing_fields",
        ], rows_from_df(frames["people"], [
            "record_id", "dept", "name", "name_ko", "name_en", "role",
            "role_normalized", "faculty_group", "email", "phone", "office",
            "research_area", "homepage", "image_url", "source_url", "crawled_at",
            "missing_fields",
        ]))

        insert_rows(cursor, "course", [
            "record_id", "dept", "course_level", "course_code", "course_name",
            "course_type", "credit", "course_description", "raw_values",
            "source_url", "crawled_at", "missing_fields",
        ], rows_from_df(frames["courses"], [
            "record_id", "dept", "course_level", "course_code", "course_name",
            "course_type", "credit", "course_description", "raw_values",
            "source_url", "crawled_at", "missing_fields",
        ]))

        insert_rows(cursor, "admission", [
            "record_id", "dept", "admission_type", "page_title", "section_title",
            "title", "content", "schedule_date", "source_url", "crawled_at",
            "source_sheet", "missing_fields",
        ], rows_from_df(frames["admissions"], [
            "record_id", "dept", "admission_type", "page_title", "section_title",
            "title", "content", "schedule_date", "source_url", "crawled_at",
            "source_sheet", "missing_fields",
        ]))

        insert_rows(cursor, "event", [
            "record_id", "dept", "event_type", "page_title", "title", "content",
            "event_date", "source_url", "crawled_at", "missing_fields",
        ], rows_from_df(frames["events"], [
            "record_id", "dept", "event_type", "page_title", "title", "content",
            "event_date", "source_url", "crawled_at", "missing_fields",
        ]))

        insert_rows(cursor, "asset", [
            "record_id", "dept", "category", "topic", "priority", "content_type",
            "asset_type", "text", "url", "filename", "source_url", "crawled_at",
            "missing_fields",
        ], rows_from_df(frames["assets"], [
            "record_id", "dept", "category", "topic", "priority", "content_type",
            "asset_type", "text", "url", "filename", "source_url", "crawled_at",
            "missing_fields",
        ]))

        attachment_rows = []
        for _, row in frames["attachments"].iterrows():
            size = clean_value(row.get("size"))
            attachment_rows.append((
                clean_value(row.get("dept")),
                clean_value(row.get("board")),
                clean_value(row.get("post_id")),
                clean_value(row.get("filename")),
                clean_value(row.get("url")),
                clean_value(row.get("ext")),
                int(float(size)) if size else None,
                clean_value(row.get("content_type")),
                clean_value(row.get("download_status")),
                clean_value(row.get("local_path")),
                clean_value(row.get("text_extraction_status")),
                clean_value(row.get("text_cache_path")),
                clean_value(row.get("text_preview")),
                clean_value(row.get("crawled_at")),
                clean_value(row.get("missing_fields")),
            ))

        insert_rows(cursor, "attachment", [
            "dept", "board", "post_id", "filename", "url", "ext", "size",
            "content_type", "download_status", "local_path", "text_extraction_status",
            "text_cache_path", "text_preview", "crawled_at", "missing_fields",
        ], attachment_rows)

        insert_rows(cursor, "department_office", [
            "office_id", "program_name", "phone", "website", "building_location",
            "source", "source_page", "missing_fields",
        ], rows_from_df(frames["department_offices"], [
            "office_id", "program_name", "phone", "website", "building_location",
            "source", "source_page", "missing_fields",
        ]))

        insert_rows(cursor, "kaist_profile", ["item", "content", "note", "source_url", "source"],
                    rows_from_df(frames["kaist_profile"], ["item", "content", "note", "source_url", "source"]))

        stat_rows = []
        for _, row in frames["kaist_statistics"].iterrows():
            value_number = clean_value(row.get("value_number"))
            stat_rows.append((
                clean_value(row.get("stat_group")),
                clean_value(row.get("level")),
                clean_value(row.get("value_raw")),
                int(float(str(value_number).replace(",", ""))) if value_number else None,
                clean_value(row.get("note")),
                clean_value(row.get("source")),
            ))
        insert_rows(cursor, "kaist_statistics", ["stat_group", "level", "value_raw", "value_number", "note", "source"], stat_rows)

        insert_rows(cursor, "kaist_link", ["link_name", "url", "note", "source"],
                    rows_from_df(frames["kaist_links"], ["link_name", "url", "note", "source"]))

        load_course_track(cursor, frames["course_track_map"])
        load_rag(cursor, frames["rag_documents"], frames["rag_chunks"])

        insert_rows(cursor, "quality_report", ["metric", "value", "note"],
                    rows_from_df(frames["quality_report"], ["metric", "value", "note"]))

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        connection.commit()

        cursor.execute("""
            SELECT 'department' AS table_name, COUNT(*) FROM department
            UNION ALL SELECT 'person', COUNT(*) FROM person
            UNION ALL SELECT 'course', COUNT(*) FROM course
            UNION ALL SELECT 'course_track', COUNT(*) FROM course_track
            UNION ALL SELECT 'admission', COUNT(*) FROM admission
            UNION ALL SELECT 'event', COUNT(*) FROM event
            UNION ALL SELECT 'asset', COUNT(*) FROM asset
            UNION ALL SELECT 'attachment', COUNT(*) FROM attachment
            UNION ALL SELECT 'department_office', COUNT(*) FROM department_office
            UNION ALL SELECT 'kaist_profile', COUNT(*) FROM kaist_profile
            UNION ALL SELECT 'kaist_statistics', COUNT(*) FROM kaist_statistics
            UNION ALL SELECT 'kaist_link', COUNT(*) FROM kaist_link
            UNION ALL SELECT 'rag_document', COUNT(*) FROM rag_document
            UNION ALL SELECT 'rag_chunk', COUNT(*) FROM rag_chunk
            UNION ALL SELECT 'quality_report', COUNT(*) FROM quality_report
        """)

        for table_name, count in cursor.fetchall():
            print(f"{table_name}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
