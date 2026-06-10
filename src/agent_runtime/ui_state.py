from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import ui_commands

RESOURCE_NAMES = ("state", "tasks", "agents", "messages", "events", "goals", "sources", "commands")

TASKS_GLOB = "agents/lead_engineer/tasks/TASK-*.md"
SESSION_GLOB = "agents/runtime/sessions/*.json"
EVENT_GLOB = "agents/runtime/events/*.jsonl"
MESSAGE_GLOBS = (
    ("messages_inbox", "agents/messages/inbox/*.md"),
    ("messages_archive", "agents/messages/archive/*.md"),
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


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


def _path_freshness(path: Path) -> str:
    return "present" if path.exists() else "missing"


def _source_metadata(root: Path, path: Path, kind: str, now: str) -> dict[str, Any]:
    rel_path = _rel(root, path)
    return {
        "path": rel_path,
        "kind": kind,
        "last_updated": _mtime_iso(path),
        "last_read_at": now,
        "freshness": _path_freshness(path),
    }


def _source_entry(root: Path, source_id: str, path: Path, kind: str, now: str, mutation_boundary: str) -> dict[str, Any]:
    exists = path.exists()
    return {
        "id": source_id,
        "path": _rel(root, path),
        "kind": kind,
        "fresh": exists,
        "last_updated": _mtime_iso(path),
        "last_read_at": now,
        "freshness": "present" if exists else "missing",
        "mutation_boundary": mutation_boundary,
    }


def _gap(source_id: str, rel_path: str, detail: str) -> dict[str, str]:
    return {
        "kind": "missing_optional_source",
        "source_id": source_id,
        "path": rel_path,
        "detail": detail,
    }


def _warning(kind: str, rel_path: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "path": rel_path, "detail": detail}


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
    if value.lower() == "null":
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    return value.strip("\"'")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse the simple YAML frontmatter shape used by runtime markdown files."""
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


def _section_text(body: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", body[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(body)
    return body[start:end].strip()


def _first_sentence(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().lstrip("-").strip()
        if stripped:
            return stripped
    return ""


def _title_from_path(path: Path, task_id: str) -> str:
    stem = path.stem
    if task_id and stem.startswith(task_id):
        stem = stem[len(task_id) :].lstrip("-_")
    return stem.replace("-", " ").replace("_", " ").strip() or task_id


def _lane_for_status(status: str) -> str:
    normalized = (status or "").strip().lower()
    mapping = {
        "planned": "Backlog",
        "ready": "Ready",
        "in_progress": "In Progress",
        "active": "In Progress",
        "blocked": "Blocked",
        "hold": "Blocked",
        "review": "Review",
        "completed": "Done",
        "done": "Done",
        "대기": "Backlog",
        "진행 중": "In Progress",
        "보류": "Blocked",
        "완료": "Done",
    }
    return mapping.get(normalized, "Backlog")


def _task_order(meta: dict[str, Any], fallback: int) -> int:
    try:
        return int(meta.get("order", fallback))
    except (TypeError, ValueError):
        return fallback


def load_tasks(root: Path, now: str, warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks: list[dict[str, Any]] = []
    if not tasks_dir.is_dir():
        return tasks

    for order, path in enumerate(sorted(tasks_dir.glob("TASK-*.md"))):
        rel_path = _rel(root, path)
        try:
            meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError as exc:
            warnings.append(_warning("task-read-error", rel_path, str(exc)))
            continue
        if not meta:
            warnings.append(_warning("task-frontmatter-missing", rel_path, "task file has no parseable frontmatter"))
            continue
        task_id = str(meta.get("id") or path.stem)
        goal = _section_text(body, "Goal") or _section_text(body, "목표") or body
        labels = meta.get("tags") if isinstance(meta.get("tags"), list) else []
        record = {
            "id": task_id,
            "title": str(meta.get("title") or _title_from_path(path, task_id)),
            "status": str(meta.get("status") or ""),
            "lane": _lane_for_status(str(meta.get("status") or "")),
            "priority": meta.get("priority"),
            "order": _task_order(meta, order),
            "owner_agent": meta.get("owner"),
            "team": meta.get("team"),
            "labels": labels,
            "description": _first_sentence(goal),
            "blocked_reason": meta.get("blocked_reason"),
            "created_at": meta.get("created") or meta.get("created_at"),
            "updated_at": meta.get("updated_at"),
            "completed_at": meta.get("completed_at"),
            "audit_log": meta.get("audit_log") if isinstance(meta.get("audit_log"), list) else [],
            "source_path": rel_path,
            "source_kind": "task_markdown",
            "source": _source_metadata(root, path, "task_markdown", now),
            "last_updated": _mtime_iso(path),
            "freshness": "present",
        }
        tasks.append(record)
    tasks.sort(key=lambda item: (int(item.get("order", 0)), str(item.get("id", ""))))
    return tasks


def load_messages(root: Path, now: str, warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for source_id, glob_expr in MESSAGE_GLOBS:
        for path in sorted(root.glob(glob_expr)):
            rel_path = _rel(root, path)
            try:
                meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            except OSError as exc:
                warnings.append(_warning("message-read-error", rel_path, str(exc)))
                continue
            if not meta:
                warnings.append(_warning("message-frontmatter-missing", rel_path, "message has no parseable frontmatter"))
                continue
            message_id = str(meta.get("id") or path.stem)
            task_id = meta.get("task_id")
            channel = f"task:{task_id}" if task_id and str(task_id).lower() != "none" else f"role:{meta.get('to') or 'unknown'}"
            messages.append(
                {
                    "id": message_id,
                    "from": meta.get("from"),
                    "to": meta.get("to"),
                    "task_id": task_id,
                    "intent": meta.get("intent"),
                    "type": meta.get("type"),
                    "status": meta.get("status"),
                    "ts": meta.get("ts"),
                    "in_reply_to": meta.get("in_reply_to"),
                    "evidence": meta.get("evidence"),
                    "next": meta.get("next"),
                    "body": body,
                    "channel": channel,
                    "thread_root_id": meta.get("in_reply_to") or message_id,
                    "created_at": meta.get("ts"),
                    "answered_at": None,
                    "source_path": rel_path,
                    "source_kind": "message_markdown",
                    "source_domain": source_id,
                    "source": _source_metadata(root, path, "message_markdown", now),
                    "last_updated": _mtime_iso(path),
                    "freshness": "present",
                }
            )
    return messages


def _event_severity(payload: dict[str, Any]) -> str:
    event_name = str(payload.get("event") or "").lower()
    if "error" in event_name or "failed" in event_name or payload.get("error"):
        return "error"
    return "info"


def load_events(root: Path, now: str, warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in sorted(root.glob(EVENT_GLOB)):
        rel_path = _rel(root, path)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            warnings.append(_warning("event-read-error", rel_path, str(exc)))
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                warnings.append(_warning("event-jsonl-parse-error", f"{rel_path}:{line_number}", str(exc)))
                continue
            if not isinstance(payload, dict):
                warnings.append(_warning("event-jsonl-invalid-record", f"{rel_path}:{line_number}", "record is not an object"))
                continue
            record = dict(payload)
            record.update(
                {
                    "id": f"{rel_path}:{line_number}",
                    "type": payload.get("event"),
                    "actor": payload.get("role"),
                    "created_at": payload.get("ts"),
                    "severity": _event_severity(payload),
                    "source_path": rel_path,
                    "source_kind": "event_jsonl",
                    "source": _source_metadata(root, path, "event_jsonl", now),
                    "last_updated": _mtime_iso(path),
                    "freshness": "present",
                }
            )
            events.append(record)
    return events


def load_agents(root: Path, now: str, events: list[dict[str, Any]], warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    latest_event_by_role: dict[str, dict[str, Any]] = {}
    latest_error_by_role: dict[str, dict[str, Any]] = {}
    for event in events:
        role = str(event.get("role") or event.get("actor") or "")
        if not role:
            continue
        latest_event_by_role[role] = event
        if event.get("severity") == "error":
            latest_error_by_role[role] = event

    for path in sorted(root.glob(SESSION_GLOB)):
        rel_path = _rel(root, path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(_warning("session-json-parse-error", rel_path, str(exc)))
            continue
        except OSError as exc:
            warnings.append(_warning("session-read-error", rel_path, str(exc)))
            continue
        if not isinstance(payload, dict):
            warnings.append(_warning("session-json-invalid-record", rel_path, "session payload is not an object"))
            continue
        role = str(payload.get("role") or path.stem)
        latest_event = latest_event_by_role.get(role)
        error_event = latest_error_by_role.get(role)
        status = str(payload.get("status") or "")
        agents.append(
            {
                "id": payload.get("agent_id") or payload.get("id") or path.stem,
                "role": role,
                "status": status,
                "current_task_id": payload.get("task_id") or payload.get("current_task_id"),
                "provider": payload.get("provider"),
                "model": payload.get("model"),
                "display_name": role.replace("_", " ").replace("-", " ").title(),
                "online": status in {"spawning", "active"},
                "last_heartbeat": latest_event.get("ts") if latest_event else None,
                "last_message": None,
                "error_state": error_event.get("event") if error_event else None,
                "source_path": rel_path,
                "source_kind": "session_json",
                "source": _source_metadata(root, path, "session_json", now),
                "last_updated": _mtime_iso(path),
                "freshness": "present",
            }
        )
    return agents


def load_goals(root: Path, now: str) -> list[dict[str, Any]]:
    status_path = root / "STATUS.md"
    if not status_path.exists():
        return []
    try:
        text = status_path.read_text(encoding="utf-8")
    except OSError:
        return []
    headings = list(re.finditer(r"^##\s+(.+)$", text, flags=re.MULTILINE))
    heading = headings[-1].group(1).strip() if headings else "Current Status"
    tail_start = headings[-1].end() if headings else 0
    tail = text[tail_start:]
    summary_match = re.search(r"Summary:\s*(.+)", tail)
    title = summary_match.group(1).strip() if summary_match else heading
    return [
        {
            "id": f"STATUS:{re.sub(r'[^A-Za-z0-9_-]+', '-', heading).strip('-') or 'current'}",
            "title": title,
            "status": "executing",
            "updated_at": _mtime_iso(status_path),
            "source_path": "STATUS.md",
            "source_kind": "status_markdown",
            "source": _source_metadata(root, status_path, "status_markdown", now),
            "last_updated": _mtime_iso(status_path),
            "freshness": "present",
        }
    ]


def _collect_sources_and_gaps(root: Path, now: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    source_specs = (
        ("tasks", root / "agents" / "lead_engineer" / "tasks", "task_directory", "api_or_outbox"),
        ("messages_inbox", root / "agents" / "messages" / "inbox", "message_directory", "api_or_outbox"),
        ("messages_archive", root / "agents" / "messages" / "archive", "message_directory", "read_only"),
        ("sessions", root / "agents" / "runtime" / "sessions", "session_directory", "runtime_api"),
        ("events", root / "agents" / "runtime" / "events", "event_directory", "append_only_runtime"),
        ("status", root / "STATUS.md", "status_markdown", "agent_doc_workflow"),
        ("state_machines", root / "agents" / "project" / "STATE-MACHINES.yml", "state_machine_yaml", "schema_first_task"),
        ("ui_outbox", root / ".ui_outbox", "ui_command_outbox", "api_only"),
    )
    sources = [_source_entry(root, source_id, path, kind, now, boundary) for source_id, path, kind, boundary in source_specs]
    optional = {"messages_inbox", "messages_archive", "sessions", "events", "status"}
    gaps = [
        _gap(source["id"], source["path"], "optional runtime source is not present")
        for source in sources
        if source["id"] in optional and not source["fresh"]
    ]
    return sources, gaps


def build_state(root: Path | str, now: str | None = None) -> dict[str, Any]:
    root_path = Path(root).resolve()
    generated_at = now or _now_iso()
    warnings: list[dict[str, str]] = []
    sources, gaps = _collect_sources_and_gaps(root_path, generated_at)
    tasks = load_tasks(root_path, generated_at, warnings)
    events = load_events(root_path, generated_at, warnings)
    agents = load_agents(root_path, generated_at, events, warnings)
    messages = load_messages(root_path, generated_at, warnings)
    goals = load_goals(root_path, generated_at)
    commands = ui_commands.list_commands(root_path)
    return {
        "generated_at": generated_at,
        "sources": sources,
        "tasks": tasks,
        "agents": agents,
        "messages": messages,
        "events": events,
        "goals": goals,
        "commands": commands,
        "gaps": gaps,
        "warnings": warnings,
    }


def build_resource(root: Path | str, resource: str, now: str | None = None) -> dict[str, Any]:
    if resource not in RESOURCE_NAMES:
        raise ValueError(f"unknown resource: {resource}")
    state = build_state(root, now=now)
    if resource == "state":
        return state
    return {
        "generated_at": state["generated_at"],
        "resource": resource,
        "items": state[resource],
        "sources": state["sources"],
        "gaps": state["gaps"],
        "warnings": state["warnings"],
    }


def render_summary(state: dict[str, Any], resource: str) -> str:
    if resource == "state":
        lines = [
            "# UI Runtime State",
            "",
            f"generated_at={state['generated_at']}",
            f"tasks={len(state['tasks'])}",
            f"agents={len(state['agents'])}",
            f"messages={len(state['messages'])}",
            f"events={len(state['events'])}",
            f"goals={len(state['goals'])}",
            f"gaps={len(state['gaps'])}",
            f"warnings={len(state['warnings'])}",
        ]
        return "\n".join(lines)
    return "\n".join([f"# UI Runtime Resource: {resource}", f"items={len(state.get(resource, []))}"])


def run_ui_state(root: Path, *, resource: str = "state", json_output: bool = False) -> int:
    payload = build_resource(root, resource)
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        state = payload if resource == "state" else build_state(root)
        print(render_summary(state, resource))
    return 0
