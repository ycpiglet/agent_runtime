"""Manage collision-proof task identity and lifecycle metadata.

Human-readable task numbers such as TASK-AR-258 are useful labels, but they are
not safe as the only identity when several panes register tasks concurrently.
This script adds and enforces a time-sortable UUIDv7 `task_uid` (UUIDv4 legacy
keys remain valid) plus lifecycle timestamps. UUIDv7 is collision-free AND
time-ordered, so panes mint locally with no coordination (RFC 9562 sec 5.7);
the reservation ledger is therefore optional -- a vanity path for contiguous
`TASK-AR-NNN` only, not on the hot path (TASK-AR-536).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from task_id_contract import build_timestamp_task_id, is_canonical_task_id
except ImportError:  # imported as scripts.<name> (namespace package)
    from scripts.task_id_contract import build_timestamp_task_id, is_canonical_task_id


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = Path("agents/lead_engineer/tasks")
RESERVATIONS_PATH = Path("agents/project/work-items/TASK-ID-RESERVATIONS.json")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[47][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
TASK_DISPLAY_RE = re.compile(r"^(TASK-AR-)(\d+)$")
try:
    import status_alias
except ImportError:  # imported as scripts.<name> (namespace package)
    from scripts import status_alias
DONE_STATUSES = status_alias.DONE_STATUSES
STARTED_STATUSES = DONE_STATUSES | {"in_progress", "active", "review", "working"}
LIFECYCLE_FIELDS = ("display_id", "task_uid", "registered_at", "created_at", "started_at", "updated_at", "completed_at")
RESERVATION_SCHEMA = "agent-runtime-task-id-reservations/v1"
ACTIVE_RESERVATION_STATUSES = {"active"}
RESERVATION_LOCK_TIMEOUT_SECONDS = 5.0
RESERVATION_LOCK_POLL_SECONDS = 0.02


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


def _format_datetime(value: datetime) -> str:
    return value.astimezone().isoformat(timespec="seconds")


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


def _reservation_path(root: Path) -> Path:
    return root / RESERVATIONS_PATH


def _lock_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.lock")


def _acquire_lock(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    import time

    deadline = time.monotonic() + RESERVATION_LOCK_TIMEOUT_SECONDS
    while True:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii", errors="ignore"))
            return fd
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"could not acquire reservation lock: {path}")
            time.sleep(RESERVATION_LOCK_POLL_SECONDS)


def _release_lock(path: Path, fd: int) -> None:
    os.close(fd)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {"schema": RESERVATION_SCHEMA, "reservations": []}, ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"{path.as_posix()}: invalid-json:{exc}"
    if not isinstance(payload, dict):
        return {}, f"{path.as_posix()}: invalid-json-root"
    if not isinstance(payload.get("reservations"), list):
        payload["reservations"] = []
    return payload, ""


try:  # bare import when run as a script (scripts/ on sys.path); package path under pytest
    import atomic_io
except ModuleNotFoundError:  # pragma: no cover
    from scripts import atomic_io


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    # Shared durable primitive: temp -> fsync -> atomic rename (TASK crash-recovery).
    atomic_io.write_json_atomic(path, payload, sort_keys=True)


def _reservation_is_expired(reservation: dict[str, Any], now: datetime) -> bool:
    raw = str(reservation.get("expires_at") or "").strip()
    if not raw:
        return True
    try:
        return _parse_datetime(raw) <= now
    except ValueError:
        return True


def _reservation_is_live(reservation: dict[str, Any], now: datetime) -> bool:
    status = str(reservation.get("status") or "").strip().lower()
    return status in ACTIVE_RESERVATION_STATUSES and not _reservation_is_expired(reservation, now)


def _display_ids_from(start_display_id: str, count: int) -> list[str]:
    if count < 1:
        raise ValueError("count must be >= 1")
    match = TASK_DISPLAY_RE.match(start_display_id)
    if not match:
        if count != 1:
            raise ValueError("non-numeric display IDs cannot reserve a range")
        return [start_display_id]
    prefix, number = match.groups()
    width = len(number)
    start = int(number)
    return [f"{prefix}{value:0{width}d}" for value in range(start, start + count)]


def _display_id_number(display_id: str) -> int | None:
    match = TASK_DISPLAY_RE.match(display_id)
    return int(match.group(2)) if match else None


def _task_paths(root: Path) -> list[Path]:
    tasks_dir = root / TASKS_DIR
    if not tasks_dir.is_dir():
        return []
    return sorted(tasks_dir.glob("TASK-*.md"), key=lambda path: path.name.lower())


def _task_path_for_id(root: Path, task_id: str) -> Path:
    return root / TASKS_DIR / f"{task_id}.md"


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


def _task_display_id(meta: dict[str, Any], fallback: str) -> str:
    return str(meta.get("display_id") or meta.get("id") or fallback).strip()


def _task_display_ids(root: Path) -> dict[str, list[Path]]:
    displays: dict[str, list[Path]] = defaultdict(list)
    for path, meta in _load_tasks(root):
        display_id = _task_display_id(meta, path.stem)
        if display_id:
            displays[display_id].append(path)
    return displays


def _next_numeric_display_id(root: Path, payload: dict[str, Any]) -> str:
    highest = 0
    for display_id in _task_display_ids(root):
        number = _display_id_number(display_id)
        if number is not None:
            highest = max(highest, number)
    for reservation in payload.get("reservations", []):
        if not isinstance(reservation, dict):
            continue
        status = str(reservation.get("status") or "").strip().lower()
        if status in ACTIVE_RESERVATION_STATUSES:
            number = _display_id_number(str(reservation.get("display_id") or ""))
            if number is not None:
                highest = max(highest, number)
    return f"TASK-AR-{highest + 1:03d}"


def _active_reservation_for_display(payload: dict[str, Any], display_id: str, now: datetime) -> dict[str, Any] | None:
    for reservation in payload.get("reservations", []):
        if not isinstance(reservation, dict):
            continue
        if str(reservation.get("display_id") or "").strip() != display_id:
            continue
        if _reservation_is_live(reservation, now):
            return reservation
    return None


def _reservation_by_id(payload: dict[str, Any], reservation_id: str) -> dict[str, Any] | None:
    for reservation in payload.get("reservations", []):
        if isinstance(reservation, dict) and str(reservation.get("reservation_id") or "") == reservation_id:
            return reservation
    return None


def _reservation_findings(root: Path, now: datetime) -> list[str]:
    findings: list[str] = []
    path = _reservation_path(root)
    payload, error = _read_json(path)
    if error:
        return [f"{_rel(root, path)}: task-reservation:invalid-ledger"]
    if not path.exists():
        return []
    if str(payload.get("schema") or "") != RESERVATION_SCHEMA:
        findings.append(f"{_rel(root, path)}: task-reservation:invalid-schema")

    task_displays = _task_display_ids(root)
    active_by_display: dict[str, list[str]] = defaultdict(list)
    seen_reservation_ids: dict[str, int] = defaultdict(int)
    for index, reservation in enumerate(payload.get("reservations", []), start=1):
        if not isinstance(reservation, dict):
            findings.append(f"{_rel(root, path)}: task-reservation:invalid-row:{index}")
            continue
        reservation_id = str(reservation.get("reservation_id") or "").strip()
        display_id = str(reservation.get("display_id") or "").strip()
        status = str(reservation.get("status") or "").strip().lower()
        if reservation_id:
            seen_reservation_ids[reservation_id] += 1
        else:
            findings.append(f"{_rel(root, path)}: task-reservation:missing-reservation-id:{index}")
        if not display_id:
            findings.append(f"{_rel(root, path)}: task-reservation:missing-display-id:{reservation_id or index}")
        if not status:
            findings.append(f"{_rel(root, path)}: task-reservation:missing-status:{reservation_id or index}")
        if status in ACTIVE_RESERVATION_STATUSES:
            active_by_display[display_id].append(reservation_id or str(index))
            if _reservation_is_expired(reservation, now):
                findings.append(f"{_rel(root, path)}: task-reservation:stale-active:{display_id}:{reservation_id}")
            if display_id in task_displays:
                joined = ",".join(_rel(root, task_path) for task_path in task_displays[display_id])
                findings.append(f"{_rel(root, path)}: task-reservation:active-existing-task:{display_id}:{joined}")
        if status == "fulfilled":
            fulfilled_by = str(reservation.get("fulfilled_by") or "").strip()
            if not fulfilled_by:
                findings.append(f"{_rel(root, path)}: task-reservation:fulfilled-missing-task:{display_id}:{reservation_id}")
            elif display_id not in task_displays:
                findings.append(f"{_rel(root, path)}: task-reservation:fulfilled-task-not-found:{display_id}:{reservation_id}")

    for reservation_id, count in seen_reservation_ids.items():
        if count > 1:
            findings.append(f"{_rel(root, path)}: task-reservation:duplicate-reservation-id:{reservation_id}")
    for display_id, reservation_ids in active_by_display.items():
        if display_id and len(reservation_ids) > 1:
            findings.append(
                f"{_rel(root, path)}: task-reservation:duplicate-live-reservation:{display_id}:{','.join(reservation_ids)}"
            )
    return findings


def _uuid7() -> uuid.UUID:
    """Generate a UUIDv7 (RFC 9562 sec 5.7): 48-bit big-endian Unix-ms timestamp,
    4-bit version (7), 12-bit rand_a, 2-bit variant (0b10), 62-bit rand_b.

    Time-sortable AND collision-free with zero coordination, so concurrent panes
    mint task_uids locally without a central allocator (TASK-AR-536). The ms
    timestamp is an opaque key component, not a human-facing timestamp, so it uses
    the wall clock directly rather than scripts/now.py.
    """
    import time

    unix_ms = time.time_ns() // 1_000_000
    rand = int.from_bytes(os.urandom(10), "big")  # 80 random bits
    rand_a = (rand >> 64) & 0x0FFF  # 12 bits
    rand_b = rand & ((1 << 62) - 1)  # 62 bits
    value = (unix_ms & 0xFFFFFFFFFFFF) << 80
    value |= 0x7 << 76  # version 7
    value |= rand_a << 64
    value |= 0b10 << 62  # variant 10
    value |= rand_b
    return uuid.UUID(int=value)


def _valid_uuid(value: str) -> bool:
    return bool(UUID_RE.match(value.strip().lower()))


def check_root(root: Path) -> list[str]:
    root = root.resolve()
    findings: list[str] = []
    records = _load_tasks(root)
    ids: dict[str, list[Path]] = defaultdict(list)
    display_ids: dict[str, list[Path]] = defaultdict(list)
    uids: dict[str, list[Path]] = defaultdict(list)
    for path, meta in records:
        task_id = str(meta.get("id") or path.stem).strip()
        display_id = _task_display_id(meta, task_id)
        task_uid = str(meta.get("task_uid") or "").strip().lower()
        ids[task_id].append(path)
        if not is_canonical_task_id(task_id):
            findings.append(f"{_rel(root, path)}: task-identity:invalid-task-id:{task_id}")
        if display_id:
            display_ids[display_id].append(path)
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
    for display_id, paths in display_ids.items():
        if len(paths) > 1:
            joined = ",".join(_rel(root, path) for path in paths)
            findings.append(f"task-identity:duplicate-display-id:{display_id}:{joined}")
    for task_uid, paths in uids.items():
        if len(paths) > 1:
            joined = ",".join(_rel(root, path) for path in paths)
            findings.append(f"task-identity:duplicate-task-uid:{task_uid}:{joined}")
    findings.extend(_reservation_findings(root, datetime.now(timezone.utc).astimezone()))
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
        updates["task_uid"] = str(_uuid7())
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


def _create_task_file(
    *,
    root: Path,
    task_id: str,
    display_id: str,
    task_uid: uuid.UUID,
    now_text: str,
    args: argparse.Namespace,
) -> Path:
    task_path = _task_path_for_id(root, task_id)
    task_path.parent.mkdir(parents=True, exist_ok=True)
    title = args.title.strip()
    goal = args.goal.strip()
    lines = [
        "---",
        f"id: {task_id}",
        f"display_id: {display_id}",
        f"task_uid: {task_uid}",
        f"registered_at: {now_text}",
        f"created_at: {now_text}",
        f"updated_at: {now_text}",
        f"status: {args.status}",
        f"priority: {args.priority}",
        f"difficulty: {args.difficulty}",
        f"est_hours: {args.est_hours:g}",
        f"est_tokens: {args.est_tokens}",
    ]
    if args.initiative_id:
        lines.append(f"initiative_id: {args.initiative_id}")
    if args.reservation_id:
        lines.append(f"reservation_id: {args.reservation_id}")
    lines.extend(
        [
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
    )
    task_path.write_text("\n".join(lines), encoding="utf-8")
    return task_path


def _cmd_create_with_reservation(args: argparse.Namespace, root: Path, now_text: str) -> int:
    now = _parse_datetime(now_text)
    ledger_path = _reservation_path(root)
    lock_path = _lock_path(ledger_path)
    try:
        fd = _acquire_lock(lock_path)
    except TimeoutError as exc:
        print(f"task-identity-create: fail", file=sys.stderr)
        print(f"reason={exc}", file=sys.stderr)
        return 2
    try:
        payload, error = _read_json(ledger_path)
        if error:
            print(f"task-identity-create: fail", file=sys.stderr)
            print("reason=reservation-ledger-invalid", file=sys.stderr)
            return 1
        reservation = _reservation_by_id(payload, args.reservation_id)
        if not reservation:
            print("task-identity-create: fail", file=sys.stderr)
            print(f"reason=reservation-not-found:{args.reservation_id}", file=sys.stderr)
            return 1
        if not _reservation_is_live(reservation, now):
            print("task-identity-create: fail", file=sys.stderr)
            print(f"reason=reservation-not-active:{args.reservation_id}", file=sys.stderr)
            return 1
        display_id = str(reservation.get("display_id") or "").strip()
        task_id = args.task_id or display_id
        if args.task_id and args.task_id != display_id:
            print("task-identity-create: fail", file=sys.stderr)
            print(f"reason=reservation-display-mismatch:{display_id}:{args.task_id}", file=sys.stderr)
            return 1
        task_path = _task_path_for_id(root, task_id)
        if task_path.exists():
            print(f"task file already exists: {_rel(root, task_path)}", file=sys.stderr)
            return 1
        task_uid = _uuid7()
        created = _create_task_file(
            root=root,
            task_id=task_id,
            display_id=display_id,
            task_uid=task_uid,
            now_text=now_text,
            args=args,
        )
        reservation["status"] = "fulfilled"
        reservation["fulfilled_by"] = _rel(root, created)
        reservation["fulfilled_task_id"] = task_id
        reservation["fulfilled_task_uid"] = str(task_uid)
        reservation["fulfilled_at"] = now_text
        payload["updated_at"] = now_text
        _write_json_atomic(ledger_path, payload)
    finally:
        _release_lock(lock_path, fd)
    print("task-identity-create: pass")
    print(f"task_id={task_id}")
    print(f"display_id={display_id}")
    print(f"task_uid={task_uid}")
    print(f"reservation_id={args.reservation_id}")
    print(f"path={_rel(root, created)}")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    now_text = _now_text(args.now)
    if args.reservation_id:
        return _cmd_create_with_reservation(args, root, now_text)
    task_uid = _uuid7()
    timestamp = _timestamp_slug(now_text)
    task_id = args.task_id or build_timestamp_task_id(timestamp, task_uid.hex[:8])
    if not is_canonical_task_id(task_id):
        print("task-identity-create: fail", file=sys.stderr)
        print(f"reason=invalid-task-id:{task_id}", file=sys.stderr)
        return 1
    display_id = args.display_id or task_id
    task_path = root / TASKS_DIR / f"{task_id}.md"
    if task_path.exists():
        print(f"task file already exists: {_rel(root, task_path)}", file=sys.stderr)
        return 1
    ledger_path = _reservation_path(root)
    payload, error = _read_json(ledger_path)
    if error:
        print("task-identity-create: fail", file=sys.stderr)
        print("reason=reservation-ledger-invalid", file=sys.stderr)
        return 1
    active = _active_reservation_for_display(payload, display_id, _parse_datetime(now_text))
    if active:
        print("task-identity-create: fail", file=sys.stderr)
        print(f"reason=display-id-reserved:{display_id}:{active.get('reservation_id', '')}", file=sys.stderr)
        return 1
    task_path = _create_task_file(
        root=root,
        task_id=task_id,
        display_id=display_id,
        task_uid=task_uid,
        now_text=now_text,
        args=args,
    )
    print("task-identity-create: pass")
    print(f"task_id={task_id}")
    print(f"display_id={display_id}")
    print(f"task_uid={task_uid}")
    print(f"path={_rel(root, task_path)}")
    return 0


def cmd_reserve_id(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    now = _parse_datetime(_now_text(args.now))
    now_text = _format_datetime(now)
    ledger_path = _reservation_path(root)
    lock_path = _lock_path(ledger_path)
    try:
        fd = _acquire_lock(lock_path)
    except TimeoutError as exc:
        print("task-id-reserve: fail", file=sys.stderr)
        print(f"reason={exc}", file=sys.stderr)
        return 2
    try:
        payload, error = _read_json(ledger_path)
        if error:
            print("task-id-reserve: fail", file=sys.stderr)
            print("reason=reservation-ledger-invalid", file=sys.stderr)
            return 1
        start_display_id = args.display_id or _next_numeric_display_id(root, payload)
        try:
            display_ids = _display_ids_from(start_display_id, args.count)
        except ValueError as exc:
            print("task-id-reserve: fail", file=sys.stderr)
            print(f"reason={exc}", file=sys.stderr)
            return 1
        task_displays = _task_display_ids(root)
        for display_id in display_ids:
            if display_id in task_displays:
                print("task-id-reserve: fail", file=sys.stderr)
                print(f"reason=display-id-exists:{display_id}", file=sys.stderr)
                return 1
            active = _active_reservation_for_display(payload, display_id, now)
            if active:
                print("task-id-reserve: fail", file=sys.stderr)
                print(f"reason=reservation-active:{display_id}:{active.get('reservation_id', '')}", file=sys.stderr)
                return 1
        expires_at = now + timedelta(seconds=args.ttl_seconds)
        group_id = f"RES-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        created: list[dict[str, Any]] = []
        for index, display_id in enumerate(display_ids, start=1):
            reservation = {
                "schema": "agent-runtime-task-id-reservation/v1",
                "reservation_id": f"{group_id}-{index:02d}",
                "reservation_group_id": group_id,
                "kind": args.kind,
                "display_id": display_id,
                "status": "active",
                "owner_id": args.owner_id,
                "task_set_id": args.task_set_id or "",
                "initiative_id": args.initiative_id or "",
                "reserved_at": now_text,
                "expires_at": _format_datetime(expires_at),
                "ttl_seconds": args.ttl_seconds,
                "reason": args.reason or "",
            }
            payload.setdefault("reservations", []).append(reservation)
            created.append(reservation)
        payload["schema"] = RESERVATION_SCHEMA
        payload["updated_at"] = now_text
        _write_json_atomic(ledger_path, payload)
    finally:
        _release_lock(lock_path, fd)

    print("task-id-reserve: pass")
    print(f"reservation_group_id={group_id}")
    print(f"display_ids={','.join(display_ids)}")
    print(f"ledger={_rel(root, ledger_path)}")
    if args.json:
        print(json.dumps({"reservations": created, "ledger": _rel(root, ledger_path)}, ensure_ascii=False, indent=2))
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
    create.add_argument("--reservation-id")
    create.add_argument("--task-set-id", required=True)
    create.add_argument("--initiative-id", default="")
    create.add_argument("--title", required=True)
    create.add_argument("--goal", required=True)
    create.add_argument("--status", default="planned")
    create.add_argument("--priority", default="P0")
    create.add_argument("--difficulty", default="M")
    create.add_argument("--est-hours", type=float, default=1.0)
    create.add_argument("--est-tokens", type=int, default=100)
    create.add_argument("--now")
    create.set_defaults(func=cmd_create)

    reserve = sub.add_parser("reserve-id")
    reserve.add_argument("--kind", default="task", choices=["initiative", "taskset", "task", "unit", "routine", "spike"])
    reserve.add_argument("--display-id")
    reserve.add_argument("--count", type=int, default=1)
    reserve.add_argument("--owner-id", required=True)
    reserve.add_argument("--task-set-id", default="")
    reserve.add_argument("--initiative-id", default="")
    reserve.add_argument("--reason", default="")
    reserve.add_argument("--ttl-seconds", type=int, default=86400)
    reserve.add_argument("--now")
    reserve.add_argument("--json", action="store_true")
    reserve.set_defaults(func=cmd_reserve_id)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.root = args.root.resolve()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
