"""RAG 평가 러너 — 검색·파이프라인 품질을 수치로 측정한다.

검색(retrieval): Chroma top-5에 대해
  - dept_hit@5  : expected_dept가 검색 결과 학과에 포함되는 비율
  - kw_hit@5    : expected_keyword가 top-5 본문에 포함되는 비율
파이프라인(pipeline): answer_question 실제 호출
  - answered_rate : 실답변 비율 (폴백/정보없음/clarify 제외)
  - route 분포, 출처 학과 정확도

사용:
    python scripts/data/rag_eval.py                 # 검색만 (빠름/저비용)
    python scripts/data/rag_eval.py --mode both     # 검색 + 파이프라인(LLM 비용)
    python scripts/data/rag_eval.py --limit 10
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kaist_rag.config.settings")

EVAL = ROOT / "data" / "eval" / "rag_eval_set.jsonl"
RESULTS_DIR = ROOT / "data" / "eval"
CHROMA = str(ROOT / "data" / "vectorstore" / "chroma_db")


def load_eval(limit: int = 0) -> list[dict]:
    rows = [json.loads(l) for l in EVAL.open(encoding="utf-8") if l.strip()]
    return rows[:limit] if limit else rows


def code_to_name() -> dict[str, str]:
    import django; django.setup()
    from kaist_rag.rag.query_analyzer import DEPARTMENTS
    return {d.code: d.name for d in DEPARTMENTS}


def eval_retrieval(rows: list[dict]) -> dict:
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    vs = Chroma(collection_name="kaist_graduate_info", persist_directory=CHROMA,
                embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"))
    dept_hit = kw_hit = kw_total = 0
    per_col = Counter(); per_col_hit = Counter()
    for r in rows:
        q = r["question"]; exp = (r.get("expected_dept") or "").lower()
        docs = vs.similarity_search(q, k=5)
        depts = {str(d.metadata.get("dept", "")).lower() for d in docs}
        blob = " ".join(d.page_content for d in docs)
        d_ok = exp in depts if exp else False
        dept_hit += d_ok
        per_col[r["college"]] += 1; per_col_hit[r["college"]] += d_ok
        kws = r.get("expected_keywords") or []
        if kws:
            kw_total += 1
            kw_hit += any(k in blob for k in kws)
    n = len(rows)
    return {
        "n": n,
        "dept_hit@5": round(dept_hit / n * 100, 1),
        "kw_hit@5": round(kw_hit / kw_total * 100, 1) if kw_total else None,
        "per_college": {c: f"{per_col_hit[c]}/{per_col[c]}" for c in per_col},
    }


def classify(answer: str, route: str, fallback: str) -> str:
    a = answer.strip()
    if a == fallback.strip():
        return "fallback"
    if any(p in a for p in ("정보가 없", "자료가 없", "수집되지 않", "답변할 수 없")):
        return "insufficient"
    if route == "clarify":
        return "clarify"
    return "answered"


def eval_pipeline(rows: list[dict], names: dict[str, str]) -> dict:
    from kaist_rag.apps.chat.services import answer_question, FALLBACK_ANSWER
    cls = Counter(); routes = Counter(); src_correct = 0
    for r in rows:
        res = answer_question(r["question"])
        c = classify(res.answer, res.route, FALLBACK_ANSWER)
        cls[c] += 1; routes[res.route] += 1
        exp_name = names.get((r.get("expected_dept") or "").lower())
        if exp_name and any(s.get("department") == exp_name for s in res.sources):
            src_correct += 1
    n = len(rows)
    return {
        "n": n,
        "answered_rate": round(cls["answered"] / n * 100, 1),
        "classification": dict(cls),
        "route_dist": dict(routes),
        "source_dept_correct": round(src_correct / n * 100, 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["retrieval", "pipeline", "both"], default="retrieval")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = load_eval(args.limit)
    names = code_to_name()
    report = {"timestamp": time.strftime("%Y-%m-%d %H:%M"), "mode": args.mode, "count": len(rows)}

    print(f"=== RAG 평가 ({len(rows)}문항, mode={args.mode}) ===")
    if args.mode in ("retrieval", "both"):
        report["retrieval"] = eval_retrieval(rows)
        print("\n[검색 retrieval]")
        for k, v in report["retrieval"].items():
            print(f"  {k}: {v}")
    if args.mode in ("pipeline", "both"):
        report["pipeline"] = eval_pipeline(rows, names)
        print("\n[파이프라인 pipeline]")
        for k, v in report["pipeline"].items():
            print(f"  {k}: {v}")

    out = RESULTS_DIR / f"rag_eval_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
