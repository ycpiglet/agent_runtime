"""Manage collision-proof task identity and lifecycle metadata.

Human-readable task numbers such as TASK-AR-258 are useful labels, but they are
not safe as the only identity when several panes register tasks concurrently.
This script adds and enforces a UUIDv4 `task_uid` plus lifecycle timestamps.
"""

from __future__ import annotations

import argparse
import re
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = Path("agents/lead_engineer/tasks")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
DONE_STATUSES = {"completed", "done", "released", "완료"}
STARTED_STATUSES = DONE_STATUSES | {"in_progress", "active", "review", "working"}
LIFECYCLE_FIELDS = ("display_id", "task_uid", "registered_at", "created_at", "started_at", "updated_at", "completed_at")


def _now_text(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _timestamp_slug(now_text: str) -> str:
    return _parse_datetime(now_text).strftime("%Y%m%d-%H%M%S")


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "task"


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _task_paths(root: Path) -> list[Path]:
    tasks_dir = root / TASKS_DIR
    if not tasks_dir.is_dir():
        return []
    return sorted(tasks_dir.glob("TASK-*.md"), key=lambda path: path.name.lower())


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
    return value.strip("\"'")


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], list[str], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, [], lines
    end = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = idx
            break
    if end is None:
        return {}, [], lines
    meta: dict[str, Any] = {}
    current_list: str | None = None
    header = lines[1:end]
    for raw in header:
        line = raw.rstrip()
        if not line.strip():
            current_list = None
            continue
        if line.startswith("  - ") and current_list:
            value = meta.setdefault(current_list, [])
            if isinstance(value, list):
                value.append(_parse_scalar(line[4:]))
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            meta[key] = []
            current_list = key
        else:
            meta[key] = _parse_scalar(value)
            current_list = None
    return meta, header, lines[end + 1 :]


def _format_scalar(value: str) -> str:
    return value


def _write_frontmatter_updates(path: Path, updates: dict[str, str]) -> bool:
    text = path.read_text(encoding="utf-8")
    meta, header, body = _parse_frontmatter(text)
    if not meta:
        return False
    changed = False
    pending = dict(updates)
    new_header: list[str] = []
    inserted_after_id = False
    for line in header:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key = match.group(1)
            if key in pending:
                new_line = f"{key}: {_format_scalar(pending.pop(key))}"
                new_header.append(new_line)
                changed = changed or new_line != line
            else:
                new_header.append(line)
            if key == "id" and not inserted_after_id:
                for field in LIFECYCLE_FIELDS:
                    if field in pending:
                        new_header.append(f"{field}: {_format_scalar(pending.pop(field))}")
                        changed = True
                inserted_after_id = True
            continue
        new_header.append(line)
    if pending:
        insert_at = 0
        new_header[insert_at:insert_at] = [f"{key}: {_format_scalar(value)}" for key, value in pending.items()]
        changed = True
    if not changed:
        return False
    path.write_text("\n".join(["---", *new_header, "---", *body]) + "\n", encoding="utf-8")
    return True


