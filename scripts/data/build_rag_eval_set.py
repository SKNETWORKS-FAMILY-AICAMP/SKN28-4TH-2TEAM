"""3개 단과대학 RAG 평가셋 구축.

- 생명과학기술대 파일의 retrieval_eval(29문항)을 가져오고,
- AI대학·자연과학대 대표 질문을 추가하여
- data/eval/rag_eval_set.jsonl 로 저장한다.

각 항목: {question, expected_dept, expected_keywords[], college, qtype}
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "newdata" / "생명과학기술대학_RAG최종_20260618_v2.xlsx"
OUT = ROOT / "data" / "eval" / "rag_eval_set.jsonl"


def split_kw(v) -> list[str]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return []
    s = str(v)
    parts = [p.strip() for p in s.replace("|", ",").split(",")]
    return [p for p in parts if p and p.lower() != "nan"]


# 생명과학기술대 retrieval_eval → 평가 항목
def from_life() -> list[dict]:
    df = pd.read_excel(SRC, sheet_name="retrieval_eval")
    rows = []
    for _, r in df.iterrows():
        q = str(r.get("question", "")).strip()
        if not q or q == "nan":
            continue
        rows.append({
            "question": q,
            "expected_dept": str(r.get("expected_dept", "")).strip().lower() or None,
            "expected_keywords": split_kw(r.get("expected_keywords")),
            "college": "life",
            "qtype": str(r.get("expected_categories", "")).strip() or "unknown",
        })
    return rows


# AI대학·자연과학대 대표 질문 (수기 큐레이션)
CURATED = [
    # AI대학
    ("AI컴퓨팅학과 졸업 이수학점 알려줘", "aic", ["138", "학점"], "ai", "degree"),
    ("AI시스템학과 대학원 입학 안내", "ai_systems", ["입학", "모집"], "ai", "admission"),
    ("AX학과 교과목 알려줘", "ax", ["과목"], "ai", "course"),
    ("AI미래학과는 어떤 학과야", "fx", ["AI미래"], "ai", "overview"),
    ("AI컴퓨팅학과 교수진 알려줘", "aic", ["교수"], "ai", "faculty"),
    # 자연과학대
    ("물리학과 교수님 알려줘", "physics", ["교수"], "natsci", "faculty"),
    ("화학과 교과목 알려줘", "chem", ["과목"], "natsci", "course"),
    ("수리과학과 소개해줘", "mathsci", ["수리"], "natsci", "overview"),
    ("양자대학원 입학 정보 알려줘", "quantum", ["양자"], "natsci", "admission"),
    ("물리학과 졸업 요건 알려줘", "physics", ["학점"], "natsci", "degree"),
]


def main() -> None:
    rows = from_life()
    for q, dept, kws, col, qt in CURATED:
        rows.append({
            "question": q, "expected_dept": dept,
            "expected_keywords": kws, "college": col, "qtype": qt,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as w:
        for r in rows:
            w.write(json.dumps(r, ensure_ascii=False) + "\n")

    from collections import Counter
    print(f"[완료] {len(rows)}문항 → {OUT.relative_to(ROOT)}")
    print("  단과대 분포:", dict(Counter(r["college"] for r in rows)))
    print("  유형 분포:", dict(Counter(r["qtype"] for r in rows)))


if __name__ == "__main__":
    main()
