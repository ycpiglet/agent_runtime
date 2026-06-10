from __future__ import annotations

import json
import re
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_STATUSES = (
    "assigned",
    "blocked",
    "claimed",
    "completed",
    "defer",
    "deferred",
    "done",
    "hold",
    "in_progress",
    "pending",
    "planned",
    "ready",
    "ready_for_governance_review",
    "review",
    "waiting_review",
    "working",
)
VALID_PRIORITIES = ("P0", "P1", "P2", "P3")
TASK_COMMAND_TYPES = ("task.create", "task.update", "task.reorder", "task.comment", "task.archive")
RUNTIME_MESSAGE_COMMAND_TYPES = (
    "runtime.call_agent",
    "runtime.assign_task",
    "runtime.request_review",
    "runtime.request_meeting",
)
RUNTIME_LIFECYCLE_COMMAND_TYPES = (
    "runtime.goal.start",
    "runtime.goal.pause",
    "runtime.goal.resume",
    "runtime.goal.stop",
)
RUNTIME_COMMAND_TYPES = RUNTIME_MESSAGE_COMMAND_TYPES + RUNTIME_LIFECYCLE_COMMAND_TYPES
PLANNING_COMMAND_TYPES = ("planning.scan",)
TASK_BOARD_SYNC_COMMANDS = {"task.create", "task.update", "task.reorder", "task.archive"}
COMMAND_TYPES = TASK_COMMAND_TYPES + RUNTIME_COMMAND_TYPES + PLANNING_COMMAND_TYPES
UNSAFE_PAYLOAD_KEYS = {"path", "source_path", "direct_file_path", "file_path", "filesystem_path"}
HIGH_RISK_TERMS = (
    ("delete", "deletion"),
    ("remove", "deletion"),
    ("commit", "git commit"),
    ("push", "git push"),
    ("pull request", "pull request"),
    ("open a pr", "pull request"),
    ("create pr", "pull request"),
    ("install", "dependency install"),
    ("dependency", "dependency install"),
    ("package", "dependency install"),
    ("long-running", "long-running goal"),
    ("long running", "long-running goal"),
    ("irreversible", "irreversible external effect"),
    ("external", "irreversible external effect"),
)


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


def _mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds")
    except OSError:
        return None


