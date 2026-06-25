"""newdata/*.xlsx 의 rag_chunks 시트를 vector_documents.jsonl 로 변환.

build_vectorstore.py 가 기대하는 형식: {"id", "text", "metadata"}.
- id   : chunk 고유 ID (파일 간 충돌 방지 위해 내용 해시 사용)
- text : chunk_text
- metadata : dept, dept_name, source_type/content_type, title, section,
             source_url, source_board, source_record_id, crawled_at
             + metadata_json 파싱 병합
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
NEWDATA = ROOT / "newdata"
OUT = ROOT / "data" / "processed" / "json" / "vector_documents.jsonl"


def na(v):
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    s = str(v).strip()
    return s if s and s.lower() != "nan" else None


def row_to_record(row: dict) -> dict | None:
    text = na(row.get("chunk_text"))
    if not text:
        return None

    meta: dict = {}
    # metadata_json 먼저 병합(있으면)
    mj = na(row.get("metadata_json"))
    if mj:
        try:
            parsed = json.loads(mj)
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    if na(v) is not None:
                        meta[k] = v
        except Exception:
            pass

    # 시트 컬럼으로 핵심 필드 채움(우선)
    direct = {
        "dept": na(row.get("dept")),
        "dept_name": na(row.get("dept_name")),
        "source_type": na(row.get("source_type")),
        "title": na(row.get("title")),
        "section": na(row.get("section_path")),
        "source_url": na(row.get("source_url")),
        "source_board": na(row.get("source_board")),
        "source_record_id": na(row.get("source_record_id")),
        "crawled_at": na(row.get("crawled_at")),
        "doc_id": na(row.get("doc_id")),
    }
    for k, v in direct.items():
        if v is not None:
            meta[k] = v

    # content_type 보강(없으면 source_type 사용) → doc_type alias·필터에 활용
    if "content_type" not in meta and meta.get("source_type"):
        meta["content_type"] = meta["source_type"]

    # 고유 ID: 내용+출처 해시(파일 간 chunk_id 중복 회피)
    basis = f"{meta.get('source_record_id','')}|{meta.get('doc_id','')}|{text}"
    doc_id = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:20]

    return {"id": doc_id, "text": text, "metadata": meta}


def main() -> None:
    files = sorted(NEWDATA.glob("*.xlsx"))
    if not files:
        raise SystemExit(f"newdata 에 xlsx 없음: {NEWDATA}")

    records: list[dict] = []
    seen: set[str] = set()
    per_file = {}

    for f in files:
        try:
            df = pd.read_excel(f, sheet_name="rag_chunks")
        except Exception as e:
            print(f"[건너뜀] {f.name}: rag_chunks 읽기 실패 ({e})")
            continue
        cnt = 0
        for _, r in df.iterrows():
            rec = row_to_record(r.to_dict())
            if rec is None:
                continue
            if rec["id"] in seen:  # 완전 중복 제거
                continue
            seen.add(rec["id"])
            records.append(rec)
            cnt += 1
        per_file[f.name] = cnt
        print(f"[수집] {f.name}: {cnt} chunks")

    # 기존 jsonl 백업 (.prev — legacy/.bak 보존 위해 별도 이름 사용)
    if OUT.exists():
        prev = OUT.with_suffix(".jsonl.prev")
        OUT.replace(prev)
        print(f"[백업] 기존 jsonl → {prev.name}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as w:
        for rec in records:
            w.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\n[완료] 총 {len(records)} chunks → {OUT.relative_to(ROOT)}")
    for name, c in per_file.items():
        print(f"   - {name}: {c}")


if __name__ == "__main__":
    main()
