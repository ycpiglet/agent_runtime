"""Manifest-first read surface + derived-index readiness (TASK-AR-537).

The store keeps markdown/JSON as the source of truth, but agents should read the
GENERATED manifests (one file) instead of globbing hundreds of records. This tool
names that canonical read surface, checks it is present + fresh, and reports when
the store has grown enough to warrant a derived SQLite/FTS5 index.

  --check   verify the read-surface manifests exist; report store size + whether
            a derived full-text index is recommended yet. Non-zero only if a
            canonical manifest is missing (a real consistency break).

Design (deferred until needed): a derived SQLite/FTS5 index, rebuilt from the
markdown via mtime+hash, switched on only past ~10k files / when cross-corpus
full-text query is needed. The markdown/JSON stays canonical; the index is a
disposable cache. See agents/project/READ-SURFACE-CONTRACT.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

# The canonical, generated read surface. Agents read THESE, not raw globs.
READ_SURFACE = [
    "BACKLOG-BOARD.md",
    "ARCHIVE-INDEX.md",
    "agents/project/work-items/WORK-ITEM-CLASSIFICATION.json",
    "agents/project/work-items/TASKSET-DEFINITIONS.json",
    "agents/project/work-items/HOST-FEEDBACK-QUEUE.json",
    "reviews/INDEX.md",
]
# Counted corpora that grow over time.
CORPORA = [
    "agents/lead_engineer/tasks",
    "reviews",
    "agents/runtime/task_claims",
]
# Switch a derived full-text index on past this many markdown files.
FTS_FILE_THRESHOLD = 10_000


def scan(root: Path = ROOT) -> dict:
    present = {rel: (root / rel).exists() for rel in READ_SURFACE}
    missing = [rel for rel, ok in present.items() if not ok]
    md_count = 0
    for rel in CORPORA:
        base = root / rel
        if base.exists():
            md_count += sum(1 for _ in base.rglob("*.md"))
    return {
        "present": present,
        "missing": missing,
        "md_count": md_count,
        "fts_recommended": md_count >= FTS_FILE_THRESHOLD,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Manifest-first read surface check (TASK-AR-537)")
    parser.add_argument("--check", action="store_true", help="verify read-surface manifests + report size; non-zero if a manifest is missing")
    args = parser.parse_args()

    info = scan()
    print(f"work-index: read-surface manifests present={sum(info['present'].values())}/{len(READ_SURFACE)}")
    print(f"work-index: corpus markdown files={info['md_count']} (FTS threshold {FTS_FILE_THRESHOLD})")
    if info["fts_recommended"]:
        print("work-index: derived SQLite/FTS5 index RECOMMENDED (corpus past threshold) -- see READ-SURFACE-CONTRACT.md")
    else:
        print("work-index: derived full-text index not needed yet; manifest-first reads suffice")
    if args.check:
        if info["missing"]:
            for rel in info["missing"]:
                print(f"work-index: fail: missing-read-surface:{rel}")
            print(f"findings={len(info['missing'])}")
            return 1
        print("work-index: pass")
        print("findings=0")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