def _sync_backlog_board(root: Path) -> bool:
    script_path = root / "scripts" / "backlog_board.py"
    if not script_path.exists():
        print(f"backlog sync skipped: missing {script_path}", file=sys.stderr)
        return False

    result = subprocess.run(
        [sys.executable, str(script_path), "--write"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        if result.stdout:
            print(result.stdout, file=sys.stderr, end="")
        return False
    return True


def _requires_backlog_board_sync(command_type: str, payload: dict[str, Any]) -> bool:
    return command_type in TASK_BOARD_SYNC_COMMANDS


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


def _runtime_text(payload: dict[str, Any]) -> str:
    values = [
        payload.get("instruction"),
        payload.get("prompt"),
        payload.get("comment"),
        payload.get("reason"),
        payload.get("title"),
    ]
    return " ".join(str(value) for value in values if value is not None)


def _approval_reasons(command_type: str, payload: dict[str, Any]) -> list[str]:
    text = _runtime_text(payload).lower()
    reasons: list[str] = []
    for token, reason in HIGH_RISK_TERMS:
        if token in text and reason not in reasons:
            reasons.append(reason)
    if command_type == "runtime.goal.start" and payload.get("long_running") is True:
        if "long-running goal" not in reasons:
            reasons.append("long-running goal")
    if payload.get("irreversible") is True or payload.get("external_effect") is True:
        if "irreversible external effect" not in reasons:
            reasons.append("irreversible external effect")
    return reasons


def _safety_metadata(command_type: str, target: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    reasons = _approval_reasons(command_type, payload)
    goal_id = payload.get("goal_id")
    if goal_id is None and command_type in RUNTIME_LIFECYCLE_COMMAND_TYPES:
        goal_id = target
    return {
        "actor": str(payload.get("actor") or "ui"),
        "reason": str(payload.get("reason") or ""),
        "task_id": payload.get("task_id"),
        "goal_id": goal_id,
        "approval_required": bool(reasons),
        "approval_reasons": reasons,
        "risk_level": "high" if reasons else "low",
    }


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
    safety = _safety_metadata(command_type, target, payload)
    record: dict[str, Any] = {
        "id": command_id,
        "type": command_type,
        "target": target,
        "payload": payload,
        "created_by": "ui",
        "created_at": now,
        "status": status,
        "actor": safety["actor"],
        "reason": safety["reason"],
        "task_id": safety["task_id"],
        "goal_id": safety["goal_id"],
        "approval_required": safety["approval_required"],
        "risk_level": safety["risk_level"],
    }
    if safety["approval_reasons"]:
        record["approval_reasons"] = safety["approval_reasons"]
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


def _runtime_instruction(payload: dict[str, Any]) -> str:
    instruction = str(payload.get("instruction") or payload.get("prompt") or payload.get("comment") or "").strip()
    if instruction:
        return instruction
    task_id = str(payload.get("task_id") or "").strip()
    if task_id:
        return f"Run task {task_id}."
    return ""


def _queue_runtime_message(root: Path, command_type: str, target: str | None, payload: dict[str, Any], now: str) -> dict[str, Any]:
    errors = _payload_errors(payload)
    to_role = str(target or payload.get("to") or payload.get("agent") or "").strip()
    if not to_role:
        errors.append("target agent is required")
    elif not re.fullmatch(r"[A-Za-z0-9_-]+", to_role):
        errors.append(f"invalid target agent: {to_role!r}")
    instruction = _runtime_instruction(payload)
    if not instruction:
        errors.append("instruction is required")
    if errors:
        return {"errors": errors}

    message_id = _message_id(now)
    path = root / "agents" / "messages" / "inbox" / f"{message_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    task_id = payload.get("task_id")
    goal_id = payload.get("goal_id")
    body = "\n".join(
        [
            "---",
            f"id: {message_id}",
            "from: ui",
            f"to: {to_role}",
            "type: runtime-command",
            "status: queued",
            f"ts: {now}",
            f"intent: {command_type}",
            f"task_id: {task_id if task_id else 'none'}",
            f"goal_id: {goal_id if goal_id else 'none'}",
            "---",
            "",
            instruction,
            "",
        ]
    )
    path.write_text(body, encoding="utf-8")
    return {
        "status": "queued",
        "result": {
            "changed": [_rel(root, path)],
            "message_id": message_id,
            "runtime_support": "message_queue",
        },
    }


def _runtime_command(root: Path, command_type: str, target: str | None, payload: dict[str, Any], now: str) -> dict[str, Any]:
    safety = _safety_metadata(command_type, target, payload)
    if safety["approval_required"]:
        return {
            "status": "approval_required",
            "result": {
                "runtime_support": "approval_queue",
                "next": "owner approval is required before any runtime execution",
            },
        }
    if command_type in RUNTIME_LIFECYCLE_COMMAND_TYPES:
        return {
            "status": "pending_runtime_support",
            "result": {
                "runtime_support": "unsupported",
                "next": "runtime executor must consume this command before UI can claim execution",
            },
        }
    return _queue_runtime_message(root, command_type, target, payload, now)


def _planning_scan_command(root: Path, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    errors = _payload_errors(payload)
    trigger = str(payload.get("trigger") or "ui")
    if trigger != "ui":
        errors.append("UI planning scan requests must use trigger='ui'")
    mode = str(payload.get("mode") or "B")
    if mode != "B":
        errors.append("UI planning scan requests are proposal-only B-mode")
    if payload.get("apply") is True or payload.get("mutate") is True:
        errors.append("UI planning scan requests cannot apply canonical mutations")
    if errors:
        return {"errors": errors}

    request = {
        "id": command_id.replace("COMMAND-", "PLANREQ-"),
        "type": "planning.scan",
        "trigger": "ui",
        "mode": "B",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "ui"),
        "reason": str(payload.get("reason") or ""),
        "gate": "scripts/planning_loop.py gate --trigger ui --action scan",
        "canonical_mutation_allowed": False,
    }
    path = root / "agents" / "planning" / "requests" / f"{request['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "queued",
        "result": {
            "changed": [_rel(root, path)],
            "planning_support": "proposal_only_scan_request",
            "next": "runtime planner must run the planning gate before scan/proposal generation",
        },
    }


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
    elif command_type == "task.comment":
        outcome = _comment_task(root_path, target_str, payload, created_at)
    elif command_type == "planning.scan":
        outcome = _planning_scan_command(root_path, payload, created_at, cid)
    else:
        outcome = _runtime_command(root_path, command_type, target_str, payload, created_at)

    if "errors" in outcome:
        return _fail(root_path, cid, command_type, target_str, payload, created_at, list(outcome["errors"]))

    backlog_board_updated = False
    if _requires_backlog_board_sync(command_type, payload):
        backlog_board_updated = _sync_backlog_board(root_path)
        if not backlog_board_updated:
            return _fail(
                root_path,
                cid,
                command_type,
                target_str,
                payload,
                created_at,
                ["BACKLOG-BOARD.md sync failed after task mutation; run python scripts/backlog_board.py --write"],
            )

    if command_type in TASK_BOARD_SYNC_COMMANDS and "result" not in outcome:
        outcome = dict(outcome)
        outcome["backlog_board_updated"] = backlog_board_updated

    record = _record(
        command_id=cid,
        command_type=command_type,
        target=target_str,
        payload=payload,
        now=created_at,
        status=str(outcome.get("status") or "accepted"),
        result=outcome.get("result") if "result" in outcome else outcome,
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
            rel_path = _rel(Path(root).resolve(), path)
            last_updated = _mtime_iso(path)
            payload["source_path"] = rel_path
            payload["source_kind"] = "ui_command"
            payload["last_updated"] = last_updated
            payload["freshness"] = "present"
            payload["source"] = {
                "path": rel_path,
                "kind": "ui_command",
                "last_updated": last_updated,
                "freshness": "present",
            }
            commands.append(payload)
    return commands