def _load_tasks(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in _task_paths(root):
        try:
            meta, _, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if meta:
            records.append((path, meta))
    return records


def _valid_uuid(value: str) -> bool:
    return bool(UUID_RE.match(value.strip().lower()))


def check_root(root: Path) -> list[str]:
    root = root.resolve()
    findings: list[str] = []
    records = _load_tasks(root)
    ids: dict[str, list[Path]] = defaultdict(list)
    uids: dict[str, list[Path]] = defaultdict(list)
    for path, meta in records:
        task_id = str(meta.get("id") or path.stem).strip()
        task_uid = str(meta.get("task_uid") or "").strip().lower()
        ids[task_id].append(path)
        if task_uid:
            uids[task_uid].append(path)
        else:
            findings.append(f"{_rel(root, path)}: task-identity:missing-task-uid:{task_id}")
        if task_uid and not _valid_uuid(task_uid):
            findings.append(f"{_rel(root, path)}: task-identity:invalid-task-uid:{task_id}:{task_uid}")
        registered_at = str(meta.get("registered_at") or meta.get("created_at") or meta.get("created") or "").strip()
        updated_at = str(meta.get("updated_at") or "").strip()
        status = str(meta.get("status") or "").strip().lower()
        if not registered_at:
            findings.append(f"{_rel(root, path)}: task-identity:missing-registered-at:{task_id}")
        if not updated_at:
            findings.append(f"{_rel(root, path)}: task-identity:missing-updated-at:{task_id}")
        if status in STARTED_STATUSES and not str(meta.get("started_at") or "").strip():
            findings.append(f"{_rel(root, path)}: task-identity:missing-started-at:{task_id}")
        if status in DONE_STATUSES and not str(meta.get("completed_at") or "").strip():
            findings.append(f"{_rel(root, path)}: task-identity:missing-completed-at:{task_id}")
    for task_id, paths in ids.items():
        if len(paths) > 1:
            joined = ",".join(_rel(root, path) for path in paths)
            findings.append(f"task-identity:duplicate-id:{task_id}:{joined}")
    for task_uid, paths in uids.items():
        if len(paths) > 1:
            joined = ",".join(_rel(root, path) for path in paths)
            findings.append(f"task-identity:duplicate-task-uid:{task_uid}:{joined}")
    return findings


def _backfill_updates(meta: dict[str, Any], now_text: str) -> dict[str, str]:
    updates: dict[str, str] = {}
    task_id = str(meta.get("id") or "").strip()
    status = str(meta.get("status") or "").strip().lower()
    registered_at = str(meta.get("registered_at") or meta.get("created_at") or meta.get("created") or now_text).strip()
    created_at = str(meta.get("created_at") or meta.get("created") or registered_at).strip()
    if not str(meta.get("display_id") or "").strip() and task_id:
        updates["display_id"] = task_id
    if not str(meta.get("task_uid") or "").strip():
        updates["task_uid"] = str(uuid.uuid4())
    if not str(meta.get("registered_at") or "").strip():
        updates["registered_at"] = registered_at
    if not str(meta.get("created_at") or "").strip():
        updates["created_at"] = created_at
    if status in STARTED_STATUSES and not str(meta.get("started_at") or "").strip():
        updates["started_at"] = registered_at
    if not str(meta.get("updated_at") or "").strip():
        updates["updated_at"] = now_text
    if status in DONE_STATUSES and not str(meta.get("completed_at") or "").strip():
        updates["completed_at"] = str(meta.get("updated_at") or now_text)
    return updates


def cmd_check(args: argparse.Namespace) -> int:
    findings = check_root(args.root)
    status = "fail" if findings else "pass"
    print(f"task-identity: {status}")
    print(f"root={args.root.resolve()}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


def cmd_backfill(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    now_text = _now_text(args.now)
    changed = 0
    for path, meta in _load_tasks(root):
        updates = _backfill_updates(meta, now_text)
        if updates and _write_frontmatter_updates(path, updates):
            changed += 1
    print("task-identity-backfill: pass")
    print(f"root={root}")
    print(f"changed={changed}")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    now_text = _now_text(args.now)
    task_uid = uuid.uuid4()
    timestamp = _timestamp_slug(now_text)
    task_id = args.task_id or f"TASK-AR-{timestamp}-{task_uid.hex[:8]}"
    task_path = root / TASKS_DIR / f"{task_id}.md"
    if task_path.exists():
        print(f"task file already exists: {_rel(root, task_path)}", file=sys.stderr)
        return 1
    task_path.parent.mkdir(parents=True, exist_ok=True)
    title = args.title.strip()
    goal = args.goal.strip()
    task_path.write_text(
        "\n".join(
            [
                "---",
                f"id: {task_id}",
                f"display_id: {args.display_id or task_id}",
                f"task_uid: {task_uid}",
                f"registered_at: {now_text}",
                f"created_at: {now_text}",
                f"updated_at: {now_text}",
                f"status: {args.status}",
                f"priority: {args.priority}",
                f"difficulty: {args.difficulty}",
                f"est_hours: {args.est_hours:g}",
                f"est_tokens: {args.est_tokens}",
                f"task_set_id: {args.task_set_id}",
                "tags:",
                "  - allocator-created",
                "---",
                "",
                f"# {title}",
                "",
                "## Goal",
                f"- {goal}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("task-identity-create: pass")
    print(f"task_id={task_id}")
    print(f"task_uid={task_uid}")
    print(f"path={_rel(root, task_path)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage collision-proof task identities")
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check")
    check.add_argument("--check", action="store_true")
    check.set_defaults(func=cmd_check)

    backfill = sub.add_parser("backfill")
    backfill.add_argument("--now")
    backfill.set_defaults(func=cmd_backfill)

    create = sub.add_parser("create")
    create.add_argument("--task-id")
    create.add_argument("--display-id")
    create.add_argument("--task-set-id", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--goal", required=True)
    create.add_argument("--status", default="planned")
    create.add_argument("--priority", default="P0")
    create.add_argument("--difficulty", default="M")
    create.add_argument("--est-hours", type=float, default=1.0)
    create.add_argument("--est-tokens", type=int, default=100)
    create.add_argument("--now")
    create.set_defaults(func=cmd_create)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.root = args.root.resolve()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
