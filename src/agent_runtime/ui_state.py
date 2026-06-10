from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import ui_commands

RESOURCE_NAMES = (
    "state",
    "tasks",
    "agents",
    "messages",
    "events",
    "goals",
    "sources",
    "errors",
    "evidence",
    "replay",
    "graph",
    "state_machines",
    "roadmap",
    "commands",
)

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


def _filter_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(_filter_text(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _first_filter(filters: dict[str, Any], *names: str) -> str:
    for name in names:
        value = filters.get(name)
        if isinstance(value, list):
            value = value[0] if value else ""
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def filter_events(events: list[dict[str, Any]], filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    event_type = _first_filter(filters, "type", "event")
    agent = _first_filter(filters, "agent", "role", "actor")
    task_id = _first_filter(filters, "task_id", "task")
    goal_id = _first_filter(filters, "goal_id", "goal")
    query = _first_filter(filters, "q", "query", "search").lower()

    filtered: list[dict[str, Any]] = []
    for event in events:
        if event_type and str(event.get("event") or event.get("type") or "") != event_type:
            continue
        if agent and str(event.get("role") or event.get("actor") or "") != agent:
            continue
        if task_id and str(event.get("task_id") or "") != task_id:
            continue
        if goal_id and str(event.get("goal_id") or "") != goal_id:
            continue
        if query and query not in _filter_text(event).lower():
            continue
        filtered.append(event)
    return filtered


def derive_errors(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for event in events:
        if event.get("severity") != "error":
            continue
        message = str(event.get("error") or event.get("message") or event.get("detail") or event.get("event") or "runtime error")
        errors.append(
            {
                "id": f"error:{event.get('id')}",
                "event_id": event.get("id"),
                "message": message,
                "event": event.get("event"),
                "actor": event.get("role") or event.get("actor"),
                "task_id": event.get("task_id"),
                "goal_id": event.get("goal_id"),
                "created_at": event.get("created_at") or event.get("ts"),
                "source_path": event.get("source_path"),
                "source_kind": "derived_error",
                "last_updated": event.get("last_updated"),
                "freshness": event.get("freshness", "present"),
            }
        )
    return errors


def _evidence_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def derive_evidence(events: list[dict[str, Any]], messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for event in events:
        for item in _evidence_values(event.get("evidence")):
            evidence.append(
                {
                    "id": f"evidence:{event.get('id')}:{len(evidence) + 1}",
                    "evidence": item,
                    "source_id": event.get("id"),
                    "source_type": "event",
                    "task_id": event.get("task_id"),
                    "goal_id": event.get("goal_id"),
                    "created_at": event.get("created_at") or event.get("ts"),
                    "source_path": event.get("source_path"),
                    "source_kind": "derived_evidence",
                    "last_updated": event.get("last_updated"),
                    "freshness": event.get("freshness", "present"),
                }
            )
    for message in messages:
        for item in _evidence_values(message.get("evidence")):
            evidence.append(
                {
                    "id": f"evidence:{message.get('id')}:{len(evidence) + 1}",
                    "evidence": item,
                    "source_id": message.get("id"),
                    "source_type": "message",
                    "task_id": message.get("task_id"),
                    "goal_id": message.get("goal_id"),
                    "created_at": message.get("created_at") or message.get("ts"),
                    "source_path": message.get("source_path"),
                    "source_kind": "derived_evidence",
                    "last_updated": message.get("last_updated"),
                    "freshness": message.get("freshness", "present"),
                }
            )
    return evidence


def build_replay(events: list[dict[str, Any]], messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    replay: list[dict[str, Any]] = []
    for event in events:
        if not event.get("goal_id") and not event.get("task_id"):
            continue
        replay.append(
            {
                "id": f"replay:{event.get('id')}",
                "kind": "event",
                "type": event.get("event") or event.get("type"),
                "actor": event.get("role") or event.get("actor"),
                "task_id": event.get("task_id"),
                "goal_id": event.get("goal_id"),
                "summary": str(event.get("error") or event.get("message") or event.get("event") or ""),
                "created_at": event.get("created_at") or event.get("ts"),
                "source_path": event.get("source_path"),
                "source_kind": "replay_event",
                "last_updated": event.get("last_updated"),
                "freshness": event.get("freshness", "present"),
            }
        )
    for message in messages:
        if not message.get("task_id"):
            continue
        replay.append(
            {
                "id": f"replay:{message.get('id')}",
                "kind": "message",
                "type": message.get("intent") or message.get("type"),
                "actor": message.get("from"),
                "task_id": message.get("task_id"),
                "goal_id": message.get("goal_id"),
                "summary": _first_sentence(str(message.get("body") or "")),
                "created_at": message.get("created_at") or message.get("ts"),
                "source_path": message.get("source_path"),
                "source_kind": "replay_message",
                "last_updated": message.get("last_updated"),
                "freshness": message.get("freshness", "present"),
            }
        )
    replay.sort(key=lambda item: str(item.get("created_at") or ""))
    return replay[-200:]


def build_graph(tasks: list[dict[str, Any]], agents: list[dict[str, Any]], messages: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    def add_node(node_id: Any, kind: str, label: str | None = None) -> None:
        if node_id is None or str(node_id).strip() == "":
            return
        key = str(node_id)
        nodes.setdefault(key, {"id": key, "kind": kind, "label": label or key})

    for agent in agents:
        add_node(agent.get("role") or agent.get("id"), "agent", agent.get("display_name"))
    for task in tasks:
        add_node(task.get("id"), "task", task.get("title"))
        add_node(task.get("owner_agent"), "agent")
        if task.get("owner_agent"):
            edges.append({"id": f"task-owner:{task.get('id')}", "from": str(task.get("owner_agent")), "to": str(task.get("id")), "kind": "owns_task", "task_id": task.get("id")})
    for message in messages:
        add_node(message.get("from"), "actor")
        add_node(message.get("to"), "agent")
        if message.get("from") and message.get("to"):
            edges.append(
                {
                    "id": f"message:{message.get('id')}",
                    "from": str(message.get("from")),
                    "to": str(message.get("to")),
                    "kind": "message",
                    "task_id": message.get("task_id"),
                    "source_path": message.get("source_path"),
                }
            )
    for event in events:
        add_node(event.get("role") or event.get("actor"), "agent")
    return {
        "nodes": sorted(nodes.values(), key=lambda item: (item["kind"], item["id"])),
        "edges": edges,
    }


def _parse_state_machines_text(text: str) -> list[dict[str, Any]]:
    machines: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_states = False
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if line.startswith("  - id: "):
            if current:
                machines.append(current)
            current = {"id": stripped.partition(":")[2].strip(), "states": []}
            in_states = False
            continue
        if current is None:
            continue
        if line.startswith("    scope: "):
            current["scope"] = stripped.partition(":")[2].strip()
        elif line.startswith("    owner: "):
            current["owner"] = stripped.partition(":")[2].strip()
        elif line.startswith("    initial: "):
            current["initial"] = stripped.partition(":")[2].strip()
        elif line.startswith("    states:"):
            in_states = True
        elif in_states and line.startswith("      - id: "):
            current.setdefault("states", []).append(stripped.partition(":")[2].strip())
        elif line.startswith("    transitions:"):
            in_states = False
    if current:
        machines.append(current)
    return machines


def _observed_machine_state(machine_id: str, tasks: list[dict[str, Any]], agents: list[dict[str, Any]], fallback: str | None) -> tuple[str | None, dict[str, int]]:
    counts: dict[str, int] = {}
    if machine_id == "task":
        for task in tasks:
            status = str(task.get("status") or "")
            if status:
                counts[status] = counts.get(status, 0) + 1
        for preferred in ("blocked", "in_progress", "review", "ready", "planned", "completed"):
            if counts.get(preferred):
                return preferred, counts
    if machine_id == "agent_job":
        for agent in agents:
            status = str(agent.get("status") or "")
            if status:
                counts[status] = counts.get(status, 0) + 1
        if counts.get("active"):
            return "working", counts
    return fallback, counts


def load_state_machines(root: Path, tasks: list[dict[str, Any]], agents: list[dict[str, Any]], now: str) -> list[dict[str, Any]]:
    path = root / "agents" / "project" / "STATE-MACHINES.yml"
    if not path.exists():
        return []
    try:
        machines = _parse_state_machines_text(path.read_text(encoding="utf-8"))
    except OSError:
        return []
    for machine in machines:
        current, counts = _observed_machine_state(str(machine.get("id") or ""), tasks, agents, machine.get("initial"))
        machine["current_state"] = current
        machine["observed_counts"] = counts
        machine["source_path"] = _rel(root, path)
        machine["source_kind"] = "state_machine_yaml"
        machine["source"] = _source_metadata(root, path, "state_machine_yaml", now)
        machine["last_updated"] = _mtime_iso(path)
        machine["freshness"] = "present"
    return machines


def load_roadmap(root: Path, now: str) -> dict[str, Any]:
    path = root / "agents" / "project" / "ROADMAP.md"
    if not path.exists():
        return {"phase": None, "next_milestone": None, "milestones": [], "source_path": _rel(root, path), "source_kind": "roadmap_markdown", "freshness": "missing", "last_updated": None}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {"phase": None, "next_milestone": None, "milestones": [], "source_path": _rel(root, path), "source_kind": "roadmap_markdown", "freshness": "missing", "last_updated": None}
    phase_match = re.search(r"^-\s+phase:\s*(.+)$", text, flags=re.MULTILINE)
    next_match = re.search(r"^-\s+next_milestone:\s*(.+)$", text, flags=re.MULTILINE)
    milestones: list[dict[str, Any]] = []
    for match in re.finditer(r"^-\s+\[(?P<done>[ xX])\]\s+(?P<date>\d{4}-\d{2}-\d{2}):\s+(?P<title>.+)$", text, flags=re.MULTILINE):
        milestones.append(
            {
                "date": match.group("date"),
                "title": match.group("title").strip(),
                "done": match.group("done").lower() == "x",
            }
        )
    return {
        "phase": phase_match.group(1).strip() if phase_match else None,
        "next_milestone": next_match.group(1).strip() if next_match else None,
        "milestones": milestones,
        "source_path": _rel(root, path),
        "source_kind": "roadmap_markdown",
        "source": _source_metadata(root, path, "roadmap_markdown", now),
        "last_updated": _mtime_iso(path),
        "freshness": "present",
    }


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
        ("roadmap", root / "agents" / "project" / "ROADMAP.md", "roadmap_markdown", "agent_doc_workflow"),
        ("ui_outbox", root / ".ui_outbox", "ui_command_outbox", "api_only"),
    )
    sources = [_source_entry(root, source_id, path, kind, now, boundary) for source_id, path, kind, boundary in source_specs]
    optional = {"messages_inbox", "messages_archive", "sessions", "events", "status", "state_machines", "roadmap"}
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
    errors = derive_errors(events)
    evidence = derive_evidence(events, messages)
    replay = build_replay(events, messages)
    graph = build_graph(tasks, agents, messages, events)
    state_machines = load_state_machines(root_path, tasks, agents, generated_at)
    roadmap = load_roadmap(root_path, generated_at)
    return {
        "generated_at": generated_at,
        "sources": sources,
        "tasks": tasks,
        "agents": agents,
        "messages": messages,
        "events": events,
        "goals": goals,
        "errors": errors,
        "evidence": evidence,
        "replay": replay,
        "graph": graph,
        "state_machines": state_machines,
        "roadmap": roadmap,
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
            f"errors={len(state['errors'])}",
            f"evidence={len(state['evidence'])}",
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
