#!/usr/bin/env python3
"""KEDB(Known Error Database) 검색 — 작업 시작 시 관련 COMPOUND 자동 surface.

TASK-150 (CYCLE-025). §17.1 strict gate 의 자동화 — "LLM 자발 검색에 의존 안 함".
작업 ID, 결함 시그니처, 키워드로 canonical per-record store를 먼저 검색하고,
과거 `compound_log.md`는 읽기 전용 fallback으로 검색해 같은 결함을 *시작 전에*
알려준다.

Usage:
  python scripts/kedb_search.py save_report VIEW
  python scripts/kedb_search.py 부산물 commit --critical
  python scripts/kedb_search.py --category process-omission
  python scripts/kedb_search.py --work-id TASK-AR-645 --signature "same-day closeout"
  python scripts/kedb_search.py VIEW --format json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
COMPOUND_LOG = ROOT / "agents" / "lead_engineer" / "compound_log.md"
CRITICAL_RECURRENCE = 3

try:
    import compound_record
except ImportError:  # imported as scripts.<name>
    from scripts import compound_record


def _field(entry: str, name: str) -> str:
    m = re.search(rf"^{re.escape(name)}:\s*(.+?)\s*$", entry, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _subsection(entry: str, header: str) -> str:
    m = re.search(rf"####\s+{re.escape(header)}(.*?)(?=^####\s|\Z)", entry, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_compounds(text: str) -> list[dict]:
    """compound_log.md 를 COMPOUND 항목 리스트로 파싱 (v1/v2 혼재 graceful)."""
    entries: list[dict] = []
    for chunk in re.split(r"(?=^### COMPOUND-\d+\s*$)", text, flags=re.MULTILINE):
        head = chunk.strip().split("\n", 1)[0] if chunk.strip() else ""
        m = re.match(r"### COMPOUND-(\d+)\s*$", head)
        if not m:
            continue
        number = int(m.group(1))
        rec_raw = _field(chunk, "재발 횟수")
        try:
            recurrence = int(rec_raw)
        except ValueError:
            recurrence = 0
        pattern = _subsection(chunk, "발견한 패턴") or _field(chunk, "발견한 패턴")
        entries.append({
            "id": f"COMPOUND-{number:03d}",
            "number": number,
            "category": _field(chunk, "카테고리"),
            "recurrence": recurrence,
            "status": _subsection(chunk, "상태") or _field(chunk, "상태"),
            "pattern": " ".join(pattern.split()),
            "text": chunk,
        })
    return entries


def search(entries: list[dict], keywords: list[str], category: str | None,
           critical_only: bool) -> list[dict]:
    results: list[dict] = []
    for e in entries:
        if category and e["category"] != category:
            continue
        if critical_only and e["recurrence"] < CRITICAL_RECURRENCE:
            continue
        if keywords:
            haystack = e["text"].lower()
            score = sum(haystack.count(k.lower()) for k in keywords)
            if score == 0:
                continue
        else:
            score = 0
        results.append({**e, "score": score})
    # 점수 desc, 동점은 재발 desc, 그다음 번호 desc (최신 우선)
    results.sort(key=lambda e: (-e["score"], -e["recurrence"], -e["number"]))
    return results


def search_knowledge(
    root: Path,
    *,
    keywords: list[str],
    work_ids: list[str],
    signatures: list[str],
    category: str | None,
    critical_only: bool,
    limit: int,
) -> list[dict]:
    """Search validated canonical records, then the legacy Markdown fallback."""
    limit = max(1, min(int(limit), compound_record.MAX_SEARCH_RESULTS))
    canonical = compound_record.search_records(
        root,
        work_ids=work_ids,
        defect_signatures=signatures,
        keywords=keywords,
        limit=limit,
    )
    rows: list[dict] = []
    for entry in canonical:
        recurrence = int(entry["recurrence_count"])
        if category and category != "canonical":
            continue
        if critical_only and recurrence < CRITICAL_RECURRENCE:
            continue
        rows.append(
            {
                "id": entry["id"],
                "number": 0,
                "category": "canonical",
                "recurrence": recurrence,
                "status": entry["status"],
                "pattern": entry["title"],
                "text": entry["title"],
                "score": entry["score"],
                "source": "record",
                "path": entry["path"],
                "work_ids": entry["work_ids"],
                "defect_signatures": entry["defect_signatures"],
            }
        )
    if len(rows) >= limit:
        return rows[:limit]

    legacy_path = root / "agents" / "lead_engineer" / "compound_log.md"
    if legacy_path.is_file():
        legacy_entries = parse_compounds(
            legacy_path.read_text(encoding="utf-8", errors="replace")
        )
        legacy_terms = [*keywords, *work_ids, *signatures]
        legacy_rows = search(
            legacy_entries, legacy_terms, category, critical_only
        )
        for entry in legacy_rows[: limit - len(rows)]:
            rows.append(
                {
                    **entry,
                    "source": "legacy",
                    "path": legacy_path.relative_to(root).as_posix(),
                    "work_ids": [],
                    "defect_signatures": [],
                }
            )
    return rows[:limit]


def render_table(rows: list[dict], keywords: list[str]) -> str:
    if not rows:
        kw = " ".join(keywords) if keywords else "(filter only)"
        return f"KEDB: no matching COMPOUND for '{kw}'. (신규 영역일 수 있음 — §17.1)\n"
    out = []
    out.append(f"{'ID':<14} {'CAT':<20} {'REC':>3} {'HIT':>3}  PATTERN")
    out.append("-" * 78)
    for e in rows:
        flag = " !" if e["recurrence"] >= CRITICAL_RECURRENCE else ""
        pat = e["pattern"][:60] + ("…" if len(e["pattern"]) > 60 else "")
        out.append(f"{e['id']:<14} {e['category'][:20]:<20} {e['recurrence']:>3}{flag:<2} {e['score']:>3}  {pat}")
    out.append("")
    out.append(f"{len(rows)} COMPOUND(s) matched. (! = critical, 재발>={CRITICAL_RECURRENCE})")
    return "\n".join(out) + "\n"


def render_json(rows: list[dict]) -> str:
    fields = (
        "id",
        "category",
        "recurrence",
        "score",
        "pattern",
        "status",
        "source",
        "path",
        "work_ids",
        "defect_signatures",
    )
    payload = [{key: entry.get(key) for key in fields} for entry in rows]
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KEDB(Known Error Database) 검색 — 작업 시작 시 관련 COMPOUND surface")
    parser.add_argument("keywords", nargs="*", help="검색 키워드 (도구/파일/패턴). 본문에 매칭")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--work-id", action="append", default=[], help="작업 ID 정확 매칭 (반복 가능)")
    parser.add_argument("--signature", action="append", default=[], help="결함 시그니처/문구 매칭 (반복 가능)")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--category", help="카테고리 정확 필터 (예: process-omission)")
    parser.add_argument("--critical", action="store_true", help=f"재발>={CRITICAL_RECURRENCE} 만")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    args = parser.parse_args(argv)

    try:
        rows = search_knowledge(
            args.root.resolve(),
            keywords=args.keywords,
            work_ids=args.work_id,
            signatures=args.signature,
            category=args.category,
            critical_only=args.critical,
            limit=args.limit,
        )
    except (OSError, compound_record.CompoundRecordError) as exc:
        print(f"KEDB: invalid compound store: {exc}", file=sys.stderr)
        return 1
    if args.format == "json":
        sys.stdout.write(render_json(rows))
    else:
        sys.stdout.write(render_table(rows, args.keywords))
    return 0


if __name__ == "__main__":
    sys.exit(main())
