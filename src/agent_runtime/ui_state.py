from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import ui_commands

RESOURCE_NAMES = (
    "state",
    "tasks",
    "agents",
    "task_sets",
    "collaboration",
    "messages",
    "events",
    "goals",
    "task_claims",
    "multipane_assurance",
    "inflight",
    "work_explorer",
    "meeting_room",
    "channels",
    "tasksets_board",
    "taskset_completion",
    "team_agents",
    "sources",
    "errors",
    "evidence",
    "replay",
    "graph",
    "live_map",
    "dependency_graph",
    "timeline",
    "state_machines",
    "roadmap",
    "roadmap_timeline",
    "planning",
    "commands",
)

TASKS_GLOB = "agents/lead_engineer/tasks/TASK-*.md"
WORK_ITEM_CLASSIFICATION_REL = "agents/project/work-items/WORK-ITEM-CLASSIFICATION.json"
SESSION_GLOB = "agents/runtime/sessions/*.json"
TASK_CLAIM_GLOB = "agents/runtime/task_claims/*.json"
INSTANCE_GLOB = "agents/runtime/instances/*.json"
EVENT_GLOB = "agents/runtime/events/*.jsonl"
PANE_EVENT_GLOB = "agents/runtime/pane_events/*.jsonl"
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


def _peek_summary(meta: dict[str, Any], goal: str) -> str:
    """Compact one-line summary reused by the board hover-peek (additive, derived)."""
    summary = _first_sentence(goal)
    blocked = str(meta.get("blocked_reason") or "").strip()
    if blocked:
        prefix = f"Blocked: {blocked}."
        return f"{prefix} {summary}".strip() if summary else prefix
    return summary


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


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower())
    text = re.sub(r"-+", "-", text)
    return text.strip("-") or "taskset"


def _taskset_slug(task_set_id: str) -> str:
    return _slug(re.sub(r"^TASKSET-AR-", "", task_set_id, flags=re.IGNORECASE))


