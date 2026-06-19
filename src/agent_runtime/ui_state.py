from __future__ import annotations

import base64
import binascii
import hashlib
import importlib.util
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import notify_routing, ui_commands

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
    "work_state",
    "meeting_room",
    "channels",
    "tasksets_board",
    "taskset_completion",
    "team_agents",
    "teams",
    "growth",
    "workload",
    "sources",
    "errors",
    "evidence",
    "attachments",
    "replay",
    "graph",
    "live_map",
    "office_map",
    "dependency_graph",
    "timeline",
    "state_machines",
    "roadmap",
    "roadmap_timeline",
    "planning",
    "custom_properties",
    "labels",
    "automation_rules",
    "triage",
    "reviews",
    "schedules",
    "calendar",
    "ops_metrics",
    "notifications",
    "daily_brief",
    "notification_routing",
    "workspaces",
    "widgets",
    "i18n",
    "search_index",
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
REVIEW_GLOB = "reviews/*.md"
# Search entity types surfaced by the global search index (TASK-AR-334).
SEARCH_ENTITY_TYPES = ("task", "taskset", "message", "event", "evidence", "review")
# Each entity type deep-links to one of the AR-321 hash routes; clicking a
# search result navigates the console to this route and selects the entity.
SEARCH_ENTITY_ROUTES = {
    "task": "home/board",
    "taskset": "work/tasksets",
    "message": "comms/messages",
    "event": "records/events",
    "evidence": "records/evidence",
    "review": "records/sources",
}


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
            # Team/role assignment fields beyond assignee (TASK-AR-337). These are
            # the raw frontmatter values; the canonical team is RESOLVED later by
            # resolve_task_assignment so heatmap/org-chart/filters agree.
            "role": _normalize_role(meta.get("role")) or None,
            "assignee": meta.get("assignee"),
            "parent_id": parent_id,
            "blocks": blocks,
            "blocked_by": blocked_by,
            "labels": labels,
            "description": _first_sentence(goal),
            "peek_summary": _peek_summary(meta, goal),
            "blocked_reason": meta.get("blocked_reason"),
            "due": meta.get("due"),
            "blocked_since": meta.get("blocked_since"),
            "registered_at": registered_at,
            "created_at": created_at,
            "started_at": started_at,
            "updated_at": updated_at,
            "completed_at": completed_at,
            "metadata": metadata,
            # Raw frontmatter retained so custom-property definitions can be
            # projected onto each task as a frontmatter extension (TASK-AR-331).
            "custom_property_source": dict(meta),
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


