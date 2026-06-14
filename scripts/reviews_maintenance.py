"""Reviews store maintenance: growth observability + safe date-shard planner (TASK-AR-534).

`reviews/` is an append-only logs/events store (meeting/seminar/council/review/
research/verification records). It only grows; it never transitions state. The
right structural treatment is date-sharding into `reviews/YYYY-MM/` + a compact
index -- BUT only once it is actually beneficial.

Today the whole store is a single month, so physically moving files would break
hundreds of references (manifests, task files, initiatives, cross-links) for zero
benefit. This tool therefore ships the *capability* and a *threshold trigger*,
and defers the move:

  --check   report counts/size/month distribution; non-zero only when a shard
            threshold is crossed (so sharding happens when it helps, not before).
  --plan    dry-run: print the YYYY-MM shard mapping + how many references would
            need rewriting. Read-only; never moves files.

The compact pointer index already exists as `reviews/INDEX.md`
(scripts/evidence_index_generator.py); this tool does not duplicate it.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REVIEWS_DIR = ROOT / "reviews"
# Shard when a single month exceeds this many files (sharding a single month into
# its own dir only helps once there are multiple months AND volume is high).
MONTH_FILE_THRESHOLD = 800
# Files that could reference a review path and would need rewriting if files move.
# Scan repo-wide (not a hand-picked few) so the reported migration cost is the
# true blast radius: manifests, BACKLOG, task files, initiatives, cross-links.
REFERENCE_GLOBS = ("*.md", "*.yml", "*.yaml")
REFERENCE_EXCLUDE = {".git", ".worktrees", "node_modules", ".venv"}
REVIEW_REF_RE = re.compile(r"reviews/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+\.md")
DATE_RE = re.compile(r"(20\d{2})-(\d{2})")


def _reference_files() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for pattern in REFERENCE_GLOBS:
        for path in ROOT.rglob(pattern):
            if any(part in REFERENCE_EXCLUDE for part in path.parts):
                continue
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            out.append(path)
    return out


def month_of(path: Path) -> str | None:
    m = DATE_RE.search(path.name)
    return f"{m.group(1)}-{m.group(2)}" if m else None


def scan(reviews_dir: Path = REVIEWS_DIR) -> dict:
    files = sorted(p for p in reviews_dir.glob("*.md") if p.is_file())
    by_month: dict[str, int] = defaultdict(int)
    undated = 0
    total_bytes = 0
    for path in files:
        total_bytes += path.stat().st_size
        month = month_of(path)
        if month:
            by_month[month] += 1
        else:
            undated += 1
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "by_month": dict(sorted(by_month.items())),
        "undated": undated,
        "months": len(by_month),
        "files": files,
    }


def shard_plan(reviews_dir: Path = REVIEWS_DIR) -> dict:
    info = scan(reviews_dir)
    mapping: list[tuple[str, str]] = []
    for path in info["files"]:
        month = month_of(path)
        if month:
            mapping.append((path.name, f"reviews/{month}/{path.name}"))
    ref_hits = 0
    for src in _reference_files():
        text = src.read_text(encoding="utf-8", errors="replace")
        ref_hits += len(REVIEW_REF_RE.findall(text))
    return {"mapping": mapping, "reference_hits": ref_hits, "months": info["months"]}


def threshold_findings(info: dict) -> list[str]:
    findings: list[str] = []
    for month, count in info["by_month"].items():
        if count > MONTH_FILE_THRESHOLD:
            findings.append(
                f"reviews-shard-due:{month}:{count}>{MONTH_FILE_THRESHOLD}: shard this month into reviews/{month}/ via --plan"
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Reviews store maintenance (TASK-AR-534)")
    parser.add_argument("--check", action="store_true", help="report growth; non-zero when a shard threshold is crossed")
    parser.add_argument("--plan", action="store_true", help="dry-run shard mapping + reference-rewrite count (no moves)")
    args = parser.parse_args()

    info = scan()
    if args.plan:
        plan = shard_plan()
        print(f"reviews-maintenance: plan: {len(plan['mapping'])} files across {plan['months']} month(s)")
        print(f"reviews-maintenance: references-to-rewrite-if-moved={plan['reference_hits']}")
        for name, dest in plan["mapping"][:10]:
            print(f"  {name} -> {dest}")
        if len(plan["mapping"]) > 10:
            print(f"  ... ({len(plan['mapping']) - 10} more)")
        print("reviews-maintenance: dry-run only; no files moved. Move is gated on the threshold + a reference-rewrite step.")
        return 0

    findings = threshold_findings(info)
    mb = info["total_bytes"] / (1024 * 1024)
    print(f"reviews-maintenance: file_count={info['file_count']} size={mb:.1f}MB months={info['months']} undated={info['undated']}")
    for month, count in info["by_month"].items():
        print(f"  {month}: {count}")
    if args.check:
        if findings:
            for finding in findings:
                print(f"reviews-maintenance: shard-due: {finding}")
            print(f"findings={len(findings)}")
            return 1
        print("reviews-maintenance: pass (no month over threshold; sharding not yet beneficial)")
        print("findings=0")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