def _letter_alias(index: int) -> str:
    if index < 1:
        return ""
    letters: list[str] = []
    value = index
    while value:
        value, remainder = divmod(value - 1, 26)
        letters.append(chr(ord("A") + remainder))
    return "".join(reversed(letters))


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _string_list(value: Any) -> list[str]:
    """Normalize a frontmatter scalar/list into a deduped list of strings.

    Tolerates both the YAML list shape (``blocks:`` followed by ``  - X``) and a
    single inline scalar (``blocks: TASK-AR-1``) so dependency edges can be
    declared either way. Empty/blank entries are dropped.
    """
    if value in (None, "", []):
        return []
    if isinstance(value, (list, tuple)):
        items = [str(item) for item in value]
    else:
        items = [str(value)]
    return _dedupe_strings(items)


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
        registered_at = meta.get("registered_at") or meta.get("created") or meta.get("created_at")
        created_at = meta.get("created_at") or meta.get("created") or registered_at
        updated_at = meta.get("updated_at")
        started_at = meta.get("started_at")
        completed_at = meta.get("completed_at")
        goal = _section_text(body, "Goal") or _section_text(body, "목표") or body
        labels = meta.get("tags") if isinstance(meta.get("tags"), list) else []
        parent_id = str(meta.get("parent_id") or "").strip()
        blocks = _string_list(meta.get("blocks"))
        blocked_by = _string_list(meta.get("blocked_by"))
        metadata = {
            "task_uid": meta.get("task_uid"),
            "display_id": meta.get("display_id") or task_id,
            "registered_at": registered_at,
            "created_at": created_at,
            "started_at": started_at,
            "updated_at": updated_at,
            "completed_at": completed_at,
        }
        record = {
            "id": task_id,
            "task_uid": meta.get("task_uid"),
            "display_id": meta.get("display_id") or task_id,
            "title": str(meta.get("title") or _title_from_path(path, task_id)),
            "status": str(meta.get("status") or ""),
            "lane": _lane_for_status(str(meta.get("status") or "")),
            "priority": meta.get("priority"),
            "task_set_id": meta.get("task_set_id"),
            "order": _task_order(meta, order),
            "owner_agent": meta.get("owner"),
            "team": meta.get("team"),
            "parent_id": parent_id,
            "blocks": blocks,
            "blocked_by": blocked_by,
            "labels": labels,
            "description": _first_sentence(goal),
            "peek_summary": _peek_summary(meta, goal),
            "blocked_reason": meta.get("blocked_reason"),
            "registered_at": registered_at,
            "created_at": created_at,
            "started_at": started_at,
            "updated_at": updated_at,
            "completed_at": completed_at,
            "metadata": metadata,
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


def load_pane_events(root: Path, now: str, warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in sorted(root.glob(PANE_EVENT_GLOB)):
        rel_path = _rel(root, path)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            warnings.append(_warning("pane-event-read-error", rel_path, str(exc)))
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                warnings.append(_warning("pane-event-jsonl-parse-error", f"{rel_path}:{line_number}", str(exc)))
                continue
            if not isinstance(payload, dict):
                warnings.append(_warning("pane-event-jsonl-invalid-record", f"{rel_path}:{line_number}", "record is not an object"))
                continue
            record = dict(payload)
            record.update(
                {
                    "id": f"{rel_path}:{line_number}",
                    "type": payload.get("event"),
                    "actor": payload.get("actor"),
                    "created_at": payload.get("ts"),
                    "source_path": rel_path,
                    "source_kind": "pane_event_jsonl",
                    "source": _source_metadata(root, path, "pane_event_jsonl", now),
                    "last_updated": _mtime_iso(path),
                    "freshness": "present",
                }
            )
            events.append(record)
    return events


def build_collaboration(pane_events: list[dict[str, Any]]) -> dict[str, Any]:
    task_sets: dict[str, dict[str, Any]] = {}
    active_claims: dict[str, str] = {}
    ssot_write_attempts = 0
    for event in pane_events:
        task_set_id = str(event.get("task_set_id") or "").strip() or "unassigned"
        group = task_sets.setdefault(
            task_set_id,
            {
                "task_set_id": task_set_id,
                "event_count": 0,
                "active_claim_ids": set(),
                "last_event": None,
                "last_ts": None,
            },
        )
        group["event_count"] += 1
        group["last_event"] = event.get("event")
        group["last_ts"] = event.get("ts")
        claim_id = str(event.get("claim_id") or "").strip()
        if claim_id:
            if event.get("event") == "claim_released":
                active_claims.pop(claim_id, None)
            else:
                active_claims[claim_id] = task_set_id
        if event.get("event") == "ssot_write_attempted":
            ssot_write_attempts += 1
    for claim_id, task_set_id in active_claims.items():
        task_sets.setdefault(
            task_set_id,
            {"task_set_id": task_set_id, "event_count": 0, "active_claim_ids": set(), "last_event": None, "last_ts": None},
        )["active_claim_ids"].add(claim_id)
    rows: list[dict[str, Any]] = []
    for task_set_id in sorted(task_sets):
        row = dict(task_sets[task_set_id])
        row["active_claim_ids"] = sorted(row["active_claim_ids"])
        rows.append(row)
    return {
        "summary": {
            "event_count": len(pane_events),
            "task_set_count": len(rows),
            "ssot_write_attempts": ssot_write_attempts,
        },
        "task_sets": rows,
        "events": pane_events[-200:],
    }


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


def enrich_tasks_with_evidence(tasks: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for item in evidence:
        task_id = str(item.get("task_id") or "").strip()
        if task_id:
            counts[task_id] = counts.get(task_id, 0) + 1
    for task in tasks:
        count = counts.get(str(task.get("id") or ""), 0)
        task["evidence_count"] = count
        task["evidence_label"] = "1 evidence" if count == 1 else f"{count} evidence"


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


def build_replay_snapshot(replay: list[dict[str, Any]], at: str | None = None) -> dict[str, Any]:
    cutoff = str(at or "").strip()
    selected = [item for item in replay if not cutoff or str(item.get("created_at") or "") <= cutoff]
    return {
        "resource": "replay_snapshot",
        "at": cutoff or None,
        "event_count": len(selected),
        "task_ids": sorted({str(item.get("task_id")) for item in selected if item.get("task_id")}),
        "goal_ids": sorted({str(item.get("goal_id")) for item in selected if item.get("goal_id")}),
        "items": selected[-80:],
    }


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


# --- Realtime presence + live map (TASK-AR-326) ----------------------------
# A typed node/edge graph layered on the existing read-only state primitives so
# the console can pulse-highlight edges as SSE events arrive. Nodes carry a
# semantic ``kind`` (owner / agent / taskset / gate) and edges a semantic
# ``kind`` (message / assignment / review / block); both expose stable ids so
# the front-end can map an incoming event onto the edge(s) it touches.
LIVE_MAP_SCHEMA = "agent-runtime-live-map/v1"
LIVE_MAP_OWNER_ID = "owner"
_LIVE_MAP_REVIEW_STATES = {"review", "waiting_review", "ready_for_governance_review", "reviewing"}
_LIVE_MAP_BLOCKED_STATES = {"blocked", "hold", "보류"}


def build_live_map(
    tasks: list[dict[str, Any]],
    agents: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    team_agents: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    """Derive the presence-aware live map (nodes + typed edges + presence roll-up).

    Read-only: every node/edge points back at a source primitive; nothing here
    mutates stored state. ``presence`` summarises the team_agents view so the
    front-end can animate state transitions without a full re-render.
    """

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    edge_ids: set[str] = set()

    def add_node(node_id: Any, kind: str, label: str | None = None, **extra: Any) -> str | None:
        if node_id is None or str(node_id).strip() == "":
            return None
        key = str(node_id)
        node = nodes.get(key)
        if node is None:
            node = nodes[key] = {"id": key, "kind": kind, "label": label or key}
        if label and node.get("label") in (None, key):
            node["label"] = label
        for name, value in extra.items():
            if value is not None and node.get(name) in (None, ""):
                node[name] = value
        return key

    def add_edge(edge_id: str, frm: str | None, to: str | None, kind: str, **extra: Any) -> None:
        if not frm or not to or edge_id in edge_ids:
            return
        edge_ids.add(edge_id)
        edge = {"id": edge_id, "from": frm, "to": to, "kind": kind}
        for name, value in extra.items():
            if value is not None:
                edge[name] = value
        edges.append(edge)

    # Owner is always present as the apex node of the org graph.
    add_node(LIVE_MAP_OWNER_ID, "owner", "Owner")

    # Presence roll-up + agent nodes from the team_agents (RPG) view.
    presence_counts: dict[str, int] = {}
    presence_agents: list[dict[str, Any]] = []
    for team in team_agents.get("teams", []) or []:
        for card in team.get("agents", []) or []:
            agent_id = str(card.get("role") or card.get("id") or "").strip()
            if not agent_id:
                continue
            presence = str(card.get("presence") or "offline")
            presence_counts[presence] = presence_counts.get(presence, 0) + 1
            presence_agents.append(
                {
                    "id": card.get("id"),
                    "role": agent_id,
                    "callsign": card.get("callsign"),
                    "presence": presence,
                    "online": bool(card.get("online")),
                    "current_task_id": card.get("current_task_id"),
                    "team_id": team.get("team_id") or team.get("id"),
                }
            )
            add_node(
                agent_id,
                "agent",
                card.get("callsign") or agent_id,
                presence=presence,
                online=bool(card.get("online")),
                team_id=team.get("team_id") or team.get("id"),
            )

    # Agent nodes from the live session view (covers agents without an instance).
    for agent in agents:
        agent_id = str(agent.get("role") or agent.get("id") or "").strip()
        if not agent_id:
            continue
        node = add_node(agent_id, "agent", agent.get("display_name") or agent_id)
        if node is not None and "presence" not in nodes[node]:
            nodes[node]["presence"] = "online" if agent.get("online") else "offline"
            nodes[node]["online"] = bool(agent.get("online"))

    # Taskset + gate nodes and assignment / review / block edges from tasks.
    for task in tasks:
        task_id = str(task.get("id") or "").strip()
        status = str(task.get("status") or "").lower()
        owner = str(task.get("owner_agent") or "").strip()
        taskset_id = str(task.get("task_set_id") or "").strip()
        taskset_node = add_node(taskset_id, "taskset") if taskset_id else None

        if owner:
            add_node(owner, "agent")
            if taskset_node:
                add_edge(
                    f"assignment:{task_id}",
                    owner,
                    taskset_node,
                    "assignment",
                    task_id=task_id,
                    status=status,
                    source_path=task.get("source_path"),
                )

        if status in _LIVE_MAP_REVIEW_STATES:
            gate_id = f"gate:{taskset_id or task_id}"
            add_node(gate_id, "gate", f"Gate {taskset_id or task_id}")
            if owner:
                add_edge(f"review:{task_id}", owner, gate_id, "review", task_id=task_id, status=status)
            add_edge(f"review-gate:{task_id}", gate_id, LIVE_MAP_OWNER_ID, "review", task_id=task_id, status=status)

        if status in _LIVE_MAP_BLOCKED_STATES:
            gate_id = f"gate:{taskset_id or task_id}"
            add_node(gate_id, "gate", f"Gate {taskset_id or task_id}")
            if owner:
                add_edge(
                    f"block:{task_id}",
                    owner,
                    gate_id,
                    "block",
                    task_id=task_id,
                    status=status,
                    blocked_reason=task.get("blocked_reason"),
                )

    # Message edges (actor -> recipient) from the message inbox/archive.
    for message in messages:
        frm = str(message.get("from") or "").strip()
        to = str(message.get("to") or "").strip()
        if not frm or not to:
            continue
        add_node(frm, "agent")
        add_node(to, "agent")
        add_edge(
            f"message:{message.get('id')}",
            frm,
            to,
            "message",
            task_id=message.get("task_id"),
            status=message.get("status"),
            source_path=message.get("source_path"),
        )

    edge_kind_counts: dict[str, int] = {}
    for edge in edges:
        edge_kind_counts[edge["kind"]] = edge_kind_counts.get(edge["kind"], 0) + 1
    node_kind_counts: dict[str, int] = {}
    for node in nodes.values():
        node_kind_counts[node["kind"]] = node_kind_counts.get(node["kind"], 0) + 1

    return {
        "schema": LIVE_MAP_SCHEMA,
        "generated_at": now,
        "presence": {
            "counts": dict(sorted(presence_counts.items())),
            "online": sum(1 for agent in presence_agents if agent["online"]),
            "agents": sorted(presence_agents, key=lambda a: (not a["online"], str(a["role"]))),
        },
        "nodes": sorted(nodes.values(), key=lambda item: (item["kind"], item["id"])),
        "edges": edges,
        "totals": {
            "nodes": len(nodes),
            "edges": len(edges),
            "node_kinds": dict(sorted(node_kind_counts.items())),
            "edge_kinds": dict(sorted(edge_kind_counts.items())),
        },
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


def _is_active_task_claim(status: str) -> bool:
    return status in {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}


def _score_label(value: Any) -> tuple[int | None, str]:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return None, "not scored"
    return max(0, min(100, score)), f"{max(0, min(100, score))}/100"


def load_task_claims(root: Path, now: str, warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for path in sorted(root.glob(TASK_CLAIM_GLOB)):
        rel_path = _rel(root, path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(_warning("task-claim-json-parse-error", rel_path, str(exc)))
            continue
        except OSError as exc:
            warnings.append(_warning("task-claim-read-error", rel_path, str(exc)))
            continue
        if not isinstance(payload, dict):
            warnings.append(_warning("task-claim-invalid-record", rel_path, "task claim payload is not an object"))
            continue
        record = dict(payload)
        record.update(
            {
                "id": payload.get("claim_id") or path.stem,
                "source_path": rel_path,
                "source_kind": "task_claim_json",
                "source": _source_metadata(root, path, "task_claim_json", now),
                "last_updated": _mtime_iso(path),
                "freshness": "present",
            }
        )
        claims.append(record)
    return claims


def load_agents(
    root: Path,
    now: str,
    events: list[dict[str, Any]],
    warnings: list[dict[str, str]],
    task_claims: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    for claim in task_claims or []:
        status = str(claim.get("status") or "")
        if not _is_active_task_claim(status):
            continue
        score, score_label = _score_label(claim.get("score"))
        agents.append(
            {
                "id": claim.get("agent_instance_id") or claim.get("claim_id"),
                "role": claim.get("agent_role"),
                "team_id": claim.get("team_id"),
                "status": status,
                "score": score,
                "score_label": score_label,
                "phase": claim.get("phase"),
                "progress_pct": claim.get("progress_pct"),
                "current_task_id": claim.get("task_id"),
                "provider": claim.get("provider"),
                "model": claim.get("model"),
                "display_name": claim.get("display_name") or claim.get("agent_instance_id") or claim.get("agent_role"),
                "mode": claim.get("mode"),
                "tags": claim.get("tags") if isinstance(claim.get("tags"), list) else [],
                "online": status in {"claimed", "in_progress", "review", "waiting_review", "working"},
                "last_heartbeat": claim.get("last_heartbeat"),
                "last_message": None,
                "error_state": None,
                "worktree_path": claim.get("worktree_path"),
                "branch": claim.get("branch"),
                "pane_id": claim.get("pane_id"),
                "task_set_id": claim.get("task_set_id"),
                "step_index": claim.get("step_index"),
                "step_total": claim.get("step_total"),
                "status_text": claim.get("status_text"),
                "callsite_id": claim.get("callsite_id"),
                "claim_id": claim.get("claim_id"),
                "source_path": claim.get("source_path"),
                "source_kind": "task_claim_json",
                "source": claim.get("source"),
                "last_updated": claim.get("last_updated"),
                "freshness": claim.get("freshness", "present"),
            }
        )

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
        score, score_label = _score_label(payload.get("score"))
        agents.append(
            {
                "id": payload.get("agent_id") or payload.get("id") or path.stem,
                "role": role,
                "status": status,
                "score": score,
                "score_label": score_label,
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


def _progress_pct(value: Any) -> int | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0 or number > 100:
        return None
    return int(round(number))


def _task_set_info_from_item(item: Any, sequence: int | None = None) -> dict[str, Any] | None:
    task_set_id = str(getattr(item, "task_set_id", "") or "").strip()
    if not task_set_id:
        return None
    try:
        order = int(getattr(item, "order", 999))
    except (TypeError, ValueError):
        order = 999
    return {
        "id": task_set_id,
        "display_name": str(getattr(item, "display_name", "") or task_set_id),
        "summary": str(getattr(item, "summary", "") or ""),
        "sort_order": order,
        "sequence": sequence,
    }


def _load_task_set_info(root: Path | None, warnings: list[dict[str, str]] | None = None) -> dict[str, dict[str, Any]]:
    if root is None:
        return {}
    path = root / "scripts" / "backlog_board.py"
    if not path.exists():
        return {}
    module_name = f"_agent_runtime_ui_backlog_board_{abs(hash(path.resolve()))}"
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return {}
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - defensive adapter boundary
        if warnings is not None:
            warnings.append(_warning("task-set-info-import-error", _rel(root, path), str(exc)))
        return {}

    infos: dict[str, dict[str, Any]] = {}
    for sequence, item in enumerate(getattr(module, "TASK_SET_DEFINITIONS", []) or [], start=1):
        info = _task_set_info_from_item(item, sequence)
        if info:
            infos[info["id"]] = info
    unclassified = _task_set_info_from_item(getattr(module, "UNCLASSIFIED_TASK_SET", None), None)
    if unclassified:
        infos[unclassified["id"]] = unclassified
    return infos


def _fallback_task_set_info(task_set_id: str) -> dict[str, Any]:
    display = _taskset_slug(task_set_id).replace("-", " ").title()
    return {
        "id": task_set_id,
        "display_name": display or task_set_id,
        "summary": f"Tasks grouped under {task_set_id}.",
        "sort_order": 999,
        "sequence": None,
    }


def _status_bucket(task: dict[str, Any]) -> str:
    status = str(task.get("status") or "").strip().lower()
    if status in {"blocked", "hold", "보류"}:
        return "blocked"
    if status in {"completed", "done", "released", "완료"} or task.get("lane") == "Done":
        return "done"
    if status in {"review", "waiting_review", "ready_for_governance_review"} or task.get("lane") == "Review":
        return "review"
    if status in {"in_progress", "active", "claimed", "working", "assigned"} or task.get("lane") == "In Progress":
        return "in_progress"
    if status in {"ready"} or task.get("lane") == "Ready":
        return "ready"
    return "planned"


def _task_is_open(task: dict[str, Any]) -> bool:
    return _status_bucket(task) != "done"


def _task_set_status(group: dict[str, Any]) -> str:
    if int(group.get("active", 0) or 0) > 0:
        return "active"
    if int(group.get("tasks_blocked", 0) or 0) > 0:
        return "blocked"
    if int(group.get("tasks_total", 0) or 0) > 0 and int(group.get("tasks_open", 0) or 0) == 0:
        return "completed"
    if int(group.get("tasks_in_progress", 0) or 0) > 0:
        return "in_progress"
    return "planned"


def _task_set_aliases(task_set_id: str, info: dict[str, Any], sequence: int) -> list[str]:
    letter = _letter_alias(sequence)
    return _dedupe_strings(
        [
            f"taskset {sequence}",
            f"taskset-{sequence}",
            f"taskset {letter}",
            f"taskset-{letter}",
            str(sequence),
            letter,
            _taskset_slug(task_set_id),
            _slug(str(info.get("display_name") or "")),
            _slug(task_set_id.replace("TASKSET-AR-", "")),
            task_set_id,
        ]
    )


def _command_alias(sequence: int) -> str:
    return str(sequence)


def build_task_sets(
    agents: list[dict[str, Any]],
    tasks: list[dict[str, Any]] | None = None,
    *,
    root: Path | None = None,
    warnings: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    info_by_id = _load_task_set_info(root, warnings)

    def group_for(task_set_id: str) -> dict[str, Any]:
        info = info_by_id.get(task_set_id) or _fallback_task_set_info(task_set_id)
        return groups.setdefault(
            task_set_id,
            {
                "id": task_set_id,
                "display_name": info["display_name"],
                "summary": info["summary"],
                "sort_order": info["sort_order"],
                "sequence": info.get("sequence"),
                "agents": 0,
                "active": 0,
                "blocked": 0,
                "done": 0,
                "current_task_ids": set(),
                "active_claim_ids": set(),
                "task_ids": set(),
                "status_text": None,
                "tasks_total": 0,
                "tasks_open": 0,
                "tasks_done": 0,
                "tasks_blocked": 0,
                "tasks_in_progress": 0,
                "tasks_ready": 0,
                "tasks_review": 0,
                "next_task_id": None,
                "next_task_title": None,
                "next_task_status": None,
                "_next_task_order": None,
                "_progress_values": [],
            },
        )

    for task in tasks or []:
        task_set_id = str(task.get("task_set_id") or "").strip()
        if not task_set_id:
            continue
        group = group_for(task_set_id)
        group["tasks_total"] += 1
        task_id = str(task.get("id") or "").strip()
        if task_id:
            group["task_ids"].add(task_id)
        bucket = _status_bucket(task)
        if bucket == "done":
            group["tasks_done"] += 1
            group["done"] += 1
        else:
            group["tasks_open"] += 1
        if bucket == "blocked":
            group["tasks_blocked"] += 1
        elif bucket == "in_progress":
            group["tasks_in_progress"] += 1
        elif bucket == "ready":
            group["tasks_ready"] += 1
        elif bucket == "review":
            group["tasks_review"] += 1

        if _task_is_open(task):
            order_value = _task_order({"order": task.get("order")}, 999999)
            current_order = group.get("_next_task_order")
            if current_order is None or order_value < int(current_order):
                group["_next_task_order"] = order_value
                group["next_task_id"] = task_id or None
                group["next_task_title"] = task.get("title")
                group["next_task_status"] = task.get("status")

    for agent in agents:
        task_set_id = str(agent.get("task_set_id") or "").strip()
        if not task_set_id:
            continue
        group = group_for(task_set_id)
        group["agents"] += 1
        status = str(agent.get("status") or "").strip().lower()
        if status in {"blocked", "hold"}:
            group["blocked"] += 1
        elif status in {"completed", "done", "released"}:
            group["done"] += 1
        elif _is_active_task_claim(status) or agent.get("online"):
            group["active"] += 1

        task_id = str(agent.get("current_task_id") or "").strip()
        if task_id:
            group["current_task_ids"].add(task_id)
        claim_id = str(agent.get("claim_id") or "").strip()
        if claim_id:
            group["active_claim_ids"].add(claim_id)
        progress = _progress_pct(agent.get("progress_pct"))
        if progress is not None:
            group["_progress_values"].append(progress)
        status_text = str(agent.get("status_text") or agent.get("phase") or "").strip()
        if status_text and not group["status_text"]:
            group["status_text"] = status_text

    task_sets: list[dict[str, Any]] = []
    sorted_ids = sorted(groups, key=lambda raw: (int(groups[raw].get("sort_order", 999)), raw))
    for fallback_sequence, task_set_id in enumerate(sorted_ids, start=1):
        group = groups[task_set_id]
        sequence = int(group.get("sequence") or fallback_sequence)
        progress_values = group.pop("_progress_values")
        current_task_ids = sorted(group.pop("current_task_ids"))
        active_claim_ids = sorted(group.pop("active_claim_ids"))
        task_ids = sorted(group.pop("task_ids"))
        group.pop("_next_task_order", None)
        task_progress = (
            int(round((int(group["tasks_done"]) / int(group["tasks_total"])) * 100))
            if int(group.get("tasks_total", 0) or 0)
            else None
        )
        live_progress = int(round(sum(progress_values) / len(progress_values))) if progress_values else None
        group["current_task_ids"] = current_task_ids
        group["active_claim_ids"] = active_claim_ids
        group["task_ids"] = task_ids
        group["task_progress_pct"] = task_progress
        group["live_progress_pct"] = live_progress
        group["progress_pct"] = live_progress if live_progress is not None else task_progress
        group["status"] = _task_set_status(group)
        group["sequence"] = sequence
        group["alias_number"] = sequence
        group["alias_letter"] = _letter_alias(sequence)
        group["primary_alias"] = f"taskset {sequence}"
        group["letter_alias"] = f"taskset {group['alias_letter']}"
        group["slug_alias"] = _taskset_slug(task_set_id)
        group["aliases"] = _task_set_aliases(task_set_id, group, sequence)
        group["quick_aliases"] = [group["primary_alias"], group["letter_alias"], group["slug_alias"]]
        command_alias = _command_alias(sequence)
        group["commands"] = {
            "plan": f"python scripts/taskset_dispatcher.py plan {command_alias} --json",
            "start": f"python scripts/taskset_dispatcher.py start {command_alias} --json",
            "gate": f"python scripts/taskset_work_gate.py --task-set-id {task_set_id} --check",
        }
        task_sets.append(group)
    return task_sets


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
        ("task_claims", root / "agents" / "runtime" / "task_claims", "task_claim_directory", "runtime_api"),
        ("events", root / "agents" / "runtime" / "events", "event_directory", "append_only_runtime"),
        ("pane_events", root / "agents" / "runtime" / "pane_events", "pane_event_directory", "append_only_collaboration"),
        ("multipane_assurance", root / "agents" / "project" / "MULTIPANE-PROCESS-POLICY.yml", "assurance_policy", "read_only"),
        ("work_items", root / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json", "work_item_classification", "read_only"),
        ("status", root / "STATUS.md", "status_markdown", "agent_doc_workflow"),
        ("state_machines", root / "agents" / "project" / "STATE-MACHINES.yml", "state_machine_yaml", "schema_first_task"),
        ("roadmap", root / "agents" / "project" / "ROADMAP.md", "roadmap_markdown", "agent_doc_workflow"),
        ("planning", root / "agents" / "planning", "planning_outbox", "proposal_only"),
        ("ui_outbox", root / ".ui_outbox", "ui_command_outbox", "api_only"),
    )
    sources = [_source_entry(root, source_id, path, kind, now, boundary) for source_id, path, kind, boundary in source_specs]
    optional = {
        "messages_inbox",
        "messages_archive",
        "sessions",
        "task_claims",
        "events",
        "pane_events",
        "multipane_assurance",
        "work_items",
        "status",
        "state_machines",
        "roadmap",
        "planning",
    }
    gaps = [
        _gap(source["id"], source["path"], "optional runtime source is not present")
        for source in sources
        if source["id"] in optional and not source["fresh"]
    ]
    return sources, gaps


def _load_planning_json_records(root: Path, rel_dir: str) -> list[dict[str, Any]]:
    directory = root / rel_dir
    if not directory.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"id": path.stem, "status": "failed", "errors": ["planning record is malformed"]}
        if isinstance(payload, dict):
            payload.setdefault("id", path.stem)
            payload["source_path"] = _rel(root, path)
            payload["source_kind"] = "planning"
            records.append(payload)
    return records


def _collect_planning(root: Path) -> dict[str, Any]:
    scans = _load_planning_json_records(root, "agents/planning/scans")
    proposals = _load_planning_json_records(root, "agents/planning/outbox")
    requests = _load_planning_json_records(root, "agents/planning/requests")
    applied = _load_planning_json_records(root, "agents/planning/applied")
    drafts: list[dict[str, Any]] = []
    draft_dir = root / "agents" / "planning" / "drafts"
    if draft_dir.is_dir():
        for path in sorted(draft_dir.glob("*.md")):
            drafts.append(
                {
                    "id": path.stem,
                    "source_path": _rel(root, path),
                    "source_kind": "planning_draft",
                    "status": "draft",
                }
            )
    proposal_statuses: dict[str, int] = {}
    risk_tiers: dict[str, int] = {}
    for proposal in proposals:
        status = str(proposal.get("status") or "unknown")
        risk = str(proposal.get("risk_tier") or "unknown")
        proposal_statuses[status] = proposal_statuses.get(status, 0) + 1
        risk_tiers[risk] = risk_tiers.get(risk, 0) + 1
    return {
        "scan_reports": scans,
        "proposals": proposals,
        "requests": requests,
        "draft_tasks": drafts,
        "applied": applied,
        "summary": {
            "scan_count": len(scans),
            "proposal_count": len(proposals),
            "request_count": len(requests),
            "draft_task_count": len(drafts),
            "proposal_statuses": proposal_statuses,
            "risk_tiers": risk_tiers,
        },
    }


def _collect_multipane_assurance(
    root: Path,
    now: str,
    pane_events: list[dict[str, Any]],
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    try:
        from scripts import multipane_census
        from scripts import multipane_drift_gate
        from scripts import multipane_process_audit
    except ImportError as exc:
        warnings.append(_warning("multipane-assurance-import-error", "scripts", str(exc)))
        return {
            "status": "watch",
            "error": str(exc),
            "census": {},
            "process": {},
            "role_coverage": {},
            "drift": {},
            "event_summary": {},
        }
    try:
        census = multipane_census.build_report(root)
        process = multipane_process_audit.audit(root)
        drift = multipane_drift_gate.check_root(root, now=now)
    except Exception as exc:  # pragma: no cover - defensive UI adapter boundary
        warnings.append(_warning("multipane-assurance-read-error", "multipane_assurance", str(exc)))
        return {
            "status": "watch",
            "error": str(exc),
            "census": {},
            "process": {},
            "role_coverage": {},
            "drift": {},
            "event_summary": {},
        }
    statuses = {str(census.get("status")), str(process.get("status")), str(drift.get("status"))}
    status = "block" if "block" in statuses else "watch" if "watch" in statuses else "pass"
    return {
        "status": status,
        "generated_at": now,
        "census": census,
        "process": process,
        "role_coverage": process.get("observed", {}).get("roles", {}),
        "drift": drift,
        "event_summary": build_collaboration(pane_events).get("summary", {}),
        "source_paths": {
            "policy": "agents/project/MULTIPANE-PROCESS-POLICY.yml",
            "claims": "agents/runtime/task_claims",
            "pane_events": "agents/runtime/pane_events",
        },
    }


# Branch scanning shells out to git per agent branch, so cache overlays per
# root to keep the 4s console polling loop cheap.
INFLIGHT_TTL_SECONDS = 60.0
_INFLIGHT_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _empty_inflight(now: str, error: str) -> dict[str, Any]:
    return {
        "schema": "agent-runtime-inflight-overlay/v1",
        "generated_at": now,
        "base": None,
        "branches_scanned": 0,
        "records": [],
        "summary": {
            "divergent_tasks": 0,
            "divergent_records": 0,
            "branches_with_divergence": 0,
            "claimless": 0,
        },
        "error": error,
    }


def load_inflight(
    root: Path,
    now: str,
    warnings: list[dict[str, str]],
    *,
    ttl_seconds: float | None = None,
) -> dict[str, Any]:
    """Branch-side task status divergence vs main (cached per root)."""
    ttl = INFLIGHT_TTL_SECONDS if ttl_seconds is None else ttl_seconds
    key = str(Path(root).resolve())
    cached = _INFLIGHT_CACHE.get(key)
    if cached is not None and time.monotonic() - cached[0] < ttl:
        overlay = cached[1]
    else:
        try:
            from scripts import inflight_overlay

            overlay = inflight_overlay.build_overlay(Path(root))
        except Exception as exc:  # pragma: no cover - defensive adapter boundary
            overlay = _empty_inflight(now, str(exc))
        _INFLIGHT_CACHE[key] = (time.monotonic(), overlay)
    if overlay.get("error"):
        warnings.append(_warning("inflight-overlay-unavailable", "scripts/inflight_overlay.py", str(overlay["error"])))
    return overlay


# --- Work Explorer (TASK-AR-516) -------------------------------------------
# Read-only tree over the generated WORK-ITEM-CLASSIFICATION.json snapshot:
# Initiative -> Taskset -> Task -> Unit, with roll-ups computed from children
# only (stored progress fields are never trusted) plus facet values for
# client-side filtering and archived evidence/review refs per node.

WORK_FACET_KEYS = (
    "status",
    "owner",
    "taskset",
    "kind",
    "priority",
    "difficulty",
    "team",
    "model_tier",
    "origin",
    "component",
    "verification",
)
_WORK_EVIDENCE_LIST_KEYS = ("evidence_refs", "audit_log")
_WORK_EVIDENCE_SCALAR_KEYS = ("origin_ref", "unit_spec")
_WORK_DESCENDANT_EVIDENCE_LIMIT = 40


def _work_status_bucket(status: Any) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"completed", "complete", "done", "released", "verified", "archived", "완료"}:
        return "completed"
    if normalized in {"in_progress", "active", "working", "claimed", "assigned", "review", "waiting_review", "진행 중"}:
        return "in_progress"
    return "planned"


def _work_record_frontmatter(root: Path, rel_path: str, warnings: list[dict[str, str]]) -> dict[str, Any]:
    if not rel_path or not rel_path.endswith(".md") or rel_path in {"-", "BACKLOG-BOARD.md"}:
        return {}
    path = root / rel_path
    if not path.is_file():
        return {}
    try:
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    except OSError as exc:
        warnings.append(_warning("work-explorer-record-read-error", rel_path, str(exc)))
        return {}
    return meta


def _work_evidence_refs(meta: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in _WORK_EVIDENCE_LIST_KEYS:
        value = meta.get(key)
        if isinstance(value, list):
            refs.extend(str(item) for item in value)
    for key in _WORK_EVIDENCE_SCALAR_KEYS:
        value = meta.get(key)
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
    return _dedupe_strings(refs)


def _work_node_facets(node: dict[str, Any], meta: dict[str, Any], taskset_id: str | None) -> dict[str, str]:
    facets = {
        "status": str(node.get("status") or "") or "unknown",
        "kind": str(meta.get("kind") or node.get("level") or ""),
    }
    if taskset_id:
        facets["taskset"] = taskset_id
    for facet, key in (
        ("owner", "owner"),
        ("priority", "priority"),
        ("difficulty", "difficulty"),
        ("team", "team"),
        ("origin", "origin_type"),
        ("component", "component"),
        ("verification", "verification_status"),
    ):
        value = meta.get(key)
        if value not in (None, "", []):
            facets[facet] = str(value)
    model_tier = meta.get("worker_model_tier") or meta.get("model_tier")
    if model_tier not in (None, "", []):
        facets["model_tier"] = str(model_tier)
    return facets


def _work_number_sort_key(number: Any) -> tuple[Any, ...]:
    parts: list[int] = []
    for part in str(number or "").split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _empty_work_explorer(now: str, *, freshness: str, staleness_note: str, error: str | None = None) -> dict[str, Any]:
    return {
        "schema": "agent-runtime-work-explorer/v1",
        "generated_at": now,
        "source_path": WORK_ITEM_CLASSIFICATION_REL,
        "source_generated_at": None,
        "source_last_updated": None,
        "staleness_note": staleness_note,
        "freshness": freshness,
        "record_count": 0,
        "roots": [],
        "nodes": [],
        "facets": {key: [] for key in WORK_FACET_KEYS},
        "summary": {"levels": {}, "status_buckets": {}},
        "error": error,
    }


def load_work_explorer(root: Path, now: str, warnings: list[dict[str, str]]) -> dict[str, Any]:
    """Read-only Work Explorer tree built from WORK-ITEM-CLASSIFICATION.json."""
    path = root / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json"
    refresh_hint = "regenerate with python scripts/work_item_classifier.py --write"
    if not path.is_file():
        warnings.append(_warning("work-explorer-source-missing", WORK_ITEM_CLASSIFICATION_REL, refresh_hint))
        return _empty_work_explorer(now, freshness="missing", staleness_note=f"classification snapshot missing; {refresh_hint}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(_warning("work-explorer-source-error", WORK_ITEM_CLASSIFICATION_REL, str(exc)))
        return _empty_work_explorer(
            now,
            freshness="missing",
            staleness_note=f"classification snapshot unreadable; {refresh_hint}",
            error=str(exc),
        )
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        records = []

    nodes: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        node_id = str(record.get("id") or "").strip()
        if not node_id or node_id in nodes:
            continue
        nodes[node_id] = {
            "key": record.get("key"),
            "level": str(record.get("level") or ""),
            "number": str(record.get("number") or ""),
            "label": record.get("label"),
            "id": node_id,
            "title": record.get("title"),
            "path": str(record.get("path") or ""),
            "parent_id": str(record.get("parent_id") or ""),
            "status": str(record.get("status") or ""),
            "status_bucket": _work_status_bucket(record.get("status")),
            "children": [],
        }
        order.append(node_id)

    roots: list[str] = []
    for node_id in order:
        node = nodes[node_id]
        parent = nodes.get(node["parent_id"])
        if parent is not None and parent is not node:
            parent["children"].append(node_id)
        else:
            roots.append(node_id)
    for node_id in order:
        nodes[node_id]["children"].sort(key=lambda child_id: (_work_number_sort_key(nodes[child_id]["number"]), child_id))
    roots.sort(key=lambda node_id: (_work_number_sort_key(nodes[node_id]["number"]), node_id))

    # Per-node enrichment: depth and nearest taskset come from tree position,
    # facets/evidence come from the record's markdown frontmatter (read-only).
    meta_by_id = {node_id: _work_record_frontmatter(root, nodes[node_id]["path"], warnings) for node_id in order}
    visited: set[str] = set()
    stack: list[tuple[str, int, str | None]] = [(node_id, 0, None) for node_id in reversed(roots)]
    while stack:
        node_id, depth, taskset_id = stack.pop()
        if node_id in visited:
            continue
        visited.add(node_id)
        node = nodes[node_id]
        if node["level"] == "taskset":
            taskset_id = node_id
        node["depth"] = depth
        node["taskset_id"] = taskset_id
        node["facets"] = _work_node_facets(node, meta_by_id[node_id], taskset_id)
        node["evidence_refs"] = _work_evidence_refs(meta_by_id[node_id])
        for child_id in reversed(node["children"]):
            stack.append((child_id, depth + 1, taskset_id))
    for node_id in order:
        if node_id in visited:
            continue
        node = nodes[node_id]
        node["depth"] = 0
        node["taskset_id"] = node_id if node["level"] == "taskset" else None
        node["facets"] = _work_node_facets(node, meta_by_id[node_id], node["taskset_id"])
        node["evidence_refs"] = _work_evidence_refs(meta_by_id[node_id])

    # Roll-ups are computed from direct children only; stored progress fields
    # in the snapshot (e.g. progress_pct) are intentionally never read.
    for node_id in sorted(order, key=lambda value: -int(nodes[value].get("depth", 0))):
        node = nodes[node_id]
        rollup = {"total": 0, "completed": 0, "in_progress": 0, "planned": 0, "pct": None}
        descendant_refs: list[str] = []
        for child_id in node["children"]:
            child = nodes[child_id]
            rollup["total"] += 1
            rollup[child["status_bucket"]] += 1
            descendant_refs.extend(child.get("evidence_refs", []))
            descendant_refs.extend(child.get("descendant_evidence_refs", []))
        if rollup["total"]:
            rollup["pct"] = int(round(rollup["completed"] / rollup["total"] * 100))
        node["rollup"] = rollup
        node["descendant_evidence_refs"] = _dedupe_strings(descendant_refs)[:_WORK_DESCENDANT_EVIDENCE_LIMIT]

    facet_values: dict[str, set[str]] = {key: set() for key in WORK_FACET_KEYS}
    level_counts: dict[str, int] = {}
    bucket_counts: dict[str, int] = {}
    for node_id in order:
        node = nodes[node_id]
        level_counts[node["level"]] = level_counts.get(node["level"], 0) + 1
        bucket_counts[node["status_bucket"]] = bucket_counts.get(node["status_bucket"], 0) + 1
        for facet, value in node["facets"].items():
            if facet in facet_values and str(value).strip():
                facet_values[facet].add(str(value))

    mtime = _mtime_iso(path)
    source_generated_at = payload.get("generated_at") if isinstance(payload, dict) else None
    staleness_note = (
        f"read-only snapshot of {WORK_ITEM_CLASSIFICATION_REL} "
        f"(generated_at={source_generated_at}, file mtime={mtime}); {refresh_hint}"
    )
    sorted_order = sorted(order, key=lambda node_id: (_work_number_sort_key(nodes[node_id]["number"]), node_id))
    return {
        "schema": "agent-runtime-work-explorer/v1",
        "generated_at": now,
        "source_path": WORK_ITEM_CLASSIFICATION_REL,
        "source_generated_at": source_generated_at,
        "source_last_updated": mtime,
        "staleness_note": staleness_note,
        "freshness": "present",
        "record_count": len(order),
        "roots": roots,
        "nodes": [nodes[node_id] for node_id in sorted_order],
        "facets": {key: sorted(values) for key, values in facet_values.items()},
        "summary": {"levels": level_counts, "status_buckets": bucket_counts},
        "error": None,
    }


# --- Meeting Room (TASK-AR-361) --------------------------------------------
# Server-rendered shell for a "Meeting Room" where agents are dragged into
# participant slots, a topic/task is chosen, and a meeting (rounds) is planned.
# This resource is computed from runtime instances + tasks; it never mutates
# reviews/. The "start" affordance in the console emits a proposal-only
# meeting.plan command (scripts/meeting_room.py) which records the skeleton.

MEETING_TYPES = ("meeting", "seminar", "review")
MEETING_DEFAULT_ROUNDS = 3
MEETING_MIN_PARTICIPANTS = 2


def _meeting_available_agents(agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Distinct draggable agent cards keyed by role (fall back to id)."""
    cards: dict[str, dict[str, Any]] = {}
    for agent in agents:
        role = str(agent.get("role") or agent.get("id") or "").strip()
        if not role:
            continue
        card = cards.get(role)
        if card is None:
            cards[role] = {
                "id": role,
                "role": role,
                "display_name": str(agent.get("display_name") or role),
                "status": str(agent.get("status") or ""),
                "online": bool(agent.get("online")),
                "current_task_id": agent.get("current_task_id"),
                "provider": agent.get("provider"),
                "model": agent.get("model"),
                "instances": 1,
            }
        else:
            card["instances"] += 1
            if agent.get("online"):
                card["online"] = True
    return sorted(cards.values(), key=lambda card: (not card["online"], card["id"]))


def _meeting_topic_options(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Open tasks offered as meeting topics, plus a free-form option."""
    options: list[dict[str, Any]] = []
    for task in tasks:
        if not _task_is_open(task):
            continue
        options.append(
            {
                "id": str(task.get("id") or ""),
                "title": str(task.get("title") or task.get("id") or ""),
                "status": str(task.get("status") or ""),
                "task_set_id": task.get("task_set_id"),
            }
        )
    options.sort(key=lambda option: (str(option.get("task_set_id") or ""), option["id"]))
    return options


def build_meeting_room(
    agents: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    *,
    now: str,
) -> dict[str, Any]:
    available = _meeting_available_agents(agents)
    topics = _meeting_topic_options(tasks)
    return {
        "schema": "agent-runtime-meeting-room/v1",
        "generated_at": now,
        "available_agents": available,
        "participant_slots": [],
        "topic_options": topics,
        "config": {
            "topic": None,
            "task_id": None,
            "meeting_type": "meeting",
            "rounds": MEETING_DEFAULT_ROUNDS,
        },
        "meeting_types": list(MEETING_TYPES),
        "constraints": {
            "min_participants": MEETING_MIN_PARTICIPANTS,
            "min_rounds": 1,
            "default_rounds": MEETING_DEFAULT_ROUNDS,
        },
        "command": {
            "type": "runtime.request_meeting",
            "script": "python scripts/meeting_room.py plan",
            "records_to": "reviews/MEETING-<date>-<topic-slug>.md",
            "mutation_boundary": "proposal_only",
        },
        "available_count": len(available),
        "topic_count": len(topics),
    }


# --- Channels (TASK-AR-327) ------------------------------------------------
# Spectate agent-to-agent conversations as Slack/Discord-style channels and
# threads. Channels = one auto channel per taskset + #general + #governance.
# Threads = per-task. Each message carries a sender, a role color that maps to
# an existing semantic status token (consumed as var(--<token>) in the console),
# and an avatar initial. This resource is read-only and derived from messages +
# tasks + task_sets; it never mutates anything.

CHANNELS_SCHEMA = "agent-runtime-channels/v1"
GENERAL_CHANNEL_ID = "general"
GOVERNANCE_CHANNEL_ID = "governance"
_GOVERNANCE_INTENT_TOKENS = ("governance", "review", "meeting", "seminar", "gate", "approval", "consensus")
# Stable role -> semantic token mapping. Tokens already exist in BOTH :root and
# the dark theme block, so per-role coloring needs no new raw color literals.
_ROLE_COLOR_TOKENS = (
    "primary",
    "success",
    "warning",
    "danger",
    "violet",
    "teal",
    "amber",
    "info",
    "purple",
    "blue",
)


def _role_color_token(role: str) -> str:
    """Deterministic role -> semantic token name (stable across renders)."""
    key = str(role or "").strip().lower() or "unknown"
    fixed = {
        "owner": "primary",
        "lead-engineer": "blue",
        "lead_engineer": "blue",
        "planner": "violet",
        "qa": "warning",
        "governance": "danger",
        "ui": "subtle",
    }
    if key in fixed:
        return fixed[key]
    digest = sum(ord(char) for char in key)
    return _ROLE_COLOR_TOKENS[digest % len(_ROLE_COLOR_TOKENS)]


def _avatar_initials(name: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", " ", str(name or "")).strip()
    if not text:
        return "?"
    parts = text.split()
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def _channel_message(message: dict[str, Any]) -> dict[str, Any]:
    sender = str(message.get("from") or "unknown")
    return {
        "id": message.get("id"),
        "from": sender,
        "to": message.get("to"),
        "role": sender,
        "role_color": _role_color_token(sender),
        "avatar": _avatar_initials(sender),
        "task_id": message.get("task_id"),
        "intent": message.get("intent"),
        "type": message.get("type"),
        "status": message.get("status"),
        "ts": message.get("ts"),
        "body": message.get("body") or "",
        "thread_root_id": message.get("thread_root_id"),
        "source_path": message.get("source_path"),
    }


def _is_governance_message(message: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(message.get(key) or "").lower()
        for key in ("intent", "type", "to", "from")
    )
    return any(token in haystack for token in _GOVERNANCE_INTENT_TOKENS)


def build_channels(
    messages: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    task_sets: list[dict[str, Any]],
    *,
    now: str,
) -> dict[str, Any]:
    task_by_id = {str(task.get("id")): task for task in tasks if task.get("id")}
    taskset_of_task = {
        str(task.get("id")): str(task.get("task_set_id") or "")
        for task in tasks
        if task.get("id")
    }

    # Channel scaffolding: #general + #governance + one per taskset.
    channels: dict[str, dict[str, Any]] = {}

    def ensure_channel(channel_id: str, *, name: str, kind: str, task_set_id: str | None = None) -> dict[str, Any]:
        return channels.setdefault(
            channel_id,
            {
                "id": channel_id,
                "name": name,
                "kind": kind,
                "task_set_id": task_set_id,
                "threads": {},
                "message_count": 0,
                "last_ts": None,
            },
        )

    ensure_channel(GENERAL_CHANNEL_ID, name="#general", kind="general")
    ensure_channel(GOVERNANCE_CHANNEL_ID, name="#governance", kind="governance")
    for task_set in task_sets:
        ts_id = str(task_set.get("id") or "").strip()
        if not ts_id:
            continue
        ensure_channel(
            _taskset_slug(ts_id),
            name="#" + _taskset_slug(ts_id),
            kind="taskset",
            task_set_id=ts_id,
        )

    def ensure_thread(channel: dict[str, Any], thread_id: str, title: str, task_id: str | None) -> dict[str, Any]:
        return channel["threads"].setdefault(
            thread_id,
            {
                "id": thread_id,
                "title": title,
                "task_id": task_id,
                "messages": [],
                "last_ts": None,
            },
        )

    for message in messages:
        rendered = _channel_message(message)
        task_id = str(message.get("task_id") or "").strip()
        if task_id and task_id.lower() != "none":
            ts_id = taskset_of_task.get(task_id, "")
            channel_id = _taskset_slug(ts_id) if ts_id else GENERAL_CHANNEL_ID
            channel = ensure_channel(
                channel_id,
                name="#" + channel_id,
                kind="taskset" if ts_id else "general",
                task_set_id=ts_id or None,
            )
            task = task_by_id.get(task_id) or {}
            thread = ensure_thread(channel, task_id, str(task.get("title") or task_id), task_id)
        elif _is_governance_message(message):
            channel = channels[GOVERNANCE_CHANNEL_ID]
            thread = ensure_thread(channel, "governance", "Governance", None)
        else:
            channel = channels[GENERAL_CHANNEL_ID]
            thread = ensure_thread(channel, "general", "General", None)
        thread["messages"].append(rendered)
        ts_value = rendered.get("ts")
        if ts_value:
            if not thread["last_ts"] or str(ts_value) > str(thread["last_ts"]):
                thread["last_ts"] = ts_value
            if not channel["last_ts"] or str(ts_value) > str(channel["last_ts"]):
                channel["last_ts"] = ts_value
        channel["message_count"] += 1

    channel_list: list[dict[str, Any]] = []
    for channel in channels.values():
        threads = sorted(
            channel.pop("threads").values(),
            key=lambda thread: (str(thread.get("last_ts") or ""), str(thread.get("id"))),
            reverse=True,
        )
        channel["threads"] = threads
        channel["thread_count"] = len(threads)
        channel_list.append(channel)

    # Stable ordering: #general, #governance, then tasksets alphabetically.
    def channel_sort_key(channel: dict[str, Any]) -> tuple[int, str]:
        if channel["id"] == GENERAL_CHANNEL_ID:
            return (0, "")
        if channel["id"] == GOVERNANCE_CHANNEL_ID:
            return (1, "")
        return (2, channel["id"])

    channel_list.sort(key=channel_sort_key)

    return {
        "schema": CHANNELS_SCHEMA,
        "generated_at": now,
        "channels": channel_list,
        "channel_count": len(channel_list),
        "message_count": sum(channel["message_count"] for channel in channel_list),
        "role_color_tokens": list(_ROLE_COLOR_TOKENS),
        "owner_input": {
            "message_command": "runtime.call_agent",
            "slash_commands": [
                {"command": "/meeting", "type": "meeting.start", "usage": "/meeting <topic> @role @role"},
                {"command": "/seminar", "type": "seminar.start", "usage": "/seminar <topic>"},
            ],
            "mutation_boundary": "proposal_only",
        },
    }


TASKSETS_BOARD_SCHEMA = "agent-runtime-tasksets-board/v1"
_TASKSETS_BOARD_ACTIVITY_LIMIT = 5
_TASKSET_CHILD_STATUS_PHASES = {
    "plan": ("planned", "backlog", "todo", "proposed", "draft"),
    "work": ("in_progress", "active", "working", "claimed", "assigned", "started"),
    "review": ("review", "waiting_review", "in_review", "verifying", "verification"),
}


def _taskset_phase(status: Any, bucket: str) -> str:
    """Map a child status to a coarse plan/work/review/done phase chip."""
    normalized = str(status or "").strip().lower()
    if bucket == "completed":
        return "done"
    for phase, tokens in _TASKSET_CHILD_STATUS_PHASES.items():
        if normalized in tokens:
            return phase
    if bucket == "in_progress":
        return "work"
    return "plan"


TASKSET_COMPLETION_SCHEMA = "agent-runtime-taskset-completion/v1"


def _suggest_next_taskset(
    task_sets: list[dict[str, Any]],
    completed_id: str,
) -> dict[str, Any] | None:
    """Lowest-sequence taskset that still has open work, excluding the one
    that just completed. Surfaced as a suggestion that AWAITS owner approval;
    no work is auto-started."""
    candidates = [
        ts
        for ts in task_sets
        if str(ts.get("id") or "") != completed_id
        and str(ts.get("status") or "") != "completed"
        and int(ts.get("tasks_open", 0) or 0) > 0
    ]
    candidates.sort(key=lambda ts: int(ts.get("sequence") or 9999))
    if not candidates:
        return None
    nxt = candidates[0]
    return {
        "id": nxt.get("id"),
        "display_name": nxt.get("display_name"),
        "primary_alias": nxt.get("primary_alias"),
        "tasks_open": nxt.get("tasks_open"),
        "tasks_total": nxt.get("tasks_total"),
        "start_command": (nxt.get("commands") or {}).get("start"),
        "approval_state": "awaiting_approval",
    }


def build_taskset_completion(
    pane_events: list[dict[str, Any]],
    task_sets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Completion banner state for the Home / Tasksets view.

    Derived only from the latest ``taskset.completed`` pane event plus the
    computed task-set summary. When a taskset has just completed, the runtime
    boundary policy is STOP-and-report; the UI shows a completion banner and a
    next-taskset suggestion that explicitly awaits owner approval (no
    auto-start). When no completion event exists the banner is inactive.
    """
    completed_events = [
        event
        for event in pane_events
        if str(event.get("event") or event.get("type") or "") == "taskset.completed"
    ]
    completed_events.sort(key=lambda event: str(event.get("ts") or event.get("created_at") or ""))
    if not completed_events:
        return {"schema": TASKSET_COMPLETION_SCHEMA, "active": False}

    latest = completed_events[-1]
    completed_id = str(latest.get("task_set_id") or "").strip()
    info = next((ts for ts in task_sets if str(ts.get("id") or "") == completed_id), {})
    return {
        "schema": TASKSET_COMPLETION_SCHEMA,
        "active": True,
        "completed_task_set_id": completed_id,
        "completed_display_name": info.get("display_name") or completed_id,
        "completed_at": latest.get("ts") or latest.get("created_at"),
        "message": latest.get("message")
        or f"Taskset {completed_id} completed; stop and report.",
        "policy": "stop_and_report",
        "next_suggestion": _suggest_next_taskset(task_sets, completed_id),
    }


def build_tasksets_board(
    work_explorer: dict[str, Any],
    tasks: list[dict[str, Any]],
    events: list[dict[str, Any]],
    now: str,
) -> dict[str, Any]:
    """Taskset-grouped board derived from the classification hierarchy.

    Progress and status distribution are computed from child task state only;
    no stored progress field from the snapshot is read. Live task records and
    runtime events are joined by id for owner and recent-activity context.
    """
    nodes = {node["id"]: node for node in work_explorer.get("nodes", [])}
    task_by_id = {str(task.get("id")): task for task in tasks if task.get("id")}

    # Most recent runtime activity per task id (events are append-only logs).
    activity_by_task: dict[str, dict[str, Any]] = {}
    for event in events:
        task_id = str(event.get("task_id") or "").strip()
        if not task_id:
            continue
        ts = str(event.get("created_at") or event.get("ts") or "")
        existing = activity_by_task.get(task_id)
        if existing is None or ts > str(existing.get("ts") or ""):
            activity_by_task[task_id] = {
                "task_id": task_id,
                "event": event.get("event") or event.get("type") or "activity",
                "actor": event.get("role") or event.get("actor") or "",
                "ts": ts,
            }

    cards: list[dict[str, Any]] = []
    for node in work_explorer.get("nodes", []):
        if str(node.get("level") or "") != "taskset":
            continue
        taskset_id = node["id"]
        children: list[dict[str, Any]] = []
        status_distribution: dict[str, int] = {}
        assigned_agents: list[str] = []
        recent: list[dict[str, Any]] = []
        for child_id in node.get("children", []):
            child = nodes.get(child_id)
            if child is None:
                continue
            live = task_by_id.get(child_id, {})
            facets = child.get("facets", {})
            owner = live.get("owner_agent") or facets.get("owner") or ""
            priority = live.get("priority") or facets.get("priority") or ""
            bucket = child.get("status_bucket", "planned")
            status = child.get("status") or live.get("status") or ""
            child_rollup = child.get("rollup") or {}
            child_pct = child_rollup.get("pct")
            if child_pct is None:
                child_pct = 100 if bucket == "completed" else 0
            last_updated = live.get("last_updated") or live.get("updated_at")
            status_distribution[bucket] = status_distribution.get(bucket, 0) + 1
            if owner:
                assigned_agents.append(str(owner))
            activity = activity_by_task.get(child_id)
            if activity:
                recent.append(activity)
            children.append(
                {
                    "id": child_id,
                    "title": child.get("title") or live.get("title") or child_id,
                    "status": status,
                    "status_bucket": bucket,
                    "phase": _taskset_phase(status, bucket),
                    "owner": str(owner),
                    "priority": str(priority),
                    "progress_pct": child_pct,
                    "last_updated": last_updated,
                    "source_path": child.get("path") or live.get("source_path") or "",
                }
            )

        rollup = node.get("rollup") or {"total": 0, "completed": 0, "in_progress": 0, "planned": 0, "pct": None}
        recent.sort(key=lambda item: str(item.get("ts") or ""), reverse=True)
        cards.append(
            {
                "id": taskset_id,
                "title": node.get("title") or taskset_id,
                "status": node.get("status") or "",
                "status_bucket": node.get("status_bucket", "planned"),
                "initiative_id": node.get("parent_id") or "",
                "progress_pct": rollup.get("pct"),
                "progress": {"done": rollup.get("completed", 0), "total": rollup.get("total", 0)},
                "status_distribution": status_distribution,
                "assigned_agents": sorted(set(assigned_agents)),
                "recent_activity": recent[:_TASKSETS_BOARD_ACTIVITY_LIMIT],
                "source_path": node.get("path") or "",
                "children": children,
            }
        )

    cards.sort(key=lambda card: (_work_number_sort_key(nodes[card["id"]].get("number")), card["id"]))
    totals = {
        "tasksets": len(cards),
        "tasks": sum(card["progress"]["total"] for card in cards),
        "completed": sum(card["progress"]["done"] for card in cards),
    }
    return {
        "schema": TASKSETS_BOARD_SCHEMA,
        "generated_at": now,
        "source_path": WORK_ITEM_CLASSIFICATION_REL,
        "source_generated_at": work_explorer.get("source_generated_at"),
        "source_last_updated": work_explorer.get("source_last_updated"),
        "staleness_note": work_explorer.get("staleness_note", ""),
        "freshness": work_explorer.get("freshness", "missing"),
        "create_command": "task.create",
        "totals": totals,
        "cards": cards,
    }


# --- Roadmap Timeline (TASK-AR-325) ----------------------------------------
# A computed-only Vision -> Milestone -> Release timeline. Milestones come from
# ROADMAP.md, the vision header from VISION.md, releases from the recorded
# release-decision YAMLs. Each milestone is linked to the initiatives/tasksets
# whose ids appear in its title and gets a status roll-up computed from the
# work-explorer hierarchy. Nothing here mutates state; every field is derived
# from existing source files joined by id.

ROADMAP_TIMELINE_SCHEMA = "agent-runtime-roadmap-timeline/v1"
RELEASE_DECISION_GLOB = "agents/project/release/RELEASE-DECISION-*.yml"
_WORK_ID_PATTERN = re.compile(r"\b(?:TASKSET-AR-[A-Z0-9-]+|INIT-AR-[A-Z0-9-]+|TASK-AR-\d+)\b")


def _roadmap_vision(root: Path, now: str) -> dict[str, Any]:
    """Top-of-timeline vision node parsed from VISION.md (computed-only)."""
    path = root / "agents" / "project" / "VISION.md"
    node: dict[str, Any] = {
        "tier": "vision",
        "title": "Vision",
        "statement": None,
        "problem": None,
        "success_metric": None,
        "source_path": _rel(root, path),
        "source_kind": "vision_markdown",
        "freshness": _path_freshness(path),
        "last_updated": _mtime_iso(path),
    }
    if not path.exists():
        return node
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        node["freshness"] = "missing"
        return node
    node["statement"] = _first_sentence(_section_text(text, "Vision")) or None
    node["problem"] = _first_sentence(_section_text(text, "Problem")) or None
    node["success_metric"] = _first_sentence(_section_text(text, "Success metric")) or None
    node["source"] = _source_metadata(root, path, "vision_markdown", now)
    return node


def _roadmap_linked_work(
    title: str,
    nodes_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Resolve work ids mentioned in a milestone title to explorer nodes.

    Returns the deduped linked-work records plus a status roll-up computed from
    the linked nodes (and their explorer roll-ups for taskset/initiative ids).
    """
    linked: list[dict[str, Any]] = []
    seen: set[str] = set()
    rollup = {"linked": 0, "completed": 0, "in_progress": 0, "planned": 0, "tasks_total": 0, "tasks_completed": 0}
    for work_id in _WORK_ID_PATTERN.findall(title or ""):
        if work_id in seen:
            continue
        seen.add(work_id)
        node = nodes_by_id.get(work_id)
        if node is None:
            linked.append({"id": work_id, "level": "unknown", "title": work_id, "status_bucket": "planned", "resolved": False})
            rollup["linked"] += 1
            rollup["planned"] += 1
            continue
        bucket = node.get("status_bucket", "planned")
        node_rollup = node.get("rollup") or {}
        linked.append(
            {
                "id": work_id,
                "level": node.get("level") or "",
                "title": node.get("title") or work_id,
                "status": node.get("status") or "",
                "status_bucket": bucket,
                "source_path": node.get("path") or "",
                "progress_pct": node_rollup.get("pct"),
                "resolved": True,
            }
        )
        rollup["linked"] += 1
        rollup[bucket] = rollup.get(bucket, 0) + 1
        total = int(node_rollup.get("total") or 0)
        completed = int(node_rollup.get("completed") or 0)
        if total:
            rollup["tasks_total"] += total
            rollup["tasks_completed"] += completed
        elif node.get("level") == "task":
            rollup["tasks_total"] += 1
            rollup["tasks_completed"] += 1 if bucket == "completed" else 0
    if rollup["tasks_total"]:
        rollup["pct"] = int(round(rollup["tasks_completed"] / rollup["tasks_total"] * 100))
    elif rollup["linked"]:
        rollup["pct"] = int(round(rollup["completed"] / rollup["linked"] * 100))
    else:
        rollup["pct"] = None
    return linked, rollup


def _roadmap_releases(root: Path, now: str, warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Release-tier nodes parsed from recorded release-decision YAMLs."""
    releases: list[dict[str, Any]] = []
    for path in sorted(root.glob(RELEASE_DECISION_GLOB)):
        rel_path = _rel(root, path)
        try:
            meta, _ = parse_frontmatter("---\n" + path.read_text(encoding="utf-8") + "\n---\n")
        except OSError as exc:
            warnings.append(_warning("roadmap-release-read-error", rel_path, str(exc)))
            continue
        version = str(meta.get("target_version") or "").strip()
        status = str(meta.get("status") or "").strip()
        releases.append(
            {
                "tier": "release",
                "id": str(meta.get("target_tag") or version or path.stem),
                "version": version,
                "tag": str(meta.get("target_tag") or "").strip(),
                "title": f"Release {meta.get('target_tag') or version or path.stem}",
                "status": status,
                "status_bucket": _work_status_bucket("completed" if status in {"released", "published"} else status),
                "criticality": str(meta.get("criticality") or "").strip(),
                "owner_required": bool(meta.get("owner_required")),
                "approved_by": str(meta.get("approved_by") or "").strip(),
                "date": str(meta.get("decision_date") or "").strip() or None,
                "source_path": rel_path,
                "source_kind": "release_decision_yaml",
                "source": _source_metadata(root, path, "release_decision_yaml", now),
                "last_updated": _mtime_iso(path),
            }
        )
    releases.sort(key=lambda item: (str(item.get("version") or ""), item["id"]))
    return releases


def build_roadmap_timeline(
    roadmap: dict[str, Any],
    work_explorer: dict[str, Any],
    root: Path,
    now: str,
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    """Vision -> Milestone -> Release vertical timeline (computed-only).

    Milestones are reused from the flat roadmap parser; each one is enriched
    with the initiatives/tasksets/tasks named in its title and a status
    roll-up derived from the work-explorer hierarchy. No stored progress is
    trusted - roll-ups come from joined explorer nodes only.
    """
    nodes_by_id = {str(node.get("id")): node for node in work_explorer.get("nodes", []) if node.get("id")}
    vision = _roadmap_vision(root, now)

    milestones: list[dict[str, Any]] = []
    for index, item in enumerate(roadmap.get("milestones", [])):
        title = str(item.get("title") or "")
        linked, rollup = _roadmap_linked_work(title, nodes_by_id)
        milestones.append(
            {
                "tier": "milestone",
                "id": f"milestone-{index + 1}",
                "date": item.get("date"),
                "title": title,
                "done": bool(item.get("done")),
                "status_bucket": "completed" if item.get("done") else ("in_progress" if rollup.get("in_progress") else "planned"),
                "linked_work": linked,
                "rollup": rollup,
                "source_path": roadmap.get("source_path") or "agents/project/ROADMAP.md",
            }
        )
    # Timeline order: dated milestones ascending by date, undated last but stable.
    milestones.sort(key=lambda entry: (str(entry.get("date") or "9999-99-99"), entry["id"]))

    releases = _roadmap_releases(root, now, warnings)

    summary = {
        "milestones": len(milestones),
        "milestones_done": sum(1 for entry in milestones if entry["done"]),
        "milestones_open": sum(1 for entry in milestones if not entry["done"]),
        "linked_work": sum(entry["rollup"]["linked"] for entry in milestones),
        "releases": len(releases),
    }
    return {
        "schema": ROADMAP_TIMELINE_SCHEMA,
        "generated_at": now,
        "phase": roadmap.get("phase"),
        "next_milestone": roadmap.get("next_milestone"),
        "vision": vision,
        "milestones": milestones,
        "releases": releases,
        "summary": summary,
        "source_path": roadmap.get("source_path") or "agents/project/ROADMAP.md",
        "freshness": roadmap.get("freshness", "missing"),
        "last_updated": roadmap.get("last_updated"),
    }


# --- Team / Agent RPG presence (TASK-AR-324) -------------------------------
# Team -> Agent organisation hierarchy rendered as online-RPG-guild character
# cards. The card "level" and "XP" are DERIVED on every build from completed
# task/unit claim counts; they are computed-only and never read from a stored
# field. This means flipping a claim status to "completed" moves a card's XP,
# while editing any stored instance/claim attribute leaves the bar untouched.

TEAM_AGENTS_SCHEMA = "agent-runtime-team-agents/v1"
_TEAM_AGENTS_ACTIVITY_LIMIT = 5
_XP_PER_COMPLETED_TASK = 100
_XP_PER_COMPLETED_UNIT = 20
_XP_PER_LEVEL = 100  # level n requires (n-1)^2 * _XP_PER_LEVEL total XP
_AGENT_ONLINE_CLAIM_STATES = {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}


def _team_agent_level(xp: int) -> dict[str, int]:
    """Derive an RPG level + within-level progress from a raw XP total.

    Levels follow a widening quadratic curve: level L starts at
    (L-1)^2 * _XP_PER_LEVEL XP. Everything here is a pure function of `xp`
    so the bar only moves when the completed-work count (hence xp) moves.
    """
    safe_xp = max(0, int(xp))
    level = 1
    while (level * level) * _XP_PER_LEVEL <= safe_xp:
        level += 1
    floor_xp = ((level - 1) * (level - 1)) * _XP_PER_LEVEL
    ceil_xp = (level * level) * _XP_PER_LEVEL
    span = max(1, ceil_xp - floor_xp)
    into_level = safe_xp - floor_xp
    pct = max(0, min(100, round((into_level / span) * 100)))
    return {
        "level": level,
        "xp": safe_xp,
        "xp_into_level": into_level,
        "xp_for_next": ceil_xp - safe_xp,
        "xp_level_floor": floor_xp,
        "xp_level_ceiling": ceil_xp,
        "xp_pct": pct,
    }


def _load_instances(root: Path, now: str, warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Read raw agent-instance spawn records (agents/runtime/instances/*.json)."""
    instances: list[dict[str, Any]] = []
    for path in sorted(root.glob(INSTANCE_GLOB)):
        rel_path = _rel(root, path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(_warning("instance-json-parse-error", rel_path, str(exc)))
            continue
        except OSError as exc:
            warnings.append(_warning("instance-read-error", rel_path, str(exc)))
            continue
        if not isinstance(payload, dict):
            warnings.append(_warning("instance-invalid-record", rel_path, "instance payload is not an object"))
            continue
        record = dict(payload)
        record["source_path"] = rel_path
        record["last_updated"] = _mtime_iso(path)
        instances.append(record)
    return instances


def build_team_agents(
    root: Path,
    instances: list[dict[str, Any]],
    agents: list[dict[str, Any]],
    task_claims: list[dict[str, Any]],
    events: list[dict[str, Any]],
    now: str,
) -> dict[str, Any]:
    """Team -> Agent hierarchy with per-agent RPG presence character cards.

    Cards join three runtime sources by agent_instance_id: instance spawn
    records (identity/role/model/skills), task claims (current claim +
    completed lifetime counts), and the active agent view (live online state).
    Level/XP are computed from completed-work counts only.
    """
    # Lifetime + current claim aggregation keyed by instance id.
    completed_tasks: dict[str, set[str]] = {}
    completed_units: dict[str, set[str]] = {}
    current_claim_by_instance: dict[str, dict[str, Any]] = {}
    for claim in task_claims:
        instance_id = str(claim.get("agent_instance_id") or "").strip()
        if not instance_id:
            continue
        status = str(claim.get("status") or "").strip().lower()
        if status == "completed":
            task_id = str(claim.get("task_id") or claim.get("claim_id") or "")
            completed_tasks.setdefault(instance_id, set()).add(task_id)
            unit_id = str(claim.get("unit_id") or "").strip()
            if unit_id:
                completed_units.setdefault(instance_id, set()).add(unit_id)
        if status in _AGENT_ONLINE_CLAIM_STATES:
            existing = current_claim_by_instance.get(instance_id)
            ts = str(claim.get("last_heartbeat") or claim.get("claimed_at") or "")
            if existing is None or ts > str(existing.get("_ts") or ""):
                current_claim_by_instance[instance_id] = {**claim, "_ts": ts}

    # Live online state from the active-agent view (task-claim derived).
    agent_by_instance = {str(agent.get("id") or ""): agent for agent in agents}

    # Most recent runtime activity per role (for recent-activity feed fallback).
    activity_by_role: dict[str, dict[str, Any]] = {}
    for event in events:
        role = str(event.get("role") or event.get("actor") or "").strip()
        if not role:
            continue
        ts = str(event.get("created_at") or event.get("ts") or "")
        existing = activity_by_role.get(role)
        if existing is None or ts > str(existing.get("ts") or ""):
            activity_by_role[role] = {
                "role": role,
                "event": event.get("event") or event.get("type") or "activity",
                "task_id": event.get("task_id") or "",
                "ts": ts,
            }

    teams: dict[str, dict[str, Any]] = {}
    for instance in instances:
        instance_id = str(instance.get("agent_instance_id") or instance.get("id") or "").strip()
        if not instance_id:
            continue
        role = str(instance.get("role") or "unknown").strip() or "unknown"
        team_id = str(instance.get("team_id") or "unassigned").strip() or "unassigned"
        callsign = str(instance.get("callsign") or instance.get("display_name") or instance_id)
        skill_versions = instance.get("skill_versions") if isinstance(instance.get("skill_versions"), dict) else {}

        done_tasks = sorted(completed_tasks.get(instance_id, set()))
        done_units = sorted(completed_units.get(instance_id, set()))
        xp_total = len(done_tasks) * _XP_PER_COMPLETED_TASK + len(done_units) * _XP_PER_COMPLETED_UNIT
        rpg = _team_agent_level(xp_total)

        claim = current_claim_by_instance.get(instance_id)
        live = agent_by_instance.get(instance_id, {})
        online = bool(live.get("online")) or claim is not None
        if claim is not None:
            presence = "in_meeting" if str(claim.get("mode") or "") == "meeting" else "working"
            if str(claim.get("status") or "").lower() in {"review", "waiting_review"}:
                presence = "reviewing"
        elif online:
            presence = "online"
        else:
            presence = "offline"

        current_claim = None
        if claim is not None:
            current_claim = {
                "claim_id": claim.get("claim_id"),
                "task_id": claim.get("task_id"),
                "task_set_id": claim.get("task_set_id"),
                "status": claim.get("status"),
                "phase": claim.get("phase"),
                "progress_pct": claim.get("progress_pct"),
                "status_text": claim.get("status_text"),
                "worktree_path": claim.get("worktree_path"),
                "branch": claim.get("branch"),
            }

        activity = activity_by_role.get(role)
        recent_activity = [activity] if activity else []

        avatar = "".join(part[:1] for part in role.replace("-", " ").replace("_", " ").split())[:2].upper() or "AG"
        card = {
            "id": instance_id,
            "role": role,
            "callsign": callsign,
            "display_name": str(instance.get("display_name") or callsign),
            "avatar": avatar,
            "model": instance.get("model") or "",
            "model_tier": instance.get("model_tier") or "",
            "provider": instance.get("provider") or "",
            "skill_versions": skill_versions,
            "skill_count": len(skill_versions),
            "presence": presence,
            "online": online,
            "current_claim": current_claim,
            "current_task_id": (claim or {}).get("task_id") if claim else None,
            "lifetime": {
                "completed_tasks": len(done_tasks),
                "completed_units": len(done_units),
                "completed_task_ids": done_tasks,
            },
            "level": rpg["level"],
            "xp": rpg["xp"],
            "xp_into_level": rpg["xp_into_level"],
            "xp_for_next": rpg["xp_for_next"],
            "xp_pct": rpg["xp_pct"],
            "recent_activity": recent_activity[:_TEAM_AGENTS_ACTIVITY_LIMIT],
            "spawned_at": instance.get("spawned_at") or instance.get("created_at"),
            "source_path": instance.get("source_path") or "",
            "last_updated": instance.get("last_updated"),
        }

        team = teams.get(team_id)
        if team is None:
            team = teams[team_id] = {
                "id": team_id,
                "team_id": team_id,
                "agents": [],
                "roles": {},
            }
        team["agents"].append(card)
        team["roles"][role] = team["roles"].get(role, 0) + 1

    team_groups: list[dict[str, Any]] = []
    for team_id in sorted(teams):
        team = teams[team_id]
        members = sorted(team["agents"], key=lambda card: (not card["online"], card["role"], card["id"]))
        online_count = sum(1 for card in members if card["online"])
        team_groups.append(
            {
                "id": team_id,
                "team_id": team_id,
                "agent_count": len(members),
                "online_count": online_count,
                "role_distribution": dict(sorted(team["roles"].items())),
                "agents": members,
            }
        )

    totals = {
        "teams": len(team_groups),
        "agents": sum(group["agent_count"] for group in team_groups),
        "online": sum(group["online_count"] for group in team_groups),
    }
    return {
        "schema": TEAM_AGENTS_SCHEMA,
        "generated_at": now,
        "source_glob": INSTANCE_GLOB,
        "xp_model": {
            "per_completed_task": _XP_PER_COMPLETED_TASK,
            "per_completed_unit": _XP_PER_COMPLETED_UNIT,
            "note": "level/xp are computed from completed claim counts only",
        },
        "totals": totals,
        "teams": team_groups,
    }


# --- Subtask + dependency model (TASK-AR-330) ------------------------------
# A single read-only derivation of the task hierarchy (parent_id) and the
# blocks/blocked_by dependency graph. The dependency *edges* computed here are
# the one source of truth shared by the board, the timeline (Gantt) and the
# dependency graph view, so a dependency renders identically in all three. The
# same edge set feeds the cycle-detection gate (scripts/dependency_cycle_gate.py)
# so a cycle the UI surfaces is exactly the cycle the gate warns on.

DEPENDENCY_GRAPH_SCHEMA = "agent-runtime-dependency-graph/v1"
TIMELINE_SCHEMA = "agent-runtime-timeline/v1"
# Bar length when a task carries no explicit start/end span (in "units").
_TIMELINE_DEFAULT_SPAN = 1


def _normalize_dependency_edges(tasks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Build the canonical directed blocker edges from task frontmatter.

    Edge direction is *blocker -> blocked* (the arrow points at the work that
    must wait). Both ``blocks`` (this task blocks X) and ``blocked_by`` (this
    task waits on X) are folded into the same edge set so the two declaration
    styles agree. Edges are deduped on (from, to). Returns the edge list plus a
    by-id index of the known task nodes for convenience.
    """
    index: dict[str, dict[str, Any]] = {}
    for task in tasks:
        task_id = str(task.get("id") or "").strip()
        if task_id:
            index[task_id] = task

    seen: set[tuple[str, str]] = set()
    edges: list[dict[str, Any]] = []

    def add_edge(blocker: str, blocked: str, declared_on: str, via: str) -> None:
        blocker = str(blocker or "").strip()
        blocked = str(blocked or "").strip()
        if not blocker or not blocked or blocker == blocked:
            return
        key = (blocker, blocked)
        if key in seen:
            return
        seen.add(key)
        edges.append(
            {
                "id": f"dep:{blocker}->{blocked}",
                "from": blocker,
                "to": blocked,
                "kind": "dependency",
                "declared_on": declared_on,
                "via": via,
                "from_known": blocker in index,
                "to_known": blocked in index,
            }
        )

    for task in tasks:
        task_id = str(task.get("id") or "").strip()
        if not task_id:
            continue
        for blocked in task.get("blocks") or []:
            add_edge(task_id, str(blocked), declared_on=task_id, via="blocks")
        for blocker in task.get("blocked_by") or []:
            add_edge(str(blocker), task_id, declared_on=task_id, via="blocked_by")
    return edges, index


def detect_dependency_cycles(edges: list[dict[str, Any]]) -> list[list[str]]:
    """Return dependency cycles as ordered node-id chains (closing node repeated).

    Pure function over the canonical edge set so the gate and the UI agree. When
    no blocker edges exist the result is always ``[]`` (no-op safe), which keeps
    the cycle gate silent on a repo that has not adopted blocks/blocked_by yet.
    """
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        adjacency.setdefault(str(edge["from"]), []).append(str(edge["to"]))
    for node in list(adjacency):
        adjacency[node].sort()

    cycles: list[list[str]] = []
    seen_signatures: set[tuple[str, ...]] = set()
    WHITE, GREY, BLACK = 0, 1, 2
    color: dict[str, int] = {}

    def _record(cycle: list[str]) -> None:
        # Canonicalize so the same loop discovered from different entry points
        # is only reported once.
        core = cycle[:-1]
        if not core:
            return
        rotation = min(range(len(core)), key=lambda i: core[i])
        normalized = core[rotation:] + core[:rotation]
        signature = tuple(normalized)
        if signature in seen_signatures:
            return
        seen_signatures.add(signature)
        cycles.append(normalized + [normalized[0]])

    def visit(node: str, stack: list[str]) -> None:
        color[node] = GREY
        stack.append(node)
        for neighbour in adjacency.get(node, []):
            state = color.get(neighbour, WHITE)
            if state == WHITE:
                visit(neighbour, stack)
            elif state == GREY:
                # Back edge: slice the live stack from the neighbour onwards.
                start = stack.index(neighbour)
                _record(stack[start:] + [neighbour])
        stack.pop()
        color[node] = BLACK

    for node in sorted(adjacency):
        if color.get(node, WHITE) == WHITE:
            visit(node, [])
    return cycles


def build_dependency_graph(tasks: list[dict[str, Any]], now: str) -> dict[str, Any]:
    """Dependency graph view sharing the board/timeline edge derivation.

    Nodes mirror the Live Map shape (id/kind/label + status) so the same
    rendering primitives apply; ``parent`` edges express the subtask hierarchy
    and ``dependency`` edges express blocks/blocked_by. ``cycles`` lists any
    circular blocker chains so the graph and the gate stay consistent.
    """
    edges, index = _normalize_dependency_edges(tasks)
    nodes: dict[str, dict[str, Any]] = {}

    def add_node(node_id: str, kind: str, label: str | None = None, **extra: Any) -> None:
        node_id = str(node_id or "").strip()
        if not node_id or node_id in nodes:
            if node_id in nodes and label and nodes[node_id].get("label") in (None, node_id):
                nodes[node_id]["label"] = label
            return
        node = {"id": node_id, "kind": kind, "label": label or node_id}
        for name, value in extra.items():
            if value not in (None, ""):
                node[name] = value
        nodes[node_id] = node

    parent_edges: list[dict[str, Any]] = []
    parent_seen: set[tuple[str, str]] = set()
    for task in tasks:
        task_id = str(task.get("id") or "").strip()
        if not task_id:
            continue
        add_node(
            task_id,
            "task",
            str(task.get("title") or task_id),
            status=str(task.get("status") or ""),
            status_bucket=_work_status_bucket(task.get("status")),
            task_set_id=task.get("task_set_id"),
            parent_id=task.get("parent_id") or "",
            source_path=task.get("source_path"),
        )
        parent_id = str(task.get("parent_id") or "").strip()
        if parent_id:
            add_node(parent_id, "parent", parent_id)
            key = (parent_id, task_id)
            if key not in parent_seen:
                parent_seen.add(key)
                parent_edges.append(
                    {
                        "id": f"parent:{parent_id}->{task_id}",
                        "from": parent_id,
                        "to": task_id,
                        "kind": "parent",
                    }
                )

    # Ensure dependency endpoints exist even if the referenced task is missing
    # (a dangling reference still has to render and feed cycle detection).
    for edge in edges:
        for endpoint in (edge["from"], edge["to"]):
            if endpoint not in nodes:
                add_node(endpoint, "missing", endpoint, missing=True)

    cycles = detect_dependency_cycles(edges)
    cycle_node_ids: set[str] = set()
    cycle_edge_ids: set[str] = set()
    for cycle in cycles:
        for node_id in cycle:
            cycle_node_ids.add(node_id)
        for a, b in zip(cycle, cycle[1:]):
            cycle_edge_ids.add(f"dep:{a}->{b}")
    for node in nodes.values():
        if node["id"] in cycle_node_ids:
            node["in_cycle"] = True
    for edge in edges:
        if edge["id"] in cycle_edge_ids:
            edge["in_cycle"] = True

    all_edges = parent_edges + edges
    return {
        "schema": DEPENDENCY_GRAPH_SCHEMA,
        "generated_at": now,
        "nodes": sorted(nodes.values(), key=lambda item: (item["kind"], item["id"])),
        "edges": all_edges,
        "cycles": cycles,
        "has_cycle": bool(cycles),
        "totals": {
            "nodes": len(nodes),
            "edges": len(all_edges),
            "dependency_edges": len(edges),
            "parent_edges": len(parent_edges),
            "cycles": len(cycles),
            "missing_refs": sum(1 for node in nodes.values() if node.get("missing")),
        },
    }


def build_timeline(tasks: list[dict[str, Any]], now: str) -> dict[str, Any]:
    """Asana/ClickUp-style horizontal-bar timeline grouped by taskset.

    Each task becomes a positioned bar inside its taskset lane; lanes are
    ordered by task ``order``. Dependency arrows reuse the same canonical edge
    set as the graph (blocker -> blocked) so a dependency line on the timeline
    matches the graph and the gate. Bar positions are an integer "unit" grid
    derived from task order within its lane (read-only; no stored geometry).
    """
    edges, _index = _normalize_dependency_edges(tasks)
    groups: dict[str, dict[str, Any]] = {}
    group_order: list[str] = []
    bar_index: dict[str, dict[str, Any]] = {}

    for task in tasks:
        task_id = str(task.get("id") or "").strip()
        if not task_id:
            continue
        taskset_id = str(task.get("task_set_id") or task.get("parent_id") or "").strip() or "UNGROUPED"
        group = groups.get(taskset_id)
        if group is None:
            group = groups[taskset_id] = {
                "id": taskset_id,
                "label": taskset_id,
                "bars": [],
            }
            group_order.append(taskset_id)
        column = len(group["bars"])
        bar = {
            "id": task_id,
            "label": str(task.get("title") or task_id),
            "status": str(task.get("status") or ""),
            "status_bucket": _work_status_bucket(task.get("status")),
            "taskset_id": taskset_id,
            "lane": column,
            "start": column,
            "span": _TIMELINE_DEFAULT_SPAN,
            "blocks": list(task.get("blocks") or []),
            "blocked_by": list(task.get("blocked_by") or []),
            "source_path": task.get("source_path"),
        }
        group["bars"].append(bar)
        bar_index[task_id] = bar

    cycles = detect_dependency_cycles(edges)
    cycle_edge_ids: set[str] = set()
    for cycle in cycles:
        for a, b in zip(cycle, cycle[1:]):
            cycle_edge_ids.add(f"dep:{a}->{b}")

    arrows: list[dict[str, Any]] = []
    for edge in edges:
        arrows.append(
            {
                "id": edge["id"],
                "from": edge["from"],
                "to": edge["to"],
                "kind": "dependency",
                "from_known": edge["from"] in bar_index,
                "to_known": edge["to"] in bar_index,
                "in_cycle": edge["id"] in cycle_edge_ids,
            }
        )

    lanes = [groups[group_id] for group_id in group_order]
    max_units = max((len(group["bars"]) for group in lanes), default=0)
    return {
        "schema": TIMELINE_SCHEMA,
        "generated_at": now,
        "lanes": lanes,
        "arrows": arrows,
        "cycles": cycles,
        "has_cycle": bool(cycles),
        "units": max_units,
        "totals": {
            "lanes": len(lanes),
            "bars": sum(len(group["bars"]) for group in lanes),
            "arrows": len(arrows),
            "cycles": len(cycles),
        },
    }


def build_state(root: Path | str, now: str | None = None) -> dict[str, Any]:
    root_path = Path(root).resolve()
    generated_at = now or _now_iso()
    warnings: list[dict[str, str]] = []
    sources, gaps = _collect_sources_and_gaps(root_path, generated_at)
    tasks = load_tasks(root_path, generated_at, warnings)
    events = load_events(root_path, generated_at, warnings)
    pane_events = load_pane_events(root_path, generated_at, warnings)
    task_claims = load_task_claims(root_path, generated_at, warnings)
    agents = load_agents(root_path, generated_at, events, warnings, task_claims)
    task_sets = build_task_sets(agents, tasks=tasks, root=root_path, warnings=warnings)
    messages = load_messages(root_path, generated_at, warnings)
    goals = load_goals(root_path, generated_at)
    commands = ui_commands.list_commands(root_path)
    errors = derive_errors(events)
    evidence = derive_evidence(events, messages)
    enrich_tasks_with_evidence(tasks, evidence)
    replay = build_replay(events, messages)
    graph = build_graph(tasks, agents, messages, events)
    state_machines = load_state_machines(root_path, tasks, agents, generated_at)
    roadmap = load_roadmap(root_path, generated_at)
    planning = _collect_planning(root_path)
    collaboration = build_collaboration(pane_events)
    multipane_assurance = _collect_multipane_assurance(root_path, generated_at, pane_events, warnings)
    inflight = load_inflight(root_path, generated_at, warnings)
    work_explorer = load_work_explorer(root_path, generated_at, warnings)
    meeting_room = build_meeting_room(agents, tasks, now=generated_at)
    channels = build_channels(messages, tasks, task_sets, now=generated_at)
    tasksets_board = build_tasksets_board(work_explorer, tasks, events, generated_at)
    taskset_completion = build_taskset_completion(pane_events, task_sets)
    roadmap_timeline = build_roadmap_timeline(roadmap, work_explorer, root_path, generated_at, warnings)
    instances = _load_instances(root_path, generated_at, warnings)
    team_agents = build_team_agents(root_path, instances, agents, task_claims, events, generated_at)
    live_map = build_live_map(tasks, agents, messages, team_agents, generated_at)
    dependency_graph = build_dependency_graph(tasks, generated_at)
    timeline = build_timeline(tasks, generated_at)
    return {
        "generated_at": generated_at,
        "sources": sources,
        "tasks": tasks,
        "agents": agents,
        "task_sets": task_sets,
        "collaboration": collaboration,
        "task_claims": task_claims,
        "multipane_assurance": multipane_assurance,
        "inflight": inflight,
        "work_explorer": work_explorer,
        "meeting_room": meeting_room,
        "channels": channels,
        "tasksets_board": tasksets_board,
        "taskset_completion": taskset_completion,
        "team_agents": team_agents,
        "messages": messages,
        "events": events,
        "goals": goals,
        "errors": errors,
        "evidence": evidence,
        "replay": replay,
        "graph": graph,
        "live_map": live_map,
        "dependency_graph": dependency_graph,
        "timeline": timeline,
        "state_machines": state_machines,
        "roadmap": roadmap,
        "roadmap_timeline": roadmap_timeline,
        "planning": planning,
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
            f"task_sets={len(state['task_sets'])}",
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
