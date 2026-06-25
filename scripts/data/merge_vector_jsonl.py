"""신규 vector_documents.jsonl + 구 백업(.bak)을 내용 기준으로 병합.

교체 시 사라진 학과/청크(예: AX·AI시스템 일부, 전산학부 등 카탈로그)를
손실 없이 복원한다. 본문 텍스트 정규화 해시로 완전중복만 제거한다.

사용:
    python scripts/data/merge_vector_jsonl.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSONL = ROOT / "data" / "processed" / "json" / "vector_documents.jsonl"
# 교체 전 구 데이터(전체 KAIST 학과 얕은 카탈로그). 보존본을 우선 사용.
BAK = JSONL.parent / "legacy_catalog.jsonl"
if not BAK.exists():
    BAK = JSONL.with_suffix(".jsonl.bak")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main() -> None:
    new = load(JSONL)          # 신규(현재)
    old = load(BAK)            # 구(백업)
    print(f"신규(현재 jsonl): {len(new)}  /  구(.bak): {len(old)}")

    seen_text: set[str] = set()
    seen_id: set[str] = set()
    merged: list[dict] = []

    def add(rec: dict, source: str) -> bool:
        text = rec.get("text", "")
        h = norm(text)
        if not h or h in seen_text:
            return False
        seen_text.add(h)
        rid = str(rec.get("id") or "")
        if not rid or rid in seen_id:
            rid = hashlib.sha1((source + h).encode("utf-8")).hexdigest()[:20]
        seen_id.add(rid)
        rec["id"] = rid
        merged.append(rec)
        return True

    # 신규 우선(같은 내용이면 신규 형식 유지), 이후 구에서 신규에 없는 것만 추가
    n_new = sum(add(r, "new") for r in new)
    n_old = sum(add(r, "old") for r in old)

    with JSONL.open("w", encoding="utf-8") as w:
        for rec in merged:
            w.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"병합 결과: 신규 {n_new} + 구에서 복원 {n_old} = 총 {len(merged)}")
    print(f"저장: {JSONL.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
