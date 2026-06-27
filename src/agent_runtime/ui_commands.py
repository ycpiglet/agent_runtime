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
TASK_COMMAND_TYPES = (
    "task.create",
    "task.update",
    "task.reorder",
    "task.comment",
    "task.archive",
    "task.move",
    "task.bulk_edit",
)
# TASK-AR-329: Owner-driven taskset lifecycle from the Tasksets view. These are
# proposal-only: the handler records a proposal under .ui_outbox/tasksets that a
# runtime executor consumes (via scripts/backlog_board.py sync_taskset_registry)
# to write the canonical TASKSET-DEFINITIONS.json registry. The console NEVER
# writes the registry/board directly.
TASKSET_COMMAND_TYPES = (
    "taskset.create",
    "taskset.rename",
    "taskset.archive",
    "taskset.template",
)
# Built-in 1-click taskset templates (Linear Projects / Notion DB recurring
# patterns). Each instantiation emits a registry-create proposal for the new
# taskset plus task.create proposals for the template tasks.
TASKSET_TEMPLATES = {
    "analysis-suite": {
        "display_name": "Analysis Suite",
        "summary": "Recurring 4-step analysis taskset: intake, structure mapping, gap finding, and follow-up planning.",
        "tasks": [
            {"title": "Intake and scope the analysis", "priority": "P1"},
            {"title": "Map current structure and sources", "priority": "P1"},
            {"title": "Find gaps and risks", "priority": "P1"},
            {"title": "Draft follow-up plan and decisions", "priority": "P2"},
        ],
    },
    "release-cycle": {
        "display_name": "Release Cycle",
        "summary": "Recurring release taskset: version decision, preflight checks, closeout evidence.",
        "tasks": [
            {"title": "Decide version bump", "priority": "P1"},
            {"title": "Run release preflight checks", "priority": "P0"},
            {"title": "Record closeout evidence", "priority": "P2"},
        ],
    },
}
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
PLANNING_COMMAND_TYPES = ("planning.scan", "planning.approve", "planning.reject")
# TASK-AR-327: Owner-summoned consensus rounds from the Channels view. Both are
# proposal-only: the handler records a proposal under .ui_outbox that a runtime
# executor consumes (via scripts/meeting_room.py plan) to write the canonical
# reviews/MEETING-* or reviews/SEMINAR-* record. The console NEVER writes the
# reviews/ file directly.
MEETING_COMMAND_TYPES = ("meeting.start", "seminar.start")
# TASK-AR-331: Custom properties / labels / automation-rule CRUD. Every one of
# these is PROPOSAL-ONLY: the handler records a declarative proposal under
# .ui_outbox/{properties,labels,automation} that a runtime executor consumes to
# write the canonical agents/project/ui/** or agents/project/automation/rules/**
# file. The console NEVER writes those canonical files directly. Rule EXECUTION
# is owned by scripts/automation_rules_gate.py in the gate chain.
PROPERTY_COMMAND_TYPES = ("property.create", "property.update", "property.delete")
LABEL_COMMAND_TYPES = ("label.create", "label.update", "label.delete")
AUTOMATION_COMMAND_TYPES = ("automation.create", "automation.update", "automation.delete", "automation.toggle")
UI_CONFIG_COMMAND_TYPES = PROPERTY_COMMAND_TYPES + LABEL_COMMAND_TYPES + AUTOMATION_COMMAND_TYPES
# TASK-AR-332: link an already-uploaded attachment to a task as closeout
# evidence. The bytes are written by the upload route (ui_state.save_attachment);
# RE-targeting that attachment's evidence linkage is a NON-upload mutation and is
# therefore PROPOSAL-ONLY: the handler records a proposal under
# .ui_outbox/attachments that a runtime executor consumes to update the canonical
# task frontmatter / evidence index. The console NEVER edits the task file here.
ATTACHMENT_COMMAND_TYPES = ("attachment.link",)
# TASK-AR-335: reserve / repeat (cron-like) taskset dispatch from the Calendar
# view. Every one of these is PROPOSAL-ONLY: the handler records a declarative
# schedule record under agents/project/schedules/*.json (via a proposal in
# .ui_outbox/schedules). The console NEVER runs taskset_dispatcher and NEVER
# writes the SSoT. A LOCAL scheduler/gate (scripts/scheduled_dispatch_gate.py)
# is the single point that reads due schedules and emits dispatch + reminder
# events; no external services or network are involved.
SCHEDULE_COMMAND_TYPES = ("schedule.create", "schedule.cancel")
# TASK-AR-337: change a task's team/role/assignee from the heatmap or org chart.
# PROPOSAL-ONLY: the handler records a declarative proposal under
# .ui_outbox/assignments that a runtime executor consumes to update the task
# frontmatter (team/role/assignee). The console NEVER edits the task file here.
ASSIGNMENT_COMMAND_TYPES = ("assignment.set",)
# TASK-AR-338: notification center + @mentions + message pin/reaction. Every one
# of these is PROPOSAL-ONLY.
#   - mention.notify: an @mention emits a runtime message proposal to the target
#     (reusing the runtime message-queue path) so the mentioned agent/role/Owner
#     receives a runtime message; the inbox then surfaces the mention.
#   - message.pin / message.react: record a declarative proposal under
#     .ui_outbox/messages for a runtime executor to apply to the message record.
#   - notification.read / notification.mute / notification.subscribe: record a
#     declarative preferences proposal under .ui_outbox/notifications that a
#     runtime executor applies to agents/project/ui/notifications.json. The
#     console NEVER writes that canonical config file directly.
MENTION_COMMAND_TYPES = ("mention.notify",)
MESSAGE_COMMAND_TYPES = ("message.pin", "message.react")
NOTIFICATION_COMMAND_TYPES = ("notification.read", "notification.mute", "notification.subscribe")
# Reactions are normalized to a fixed safe set so a rendered chip can never carry
# arbitrary user input as markup/CSS.
MESSAGE_REACTIONS = ("ack", "thumbsup", "eyes", "celebrate", "question", "blocked")
# Notification preference axes the inbox can subscribe to.
NOTIFICATION_KINDS = ("reminder", "blocked", "approval", "mention", "error")
NOTIFICATION_SEVERITIES = ("overdue", "blocked", "error", "approval", "due_soon", "mention", "info")
# TASK-AR-365: per-channel notification subscription-rule CRUD from the external
# notification-routing view. Every one of these is PROPOSAL-ONLY: the handler
# records a declarative proposal under .ui_outbox/notifications that a runtime
# executor applies to the LOCAL gitignored notifications config. The console
# NEVER writes the local config, NEVER accepts secret values (webhook URLs /
# tokens / SMTP creds are rejected if present), and NEVER sends to any external
# service. Actual dispatch is a separate opt-in local runner.
SUBSCRIPTION_COMMAND_TYPES = ("subscription.create", "subscription.update", "subscription.delete", "subscription.toggle")
# Secret-bearing payload keys the console must NEVER carry on a proposal. A
# subscription proposal only references a channel by name + recipe kind +
# subscribed severities; the owner fills secrets directly into the local config.
SUBSCRIPTION_SECRET_KEYS = {
    "webhook_url",
    "url",
    "bot_token",
    "token",
    "chat_id",
    "smtp_host",
    "smtp_user",
    "smtp_password",
    "password",
    "api_key",
    "auth",
    "authorization",
}
NOTIFICATION_CHANNEL_KINDS = ("discord", "telegram", "email")
# Routing modes by severity (AR-365). Named distinctly from AR-338's
# NOTIFICATION_SEVERITIES (notification kinds) to avoid a name collision.
NOTIFICATION_ROUTING_MODES = ("immediate", "aggregate", "digest")
NOTIFICATION_AGGREGATE_WINDOWS = (5, 15)