def load_reviews(root: Path, now: str, warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Load review/meeting/call records under ``reviews/`` as searchable docs.

    Read-only: these are durable planning artefacts (meeting notes, call logs,
    gate records, evidence indexes). We surface frontmatter (id/title/type/
    status/tags) plus the document body so the global search can match free text.
    """
    reviews: list[dict[str, Any]] = []
    for path in sorted(root.glob(REVIEW_GLOB)):
        rel_path = _rel(root, path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            warnings.append(_warning("review-read-error", rel_path, str(exc)))
            continue
        meta, body = parse_frontmatter(text)
        review_id = str(meta.get("id") or path.stem)
        # Title: explicit frontmatter, else the first markdown H1, else the slug.
        title = str(meta.get("title") or "").strip()
        if not title:
            for line in body.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
        if not title:
            title = path.stem.replace("-", " ")
        tags = meta.get("tags") if isinstance(meta.get("tags"), list) else _string_list(meta.get("tags"))
        reviews.append(
            {
                "id": review_id,
                "title": title,
                "type": meta.get("type") or "review",
                "status": meta.get("status"),
                "signal": meta.get("signal"),
                "score": meta.get("score"),
                "priority": meta.get("priority"),
                "audience": meta.get("audience"),
                "tags": tags,
                "summary": _first_sentence(_section_text(body, "Bottom Line") or body),
                "body": body,
                "created_at": meta.get("generated_at") or meta.get("date") or _mtime_iso(path),
                "source_path": rel_path,
                "source_kind": "review_markdown",
                "source": _source_metadata(root, path, "review_markdown", now),
                "last_updated": _mtime_iso(path),
                "freshness": "present",
            }
        )
    return reviews


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


# ----- TASK-AR-332: file attachments (upload/download/preview + evidence) -----
#
# Storage layout (the upload route in ui_console is the ONLY file-write path for
# uploaded bytes; everything here reads or is called BY that route):
#   agents/project/evidence/attachments/<attachment_id>/<safe_filename>  <- bytes
#   agents/project/evidence/attachments/<attachment_id>.json             <- record
# The sidecar JSON IS the evidence record: it links the stored file to a task /
# message and is surfaced both as an "attachments" resource and (for closeout)
# inside the derived evidence index.
ATTACHMENTS_REL = "agents/project/evidence/attachments"
# Hard cap on a single uploaded payload (decoded bytes). Keeps the in-memory,
# JSON+base64 upload path bounded.
ATTACHMENT_MAX_BYTES = 5 * 1024 * 1024
# Content-type allowlist. Each entry maps the accepted upload content-type to the
# canonical type stored/served back. Only images, plain text, markdown and pdf
# are accepted; executables / html / svg (script vectors) are rejected.
ATTACHMENT_CONTENT_TYPES = {
    "image/png": "image/png",
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/gif": "image/gif",
    "image/webp": "image/webp",
    "text/plain": "text/plain; charset=utf-8",
    "text/markdown": "text/markdown; charset=utf-8",
    "text/x-markdown": "text/markdown; charset=utf-8",
    "application/pdf": "application/pdf",
}
# Extensions allowed in the stored filename. Anything else is normalized to .bin
# so an upload can never land an executable/script extension on disk.
ATTACHMENT_ALLOWED_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt", ".md", ".markdown", ".pdf", ".bin",
}
_ATTACHMENT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class AttachmentError(ValueError):
    """Raised when an upload fails validation (caller maps to HTTP 400)."""


def attachments_dir(root: Path) -> Path:
    return (Path(root).resolve() / ATTACHMENTS_REL).resolve()


def _attachment_id(now: str) -> str:
    compact = re.sub(r"[^0-9]", "", now)[:14] or datetime.now().strftime("%Y%m%d%H%M%S")
    return f"att-{compact}-{secrets.token_hex(4)}"


def normalize_attachment_filename(raw: Any) -> str:
    """Strip any path components and force a safe, allowlisted filename.

    Defends against path traversal: drive letters, leading slashes, ``..`` and
    embedded separators are all discarded -- only the final basename survives,
    and its extension is constrained to the allowlist.
    """
    name = str(raw or "").strip()
    # Drop anything before the last path separator (handles ``../``, ``/etc/``,
    # ``C:\\Windows\\`` and mixed separators alike).
    name = re.split(r"[\\/]", name)[-1]
    # Reject NUL and control chars; keep a conservative filename charset.
    name = "".join(ch for ch in name if ch.isprintable() and ch not in '\\/:*?"<>|')
    name = name.strip().lstrip(".") or "upload"
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    ext = ("." + ext.lower()) if ext else ""
    if ext not in ATTACHMENT_ALLOWED_EXTS:
        ext = ".bin"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._") or "upload"
    return f"{stem[:120]}{ext}"


def _assert_within(base: Path, candidate: Path) -> Path:
    """Resolve ``candidate`` and assert it stays inside ``base`` (or raise)."""
    base_resolved = base.resolve()
    resolved = candidate.resolve()
    if resolved != base_resolved and base_resolved not in resolved.parents:
        raise AttachmentError("resolved path escapes the attachments directory")
    return resolved


def save_attachment(
    root: Path | str,
    *,
    filename: Any,
    content_type: Any,
    data: bytes,
    task_id: Any = None,
    message_id: Any = None,
    actor: Any = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Validate + persist an uploaded file and its evidence sidecar record.

    This is the single trusted file-write entry point for uploads. It enforces a
    size cap, a content-type allowlist, and writes ONLY under the attachments
    directory after re-resolving and asserting containment.
    """
    root_path = Path(root).resolve()
    created_at = now or _now_iso()

    ctype_raw = str(content_type or "").split(";", 1)[0].strip().lower()
    if ctype_raw not in ATTACHMENT_CONTENT_TYPES:
        raise AttachmentError(f"unsupported content type: {ctype_raw or 'unknown'!r}")
    stored_content_type = ATTACHMENT_CONTENT_TYPES[ctype_raw]

    if not isinstance(data, (bytes, bytearray)):
        raise AttachmentError("attachment data must be bytes")
    data = bytes(data)
    if not data:
        raise AttachmentError("attachment is empty")
    if len(data) > ATTACHMENT_MAX_BYTES:
        raise AttachmentError(
            f"attachment exceeds size limit ({len(data)} > {ATTACHMENT_MAX_BYTES} bytes)"
        )

    safe_name = normalize_attachment_filename(filename)
    attachment_id = _attachment_id(created_at)

    base = attachments_dir(root_path)
    base.mkdir(parents=True, exist_ok=True)
    item_dir = _assert_within(base, base / attachment_id)
    item_dir.mkdir(parents=True, exist_ok=True)
    blob_path = _assert_within(item_dir, item_dir / safe_name)
    blob_path.write_bytes(data)

    record = {
        "id": attachment_id,
        "schema_version": "agent-runtime-attachment/v1",
        "filename": safe_name,
        "original_filename": str(filename or safe_name),
        "content_type": stored_content_type,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "task_id": (str(task_id).strip() or None) if task_id is not None else None,
        "message_id": (str(message_id).strip() or None) if message_id is not None else None,
        "uploaded_by": str(actor or "ui"),
        "created_at": created_at,
        "blob_rel": _rel(root_path, blob_path),
        "is_image": stored_content_type.startswith("image/"),
        "is_text": stored_content_type.startswith("text/"),
        "evidence": f"attachment:{safe_name}",
        "source_kind": "attachment_evidence",
    }
    record_path = _assert_within(base, base / f"{attachment_id}.json")
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    record = dict(record)
    record["source_path"] = _rel(root_path, record_path)
    return record


def load_attachments(root: Path | str, now: str | None = None) -> list[dict[str, Any]]:
    """Read all attachment evidence sidecars (newest first)."""
    root_path = Path(root).resolve()
    base = attachments_dir(root_path)
    if not base.is_dir():
        return []
    generated_at = now or _now_iso()
    items: list[dict[str, Any]] = []
    for path in sorted(base.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(record, dict):
            continue
        record.setdefault("id", path.stem)
        record["source_path"] = _rel(root_path, path)
        record["source_kind"] = "attachment_evidence"
        record["last_updated"] = _mtime_iso(path)
        record["last_read_at"] = generated_at
        blob_rel = str(record.get("blob_rel") or "")
        record["freshness"] = "present" if blob_rel and (root_path / blob_rel).is_file() else "missing"
        record["download_url"] = f"/api/attachments/{record['id']}/download"
        items.append(record)
    items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return items


def read_attachment_blob(root: Path | str, attachment_id: Any) -> tuple[bytes, str, str] | None:
    """Return (bytes, content_type, filename) for an attachment id, or None.

    The id is constrained to a safe charset and the resolved blob path is
    asserted to live inside the attachments dir before any read.
    """
    aid = str(attachment_id or "").strip()
    if not _ATTACHMENT_ID_RE.match(aid):
        return None
    root_path = Path(root).resolve()
    base = attachments_dir(root_path)
    record_path = base / f"{aid}.json"
    if not record_path.is_file():
        return None
    try:
        _assert_within(base, record_path)
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (AttachmentError, OSError, json.JSONDecodeError):
        return None
    if not isinstance(record, dict):
        return None
    blob_rel = str(record.get("blob_rel") or "")
    if not blob_rel:
        return None
    try:
        blob_path = _assert_within(base, root_path / blob_rel)
    except AttachmentError:
        return None
    if not blob_path.is_file():
        return None
    content_type = str(record.get("content_type") or "application/octet-stream")
    filename = str(record.get("filename") or "attachment")
    try:
        return blob_path.read_bytes(), content_type, filename
    except OSError:
        return None


def decode_attachment_payload(content_b64: Any) -> bytes:
    """Decode a base64 upload payload, raising AttachmentError on bad input."""
    raw = str(content_b64 or "")
    if "," in raw and raw.strip().lower().startswith("data:"):
        # Tolerate a data: URL prefix (clipboard paste produces these).
        raw = raw.split(",", 1)[1]
    raw = raw.strip()
    if not raw:
        raise AttachmentError("attachment content is empty")
    try:
        return base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AttachmentError(f"invalid base64 content: {exc}") from None


def attachment_evidence(attachments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project attachments into the shared evidence index for task closeout."""
    evidence: list[dict[str, Any]] = []
    for item in attachments:
        evidence.append(
            {
                "id": f"evidence:{item.get('id')}",
                "evidence": item.get("evidence") or f"attachment:{item.get('filename')}",
                "source_id": item.get("id"),
                "source_type": "attachment",
                "task_id": item.get("task_id"),
                "goal_id": None,
                "created_at": item.get("created_at"),
                "source_path": item.get("source_path"),
                "source_kind": "attachment_evidence",
                "last_updated": item.get("last_updated"),
                "freshness": item.get("freshness", "present"),
                "download_url": item.get("download_url"),
                "filename": item.get("filename"),
                "content_type": item.get("content_type"),
            }
        )
    return evidence


def enrich_tasks_with_attachments(tasks: list[dict[str, Any]], attachments: list[dict[str, Any]]) -> None:
    by_task: dict[str, list[dict[str, Any]]] = {}
    for item in attachments:
        task_id = str(item.get("task_id") or "").strip()
        if task_id:
            by_task.setdefault(task_id, []).append(item)
    for task in tasks:
        linked = by_task.get(str(task.get("id") or ""), [])
        task["attachments"] = linked
        task["attachment_count"] = len(linked)


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


# --- State-machine interactive viewer (TASK-AR-336) ------------------------
# The lifecycles in agents/project/STATE-MACHINES.yml are the single source of
# truth (SSoT) for task / claim / role state machines. This adapter parses that
# YAML into a render-ready node+edge graph (state nodes carry the declared
# signal/score; transition edges carry from/to/trigger and a wildcard flag for
# ``from: "*"``) and derives, per task, the current state + the transition path
# the task has traversed -- computed strictly from the append-only event log.
# Nothing here mutates the YAML or any runtime state; the viewer is read-only.

STATE_MACHINES_REL = "agents/project/STATE-MACHINES.yml"
STATE_MACHINES_SCHEMA = "agent-runtime-state-machines-view/v1"
# Declared signal -> existing semantic token name (defined in BOTH theme blocks
# of the console stylesheet). Used by the front-end as var(--<token>), so no raw
# colors leak into the rendered graph. Anything unknown falls back to "subtle".
STATE_SIGNAL_TOKENS = {
    "pass": "success",
    "watch": "warning",
    "block": "danger",
}
# Wildcard source used by STATE-MACHINES.yml transitions (``from: "*"``): the
# transition can fire from ANY state of the machine.
_STATE_WILDCARD = "*"
# Event-name (substring, lowercased) -> task-machine state. The event log is
# append-only and heterogeneous, so we match on tolerant substrings and map an
# event to the lifecycle state it implies. Order is longest-first at match time.
_TASK_EVENT_STATE_MARKERS: tuple[tuple[str, str], ...] = (
    ("archiv", "archived"),
    ("complet", "completed"),
    ("done", "completed"),
    ("verif", "completed"),
    ("block", "blocked"),
    ("blocker", "blocked"),
    ("claim", "in_progress"),
    ("start", "in_progress"),
    ("progress", "in_progress"),
    ("assign", "in_progress"),
    ("resume", "in_progress"),
    ("plan", "planned"),
    ("creat", "planned"),
    ("intake", "planned"),
)


def _parse_state_machines_text(text: str) -> list[dict[str, Any]]:
    """Parse the STATE-MACHINES.yml ``machines:`` list into structured records.

    Each machine keeps the legacy ``states`` list of ids (consumed by the live
    map summary) plus a structured ``state_defs`` list (id/signal/score) and a
    ``transitions`` list (from/to/trigger). The shape mirrors the YAML so the
    viewer can render the lifecycle without trusting any derived state.
    """
    machines: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    # section is one of: None, "states", "transitions".
    section: str | None = None
    state_entry: dict[str, Any] | None = None
    transition_entry: dict[str, Any] | None = None

    def _flush_state() -> None:
        nonlocal state_entry
        if current is not None and state_entry is not None and state_entry.get("id"):
            current["state_defs"].append(state_entry)
            current["states"].append(state_entry["id"])
        state_entry = None

    def _flush_transition() -> None:
        nonlocal transition_entry
        if current is not None and transition_entry is not None and transition_entry.get("from") and transition_entry.get("to"):
            current["transitions"].append(transition_entry)
        transition_entry = None

    def _flush_machine() -> None:
        nonlocal current
        _flush_state()
        _flush_transition()
        if current is not None:
            machines.append(current)
        current = None

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if line.startswith("  - id: "):
            _flush_machine()
            current = {"id": stripped.partition(":")[2].strip(), "states": [], "state_defs": [], "transitions": []}
            section = None
            continue
        if current is None:
            continue
        if line.startswith("    scope: "):
            _flush_state()
            _flush_transition()
            current["scope"] = stripped.partition(":")[2].strip()
        elif line.startswith("    owner: "):
            _flush_state()
            _flush_transition()
            current["owner"] = stripped.partition(":")[2].strip()
        elif line.startswith("    initial: "):
            _flush_state()
            _flush_transition()
            current["initial"] = stripped.partition(":")[2].strip()
        elif line.startswith("    states:"):
            _flush_state()
            _flush_transition()
            section = "states"
        elif line.startswith("    transitions:"):
            _flush_state()
            _flush_transition()
            section = "transitions"
        elif section == "states" and line.startswith("      - id: "):
            _flush_state()
            state_entry = {"id": stripped.partition(":")[2].strip().strip("\"'")}
        elif section == "states" and state_entry is not None and line.startswith("        signal: "):
            state_entry["signal"] = stripped.partition(":")[2].strip().strip("\"'")
        elif section == "states" and state_entry is not None and line.startswith("        score: "):
            try:
                state_entry["score"] = int(stripped.partition(":")[2].strip())
            except ValueError:
                state_entry["score"] = None
        elif section == "transitions" and line.startswith("      - from: "):
            _flush_transition()
            transition_entry = {"from": stripped.partition(":")[2].strip().strip("\"'")}
        elif section == "transitions" and transition_entry is not None and line.startswith("        to: "):
            transition_entry["to"] = stripped.partition(":")[2].strip().strip("\"'")
        elif section == "transitions" and transition_entry is not None and line.startswith("        trigger: "):
            transition_entry["trigger"] = stripped.partition(":")[2].strip().strip("\"'")
    _flush_machine()
    return machines


def _machine_graph(machine: dict[str, Any]) -> dict[str, Any]:
    """Build the render-ready node + edge graph for one parsed machine.

    State nodes carry the declared signal/score plus a stable signal token and a
    flag marking the initial state. Transition edges carry from/to/trigger; a
    ``from: "*"`` edge is marked ``wildcard`` and expanded to per-state target
    hints so the front-end can highlight "from any state" transitions.
    """
    initial = str(machine.get("initial") or "").strip()
    defs = machine.get("state_defs") or [{"id": sid} for sid in machine.get("states") or []]
    known_ids = [str(entry.get("id")) for entry in defs if entry.get("id")]
    nodes: list[dict[str, Any]] = []
    for entry in defs:
        sid = str(entry.get("id") or "").strip()
        if not sid:
            continue
        signal = str(entry.get("signal") or "").strip()
        nodes.append(
            {
                "id": sid,
                "signal": signal or None,
                "signal_token": STATE_SIGNAL_TOKENS.get(signal, "subtle"),
                "score": entry.get("score"),
                "is_initial": sid == initial,
            }
        )
    edges: list[dict[str, Any]] = []
    for index, transition in enumerate(machine.get("transitions") or []):
        frm = str(transition.get("from") or "").strip()
        to = str(transition.get("to") or "").strip()
        if not frm or not to:
            continue
        wildcard = frm == _STATE_WILDCARD
        edges.append(
            {
                "id": f"{machine.get('id')}:{frm}->{to}:{index}",
                "from": frm,
                "to": to,
                "trigger": str(transition.get("trigger") or "").strip() or None,
                "wildcard": wildcard,
                # For a wildcard edge the concrete sources are every state but
                # the target itself; this lets the viewer fan the edge out.
                "wildcard_sources": [sid for sid in known_ids if sid != to] if wildcard else [],
            }
        )
    return {"nodes": nodes, "edges": edges}


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


def _task_state_from_status(status: str, known_ids: set[str]) -> str | None:
    """Map a task's stored status onto a state id of the task machine."""
    normalized = (status or "").strip().lower()
    if not normalized:
        return None
    if normalized in known_ids:
        return normalized
    alias = {
        "active": "in_progress",
        "claimed": "in_progress",
        "working": "in_progress",
        "assigned": "in_progress",
        "review": "in_progress",
        "waiting_review": "in_progress",
        "ready": "planned",
        "hold": "blocked",
        "보류": "blocked",
        "진행 중": "in_progress",
        "대기": "planned",
        "done": "completed",
        "released": "completed",
        "완료": "completed",
    }
    mapped = alias.get(normalized)
    return mapped if mapped in known_ids else (mapped or None)


def _event_state_marker(event_name: str, known_ids: set[str]) -> str | None:
    """Map an append-only event name onto a task-machine state id (or None)."""
    name = str(event_name or "").strip().lower()
    if not name:
        return None
    # Longest marker key first so e.g. "blocker" wins over "block" only when it
    # would change the outcome; both map to the same state here, but ordering
    # keeps the match deterministic.
    for marker, state in sorted(_TASK_EVENT_STATE_MARKERS, key=lambda item: -len(item[0])):
        if marker in name and state in known_ids:
            return state
    return None


def _resolve_transition_path(machine: dict[str, Any], state_sequence: list[str]) -> list[dict[str, Any]]:
    """Resolve consecutive distinct states into the transition edges traversed.

    For each (prev -> curr) hop we prefer an explicit edge (prev -> curr); if
    none exists we fall back to a wildcard edge (``from: "*"`` -> curr). Edges
    are returned with the edge id so the viewer can highlight them in place.
    """
    transitions = machine.get("transitions") or []
    explicit: dict[tuple[str, str], int] = {}
    wildcard_to: dict[str, int] = {}
    for index, transition in enumerate(transitions):
        frm = str(transition.get("from") or "").strip()
        to = str(transition.get("to") or "").strip()
        if not frm or not to:
            continue
        if frm == _STATE_WILDCARD:
            wildcard_to.setdefault(to, index)
        else:
            explicit.setdefault((frm, to), index)
    path: list[dict[str, Any]] = []
    machine_id = machine.get("id")
    for prev, curr in zip(state_sequence, state_sequence[1:]):
        if prev == curr:
            continue
        index = explicit.get((prev, curr))
        wildcard = False
        if index is None:
            index = wildcard_to.get(curr)
            wildcard = index is not None
        if index is None:
            continue
        transition = transitions[index]
        frm = str(transition.get("from") or "").strip()
        path.append(
            {
                "id": f"{machine_id}:{frm}->{curr}:{index}",
                "from": prev,
                "to": curr,
                "trigger": str(transition.get("trigger") or "").strip() or None,
                "wildcard": wildcard,
            }
        )
    return path


def derive_task_state_paths(machine: dict[str, Any], tasks: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per-task current state + traversed transition path for the task machine.

    The state SEQUENCE is read from the append-only event log (ordered by ts):
    every event that maps to a lifecycle state contributes a step. The task's
    stored status seeds the start (initial) and is appended as the authoritative
    current state. Transitions are then resolved against the machine definition.
    Returns a mapping keyed by task id; only tasks with a resolvable current
    state are included.
    """
    known_ids = {str(entry.get("id")) for entry in (machine.get("state_defs") or []) if entry.get("id")}
    known_ids.update(str(sid) for sid in (machine.get("states") or []))
    initial = str(machine.get("initial") or "").strip() or None

    # Bucket events by task id, ordered by timestamp (stable, append-only log).
    events_by_task: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        task_id = str(event.get("task_id") or "").strip()
        if not task_id:
            continue
        events_by_task.setdefault(task_id, []).append(event)

    result: dict[str, dict[str, Any]] = {}
    for task in tasks:
        task_id = str(task.get("id") or "").strip()
        if not task_id:
            continue
        ordered = sorted(events_by_task.get(task_id, []), key=lambda ev: str(ev.get("created_at") or ev.get("ts") or ""))
        sequence: list[str] = []
        if initial and initial in known_ids:
            sequence.append(initial)
        for event in ordered:
            state = _event_state_marker(event.get("event") or event.get("type"), known_ids)
            if state and (not sequence or sequence[-1] != state):
                sequence.append(state)
        current = _task_state_from_status(str(task.get("status") or ""), known_ids)
        if current and (not sequence or sequence[-1] != current):
            sequence.append(current)
        if not current:
            current = sequence[-1] if sequence else initial
        if not current:
            continue
        result[task_id] = {
            "task_id": task_id,
            "title": task.get("title"),
            "current_state": current,
            "state_sequence": sequence,
            "transition_path": _resolve_transition_path(machine, sequence),
            "source_path": task.get("source_path"),
        }
    return result


def load_state_machines(root: Path, tasks: list[dict[str, Any]], agents: list[dict[str, Any]], now: str, events: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Read STATE-MACHINES.yml into render-ready machine records (read-only).

    Every machine carries the parsed lifecycle (state nodes + transition edges)
    so the interactive viewer can render it directly. The ``task`` machine is
    additionally annotated with a per-task ``task_states`` map (current state +
    event-log-derived traversed transition path), keyed by task id, so the
    "view in state machine" deep-link from a task can highlight its position.
    """
    path = root / "agents" / "project" / "STATE-MACHINES.yml"
    if not path.exists():
        return []
    try:
        machines = _parse_state_machines_text(path.read_text(encoding="utf-8"))
    except OSError:
        return []
    events = events or []
    for machine in machines:
        machine_id = str(machine.get("id") or "")
        current, counts = _observed_machine_state(machine_id, tasks, agents, machine.get("initial"))
        graph = _machine_graph(machine)
        machine["current_state"] = current
        machine["observed_counts"] = counts
        machine["state_nodes"] = graph["nodes"]
        machine["transition_edges"] = graph["edges"]
        machine["totals"] = {"states": len(graph["nodes"]), "transitions": len(graph["edges"])}
        # Per-task traversed-path highlighting is meaningful for the backlog task
        # lifecycle; other machines render the graph without per-task overlays.
        if machine_id == "task":
            machine["task_states"] = derive_task_state_paths(machine, tasks, events)
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
    # TASK-AR-329: merge the canonical TASKSET-DEFINITIONS.json registry so a
    # UI-created taskset (registered via backlog_board.sync_taskset_registry)
    # surfaces in the console exactly as it does on the generated board. The
    # registry rows are sorted by order so the assigned sequence is stable.
    info_map = getattr(module, "_task_set_info_map", None)
    if callable(info_map):
        try:
            merged = info_map(root)
        except Exception as exc:  # pragma: no cover - defensive adapter boundary
            if warnings is not None:
                warnings.append(_warning("task-set-registry-error", _rel(root, path), str(exc)))
            merged = {}
        ordered = sorted(merged.values(), key=lambda item: (getattr(item, "order", 999), getattr(item, "task_set_id", "")))
        for sequence, item in enumerate(ordered, start=1):
            info = _task_set_info_from_item(item, infos.get(str(getattr(item, "task_set_id", "")), {}).get("sequence") or sequence)
            if info and info["id"] not in infos:
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


# ----- TASK-AR-341: workspace switcher + widget extension points + i18n -----
#
# These three features are *navigation/config* surfaces, not write surfaces. The
# console already takes ``--root``; the workspace switcher lists registered host
# projects (read-only) and offers a safe relaunch command — it never execs an
# arbitrary path or writes the SSoT. Widgets are declarative data definitions
# (JSON/YAML) rendered with every field HTML-escaped (no eval / no raw HTML).
# i18n strings live Python-side (here) so the served app.js stays ASCII; the KR
# values are delivered to the browser as JSON via /api/i18n + /api/state.

# Default language is Korean (the owner-facing default).
DEFAULT_LANGUAGE = "ko"
I18N_LANGUAGES = ("ko", "en")

# Key shell strings and decision-first hero strings. Runtime/API data identifiers
# remain English; display labels are mapped in the browser via this table.
I18N_STRINGS: dict[str, dict[str, str]] = {
    "nav.group.home": {"ko": "홈", "en": "Home"},
    "nav.group.work": {"ko": "작업", "en": "Work"},
    "nav.group.agents": {"ko": "에이전트", "en": "Agents"},
    "nav.group.comms": {"ko": "소통", "en": "Comms"},
    "nav.group.records": {"ko": "기록", "en": "Records"},
    "nav.group.ops": {"ko": "운영", "en": "Ops"},
    "view.board.title": {"ko": "홈 대시보드", "en": "Home Dashboard"},
    "view.tasksets.title": {"ko": "태스크셋", "en": "Tasksets"},
    "view.work.title": {"ko": "작업 탐색기", "en": "Work Explorer"},
    "view.agents.title": {"ko": "에이전트", "en": "Agents"},
    "view.channels.title": {"ko": "채널", "en": "Channels"},
    "view.events.title": {"ko": "이벤트", "en": "Events"},
    "button.refresh": {"ko": "새로고침", "en": "Refresh"},
    "button.create": {"ko": "생성", "en": "Create"},
    "button.send": {"ko": "보내기", "en": "Send"},
    "button.save": {"ko": "저장", "en": "Save"},
    "button.cancel": {"ko": "취소", "en": "Cancel"},
    "common.loading": {"ko": "런타임 상태 불러오는 중", "en": "Loading runtime state"},
    "common.language": {"ko": "언어", "en": "Language"},
    "workspace.title": {"ko": "워크스페이스", "en": "Workspace"},
    "workspace.switch": {"ko": "전환", "en": "Switch"},
    "workspace.current": {"ko": "현재", "en": "Current"},
    "workspace.relaunch_hint": {
        "ko": "선택한 워크스페이스로 콘솔을 다시 실행하려면 아래 명령을 복사하세요.",
        "en": "Copy the command below to relaunch the console for the selected workspace.",
    },
    "widgets.title": {"ko": "위젯", "en": "Widgets"},
    "widgets.empty": {"ko": "등록된 위젯이 없습니다", "en": "No widgets registered"},
    "cockpit.aria": {
        "ko": "주의 인박스 - 지금 필요한 일",
        "en": "Attention inbox - what needs you now",
    },
    "cockpit.title": {"ko": "지금 필요한 일", "en": "What needs you now"},
    "cockpit.empty": {"ko": "지금 필요한 항목이 없습니다.", "en": "Nothing needs you right now."},
    "cockpit.total.clear": {"ko": "모두 정상", "en": "all clear"},
    "cockpit.total.one": {"ko": "1개 항목 확인 필요", "en": "1 item needs attention"},
    "cockpit.total.many_suffix": {"ko": "개 항목 확인 필요", "en": "items need attention"},
    "cockpit.unavailable": {"ko": "인박스를 불러올 수 없습니다", "en": "inbox unavailable"},
    "cockpit.open_details": {"ko": "상세 열기", "en": "Open details"},
    "cockpit.detail.kicker": {"ko": "주의 상세", "en": "Attention detail"},
    "cockpit.detail.title": {"ko": "인박스 상세", "en": "Inbox detail"},
    "cockpit.detail.close": {"ko": "주의 상세 닫기", "en": "Close attention detail"},
    "cockpit.detail.summary": {
        "ko": "전체 신호 목록을 확인하고 심각도가 가장 높은 항목부터 처리하세요.",
        "en": "Review the full signal list and act on the highest-severity item first.",
    },
    "cockpit.detail.empty": {"ko": "이 그룹에는 항목이 없습니다.", "en": "No items in this group."},
    "cockpit.item.untitled": {"ko": "제목 없는 항목", "en": "Untitled item"},
    "cockpit.summary.empty": {"ko": "이 그룹에는 항목이 없습니다.", "en": "No items in this group."},
    "cockpit.summary.more": {"ko": "개 더 있음", "en": "more"},
    "inbox.group.approval_pending": {"ko": "승인", "en": "Approvals"},
    "inbox.group.blocked": {"ko": "차단됨", "en": "Blocked"},
    "inbox.group.runtime_anomalies": {"ko": "런타임 이상", "en": "Runtime anomalies"},
    "inbox.group.gate_failures": {"ko": "게이트 실패", "en": "Gate failures"},
    "inbox.group.cost_anomalies": {"ko": "비용 이상", "en": "Cost anomalies"},
    "inbox.group.stale": {"ko": "오래됨", "en": "Stale"},
    "inbox.action.approve_gate": {"ko": "승인 / 게이트", "en": "approve / gate"},
    "inbox.action.resolve_blocker": {"ko": "차단 해소", "en": "resolve blocker"},
    "inbox.action.fix_gate": {"ko": "게이트 수정", "en": "fix gate"},
    "inbox.action.review_cost": {"ko": "비용 검토", "en": "review cost"},
    "inbox.action.review_refresh": {"ko": "검토 / 갱신", "en": "review / refresh"},
    "inbox.action.resolve_claim": {"ko": "클레임 해소", "en": "resolve claim"},
    "inbox.why.approval_required": {"ko": "승인 필요", "en": "approval_required"},
    "inbox.why.status": {"ko": "상태", "en": "status"},
    "inbox.why.gate_failures": {"ko": "게이트 실패", "en": "gate failures"},
    "inbox.why.actual": {"ko": "실제", "en": "actual"},
    "inbox.why.budget": {"ko": "예산", "en": "budget"},
    "inbox.why.no_update": {"ko": "업데이트 없음", "en": "no update"},
    "inbox.why.cross_host_claim_conflict": {
        "ko": "호스트 간 클레임 충돌",
        "en": "cross-host claim conflict",
    },
    "work_state.kicker": {"ko": "작업", "en": "Work"},
    "work_state.title": {"ko": "작업 상태", "en": "Work state"},
    "work_state.empty": {"ko": "활성 작업 상태가 없습니다.", "en": "No active work state."},
    "work_state.unavailable": {"ko": "작업 상태를 불러올 수 없습니다", "en": "work state unavailable"},
    "work_state.total.none": {"ko": "작업 상태 없음", "en": "no work state"},
    "work_state.total.tasksets": {"ko": "태스크셋", "en": "tasksets"},
    "work_state.total.units": {"ko": "유닛", "en": "units"},
    "work_state.count.waiting": {"ko": "대기", "en": "Waiting"},
    "work_state.count.active": {"ko": "진행", "en": "Active"},
    "work_state.count.review": {"ko": "검토", "en": "Review"},
    "work_state.count.done": {"ko": "완료", "en": "Done"},
    "work_state.units": {"ko": "유닛", "en": "units"},
    "work_state.units.shown": {"ko": "개 유닛 표시", "en": "units shown"},
    "work_state.units.hidden": {"ko": "개 숨김", "en": "hidden"},
    "work_state.bucket.waiting": {"ko": "대기", "en": "waiting"},
    "work_state.bucket.active": {"ko": "진행", "en": "active"},
    "work_state.bucket.review": {"ko": "검토", "en": "review"},
    "work_state.bucket.done": {"ko": "완료", "en": "done"},
}


def lookup_i18n(key: str, lang: str | None = None) -> str:
    """Resolve an i18n key for ``lang`` with KR/EN fallbacks (server mirror of t())."""

    language = lang if lang in I18N_LANGUAGES else DEFAULT_LANGUAGE
    entry = I18N_STRINGS.get(key)
    if not entry:
        return key
    return entry.get(language) or entry.get(DEFAULT_LANGUAGE) or entry.get("en") or key


def build_i18n(now: str | None = None) -> dict[str, Any]:
    """Build the i18n resource: string table + language metadata + default."""

    return {
        "generated_at": now or _now_iso(),
        "default_language": DEFAULT_LANGUAGE,
        "languages": list(I18N_LANGUAGES),
        "strings": {key: dict(values) for key, values in I18N_STRINGS.items()},
    }


# Read-only workspace registry lookup order. A registry is a JSON list/object of
# host projects; the current root is always included. None of these are executed
# or written — they are *links* the operator may relaunch the console against.
WORKSPACE_REGISTRY_RELPATHS = (
    "agents/runtime/workspaces.json",
    ".agent-runtime/workspaces.json",
)
WORKSPACE_REGISTRY_HOME = Path.home() / ".codex" / "autofolio" / "workspaces.json"


def _workspace_id(path: Path) -> str:
    raw = path.name or path.as_posix()
    return _slug(raw) or "workspace"


def _workspace_recent_state(path: Path, now: str) -> dict[str, Any]:
    """Read-only recent-state preview for a registered host project.

    Only stats a couple of well-known marker files; never opens task bodies or
    runs anything. Missing markers degrade to ``available: false``.
    """

    if not path.exists() or not path.is_dir():
        return {"available": False, "last_activity": None, "open_tasks": None, "status_title": None}
    tasks_dir = path / "agents" / "lead_engineer" / "tasks"
    open_tasks: int | None = None
    last_activity: str | None = None
    if tasks_dir.is_dir():
        try:
            task_files = list(tasks_dir.glob("TASK-*.md"))
        except OSError:
            task_files = []
        open_tasks = len(task_files)
        for task_file in task_files:
            stamp = _mtime_iso(task_file)
            if stamp and (last_activity is None or stamp > last_activity):
                last_activity = stamp
    status_path = path / "STATUS.md"
    status_title: str | None = None
    if status_path.exists():
        status_stamp = _mtime_iso(status_path)
        if status_stamp and (last_activity is None or status_stamp > last_activity):
            last_activity = status_stamp
        try:
            text = status_path.read_text(encoding="utf-8")
            headings = list(re.finditer(r"^##\s+(.+)$", text, flags=re.MULTILINE))
            if headings:
                status_title = headings[-1].group(1).strip()
        except OSError:
            status_title = None
    return {
        "available": True,
        "last_activity": last_activity,
        "open_tasks": open_tasks,
        "status_title": status_title,
    }


def _parse_workspace_registry(raw: Any) -> list[dict[str, Any]]:
    """Normalize a registry document into a list of {path, name?} candidates."""

    rows: list[Any]
    if isinstance(raw, dict):
        if isinstance(raw.get("workspaces"), list):
            rows = raw["workspaces"]
        elif isinstance(raw.get("projects"), list):
            rows = raw["projects"]
        else:
            rows = []
    elif isinstance(raw, list):
        rows = raw
    else:
        rows = []
    candidates: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, str):
            candidates.append({"path": row, "name": None})
        elif isinstance(row, dict):
            path_value = row.get("path") or row.get("root") or row.get("dir")
            if path_value:
                candidates.append({"path": str(path_value), "name": row.get("name") or row.get("label")})
    return candidates


def _load_workspace_registry_candidates(root: Path) -> list[dict[str, Any]]:
    seen_files: list[Path] = []
    for rel in WORKSPACE_REGISTRY_RELPATHS:
        seen_files.append(root / rel)
    seen_files.append(WORKSPACE_REGISTRY_HOME)
    candidates: list[dict[str, Any]] = []
    for registry_path in seen_files:
        if not registry_path.exists():
            continue
        try:
            raw = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        candidates.extend(_parse_workspace_registry(raw))
    return candidates


def load_workspaces(root: Path | str, now: str | None = None) -> dict[str, Any]:
    """Derive the read-only list of registered host-project workspaces.

    The current ``--root`` is always present and marked ``current``. Registered
    hosts are read from the registry files (read-only). Switching is a navigation
    action: each entry carries a ``relaunch_command`` (``agent-runtime ui-console
    --root <path>``) the operator can copy — the console NEVER execs the path or
    writes any SSoT here.
    """

    root_path = Path(root).resolve()
    generated_at = now or _now_iso()
    items: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    def add(path: Path, name: str | None, *, current: bool) -> None:
        resolved = path.resolve()
        key = resolved.as_posix()
        if key in seen_paths:
            return
        seen_paths.add(key)
        items.append(
            {
                "id": _workspace_id(resolved),
                "name": name or resolved.name or key,
                "path": key,
                "current": current,
                "exists": resolved.exists() and resolved.is_dir(),
                "recent_state": _workspace_recent_state(resolved, generated_at),
                # Navigation-only relaunch hint. NOT executed by the console.
                "relaunch_command": f"agent-runtime ui-console --root {key}",
            }
        )

    add(root_path, root_path.name or "current", current=True)
    for candidate in _load_workspace_registry_candidates(root_path):
        raw_path = candidate.get("path")
        if not raw_path:
            continue
        expanded = Path(str(raw_path)).expanduser()
        if not expanded.is_absolute():
            expanded = (root_path / expanded)
        add(expanded, candidate.get("name"), current=False)

    return {
        "generated_at": generated_at,
        "current_path": root_path.as_posix(),
        "items": items,
    }


# Declarative widget extension point. Widget defs are data files dropped into the
# widgets dir; each describes a Home dashboard card. Fields are rendered escaped.
WIDGETS_DIR_RELPATHS = (
    "agents/runtime/widgets",
    ".agent-runtime/widgets",
)
WIDGET_ALLOWED_KINDS = ("metric", "list", "shortcut", "note")
WIDGET_MAX = 24

# Built-in sample widgets so the extension point renders out-of-the-box and the
# acceptance criterion ("a sample custom widget renders by declaration only") is
# satisfied without requiring the operator to author a file first.
BUILTIN_WIDGETS: tuple[dict[str, Any], ...] = (
    {
        "id": "sample-shortcuts",
        "kind": "shortcut",
        "title": "Shortcuts",
        "items": [
            {"label": "New Task", "shortcut": "Ctrl+Shift+N", "route": "home/board"},
            {"label": "Command Palette", "shortcut": "Ctrl+K", "route": "home/board"},
            {"label": "Tasksets", "shortcut": "g t", "route": "work/tasksets"},
        ],
        "builtin": True,
    },
    {
        "id": "sample-note",
        "kind": "note",
        "title": "About Widgets",
        "body": "Drop a JSON/YAML file in agents/runtime/widgets to add a card.",
        "builtin": True,
    },
)


def _coerce_widget(raw: Any, source: str) -> dict[str, Any] | None:
    """Validate + normalize one declarative widget definition (data only)."""

    if not isinstance(raw, dict):
        return None
    kind = str(raw.get("kind") or "note").strip().lower()
    if kind not in WIDGET_ALLOWED_KINDS:
        kind = "note"
    widget: dict[str, Any] = {
        "id": str(raw.get("id") or source or "widget"),
        "kind": kind,
        "title": str(raw.get("title") or raw.get("name") or "Widget"),
        "source": source,
        "builtin": bool(raw.get("builtin", False)),
    }
    if kind == "metric":
        widget["value"] = "" if raw.get("value") is None else str(raw.get("value"))
        widget["caption"] = str(raw.get("caption") or "")
    elif kind == "list":
        raw_items = raw.get("items") if isinstance(raw.get("items"), list) else []
        widget["items"] = [
            {
                "label": str(item.get("label") if isinstance(item, dict) else item),
                "value": str(item.get("value")) if isinstance(item, dict) and item.get("value") is not None else "",
            }
            for item in raw_items
        ][:20]
    elif kind == "shortcut":
        raw_items = raw.get("items") if isinstance(raw.get("items"), list) else []
        widget["items"] = [
            {
                "label": str(item.get("label", "")),
                "shortcut": str(item.get("shortcut", "")),
                "route": str(item.get("route", "")),
            }
            for item in raw_items
            if isinstance(item, dict)
        ][:20]
    else:  # note
        widget["body"] = str(raw.get("body") or raw.get("text") or "")
    return widget


def _parse_widget_document(text: str, suffix: str) -> list[Any]:
    """Parse a widget file into one-or-many raw widget dicts (JSON or YAML)."""

    suffix = suffix.lower()
    parsed: Any = None
    if suffix == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return []
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml  # PyYAML ships with the project deps; degrade if absent.

            parsed = yaml.safe_load(text)
        except Exception:
            return []
    else:
        return []
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        if isinstance(parsed.get("widgets"), list):
            return parsed["widgets"]
        return [parsed]
    return []


def load_widgets(root: Path | str, now: str | None = None) -> dict[str, Any]:
    """Load declarative Home dashboard widget definitions (read-only data).

    Built-in samples are always present; operator-authored JSON/YAML files in the
    widgets dir are appended. Every field is plain data — the renderer escapes it
    and never evals or injects raw HTML/JS from a definition.
    """

    root_path = Path(root).resolve()
    generated_at = now or _now_iso()
    widgets: list[dict[str, Any]] = [dict(widget) for widget in BUILTIN_WIDGETS]
    seen_ids: set[str] = {widget["id"] for widget in widgets}
    sources: list[str] = []
    for rel in WIDGETS_DIR_RELPATHS:
        widgets_dir = root_path / rel
        if not widgets_dir.is_dir():
            continue
        try:
            files = sorted(
                p
                for p in widgets_dir.iterdir()
                if p.is_file() and p.suffix.lower() in {".json", ".yaml", ".yml"}
            )
        except OSError:
            files = []
        for widget_file in files:
            try:
                text = widget_file.read_text(encoding="utf-8")
            except OSError:
                continue
            sources.append(_rel(root_path, widget_file))
            for raw in _parse_widget_document(text, widget_file.suffix):
                widget = _coerce_widget(raw, _rel(root_path, widget_file))
                if widget is None:
                    continue
                if widget["id"] in seen_ids:
                    widget["id"] = f"{widget['id']}-{len(widgets)}"
                seen_ids.add(widget["id"])
                widgets.append(widget)
                if len(widgets) >= WIDGET_MAX:
                    break
            if len(widgets) >= WIDGET_MAX:
                break
    return {
        "generated_at": generated_at,
        "dir_candidates": list(WIDGETS_DIR_RELPATHS),
        "sources": sources,
        "items": widgets,
    }


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


# --- Entity catalog (TASK-AR-539/540): manifest-first read + palette search ---
def load_catalog(root: Path) -> dict[str, Any]:
    """Read the generated ENTITY-CATALOG.json (manifest-first; {} if absent)."""
    path = Path(root) / "agents" / "project" / "work-items" / "ENTITY-CATALOG.json"
    if not path.exists():
        return {"schema": "agent-runtime-entity-catalog/v1", "entities": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema": "agent-runtime-entity-catalog/v1", "entities": []}


_CATALOG_SCOPE_RE = re.compile(r"^(?:kind:|@)(\w[\w-]*)\s+(.*)$", re.IGNORECASE)


def catalog_search(root: Path, query: str, kinds: list[str] | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Cross-entity command-palette search over the catalog (TASK-AR-540).

    Reads the generated ENTITY-CATALOG.json (manifest-first) and ranks matches.
    Supports prefix scoping like ``kind:task foo`` / ``@taskset bar``. Implemented
    inline here (not via scripts.entity_catalog) so it works inside the server
    process, whose sys.path is src-only.
    """
    catalog = load_catalog(root)
    raw = (query or "").strip()
    scoped: str | None = None
    match = _CATALOG_SCOPE_RE.match(raw)
    if match:
        scoped, raw = match.group(1).lower(), match.group(2).strip()
    kind_filter = {scoped} if scoped else ({k.lower() for k in kinds} if kinds else None)
    needle = raw.lower()
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    for entity in catalog.get("entities", []):
        if kind_filter and str(entity.get("kind", "")).lower() not in kind_filter:
            continue
        eid = str(entity.get("id", ""))
        title = str(entity.get("title", ""))
        if not needle:
            score = 1
        elif needle in eid.lower():
            score = 3
        elif needle in title.lower():
            score = 2
        elif needle in json.dumps(entity.get("metadata", {}), ensure_ascii=False).lower():
            score = 1
        else:
            continue
        ranked.append((score, eid, entity))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    return [entity for _, _, entity in ranked[:limit]]


def catalog_entity(root: Path, entity_id: str) -> dict[str, Any] | None:
    """Entity detail + forward relations + computed BACKLINKS (TASK-AR-541)."""
    entities = load_catalog(root).get("entities", [])
    by_id = {str(item.get("id")): item for item in entities}
    entity = by_id.get(entity_id)
    if entity is None:
        return None
    forward = [
        {
            "type": rel.get("type"),
            "target": rel.get("target"),
            "target_title": (by_id.get(str(rel.get("target"))) or {}).get("title"),
            "resolved": str(rel.get("target")) in by_id,
        }
        for rel in entity.get("relations", [])
    ]
    backlinks = [
        {"type": rel.get("type"), "source": str(other.get("id")), "source_kind": other.get("kind")}
        for other in entities
        for rel in other.get("relations", [])
        if str(rel.get("target")) == entity_id
    ]
    return {"entity": entity, "relations": forward, "backlinks": backlinks}


def catalog_facets(root: Path) -> dict[str, Any]:
    """Faceted counts (kind/status) + a needs-attention rollup (TASK-AR-543)."""
    entities = load_catalog(root).get("entities", [])
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    triage: list[str] = []
    for entity in entities:
        kind = str(entity.get("kind", ""))
        by_kind[kind] = by_kind.get(kind, 0) + 1
        status = str((entity.get("metadata") or {}).get("status") or "")
        if status:
            by_status[status] = by_status.get(status, 0) + 1
        if status == "triage":
            triage.append(str(entity.get("id")))
    return {
        "by_kind": dict(sorted(by_kind.items())),
        "by_status": dict(sorted(by_status.items())),
        "needs_attention": {"triage": triage, "triage_count": len(triage)},
        "total": len(entities),
    }


DOC_KINDS = ("council", "seminar", "meeting", "review", "research", "verification", "skill", "plan")


def catalog_docs(root: Path) -> dict[str, Any]:
    """Governance/knowledge document surface grouped by kind (TASK-AR-545)."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for entity in load_catalog(root).get("entities", []):
        kind = str(entity.get("kind", ""))
        if kind not in DOC_KINDS:
            continue
        meta = entity.get("metadata") or {}
        groups.setdefault(kind, []).append(
            {
                "id": str(entity.get("id")),
                "title": entity.get("title"),
                "date": meta.get("date"),
                "path": meta.get("path"),
                "references": [r.get("target") for r in entity.get("relations", []) if r.get("type") == "references"],
            }
        )
    return {
        "kinds": {k: sorted(v, key=lambda row: str(row.get("date") or ""), reverse=True) for k, v in sorted(groups.items())},
        "counts": {k: len(v) for k, v in sorted(groups.items())},
    }


def _git_lines(root: Path, args: list[str], limit: int = 40) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()][:limit]


def entity_activity(root: Path, entity_id: str) -> dict[str, Any]:
    """Typed chronological activity/provenance timeline for an entity (TASK-AR-542).

    Unifies record provenance (review/verification/etc. that reference the entity,
    from the catalog backlinks) with git commits mentioning the entity id.
    """
    events: list[dict[str, Any]] = []
    catalog = load_catalog(root)
    by_id = {str(item.get("id")): item for item in catalog.get("entities", [])}
    for other in catalog.get("entities", []):
        for rel in other.get("relations", []):
            if str(rel.get("target")) == entity_id:
                meta = other.get("metadata") or {}
                events.append(
                    {
                        "type": rel.get("type"),
                        "actor": other.get("kind"),
                        "ref": str(other.get("id")),
                        "date": meta.get("date"),
                        "source": "record",
                    }
                )
    for line in _git_lines(root, ["log", "--grep", entity_id, "-n", "20", "--date=short", "--pretty=%ad %h %s"]):
        parts = line.split(" ", 2)
        events.append(
            {
                "type": "committed",
                "actor": "git",
                "ref": parts[1] if len(parts) > 1 else "",
                "date": parts[0] if parts else None,
                "source": "commit",
                "summary": parts[2] if len(parts) > 2 else line,
            }
        )
    events.sort(key=lambda event: str(event.get("date") or ""), reverse=True)
    return {"entity_id": entity_id, "events": events, "count": len(events)}


def scm_overview(root: Path) -> dict[str, Any]:
    """Live SCM surface: branches + recent commits from local git (TASK-AR-544)."""
    branches = [line.strip().lstrip("* ").strip() for line in _git_lines(root, ["branch", "--all", "--no-color"], limit=80)]
    commits: list[dict[str, Any]] = []
    for line in _git_lines(root, ["log", "-n", "20", "--date=short", "--pretty=%ad %h %s"], limit=20):
        parts = line.split(" ", 2)
        commits.append(
            {
                "date": parts[0] if parts else None,
                "hash": parts[1] if len(parts) > 1 else "",
                "summary": parts[2] if len(parts) > 2 else line,
            }
        )
    current = _git_lines(root, ["rev-parse", "--abbrev-ref", "HEAD"], limit=1)
    return {
        "current_branch": current[0] if current else None,
        "branch_count": len(branches),
        "branches": branches,
        "recent_commits": commits,
    }


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
WORK_STATE_BOARD_SCHEMA = "agent-runtime-work-state-board/v1"
_TASKSETS_BOARD_ACTIVITY_LIMIT = 5
_WORK_STATE_TASK_LIMIT = 12
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


def _load_org_read_api(root: Path, warnings: list[dict[str, str]]) -> Any | None:
    candidates = [
        root / "scripts" / "org_read_api.py",
        Path(__file__).resolve().parents[2] / "scripts" / "org_read_api.py",
    ]
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if not resolved.is_file():
            continue
        try:
            spec = importlib.util.spec_from_file_location("agent_runtime_org_read_api", resolved)
            if spec is None or spec.loader is None:
                raise RuntimeError("unable to load module spec")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as exc:  # pragma: no cover - defensive path
            warnings.append(_warning("work-state-read-api-error", _rel(root, resolved), str(exc)))
            return None
    warnings.append(_warning("work-state-read-api-missing", "scripts/org_read_api.py", "org read API not found"))
    return None


def build_work_state_board(
    root: Path,
    task_sets: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    now: str,
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    module = _load_org_read_api(root, warnings)
    raw: dict[str, Any] = {}
    if module is not None and hasattr(module, "work_state"):
        try:
            raw = module.work_state(root)
        except Exception as exc:  # pragma: no cover - defensive path
            warnings.append(_warning("work-state-read-error", "scripts/org_read_api.py::work_state", str(exc)))
            raw = {}

    taskset_meta = {str(item.get("id") or ""): item for item in task_sets if item.get("id")}
    task_meta = {str(item.get("id") or ""): item for item in tasks if item.get("id")}
    totals = {"waiting": 0, "active": 0, "review": 0, "done": 0, "tasksets": 0, "tasks": 0}
    cards: list[dict[str, Any]] = []
    for taskset_id, record in sorted(raw.items()):
        taskset_key = str(taskset_id or "").strip()
        if not taskset_key or not isinstance(record, dict):
            continue
        counts = {
            "waiting": int(record.get("waiting", 0) or 0),
            "active": int(record.get("active", 0) or 0),
            "review": int(record.get("review", 0) or 0),
            "done": int(record.get("done", 0) or 0),
        }
        total = sum(counts.values())
        if total == 0:
            continue
        for key, value in counts.items():
            totals[key] += value
        totals["tasksets"] += 1
        totals["tasks"] += total

        meta = taskset_meta.get(taskset_key, {})
        raw_tasks = record.get("tasks") or []
        task_rows: list[dict[str, Any]] = []
        if isinstance(raw_tasks, list):
            for raw_task in raw_tasks:
                if not isinstance(raw_task, dict):
                    continue
                task_id = str(raw_task.get("id") or "").strip()
                live = task_meta.get(task_id, {})
                task_rows.append(
                    {
                        "id": task_id,
                        "title": live.get("title") or task_id,
                        "status": raw_task.get("status") or live.get("status") or "",
                        "bucket": raw_task.get("bucket") or "waiting",
                        "priority": live.get("priority") or "",
                        "source_path": live.get("source_path") or "",
                    }
                )
        task_rows.sort(key=lambda item: (str(item.get("bucket") or ""), str(item.get("id") or "")))
        cards.append(
            {
                "id": taskset_key,
                "title": meta.get("display_name") or taskset_key,
                "initiative_id": meta.get("initiative_id") or "",
                "primary_alias": meta.get("primary_alias") or "",
                "counts": counts,
                "active_total": counts["active"] + counts["review"],
                "total": total,
                "tasks": task_rows[:_WORK_STATE_TASK_LIMIT],
                "task_limit": _WORK_STATE_TASK_LIMIT,
                "hidden_tasks": max(0, len(task_rows) - _WORK_STATE_TASK_LIMIT),
            }
        )
    cards.sort(key=lambda item: (-int(item["active_total"]), -int(item["counts"]["waiting"]), str(item["id"])))
    return {
        "schema": WORK_STATE_BOARD_SCHEMA,
        "generated_at": now,
        "source": "scripts/org_read_api.py::work_state",
        "totals": totals,
        "tasksets": cards,
    }


_TASKSET_CLAIM_ACTIVE_STATUSES = {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}
_TASKSET_CLAIM_DONE_STATUSES = {"released", "completed", "closed", "done", "verified"}
_TASKSET_CLAIM_GUARDED_STATUSES = {"blocked", "expired", "reaped", "cancelled", "stale"}


def _claim_relation_kind(claim: dict[str, Any]) -> str:
    status = str(claim.get("status") or "").strip().lower().replace("-", "_")
    phase = str(claim.get("phase") or "").strip().lower().replace("-", "_")
    status_text = str(claim.get("status_text") or "").strip().lower()
    combined = f"{status} {phase} {status_text}"
    if "interrupt" in combined:
        return "interrupted"
    if "guard" in combined or "block" in combined:
        return "guarded"
    if status in _TASKSET_CLAIM_GUARDED_STATUSES:
        return "guarded"
    if status in _TASKSET_CLAIM_ACTIVE_STATUSES:
        return "claimed"
    if status in _TASKSET_CLAIM_DONE_STATUSES:
        return "completed"
    return "unknown"


def _claim_actor_label(claim: dict[str, Any]) -> str:
    for key in ("display_name", "agent_instance_id", "agent_role", "claim_id"):
        value = str(claim.get(key) or "").strip()
        if value:
            return value
    return "claim"


def _claim_sort_key(claim: dict[str, Any]) -> str:
    return str(
        claim.get("last_heartbeat")
        or claim.get("updated_at")
        or claim.get("claimed_at")
        or claim.get("source", {}).get("mtime")
        or ""
    )


def _claim_relation_summary(claims: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"claimed": 0, "guarded": 0, "interrupted": 0, "completed": 0, "unknown": 0}
    latest_by_kind: dict[str, dict[str, Any]] = {}
    for claim in claims:
        kind = _claim_relation_kind(claim)
        counts[kind] = counts.get(kind, 0) + 1
        existing = latest_by_kind.get(kind)
        if existing is None or _claim_sort_key(claim) >= _claim_sort_key(existing):
            latest_by_kind[kind] = claim

    if counts["interrupted"]:
        state = "interrupted"
        latest = latest_by_kind["interrupted"]
        label = f"{counts['interrupted']} interrupted"
        command_state = "guarded"
        command_label = "interruption recovery"
    elif counts["guarded"]:
        state = "guarded"
        latest = latest_by_kind["guarded"]
        label = f"{counts['guarded']} guarded"
        command_state = "guarded"
        command_label = "claim guard review"
    elif counts["claimed"]:
        state = "claimed"
        latest = latest_by_kind["claimed"]
        label = f"claimed by {_claim_actor_label(latest)}"
        command_state = "guarded"
        command_label = "claim guard active"
    elif counts["completed"]:
        state = "default"
        latest = latest_by_kind["completed"]
        label = "released"
        command_state = "default"
        command_label = "proposal ready"
    else:
        state = "default"
        latest = {}
        label = ""
        command_state = "default"
        command_label = ""

    return {
        "count": len(claims),
        "counts": counts,
        "state": state,
        "label": label,
        "command_state": command_state,
        "command_label": command_label,
        "latest_claim_id": latest.get("claim_id", ""),
        "latest_actor": _claim_actor_label(latest) if latest else "",
    }


def _unique_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []
    for claim in claims:
        claim_id = str(claim.get("claim_id") or claim.get("id") or "").strip()
        if claim_id:
            by_id[claim_id] = claim
        else:
            anonymous.append(claim)
    return [*by_id.values(), *anonymous]


TASKSET_ATTENTION_LANES = (
    {
        "id": "active_claims",
        "label": "Active claims",
        "state": "claimed",
        "reason": "Claim path currently owns work.",
    },
    {
        "id": "guarded_recovery",
        "label": "Guarded or interrupted",
        "state": "guarded",
        "reason": "Claim guard or interrupted recovery needs review.",
    },
    {
        "id": "evidence_gaps",
        "label": "Stale or missing evidence",
        "state": "stale",
        "reason": "Taskset has no recent activity evidence in the board feed.",
    },
    {
        "id": "recently_changed",
        "label": "Recently changed",
        "state": "active",
        "reason": "Recent runtime activity is available for inspection.",
    },
    {
        "id": "ready_next",
        "label": "Ready next action",
        "state": "default",
        "reason": "Open taskset has no active claim guard.",
    },
)


def _attention_relation_state(card: dict[str, Any]) -> str:
    claim_summary = card.get("claim_summary") or {}
    claim_state = str(claim_summary.get("state") or "default").strip().lower()
    child_states = {
        str(child.get("relation_state") or (child.get("claim_summary") or {}).get("state") or "").strip().lower()
        for child in card.get("children", [])
    }
    if "interrupted" in child_states or claim_state == "interrupted":
        return "interrupted"
    if "guarded" in child_states or claim_state == "guarded":
        return "guarded"
    if "blocked" in child_states or claim_state == "blocked":
        return "blocked"
    if "claimed" in child_states or claim_state == "claimed":
        return "claimed"
    if claim_state == "active":
        return "active"
    return "default"


def _attention_card_item(card: dict[str, Any], lane: dict[str, str], reason: str, fields: list[str]) -> dict[str, Any]:
    claim_summary = card.get("claim_summary") or {}
    progress = card.get("progress") or {}
    relation_state = _attention_relation_state(card)
    return {
        "taskset_id": card.get("id") or "",
        "title": card.get("title") or card.get("id") or "",
        "state": relation_state if relation_state != "default" else lane["state"],
        "reason": reason or lane["reason"],
        "reason_fields": fields,
        "claim_label": claim_summary.get("label") or "",
        "command_label": claim_summary.get("command_label") or "",
        "progress_label": f"{progress.get('done', 0)}/{progress.get('total', 0)}",
        "status": card.get("status") or card.get("status_bucket") or "",
    }


def _taskset_attention_workspace(cards: list[dict[str, Any]]) -> dict[str, Any]:
    lanes: list[dict[str, Any]] = []
    for lane in TASKSET_ATTENTION_LANES:
        lane_items: list[dict[str, Any]] = []
        for card in cards:
            claim_summary = card.get("claim_summary") or {}
            claim_state = _attention_relation_state(card)
            progress = card.get("progress") or {}
            recent = card.get("recent_activity") or []
            children = card.get("children") or []
            open_children = [
                child
                for child in children
                if str(child.get("status_bucket") or "").strip().lower() != "completed"
                and str(child.get("phase") or "").strip().lower() != "done"
            ]

            if lane["id"] == "active_claims" and claim_state in {"claimed", "active"}:
                lane_items.append(
                    _attention_card_item(
                        card,
                        lane,
                        str(claim_summary.get("label") or "Active claim path"),
                        ["claim_summary.state", "claim_summary.label", "children[].claim_summary"],
                    )
                )
            elif lane["id"] == "guarded_recovery" and claim_state in {"guarded", "interrupted", "blocked"}:
                lane_items.append(
                    _attention_card_item(
                        card,
                        lane,
                        str(claim_summary.get("command_label") or claim_summary.get("label") or lane["reason"]),
                        ["claim_summary.state", "claim_summary.command_label", "children[].relation_state"],
                    )
                )
            elif lane["id"] == "evidence_gaps" and children and not recent:
                done = int(progress.get("done") or 0)
                total = int(progress.get("total") or 0)
                state = "missing" if done == 0 else "stale"
                lane_items.append(
                    _attention_card_item(
                        card,
                        {**lane, "state": state},
                        f"No recent activity evidence; progress {done}/{total}",
                        ["recent_activity", "progress.done", "progress.total"],
                    )
                )
            elif lane["id"] == "recently_changed" and recent:
                latest = recent[0]
                lane_items.append(
                    _attention_card_item(
                        card,
                        lane,
                        f"{latest.get('task_id') or card.get('id')} {latest.get('event') or 'activity'}",
                        ["recent_activity[].task_id", "recent_activity[].event", "recent_activity[].ts"],
                    )
                )
            elif lane["id"] == "ready_next" and open_children and claim_state == "default":
                lane_items.append(
                    _attention_card_item(
                        card,
                        lane,
                        f"{len(open_children)} open child tasks; claim path open",
                        ["children[].phase", "children[].status_bucket", "claim_summary.state"],
                    )
                )

        lanes.append(
            {
                **lane,
                "count": len(lane_items),
                "items": lane_items[:8],
            }
        )

    selected = ""
    for lane in lanes:
        if lane["items"]:
            selected = str(lane["items"][0]["taskset_id"])
            break
    return {
        "version": "taskset_attention_workspace/v1",
        "selected_taskset_id": selected or (cards[0]["id"] if cards else ""),
        "derived_from": [
            "claim_summary.state",
            "claim_summary.label",
            "claim_summary.command_state",
            "claim_summary.command_label",
            "recent_activity",
            "children[].phase",
            "children[].relation_state",
            "progress.done",
            "progress.total",
            "status_bucket",
            "assigned_agents",
        ],
        "lanes": lanes,
    }


def build_tasksets_board(
    work_explorer: dict[str, Any],
    tasks: list[dict[str, Any]],
    events: list[dict[str, Any]],
    task_claims: list[dict[str, Any]],
    now: str,
) -> dict[str, Any]:
    """Taskset-grouped board derived from the classification hierarchy.

    Progress and status distribution are computed from child task state only;
    no stored progress field from the snapshot is read. Live task records and
    runtime events are joined by id for owner and recent-activity context.
    """
    nodes = {node["id"]: node for node in work_explorer.get("nodes", [])}
    task_by_id = {str(task.get("id")): task for task in tasks if task.get("id")}
    claims_by_task: dict[str, list[dict[str, Any]]] = {}
    claims_by_taskset: dict[str, list[dict[str, Any]]] = {}
    for claim in task_claims:
        task_id = str(claim.get("task_id") or "").strip()
        taskset_id = str(claim.get("task_set_id") or claim.get("taskset_id") or "").strip()
        if task_id:
            claims_by_task.setdefault(task_id, []).append(claim)
        if taskset_id:
            claims_by_taskset.setdefault(taskset_id, []).append(claim)

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
        taskset_claims = list(claims_by_taskset.get(taskset_id, []))
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
            child_claims = claims_by_task.get(child_id, [])
            child_claim_summary = _claim_relation_summary(child_claims)
            child_relation_state = (
                child_claim_summary["state"]
                if child_claim_summary["state"] != "default"
                else ""
            )
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
                    "claim_summary": child_claim_summary,
                    "relation_state": child_relation_state,
                    "last_updated": last_updated,
                    "source_path": child.get("path") or live.get("source_path") or "",
                }
            )
            taskset_claims.extend(child_claims)

        rollup = node.get("rollup") or {"total": 0, "completed": 0, "in_progress": 0, "planned": 0, "pct": None}
        recent.sort(key=lambda item: str(item.get("ts") or ""), reverse=True)
        claim_summary = _claim_relation_summary(_unique_claims(taskset_claims))
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
                "claim_summary": claim_summary,
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
        "attention_workspace": _taskset_attention_workspace(cards),
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


# --- Team / role assignment model (TASK-AR-337) ----------------------------
# Canonical teams + roles are read once from agents/project/TEAMS.md (the host
# overlay). A task's team/role assignment is RESOLVED against this registry so
# the heatmap, the org chart and the board filters all agree on which team owns
# a task. Resolution order for a task's team: explicit `team` frontmatter ->
# the team that owns the task's `role`/`owner` role -> the taskset default team.

TEAMS_SCHEMA = "agent-runtime-teams/v1"
TEAMS_REL = "agents/project/TEAMS.md"


def _normalize_role(value: Any) -> str:
    """Canonicalize a role/owner token (lead_engineer / Lead Engineer -> lead-engineer)."""
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def load_teams(root: Path, now: str, warnings: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """Parse the canonical TEAMS.md host overlay into a team/role registry.

    Each block (``- team_id: X``) yields a team with its lead and the list of
    canonical roles it owns. A reverse role->team index lets task assignment be
    resolved against the canonical roles (TASK-AR-337). Missing file degrades to
    an empty, well-formed registry (no crash).
    """
    path = root / TEAMS_REL
    teams: list[dict[str, Any]] = []
    role_to_team: dict[str, str] = {}
    freshness = "present"
    last_updated = _mtime_iso(path)
    if not path.exists():
        freshness = "missing"
    else:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            if warnings is not None:
                warnings.append(_warning("teams-read-error", _rel(root, path), str(exc)))
            text = ""
            freshness = "missing"
        current: dict[str, Any] | None = None
        section: str | None = None
        for raw in text.splitlines():
            line = raw.rstrip()
            if not line.strip():
                continue
            stripped = line.strip()
            block = re.match(r"-\s*team_id:\s*(.+)$", stripped)
            if block:
                current = {"team_id": block.group(1).strip(), "purpose": "", "lead": "", "roles": []}
                teams.append(current)
                section = None
                continue
            if current is None:
                continue
            purpose = re.match(r"purpose:\s*(.+)$", stripped)
            if purpose:
                current["purpose"] = purpose.group(1).strip()
                section = None
                continue
            lead = re.match(r"lead:\s*(.+)$", stripped)
            if lead:
                current["lead"] = _normalize_role(lead.group(1))
                section = None
                continue
            if re.match(r"roles:\s*$", stripped):
                section = "roles"
                continue
            if re.match(r"canonical_context:\s*$", stripped):
                section = "context"
                continue
            item = re.match(r"-\s*(.+)$", stripped)
            if item and section == "roles":
                role = _normalize_role(item.group(1))
                if role:
                    current["roles"].append(role)
                    role_to_team.setdefault(role, current["team_id"])
                continue
            if item and section == "context":
                continue
    for team in teams:
        team["roles"] = _dedupe_strings(team["roles"])
        team["role_count"] = len(team["roles"])
    return {
        "schema": TEAMS_SCHEMA,
        "generated_at": now,
        "source_path": TEAMS_REL,
        "freshness": freshness,
        "last_updated": last_updated,
        "teams": teams,
        "role_to_team": role_to_team,
        "team_ids": [team["team_id"] for team in teams],
    }


def resolve_task_assignment(
    task: dict[str, Any],
    teams: dict[str, Any],
    taskset_team_defaults: dict[str, str],
) -> dict[str, Any]:
    """Resolve a task's canonical team/role assignment (TASK-AR-337).

    Returns the resolved ``team``, ``role`` and the ``assignment_source`` that
    explains how the team was chosen. This is the SINGLE place the team is
    decided so the heatmap, org chart and filters stay consistent.
    """
    role_to_team = teams.get("role_to_team") or {}
    raw_team = str(task.get("team") or "").strip()
    raw_role = _normalize_role(task.get("role") or task.get("owner_agent") or task.get("owner") or "")
    assignee = str(task.get("assignee") or "").strip() or None

    team = raw_team
    source = "task_team" if raw_team else None
    if not team and raw_role and raw_role in role_to_team:
        team = role_to_team[raw_role]
        source = "role"
    if not team:
        task_set_id = str(task.get("task_set_id") or "").strip()
        default_team = taskset_team_defaults.get(task_set_id)
        if default_team:
            team = default_team
            source = "taskset_default"
    if not team:
        team = "unassigned"
        source = source or "unassigned"
    return {
        "team": team,
        "role": raw_role or None,
        "assignee": assignee,
        "assignment_source": source,
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


# --- 2D Office Map (TASK-AR-364) -------------------------------------------
# Place agents on a company-like 2D map so org activity reads at a glance
# (Smallville / Generative Agents pattern, arXiv 2304.03442). This derivation
# is READ-ONLY: it computes a world -> areas tree (one room per team function)
# plus a per-agent position + action snapshot, all from the already-derived
# team_agents presence cards and the runtime event log. Nothing here mutates
# stored state and no pathfinding is performed -- agents teleport to the room
# their role (or live meeting) maps to.
#
# Emoji glyphs are served from THIS (Python) side only. The console JS guard
# requires app.js to stay ASCII (cp949 node-check), so the front-end renders the
# glyph from the ``glyph`` field on each agent / the ACTION glyph table here and
# never inlines a non-ASCII literal of its own.
OFFICE_MAP_SCHEMA = "agent-runtime-office-map/v1"
OFFICE_MAP_WORLD_ID = "headquarters"
OFFICE_MAP_WORLD_NAME = "Agent Runtime HQ"

# Action -> wordless emoji glyph. The four canonical actions in the task spec are
# working / recording / reviewing / idle; ``meeting`` is an additional state for
# agents pulled into a live meeting. Glyphs are unicode literals kept on the
# Python side so the served JS stays ASCII.
OFFICE_ACTION_GLYPHS: dict[str, str] = {
    "working": "\U0001F4BB",    # laptop computer
    "recording": "\U0001F4DD",  # memo
    "reviewing": "\U0001F50D",  # magnifying glass
    "meeting": "\U0001F465",    # busts in silhouette
    "idle": "\U0001F4A4",       # zzz / sleep
}
OFFICE_ACTION_LABELS: dict[str, str] = {
    "working": "working",
    "recording": "recording",
    "reviewing": "reviewing",
    "meeting": "in meeting",
    "idle": "idle",
}

# Static rooms (areas) of the office. Each room is a function/team space with a
# grid rectangle (col/row spans on an OFFICE_MAP_COLS x OFFICE_MAP_ROWS lattice)
# and a semantic color token (defined in BOTH console theme blocks). ``role_kinds``
# are substring markers matched against a normalized role to assign a room.
OFFICE_MAP_COLS = 12
OFFICE_MAP_ROWS = 8
OFFICE_ROOMS: tuple[dict[str, Any], ...] = (
    {
        "id": "planning",
        "name": "Planning Room",
        "token": "violet",
        "rect": {"col": 0, "row": 0, "cols": 6, "rows": 4},
        "role_markers": (
            "plan", "roadmap", "task-architect", "prioritization",
            "ceo", "owner", "secretary", "product",
        ),
    },
    {
        "id": "dev",
        "name": "Dev Room",
        "token": "blue",
        "rect": {"col": 6, "row": 0, "cols": 6, "rows": 4},
        "role_markers": (
            "lead-engineer", "engineer", "backend", "frontend",
            "ci-cd", "worktree", "dispatcher", "dev",
        ),
    },
    {
        "id": "qa",
        "name": "QA Room",
        "token": "amber",
        "rect": {"col": 0, "row": 4, "cols": 4, "rows": 4},
        "role_markers": ("qa", "audit", "compatibility", "test", "quality"),
    },
    {
        "id": "release",
        "name": "Release Room",
        "token": "success",
        "rect": {"col": 8, "row": 4, "cols": 4, "rows": 4},
        "role_markers": (
            "version", "release", "evidence", "doc-steward",
            "scribe", "librarian", "governor", "deploy",
        ),
    },
    {
        "id": "meeting",
        "name": "Meeting Room",
        "token": "primary",
        "rect": {"col": 4, "row": 4, "cols": 4, "rows": 4},
        # The meeting room is reached by live state (in-meeting agents), not by a
        # role mapping; it is the fallback room for any unmatched role too.
        "role_markers": (),
    },
)
OFFICE_DEFAULT_ROOM_ID = "meeting"


def _office_room_for_role(role: str) -> str:
    """Map a normalized role to a room id by substring markers (fallback room)."""
    normalized = _normalize_role(role)
    if not normalized:
        return OFFICE_DEFAULT_ROOM_ID
    for room in OFFICE_ROOMS:
        for marker in room["role_markers"]:
            if marker in normalized:
                return room["id"]
    return OFFICE_DEFAULT_ROOM_ID


# Event-name (substring, lowercased) -> office action. Used to upgrade an
# otherwise "working" agent to "recording" when its most recent runtime activity
# was a write/record/log/note style event (the memo glyph). Order is irrelevant;
# any marker match flips the action to recording.
_OFFICE_RECORDING_EVENT_MARKERS = (
    "record", "write", "wrote", "log", "note", "memo",
    "evidence", "report", "scribe", "document", "minutes",
)


def _office_action_for_card(card: dict[str, Any], activity: dict[str, Any] | None) -> str:
    """Derive the wordless action for an agent presence card.

    Presence is the primary signal (working / reviewing / in_meeting), with an
    upgrade to ``recording`` when the agent's most recent event looks like a
    write/log/record. Anything else (online without a claim, offline) reads as
    ``idle``.
    """
    presence = str(card.get("presence") or "offline").strip().lower()
    if presence == "in_meeting":
        return "meeting"
    if presence == "reviewing":
        return "reviewing"
    if presence == "working":
        event_name = str((activity or {}).get("event") or "").lower()
        if any(marker in event_name for marker in _OFFICE_RECORDING_EVENT_MARKERS):
            return "recording"
        return "working"
    # online (session up but no active claim) or offline both read as idle.
    return "idle"


def build_office_map(
    team_agents: dict[str, Any],
    events: list[dict[str, Any]],
    now: str,
) -> dict[str, Any]:
    """Derive the 2D office map: world -> areas tree + per-agent placement.

    Read-only. Agents are placed in the room their role maps to, EXCEPT agents
    in a live meeting (presence ``in_meeting``) who are relocated to the meeting
    room (TASK-AR-361 integration). Each agent carries an (x, y) cell within its
    room, a wordless action, and the emoji glyph for that action (served from the
    Python side so app.js stays ASCII). Degrades to an empty-but-well-formed map
    when there are no agents.
    """
    # Most-recent event per role (for the recording-action upgrade).
    activity_by_role: dict[str, dict[str, Any]] = {}
    for event in events or []:
        role = _normalize_role(event.get("role") or event.get("actor") or "")
        if not role:
            continue
        ts = str(event.get("created_at") or event.get("ts") or "")
        existing = activity_by_role.get(role)
        if existing is None or ts > str(existing.get("ts") or ""):
            activity_by_role[role] = {
                "event": event.get("event") or event.get("type") or "",
                "task_id": event.get("task_id") or "",
                "ts": ts,
            }

    # Flatten the team_agents cards into placement-ready agent records.
    agents_out: list[dict[str, Any]] = []
    for team in team_agents.get("teams", []) or []:
        team_id = str(team.get("team_id") or team.get("id") or "")
        for card in team.get("agents", []) or []:
            role = str(card.get("role") or "").strip()
            if not role:
                continue
            activity = activity_by_role.get(_normalize_role(role))
            action = _office_action_for_card(card, activity)
            # Meeting integration: an in-meeting agent always sits in the meeting
            # room regardless of its role's home room.
            room_id = "meeting" if action == "meeting" else _office_room_for_role(role)
            agents_out.append(
                {
                    "id": card.get("id"),
                    "role": role,
                    "callsign": card.get("callsign") or role,
                    "display_name": card.get("display_name") or card.get("callsign") or role,
                    "avatar": card.get("avatar") or "AG",
                    "team_id": team_id,
                    "presence": card.get("presence") or "offline",
                    "online": bool(card.get("online")),
                    "current_task_id": card.get("current_task_id"),
                    "room_id": room_id,
                    "action": action,
                    "action_label": OFFICE_ACTION_LABELS.get(action, action),
                    "glyph": OFFICE_ACTION_GLYPHS.get(action, OFFICE_ACTION_GLYPHS["idle"]),
                }
            )

    # Stable ordering so the layout is identical across refreshes.
    agents_out.sort(key=lambda a: (str(a.get("room_id")), str(a.get("role")), str(a.get("id"))))

    # Assign a deterministic cell (x, y) to each agent inside its room. Agents in
    # the same room are laid out left-to-right, top-to-bottom on a small grid so
    # they never overlap; coordinates are normalized 0..1 within the room rect.
    by_room: dict[str, list[dict[str, Any]]] = {}
    for agent in agents_out:
        by_room.setdefault(str(agent["room_id"]), []).append(agent)

    rooms_out: list[dict[str, Any]] = []
    action_counts: dict[str, int] = {}
    for room in OFFICE_ROOMS:
        occupants = by_room.get(room["id"], [])
        count = len(occupants)
        # Pack occupants into a near-square sub-grid within the room.
        per_row = max(1, int(count ** 0.5 + 0.999)) if count else 1
        for index, agent in enumerate(occupants):
            col = index % per_row
            row = index // per_row
            rows_used = max(1, (count + per_row - 1) // per_row)
            # Normalized cell center within the room (0..1), padded from edges.
            fx = (col + 0.5) / per_row
            fy = (row + 0.5) / rows_used
            agent["cell"] = {"fx": round(fx, 4), "fy": round(fy, 4)}
            agent["room_name"] = room["name"]
            action_counts[agent["action"]] = action_counts.get(agent["action"], 0) + 1
        rooms_out.append(
            {
                "id": room["id"],
                "name": room["name"],
                "token": room["token"],
                "rect": dict(room["rect"]),
                "occupant_count": count,
                "occupant_ids": [str(a.get("id")) for a in occupants],
            }
        )

    world = {
        "id": OFFICE_MAP_WORLD_ID,
        "name": OFFICE_MAP_WORLD_NAME,
        "cols": OFFICE_MAP_COLS,
        "rows": OFFICE_MAP_ROWS,
        "areas": [room["id"] for room in OFFICE_ROOMS],
    }

    return {
        "schema": OFFICE_MAP_SCHEMA,
        "generated_at": now,
        "world": world,
        "rooms": rooms_out,
        "agents": agents_out,
        "action_glyphs": dict(OFFICE_ACTION_GLYPHS),
        "action_labels": dict(OFFICE_ACTION_LABELS),
        "totals": {
            "agents": len(agents_out),
            "rooms": len(rooms_out),
            "actions": dict(sorted(action_counts.items())),
            "in_meeting": sum(1 for a in agents_out if a["action"] == "meeting"),
        },
    }


# --- Growth system (TASK-AR-363) -------------------------------------------
# Measure/display project maturity like an evolving character: a project level
# from a cumulative-XP curve, a business-stage title (garage -> seed -> startup
# -> scaleup -> unicorn) from milestone/release achievement, and per-agent XP
# reused from the AR-324 team_agents cards (role-based completion, team first).
#
# RESEARCH-BACKED GUARDRAILS (acceptance-critical, enforced here in code):
#   * Token consumption NEVER adds XP. XP is a weighted sum of *outcomes only*
#     (completed tasks, gate passes, test growth, review outputs). Token spend
#     feeds only the SEPARATE "efficiency" stat (tokens/task) -- this is the
#     anti-waste guardrail: spending more tokens can never raise the score.
#   * NO punishment / decay (Habitica backfire): XP is monotonic and cumulative;
#     there is no field that subtracts XP. Rework is reported as a neutral
#     efficiency stat, never as an XP penalty.
#   * NO streak / consecutive-day pressure (GitHub removed it): there is NO
#     streak or consecutive-day counter anywhere in this payload.
#   * Feedback visibility: the formula weights and every contributing count are
#     published in the payload so the score is explainable.
#   * Global toggle: self-contained ``enabled`` flag (default on). Degrades
#     gracefully if the AR-340 gamification policy is absent (policy not yet
#     landed) -- when present its ``enabled`` value is honoured.
GROWTH_SCHEMA = "agent-runtime-growth/v1"
# Optional AR-340 gamification policy file. AR-340 lands separately; if the file
# is missing the growth system stays fully self-contained and defaults to on.
GAMIFICATION_POLICY_REL = "agents/project/ui/GAMIFICATION-POLICY.json"
# XP weights -- a weighted sum of OUTCOME counts. Token spend is deliberately
# absent: there is no token weight, so tokens can never contribute XP.
_GROWTH_XP_PER_COMPLETED_TASK = 100
_GROWTH_XP_PER_GATE_PASS = 40
_GROWTH_XP_PER_TEST_GROWTH = 15
_GROWTH_XP_PER_REVIEW = 25
# Business-stage ladder. Stage is unlocked by cumulative milestone+release
# achievement (a non-token, non-XP achievement signal). ASCII keys only so the
# JS keeps no KR string literals (cp949 node-check guard); KR labels live here.
GROWTH_STAGES: tuple[dict[str, Any], ...] = (
    {"key": "garage", "label_ko": "가레이지", "min_achievements": 0},
    {"key": "seed", "label_ko": "시드", "min_achievements": 1},
    {"key": "startup", "label_ko": "스타트업", "min_achievements": 3},
    {"key": "scaleup", "label_ko": "스케일업", "min_achievements": 6},
    {"key": "unicorn", "label_ko": "유니콘", "min_achievements": 10},
)
# Tolerant event-name substrings -> growth signal. The event log is append-only
# and heterogeneous, so we match lowercased substrings rather than exact names.
_GROWTH_GATE_PASS_MARKERS = ("gate_pass", "gate.pass", "gate_passed", "gate.passed", "gate_green")
_GROWTH_TEST_MARKERS = ("test_added", "tests_added", "test.added", "test_growth", "tests_passed", "test.pass")
# Rework markers feed ONLY the neutral efficiency stat -- never XP, never a
# penalty. A reopened/reverted/regressed signal counts as one rework unit.
_GROWTH_REWORK_MARKERS = ("reopen", "revert", "regress", "rework", "rollback", "reverted")
_GROWTH_COMPLETED_TASK_STATES = {"completed", "done", "released", "verified", "archived", "완료"}


def _growth_int(value: Any) -> int:
    """Coerce a tolerant numeric (int/float/str) into a non-negative int."""
    try:
        number = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return 0
    return max(0, number)


def _growth_event_tokens(event: dict[str, Any]) -> int:
    """Read an optional token-usage field off an event (efficiency stat only).

    Tolerates several field names. CRITICAL: the returned value feeds ONLY the
    efficiency stat (tokens/task); it is NEVER summed into XP.
    """
    for key in ("tokens", "tokens_used", "total_tokens", "token_count", "usage_tokens"):
        if key in event:
            return _growth_int(event.get(key))
    usage = event.get("usage")
    if isinstance(usage, dict):
        for key in ("total_tokens", "tokens", "input_tokens"):
            if key in usage:
                return _growth_int(usage.get(key))
    return 0


def load_gamification_policy(root: Path, now: str) -> dict[str, Any]:
    """Read the optional AR-340 gamification policy; self-contained default.

    AR-340 lands separately. When the policy file is absent we return a
    well-formed default (enabled=True, present=False) so the growth system never
    depends on 340 having shipped. When present, its ``enabled`` flag is honoured.
    """
    path = root / GAMIFICATION_POLICY_REL
    default = {
        "enabled": True,
        "present": False,
        "source": "default",
        "source_path": GAMIFICATION_POLICY_REL,
    }
    if not path.exists():
        return default
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {**default, "present": True, "source": "unreadable"}
    if not isinstance(payload, dict):
        return {**default, "present": True, "source": "invalid"}
    enabled = payload.get("enabled")
    return {
        "enabled": True if enabled is None else bool(enabled),
        "present": True,
        "source": "policy",
        "source_path": GAMIFICATION_POLICY_REL,
    }


def _growth_business_stage(achievements: int) -> dict[str, Any]:
    """Pick the business-stage title unlocked by milestone/release achievement.

    Stage is a pure function of the achievement count (milestones done +
    releases shipped). It is NOT a function of XP or tokens -- it is a separate
    "release achievement" title as required by the spec.
    """
    safe = max(0, int(achievements))
    current = GROWTH_STAGES[0]
    next_stage: dict[str, Any] | None = None
    for index, stage in enumerate(GROWTH_STAGES):
        if safe >= int(stage["min_achievements"]):
            current = stage
            next_stage = GROWTH_STAGES[index + 1] if index + 1 < len(GROWTH_STAGES) else None
    to_next = None
    if next_stage is not None:
        to_next = max(0, int(next_stage["min_achievements"]) - safe)
    return {
        "key": current["key"],
        "label_ko": current["label_ko"],
        "achievements": safe,
        "next_key": next_stage["key"] if next_stage else None,
        "next_label_ko": next_stage["label_ko"] if next_stage else None,
        "achievements_to_next": to_next,
        "ladder": [stage["key"] for stage in GROWTH_STAGES],
    }


def build_growth(
    tasks: list[dict[str, Any]],
    task_claims: list[dict[str, Any]],
    events: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    team_agents: dict[str, Any],
    roadmap_timeline: dict[str, Any],
    policy: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    """Project-maturity growth payload (computed-only; tokens excluded from XP).

    Cumulative XP = weighted sum of OUTCOME counts only:
        completed-task count, gate passes, test growth, review outputs.
    Token spend is NEVER summed into XP; it feeds only the SEPARATE efficiency
    stat (tokens/task). XP is monotonic/cumulative -- no decay, no penalty, no
    streak. Project Lv is read off the same cumulative-XP curve as the agent
    cards (AR-324). Business stage is a milestone/release-achievement title.
    """
    # --- OUTCOME counts (XP inputs) ---------------------------------------
    # Completed tasks: union of completed task claims and tasks already in a
    # done lane/status. Counting ids (a set) keeps each task worth XP once.
    completed_task_ids: set[str] = set()
    for claim in task_claims:
        if str(claim.get("status") or "").strip().lower() == "completed":
            completed_task_ids.add(str(claim.get("task_id") or claim.get("claim_id") or ""))
    for task in tasks:
        status = str(task.get("status") or "").strip().lower()
        if status in _GROWTH_COMPLETED_TASK_STATES or str(task.get("lane") or "") == "Done":
            completed_task_ids.add(str(task.get("id") or ""))
    completed_task_ids.discard("")
    completed_tasks = len(completed_task_ids)

    gate_passes = 0
    test_growth = 0
    rework_events = 0
    token_total = 0
    for event in events:
        name = str(event.get("event") or event.get("type") or "").lower()
        if any(marker in name for marker in _GROWTH_GATE_PASS_MARKERS):
            gate_passes += 1
        if any(marker in name for marker in _GROWTH_TEST_MARKERS):
            test_growth += _growth_int(event.get("count")) or 1
        if any(marker in name for marker in _GROWTH_REWORK_MARKERS):
            rework_events += 1
        # Token spend is read for the efficiency stat ONLY (never XP).
        token_total += _growth_event_tokens(event)

    review_outputs = len(reviews)

    # --- Cumulative XP (weighted sum of OUTCOMES only; NO token term) ------
    contributions = {
        "completed_tasks": completed_tasks * _GROWTH_XP_PER_COMPLETED_TASK,
        "gate_passes": gate_passes * _GROWTH_XP_PER_GATE_PASS,
        "test_growth": test_growth * _GROWTH_XP_PER_TEST_GROWTH,
        "review_outputs": review_outputs * _GROWTH_XP_PER_REVIEW,
    }
    cumulative_xp = sum(contributions.values())
    project_curve = _team_agent_level(cumulative_xp)

    # --- Business stage from milestone/release achievement (not XP/tokens) -
    summary = roadmap_timeline.get("summary") if isinstance(roadmap_timeline, dict) else {}
    summary = summary if isinstance(summary, dict) else {}
    milestones_done = _growth_int(summary.get("milestones_done"))
    releases = roadmap_timeline.get("releases") if isinstance(roadmap_timeline, dict) else []
    releases_shipped = sum(
        1
        for release in (releases or [])
        if isinstance(release, dict) and str(release.get("status_bucket") or "") == "completed"
    )
    achievements = milestones_done + releases_shipped
    stage = _growth_business_stage(achievements)

    # --- Per-agent XP (role-based; reuse AR-324 team_agents, team first) ---
    agent_rows: list[dict[str, Any]] = []
    for team in (team_agents.get("teams", []) if isinstance(team_agents, dict) else []) or []:
        team_id = str(team.get("team_id") or team.get("id") or "")
        for card in team.get("agents", []) or []:
            agent_rows.append(
                {
                    "id": card.get("id"),
                    "role": card.get("role"),
                    "callsign": card.get("callsign"),
                    "team_id": team_id,
                    "level": card.get("level", 1),
                    "xp": card.get("xp", 0),
                    "xp_pct": card.get("xp_pct", 0),
                    "completed_tasks": (card.get("lifetime") or {}).get("completed_tasks", 0),
                }
            )
    # Team-level XP roll-up (team achievement prioritized over the individual).
    team_rows: list[dict[str, Any]] = []
    for team in (team_agents.get("teams", []) if isinstance(team_agents, dict) else []) or []:
        team_id = str(team.get("team_id") or team.get("id") or "")
        members = team.get("agents", []) or []
        team_xp = sum(_growth_int(card.get("xp")) for card in members)
        team_curve = _team_agent_level(team_xp)
        team_rows.append(
            {
                "team_id": team_id,
                "xp": team_xp,
                "level": team_curve["level"],
                "xp_pct": team_curve["xp_pct"],
                "agent_count": len(members),
            }
        )
    team_rows.sort(key=lambda row: (-int(row["xp"]), row["team_id"]))
    agent_rows.sort(key=lambda row: (-int(row["xp"] or 0), str(row["role"] or "")))

    # --- Efficiency stats (SEPARATE; tokens/task + rework rate) ------------
    # These never affect XP. tokens/task is the anti-waste signal; rework rate is
    # a neutral quality signal (NOT a penalty).
    tokens_per_task = round(token_total / completed_tasks, 1) if completed_tasks else 0
    rework_rate_pct = round((rework_events / completed_tasks) * 100, 1) if completed_tasks else 0
    efficiency = {
        "token_total": token_total,
        "completed_tasks": completed_tasks,
        "tokens_per_task": tokens_per_task,
        "rework_events": rework_events,
        "rework_rate_pct": rework_rate_pct,
        "note": "efficiency stats are reported separately; they never affect XP",
    }

    return {
        "schema": GROWTH_SCHEMA,
        "generated_at": now,
        # Global toggle (self-contained). Honour AR-340 policy when present.
        "enabled": bool(policy.get("enabled", True)),
        "policy": policy,
        # Project level off the cumulative-XP curve.
        "project": {
            "level": project_curve["level"],
            "cumulative_xp": cumulative_xp,
            "xp_into_level": project_curve["xp_into_level"],
            "xp_for_next": project_curve["xp_for_next"],
            "xp_pct": project_curve["xp_pct"],
        },
        "business_stage": stage,
        # XP formula is published for feedback visibility (no token term exists).
        "xp_formula": {
            "weights": {
                "completed_task": _GROWTH_XP_PER_COMPLETED_TASK,
                "gate_pass": _GROWTH_XP_PER_GATE_PASS,
                "test_growth": _GROWTH_XP_PER_TEST_GROWTH,
                "review_output": _GROWTH_XP_PER_REVIEW,
            },
            "counts": {
                "completed_tasks": completed_tasks,
                "gate_passes": gate_passes,
                "test_growth": test_growth,
                "review_outputs": review_outputs,
            },
            "contributions": contributions,
            "cumulative_xp": cumulative_xp,
            "token_spend_excluded": True,
            "note": "token consumption is excluded from XP by design (anti-waste)",
        },
        "efficiency": efficiency,
        "agents": agent_rows,
        "teams": team_rows,
        # Explicit guardrail manifest so the front-end and tests can assert the
        # research-backed constraints are honoured. These flags are descriptive;
        # the absence of streak/penalty fields elsewhere is what enforces them.
        "guardrails": {
            "token_spend_excluded_from_xp": True,
            "monotonic_cumulative_xp": True,
            "no_streak_pressure": True,
            "no_punishment_mechanic": True,
            "feedback_visible": True,
            "global_toggle": True,
        },
    }


# --- Workload heatmap (TASK-AR-337) ----------------------------------------
# A per-agent and per-team load grid (assignee/team x period) derived from the
# resolved task assignments. Each open task contributes one "load unit" to its
# assignee's and its team's cell for the period its due/updated date falls in.
# Cells are classified idle / normal / busy / overload from the load count so
# the heatmap can color overload and idle without inventing per-cell colors.

WORKLOAD_HEATMAP_SCHEMA = "agent-runtime-workload-heatmap/v1"
# Per-period open-task thresholds. <= idle: idle; <= busy: normal; <= overload:
# busy; above overload: overload. Tuned so a single agent juggling >3 open
# tasks in one period reads as "overload".
_WORKLOAD_IDLE_MAX = 0
_WORKLOAD_NORMAL_MAX = 2
_WORKLOAD_BUSY_MAX = 3
_WORKLOAD_PERIODS = 6


def _workload_period_key(value: Any, now: str) -> str:
    """Bucket a task date into a YYYY-MM period key (falls back to current month)."""
    text = str(value or "").strip()
    match = re.match(r"(\d{4})-(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    fallback = re.match(r"(\d{4})-(\d{2})", str(now or ""))
    return f"{fallback.group(1)}-{fallback.group(2)}" if fallback else "unknown"


def _workload_band(load: int) -> str:
    if load <= _WORKLOAD_IDLE_MAX:
        return "idle"
    if load <= _WORKLOAD_NORMAL_MAX:
        return "normal"
    if load <= _WORKLOAD_BUSY_MAX:
        return "busy"
    return "overload"


def derive_taskset_team_defaults(tasks: list[dict[str, Any]], teams: dict[str, Any]) -> dict[str, str]:
    """Pick a default team per taskset from its tasks' explicit/role assignments.

    A task that names no team but belongs to a taskset inherits the taskset's
    default team (the team most of its siblings resolve to). This realizes the
    "taskset -> team default assignment" requirement (TASK-AR-337) without a new
    canonical field: the default is the consensus of the taskset's tasks.
    """
    role_to_team = teams.get("role_to_team") or {}
    votes: dict[str, dict[str, int]] = {}
    for task in tasks:
        task_set_id = str(task.get("task_set_id") or "").strip()
        if not task_set_id:
            continue
        explicit = str(task.get("team") or "").strip()
        role = _normalize_role(task.get("role") or task.get("owner_agent") or task.get("owner") or "")
        team = explicit or role_to_team.get(role)
        if not team:
            continue
        tally = votes.setdefault(task_set_id, {})
        # Explicit team assignments weigh more than role-derived ones.
        tally[team] = tally.get(team, 0) + (2 if explicit else 1)
    defaults: dict[str, str] = {}
    for task_set_id, tally in votes.items():
        defaults[task_set_id] = max(sorted(tally), key=lambda team: tally[team])
    return defaults


def enrich_tasks_with_assignment(
    tasks: list[dict[str, Any]],
    teams: dict[str, Any],
    taskset_team_defaults: dict[str, str],
) -> None:
    """Stamp each task with its RESOLVED team/role assignment (TASK-AR-337).

    The same resolution drives the heatmap, so a task shows the same assigned
    team in the org chart, the heatmap and the board team filter. Mutates each
    task dict in place by adding ``assigned_team`` / ``assigned_role`` /
    ``assigned_assignee`` / ``assignment_source``.
    """
    for task in tasks:
        assignment = resolve_task_assignment(task, teams, taskset_team_defaults)
        task["assigned_team"] = assignment["team"]
        task["assigned_role"] = assignment["role"]
        task["assigned_assignee"] = assignment["assignee"]
        task["assignment_source"] = assignment["assignment_source"]


def build_workload_heatmap(
    tasks: list[dict[str, Any]],
    teams: dict[str, Any],
    taskset_team_defaults: dict[str, str],
    now: str,
) -> dict[str, Any]:
    """Aggregate open-task load per agent and per team across recent periods.

    The same resolved team/role assignment used by the board filters and the org
    chart feeds this grid, so a task's team is the same everywhere. Intensity is
    expressed as a normalized 0..1 ``intensity`` plus a discrete ``band`` so the
    renderer can map it to opacity over a single token color (never raw rgba).
    """
    periods: set[str] = set()
    agents: dict[str, dict[str, Any]] = {}
    team_rows: dict[str, dict[str, Any]] = {}

    def _row(table: dict[str, dict[str, Any]], key: str, kind: str) -> dict[str, Any]:
        row = table.get(key)
        if row is None:
            row = table[key] = {"id": key, "kind": kind, "cells": {}, "open_total": 0}
        return row

    for task in tasks:
        if not _task_is_open(task):
            continue
        assignment = resolve_task_assignment(task, teams, taskset_team_defaults)
        period = _workload_period_key(task.get("due") or task.get("updated_at") or task.get("created_at"), now)
        periods.add(period)
        team_id = assignment["team"]
        agent_id = assignment["assignee"] or assignment["role"] or "unassigned"
        for table, key, kind in ((agents, agent_id, "agent"), (team_rows, team_id, "team")):
            row = _row(table, key, kind)
            cell = row["cells"].setdefault(period, {"load": 0, "task_ids": []})
            cell["load"] += 1
            cell["task_ids"].append(str(task.get("id") or ""))
            row["open_total"] += 1

    period_list = sorted(periods)[-_WORKLOAD_PERIODS:] if periods else []
    max_load = 1
    for table in (agents, team_rows):
        for row in table.values():
            for cell in row["cells"].values():
                max_load = max(max_load, int(cell["load"]))

    def _finalize(table: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for key in sorted(table):
            row = table[key]
            cells = []
            for period in period_list:
                cell = row["cells"].get(period, {"load": 0, "task_ids": []})
                load = int(cell["load"])
                cells.append(
                    {
                        "period": period,
                        "load": load,
                        "band": _workload_band(load),
                        "intensity": round(load / max_load, 3) if max_load else 0.0,
                        "task_ids": [tid for tid in cell.get("task_ids", []) if tid],
                    }
                )
            rows.append(
                {
                    "id": row["id"],
                    "kind": row["kind"],
                    "open_total": row["open_total"],
                    "cells": cells,
                    "peak_band": _workload_band(max((c["load"] for c in cells), default=0)),
                }
            )
        return rows

    agent_rows = _finalize(agents)
    finalized_team_rows = _finalize(team_rows)
    return {
        "schema": WORKLOAD_HEATMAP_SCHEMA,
        "generated_at": now,
        "periods": period_list,
        "agents": agent_rows,
        "teams": finalized_team_rows,
        "max_load": max_load,
        "bands": ["idle", "normal", "busy", "overload"],
        "thresholds": {
            "idle_max": _WORKLOAD_IDLE_MAX,
            "normal_max": _WORKLOAD_NORMAL_MAX,
            "busy_max": _WORKLOAD_BUSY_MAX,
        },
        "totals": {
            "agents": len(agent_rows),
            "teams": len(finalized_team_rows),
            "open_tasks": sum(row["open_total"] for row in agent_rows),
            "overloaded": sum(1 for row in agent_rows if row["peak_band"] == "overload"),
            "idle": sum(1 for row in agent_rows if row["peak_band"] == "idle"),
        },
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


KNOWLEDGE_GRAPH_VIEW_SCHEMA = "agent-runtime-knowledge-graph-view/v1"
KNOWLEDGE_GRAPH_VIEW_LIMIT = 140
WIKI_PAGE_SCHEMA = "agent-runtime-wiki-page/v1"
WIKI_SEARCH_SCHEMA = "agent-runtime-wiki-search/v1"
WIKI_ASK_SCHEMA = "agent-runtime-wiki-ask/v1"
WIKI_MINIGRAPH_LIMIT = 48
WIKI_SEARCH_LIMIT = 20
WIKI_ASK_EVIDENCE_LIMIT = 5


def _ensure_knowledge_import_paths(root: Path) -> None:
    root_path = Path(root).resolve()
    repo_root = Path(__file__).resolve().parents[2]
    for path in (root_path, root_path / "scripts", repo_root, repo_root / "scripts"):
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)


def _knowledge_source_metadata(root: Path, node: dict[str, Any], *, now: str) -> dict[str, Any]:
    metadata = node.get("metadata") or {}
    source = str(metadata.get("path") or "").strip()
    source_path = Path(root) / source if source else Path(root)
    updated_at = _mtime_iso(source_path) if source else None
    return {
        "owner": metadata.get("owner") or metadata.get("agent_role"),
        "status": metadata.get("status"),
        "updated_at": updated_at or metadata.get("date") or metadata.get("updated_at"),
        "freshness": _path_freshness(source_path) if source else "unknown",
        "lineage": metadata.get("fingerprint"),
        "source": source or None,
    }


def _wiki_node_summary(
    node: dict[str, Any],
    *,
    root_id: str | None = None,
    lens: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    node_id = str(node.get("id") or "")
    stats = (lens or {}).get(node_id, {})
    edge_types = sorted(str(item) for item in stats.get("edge_types", []) if str(item).strip())
    return {
        "id": node_id,
        "kind": str(node.get("kind") or "entity"),
        "title": str(node.get("title") or node_id),
        "root": bool(root_id and node_id == root_id),
        "role": str(stats.get("role") or ("root" if root_id and node_id == root_id else "neighbor")),
        "degree": int(stats.get("degree") or 0),
        "incoming_count": int(stats.get("incoming_count") or 0),
        "outgoing_count": int(stats.get("outgoing_count") or 0),
        "edge_types": edge_types,
    }


def _wiki_search_score(node: dict[str, Any], query: str) -> int:
    needle = (query or "").strip().lower()
    if not needle:
        return 0
    node_id = str(node.get("id") or "")
    title = str(node.get("title") or "")
    metadata = json.dumps(node.get("metadata") or {}, ensure_ascii=False).lower()
    if needle in node_id.lower():
        return 3
    if needle in title.lower():
        return 2
    if needle in metadata:
        return 1
    return 0


def _wiki_search_snippet(node: dict[str, Any], query: str) -> str:
    metadata = node.get("metadata") or {}
    parts = []
    status = str(metadata.get("status") or "").strip()
    owner = str(metadata.get("owner") or metadata.get("agent_role") or "").strip()
    source = str(metadata.get("path") or "").strip()
    if status:
        parts.append(f"status: {status}")
    if owner:
        parts.append(f"owner: {owner}")
    if source:
        parts.append(f"source: {source}")
    if not parts:
        rel_count = len(node.get("relations") or [])
        parts.append(f"{node.get('kind') or 'entity'} with {rel_count} relation(s)")
    return "; ".join(parts)[:240]


def _wiki_evidence_excerpt(pack: dict[str, Any]) -> str:
    root = pack.get("root") or {}
    metadata = root.get("metadata") or {}
    related = [str(item.get("id") or "") for item in pack.get("neighbors", []) if item.get("id")]
    backlinks = [str(item.get("id") or "") for item in pack.get("backlinks", []) if item.get("id")]
    parts = [
        str(root.get("kind") or "entity"),
        str(root.get("title") or root.get("id") or ""),
    ]
    source = str(metadata.get("path") or "").strip()
    status = str(metadata.get("status") or "").strip()
    if status:
        parts.append(f"status {status}")
    if source:
        parts.append(f"source {source}")
    if related:
        parts.append("related " + ", ".join(related[:4]))
    if backlinks:
        parts.append("backlinks " + ", ".join(backlinks[:4]))
    return "; ".join(part for part in parts if part)[:360]


def build_wiki_search(
    root: Path, query: str, *, limit: int = WIKI_SEARCH_LIMIT, now: str | None = None
) -> dict[str, Any]:
    """Deterministic ranked wiki search over the existing knowledge graph."""
    moment = now or datetime.now(timezone.utc).isoformat()
    query = (query or "").strip()
    try:
        limit = max(1, min(int(limit), 50))
    except (TypeError, ValueError):
        limit = WIKI_SEARCH_LIMIT
    if not query:
        return {
            "schema": WIKI_SEARCH_SCHEMA,
            "generated_at": moment,
            "query": query,
            "results": [],
        }
    try:
        _ensure_knowledge_import_paths(root)
        from scripts import knowledge_graph as kg
        graph = kg.build_graph(Path(root))
        hits = kg.search(graph, query, limit=limit)
    except Exception as exc:
        return {
            "schema": WIKI_SEARCH_SCHEMA,
            "generated_at": moment,
            "query": query,
            "results": [],
            "error": type(exc).__name__,
        }
    results = []
    for node in hits:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        results.append({
            "id": node_id,
            "kind": str(node.get("kind") or "entity"),
            "title": str(node.get("title") or node_id),
            "snippet": _wiki_search_snippet(node, query),
            "score": _wiki_search_score(node, query),
        })
    return {
        "schema": WIKI_SEARCH_SCHEMA,
        "generated_at": moment,
        "query": query,
        "results": results,
    }


def build_wiki_ask(
    root: Path,
    query: str,
    *,
    use_llm: bool = False,
    k: int = WIKI_ASK_EVIDENCE_LIMIT,
    now: str | None = None,
    synthesizer: Any | None = None,
) -> dict[str, Any]:
    """Evidence-first wiki ask endpoint envelope, with explicit LLM opt-in."""
    moment = now or datetime.now(timezone.utc).isoformat()
    query = (query or "").strip()
    try:
        k = max(1, min(int(k), 10))
    except (TypeError, ValueError):
        k = WIKI_ASK_EVIDENCE_LIMIT
    if not query:
        return {
            "schema": WIKI_ASK_SCHEMA,
            "generated_at": moment,
            "query": query,
            "evidence": [],
            "cited": [],
            "answer": "No query provided.",
            "llm_used": False,
        }
    try:
        _ensure_knowledge_import_paths(root)
        from scripts import knowledge_ask as ka
        from scripts import knowledge_graph as kg
        graph = kg.build_graph(Path(root))
        result = ka.answer(Path(root), graph, query, k=k, use_llm=use_llm, synthesizer=synthesizer)
    except Exception as exc:
        return {
            "schema": WIKI_ASK_SCHEMA,
            "generated_at": moment,
            "query": query,
            "evidence": [],
            "cited": [],
            "answer": "Wiki evidence lookup failed.",
            "llm_used": False,
            "error": type(exc).__name__,
        }

    evidence: list[dict[str, Any]] = []
    for pack in result.get("context") or []:
        root_node = pack.get("root") or {}
        node_id = str(root_node.get("id") or "")
        if not node_id:
            continue
        evidence.append({
            "id": node_id,
            "kind": str(root_node.get("kind") or "entity"),
            "title": str(root_node.get("title") or node_id),
            "excerpt": _wiki_evidence_excerpt(pack),
        })
    cited = [item["id"] for item in evidence]
    llm_used = result.get("mode") == "llm" and bool(result.get("answer"))
    if llm_used:
        answer_text = str(result.get("answer") or "")
    elif evidence:
        answer_text = "Evidence-only result: " + "; ".join(f"{item['title']} [{item['id']}]" for item in evidence[:3])
    else:
        answer_text = "No matching evidence found."
    payload = {
        "schema": WIKI_ASK_SCHEMA,
        "generated_at": moment,
        "query": query,
        "evidence": evidence,
        "cited": cited,
        "answer": answer_text,
        "llm_used": bool(llm_used),
    }
    if result.get("note"):
        payload["note"] = result.get("note")
    return payload


def build_wiki_page(root: Path, entity_id: str, *, now: str | None = None) -> dict[str, Any] | None:
    """Deterministic wiki page envelope over the knowledge graph.

    The console route uses this read-only helper for a page API. It omits
    unresolved relation endpoints so rendered links can stay dead-link free.
    """
    entity_id = (entity_id or "").strip()
    if not entity_id:
        return None
    moment = now or datetime.now(timezone.utc).isoformat()
    try:
        _ensure_knowledge_import_paths(root)
        from scripts import knowledge_digest as kd
        from scripts import knowledge_graph as kg
    except ImportError:
        return None
    try:
        graph = kg.build_graph(Path(root))
        idx = kg.build_index(graph)
        digest_page = kd.build_page(idx, entity_id)
    except Exception:
        return None
    if digest_page is None:
        return None
    node = idx.by_id.get(entity_id)
    if node is None:
        return None

    relations: list[dict[str, Any]] = []
    for rel_type, target in idx.forward.get(entity_id, []):
        target_node = idx.by_id.get(target)
        if target_node is None:
            continue
        relations.append({
            "type": rel_type,
            "target_id": target,
            "target_title": target_node.get("title") or target,
            "target_kind": target_node.get("kind") or "entity",
        })

    backlinks: list[dict[str, Any]] = []
    for rel_type, source in idx.backward.get(entity_id, []):
        source_node = idx.by_id.get(source)
        if source_node is None:
            continue
        backlinks.append({
            "type": rel_type,
            "source_id": source,
            "source_title": source_node.get("title") or source,
            "source_kind": source_node.get("kind") or "entity",
        })

    lens_stats: dict[str, dict[str, Any]] = {
        entity_id: {
            "role": "root",
            "degree": 0,
            "incoming_count": 0,
            "outgoing_count": 0,
            "edge_types": set(),
        }
    }
    relation_counts: dict[str, dict[str, int]] = {}

    def _relation_count(rel_type: str, direction: str) -> None:
        bucket = relation_counts.setdefault(rel_type, {"incoming": 0, "outgoing": 0, "total": 0})
        bucket[direction] += 1
        bucket["total"] += 1

    def _node_lens(node_id: str) -> dict[str, Any]:
        return lens_stats.setdefault(node_id, {
            "role": "neighbor",
            "degree": 0,
            "incoming_count": 0,
            "outgoing_count": 0,
            "edge_types": set(),
        })

    def _add_lens_edge(other_id: str, rel_type: str, direction: str) -> None:
        root_lens = _node_lens(entity_id)
        other_lens = _node_lens(other_id)
        root_lens["degree"] += 1
        root_lens[f"{direction}_count"] += 1
        root_lens["edge_types"].add(rel_type)
        other_lens["degree"] += 1
        other_lens["edge_types"].add(rel_type)
        if direction == "outgoing":
            other_lens["incoming_count"] += 1
            other_role = "outgoing"
        else:
            other_lens["outgoing_count"] += 1
            other_role = "incoming"
        existing_role = str(other_lens.get("role") or "neighbor")
        if existing_role in ("neighbor", other_role):
            other_lens["role"] = other_role
        elif existing_role != "root":
            other_lens["role"] = "mixed"
        _relation_count(rel_type, direction)

    for rel in relations:
        _add_lens_edge(str(rel["target_id"]), str(rel["type"]), "outgoing")
    for rel in backlinks:
        _add_lens_edge(str(rel["source_id"]), str(rel["type"]), "incoming")

    local_ids = [entity_id]
    for rel in relations:
        if rel["target_id"] not in local_ids:
            local_ids.append(rel["target_id"])
    for rel in backlinks:
        if rel["source_id"] not in local_ids:
            local_ids.append(rel["source_id"])
    total_nodes = len(local_ids)
    local_ids = local_ids[:WIKI_MINIGRAPH_LIMIT]
    kept = set(local_ids)
    minigraph_edges: list[dict[str, Any]] = []
    for rel in relations:
        target = str(rel["target_id"])
        if target in kept:
            minigraph_edges.append({
                "from": entity_id,
                "to": target,
                "type": str(rel["type"]),
                "source_title": node.get("title") or entity_id,
                "source_kind": node.get("kind") or "entity",
                "target_title": rel.get("target_title") or target,
                "target_kind": rel.get("target_kind") or "entity",
            })
    for rel in backlinks:
        source = str(rel["source_id"])
        if source in kept:
            minigraph_edges.append({
                "from": source,
                "to": entity_id,
                "type": str(rel["type"]),
                "source_title": rel.get("source_title") or source,
                "source_kind": rel.get("source_kind") or "entity",
                "target_title": node.get("title") or entity_id,
                "target_kind": node.get("kind") or "entity",
            })

    relation_summary = [
        {
            "type": rel_type,
            "incoming": counts["incoming"],
            "outgoing": counts["outgoing"],
            "total": counts["total"],
        }
        for rel_type, counts in sorted(
            relation_counts.items(),
            key=lambda item: (-item[1]["total"], item[0]),
        )
    ]

    metadata = _knowledge_source_metadata(Path(root), node, now=moment)
    metadata["lineage"] = digest_page.get("fingerprint")
    return {
        "schema": WIKI_PAGE_SCHEMA,
        "generated_at": moment,
        "id": entity_id,
        "kind": node.get("kind"),
        "title": node.get("title") or entity_id,
        "summary": kd.render_markdown(digest_page),
        "metadata": metadata,
        "relations": relations,
        "backlinks": backlinks,
        "minigraph": {
            "root_id": entity_id,
            "limit": WIKI_MINIGRAPH_LIMIT,
            "total_nodes": total_nodes,
            "total_edges": len(relations) + len(backlinks),
            "capped": total_nodes > WIKI_MINIGRAPH_LIMIT,
            "relation_counts": relation_summary,
            "nodes": [_wiki_node_summary(idx.by_id[i], root_id=entity_id, lens=lens_stats) for i in local_ids if i in idx.by_id],
            "edges": minigraph_edges,
        },
    }


def build_knowledge_graph_view(
    root: Path, *, limit: int = KNOWLEDGE_GRAPH_VIEW_LIMIT, now: str | None = None
) -> dict[str, Any]:
    """Bounded knowledge-graph view for the console: the most-connected entities
    and the edges among them.

    On-demand (not part of build_state) because building the full graph scans work
    items, reviews, claims, and git history. Returns a degree-ranked top-N subgraph
    so the SVG stays readable; `totals.capped` flags when the full graph is larger.
    """
    moment = now or datetime.now(timezone.utc).isoformat()
    empty_totals = {"nodes": 0, "edges": 0, "shown": 0, "capped": False}

    def _fail(error: str) -> dict[str, Any]:
        return {"schema": KNOWLEDGE_GRAPH_VIEW_SCHEMA, "generated_at": moment,
                "nodes": [], "edges": [], "totals": dict(empty_totals), "error": error}

    try:
        # The console process runs from scripts/, so the repo root (parent of
        # scripts/) is not on sys.path by default — add it so `from scripts` resolves.
        root_str = str(Path(root).resolve())
        if root_str not in sys.path:
            sys.path.insert(0, root_str)
        from scripts import knowledge_graph as kg
    except ImportError as exc:
        return _fail(f"knowledge_graph unavailable: {exc}")
    try:
        graph = kg.build_graph(Path(root))
    except Exception as exc:  # building scans the repo; never break the endpoint
        return _fail(f"knowledge graph build failed: {exc}")

    by_id: dict[str, dict[str, Any]] = {}
    for node in graph.get("nodes", []) or []:
        nid = str(node.get("id") or "").strip()
        if nid:
            by_id[nid] = node

    degree: dict[str, int] = {}
    adjacency: list[tuple[str, str, str]] = []
    for nid, node in by_id.items():
        for relation in node.get("relations") or []:
            target = str(relation.get("target") or "").strip()
            rel_type = str(relation.get("type") or "").strip()
            if not target:
                continue
            adjacency.append((nid, rel_type, target))
            degree[nid] = degree.get(nid, 0) + 1
            degree[target] = degree.get(target, 0) + 1

    ranked = sorted(by_id, key=lambda i: (-degree.get(i, 0), i))[: max(1, limit)]
    kept = set(ranked)
    nodes = [
        {"id": i, "kind": str(by_id[i].get("kind") or "entity"),
         "label": str(by_id[i].get("title") or i), "degree": degree.get(i, 0)}
        for i in ranked
    ]
    edges: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for src, rel_type, target in adjacency:
        if src in kept and target in kept and (src, rel_type, target) not in seen:
            seen.add((src, rel_type, target))
            edges.append({"from": src, "to": target, "type": rel_type or "relates"})

    return {
        "schema": KNOWLEDGE_GRAPH_VIEW_SCHEMA,
        "generated_at": moment,
        "nodes": nodes,
        "edges": edges,
        "totals": {
            "nodes": len(by_id),
            "edges": len(adjacency),
            "shown": len(nodes),
            "capped": len(by_id) > len(nodes),
        },
    }


# --- Custom properties + labels + automation rules + triage (TASK-AR-331) ---
# Notion-style custom properties, Monday/Linear-style labels, Monday/ClickUp
# "when X then Y" automation rules, and a Linear-style triage queue. All four
# are READ-ONLY derivations here: definitions come from declarative files under
# agents/project/ui/** and agents/project/automation/rules/**; usage counts and
# the triage inbox are computed from the canonical task files. Nothing in this
# module mutates stored state - rule/label/property edits arrive as proposals in
# .ui_outbox (see ui_commands) and a runtime executor applies them, while rule
# EXECUTION happens in the gate chain (scripts/automation_rules_gate.py).

CUSTOM_PROPERTIES_SCHEMA = "agent-runtime-custom-properties/v1"
LABELS_SCHEMA = "agent-runtime-labels/v1"
AUTOMATION_RULES_SCHEMA = "agent-runtime-automation-rules/v1"
TRIAGE_SCHEMA = "agent-runtime-triage/v1"
# TASK-AR-335: calendar/scheduling.
SCHEDULES_SCHEMA = "agent-runtime-schedules/v1"
CALENDAR_SCHEMA = "agent-runtime-calendar/v1"
SCHEDULES_GLOB = "agents/project/schedules/*.json"
SCHEDULE_DISPATCH_EVENT_GLOB = "agents/runtime/events/scheduled_dispatch.jsonl"
SCHEDULE_MODES = ("reserve", "repeat")
# Reminder horizons (days). A schedule/milestone/task with a due date within
# DUE_SOON_DAYS is "due_soon"; once the date is in the past it is "overdue".
CALENDAR_DUE_SOON_DAYS = 3

# TASK-AR-338: notification center + @mentions/pins/reactions + daily brief.
NOTIFICATIONS_SCHEMA = "agent-runtime-notifications/v1"
DAILY_BRIEF_SCHEMA = "agent-runtime-daily-brief/v1"
# Declarative notification preferences (subscription rules / mutes / keyword
# rules / read state). Authored proposal-only from the inbox view; a runtime
# executor applies the proposal to this canonical file. The console NEVER writes
# it directly. Read-only here.
NOTIFICATIONS_CONFIG_REL = "agents/project/ui/notifications.json"
# Notification event kinds the inbox aggregates. Each maps to a severity.
NOTIFICATION_KINDS = ("reminder", "blocked", "approval", "mention", "error")
# Severities, ordered most-to-least urgent. Severity tokens map to existing
# status color tokens in the console CSS (overdue/blocked/error -> danger;
# due_soon/approval -> warning; mention -> primary; info -> info).
NOTIFICATION_SEVERITIES = ("overdue", "blocked", "error", "approval", "due_soon", "mention", "info")

CUSTOM_PROPERTIES_REL = "agents/project/ui/custom-properties.json"
LABELS_REL = "agents/project/ui/labels.json"
AUTOMATION_RULES_GLOB = "agents/project/automation/rules/*.json"

CUSTOM_PROPERTY_TYPES = ("text", "select", "number", "date")

# Label colors map onto the SAME fixed semantic token palette used by channel
# role colors. User-defined label colors NEVER inject raw CSS; they are mapped
# to one of these token names, which the stylesheet resolves via var(--token)
# (defined in BOTH theme blocks). This keeps the tokenization gate green.
LABEL_COLOR_TOKENS = (
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

# Declarative automation rule triggers/actions. Execution lives in the gate
# chain; the UI only does CRUD + the active/inactive toggle.
AUTOMATION_TRIGGERS = ("status_change", "due_passed", "blocked_too_long")
AUTOMATION_ACTIONS = ("board_regen", "escalation_message", "label_apply")

# Triage collection thresholds (Linear-style inbox).
TRIAGE_BLOCKED_DAYS = 3
_TRIAGE_DONE_STATUSES = {"completed", "done", "released", "완료"}


def _label_color_token(value: Any) -> str:
    """Map an arbitrary label color request onto a fixed semantic token.

    Accepts a token name directly (validated against the palette) or hashes any
    other string deterministically. Guarantees the result is always a known
    token so the rendered chip can only ever consume var(--<token>).
    """
    key = str(value or "").strip().lower()
    if key in LABEL_COLOR_TOKENS:
        return key
    if not key:
        return "primary"
    digest = sum(ord(char) for char in key)
    return LABEL_COLOR_TOKENS[digest % len(LABEL_COLOR_TOKENS)]


def load_custom_properties(root: Path, now: str, warnings: list[dict[str, str]]) -> dict[str, Any]:
    """Load custom-property DEFINITIONS (text/select/number/date) from the UI config file."""
    path = root / CUSTOM_PROPERTIES_REL
    definitions: list[dict[str, Any]] = []
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(_warning("custom-properties-parse-error", _rel(root, path), str(exc)))
            payload = {}
        except OSError as exc:
            warnings.append(_warning("custom-properties-read-error", _rel(root, path), str(exc)))
            payload = {}
        raw = payload.get("properties") if isinstance(payload, dict) else None
        for entry in raw or []:
            if not isinstance(entry, dict):
                continue
            key = str(entry.get("key") or entry.get("id") or "").strip()
            if not key:
                continue
            prop_type = str(entry.get("type") or "text").strip().lower()
            if prop_type not in CUSTOM_PROPERTY_TYPES:
                prop_type = "text"
            options = entry.get("options") if isinstance(entry.get("options"), list) else []
            definitions.append(
                {
                    "key": key,
                    "label": str(entry.get("label") or key),
                    "type": prop_type,
                    "options": [str(option) for option in options if str(option).strip()],
                    "filterable": bool(entry.get("filterable", True)),
                }
            )
    return {
        "schema": CUSTOM_PROPERTIES_SCHEMA,
        "generated_at": now,
        "source_path": CUSTOM_PROPERTIES_REL,
        "source_kind": "custom_properties_json",
        "freshness": _path_freshness(path),
        "last_updated": _mtime_iso(path),
        "types": list(CUSTOM_PROPERTY_TYPES),
        "definitions": definitions,
    }


def _coerce_property_value(prop_type: str, raw: Any) -> dict[str, Any]:
    """Display/filter shape for a single task's value of one custom property."""
    display = "" if raw is None else str(raw)
    valid = True
    if prop_type == "number" and display:
        try:
            float(display)
        except ValueError:
            valid = False
    return {"raw": raw, "display": display, "valid": valid}


def enrich_tasks_with_custom_properties(
    tasks: list[dict[str, Any]],
    custom_properties: dict[str, Any],
) -> None:
    """Project each definition onto every task (frontmatter extension), display + filter ready."""
    definitions = custom_properties.get("definitions", [])
    for task in tasks:
        meta = task.get("custom_property_source") or {}
        projected: dict[str, dict[str, Any]] = {}
        for definition in definitions:
            key = definition["key"]
            projected[key] = _coerce_property_value(definition["type"], meta.get(key))
        task["custom_properties"] = projected


def filter_tasks_by_custom_properties(
    tasks: list[dict[str, Any]],
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Filter tasks by exact custom-property display value (computed-only)."""
    filters = filters or {}
    if not filters:
        return list(tasks)
    result: list[dict[str, Any]] = []
    for task in tasks:
        props = task.get("custom_properties") or {}
        keep = True
        for key, wanted in filters.items():
            want = str(wanted).strip()
            if not want:
                continue
            value = props.get(key) or {}
            if str(value.get("display") or "") != want:
                keep = False
                break
        if keep:
            result.append(task)
    return result


def build_labels(
    root: Path,
    tasks: list[dict[str, Any]],
    now: str,
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    """Label registry (name/color-token) joined with computed usage counts from task tags."""
    path = root / LABELS_REL
    defined: dict[str, dict[str, Any]] = {}
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(_warning("labels-parse-error", _rel(root, path), str(exc)))
            payload = {}
        except OSError as exc:
            warnings.append(_warning("labels-read-error", _rel(root, path), str(exc)))
            payload = {}
        raw = payload.get("labels") if isinstance(payload, dict) else None
        for entry in raw or []:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or "").strip()
            if not name:
                continue
            defined[name.lower()] = {
                "name": name,
                "color_token": _label_color_token(entry.get("color") or entry.get("color_token")),
                "description": str(entry.get("description") or ""),
                "defined": True,
            }

    # Usage counts are COMPUTED from task tags/labels (never a stored count).
    usage: dict[str, int] = {}
    used_tasks: dict[str, list[str]] = {}
    for task in tasks:
        seen: set[str] = set()
        for tag in task.get("labels") or []:
            name = str(tag or "").strip()
            if not name:
                continue
            low = name.lower()
            if low in seen:
                continue
            seen.add(low)
            usage[low] = usage.get(low, 0) + 1
            used_tasks.setdefault(low, []).append(str(task.get("id") or ""))

    labels: list[dict[str, Any]] = []
    for low in sorted(set(defined) | set(usage)):
        entry = defined.get(low)
        if entry is None:
            # Tag used on tasks but not formally defined - still surface it.
            display = next(
                (str(tag) for task in tasks for tag in (task.get("labels") or []) if str(tag).lower() == low),
                low,
            )
            entry = {
                "name": display,
                "color_token": _label_color_token(display),
                "description": "",
                "defined": False,
            }
        record = dict(entry)
        record["usage_count"] = usage.get(low, 0)
        record["task_ids"] = sorted({tid for tid in used_tasks.get(low, []) if tid})
        labels.append(record)

    labels.sort(key=lambda item: (-item["usage_count"], item["name"].lower()))
    return {
        "schema": LABELS_SCHEMA,
        "generated_at": now,
        "source_path": LABELS_REL,
        "source_kind": "labels_json",
        "freshness": _path_freshness(path),
        "last_updated": _mtime_iso(path),
        "color_tokens": list(LABEL_COLOR_TOKENS),
        "labels": labels,
        "totals": {
            "labels": len(labels),
            "defined": sum(1 for label in labels if label["defined"]),
            "used": sum(1 for label in labels if label["usage_count"]),
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


def load_automation_rules(root: Path, now: str, warnings: list[dict[str, str]]) -> dict[str, Any]:
    """Load declarative automation rules (one JSON file per rule, gate-executed)."""
    rules: list[dict[str, Any]] = []
    for path in sorted(root.glob(AUTOMATION_RULES_GLOB)):
        rel_path = _rel(root, path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(_warning("automation-rule-parse-error", rel_path, str(exc)))
            continue
        except OSError as exc:
            warnings.append(_warning("automation-rule-read-error", rel_path, str(exc)))
            continue
        if not isinstance(payload, dict):
            warnings.append(_warning("automation-rule-invalid-record", rel_path, "rule payload is not an object"))
            continue
        trigger = str(payload.get("trigger") or "").strip()
        action = str(payload.get("action") or "").strip()
        invalid: list[str] = []
        if trigger not in AUTOMATION_TRIGGERS:
            invalid.append(f"unknown trigger: {trigger!r}")
        if action not in AUTOMATION_ACTIONS:
            invalid.append(f"unknown action: {action!r}")
        rules.append(
            {
                "id": str(payload.get("id") or path.stem),
                "name": str(payload.get("name") or payload.get("id") or path.stem),
                "description": str(payload.get("description") or ""),
                "trigger": trigger,
                "action": action,
                "params": payload.get("params") if isinstance(payload.get("params"), dict) else {},
                "active": bool(payload.get("active", False)),
                "invalid": invalid,
                "source_path": rel_path,
                "source_kind": "automation_rule_json",
                "source": _source_metadata(root, path, "automation_rule_json", now),
                "last_updated": _mtime_iso(path),
                "freshness": "present",
            }
        )
    active = [rule for rule in rules if rule["active"] and not rule["invalid"]]
    return {
        "schema": AUTOMATION_RULES_SCHEMA,
        "generated_at": now,
        "source_glob": AUTOMATION_RULES_GLOB,
        "triggers": list(AUTOMATION_TRIGGERS),
        "actions": list(AUTOMATION_ACTIONS),
        "rules": rules,
        "totals": {
            "rules": len(rules),
            "active": len(active),
            "inactive": sum(1 for rule in rules if not rule["active"]),
            "invalid": sum(1 for rule in rules if rule["invalid"]),
        },
    }


def _days_since(value: Any, now: str) -> float | None:
    """Whole+fractional days between an ISO timestamp/date and ``now`` (>= 0)."""
    raw = str(value or "").strip()
    if not raw:
        return None

    def _parse(text: str) -> datetime | None:
        text = text.strip()
        for candidate in (text, text[:19], text[:10]):
            try:
                parsed = datetime.fromisoformat(candidate)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed
            except ValueError:
                continue
        return None

    start = _parse(raw)
    current = _parse(now) or datetime.now(timezone.utc)
    if start is None:
        return None
    delta = (current - start).total_seconds() / 86400.0
    return max(0.0, delta)


def build_triage(
    tasks: list[dict[str, Any]],
    now: str,
) -> dict[str, Any]:
    """Linear-style triage inbox: unclassified / overdue / long-blocked tasks (computed-only).

    Collection rules (each task can carry multiple reasons):
    - ``unclassified``: an open task with no ``task_set_id``.
    - ``overdue``: an open task whose ``due`` date has passed.
    - ``long_blocked``: a blocked task blocked longer than ``TRIAGE_BLOCKED_DAYS``.
    """
    items: list[dict[str, Any]] = []
    reason_counts = {"unclassified": 0, "overdue": 0, "long_blocked": 0}
    for task in tasks:
        bucket = _status_bucket(task)
        if str(task.get("status") or "").strip().lower() in _TRIAGE_DONE_STATUSES or bucket == "done":
            continue
        reasons: list[str] = []
        details: dict[str, Any] = {}

        if not str(task.get("task_set_id") or "").strip():
            reasons.append("unclassified")

        due = task.get("due") or (task.get("metadata") or {}).get("due")
        overdue_days = _days_since(due, now) if due else None
        if overdue_days is not None and overdue_days > 0:
            reasons.append("overdue")
            details["overdue_days"] = round(overdue_days, 2)
            details["due"] = str(due)

        if bucket == "blocked":
            since = (
                task.get("blocked_since")
                or task.get("updated_at")
                or task.get("started_at")
                or task.get("created_at")
            )
            blocked_days = _days_since(since, now)
            if blocked_days is not None and blocked_days >= TRIAGE_BLOCKED_DAYS:
                reasons.append("long_blocked")
                details["blocked_days"] = round(blocked_days, 2)

        if not reasons:
            continue
        for reason in reasons:
            reason_counts[reason] += 1
        items.append(
            {
                "id": task.get("id"),
                "title": task.get("title"),
                "status": task.get("status"),
                "priority": task.get("priority"),
                "owner_agent": task.get("owner_agent"),
                "task_set_id": task.get("task_set_id") or None,
                "labels": task.get("labels") or [],
                "reasons": reasons,
                "details": details,
                "blocked_reason": task.get("blocked_reason"),
                "source_path": task.get("source_path"),
                "source_kind": "triage_item",
                "last_updated": task.get("last_updated"),
                "freshness": task.get("freshness", "present"),
            }
        )

    # Most reasons first, then unclassified-priority, then id for stability.
    items.sort(key=lambda item: (-len(item["reasons"]), str(item.get("id") or "")))
    return {
        "schema": TRIAGE_SCHEMA,
        "generated_at": now,
        "blocked_threshold_days": TRIAGE_BLOCKED_DAYS,
        "items": items,
        "totals": {"total": len(items), **reason_counts},
    }


# ---------------------------------------------------------------------------
# Calendar / scheduling (TASK-AR-335)
# ---------------------------------------------------------------------------


def _date_key(value: Any) -> str | None:
    """Normalize a timestamp/date string to a ``YYYY-MM-DD`` day key, or None."""
    raw = str(value or "").strip()
    if not raw:
        return None
    match = re.match(r"\d{4}-\d{2}-\d{2}", raw)
    return match.group(0) if match else None


def _reminder_status(date_key: str | None, now: str) -> str | None:
    """Classify a due date against ``now`` as overdue / due_soon / upcoming.

    Returns None when there is no parseable date. Day-granular: comparison uses
    the calendar day so a same-day deadline reads as due_soon (0 days), and any
    earlier day reads as overdue.
    """
    if not date_key:
        return None
    today = _date_key(now) or datetime.now(timezone.utc).date().isoformat()
    try:
        due = datetime.strptime(date_key, "%Y-%m-%d").date()
        today_date = datetime.strptime(today, "%Y-%m-%d").date()
    except ValueError:
        return None
    delta_days = (due - today_date).days
    if delta_days < 0:
        return "overdue"
    if delta_days <= CALENDAR_DUE_SOON_DAYS:
        return "due_soon"
    return "upcoming"


def load_schedules(root: Path, now: str, warnings: list[dict[str, str]]) -> dict[str, Any]:
    """Load declarative scheduled-dispatch records (one JSON file per schedule).

    Read-only: the records are authored proposal-only from the Calendar view and
    applied by a runtime executor to ``agents/project/schedules/*.json``. The
    LOCAL ``scripts/scheduled_dispatch_gate.py`` is the only point that dispatches
    when due; this loader merely surfaces the schedules for the calendar.
    """
    schedules: list[dict[str, Any]] = []
    for path in sorted(root.glob(SCHEDULES_GLOB)):
        rel_path = _rel(root, path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(_warning("schedule-parse-error", rel_path, str(exc)))
            continue
        except OSError as exc:
            warnings.append(_warning("schedule-read-error", rel_path, str(exc)))
            continue
        if not isinstance(payload, dict):
            warnings.append(_warning("schedule-invalid-record", rel_path, "schedule payload is not an object"))
            continue
        mode = str(payload.get("mode") or "").strip().lower()
        invalid: list[str] = []
        if mode not in SCHEDULE_MODES:
            invalid.append(f"unknown mode: {mode!r}")
        run_at = payload.get("run_at")
        cron = payload.get("cron")
        if mode == "reserve" and not run_at:
            invalid.append("reserve schedule missing run_at")
        if mode == "repeat" and not cron:
            invalid.append("repeat schedule missing cron expression")
        schedules.append(
            {
                "id": str(payload.get("id") or path.stem),
                "name": str(payload.get("name") or payload.get("id") or path.stem),
                "taskset_id": str(payload.get("taskset_id") or payload.get("task_set_id") or ""),
                "mode": mode,
                "run_at": run_at,
                "cron": cron,
                "cron_fields": payload.get("cron_fields") if isinstance(payload.get("cron_fields"), dict) else None,
                "note": str(payload.get("note") or ""),
                "active": bool(payload.get("active", True)),
                "invalid": invalid,
                "created_at": payload.get("created_at"),
                "source_path": rel_path,
                "source_kind": "schedule_json",
                "source": _source_metadata(root, path, "schedule_json", now),
                "last_updated": _mtime_iso(path),
                "freshness": "present",
            }
        )
    active = [item for item in schedules if item["active"] and not item["invalid"]]
    return {
        "schema": SCHEDULES_SCHEMA,
        "generated_at": now,
        "source_glob": SCHEDULES_GLOB,
        "modes": list(SCHEDULE_MODES),
        "schedules": schedules,
        "totals": {
            "schedules": len(schedules),
            "active": len(active),
            "reserve": sum(1 for item in schedules if item["mode"] == "reserve"),
            "repeat": sum(1 for item in schedules if item["mode"] == "repeat"),
            "invalid": sum(1 for item in schedules if item["invalid"]),
        },
    }


def _calendar_event(
    *,
    kind: str,
    date_key: str | None,
    title: str,
    entity_id: str,
    now: str,
    source_path: Any = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "kind": kind,
        "date": date_key,
        "title": title,
        "id": entity_id,
        "reminder": _reminder_status(date_key, now),
        "source_path": source_path,
    }
    if extra:
        event.update(extra)
    return event


def build_calendar(
    tasks: list[dict[str, Any]],
    roadmap: dict[str, Any],
    reviews: list[dict[str, Any]],
    taskset_completion: dict[str, Any],
    schedules: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    """Aggregate a month/week calendar from read-only state + scheduled items.

    Sources (all read-only derivations except schedules, which are authored
    proposal-only and surfaced here):

    - ``milestone`` deadlines from the roadmap,
    - ``meeting``/``seminar`` records from ``reviews/`` (by date),
    - ``completion`` history from completed tasks (``completed_at``),
    - ``deadline`` markers from open tasks with a ``due`` date,
    - ``scheduled`` dispatch items (reserve run_at / repeat cron preview).

    Also emits due-soon/overdue ``reminders`` (records/events for the future
    notification center TASK-AR-338; this task only PUBLISHES them).
    """
    events: list[dict[str, Any]] = []
    reminders: list[dict[str, Any]] = []
    done_statuses = _TRIAGE_DONE_STATUSES

    # Milestones (roadmap deadlines).
    for index, milestone in enumerate(roadmap.get("milestones", []) or []):
        date_key = _date_key(milestone.get("date"))
        title = str(milestone.get("title") or "milestone")
        done = bool(milestone.get("done"))
        event = _calendar_event(
            kind="milestone",
            date_key=date_key,
            title=title,
            entity_id=f"milestone-{index + 1}",
            now=now,
            source_path=roadmap.get("source_path"),
            extra={"done": done},
        )
        events.append(event)
        if not done and event["reminder"] in {"due_soon", "overdue"}:
            reminders.append(_reminder_record("milestone", event, now))

    # Meetings / seminars (review records by date).
    for review in reviews:
        review_type = str(review.get("type") or "review").strip().lower()
        if review_type not in {"meeting", "seminar"}:
            continue
        date_key = _date_key(review.get("created_at"))
        events.append(
            _calendar_event(
                kind=review_type,
                date_key=date_key,
                title=str(review.get("title") or review.get("id")),
                entity_id=str(review.get("id")),
                now=now,
                source_path=review.get("source_path"),
            )
        )

    # Task completion history + open-task deadlines.
    for task in tasks:
        status = str(task.get("status") or "").strip().lower()
        completed_at = task.get("completed_at") or (task.get("metadata") or {}).get("completed_at")
        completed_key = _date_key(completed_at)
        if completed_key and (status in done_statuses or completed_at):
            events.append(
                _calendar_event(
                    kind="completion",
                    date_key=completed_key,
                    title=str(task.get("title") or task.get("id")),
                    entity_id=str(task.get("id")),
                    now=now,
                    source_path=task.get("source_path"),
                    extra={"status": status},
                )
            )
        due_key = _date_key(task.get("due"))
        if due_key and status not in done_statuses:
            event = _calendar_event(
                kind="deadline",
                date_key=due_key,
                title=str(task.get("title") or task.get("id")),
                entity_id=str(task.get("id")),
                now=now,
                source_path=task.get("source_path"),
                extra={"status": status, "priority": task.get("priority")},
            )
            events.append(event)
            if event["reminder"] in {"due_soon", "overdue"}:
                reminders.append(_reminder_record("task", event, now))

    # Scheduled dispatches (reserve = dated; repeat = cron preview, no fixed day).
    for schedule in schedules.get("schedules", []) or []:
        if not schedule.get("active") or schedule.get("invalid"):
            continue
        if schedule.get("mode") == "reserve":
            date_key = _date_key(schedule.get("run_at"))
        else:
            date_key = None  # recurring: rendered as a cron badge, not a fixed cell
        events.append(
            _calendar_event(
                kind="scheduled",
                date_key=date_key,
                title=str(schedule.get("name") or schedule.get("id")),
                entity_id=str(schedule.get("id")),
                now=now,
                source_path=schedule.get("source_path"),
                extra={
                    "mode": schedule.get("mode"),
                    "taskset_id": schedule.get("taskset_id"),
                    "cron": schedule.get("cron"),
                    "run_at": schedule.get("run_at"),
                },
            )
        )

    # Index events by day for month/week grids.
    by_date: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        key = event.get("date")
        if not key:
            continue
        by_date.setdefault(key, []).append(event)

    kind_counts: dict[str, int] = {}
    for event in events:
        kind_counts[event["kind"]] = kind_counts.get(event["kind"], 0) + 1

    reminders.sort(key=lambda item: (item.get("severity") != "overdue", str(item.get("date") or "")))
    return {
        "schema": CALENDAR_SCHEMA,
        "generated_at": now,
        "today": _date_key(now),
        "due_soon_days": CALENDAR_DUE_SOON_DAYS,
        "events": events,
        "by_date": by_date,
        "reminders": reminders,
        "totals": {
            "events": len(events),
            "dated": sum(1 for event in events if event.get("date")),
            "undated": sum(1 for event in events if not event.get("date")),
            "reminders": len(reminders),
            "due_soon": sum(1 for item in reminders if item["severity"] == "due_soon"),
            "overdue": sum(1 for item in reminders if item["severity"] == "overdue"),
            "by_kind": kind_counts,
        },
    }


def _reminder_record(entity_kind: str, event: dict[str, Any], now: str) -> dict[str, Any]:
    """Build a due-soon/overdue reminder record for the notification center.

    These are PUBLISHED here (TASK-AR-335); TASK-AR-338 will consume them. The
    record is event-shaped so a future executor can append it to a runtime event
    log without reshaping.
    """
    severity = "overdue" if event.get("reminder") == "overdue" else "due_soon"
    return {
        "id": f"reminder:{entity_kind}:{event.get('id')}",
        "event": "calendar_reminder",
        "severity": severity,
        "entity_kind": entity_kind,
        "calendar_kind": event.get("kind"),
        "entity_id": event.get("id"),
        "title": event.get("title"),
        "date": event.get("date"),
        "source_path": event.get("source_path"),
        "generated_at": now,
        "consumer": "TASK-AR-338 notification-center",
    }


# ---------------------------------------------------------------------------
# Notification center + @mentions + daily brief (TASK-AR-338)
# ---------------------------------------------------------------------------

# Approval / mention detection tokens. Kept small + lowercased; matched against a
# joined text blob of the event/message fields.
_APPROVAL_TOKENS = ("approval", "approve", "pending_approval", "awaiting_approval", "needs_approval", "승인")
# Recognizes @agent / @role / @owner mentions in message bodies and event text.
_MENTION_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9][A-Za-z0-9_.-]*)")


def _notification_severity_rank(severity: str) -> int:
    """Position in NOTIFICATION_SEVERITIES (lower = more urgent); unknown last."""
    try:
        return NOTIFICATION_SEVERITIES.index(severity)
    except ValueError:
        return len(NOTIFICATION_SEVERITIES)


def load_notifications_config(root: Path, now: str, warnings: list[dict[str, str]]) -> dict[str, Any]:
    """Load declarative notification preferences (read-only).

    Authored proposal-only from the inbox view (notification.subscribe /
    notification.mute / notification.read); a runtime executor applies the
    proposal to ``agents/project/ui/notifications.json``. The console NEVER
    writes it directly. Missing file = permissive defaults (subscribe to all).

    Shape::

        {
          "subscriptions": {"kinds": [...], "severities": [...], "tasksets": [...]},
          "mutes": ["<notification id or entity id>", ...],
          "keyword_rules": [{"keyword": "...", "action": "mute|highlight"}],
          "read": ["<notification id>", ...]
        }
    """
    path = root / NOTIFICATIONS_CONFIG_REL
    rel_path = NOTIFICATIONS_CONFIG_REL
    payload: dict[str, Any] = {}
    present = path.exists()
    if present:
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(_warning("notifications-config-parse-error", rel_path, str(exc)))
            loaded = {}
        except OSError as exc:
            warnings.append(_warning("notifications-config-read-error", rel_path, str(exc)))
            loaded = {}
        if isinstance(loaded, dict):
            payload = loaded
        else:
            warnings.append(_warning("notifications-config-invalid-record", rel_path, "config payload is not an object"))

    subs_raw = payload.get("subscriptions") if isinstance(payload.get("subscriptions"), dict) else {}
    subscriptions = {
        "kinds": [str(value).strip().lower() for value in _string_list(subs_raw.get("kinds")) if str(value).strip()],
        "severities": [str(value).strip().lower() for value in _string_list(subs_raw.get("severities")) if str(value).strip()],
        "tasksets": [str(value).strip() for value in _string_list(subs_raw.get("tasksets")) if str(value).strip()],
    }
    mutes = [str(value).strip() for value in _string_list(payload.get("mutes")) if str(value).strip()]
    read = [str(value).strip() for value in _string_list(payload.get("read")) if str(value).strip()]
    keyword_rules: list[dict[str, str]] = []
    for rule in payload.get("keyword_rules") or []:
        if not isinstance(rule, dict):
            continue
        keyword = str(rule.get("keyword") or "").strip()
        if not keyword:
            continue
        action = str(rule.get("action") or "mute").strip().lower()
        if action not in {"mute", "highlight"}:
            action = "mute"
        keyword_rules.append({"keyword": keyword, "action": action})
    return {
        "subscriptions": subscriptions,
        "mutes": mutes,
        "read": read,
        "keyword_rules": keyword_rules,
        "source_path": rel_path,
        "freshness": "present" if present else "absent",
        "config_present": present,
        "generated_at": now,
        "mutation_boundary": "proposal_only",
    }


def extract_mentions(text: Any) -> list[str]:
    """Return distinct @mention targets (lowercased) found in free text.

    Order-preserving, deduped. Targets are agent ids / role names / ``owner``.
    """
    seen: set[str] = set()
    result: list[str] = []
    for match in _MENTION_RE.finditer(str(text or "")):
        target = match.group(1).strip().lower().rstrip(".")
        if not target or target in seen:
            continue
        seen.add(target)
        result.append(target)
    return result


def _notification(
    *,
    notification_id: str,
    kind: str,
    severity: str,
    title: str,
    body: str,
    entity_kind: str,
    entity_id: Any,
    task_id: Any,
    taskset_id: Any,
    deep_link: str | None,
    created_at: Any,
    source_path: Any,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "id": notification_id,
        "kind": kind,
        "severity": severity,
        "title": title,
        "body": body,
        "entity_kind": entity_kind,
        "entity_id": str(entity_id) if entity_id is not None else None,
        "task_id": str(task_id) if task_id else None,
        "taskset_id": str(taskset_id) if taskset_id else None,
        "deep_link": deep_link,
        "created_at": created_at,
        "source_path": source_path,
        "read": False,
        "muted": False,
        "highlighted": False,
        "mute_reason": None,
    }
    if extra:
        record.update(extra)
    return record


def build_notifications(
    events: list[dict[str, Any]],
    calendar: dict[str, Any],
    tasks: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    config: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    """Aggregate the in-app notification inbox (Slack + Linear Inbox model).

    Sources (all read-only derivations):

    - ``reminder``: due-soon / overdue reminders PUBLISHED by the calendar
      (TASK-AR-335) -- consumed here, never re-emitted.
    - ``blocked``: open tasks in the blocked bucket (deep-link to the task).
    - ``approval``: approval-pending events / messages (high-risk command queue,
      governance approvals).
    - ``mention``: @agent / @role / @owner mentions found in message bodies.
    - ``error``: error-severity runtime events.

    Subscription rules (by kind/severity/taskset), mute rules, and keyword rules
    are applied from the declarative config; read state is stamped from the
    config's ``read`` list. Muted / unsubscribed notifications are retained in
    the payload (flagged) so the UI can show a muted section and the totals stay
    honest; ``inbox`` is the visible (subscribed, unmuted) subset.
    """
    task_by_id = {str(task.get("id")): task for task in tasks if task.get("id")}
    taskset_of_task = {
        str(task.get("id")): str(task.get("task_set_id") or "")
        for task in tasks
        if task.get("id")
    }

    notifications: list[dict[str, Any]] = []

    # 1) Calendar reminders (due-soon / overdue) -- consumed from AR-335.
    for reminder in calendar.get("reminders", []) or []:
        severity = "overdue" if reminder.get("severity") == "overdue" else "due_soon"
        entity_id = reminder.get("entity_id")
        task_id = entity_id if reminder.get("entity_kind") == "task" else None
        taskset_id = taskset_of_task.get(str(task_id or ""), "") or None
        deep_link = f"#/work/calendar" if not task_id else f"#/home/board?select={task_id}"
        notifications.append(
            _notification(
                notification_id=f"notif:{reminder.get('id')}",
                kind="reminder",
                severity=severity,
                title=str(reminder.get("title") or entity_id or "reminder"),
                body=f"{reminder.get('calendar_kind') or 'item'} {severity.replace('_', ' ')}"
                + (f" on {reminder.get('date')}" if reminder.get("date") else ""),
                entity_kind=str(reminder.get("entity_kind") or "calendar"),
                entity_id=entity_id,
                task_id=task_id,
                taskset_id=taskset_id,
                deep_link=deep_link,
                created_at=reminder.get("date") or now,
                source_path=reminder.get("source_path"),
                extra={"date": reminder.get("date"), "calendar_kind": reminder.get("calendar_kind")},
            )
        )

    # 2) Blocked tasks -> blocked notification with a task deep link.
    for task in tasks:
        if _status_bucket(task) != "blocked":
            continue
        task_id = str(task.get("id") or "")
        if not task_id:
            continue
        reason = str(task.get("blocked_reason") or "").strip()
        notifications.append(
            _notification(
                notification_id=f"notif:blocked:{task_id}",
                kind="blocked",
                severity="blocked",
                title=f"Blocked: {task.get('title') or task_id}",
                body=reason or "Task is blocked.",
                entity_kind="task",
                entity_id=task_id,
                task_id=task_id,
                taskset_id=task.get("task_set_id") or None,
                deep_link=f"#/home/board?select={task_id}",
                created_at=task.get("updated_at") or task.get("created_at") or now,
                source_path=task.get("source_path"),
            )
        )

    # 3) Approval-pending events / messages.
    for event in events:
        blob = " ".join(
            str(event.get(key) or "")
            for key in ("event", "type", "status", "intent", "approval_state", "message")
        ).lower()
        if not (any(token in blob for token in _APPROVAL_TOKENS) and "approv" in blob):
            continue
        event_id = event.get("id")
        task_id = event.get("task_id")
        notifications.append(
            _notification(
                notification_id=f"notif:approval:{event_id}",
                kind="approval",
                severity="approval",
                title=f"Approval pending: {event.get('type') or event.get('event') or event_id}",
                body=str(event.get("message") or event.get("reason") or "Owner approval is required."),
                entity_kind="event",
                entity_id=event_id,
                task_id=task_id,
                taskset_id=taskset_of_task.get(str(task_id or ""), "") or None,
                deep_link=f"#/records/events?select={event_id}",
                created_at=event.get("created_at") or event.get("ts") or now,
                source_path=event.get("source_path"),
            )
        )

    # 4) @mentions in message bodies -> one notification per (message, target).
    for message in messages:
        targets = extract_mentions(message.get("body"))
        if not targets:
            continue
        message_id = str(message.get("id") or "")
        task_id = message.get("task_id")
        if task_id and str(task_id).lower() == "none":
            task_id = None
        for target in targets:
            notifications.append(
                _notification(
                    notification_id=f"notif:mention:{message_id}:{target}",
                    kind="mention",
                    severity="mention",
                    title=f"@{target} mentioned by {message.get('from') or 'unknown'}",
                    body=str(message.get("body") or ""),
                    entity_kind="message",
                    entity_id=message_id,
                    task_id=task_id,
                    taskset_id=taskset_of_task.get(str(task_id or ""), "") or None,
                    deep_link=f"#/comms/messages?select={message_id}",
                    created_at=message.get("ts") or message.get("created_at") or now,
                    source_path=message.get("source_path"),
                    extra={"mention_target": target, "from": message.get("from")},
                )
            )

    # 5) Error-severity runtime events.
    for event in events:
        if str(event.get("severity") or "").lower() != "error":
            continue
        event_id = event.get("id")
        task_id = event.get("task_id")
        notifications.append(
            _notification(
                notification_id=f"notif:error:{event_id}",
                kind="error",
                severity="error",
                title=f"Error: {event.get('type') or event.get('event') or event_id}",
                body=str(event.get("error") or event.get("message") or "Runtime error event."),
                entity_kind="event",
                entity_id=event_id,
                task_id=task_id,
                taskset_id=taskset_of_task.get(str(task_id or ""), "") or None,
                deep_link=f"#/records/events?select={event_id}",
                created_at=event.get("created_at") or event.get("ts") or now,
                source_path=event.get("source_path"),
            )
        )

    # --- Apply subscription / mute / keyword rules + read state. -------------
    subscriptions = config.get("subscriptions") or {}
    sub_kinds = set(subscriptions.get("kinds") or [])
    sub_severities = set(subscriptions.get("severities") or [])
    sub_tasksets = set(subscriptions.get("tasksets") or [])
    mutes = set(config.get("mutes") or [])
    read_ids = set(config.get("read") or [])
    keyword_rules = config.get("keyword_rules") or []

    def _subscribed(record: dict[str, Any]) -> bool:
        # An empty subscription axis means "all" for that axis (permissive).
        if sub_kinds and record["kind"] not in sub_kinds:
            return False
        if sub_severities and record["severity"] not in sub_severities:
            return False
        if sub_tasksets and (record.get("taskset_id") or "") not in sub_tasksets:
            return False
        return True

    for record in notifications:
        record["read"] = record["id"] in read_ids
        record["subscribed"] = _subscribed(record)
        # Mute by explicit notification id, or the underlying entity/task id.
        if record["id"] in mutes or (record.get("entity_id") and record["entity_id"] in mutes) or (
            record.get("task_id") and record["task_id"] in mutes
        ):
            record["muted"] = True
            record["mute_reason"] = "muted"
        # Keyword rules scan the title + body.
        haystack = f"{record.get('title') or ''} {record.get('body') or ''}".lower()
        for rule in keyword_rules:
            if rule["keyword"].lower() in haystack:
                if rule["action"] == "mute":
                    record["muted"] = True
                    record["mute_reason"] = f"keyword:{rule['keyword']}"
                elif rule["action"] == "highlight":
                    record["highlighted"] = True

    # Stable, urgency-first ordering: severity rank, then unread first, then date.
    notifications.sort(
        key=lambda item: (
            _notification_severity_rank(item["severity"]),
            item["read"],
            "" if (item.get("created_at") is None) else str(item.get("created_at")),
        )
    )

    inbox = [item for item in notifications if item["subscribed"] and not item["muted"]]
    muted = [item for item in notifications if item["muted"]]
    unread = sum(1 for item in inbox if not item["read"])
    by_kind: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for item in inbox:
        by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
        by_severity[item["severity"]] = by_severity.get(item["severity"], 0) + 1

    return {
        "schema": NOTIFICATIONS_SCHEMA,
        "generated_at": now,
        "kinds": list(NOTIFICATION_KINDS),
        "severities": list(NOTIFICATION_SEVERITIES),
        "notifications": notifications,
        "inbox": inbox,
        "muted": muted,
        "config": config,
        "totals": {
            "total": len(notifications),
            "inbox": len(inbox),
            "unread": unread,
            "muted": len(muted),
            "by_kind": by_kind,
            "by_severity": by_severity,
        },
        "mutation_boundary": "proposal_only",
    }


def build_daily_brief(
    tasks: list[dict[str, Any]],
    events: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    notifications: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    """Auto-summary card: today's completed / blocked / decisions / next (brief 13.2).

    All sections are read-only derivations of state:

    - ``completed``: tasks completed today (``completed_at`` day == today).
    - ``blocked``: currently-blocked tasks (from the notification inbox).
    - ``decisions``: today's decision/meeting/governance review records.
    - ``next_recommended``: top open, unblocked tasks by priority (the work the
      Owner should pick up next).
    """
    today = _date_key(now)

    def _section_item(entity_id: Any, title: Any, **extra: Any) -> dict[str, Any]:
        item = {"id": str(entity_id) if entity_id is not None else None, "title": str(title or entity_id or "")}
        item.update({key: value for key, value in extra.items() if value is not None})
        return item

    completed: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    next_recommended: list[dict[str, Any]] = []
    for task in tasks:
        bucket = _status_bucket(task)
        completed_at = task.get("completed_at") or (task.get("metadata") or {}).get("completed_at")
        if bucket == "done" and completed_at and _date_key(completed_at) == today:
            completed.append(
                _section_item(
                    task.get("id"),
                    task.get("title"),
                    task_set_id=task.get("task_set_id") or None,
                    completed_at=completed_at,
                    deep_link=f"#/home/board?select={task.get('id')}",
                )
            )
        if bucket == "blocked":
            blocked.append(
                _section_item(
                    task.get("id"),
                    task.get("title"),
                    blocked_reason=str(task.get("blocked_reason") or "") or None,
                    task_set_id=task.get("task_set_id") or None,
                    deep_link=f"#/home/board?select={task.get('id')}",
                )
            )
        if bucket in {"planned", "ready", "in_progress"}:
            next_recommended.append(task)

    # Next-recommended: highest priority (P0 first) then explicit order, capped.
    def _priority_rank(task: dict[str, Any]) -> int:
        priority = str(task.get("priority") or "P3").upper()
        return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(priority, 4)

    next_recommended.sort(key=lambda task: (_priority_rank(task), _task_order(task, 0), str(task.get("id") or "")))
    next_items = [
        _section_item(
            task.get("id"),
            task.get("title"),
            priority=task.get("priority"),
            status=task.get("status"),
            task_set_id=task.get("task_set_id") or None,
            deep_link=f"#/home/board?select={task.get('id')}",
        )
        for task in next_recommended[:5]
    ]

    # Decisions: review records typed as decision/meeting/governance dated today.
    decisions: list[dict[str, Any]] = []
    for review in reviews:
        review_type = str(review.get("type") or "").strip().lower()
        if review_type not in {"decision", "meeting", "governance", "release"}:
            continue
        created_at = review.get("created_at")
        if _date_key(created_at) != today:
            continue
        decisions.append(
            _section_item(
                review.get("id"),
                review.get("title"),
                review_type=review_type,
                summary=review.get("summary") or None,
                deep_link=f"#/records/sources?select={review.get('id')}",
            )
        )

    return {
        "schema": DAILY_BRIEF_SCHEMA,
        "generated_at": now,
        "date": today,
        "completed": completed,
        "blocked": blocked,
        "decisions": decisions,
        "next_recommended": next_items,
        "totals": {
            "completed": len(completed),
            "blocked": len(blocked),
            "decisions": len(decisions),
            "next_recommended": len(next_items),
            "unread_notifications": (notifications.get("totals") or {}).get("unread", 0),
        },
    }


# ---------------------------------------------------------------------------
# Global search + quick open (TASK-AR-334)
# ---------------------------------------------------------------------------

# Slack-style operator tokens supported in the search box. Each maps to a
# normalized field on the search-index entry.
_SEARCH_OPERATORS = ("type", "status", "owner", "date")
# Matches ``key:value`` pairs (value may be quoted to allow spaces).
_SEARCH_OPERATOR_RE = re.compile(r'(\w+):("[^"]*"|\'[^\']*\'|\S+)')
# Extracts bare commit SHAs (7-40 hex chars) referenced in task/review text so
# results can surface a related-commit link.
_COMMIT_SHA_RE = re.compile(r"\b([0-9a-f]{7,40})\b")


def _search_text_blob(*parts: Any) -> str:
    """Join arbitrary fields into one lowercased, searchable text blob."""
    return " ".join(_filter_text(part) for part in parts if part is not None).strip()


def _search_date_key(value: Any) -> str:
    """Normalize a timestamp to a ``YYYY-MM-DD`` prefix for date: matching."""
    text = str(value or "").strip()
    return text[:10] if len(text) >= 10 else text


def _review_links_for(entity_id: str, reviews: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Surface related review/meeting docs that mention this entity id."""
    needle = str(entity_id or "").strip().lower()
    links: list[dict[str, str]] = []
    if not needle:
        return links
    for review in reviews:
        haystack = f"{review.get('id', '')} {review.get('source_path', '')} {review.get('body', '')}".lower()
        if needle in haystack:
            links.append({"label": str(review.get("title") or review.get("id")), "path": str(review.get("source_path") or "")})
        if len(links) >= 3:
            break
    return links


def _commit_links_for(*texts: Any) -> list[dict[str, str]]:
    """Surface commit SHAs mentioned in entity text as related-commit links."""
    seen: list[dict[str, str]] = []
    blob = " ".join(_filter_text(text) for text in texts if text is not None)
    for match in _COMMIT_SHA_RE.findall(blob):
        # Skip obvious non-SHA hex (pure digits read as IDs/years).
        if match.isdigit():
            continue
        entry = {"label": match[:10], "sha": match}
        if entry not in seen:
            seen.append(entry)
        if len(seen) >= 3:
            break
    return seen


def build_search_index(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive a flat, read-only search index from the runtime state.

    Each entry carries the normalized fields the search box needs:
    ``entity_type`` / ``id`` / ``title`` / ``status`` / ``owner`` / ``date`` /
    ``text`` (the lowercased searchable blob), the AR-321 hash ``route`` +
    ``entity`` selector used for deep-linking, and any related commit/review
    document links surfaced for that entity.
    """
    reviews = state.get("reviews") or []
    index: list[dict[str, Any]] = []

    def add(
        entity_type: str,
        entity_id: Any,
        title: Any,
        *,
        status: Any = None,
        owner: Any = None,
        date: Any = None,
        text: str = "",
        source_path: Any = None,
        related: list[dict[str, str]] | None = None,
    ) -> None:
        entity_id_str = str(entity_id or "").strip()
        route = SEARCH_ENTITY_ROUTES.get(entity_type, "home/board")
        index.append(
            {
                "entity_type": entity_type,
                "id": entity_id_str,
                "title": str(title or entity_id_str or "(untitled)"),
                "status": str(status or "").strip() or None,
                "owner": str(owner or "").strip() or None,
                "date": _search_date_key(date),
                "text": text.lower(),
                "route": route,
                # Deep-link target: hash route + selected entity id (AR-321).
                "deep_link": f"#/{route}?select={entity_id_str}" if entity_id_str else f"#/{route}",
                "entity": entity_id_str,
                "source_path": str(source_path or "") or None,
                "related": related or [],
            }
        )

    for task in state.get("tasks") or []:
        owner = task.get("owner_agent") or task.get("team")
        text = _search_text_blob(
            task.get("id"), task.get("title"), task.get("status"), task.get("priority"),
            task.get("description"), task.get("peek_summary"), task.get("labels"),
            task.get("task_set_id"), owner,
        )
        related = _review_links_for(task.get("id"), reviews) + _commit_links_for(
            task.get("audit_log"), task.get("peek_summary"), task.get("description"),
        )
        add(
            "task", task.get("id"), task.get("title"),
            status=task.get("status"), owner=owner,
            date=task.get("updated_at") or task.get("created_at"),
            text=text, source_path=task.get("source_path"), related=related,
        )

    for ts in state.get("task_sets") or []:
        text = _search_text_blob(
            ts.get("id"), ts.get("display_name"), ts.get("summary"),
            ts.get("status"), ts.get("status_text"), ts.get("aliases"),
        )
        add(
            "taskset", ts.get("id"), ts.get("display_name") or ts.get("id"),
            status=ts.get("status"),
            text=text, related=_review_links_for(ts.get("id"), reviews),
        )

    for msg in state.get("messages") or []:
        text = _search_text_blob(
            msg.get("id"), msg.get("from"), msg.get("to"), msg.get("intent"),
            msg.get("type"), msg.get("status"), msg.get("body"), msg.get("task_id"),
        )
        add(
            "message", msg.get("id"), (str(msg.get("intent") or msg.get("type") or "message")),
            status=msg.get("status"), owner=msg.get("from"),
            date=msg.get("created_at") or msg.get("ts"),
            text=text, source_path=msg.get("source_path"),
        )

    for ev in state.get("events") or []:
        text = _search_text_blob(
            ev.get("id"), ev.get("event") or ev.get("type"), ev.get("role") or ev.get("actor"),
            ev.get("task_id"), ev.get("goal_id"), ev.get("severity"), ev.get("detail"),
        )
        add(
            "event", ev.get("id"), (str(ev.get("event") or ev.get("type") or "event")),
            status=ev.get("severity"), owner=ev.get("actor") or ev.get("role"),
            date=ev.get("created_at") or ev.get("ts"),
            text=text, source_path=ev.get("source_path"),
        )

    for item in state.get("evidence") or []:
        text = _search_text_blob(
            item.get("id"), item.get("evidence"), item.get("source_type"),
            item.get("task_id"), item.get("goal_id"),
        )
        add(
            "evidence", item.get("id"), (str(item.get("evidence") or "evidence")),
            owner=item.get("source_type"), date=item.get("created_at"),
            text=text, source_path=item.get("source_path"),
            related=_commit_links_for(item.get("evidence")),
        )

    for review in reviews:
        text = _search_text_blob(
            review.get("id"), review.get("title"), review.get("type"),
            review.get("status"), review.get("tags"), review.get("summary"), review.get("body"),
        )
        add(
            "review", review.get("id"), review.get("title"),
            status=review.get("status"), owner=review.get("audience"),
            date=review.get("created_at"),
            text=text, source_path=review.get("source_path"),
            related=_commit_links_for(review.get("body")),
        )

    return index


def parse_search_query(query: str) -> dict[str, Any]:
    """Parse a Slack-style search string into operators + free text.

    Supports ``type:`` / ``status:`` / ``owner:`` / ``date:`` operators (values
    may be quoted). Everything else becomes the free-text term list. Unknown
    ``key:value`` tokens are left in the free text so they still match literally.
    """
    operators: dict[str, str] = {}
    remainder = query or ""
    for match in _SEARCH_OPERATOR_RE.finditer(query or ""):
        key = match.group(1).lower()
        if key not in _SEARCH_OPERATORS:
            continue
        value = match.group(2).strip().strip("\"'")
        operators[key] = value.lower()
        remainder = remainder.replace(match.group(0), " ", 1)
    terms = [token for token in remainder.lower().split() if token]
    return {"operators": operators, "terms": terms, "raw": query or ""}


def run_search(index: list[dict[str, Any]], query: str, *, limit: int = 40) -> list[dict[str, Any]]:
    """Filter + rank the search index for a parsed query.

    Operator filters are applied as exact/prefix matches; free-text terms must
    all appear in the entity's searchable blob (AND semantics). Results are
    ranked: title hits first, then entity-type grouping, then recency.
    """
    parsed = parse_search_query(query)
    operators = parsed["operators"]
    terms = parsed["terms"]
    want_type = operators.get("type")
    want_status = operators.get("status")
    want_owner = operators.get("owner")
    want_date = operators.get("date")

    results: list[dict[str, Any]] = []
    for entry in index:
        if want_type and entry.get("entity_type") != want_type:
            continue
        if want_status and (entry.get("status") or "").lower() != want_status:
            continue
        if want_owner and want_owner not in (entry.get("owner") or "").lower():
            continue
        if want_date and not (entry.get("date") or "").startswith(want_date):
            continue
        text = entry.get("text") or ""
        title = (entry.get("title") or "").lower()
        if terms and not all(term in text for term in terms):
            continue
        title_hit = any(term in title for term in terms) if terms else False
        scored = dict(entry)
        scored["_title_hit"] = title_hit
        results.append(scored)

    results.sort(
        key=lambda item: (
            0 if item.get("_title_hit") else 1,
            item.get("entity_type") or "",
            # Newest first within a tier (descending date string).
            "" if item.get("date") else "z",
        )
    )
    results.sort(key=lambda item: (item.get("date") or ""), reverse=True)
    results.sort(key=lambda item: (0 if item.get("_title_hit") else 1))
    for item in results:
        item.pop("_title_hit", None)
        item.pop("text", None)
    return results[:limit]


# --- Ops dashboard (TASK-AR-339) -------------------------------------------
# A single read-only derivation that powers the Grafana/Sentry-style ops view:
#   1. token + cost aggregation (estimated vs actual) per task and per taskset,
#      with a per-taskset budget bar.
#   2. eval score trend derived from existing eval/gate evidence files.
#   3. a gate status board (pass / watch / block) from reviews/*GATE*.json.
#   4. taskset burndown + weekly completion velocity.
# Everything here is a pure derivation; no file is mutated and missing inputs
# degrade gracefully (empty series / est-only labels) rather than raising.
OPS_METRICS_SCHEMA = "agent-runtime-ops-metrics/v1"
# Cost is a transparent linear derivation of tokens so the chart is meaningful
# even before real billing actuals exist. USD per 1k tokens; documented in the
# payload so the UI can label the figure as a derived estimate.
_OPS_COST_PER_1K_TOKENS = 0.003
# Eval/gate evidence locations. Eval *score* trend is derived from the offline
# eval reports, the live-reviewer gates and the provider-live eval evidence.
_OPS_EVAL_REVIEW_GLOBS = ("OFFLINE-EVAL-*.json", "LIVE-REVIEWER-GATE-*.json")
_OPS_EVAL_EVIDENCE_GLOB = "agents/project/evidence/evaluations/*.json"
# Gate board reads every *GATE*.json record under reviews/.
_OPS_GATE_REVIEW_GLOB = "*GATE*.json"
_OPS_GATE_STATUSES = ("pass", "watch", "block")
# Cap long trend series so the inline SVG stays readable.
_OPS_TREND_LIMIT = 24
_OPS_VELOCITY_WEEKS = 8


def _ops_int(value: Any) -> int:
    """Coerce a frontmatter scalar to a non-negative int (0 on garbage)."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(0, int(value))
    try:
        return max(0, int(str(value).strip()))
    except (TypeError, ValueError):
        return 0


def _ops_cost(tokens: int) -> float:
    return round((max(0, int(tokens)) / 1000.0) * _OPS_COST_PER_1K_TOKENS, 4)


def _ops_iso_week(value: Any) -> str | None:
    """Return the ISO ``YYYY-Www`` week key for a date/timestamp, or None."""
    text = str(value or "").strip()
    if not text:
        return None
    for candidate in (text, text[:19], text[:10]):
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        iso = parsed.isocalendar()
        return f"{iso[0]:04d}-W{iso[1]:02d}"
    return None


def _ops_eval_record(path: Path, root: Path) -> dict[str, Any] | None:
    """Normalize one eval/gate evidence file into a trend point, or None.

    Score is read from ``score`` then ``metric_value``; only numeric scores
    contribute to the trend. ``generated_at`` orders the series.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    raw_score = data.get("score")
    if raw_score is None:
        raw_score = data.get("metric_value")
    try:
        score = float(raw_score)
    except (TypeError, ValueError):
        return None
    return {
        "id": str(data.get("record_id") or path.stem),
        "score": round(score, 4),
        "status": str(data.get("status") or data.get("result") or "").strip().lower(),
        "generated_at": str(data.get("generated_at") or ""),
        "mode": str(
            data.get("evaluation_mode")
            or data.get("metric_name")
            or data.get("scope_boundary")
            or ""
        ),
        "task_ref": str(data.get("task_ref") or data.get("task_id") or ""),
        "minimum_score": data.get("minimum_score") or data.get("minimum_score_by_domain"),
        "source_path": _rel(root, path),
    }


def _ops_eval_trend(root: Path) -> dict[str, Any]:
    """Eval score trend across offline/live/provider evidence (graceful if absent)."""
    points: list[dict[str, Any]] = []
    seen: set[str] = set()
    reviews_dir = root / "reviews"
    if reviews_dir.is_dir():
        for pattern in _OPS_EVAL_REVIEW_GLOBS:
            for path in reviews_dir.glob(pattern):
                point = _ops_eval_record(path, root)
                if point and point["source_path"] not in seen:
                    seen.add(point["source_path"])
                    points.append(point)
    for path in sorted(root.glob(_OPS_EVAL_EVIDENCE_GLOB)):
        point = _ops_eval_record(path, root)
        if point and point["source_path"] not in seen:
            seen.add(point["source_path"])
            points.append(point)
    points.sort(key=lambda item: (item.get("generated_at") or "", item.get("id") or ""))
    points = points[-_OPS_TREND_LIMIT:]
    scores = [p["score"] for p in points]
    latest = points[-1] if points else None
    return {
        "points": points,
        "available": bool(points),
        "count": len(points),
        "latest_score": latest["score"] if latest else None,
        "latest_status": latest["status"] if latest else "",
        "min_score": round(min(scores), 4) if scores else None,
        "max_score": round(max(scores), 4) if scores else None,
        "avg_score": round(sum(scores) / len(scores), 4) if scores else None,
    }


def _ops_gate_board(root: Path) -> dict[str, Any]:
    """Gate status board (pass/watch/block) from reviews/*GATE*.json."""
    gates: list[dict[str, Any]] = []
    counts = {status: 0 for status in _OPS_GATE_STATUSES}
    counts["other"] = 0
    reviews_dir = root / "reviews"
    if reviews_dir.is_dir():
        for path in sorted(reviews_dir.glob(_OPS_GATE_REVIEW_GLOB)):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(data, dict):
                continue
            status = str(data.get("status") or data.get("result") or "").strip().lower()
            bucket = status if status in counts else "other"
            counts[bucket] += 1
            schema = str(data.get("schema") or "")
            kind = schema.split("/")[0].replace("agent-runtime-", "") if schema else path.stem
            gates.append(
                {
                    "id": path.stem,
                    "kind": kind,
                    "status": status or "unknown",
                    "score": data.get("score"),
                    "task_ref": str(data.get("task_ref") or data.get("task_id") or ""),
                    "generated_at": str(data.get("generated_at") or ""),
                    "findings": len(data.get("findings") or []),
                    "source_path": _rel(root, path),
                }
            )
    # block first, then watch, then pass, most recent within each bucket.
    order = {"block": 0, "watch": 1, "pass": 2}
    gates.sort(
        key=lambda g: (order.get(g["status"], 3), _invert_ts(g.get("generated_at"))),
    )
    return {
        "gates": gates,
        "counts": counts,
        "total": len(gates),
        "blocking": counts["block"],
        "available": bool(gates),
    }


def _invert_ts(value: Any) -> str:
    # Sort key helper: newer timestamps first within a status bucket.
    text = str(value or "")
    return "".join(chr(0x10FFFF - ord(c)) if ord(c) < 0x10FFFF else c for c in text) if text else "~"


def build_ops_metrics(
    tasks: list[dict[str, Any]],
    task_sets: list[dict[str, Any]],
    root: Path,
    now: str,
) -> dict[str, Any]:
    """Aggregate the four ops-dashboard widgets from existing read-only inputs."""
    # ---- Token + cost aggregation (estimated vs actual) -------------------
    taskset_buckets: dict[str, dict[str, Any]] = {}
    est_total = 0
    actual_total = 0
    any_actual = False
    per_task: list[dict[str, Any]] = []
    for task in tasks:
        meta = task.get("custom_property_source") or {}
        est = _ops_int(meta.get("est_tokens"))
        has_actual = "actual_tokens" in meta and meta.get("actual_tokens") is not None
        actual = _ops_int(meta.get("actual_tokens")) if has_actual else 0
        if has_actual:
            any_actual = True
        est_total += est
        actual_total += actual
        ts_id = str(task.get("task_set_id") or "").strip() or "UNCLASSIFIED"
        bucket = taskset_buckets.setdefault(
            ts_id,
            {
                "task_set_id": ts_id,
                "est_tokens": 0,
                "actual_tokens": 0,
                "tasks": 0,
                "tasks_with_actual": 0,
            },
        )
        bucket["est_tokens"] += est
        bucket["actual_tokens"] += actual
        bucket["tasks"] += 1
        if has_actual:
            bucket["tasks_with_actual"] += 1
        if est or has_actual:
            per_task.append(
                {
                    "id": str(task.get("id") or ""),
                    "task_set_id": ts_id,
                    "est_tokens": est,
                    "actual_tokens": actual if has_actual else None,
                    "has_actual": has_actual,
                    "est_cost": _ops_cost(est),
                    "actual_cost": _ops_cost(actual) if has_actual else None,
                }
            )
    set_name = {str(ts.get("id") or ""): str(ts.get("display_name") or ts.get("id") or "") for ts in task_sets}
    taskset_rows: list[dict[str, Any]] = []
    for ts_id, bucket in taskset_buckets.items():
        est = bucket["est_tokens"]
        actual = bucket["actual_tokens"]
        # The per-taskset *budget* is the sum of member estimates; actual vs
        # budget gives a consumed-percentage bar (est-only when no actuals).
        budget = est
        consumed = actual if bucket["tasks_with_actual"] else 0
        pct = round((consumed / budget) * 100, 1) if budget and bucket["tasks_with_actual"] else None
        taskset_rows.append(
            {
                "task_set_id": ts_id,
                "display_name": set_name.get(ts_id, ts_id),
                "est_tokens": est,
                "actual_tokens": actual,
                "budget_tokens": budget,
                "est_cost": _ops_cost(est),
                "actual_cost": _ops_cost(actual),
                "tasks": bucket["tasks"],
                "tasks_with_actual": bucket["tasks_with_actual"],
                "has_actual": bool(bucket["tasks_with_actual"]),
                "consumed_pct": pct,
                "over_budget": bool(pct is not None and pct > 100),
            }
        )
    taskset_rows.sort(key=lambda row: (-row["est_tokens"], row["task_set_id"]))
    per_task.sort(key=lambda row: (-row["est_tokens"], row["id"]))
    resources = {
        "schema_note": "cost derived from tokens at USD/1k; not billing actuals",
        "cost_per_1k_tokens": _OPS_COST_PER_1K_TOKENS,
        "est_tokens": est_total,
        "actual_tokens": actual_total,
        "est_cost": _ops_cost(est_total),
        "actual_cost": _ops_cost(actual_total),
        "has_actuals": any_actual,
        "actuals_label": "actual" if any_actual else "estimate-only",
        "tasksets": taskset_rows,
        "tasks": per_task[:_OPS_TREND_LIMIT],
        "task_count": len(per_task),
    }

    # ---- Eval trend + gate board ----------------------------------------
    eval_trend = _ops_eval_trend(root)
    gates = _ops_gate_board(root)

    # ---- Taskset burndown + weekly velocity -----------------------------
    open_total = 0
    done_total = 0
    for task in tasks:
        if _status_bucket(task) == "done":
            done_total += 1
        else:
            open_total += 1
    grand_total = open_total + done_total
    burndown = {
        "total": grand_total,
        "done": done_total,
        "remaining": open_total,
        "pct_done": round((done_total / grand_total) * 100, 1) if grand_total else 0.0,
        "tasksets": [],
    }
    for ts in task_sets:
        total = _ops_int(ts.get("tasks_total"))
        done = _ops_int(ts.get("tasks_done"))
        remaining = max(0, total - done)
        burndown["tasksets"].append(
            {
                "task_set_id": str(ts.get("id") or ""),
                "display_name": str(ts.get("display_name") or ts.get("id") or ""),
                "total": total,
                "done": done,
                "remaining": remaining,
                "pct_done": round((done / total) * 100, 1) if total else 0.0,
            }
        )
    burndown["tasksets"].sort(key=lambda row: (-row["remaining"], row["task_set_id"]))

    # Weekly completion velocity: count tasks whose completed_at falls in each
    # ISO week. Falls back to updated_at for done tasks lacking completed_at.
    week_counts: dict[str, int] = {}
    for task in tasks:
        if _status_bucket(task) != "done":
            continue
        when = task.get("completed_at") or task.get("updated_at")
        week = _ops_iso_week(when)
        if week:
            week_counts[week] = week_counts.get(week, 0) + 1
    weekly = [
        {"week": week, "done": count}
        for week, count in sorted(week_counts.items())
    ][-_OPS_VELOCITY_WEEKS:]
    velocity = {
        "weeks": weekly,
        "available": bool(weekly),
        "total_done": sum(item["done"] for item in weekly),
        "avg_per_week": round(sum(item["done"] for item in weekly) / len(weekly), 2) if weekly else 0.0,
        "peak_week": max((item["done"] for item in weekly), default=0),
    }

    return {
        "schema": OPS_METRICS_SCHEMA,
        "generated_at": now,
        "sources": {
            "tokens": TASKS_GLOB,
            "evals": [REVIEW_GLOB, _OPS_EVAL_EVIDENCE_GLOB],
            "gates": "reviews/*GATE*.json",
            "burndown": TASKS_GLOB,
        },
        "resources": resources,
        "eval_trend": eval_trend,
        "gates": gates,
        "burndown": burndown,
        "velocity": velocity,
    }


# --- Full-state cache (console perf) ----------------------------------------
# build_state assembles ~40 substructures and shells out to git for the inflight
# overlay, so a cold build is multi-second on a large store. The 4s console poll
# must not pay that every time, or the board appears empty while /api/state hangs
# (observed: ~60s, 6.5MB per call on a 800+ record store). Cache the full state
# per root, invalidated by a cheap mtime+count signature over the source dirs that
# change during work, with a long TTL backstop for anything the signature misses.
_STATE_CACHE: dict[str, tuple[float, tuple, dict[str, Any]]] = {}
# Serialize cold builds: the frontend fires a burst of requests on load (state +
# SSE + resources); without this each would pay the full cold build in parallel.
_STATE_BUILD_LOCK = threading.Lock()
_STATE_TTL_BACKSTOP = 300.0
_STATE_SIG_DIRS = (
    "agents/lead_engineer/tasks",
    "agents/runtime",
    "agents/project",
    "reviews",
)


def _state_signature(root_path: Path) -> tuple:
    """Cheap change-detector: (rel, file count, latest mtime) per source dir.

    os.walk + os.stat (no pathlib object churn) so this stays ~0.3s even over the
    whole runtime/project/reviews tree -- two orders of magnitude under a rebuild.
    Any add/remove/edit under these dirs changes the tuple and busts the cache.
    """
    parts: list[tuple[str, int, float]] = []
    for rel in _STATE_SIG_DIRS:
        base = root_path / rel
        if not base.exists():
            continue
        count = 0
        latest = 0.0
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git", "node_modules")]
            for filename in filenames:
                count += 1
                try:
                    mtime = os.stat(os.path.join(dirpath, filename)).st_mtime
                except OSError:
                    continue
                if mtime > latest:
                    latest = mtime
        parts.append((rel, count, round(latest, 3)))
    return tuple(parts)


def build_state(root: Path | str, now: str | None = None) -> dict[str, Any]:
    """Cached front for the full console state (see ``_build_state_uncached``).

    Explicit ``now`` (deterministic test / replay calls) bypasses the cache.
    Otherwise the per-root cache returns instantly while the source signature is
    unchanged; any edit to a task/claim/review/etc. changes the signature and
    forces a rebuild. ``generated_at`` is re-stamped on cache hits so the console
    still shows a live timestamp.
    """
    if now is not None:
        return _build_state_uncached(root, now)
    root_path = Path(root).resolve()
    key = str(root_path)
    signature = _state_signature(root_path)

    def _fresh_hit() -> dict[str, Any] | None:
        cached = _STATE_CACHE.get(key)
        if cached is not None:
            stamped_at, cached_sig, cached_state = cached
            if cached_sig == signature and (time.monotonic() - stamped_at) < _STATE_TTL_BACKSTOP:
                return {**cached_state, "generated_at": _now_iso()}
        return None

    hit = _fresh_hit()
    if hit is not None:
        return hit
    # Cold build: serialize so a request burst does not rebuild in parallel; a
    # request that waited gets the cache the winner just populated.
    with _STATE_BUILD_LOCK:
        hit = _fresh_hit()
        if hit is not None:
            return hit
        state = _build_state_uncached(root_path, now)
        _STATE_CACHE[key] = (time.monotonic(), signature, state)
        return state


def _build_state_uncached(root: Path | str, now: str | None = None) -> dict[str, Any]:
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
    attachments = load_attachments(root_path, generated_at)
    evidence.extend(attachment_evidence(attachments))
    enrich_tasks_with_evidence(tasks, evidence)
    enrich_tasks_with_attachments(tasks, attachments)
    replay = build_replay(events, messages)
    graph = build_graph(tasks, agents, messages, events)
    state_machines = load_state_machines(root_path, tasks, agents, generated_at, events)
    roadmap = load_roadmap(root_path, generated_at)
    planning = _collect_planning(root_path)
    collaboration = build_collaboration(pane_events)
    multipane_assurance = _collect_multipane_assurance(root_path, generated_at, pane_events, warnings)
    inflight = load_inflight(root_path, generated_at, warnings)
    work_explorer = load_work_explorer(root_path, generated_at, warnings)
    meeting_room = build_meeting_room(agents, tasks, now=generated_at)
    channels = build_channels(messages, tasks, task_sets, now=generated_at)
    tasksets_board = build_tasksets_board(work_explorer, tasks, events, task_claims, generated_at)
    work_state = build_work_state_board(root_path, task_sets, tasks, generated_at, warnings)
    taskset_completion = build_taskset_completion(pane_events, task_sets)
    roadmap_timeline = build_roadmap_timeline(roadmap, work_explorer, root_path, generated_at, warnings)
    instances = _load_instances(root_path, generated_at, warnings)
    team_agents = build_team_agents(root_path, instances, agents, task_claims, events, generated_at)
    # Team/role assignment + workload heatmap (TASK-AR-337). Resolution against
    # the canonical TEAMS.md registry is computed once and stamped onto tasks so
    # the heatmap, org chart and board filters all read the same assigned team.
    teams = load_teams(root_path, generated_at, warnings)
    taskset_team_defaults = derive_taskset_team_defaults(tasks, teams)
    enrich_tasks_with_assignment(tasks, teams, taskset_team_defaults)
    teams["taskset_defaults"] = taskset_team_defaults
    workload = build_workload_heatmap(tasks, teams, taskset_team_defaults, generated_at)
    live_map = build_live_map(tasks, agents, messages, team_agents, generated_at)
    # 2D office map (TASK-AR-364): world->areas tree + per-agent placement,
    # derived from the team_agents presence cards (+ events for the recording
    # action). In-meeting agents are relocated to the meeting room.
    office_map = build_office_map(team_agents, events, generated_at)
    dependency_graph = build_dependency_graph(tasks, generated_at)
    timeline = build_timeline(tasks, generated_at)
    # Custom properties / labels / automation rules / triage (TASK-AR-331).
    custom_properties = load_custom_properties(root_path, generated_at, warnings)
    enrich_tasks_with_custom_properties(tasks, custom_properties)
    labels = build_labels(root_path, tasks, generated_at, warnings)
    automation_rules = load_automation_rules(root_path, generated_at, warnings)
    triage = build_triage(tasks, generated_at)
    reviews = load_reviews(root_path, generated_at, warnings)
    # Calendar / scheduling (TASK-AR-335): schedules are declarative records;
    # the calendar aggregates read-only milestones/meetings/completions/deadlines
    # plus scheduled dispatches and publishes due-soon/overdue reminders.
    schedules = load_schedules(root_path, generated_at, warnings)
    calendar = build_calendar(tasks, roadmap, reviews, taskset_completion, schedules, generated_at)
    # Ops dashboard (TASK-AR-339): token/cost, eval trend, gate board, burndown.
    # Pure read-only derivation over tasks + task_sets + eval/gate evidence files.
    ops_metrics = build_ops_metrics(tasks, task_sets, root_path, generated_at)
    # Notification center + @mentions + daily brief (TASK-AR-338). The inbox
    # consumes the calendar's due-soon/overdue reminders plus blocked/approval/
    # mention/error events; the daily brief summarizes today's work. Notification
    # preferences are read-only here (authored proposal-only via ui_commands).
    notifications_config = load_notifications_config(root_path, generated_at, warnings)
    notifications = build_notifications(events, calendar, tasks, messages, notifications_config, generated_at)
    daily_brief = build_daily_brief(tasks, events, messages, reviews, notifications, generated_at)
    # External notification routing (TASK-AR-365): SECRET-FREE status only. The
    # local config (webhook URLs / tokens / SMTP creds) is gitignored and is
    # NEVER read into served state -- routing_status strips every secret value
    # and reports only channel name / kind / enabled flag / subscribed
    # severities. Default state is DORMANT (no channels => nothing sends).
    notification_routing = notify_routing.routing_status(root_path, generated_at)
    # Growth system (TASK-AR-363): project Lv / business stage / XP, computed
    # ONLY from outcomes (completed tasks, gate passes, test growth, reviews) --
    # token spend is excluded from XP and reported only as an efficiency stat.
    gamification_policy = load_gamification_policy(root_path, generated_at)
    growth = build_growth(
        tasks,
        task_claims,
        events,
        reviews,
        team_agents,
        roadmap_timeline,
        gamification_policy,
        generated_at,
    )
    # Platform extensions (TASK-AR-341): workspace switcher list, declarative
    # Home widgets, and the KR/EN i18n string table. All read-only / data-only.
    workspaces = load_workspaces(root_path, generated_at)
    widgets = load_widgets(root_path, generated_at)
    i18n = build_i18n(generated_at)
    state: dict[str, Any] = {
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
        "work_state": work_state,
        "taskset_completion": taskset_completion,
        "team_agents": team_agents,
        "teams": teams,
        "growth": growth,
        "workload": workload,
        "messages": messages,
        "events": events,
        "goals": goals,
        "errors": errors,
        "evidence": evidence,
        "attachments": attachments,
        "replay": replay,
        "graph": graph,
        "live_map": live_map,
        "office_map": office_map,
        "dependency_graph": dependency_graph,
        "timeline": timeline,
        "state_machines": state_machines,
        "roadmap": roadmap,
        "roadmap_timeline": roadmap_timeline,
        "planning": planning,
        "custom_properties": custom_properties,
        "labels": labels,
        "automation_rules": automation_rules,
        "triage": triage,
        "reviews": reviews,
        "schedules": schedules,
        "calendar": calendar,
        "ops_metrics": ops_metrics,
        "notifications": notifications,
        "daily_brief": daily_brief,
        "notification_routing": notification_routing,
        "workspaces": workspaces,
        "widgets": widgets,
        "i18n": i18n,
        "commands": commands,
        "gaps": gaps,
        "warnings": warnings,
    }
    # Global search index is derived from the assembled state (TASK-AR-334).
    state["search_index"] = build_search_index(state)
    return state


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
