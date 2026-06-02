from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "processed" / "csv"

DEPT_LABELS = {
    "aic": "AI컴퓨팅학과",
    "ai_systems": "AI시스템학과",
    "ai_future": "AI미래학과",
    "ax": "AX학과",
}


def load_csv(filename: str) -> pd.DataFrame:
    path = RAW_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


admissions_df = load_csv("admissions.csv")
courses_df = load_csv("courses.csv")
people_df = load_csv("people.csv")
events_df = load_csv("events.csv")
assets_df = load_csv("assets.csv")
try:
    import chromadb
    _chroma_client = chromadb.PersistentClient(path=str(BASE_DIR / "vectorstore" / "chroma_db"))
    _rag_chunk_count = _chroma_client.get_collection("kaist_graduate_info").count()
except Exception:
    _rag_chunk_count = 0
rag_chunks_df = pd.DataFrame(range(_rag_chunk_count), columns=["id"])
rag_documents_df = pd.DataFrame()  # rag_documents 미제공
course_track_df = load_csv("course_track_map.csv")


def safe_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def get_data_summary():
    return {
        "admissions": len(admissions_df),
        "courses": len(courses_df),
        "people": len(people_df),
        "events": len(events_df),
        "rag_chunks": len(rag_chunks_df),
        "rag_documents": len(rag_documents_df),
    }


def get_department_heads():
    """학과당 대표 교수 1인 반환 (학과장 우선, 없으면 전임교수·중점교원·교수 순)."""
    if people_df.empty:
        return []
    DEPT_ORDER = ["AI컴퓨팅학과", "AI시스템학과", "AI미래학과", "AX학과"]
    ROLE_PRIORITY = ["학과장", "전임교수", "중점교원", "교수"]
    cols = ["dept_name", "name_ko", "role_normalized", "homepage"]
    available = [c for c in cols if c in people_df.columns]
    result = []
    for dept_name in DEPT_ORDER:
        dept_rows = people_df[people_df["dept_name"] == dept_name]
        if dept_rows.empty:
            continue
        selected = None
        for role in ROLE_PRIORITY:
            match = dept_rows[dept_rows["role_normalized"] == role]
            if not match.empty:
                selected = match.iloc[0]
                break
        if selected is None:
            selected = dept_rows.iloc[0]
        result.append(selected[available].fillna("").to_dict())
    return result


def get_departments():
    return [
        {
            "dept_name": "AI컴퓨팅학과",
            "summary": "AI 알고리즘, 머신러닝, 컴퓨팅 기반 기술, 데이터 처리 역량을 중심으로 한 학과입니다.",
            "source_url": "https://aic.kaist.ac.kr",
        },
        {
            "dept_name": "AI시스템학과",
            "summary": "지능형 소프트웨어, AI 플랫폼, 응용 시스템 설계를 중심으로 한 학과입니다.",
            "source_url": "https://ai-systems.kaist.ac.kr",
        },
        {
            "dept_name": "AI미래학과",
            "summary": "미래 사회 문제와 AI 융합 연구를 연결하는 학제간 융합 학과입니다.",
            "source_url": "https://fx.kaist.ac.kr",
        },
        {
            "dept_name": "AX학과",
            "summary": "AI 전환(AI Transformation)과 산업·사회 적용을 중심으로 한 융합 학과입니다.",
            "source_url": "https://ax.kaist.ac.kr",
        },
    ]


def _sample_by_dept(df: "pd.DataFrame", cols: list, limit: int) -> list:
    """학과별 균등 샘플링."""
    available_cols = [c for c in cols if c in df.columns]
    sub = df[available_cols].fillna("")
    if "dept" not in df.columns:
        return sub.head(limit).to_dict("records")
    depts = df["dept"].unique()
    per_dept = max(1, limit // len(depts))
    frames = [sub[df["dept"] == d].head(per_dept) for d in depts]
    import pandas as pd
    return pd.concat(frames).head(limit).to_dict("records")


def get_representative_people(limit=9):
    if people_df.empty:
        return []
    cols = ["dept_name", "name", "name_ko", "role", "research_area", "homepage", "source_url"]
    return _sample_by_dept(people_df, cols, limit)


def get_representative_courses(limit=12):
    if courses_df.empty:
        return []
    cols = ["dept_name", "course_level", "course_code", "course_name", "course_type", "credit", "source_url"]
    return _sample_by_dept(courses_df, cols, limit)


def search_chunks(query: str, limit=3):
    if rag_chunks_df.empty:
        return []
    q = query.lower()
    keywords = [word for word in q.replace("?", " ").replace(",", " ").split() if len(word) >= 2]
    if not keywords:
        return []
    scored = []
    for _, row in rag_chunks_df.iterrows():
        text = safe_text(row.get("chunk_text", row.get("text", "")))
        title = safe_text(row.get("title", row.get("document_title", "")))
        dept_name = safe_text(row.get("dept_name", row.get("dept", "")))
        source_url = safe_text(row.get("source_url", ""))
        combined = f"{title} {text}".lower()
        score = sum(1 for keyword in keywords if keyword in combined)
        if score > 0:
            scored.append({"score": score, "title": title, "dept_name": dept_name, "text": text, "source_url": source_url})
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:limit]


def _rows_to_sources(rows, fallback_title="Document", meta="Local CSV"):
    sources = []
    for _, row in rows.iterrows():
        title = safe_text(row.get("title", row.get("course_name", row.get("name", fallback_title))))
        dept_name = safe_text(row.get("dept_name", row.get("dept", "")))
        url = safe_text(row.get("source_url", row.get("homepage", "")))
        sources.append({"title": title or fallback_title, "meta": f"{dept_name} · {meta}" if dept_name else meta, "url": url})
    return sources[:3]


