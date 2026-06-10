from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_STATUSES = ("planned", "ready", "in_progress", "review", "blocked", "completed")
VALID_PRIORITIES = ("P0", "P1", "P2", "P3")
COMMAND_TYPES = ("task.create", "task.update", "task.reorder", "task.comment", "task.archive")
UNSAFE_PAYLOAD_KEYS = {"path", "source_path", "direct_file_path", "file_path", "filesystem_path"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    return slug or "task"


def _command_id(now: str) -> str:
    compact = re.sub(r"[^0-9]", "", now)[:14] or datetime.now().strftime("%Y%m%d%H%M%S")
    return f"COMMAND-{compact}-{secrets.token_hex(3)}"


def _message_id(now: str) -> str:
    compact = re.sub(r"[^0-9]", "", now)[:14] or datetime.now().strftime("%Y%m%d%H%M%S")
    return f"MSG-{compact}-{secrets.token_hex(3)}"


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() == "null":
        return None
    try:
        return int(value)
    except ValueError:
        return value.strip("\"'")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}, text

    meta: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw in lines[1:end_index]:
        line = raw.rstrip()
        if not line.strip():
            current_list_key = None
            continue
        if line.startswith("  - ") and current_list_key:
            existing = meta.setdefault(current_list_key, [])
            if isinstance(existing, list):
                existing.append(_parse_scalar(line[4:]))
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            meta[key] = []
            current_list_key = key
        else:
            meta[key] = _parse_scalar(value)
            current_list_key = None
    return meta, "\n".join(lines[end_index + 1 :]).strip()


def _format_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    return str(value)


def serialize_frontmatter(meta: dict[str, Any], body: str) -> str:
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {_format_scalar(item)}")
        else:
            lines.append(f"{key}: {_format_scalar(value)}")
    lines.extend(["---", "", body.strip(), ""])
    return "\n".join(lines)


def _tasks_dir(root: Path) -> Path:
    return root / "agents" / "lead_engineer" / "tasks"


def _task_path(root: Path, task_id: str) -> Path | None:
    for path in sorted(_tasks_dir(root).glob("TASK-*.md")):
        try:
            meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if meta.get("id") == task_id or path.stem == task_id:
            return path
    return None


def _validate_task_id(task_id: Any) -> str | None:
    if not isinstance(task_id, str) or not task_id.strip():
        return "missing task id"
    if not re.fullmatch(r"TASK-[A-Za-z0-9-]+", task_id.strip()):
        return f"invalid task id: {task_id!r}"
    return None


def _payload_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload must be an object"]
    unsafe = sorted(UNSAFE_PAYLOAD_KEYS.intersection(payload))
    if unsafe:
        return [f"direct file mutation is not allowed: {', '.join(unsafe)}"]
    errors: list[str] = []
    if "status" in payload and payload["status"] not in VALID_STATUSES:
        errors.append(f"invalid status: {payload['status']!r}")
    if "priority" in payload and payload["priority"] not in VALID_PRIORITIES:
        errors.append(f"invalid priority: {payload['priority']!r}")
    if "order" in payload:
        try:
            order = int(payload["order"])
        except (TypeError, ValueError):
            errors.append("order must be an integer")
        else:
            if order < 0:
                errors.append("order must be >= 0")
    return errors


def _goal_body(description: str) -> str:
    return "\n".join(["## Goal", "", description.strip() or "No description.", ""])