CUSTOM_PROPERTY_TYPES = ("text", "select", "number", "date")
AUTOMATION_TRIGGERS = ("status_change", "due_passed", "blocked_too_long")
AUTOMATION_ACTIONS = ("board_regen", "escalation_message", "label_apply")
# Fixed semantic label-color tokens (mirror ui_state.LABEL_COLOR_TOKENS). A
# label color request is always normalized to one of these so a rendered chip
# can only ever consume var(--<token>); user input never becomes raw CSS.
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
MEETING_TYPES = ("meeting", "seminar", "review")
MEETING_MIN_PARTICIPANTS = 2
MEETING_DEFAULT_ROUNDS = 3
MEETING_MAX_ROUNDS = 20
# Upper bound on a task title. The created task filename is
# ``TASK-UI-<14 digits>-<slug-of-title>.md``; without a bound a multi-thousand
# character title produces a path over the OS limit and ``write_text`` raises an
# uncaught OSError that resets the HTTP connection (beta-exploration finding).
# 200 chars keeps the slug well within every common path limit (Windows MAX_PATH
# is 260 incl. the absolute prefix) while staying generous for real titles.
TASK_TITLE_MAX_LENGTH = 200
TASK_BOARD_SYNC_COMMANDS = {"task.create", "task.update", "task.reorder", "task.archive", "task.move", "task.bulk_edit"}
# SPEC-decision-inbox-v1: the cockpit attention inbox lets the operator respond to
# an item with a light, reversible, proposal-only decision. acknowledge ("I have
# seen / I approve this"), comment (an opinion/question), and hold ("pause this").
# All three only RECORD a decision under .ui_outbox/decisions/; a runtime executor
# (v2) consumes them. They never mutate a canonical task from the UI.
DECISION_COMMAND_TYPES = ("decision.acknowledge", "decision.comment", "decision.hold")
COMMAND_TYPES = (
    TASK_COMMAND_TYPES
    + TASKSET_COMMAND_TYPES
    + RUNTIME_COMMAND_TYPES
    + PLANNING_COMMAND_TYPES
    + MEETING_COMMAND_TYPES
    + UI_CONFIG_COMMAND_TYPES
    + ATTACHMENT_COMMAND_TYPES
    + SCHEDULE_COMMAND_TYPES
    + ASSIGNMENT_COMMAND_TYPES
    + MENTION_COMMAND_TYPES
    + MESSAGE_COMMAND_TYPES
    + NOTIFICATION_COMMAND_TYPES
    + SUBSCRIPTION_COMMAND_TYPES
    + DECISION_COMMAND_TYPES
)
# TASK-AR-335: a schedule fires either once at a fixed time (``reserve``) or on a
# recurring cron-like cadence (``repeat``). The cron expression is a 5-field
# POSIX-style schedule (minute hour day-of-month month day-of-week) restricted to
# ``*`` / integers / comma lists / ``*/step``; we only PARSE + validate it here so
# the proposal carries a normalized spec. The local scheduler does the matching.
SCHEDULE_MODES = ("reserve", "repeat")
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


def _validate_task_set_id(task_set_id: Any) -> str | None:
    if not isinstance(task_set_id, str) or not task_set_id.strip():
        return "missing taskset id"
    if not re.fullmatch(r"TASKSET-[A-Za-z0-9-]+", task_set_id.strip()):
        return f"invalid taskset id: {task_set_id!r}"
    return None


def _taskset_id_from_name(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name.strip()).strip("-").upper()
    return f"TASKSET-{slug or 'NEW'}"


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
    elif len(title) > TASK_TITLE_MAX_LENGTH:
        errors.append(f"title is too long: {len(title)} chars (max {TASK_TITLE_MAX_LENGTH})")
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