def get_admission_answer():
    if admissions_df.empty:
        return {"answer": "입학 데이터가 아직 준비되지 않았습니다. data/raw/admissions_clean.csv 파일을 추가하면 이 영역이 자동으로 채워집니다.", "sources": []}
    rows = admissions_df.fillna("").head(5)
    lines = []
    for _, row in rows.iterrows():
        dept_name = safe_text(row.get("dept_name", ""))
        title = safe_text(row.get("title", row.get("section_title", "Admission")))
        content = safe_text(row.get("content", row.get("text", "")))
        lines.append(f"- {dept_name}: {title} — {content[:160]}")
    return {"answer": "KAIST AI College 입학 정보에서 확인할 수 있는 주요 항목입니다.\n\n" + "\n".join(lines), "sources": _rows_to_sources(rows, "Admission", "Admission")}


def get_research_answer():
    chunks = search_chunks("연구 분야 research lab faculty", limit=3)
    if not chunks:
        return {"answer": "KAIST AI College는 Machine Learning, Deep Learning, NLP, Computer Vision, Robotics, Human-Centered AI, Trustworthy AI 등 다양한 AI 연구 분야를 탐색할 수 있도록 구성됩니다.", "sources": []}
    lines = [f"- {item['dept_name']}: {item['text'][:220]}" for item in chunks]
    sources = [{"title": item["title"] or "Research Information", "meta": f"{item['dept_name']} · RAG Chunk", "url": item["source_url"]} for item in chunks]
    return {"answer": "관련 문서에서 검색된 연구 분야 정보입니다.\n\n" + "\n".join(lines), "sources": sources}


def get_faculty_answer():
    if people_df.empty:
        return {"answer": "교수진 데이터가 아직 준비되지 않았습니다. data/raw/people_clean.csv 파일을 추가하면 이 영역이 자동으로 채워집니다.", "sources": []}
    rows = people_df.fillna("").head(6)
    lines = []
    for _, row in rows.iterrows():
        name = safe_text(row.get("name", ""))
        dept_name = safe_text(row.get("dept_name", ""))
        role = safe_text(row.get("role", ""))
        research_area = safe_text(row.get("research_area", ""))
        lines.append(f"- {name} / {dept_name}: {research_area or role}")
    return {"answer": "교수진 탐색은 연구 키워드와 학과 적합성을 중심으로 볼 수 있습니다.\n\n" + "\n".join(lines), "sources": _rows_to_sources(rows, "Faculty", "Faculty")}


def get_course_answer():
    if courses_df.empty:
        return {"answer": "교과목 데이터가 아직 준비되지 않았습니다. data/raw/courses_clean.csv 파일을 추가하면 이 영역이 자동으로 채워집니다.", "sources": []}
    rows = courses_df.fillna("").head(6)
    lines = []
    for _, row in rows.iterrows():
        dept_name = safe_text(row.get("dept_name", ""))
        code = safe_text(row.get("course_code", ""))
        name = safe_text(row.get("course_name", ""))
        level = safe_text(row.get("course_level", ""))
        lines.append(f"- {dept_name}: {code} {name} ({level})")
    return {"answer": "데모 데이터에서 확인되는 교과목 예시는 다음과 같습니다.\n\n" + "\n".join(lines), "sources": _rows_to_sources(rows, "Course", "Course")}


def get_event_answer():
    if events_df.empty:
        return {"answer": "행사 및 공지 데이터가 아직 준비되지 않았습니다. data/raw/events_clean.csv 파일을 추가하면 이 영역이 자동으로 채워집니다.", "sources": []}
    rows = events_df.fillna("").head(4)
    lines = []
    for _, row in rows.iterrows():
        dept_name = safe_text(row.get("dept_name", ""))
        title = safe_text(row.get("title", ""))
        date = safe_text(row.get("event_date", row.get("date", "")))
        lines.append(f"- {dept_name}: {title} ({date})")
    return {"answer": "설명회나 공지성 정보는 다음과 같이 확인할 수 있습니다.\n\n" + "\n".join(lines), "sources": _rows_to_sources(rows, "Event", "Event")}


def get_default_answer(question: str):
    chunks = search_chunks(question, limit=3)
    if chunks:
        lines = [f"- {item['dept_name']}: {item['text'][:220]}" for item in chunks]
        sources = [{"title": item["title"] or "Retrieved Document", "meta": f"{item['dept_name']} · RAG Chunk", "url": item["source_url"]} for item in chunks]
        return {"answer": "질문과 관련된 문서 조각을 검색했습니다.\n\n" + "\n".join(lines), "sources": sources}
    return {"answer": "입학, 연구 분야, 교수진, 교과목, 행사 정보를 중심으로 질문해보세요. 예: ‘입학 서류가 궁금해요’, ‘연구 분야 알려줘’, ‘교수진 정보 알려줘’. ", "sources": [{"title": "KAIST AI College Demo Knowledge Base", "meta": "Demo · Local CSV Data", "url": ""}]}


def get_demo_response(question: str):
    q = question.lower()
    if any(k in q for k in ["입학", "지원", "서류", "모집", "영어", "admission", "apply"]):
        return get_admission_answer()
    if any(k in q for k in ["연구", "분야", "랩", "연구실", "research", "lab"]):
        return get_research_answer()
    if any(k in q for k in ["교수", "교수진", "지도교수", "faculty", "professor"]):
        return get_faculty_answer()
    if any(k in q for k in ["교과", "수업", "과목", "course", "curriculum"]):
        return get_course_answer()
    if any(k in q for k in ["행사", "설명회", "이벤트", "공지", "event", "notice"]):
        return get_event_answer()
    return get_default_answer(question)