def _replace_goal_body(body: str, description: str) -> str:
    replacement = _goal_body(description).strip()
    match = re.search(r"^##\s+(Goal|목표)\s*$", body, flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        return replacement
    start = match.start()
    next_heading = re.search(r"^##\s+", body[match.end() :], flags=re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(body)
    return (body[:start] + replacement + body[end:]).strip()


def _write_command(root: Path, record: dict[str, Any]) -> Path:
    outbox = root / ".ui_outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    path = outbox / f"{record['id']}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _record(
    *,
    command_id: str,
    command_type: str,
    target: str | None,
    payload: dict[str, Any],
    now: str,
    status: str,
    errors: list[str] | None = None,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": command_id,
        "type": command_type,
        "target": target,
        "payload": payload,
        "created_by": "ui",
        "created_at": now,
        "status": status,
    }
    if errors:
        record["errors"] = errors
    if result:
        record["result"] = result
    return record


def _fail(root: Path, command_id: str, command_type: str, target: str | None, payload: Any, now: str, errors: list[str]) -> dict[str, Any]:
    safe_payload = payload if isinstance(payload, dict) else {"raw": payload}
    record = _record(
        command_id=command_id,
        command_type=command_type,
        target=target,
        payload=safe_payload,
        now=now,
        status="failed",
        errors=errors,
    )
    _write_command(root, record)
    return record


def _create_task(root: Path, payload: dict[str, Any], now: str) -> dict[str, Any]:
    task_id = str(payload.get("id") or f"TASK-UI-{re.sub(r'[^0-9]', '', now)[:14]}")
    errors = [_validate_task_id(task_id)] if _validate_task_id(task_id) else []
    errors.extend(_payload_errors(payload))
    title = str(payload.get("title") or "").strip()
    if not title:
        errors.append("title is required")
    if _task_path(root, task_id):
        errors.append(f"task already exists: {task_id}")
    if errors:
        return {"errors": errors}

    meta: dict[str, Any] = {
        "id": task_id,
        "title": title,
        "status": payload.get("status") or "planned",
        "owner": payload.get("owner") or "lead-engineer",
        "priority": payload.get("priority") or "P1",
        "order": int(payload.get("order", 0)),
        "tags": payload.get("tags") if isinstance(payload.get("tags"), list) else ["ui-console"],
        "audit_log": ["ui-console"],
        "created": now[:10],
    }
    description = str(payload.get("description") or title)
    path = _tasks_dir(root) / f"{task_id}-{_slug(title)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_frontmatter(meta, _goal_body(description)), encoding="utf-8")
    return {"changed": [_rel(root, path)]}


def _update_task(root: Path, target: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    if not target:
        return {"errors": ["missing task id"]}
    errors = [_validate_task_id(target)] if _validate_task_id(target) else []
    errors.extend(_payload_errors(payload))
    path = _task_path(root, target)
    if path is None:
        errors.append(f"task not found: {target}")
    if errors:
        return {"errors": errors}

    assert path is not None
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    for key in ("title", "status", "priority", "owner", "order", "archived"):
        if key in payload:
            meta[key] = int(payload[key]) if key == "order" else payload[key]
    if "description" in payload:
        body = _replace_goal_body(body, str(payload["description"]))
    path.write_text(serialize_frontmatter(meta, body), encoding="utf-8")
    return {"changed": [_rel(root, path)]}


def _reorder_task(root: Path, target: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    if "order" not in payload:
        return {"errors": ["order is required"]}
    return _update_task(root, target, payload)


def _archive_task(root: Path, target: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    archive_payload = dict(payload)
    archive_payload["archived"] = True
    archive_payload.setdefault("status", "completed")
    return _update_task(root, target, archive_payload)


def _comment_task(root: Path, target: str | None, payload: dict[str, Any], now: str) -> dict[str, Any]:
    task_id = target or str(payload.get("task_id") or "")
    errors = [_validate_task_id(task_id)] if _validate_task_id(task_id) else []
    errors.extend(_payload_errors(payload))
    if _task_path(root, task_id) is None:
        errors.append(f"task not found: {task_id}")
    comment = str(payload.get("comment") or payload.get("instruction") or "").strip()
    if not comment:
        errors.append("comment is required")
    if errors:
        return {"errors": errors}

    message_id = _message_id(now)
    to_role = str(payload.get("to") or "lead-engineer")
    path = root / "agents" / "messages" / "inbox" / f"{message_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        [
            "---",
            f"id: {message_id}",
            "from: ui",
            f"to: {to_role}",
            "type: comment",
            "status: queued",
            f"ts: {now}",
            "intent: task-comment",
            f"task_id: {task_id}",
            "---",
            "",
            comment,
            "",
        ]
    )
    path.write_text(body, encoding="utf-8")
    return {"changed": [_rel(root, path)]}


def submit_command(
    root: Path | str,
    command: dict[str, Any],
    *,
    now: str | None = None,
    command_id: str | None = None,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    created_at = now or _now_iso()
    cid = command_id or _command_id(created_at)
    command_type = str(command.get("type") or "")
    target = command.get("target")
    target_str = str(target) if target is not None else None
    payload = command.get("payload") if isinstance(command.get("payload"), dict) else {}

    if command_type not in COMMAND_TYPES:
        return _fail(root_path, cid, command_type or "unknown", target_str, payload, created_at, [f"unsupported command type: {command_type!r}"])

    base_errors = _payload_errors(payload)
    if base_errors:
        return _fail(root_path, cid, command_type, target_str, payload, created_at, base_errors)

    if command_type == "task.create":
        outcome = _create_task(root_path, payload, created_at)
    elif command_type == "task.update":
        outcome = _update_task(root_path, target_str, payload)
    elif command_type == "task.reorder":
        outcome = _reorder_task(root_path, target_str, payload)
    elif command_type == "task.archive":
        outcome = _archive_task(root_path, target_str, payload)
    else:
        outcome = _comment_task(root_path, target_str, payload, created_at)

    if "errors" in outcome:
        return _fail(root_path, cid, command_type, target_str, payload, created_at, list(outcome["errors"]))
    record = _record(
        command_id=cid,
        command_type=command_type,
        target=target_str,
        payload=payload,
        now=created_at,
        status="accepted",
        result=outcome,
    )
    _write_command(root_path, record)
    return record


def list_commands(root: Path | str) -> list[dict[str, Any]]:
    outbox = Path(root).resolve() / ".ui_outbox"
    if not outbox.is_dir():
        return []
    commands: list[dict[str, Any]] = []
    for path in sorted(outbox.glob("COMMAND-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"id": path.stem, "status": "failed", "errors": ["command file is malformed"]}
        if isinstance(payload, dict):
            payload.setdefault("id", path.stem)
            payload["source_path"] = _rel(Path(root).resolve(), path)
            payload["source_kind"] = "ui_command"
            commands.append(payload)
    return commands