def _move_task(root: Path, target: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    """Move a task into another taskset by updating its task_set_id frontmatter.

    Reuses the established task-update mutation path (the runtime executor writes
    the task file and re-syncs the board); the console only proposes the move.
    """
    task_set_id = str(payload.get("task_set_id") or payload.get("to_task_set_id") or "").strip()
    error = _validate_task_set_id(task_set_id)
    if error:
        return {"errors": [error]}
    if not target:
        return {"errors": ["missing task id"]}
    path = _task_path(root, target)
    if path is None:
        return {"errors": [f"task not found: {target}"]}
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    meta["task_set_id"] = task_set_id
    path.write_text(serialize_frontmatter(meta, body), encoding="utf-8")
    return {"changed": [_rel(root, path)], "task_set_id": task_set_id}


def _bulk_edit_tasks(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Apply the same status/priority/owner change to multiple tasks at once.

    The result captures a per-task before/after snapshot so the UI can render an
    undo toast; the inverse edit is itself a task.bulk_edit command.
    """
    task_ids = payload.get("task_ids")
    if not isinstance(task_ids, list) or not task_ids:
        return {"errors": ["task_ids must be a non-empty list"]}
    fields = {key: payload[key] for key in ("status", "priority", "owner") if key in payload}
    if not fields:
        return {"errors": ["bulk edit requires at least one of status/priority/owner"]}
    field_errors = _payload_errors(fields)
    if field_errors:
        return {"errors": field_errors}

    changed: list[str] = []
    undo: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw_id in task_ids:
        task_id = str(raw_id or "").strip()
        id_error = _validate_task_id(task_id)
        if id_error:
            errors.append(id_error)
            continue
        path = _task_path(root, task_id)
        if path is None:
            errors.append(f"task not found: {task_id}")
            continue
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        before = {key: meta.get(key) for key in fields}
        meta.update(fields)
        path.write_text(serialize_frontmatter(meta, body), encoding="utf-8")
        changed.append(_rel(root, path))
        undo.append({"id": task_id, "before": before})
    if errors:
        return {"errors": errors}
    return {
        "changed": changed,
        "result": {
            "changed": changed,
            "applied": fields,
            "count": len(changed),
            "undo": {"type": "task.bulk_edit", "items": undo, "fields": list(fields)},
        },
    }


def _taskset_lifecycle_command(
    root: Path,
    command_type: str,
    target: str | None,
    payload: dict[str, Any],
    now: str,
    command_id: str,
) -> dict[str, Any]:
    """Record a proposal-only taskset create/rename/archive request.

    The console does NOT write the canonical TASKSET-DEFINITIONS.json registry
    or BACKLOG-BOARD.md; it emits a proposal under .ui_outbox/tasksets plus a
    runtime event. A runtime executor consumes the proposal and runs
    ``scripts/backlog_board.py`` ``sync_taskset_registry`` to write the registry,
    then ``--write`` to regenerate the board, keeping registry, board, and the
    state-sync gate consistent.
    """
    if command_type == "taskset.create":
        display_name = str(payload.get("display_name") or payload.get("name") or "").strip()
        if not display_name:
            return {"errors": ["display_name is required"]}
        task_set_id = str(payload.get("task_set_id") or "").strip() or _taskset_id_from_name(display_name)
    else:
        task_set_id = str(payload.get("task_set_id") or target or "").strip()
        display_name = str(payload.get("display_name") or payload.get("name") or "").strip()
    id_error = _validate_task_set_id(task_set_id)
    if id_error:
        return {"errors": [id_error]}
    if command_type == "taskset.rename" and not display_name:
        return {"errors": ["display_name is required"]}

    summary = str(payload.get("summary") or "").strip()
    archived = command_type == "taskset.archive"
    action = {"taskset.create": "create", "taskset.rename": "rename", "taskset.archive": "archive"}[command_type]
    order_value = payload.get("order")
    try:
        order = int(order_value) if order_value is not None else None
    except (TypeError, ValueError):
        return {"errors": ["order must be an integer"]}

    proposal = {
        "id": command_id.replace("COMMAND-", "TASKSETREQ-"),
        "type": command_type,
        "action": action,
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "owner"),
        "task_set_id": task_set_id,
        "display_name": display_name or None,
        "summary": summary or None,
        "order": order,
        "archived": archived,
        "registry": "agents/project/work-items/TASKSET-DEFINITIONS.json",
        "sync": (
            "python -c \"import sys; sys.path.insert(0, 'scripts'); import backlog_board;"
            f" backlog_board.sync_taskset_registry('.', {json.dumps(task_set_id)},"
            f" display_name={json.dumps(display_name)}, summary={json.dumps(summary)},"
            f" order={order!r}, archived={archived!r})\""
        ),
        "regenerate_board": "python scripts/backlog_board.py --write",
        "mutation_boundary": "proposal_only",
        "next": "runtime executor must call sync_taskset_registry then regenerate the board",
    }
    path = root / ".ui_outbox" / "tasksets" / f"{proposal['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    event_path = root / "agents" / "runtime" / "events" / "ui_taskset_requests.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": now,
        "event": command_type,
        "role": str(payload.get("actor") or "owner"),
        "task_set_id": task_set_id,
        "display_name": display_name or None,
        "proposal_id": proposal["id"],
        "source": "ui_console",
    }
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {
        "status": "queued",
        "result": {
            "changed": [_rel(root, path), _rel(root, event_path)],
            "proposal_id": proposal["id"],
            "task_set_id": task_set_id,
            "action": action,
            "runtime_support": "taskset_registry_proposal",
            "mutation_boundary": "proposal_only",
            "next": proposal["next"],
        },
    }


def _taskset_template_command(
    root: Path,
    payload: dict[str, Any],
    now: str,
    command_id: str,
) -> dict[str, Any]:
    """Instantiate a recurring taskset template in one click (proposal-only).

    Emits one taskset-create proposal for the new taskset plus a task.create
    proposal for each template task, all under .ui_outbox. The runtime executor
    registers the taskset and creates the tasks.
    """
    template_key = str(payload.get("template") or payload.get("template_key") or "").strip()
    template = TASKSET_TEMPLATES.get(template_key)
    if template is None:
        return {"errors": [f"unknown taskset template: {template_key!r}"]}
    display_name = str(payload.get("display_name") or payload.get("name") or template["display_name"]).strip()
    task_set_id = str(payload.get("task_set_id") or "").strip() or _taskset_id_from_name(display_name)
    id_error = _validate_task_set_id(task_set_id)
    if id_error:
        return {"errors": [id_error]}

    template_tasks = template.get("tasks", [])
    proposed_tasks = []
    for index, spec in enumerate(template_tasks, start=1):
        proposed_tasks.append(
            {
                "type": "task.create",
                "payload": {
                    "title": spec["title"],
                    "priority": spec.get("priority", "P1"),
                    "status": "planned",
                    "task_set_id": task_set_id,
                    "owner": str(payload.get("owner") or "lead-engineer"),
                    "actor": str(payload.get("actor") or "owner"),
                },
            }
        )

    proposal = {
        "id": command_id.replace("COMMAND-", "TASKSETTPL-"),
        "type": "taskset.template",
        "action": "template_instantiate",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "owner"),
        "template": template_key,
        "task_set_id": task_set_id,
        "display_name": display_name,
        "summary": template["summary"],
        "taskset_create": {
            "type": "taskset.create",
            "payload": {
                "task_set_id": task_set_id,
                "display_name": display_name,
                "summary": template["summary"],
            },
        },
        "tasks": proposed_tasks,
        "task_count": len(proposed_tasks),
        "registry": "agents/project/work-items/TASKSET-DEFINITIONS.json",
        "mutation_boundary": "proposal_only",
        "next": "runtime executor registers the taskset then creates each template task",
    }
    path = root / ".ui_outbox" / "tasksets" / f"{proposal['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "queued",
        "result": {
            "changed": [_rel(root, path)],
            "proposal_id": proposal["id"],
            "task_set_id": task_set_id,
            "template": template_key,
            "task_count": len(proposed_tasks),
            "runtime_support": "taskset_template_proposal",
            "mutation_boundary": "proposal_only",
            "next": proposal["next"],
        },
    }


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


def _planning_decision_command(root: Path, command_type: str, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    errors = _payload_errors(payload)
    proposal_id = str(payload.get("proposal_id") or payload.get("id") or "").strip()
    if not proposal_id:
        errors.append("proposal_id is required")
    reason = str(payload.get("reason") or "").strip()
    if not reason:
        errors.append("reason is required")
    if payload.get("apply") is True or payload.get("mutate") is True:
        errors.append("planner decision commands cannot apply canonical mutations")
    if errors:
        return {"errors": errors}
    action = "approved" if command_type == "planning.approve" else "rejected"
    decision = {
        "id": command_id.replace("COMMAND-", "PLANDEC-"),
        "type": command_type,
        "proposal_id": proposal_id,
        "status": action,
        "created_at": now,
        "decided_by": str(payload.get("actor") or "ui"),
        "reason": reason,
        "gate": "scripts/planning_loop.py gate --trigger ui --action scan",
        "canonical_mutation_allowed": False,
        "next": "planner gate must consume this decision before any apply step",
    }
    path = root / "agents" / "planning" / "decisions" / f"{decision['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "queued",
        "result": {
            "changed": [_rel(root, path)],
            "planning_support": "decision_audit_record",
            "canonical_mutation_allowed": False,
            "next": decision["next"],
        },
    }


_DECISION_ACTIONS = {
    "decision.acknowledge": "acknowledged",
    "decision.comment": "commented",
    "decision.hold": "held",
}


def _decision_command(
    root: Path,
    command_type: str,
    target: str | None,
    payload: dict[str, Any],
    now: str,
    command_id: str,
) -> dict[str, Any]:
    """Record a proposal-only operator decision on an attention-inbox item.

    SPEC-decision-inbox-v1. The console NEVER mutates a canonical task here; it
    writes one auditable decision record under ``.ui_outbox/decisions/`` (the same
    proposal convention as meetings/tasksets). A runtime executor consumes it
    later. ``acknowledge`` needs no reason; ``comment`` and ``hold`` require one.
    """
    errors = _payload_errors(payload)
    item_id = str(target or payload.get("target") or payload.get("id") or "").strip()
    if not item_id:
        errors.append("target (inbox item id) is required")
    reason = str(payload.get("reason") or payload.get("note") or "").strip()
    if command_type in {"decision.comment", "decision.hold"} and not reason:
        errors.append("reason is required")
    if payload.get("apply") is True or payload.get("mutate") is True:
        errors.append("decision commands cannot apply canonical mutations")
    if errors:
        return {"errors": errors}

    decision = {
        "id": command_id.replace("COMMAND-", "DECISION-"),
        "type": command_type,
        "target": item_id,
        "group": (str(payload.get("group") or "").strip() or None),
        "title": (str(payload.get("title") or "").strip() or None),
        "action": _DECISION_ACTIONS[command_type],
        "status": "queued",
        "created_at": now,
        "decided_by": str(payload.get("actor") or "owner"),
        "reason": reason or None,
        "canonical_mutation_allowed": False,
        "mutation_boundary": "proposal_only",
        "next": "runtime executor must consume this decision before any canonical mutation",
    }
    path = root / ".ui_outbox" / "decisions" / f"{decision['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    changed = [_rel(root, path)]
    # v2: a comment on a REAL task is also relayed to the agent message inbox (the
    # same channel task.comment uses), so the operator genuinely reaches the agents
    # working it instead of only leaving an audit record. Non-task items (e.g. claim
    # conflicts) get the record above only. This writes an agent message, never a
    # task mutation, so the proposal-only / canonical_mutation_allowed:false contract
    # still holds.
    agent_routed = False
    if command_type == "decision.comment" and reason and _task_path(root, item_id) is not None:
        relay = _comment_task(
            root,
            item_id,
            {"comment": reason, "to": payload.get("to") or "lead-engineer", "actor": payload.get("actor")},
            now,
        )
        if "changed" in relay:
            changed.extend(relay["changed"])
            agent_routed = True
        # else: the task vanished between the _task_path check and the relay (rare
        # race). The decision proposal above is already durable; we degrade to
        # record-only and the UI honestly shows "recorded" (not "delivered"),
        # agent_routed staying False. Errors are intentionally not fatal here.

    return {
        "status": "queued",
        "result": {
            "changed": changed,
            "decision": decision["action"],
            "agent_routed": agent_routed,
            "canonical_mutation_allowed": False,
            "next": decision["next"],
        },
    }


def _normalize_participants(value: Any) -> list[str]:
    """Dedupe (case-insensitive, first wins) and drop blanks, preserving order."""
    if isinstance(value, str):
        candidates: list[Any] = re.split(r"[,\n]", value)
    elif isinstance(value, (list, tuple)):
        candidates = list(value)
    else:
        candidates = []
    seen: set[str] = set()
    result: list[str] = []
    for candidate in candidates:
        name = str(candidate if candidate is not None else "").strip().lstrip("@")
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(name)
    return result


def _meeting_date_and_slug(topic: str, now: str) -> tuple[str, str]:
    today = re.match(r"(\d{4}-\d{2}-\d{2})", now)
    date = today.group(1) if today else datetime.now().strftime("%Y-%m-%d")
    return date, _slug(topic)


def _meeting_command(
    root: Path,
    command_type: str,
    target: str | None,
    payload: dict[str, Any],
    now: str,
    command_id: str,
) -> dict[str, Any]:
    """Record a proposal-only meeting/seminar consensus-round request.

    The console does NOT write the reviews/ record directly; it emits a proposal
    under .ui_outbox describing the consensus round (topic, participants, rounds)
    plus a runtime event so the conversation is traceable. A runtime executor
    consumes the proposal and runs ``scripts/meeting_room.py plan`` to write the
    canonical reviews/MEETING-* or reviews/SEMINAR-* record.
    """
    meeting_type = "seminar" if command_type == "seminar.start" else "meeting"
    topic = str(payload.get("topic") or payload.get("instruction") or "").strip()
    participants = _normalize_participants(
        payload.get("participants")
        or payload.get("roles")
        or ([target] if target else [])
    )
    task_id = payload.get("task_id")
    channel = str(payload.get("channel") or "").strip()
    try:
        rounds = int(payload.get("rounds", MEETING_DEFAULT_ROUNDS))
    except (TypeError, ValueError):
        rounds = -1

    errors: list[str] = []
    if not topic:
        errors.append("topic is required")
    if meeting_type == "meeting" and len(participants) < MEETING_MIN_PARTICIPANTS:
        errors.append(f"at least {MEETING_MIN_PARTICIPANTS} participants are required for a meeting")
    if rounds < 1:
        errors.append("rounds must be > 0")
    elif rounds > MEETING_MAX_ROUNDS:
        errors.append(f"rounds must be <= {MEETING_MAX_ROUNDS}")
    if errors:
        return {"errors": errors}

    date, topic_slug = _meeting_date_and_slug(topic, now)
    record_prefix = "SEMINAR" if meeting_type == "seminar" else "MEETING"
    records_to = f"reviews/{record_prefix}-{date}-{topic_slug}.md"
    proposal = {
        "id": command_id.replace("COMMAND-", "MEETREQ-"),
        "type": command_type,
        "meeting_type": meeting_type,
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "owner"),
        "topic": topic,
        "task_id": task_id,
        "channel": channel or None,
        "participants": participants,
        "rounds": rounds,
        "consensus_round": True,
        "records_to": records_to,
        "script": (
            f"python scripts/meeting_room.py plan --type {meeting_type}"
            f" --topic {json.dumps(topic, ensure_ascii=False)} --rounds {rounds}"
            + ("".join(f" --participant {p}" for p in participants))
            + (f" --task-id {task_id}" if task_id else "")
        ),
        "mutation_boundary": "proposal_only",
        "next": "runtime meeting executor must run the consensus round and write the reviews/ record",
    }
    path = root / ".ui_outbox" / "meetings" / f"{proposal['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Runtime event so the summon is traceable from the Channels conversation.
    event_path = root / "agents" / "runtime" / "events" / "ui_meeting_requests.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": now,
        "event": f"{meeting_type}.start",
        "role": str(payload.get("actor") or "owner"),
        "task_id": task_id,
        "topic": topic,
        "channel": channel or None,
        "participants": participants,
        "rounds": rounds,
        "proposal_id": proposal["id"],
        "records_to": records_to,
        "source": "ui_console",
    }
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return {
        "status": "queued",
        "result": {
            "changed": [_rel(root, path), _rel(root, event_path)],
            "proposal_id": proposal["id"],
            "meeting_type": meeting_type,
            "records_to": records_to,
            "participants": participants,
            "rounds": rounds,
            "runtime_support": "consensus_round_proposal",
            "mutation_boundary": "proposal_only",
            "next": proposal["next"],
        },
    }


# ----- TASK-AR-331: property / label / automation-rule CRUD (proposal-only) -----


def _label_color_token(value: Any) -> str:
    """Normalize any color request to a fixed semantic token (never raw CSS)."""
    key = str(value or "").strip().lower()
    if key in LABEL_COLOR_TOKENS:
        return key
    if not key:
        return "primary"
    digest = sum(ord(char) for char in key)
    return LABEL_COLOR_TOKENS[digest % len(LABEL_COLOR_TOKENS)]


def _ui_key(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", str(value or "").strip()).strip("-").lower()


def _write_ui_proposal(root: Path, subdir: str, proposal: dict[str, Any]) -> str:
    path = root / ".ui_outbox" / subdir / f"{proposal['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return _rel(root, path)


def _property_command(root: Path, command_type: str, target: str | None, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    action = command_type.split(".", 1)[1]
    key = _ui_key(target or payload.get("key") or payload.get("id"))
    errors: list[str] = []
    if not key:
        errors.append("property key is required")
    prop_type = str(payload.get("type") or "text").strip().lower()
    if action in {"create", "update"} and prop_type not in CUSTOM_PROPERTY_TYPES:
        errors.append(f"invalid property type: {prop_type!r} (expected {', '.join(CUSTOM_PROPERTY_TYPES)})")
    options = payload.get("options") if isinstance(payload.get("options"), list) else []
    if action in {"create", "update"} and prop_type == "select" and not options:
        errors.append("select property requires at least one option")
    if errors:
        return {"errors": errors}

    proposal = {
        "id": command_id.replace("COMMAND-", "PROPREQ-"),
        "type": command_type,
        "action": action,
        "target_file": "agents/project/ui/custom-properties.json",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "ui"),
        "key": key,
        "definition": None
        if action == "delete"
        else {
            "key": key,
            "label": str(payload.get("label") or key),
            "type": prop_type,
            "options": [str(option) for option in options if str(option).strip()],
            "filterable": bool(payload.get("filterable", True)),
        },
        "mutation_boundary": "proposal_only",
        "next": "runtime executor applies this proposal to agents/project/ui/custom-properties.json",
    }
    changed = _write_ui_proposal(root, "properties", proposal)
    return {"status": "queued", "result": {"changed": [changed], "proposal_id": proposal["id"], "action": action, "mutation_boundary": "proposal_only", "next": proposal["next"]}}


def _label_command(root: Path, command_type: str, target: str | None, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    action = command_type.split(".", 1)[1]
    name = str(target or payload.get("name") or "").strip()
    errors: list[str] = []
    if not name:
        errors.append("label name is required")
    if errors:
        return {"errors": errors}

    color_token = _label_color_token(payload.get("color") or payload.get("color_token"))
    proposal = {
        "id": command_id.replace("COMMAND-", "LABELREQ-"),
        "type": command_type,
        "action": action,
        "target_file": "agents/project/ui/labels.json",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "ui"),
        "name": name,
        "label": None
        if action == "delete"
        else {
            "name": name,
            "color_token": color_token,
            "description": str(payload.get("description") or ""),
        },
        "mutation_boundary": "proposal_only",
        "next": "runtime executor applies this proposal to agents/project/ui/labels.json",
    }
    changed = _write_ui_proposal(root, "labels", proposal)
    return {"status": "queued", "result": {"changed": [changed], "proposal_id": proposal["id"], "action": action, "color_token": color_token, "mutation_boundary": "proposal_only", "next": proposal["next"]}}


def _automation_command(root: Path, command_type: str, target: str | None, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    action = command_type.split(".", 1)[1]
    rule_id = str(target or payload.get("id") or payload.get("rule_id") or "").strip()
    errors: list[str] = []
    if action in {"update", "delete", "toggle"} and not rule_id:
        errors.append("rule id is required")
    trigger = str(payload.get("trigger") or "").strip()
    action_kind = str(payload.get("action") or "").strip()
    if action in {"create", "update"}:
        if trigger not in AUTOMATION_TRIGGERS:
            errors.append(f"invalid trigger: {trigger!r} (expected {', '.join(AUTOMATION_TRIGGERS)})")
        if action_kind not in AUTOMATION_ACTIONS:
            errors.append(f"invalid action: {action_kind!r} (expected {', '.join(AUTOMATION_ACTIONS)})")
    if action == "toggle" and not isinstance(payload.get("active"), bool):
        errors.append("toggle requires a boolean 'active' field")
    if errors:
        return {"errors": errors}

    if action == "create" and not rule_id:
        rule_id = "RULE-" + (_ui_key(payload.get("name")) or re.sub(r"[^0-9]", "", now)[:14])

    rule = None
    if action in {"create", "update"}:
        rule = {
            "id": rule_id,
            "name": str(payload.get("name") or rule_id),
            "description": str(payload.get("description") or ""),
            "trigger": trigger,
            "action": action_kind,
            "params": payload.get("params") if isinstance(payload.get("params"), dict) else {},
            "active": bool(payload.get("active", False)),
        }

    proposal = {
        "id": command_id.replace("COMMAND-", "AUTOREQ-"),
        "type": command_type,
        "action": action,
        "rule_id": rule_id,
        "target_file": f"agents/project/automation/rules/{rule_id}.json" if rule_id else "agents/project/automation/rules/",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "ui"),
        "rule": rule,
        "active": payload.get("active") if action == "toggle" else (rule["active"] if rule else None),
        "mutation_boundary": "proposal_only",
        "execution_boundary": "gate_chain",
        "executor": "scripts/automation_rules_gate.py",
        "next": "runtime executor applies this proposal to the declarative rule file; the gate chain executes active rules",
    }
    changed = _write_ui_proposal(root, "automation", proposal)
    return {
        "status": "queued",
        "result": {
            "changed": [changed],
            "proposal_id": proposal["id"],
            "action": action,
            "rule_id": rule_id,
            "mutation_boundary": "proposal_only",
            "execution_boundary": "gate_chain",
            "next": proposal["next"],
        },
    }


def _attachment_link_command(root: Path, target: str | None, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    """Propose linking an already-uploaded attachment to a task (proposal-only).

    The attachment id is normalized to a safe slug; the task id is validated. The
    console NEVER edits the task file -- it records a declarative proposal for a
    runtime executor to apply to the task frontmatter / evidence index.
    """
    attachment_id = re.sub(r"[^a-z0-9-]+", "", str(payload.get("attachment_id") or "").strip().lower())
    task_id = str(target or payload.get("task_id") or "").strip()
    errors: list[str] = []
    if not attachment_id:
        errors.append("attachment id is required")
    task_error = _validate_task_id(task_id)
    if task_error:
        errors.append(task_error)
    if errors:
        return {"errors": errors}

    proposal = {
        "id": command_id.replace("COMMAND-", "ATTACHREQ-"),
        "type": "attachment.link",
        "action": "link",
        "target_file": "agents/lead_engineer/tasks/",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "ui"),
        "attachment_id": attachment_id,
        "task_id": task_id,
        "evidence_ref": f"agents/project/evidence/attachments/{attachment_id}.json",
        "mutation_boundary": "proposal_only",
        "next": "runtime executor links this attachment evidence record to the task closeout",
    }
    changed = _write_ui_proposal(root, "attachments", proposal)
    return {
        "status": "queued",
        "result": {
            "changed": [changed],
            "proposal_id": proposal["id"],
            "action": "link",
            "attachment_id": attachment_id,
            "task_id": task_id,
            "mutation_boundary": "proposal_only",
            "next": proposal["next"],
        },
    }


# --- TASK-AR-335: cron-like repeat parsing -------------------------------------
# Bounds for each of the 5 cron fields (minute hour day-of-month month day-of-week).
_CRON_FIELD_BOUNDS = (
    (0, 59),  # minute
    (0, 23),  # hour
    (1, 31),  # day of month
    (1, 12),  # month
    (0, 6),  # day of week (0 = Sunday)
)
_CRON_FIELD_NAMES = ("minute", "hour", "day_of_month", "month", "day_of_week")


def _parse_cron_field(token: str, low: int, high: int) -> list[int] | str | None:
    """Parse one cron field. Returns sorted ints, "*" wildcard, or None on error.

    Supports ``*``, a plain integer, comma lists, and ``*/step`` (step over the
    full range). Deliberately small: no ranges/names so the local scheduler match
    stays trivial and proposal-only.
    """
    token = token.strip()
    if not token:
        return None
    if token == "*":
        return "*"
    if token.startswith("*/"):
        step_raw = token[2:]
        if not step_raw.isdigit() or int(step_raw) <= 0:
            return None
        step = int(step_raw)
        return [value for value in range(low, high + 1) if (value - low) % step == 0]
    values: list[int] = []
    for part in token.split(","):
        part = part.strip()
        if not part or not re.fullmatch(r"-?\d+", part):
            return None
        value = int(part)
        if value < low or value > high:
            return None
        values.append(value)
    return sorted(set(values))


def parse_cron(expression: Any) -> dict[str, Any]:
    """Validate + normalize a 5-field cron-like expression.

    Returns ``{"valid": bool, "expression": str, "fields": {...}, "errors": [...]}``.
    ``fields`` maps each field name to ``"*"`` or a sorted int list. This is a pure
    parser: it never schedules or dispatches anything.
    """
    raw = str(expression or "").strip()
    if not raw:
        return {"valid": False, "expression": raw, "fields": {}, "errors": ["cron expression is required"]}
    tokens = raw.split()
    if len(tokens) != 5:
        return {
            "valid": False,
            "expression": raw,
            "fields": {},
            "errors": [f"cron expression must have 5 fields (minute hour day-of-month month day-of-week); got {len(tokens)}"],
        }
    fields: dict[str, Any] = {}
    errors: list[str] = []
    for token, name, (low, high) in zip(tokens, _CRON_FIELD_NAMES, _CRON_FIELD_BOUNDS):
        parsed = _parse_cron_field(token, low, high)
        if parsed is None:
            errors.append(f"invalid {name} field: {token!r} (expected *, int {low}-{high}, comma list, or */step)")
        else:
            fields[name] = parsed
    if errors:
        return {"valid": False, "expression": raw, "fields": {}, "errors": errors}
    return {"valid": True, "expression": " ".join(tokens), "fields": fields, "errors": []}


def _schedule_command(root: Path, command_type: str, target: str | None, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    """Reserve / repeat a taskset dispatch -- PROPOSAL ONLY (TASK-AR-335).

    The console NEVER executes ``taskset_dispatcher`` and NEVER writes the SSoT.
    It records a declarative schedule proposal under ``.ui_outbox/schedules`` that
    a runtime executor applies to ``agents/project/schedules/<id>.json``; the LOCAL
    ``scripts/scheduled_dispatch_gate.py`` is the single point that reads due
    schedules and emits dispatch + reminder events. No external services.
    """
    action = command_type.split(".", 1)[1]
    schedule_id = _ui_key(target or payload.get("id") or payload.get("schedule_id"))

    if action == "cancel":
        if not schedule_id:
            return {"errors": ["schedule id is required to cancel"]}
        proposal = {
            "id": command_id.replace("COMMAND-", "SCHEDREQ-"),
            "type": command_type,
            "action": "cancel",
            "schedule_id": schedule_id,
            "target_file": f"agents/project/schedules/{schedule_id}.json",
            "status": "queued",
            "created_at": now,
            "requested_by": str(payload.get("actor") or "ui"),
            "schedule": None,
            "mutation_boundary": "proposal_only",
            "execution_boundary": "local_scheduler",
            "executor": "scripts/scheduled_dispatch_gate.py",
            "next": "runtime executor removes/deactivates the declarative schedule file; no dispatch is run by the console",
        }
        changed = _write_ui_proposal(root, "schedules", proposal)
        return {
            "status": "queued",
            "result": {
                "changed": [changed],
                "proposal_id": proposal["id"],
                "action": "cancel",
                "schedule_id": schedule_id,
                "mutation_boundary": "proposal_only",
                "execution_boundary": "local_scheduler",
                "next": proposal["next"],
            },
        }

    # create
    taskset_id = str(payload.get("taskset_id") or payload.get("task_set_id") or "").strip()
    mode = str(payload.get("mode") or "").strip().lower()
    errors: list[str] = []
    if not taskset_id:
        errors.append("taskset_id is required")
    if mode not in SCHEDULE_MODES:
        errors.append(f"invalid mode: {mode!r} (expected {', '.join(SCHEDULE_MODES)})")

    run_at = str(payload.get("run_at") or payload.get("at") or "").strip()
    cron_spec: dict[str, Any] | None = None
    if mode == "reserve":
        if not run_at:
            errors.append("reserve mode requires a run_at timestamp")
        elif _parse_scalar(run_at) is None and not re.match(r"^\d{4}-\d{2}-\d{2}", run_at):
            errors.append(f"invalid run_at timestamp: {run_at!r}")
    elif mode == "repeat":
        cron_spec = parse_cron(payload.get("cron") or payload.get("repeat"))
        if not cron_spec["valid"]:
            errors.extend(cron_spec["errors"])

    if errors:
        return {"errors": errors}

    if not schedule_id:
        schedule_id = "SCHED-" + (_ui_key(taskset_id) or re.sub(r"[^0-9]", "", now)[:14])

    schedule = {
        "id": schedule_id,
        "name": str(payload.get("name") or schedule_id),
        "taskset_id": taskset_id,
        "mode": mode,
        "run_at": run_at if mode == "reserve" else None,
        "cron": cron_spec["expression"] if (mode == "repeat" and cron_spec) else None,
        "cron_fields": cron_spec["fields"] if (mode == "repeat" and cron_spec) else None,
        "actor": str(payload.get("actor") or "ui"),
        "note": str(payload.get("note") or ""),
        "active": bool(payload.get("active", True)),
        "created_at": now,
    }
    proposal = {
        "id": command_id.replace("COMMAND-", "SCHEDREQ-"),
        "type": command_type,
        "action": "create",
        "schedule_id": schedule_id,
        "target_file": f"agents/project/schedules/{schedule_id}.json",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "ui"),
        "schedule": schedule,
        "mutation_boundary": "proposal_only",
        "execution_boundary": "local_scheduler",
        "executor": "scripts/scheduled_dispatch_gate.py",
        "next": "runtime executor applies this proposal to agents/project/schedules/<id>.json; the local scheduler dispatches when due (no external services)",
    }
    changed = _write_ui_proposal(root, "schedules", proposal)
    return {
        "status": "queued",
        "result": {
            "changed": [changed],
            "proposal_id": proposal["id"],
            "action": "create",
            "schedule_id": schedule_id,
            "mode": mode,
            "mutation_boundary": "proposal_only",
            "execution_boundary": "local_scheduler",
            "next": proposal["next"],
        },
    }


def _assignment_set_command(root: Path, target: str | None, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    """Propose changing a task's team/role/assignee (proposal-only, TASK-AR-337).

    The team/role/assignee are normalized to safe slugs; the task id is
    validated. At least one of team/role/assignee must be supplied. The console
    NEVER edits the task file -- it records a declarative proposal for a runtime
    executor to apply to the task frontmatter, keeping the assignment-change on
    the command path (no direct task-file writes from the UI).
    """
    task_id = str(target or payload.get("task_id") or "").strip()
    errors: list[str] = []
    task_error = _validate_task_id(task_id)
    if task_error:
        errors.append(task_error)

    def _slug_field(value: Any) -> str | None:
        slug = re.sub(r"[^a-z0-9-]+", "-", str(value or "").strip().lower()).strip("-")
        return slug or None

    assignment: dict[str, Any] = {}
    if "team" in payload:
        assignment["team"] = _slug_field(payload.get("team"))
    if "role" in payload:
        assignment["role"] = _slug_field(payload.get("role"))
    if "assignee" in payload:
        assignment["assignee"] = _slug_field(payload.get("assignee"))
    if not assignment:
        errors.append("assignment requires at least one of team/role/assignee")
    if errors:
        return {"errors": errors}

    proposal = {
        "id": command_id.replace("COMMAND-", "ASSIGNREQ-"),
        "type": "assignment.set",
        "action": "set",
        "target_file": "agents/lead_engineer/tasks/",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "ui"),
        "task_id": task_id,
        "assignment": assignment,
        "mutation_boundary": "proposal_only",
        "next": "runtime executor applies this team/role/assignee change to the task frontmatter",
    }
    changed = _write_ui_proposal(root, "assignments", proposal)
    return {
        "status": "queued",
        "result": {
            "changed": [changed],
            "proposal_id": proposal["id"],
            "action": "set",
            "task_id": task_id,
            "assignment": assignment,
            "mutation_boundary": "proposal_only",
            "next": proposal["next"],
        },
    }


# ----- TASK-AR-338: @mentions, message pin/reaction, notification prefs --------


def _mention_target(value: Any) -> str | None:
    """Normalize an @mention target (agent id / role / owner) to a safe slug."""
    target = str(value or "").strip().lstrip("@").lower()
    target = re.sub(r"[^a-z0-9_.-]+", "", target).strip(".")
    return target or None


def _mention_notify_command(root: Path, target: str | None, payload: dict[str, Any], now: str) -> dict[str, Any]:
    """An @mention -> a runtime message proposal to the mentioned target.

    PROPOSAL-ONLY: this reuses the established runtime message-queue path (writes
    a queued message under agents/messages/inbox so the mentioned agent/role/
    Owner receives a runtime message); the notification center then surfaces the
    mention from that message body. The console NEVER calls an agent directly.
    """
    mention_target = _mention_target(target or payload.get("target") or payload.get("to") or payload.get("agent"))
    errors = _payload_errors(payload)
    if not mention_target:
        errors.append("mention target is required")
    text = str(payload.get("message") or payload.get("instruction") or payload.get("comment") or "").strip()
    if not text:
        errors.append("mention message is required")
    if errors:
        return {"errors": errors}

    # Carry the @mention in the body so the inbox aggregates it on the next scan.
    body_text = text if f"@{mention_target}" in text.lower() else f"@{mention_target} {text}"
    queue_payload = dict(payload)
    queue_payload["instruction"] = body_text
    outcome = _queue_runtime_message(root, "mention.notify", mention_target, queue_payload, now)
    if "errors" in outcome:
        return outcome
    result = dict(outcome.get("result") or {})
    result.update(
        {
            "mention_target": mention_target,
            "runtime_support": "message_queue",
            "mutation_boundary": "proposal_only",
            "next": "the mentioned target receives a runtime message; the inbox surfaces the mention",
        }
    )
    return {"status": str(outcome.get("status") or "queued"), "result": result}


def _message_id_arg(value: Any) -> str | None:
    """Validate a message id reference (alnum + ._- only)."""
    message_id = str(value or "").strip()
    if not message_id or not re.fullmatch(r"[A-Za-z0-9_.:-]+", message_id):
        return None
    return message_id


def _message_command(root: Path, command_type: str, target: str | None, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    """Pin or react to a channel message -- PROPOSAL ONLY (TASK-AR-338).

    Records a declarative proposal under .ui_outbox/messages for a runtime
    executor to apply to the canonical message record (pin flag / reaction list).
    The console NEVER edits the message file.
    """
    action = command_type.split(".", 1)[1]
    message_id = _message_id_arg(target or payload.get("message_id") or payload.get("id"))
    errors = _payload_errors(payload)
    if not message_id:
        errors.append("a valid message id is required")
    reaction: str | None = None
    if action == "react":
        reaction = str(payload.get("reaction") or payload.get("emoji") or "").strip().lower()
        if reaction not in MESSAGE_REACTIONS:
            errors.append(f"invalid reaction: {reaction!r} (expected {', '.join(MESSAGE_REACTIONS)})")
    pinned = bool(payload.get("pinned", True)) if action == "pin" else None
    if errors:
        return {"errors": errors}

    proposal = {
        "id": command_id.replace("COMMAND-", "MSGREQ-"),
        "type": command_type,
        "action": action,
        "target_file": "agents/messages/",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "ui"),
        "message_id": message_id,
        "pinned": pinned,
        "reaction": reaction,
        "mutation_boundary": "proposal_only",
        "next": "runtime executor applies this pin/reaction to the canonical message record",
    }
    changed = _write_ui_proposal(root, "messages", proposal)
    return {
        "status": "queued",
        "result": {
            "changed": [changed],
            "proposal_id": proposal["id"],
            "action": action,
            "message_id": message_id,
            "reaction": reaction,
            "pinned": pinned,
            "mutation_boundary": "proposal_only",
            "next": proposal["next"],
        },
    }


def _notification_command(root: Path, command_type: str, target: str | None, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    """Mark-read / mute / subscribe for the notification inbox -- PROPOSAL ONLY.

    Records a declarative preferences proposal under .ui_outbox/notifications
    that a runtime executor applies to agents/project/ui/notifications.json. The
    console NEVER writes that canonical config file directly.
    """
    action = command_type.split(".", 1)[1]
    errors = _payload_errors(payload)
    preference: dict[str, Any] = {"action": action}

    if action == "read":
        notification_id = str(target or payload.get("notification_id") or payload.get("id") or "").strip()
        if not notification_id and not payload.get("all"):
            errors.append("notification id is required to mark read (or set all=true)")
        preference["notification_id"] = notification_id or None
        preference["all"] = bool(payload.get("all", False))
    elif action == "mute":
        mute_id = str(target or payload.get("notification_id") or payload.get("id") or payload.get("entity_id") or "").strip()
        keyword = str(payload.get("keyword") or "").strip()
        if not mute_id and not keyword:
            errors.append("mute requires a notification/entity id or a keyword")
        preference["mute_id"] = mute_id or None
        preference["keyword"] = keyword or None
    elif action == "subscribe":
        def _axis(value: Any, allowed: tuple[str, ...]) -> list[str]:
            raw = value if isinstance(value, list) else ([value] if value else [])
            return [str(item).strip().lower() for item in raw if str(item).strip().lower() in allowed]

        tasksets = payload.get("tasksets") if isinstance(payload.get("tasksets"), list) else (
            [payload.get("taskset_id")] if payload.get("taskset_id") else []
        )
        preference["kinds"] = _axis(payload.get("kinds") or payload.get("kind"), NOTIFICATION_KINDS)
        preference["severities"] = _axis(payload.get("severities") or payload.get("severity"), NOTIFICATION_SEVERITIES)
        preference["tasksets"] = [str(item).strip() for item in tasksets if str(item).strip()]
        if not (preference["kinds"] or preference["severities"] or preference["tasksets"]):
            errors.append("subscribe requires at least one of kinds/severities/tasksets")
    if errors:
        return {"errors": errors}

    proposal = {
        "id": command_id.replace("COMMAND-", "NOTIFREQ-"),
        "type": command_type,
        "action": action,
        "target_file": "agents/project/ui/notifications.json",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "ui"),
        "preference": preference,
        "mutation_boundary": "proposal_only",
        "next": "runtime executor applies this preference to agents/project/ui/notifications.json",
    }
    changed = _write_ui_proposal(root, "notifications", proposal)
    return {
        "status": "queued",
        "result": {
            "changed": [changed],
            "proposal_id": proposal["id"],
            "action": action,
            "preference": preference,
            "mutation_boundary": "proposal_only",
            "next": proposal["next"],
        },
    }


def _subscription_command(root: Path, command_type: str, target: str | None, payload: dict[str, Any], now: str, command_id: str) -> dict[str, Any]:
    """Propose a per-channel notification subscription-rule edit (proposal-only).

    TASK-AR-365. The console NEVER writes the LOCAL notifications config and NEVER
    sends to any external service -- it records a declarative proposal under
    .ui_outbox/notifications that a runtime executor applies to the gitignored
    local config. SECRETS (webhook URLs / tokens / SMTP creds) are REJECTED if
    present on the payload: the owner fills those directly into the local config,
    never through the UI/command path.
    """
    action = command_type.split(".", 1)[1]
    channel = re.sub(r"[^a-z0-9_-]+", "-", str(target or payload.get("channel") or payload.get("name") or "").strip().lower()).strip("-")
    errors: list[str] = []

    leaked = sorted(SUBSCRIPTION_SECRET_KEYS.intersection(payload))
    if leaked:
        errors.append(f"secret values are not allowed on subscription proposals: {', '.join(leaked)} (put secrets in the local config only)")
    if not channel:
        errors.append("channel name is required")

    kind = str(payload.get("kind") or "").strip().lower()
    if action in {"create", "update"} and kind not in NOTIFICATION_CHANNEL_KINDS:
        errors.append(f"invalid channel kind: {kind!r} (expected {', '.join(NOTIFICATION_CHANNEL_KINDS)})")

    raw_severities = payload.get("severities")
    severities: list[str] = []
    if isinstance(raw_severities, list):
        for value in raw_severities:
            sev = str(value or "").strip().lower()
            if sev and sev not in NOTIFICATION_ROUTING_MODES:
                errors.append(f"invalid severity: {sev!r} (expected {', '.join(NOTIFICATION_ROUTING_MODES)})")
            elif sev and sev not in severities:
                severities.append(sev)
    if action in {"create", "update"} and not severities:
        severities = list(NOTIFICATION_ROUTING_MODES)

    aggregate_minutes = payload.get("aggregate_minutes")
    if aggregate_minutes is not None:
        try:
            aggregate_minutes = int(aggregate_minutes)
        except (TypeError, ValueError):
            errors.append("aggregate_minutes must be an integer")
            aggregate_minutes = None
        else:
            if aggregate_minutes not in NOTIFICATION_AGGREGATE_WINDOWS:
                errors.append(f"invalid aggregate_minutes: {aggregate_minutes!r} (expected one of {', '.join(str(value) for value in NOTIFICATION_AGGREGATE_WINDOWS)})")
    if action == "toggle" and not isinstance(payload.get("enabled"), bool):
        errors.append("toggle requires a boolean 'enabled' field")
    if errors:
        return {"errors": errors}

    rule = None
    if action in {"create", "update"}:
        rule = {
            "name": channel,
            "kind": kind,
            "enabled": bool(payload.get("enabled", False)),
            "severities": severities,
            "aggregate_minutes": aggregate_minutes if aggregate_minutes in NOTIFICATION_AGGREGATE_WINDOWS else 5,
        }

    proposal = {
        "id": command_id.replace("COMMAND-", "SUBREQ-"),
        "type": command_type,
        "action": action,
        "target_file": "agents/project/notifications.local.json",
        "status": "queued",
        "created_at": now,
        "requested_by": str(payload.get("actor") or "ui"),
        "channel": channel,
        "rule": rule,
        "enabled": payload.get("enabled") if action == "toggle" else (rule["enabled"] if rule else None),
        "mutation_boundary": "proposal_only",
        "secrets_boundary": "local_config_only",
        "dispatch_boundary": "opt_in_local_runner",
        "next": "runtime executor applies this subscription rule to the LOCAL gitignored notifications config; secrets are authored by the owner directly, never via the UI; an opt-in local runner performs the actual dispatch",
    }
    changed = _write_ui_proposal(root, "notifications", proposal)
    return {
        "status": "queued",
        "result": {
            "changed": [changed],
            "proposal_id": proposal["id"],
            "action": action,
            "channel": channel,
            "mutation_boundary": "proposal_only",
            "secrets_boundary": "local_config_only",
            "dispatch_boundary": "opt_in_local_runner",
            "next": proposal["next"],
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
    elif command_type == "task.move":
        outcome = _move_task(root_path, target_str, payload)
    elif command_type == "task.bulk_edit":
        outcome = _bulk_edit_tasks(root_path, payload)
    elif command_type in {"taskset.create", "taskset.rename", "taskset.archive"}:
        outcome = _taskset_lifecycle_command(root_path, command_type, target_str, payload, created_at, cid)
    elif command_type == "taskset.template":
        outcome = _taskset_template_command(root_path, payload, created_at, cid)
    elif command_type == "task.comment":
        outcome = _comment_task(root_path, target_str, payload, created_at)
    elif command_type == "planning.scan":
        outcome = _planning_scan_command(root_path, payload, created_at, cid)
    elif command_type in {"planning.approve", "planning.reject"}:
        outcome = _planning_decision_command(root_path, command_type, payload, created_at, cid)
    elif command_type in MEETING_COMMAND_TYPES:
        outcome = _meeting_command(root_path, command_type, target_str, payload, created_at, cid)
    elif command_type in DECISION_COMMAND_TYPES:
        outcome = _decision_command(root_path, command_type, target_str, payload, created_at, cid)
    elif command_type in PROPERTY_COMMAND_TYPES:
        outcome = _property_command(root_path, command_type, target_str, payload, created_at, cid)
    elif command_type in LABEL_COMMAND_TYPES:
        outcome = _label_command(root_path, command_type, target_str, payload, created_at, cid)
    elif command_type in AUTOMATION_COMMAND_TYPES:
        outcome = _automation_command(root_path, command_type, target_str, payload, created_at, cid)
    elif command_type in ATTACHMENT_COMMAND_TYPES:
        outcome = _attachment_link_command(root_path, target_str, payload, created_at, cid)
    elif command_type in SCHEDULE_COMMAND_TYPES:
        outcome = _schedule_command(root_path, command_type, target_str, payload, created_at, cid)
    elif command_type in ASSIGNMENT_COMMAND_TYPES:
        outcome = _assignment_set_command(root_path, target_str, payload, created_at, cid)
    elif command_type in MENTION_COMMAND_TYPES:
        outcome = _mention_notify_command(root_path, target_str, payload, created_at)
    elif command_type in MESSAGE_COMMAND_TYPES:
        outcome = _message_command(root_path, command_type, target_str, payload, created_at, cid)
    elif command_type in NOTIFICATION_COMMAND_TYPES:
        outcome = _notification_command(root_path, command_type, target_str, payload, created_at, cid)
    elif command_type in SUBSCRIPTION_COMMAND_TYPES:
        outcome = _subscription_command(root_path, command_type, target_str, payload, created_at, cid)
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
