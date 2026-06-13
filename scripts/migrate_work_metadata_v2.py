"""Migrate legacy task frontmatter to the v0.2.0 Work Item metadata catalog.

Open (non-completed) task records authored before AR-515 lack the v2.0 envelope
fields (schema_version, work_id, work_uid, kind, parent_id, origin_*). Until they
carry `schema_version: agent-runtime-work-item/v1` the work_schema gate skips them.
This migration derives the required v2.0 catalog fields from the existing
frontmatter so the records become first-class, gate-validated v2.0 work items
without changing their substance.

Idempotent: re-running makes no change once a record already carries
schema_version. Only files passed on the command line (or all open task files via
--all-open) are touched; completed/archived records are left as historical.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

WORK_ITEM_SCHEMA = "agent-runtime-work-item/v1"
TASKS_DIR = Path("agents/lead_engineer/tasks")
CLOSED = {"completed", "done", "closed"}


def _field(text: str, key: str) -> str:
    m = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    return m.group(1).strip().strip('"').strip("'") if m else ""


def _has(text: str, key: str) -> bool:
    return re.search(rf"(?m)^{re.escape(key)}:", text) is not None


def migrate_text(text: str) -> tuple[str, bool]:
    if _has(text, "schema_version"):
        return text, False  # already v2.0 — idempotent
    status = _field(text, "status").lower()
    work_id = _field(text, "id") or _field(text, "display_id")
    work_uid = _field(text, "task_uid")
    parent_id = _field(text, "task_set_id")
    created_at = _field(text, "created_at") or _field(text, "registered_at")
    # Derived provenance: these legacy tasks were registered from planning records.
    derived = {
        "schema_version": WORK_ITEM_SCHEMA,
        "work_id": work_id,
        "work_uid": work_uid,
        "kind": "task",
        "parent_id": parent_id,
        "origin_type": "planning_proposal",
        "origin_ref": parent_id,  # the taskset registration is the originating record
        "created_by": "planner",
    }
    # Insert the new fields right after the opening frontmatter `---` line,
    # skipping any key that already exists.
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text, False
    insert = [f"{k}: {v}" for k, v in derived.items() if not _has(text, k)]
    out = [lines[0], *insert, *lines[1:]]
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--all-open", action="store_true", help="migrate every non-completed task file")
    parser.add_argument("--check", action="store_true", help="report which files would change; exit 1 if any")
    args = parser.parse_args()

    targets: list[Path] = list(args.paths)
    if args.all_open:
        for p in sorted(TASKS_DIR.glob("TASK-AR-*.md")):
            if _field(p.read_text(encoding="utf-8"), "status").lower() not in CLOSED:
                targets.append(p)

    changed = 0
    for p in targets:
        text = p.read_text(encoding="utf-8")
        new, did = migrate_text(text)
        if did:
            changed += 1
            if not args.check:
                p.write_text(new, encoding="utf-8")
            print(("would-migrate" if args.check else "migrated"), p.as_posix())
    print(f"changed={changed}")
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
