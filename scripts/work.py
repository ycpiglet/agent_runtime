"""Deterministic Work Item registration CLI.

This is the scaffolded, non-LLM path for planner-approved work intake. It
creates stable records first; generated views such as hierarchy numbers and the
backlog board are refreshed afterward.

Lifecycle defaults (W0~W6, TASK-AR-506):
- ``new``/``register`` automatically records the taskset's plan-assumption
  snapshot (T0) via ``plan_assumption_gate``; ``--no-plan-snapshot`` opts out.
  The matching T2 drift check runs in ``task_claim_dispatcher.py create``.
- ``status`` is the W0 session-start visibility surface: active claims,
  git worktrees, and unmerged agent-branch divergence in one read-only view.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import backlog_board
import evidence_index_generator
import inflight_overlay
import now as now_util
import plan_assumption_gate
import task_identity
import work_item_classifier


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_SCHEMA = "agent-runtime-work-registration/v1"
WORK_ITEM_SCHEMA = "agent-runtime-work-item/v1"
TASKSET_REGISTRY_SCHEMA = "agent-runtime-taskset-definitions/v1"
TASKSET_REGISTRY_PATH = Path("agents/project/work-items/TASKSET-DEFINITIONS.json")
TASKS_DIR = Path("agents/lead_engineer/tasks")
UNITS_DIR = Path("agents/lead_engineer/tasks/units")
INITIATIVES_DIR = Path("agents/project/initiatives")
PLANS_DIR = Path("docs/superpowers/plans")
REVIEWS_DIR = Path("reviews")
OWNER_DOCS_PATH = Path("owner-docs.yml")
RESERVATION_TTL_SECONDS = 86400
TASK_DISPLAY_RE = re.compile(r"^TASK-AR-\d+$")
UNIT_DISPLAY_RE = re.compile(r"^UNIT-(TASK-AR-\d+)-\d{3}$")
UNIT_REQUIRED_FIELDS = {
    "title",
    "context",
    "inputs",
    "target_files",
    "scope",
    "steps",
    "acceptance",
    "verification",
    "handoff",
    "stop_condition",
}
RESOLUTION_VALUES = {"done", "wontfix", "duplicate", "superseded", "moved_to_vault"}
CLOSEOUT_START = "<!-- work-close:start -->"
CLOSEOUT_END = "<!-- work-close:end -->"
PLANNING_OUTBOX_DIR = Path("agents/planning/outbox")
PLANNING_DRAFTS_DIR = Path("agents/planning/drafts")
ACTIVE_CLAIM_STATUSES = {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}
ASSIGNMENT_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    (
        "agent-runtime-core",
        "lead-engineer",
        (
            "scripts/",
            "scripts\\",
            "src/agent_runtime",
            "src\\agent_runtime",
            "tests/",
            "tests\\",
            "runtime",
            "cli",
            "gate",
        ),
    ),
    (
        "risk-and-safety",
        "drift-guard",
        ("risk", "security", "approval", "sandbox", "budget", "secret", "external effect"),
    ),
    (
        "release-integrity",
        "version-steward",
        ("release", "version", "tag", "changelog", "compatibility", "migration"),
    ),
    (
        "evaluation-office",
        "trace-analyst",
        ("evidence", "verify", "verification", "eval", "trace", "grader", "regression"),
    ),
    (
        "planning-office",
        "planning-coordinator",
        ("planning", "proposal", "split", "criteria", "assign", "work item", "backlog", "taskset", "initiative"),
    ),
]
WORK_ITEM_PATH_PATTERNS = (
    INITIATIVES_DIR / "*.md",
    PLANS_DIR / "*.md",
    TASKS_DIR / "TASK-*.md",
    UNITS_DIR / "**" / "*.md",
)
STATS_NUMERIC_METRICS = {
    "actual_tokens",
    "actual_hours",
    "est_tokens",
    "est_hours",
    "est_cost",
    "actual_cost",
    "budget_cap",
    "rework_count",
    "gate_failure_count",
    "reopened_count",
}
STATS_COMPUTED_METRICS = {"lead_time", "age"}
STATS_METRICS = {"count"} | STATS_NUMERIC_METRICS | STATS_COMPUTED_METRICS
# WORK-SCHEMA.yml computed_only_fields: storing these in work-item frontmatter
# is a schema violation, so stats must never read them from records.
STATS_COMPUTED_ONLY_FIELDS = {
    "progress_pct",
    "age",
    "lead_time",
    "est_actual_delta",
    "variance",
    "rollup_progress_pct",
}
# Stable group-by dimensions (stored, non-derived fields from WORK-SCHEMA.yml).
STATS_DIMENSIONS = {
    "kind",
    "status",
    "resolution",
    "verification_status",
    "owner",
    "team",
    "created_by",
    "created_by_instance",
    "last_actor_instance",
    "closed_by",
    "verified_by",
    "origin_type",
    "priority",
    "difficulty",
    "risk_tier",
    "horizon",
    "area",
    "component",
    "project_id",
    "initiative_id",
    "task_set_id",
    "task_id",
    "unit_id",
    "parent_id",
    "model_tier",
    "planner_model_tier",
    "worker_model_tier",
    "reviewer_model_tier",
}
STATS_ROW_AGGREGATES = ("value_count", "sum", "avg", "min", "max")
STATS_EXPORT_FORMATS = {"json", "csv"}
STATS_EXPORT_SCHEMA = "agent-runtime-work-stats-export/v1"
STATS_EXPORT_TEXT_FIELDS = (
    "work_id",
    "work_uid",
    "display_id",
    "kind",
    "status",
    "resolution",
    "verification_status",
    "title",
    "owner",
    "team",
    "origin_type",
    "origin_ref",
    "created_by",
    "created_by_instance",
    "last_actor_instance",
    "closed_by",
    "verified_by",
    "priority",
    "difficulty",
    "risk_tier",
    "horizon",
    "area",
    "component",
    "project_id",
    "initiative_id",
    "task_set_id",
    "task_id",
    "unit_id",
    "parent_id",
    "model_tier",
    "planner_model_tier",
    "worker_model_tier",
    "reviewer_model_tier",
    "created_at",
    "registered_at",
    "started_at",
    "updated_at",
    "completed_at",
    "verified_at",
    "due_date",
)
STATS_EXPORT_NUMERIC_FIELDS = (
    "est_tokens",
    "actual_tokens",
    "est_hours",
    "actual_hours",
    "est_cost",
    "actual_cost",
    "budget_cap",
    "rework_count",
    "gate_failure_count",
    "reopened_count",
)
STATS_EXPORT_COLUMNS = (
    *STATS_EXPORT_TEXT_FIELDS,
    "tags",
    *STATS_EXPORT_NUMERIC_FIELDS,
    "lead_time_hours",
    "age_hours",
    "path",
)
# Stored fields --filter/--where may match without an unknown-key warning.
# Unknown keys still match nothing (zero results) but warn on stderr so a
# typo does not silently look like an empty result set.
STATS_FILTERABLE_FIELDS = (
    STATS_DIMENSIONS | set(STATS_EXPORT_TEXT_FIELDS) | set(STATS_EXPORT_NUMERIC_FIELDS) | {"tags"}
)
WORK_VIEWS_SCHEMA = "agent-runtime-work-views/v1"
WORK_VIEWS_PATH = Path("agents/project/work-items/WORK-VIEWS.json")
VIEW_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
MISSING_GROUP_VALUE = "(none)"
# T0 default anchors: the registration/dispatch flow itself. If these scripts
# change between registration (T0) and dispatch (T2), the plan was made
# against a different flow and must be revalidated before claiming.
PLAN_SNAPSHOT_DEFAULT_ANCHORS = (
    "scripts/work.py",
    "scripts/task_claim_dispatcher.py",
)


class WorkRegistrationError(RuntimeError):
    def __init__(self, findings: list[str]):
        super().__init__("work registration failed")
        self.findings = findings


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _now_text(value: str | None) -> str:
    if value:
        return value
    return now_util.local_iso()


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower())
    return re.sub(r"-+", "-", text).strip("-") or "work"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkRegistrationError([f"{path.as_posix()}: invalid-json:{exc}"])
    if not isinstance(payload, dict):
        raise WorkRegistrationError([f"{path.as_posix()}: invalid-json-root"])
    return payload


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, payload: Any) -> str:
    return f"{prefix}-{_stable_hash(payload)[:12].upper()}"


def _as_dict(value: Any, name: str, findings: list[str]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    findings.append(f"input:{name}:missing-or-invalid")
    return {}


def _as_tasks(value: Any, findings: list[str]) -> list[dict[str, Any]]:
    if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
        return list(value)
    findings.append("input:tasks:missing-or-invalid")
    return []


def _require_text(record: dict[str, Any], field: str, prefix: str, findings: list[str]) -> str:
    value = str(record.get(field) or "").strip()
    if not value:
        findings.append(f"input:{prefix}:missing:{field}")
    return value


def _list_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _text_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [line.strip() for line in value.splitlines() if line.strip()]
    return []


def _section_blocks(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = re.match(r"^##+\s+(.+?)\s*$", line)
        if match:
            current = re.sub(r"\s+", " ", match.group(1).strip()).lower()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def _clean_bullet_line(line: str) -> str:
    text = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line).strip()
    if text.startswith("`") and text.endswith("`") and len(text) > 1:
        text = text[1:-1].strip()
    return text


def _section_list(body: str, *names: str) -> list[str]:
    sections = _section_blocks(body)
    for name in names:
        text = sections.get(name.lower(), "")
        if text:
            return [line for line in (_clean_bullet_line(raw) for raw in text.splitlines()) if line]
    return []


def _has_text_value(value: Any) -> bool:
    return bool(_text_lines(value))


_FRONTMATTER_LINE_BOUNDARIES = "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029"


def _frontmatter_scalar(value: Any) -> str:
    text = str(value)
    splitline_boundary = any(separator in text for separator in _FRONTMATTER_LINE_BOUNDARIES)
    unsafe = (
        "#" in text
        or splitline_boundary
        or text != text.strip()
        or (text.startswith("[") and text.endswith("]"))
        or text.startswith(("'", '"'))
        or text.endswith(("'", '"'))
    )
    if not unsafe:
        return text
    return json.dumps(
        backlog_board.ENCODED_WORK_SCALAR_PREFIX + text,
        ensure_ascii=True,
    )


def _frontmatter(meta: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {_frontmatter_scalar(item)}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif value is not None and str(value) != "":
            lines.append(f"{key}: {_frontmatter_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def _rewrite_frontmatter(path: Path, meta: dict[str, Any], body: str) -> None:
    path.write_text(_frontmatter(meta) + "\n\n" + body.lstrip("\n"), encoding="utf-8")


def _title_from_task(task: dict[str, Any], display_id: str) -> str:
    return str(task.get("title") or display_id).strip()


def _task_path(root: Path, display_id: str) -> Path:
    return root / TASKS_DIR / f"{display_id}.md"


def _unit_path(root: Path, task_id: str, unit_id: str) -> Path:
    return root / UNITS_DIR / task_id / f"{unit_id}.md"


def _unit_rel_path(task_id: str, unit_id: str) -> str:
    return (UNITS_DIR / task_id / f"{unit_id}.md").as_posix()


def _initiative_path(root: Path, initiative_id: str) -> Path:
    return root / INITIATIVES_DIR / f"{initiative_id}.md"


def _plan_path(root: Path, now_text: str, taskset: dict[str, Any]) -> Path:
    plan_slug = str(taskset.get("plan_slug") or "").strip()
    if not plan_slug:
        date_part = _parse_datetime(now_text).date().isoformat()
        plan_slug = f"{date_part}-{_slug(str(taskset.get('id') or taskset.get('display_name') or 'taskset'))}"
    if not plan_slug.endswith(".md"):
        plan_slug += ".md"
    return root / PLANS_DIR / plan_slug


def _review_path(root: Path, now_text: str, taskset: dict[str, Any]) -> Path:
    raw = str(taskset.get("review_path") or "").strip()
    if raw:
        return root / raw
    date_part = _parse_datetime(now_text).date().isoformat()
    slug = _slug(str(taskset.get("id") or taskset.get("display_name") or "work-registration"))
    return root / REVIEWS_DIR / f"REVIEW-{date_part}-{slug}-registration.md"


def _render_initiative(now_text: str, payload: dict[str, Any], initiative: dict[str, Any]) -> str:
    initiative_id = str(initiative["id"])
    meta = {
        "schema_version": WORK_ITEM_SCHEMA,
        "work_id": initiative_id,
        "work_uid": initiative.get("work_uid") or str(uuid.uuid4()),
        "kind": "initiative",
        "id": initiative_id,
        "status": initiative.get("status", "active"),
        "owner": initiative["owner"],
        "created_at": now_text,
        "updated_at": now_text,
        "origin_type": payload["origin_type"],
        "origin_ref": payload["origin_ref"],
        "created_by": payload["created_by"],
        "summary": initiative["summary"],
    }
    return (
        _frontmatter(meta)
        + "\n\n"
        + f"# {initiative['title']}\n\n"
        + "## Goal\n\n"
        + f"- {initiative['summary']}\n"
    )


def _render_plan(
    *,
    now_text: str,
    payload: dict[str, Any],
    initiative: dict[str, Any],
    taskset: dict[str, Any],
    tasks: list[dict[str, Any]],
) -> str:
    taskset_id = str(taskset["id"])
    meta = {
        "schema_version": WORK_ITEM_SCHEMA,
        "work_id": taskset_id,
        "work_uid": taskset.get("work_uid") or str(uuid.uuid4()),
        "kind": "taskset",
        "id": taskset_id,
        "parent_id": initiative["id"],
        "initiative_id": initiative["id"],
        "status": taskset.get("status", "active"),
        "owner": taskset.get("owner", initiative["owner"]),
        "created_at": now_text,
        "updated_at": now_text,
        "origin_type": payload["origin_type"],
        "origin_ref": payload["origin_ref"],
        "created_by": payload["created_by"],
        "summary": taskset["summary"],
    }
    lines = [
        _frontmatter(meta),
        "",
        f"# {taskset['display_name']}",
        "",
        "## Goal",
        "",
        f"- {taskset['summary']}",
        "",
        "## Tasks",
        "",
        "| Task | Title |",
        "| --- | --- |",
    ]
    for task in tasks:
        lines.append(f"| `{task['display_id']}` | {task['title']} |")
    unit_rows = [
        f"| `{unit['unit_id']}` | `{task['display_id']}` | {unit['title']} |"
        for task in tasks
        for unit in _units_for(task)
    ]
    if unit_rows:
        lines.extend(
            [
                "",
                "## Unit Specs",
                "",
                "| Unit | Task | Title |",
                "| --- | --- | --- |",
                *unit_rows,
            ]
        )
    lines.extend(
        [
            "",
            "## Verification",
            "",
            "- `python scripts/task_identity.py check --check`",
            "- `python scripts/work_item_classifier.py --check`",
            "- `python scripts/taskset_work_gate.py --check`",
            "",
        ]
    )
    return "\n".join(lines)


def _render_task(
    *,
    now_text: str,
    payload: dict[str, Any],
    initiative: dict[str, Any],
    taskset: dict[str, Any],
    task: dict[str, Any],
    task_uid: str,
    reservation_id: str,
) -> str:
    display_id = str(task["display_id"])
    tags = _list_value(task.get("tags")) or ["work-cli-created"]
    meta = {
        "schema_version": WORK_ITEM_SCHEMA,
        "id": display_id,
        "display_id": display_id,
        "task_uid": task_uid,
        "work_id": display_id,
        "work_uid": task_uid,
        "kind": "task",
        "parent_id": taskset["id"],
        "registered_at": now_text,
        "created_at": now_text,
        "updated_at": now_text,
        "title": task["title"],
        "status": task.get("status", "planned"),
        "priority": task.get("priority", "P1"),
        "difficulty": task.get("difficulty", "M"),
        "est_hours": task.get("est_hours", 1),
        "est_tokens": task.get("est_tokens", 1000),
        "owner": task.get("owner", taskset.get("owner", initiative["owner"])),
        "team": task.get("team", ""),
        "initiative_id": initiative["id"],
        "project_id": payload.get("project_id", "PROJECT-AGENT-RUNTIME-PM-OS"),
        "task_set_id": taskset["id"],
        "unit_spec": task.get("unit_spec", ""),
        "reservation_id": reservation_id,
        "origin_type": payload["origin_type"],
        "origin_ref": payload["origin_ref"],
        "created_by": payload["created_by"],
        "summary": task.get("summary", task["goal"]),
        "planner_model_tier": task.get("planner_model_tier", taskset.get("planner_model_tier", "planner_high")),
        "worker_model_tier": task.get("worker_model_tier", taskset.get("worker_model_tier", "worker_standard")),
        "reviewer_model_tier": task.get("reviewer_model_tier", taskset.get("reviewer_model_tier", "reviewer_standard")),
        "tags": tags,
    }
    return (
        _frontmatter(meta)
        + "\n\n"
        + f"# {display_id} - {task['title']}\n\n"
        + "## Goal\n\n"
        + f"- {task['goal']}\n\n"
        + "## Scope\n\n"
        + f"- {task.get('scope', task['goal'])}\n\n"
        + "## Acceptance Criteria\n\n"
        + "\n".join(f"- {item}" for item in _list_value(task.get("acceptance")) or [task["goal"]])
        + "\n\n"
        + "## Verification\n\n"
        + "\n".join(f"- `{item}`" for item in _list_value(task.get("verification")) or ["python scripts/task_identity.py check --check"])
        + "\n"
    )


def _render_unit(
    *,
    now_text: str,
    payload: dict[str, Any],
    initiative: dict[str, Any],
    taskset: dict[str, Any],
    task: dict[str, Any],
    unit: dict[str, Any],
    unit_uid: str,
) -> str:
    task_id = str(task["display_id"])
    unit_id = str(unit["unit_id"])
    owner = unit.get("owner", task.get("owner", taskset.get("owner", initiative["owner"])))
    model_tier = unit.get("model_tier", task.get("worker_model_tier", taskset.get("worker_model_tier", "worker_standard")))
    status = unit.get("status", "worker_ready")
    meta = {
        "schema_version": WORK_ITEM_SCHEMA,
        "work_id": unit_id,
        "work_uid": unit_uid,
        "kind": "unit",
        "parent_id": task_id,
        "unit_id": unit_id,
        "task_id": task_id,
        "task_set_id": taskset["id"],
        "initiative_id": initiative["id"],
        "project_id": payload.get("project_id", "PROJECT-AGENT-RUNTIME-PM-OS"),
        "status": status,
        "verification_status": unit.get("verification_status", "pending"),
        "owner": owner,
        "created_at": now_text,
        "updated_at": now_text,
        "origin_type": payload["origin_type"],
        "origin_ref": payload["origin_ref"],
        "created_by": payload["created_by"],
        "summary": unit["title"],
        "horizon": unit.get("horizon", "unit"),
        "model_tier": model_tier,
        "escalation_triggers": _list_value(unit.get("escalation_triggers")) or ["ambiguity", "data_integrity"],
        "context": unit["context"],
        "inputs": _text_lines(unit.get("inputs")),
        "target_files": _text_lines(unit.get("target_files")),
        "scope": unit["scope"],
        "acceptance": _text_lines(unit.get("acceptance")),
        "verification": _text_lines(unit.get("verification")),
        "handoff": unit["handoff"],
        "stop_condition": unit["stop_condition"],
    }
    steps = _text_lines(unit.get("steps"))
    sections = [
        ("Context", str(unit["context"]).strip()),
        ("Inputs", "\n".join(f"- {item}" for item in _text_lines(unit.get("inputs")))),
        ("Target Files", "\n".join(f"- {item}" for item in _text_lines(unit.get("target_files")))),
        ("Scope", str(unit["scope"]).strip()),
        ("Steps", "\n".join(f"{index}. {item}" for index, item in enumerate(steps, start=1))),
        ("Acceptance Criteria", "\n".join(f"- {item}" for item in _text_lines(unit.get("acceptance")))),
        ("Verification", "\n".join(f"- `{item}`" for item in _text_lines(unit.get("verification")))),
        ("Handoff", str(unit["handoff"]).strip()),
        ("Stop Boundary", str(unit["stop_condition"]).strip()),
    ]
    body = "\n\n".join(f"## {title}\n\n{text}" for title, text in sections)
    return (
        _frontmatter(meta)
        + "\n\n"
        + f"# {unit_id} - {unit['title']}\n\n"
        + body
        + "\n"
    )


def _render_review(
    *,
    now_text: str,
    payload: dict[str, Any],
    initiative: dict[str, Any],
    taskset: dict[str, Any],
    tasks: list[dict[str, Any]],
) -> str:
    title = f"{taskset['display_name']} Registration"
    rows = "\n".join(f"| `{task['display_id']}` | {task['title']} | planned |" for task in tasks)
    unit_count = sum(len(_units_for(task)) for task in tasks)
    unit_signal = "unit specs included" if unit_count else "unit specs deferred"
    next_unit_line = (
        "- Continue into `work close`, `work verify`, and AI proposal tools after unit generation is covered."
        if unit_count
        else "- Continue into unit spec generation, `work close`, `work verify`, and AI proposal tools."
    )
    return f"""---
title: {title}
date: {_parse_datetime(now_text).date().isoformat()}
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# {title}

## Bottom Line

Structured work registration created initiative `{initiative['id']}`, taskset
`{taskset['id']}`, `{len(tasks)}` task records, and `{unit_count}` unit specs
from one input file.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Input schema | pass | `{REGISTRATION_SCHEMA}` |
| Reservation ledger | pass | task display IDs fulfilled during registration |
| Generated records | pass | initiative, taskset plan, task files, {unit_signal}, and generated views refreshed |

## Decision

Use `scripts/work.py new --input <json>` as the deterministic planner-facing
registration path for this taskset shape.

## Action Board

| Task | Title | Status |
| --- | --- | --- |
{rows}

## Risks / Blockers

- This deterministic path does not perform AI decomposition, assignment, or
  approval bypass.
- Additional work is still needed for closeout automation and proposal-backed
  AI split/criteria/assign behavior.

## Next

- Run `python scripts/work_item_classifier.py --check` and
  `python scripts/taskset_work_gate.py --check` before handoff.
- Keep AI `split`, `criteria`, and `assign` tools behind B-mode proposal review.
{next_unit_line}
"""


def _validate_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    findings: list[str] = []
    if str(payload.get("schema_version") or "") != REGISTRATION_SCHEMA:
        findings.append("input:schema_version:invalid-or-missing")
    for field in ("origin_type", "origin_ref", "created_by"):
        _require_text(payload, field, "root", findings)
    initiative = _as_dict(payload.get("initiative"), "initiative", findings)
    taskset = _as_dict(payload.get("taskset"), "taskset", findings)
    tasks = _as_tasks(payload.get("tasks"), findings)

    for field in ("id", "title", "summary", "owner"):
        _require_text(initiative, field, "initiative", findings)
    for field in ("id", "display_name", "summary"):
        _require_text(taskset, field, "taskset", findings)
    try:
        int(taskset.get("order", 500))
    except (TypeError, ValueError):
        findings.append("input:taskset:invalid:order")

    display_ids: list[str] = []
    for index, task in enumerate(tasks, start=1):
        prefix = f"tasks[{index}]"
        _require_text(task, "title", prefix, findings)
        _require_text(task, "goal", prefix, findings)
        display_id = str(task.get("display_id") or "").strip()
        if display_id:
            if not TASK_DISPLAY_RE.match(display_id):
                findings.append(f"input:{prefix}:invalid:display_id:{display_id}")
            display_ids.append(display_id)
        units = task.get("units")
        if units is None:
            continue
        if not isinstance(units, list) or not all(isinstance(item, dict) for item in units):
            findings.append(f"input:{prefix}:units:missing-or-invalid")
            continue
        unit_ids: list[str] = []
        for unit_index, unit in enumerate(units, start=1):
            unit_prefix = f"{prefix}.units[{unit_index}]"
            for field in sorted(UNIT_REQUIRED_FIELDS):
                if not _has_text_value(unit.get(field)):
                    findings.append(f"input:{unit_prefix}:missing:{field}")
            unit_id = str(unit.get("unit_id") or "").strip()
            if unit_id:
                match = UNIT_DISPLAY_RE.match(unit_id)
                if not match:
                    findings.append(f"input:{unit_prefix}:invalid:unit_id:{unit_id}")
                elif display_id and match.group(1) != display_id:
                    findings.append(f"input:{unit_prefix}:unit-task-mismatch:{unit_id}:{display_id}")
                unit_ids.append(unit_id)
        duplicate_units = sorted({unit_id for unit_id in unit_ids if unit_ids.count(unit_id) > 1})
        for unit_id in duplicate_units:
            findings.append(f"input:{prefix}:units:duplicate-unit-id:{unit_id}")
    duplicates = sorted({display_id for display_id in display_ids if display_ids.count(display_id) > 1})
    for display_id in duplicates:
        findings.append(f"input:tasks:duplicate-display-id:{display_id}")
    if findings:
        raise WorkRegistrationError(findings)
    return initiative, taskset, tasks


def _existing_task_matches(path: Path, taskset_id: str, initiative_id: str) -> bool:
    if not path.exists():
        return False
    meta, _ = backlog_board.parse_frontmatter(path.read_text(encoding="utf-8"))
    return (
        str(meta.get("id") or path.stem) == path.stem
        and str(meta.get("task_set_id") or "") == taskset_id
        and str(meta.get("initiative_id") or "") == initiative_id
    )


def _existing_simple_record_matches(path: Path, item_id: str) -> bool:
    if not path.exists():
        return False
    meta, _ = backlog_board.parse_frontmatter(path.read_text(encoding="utf-8"))
    return str(meta.get("id") or meta.get("work_id") or path.stem) == item_id


def _load_taskset_registry(root: Path) -> dict[str, Any]:
    path = root / TASKSET_REGISTRY_PATH
    if not path.exists():
        return {"schema": TASKSET_REGISTRY_SCHEMA, "tasksets": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkRegistrationError([f"{_rel(root, path)}: invalid-json:{exc}"])
    if not isinstance(payload, dict):
        raise WorkRegistrationError([f"{_rel(root, path)}: invalid-json-root"])
    payload.setdefault("schema", TASKSET_REGISTRY_SCHEMA)
    payload.setdefault("tasksets", [])
    return payload


def _write_taskset_registry(root: Path, taskset: dict[str, Any]) -> None:
    path = root / TASKSET_REGISTRY_PATH
    payload = _load_taskset_registry(root)
    rows = [row for row in payload.get("tasksets", []) if isinstance(row, dict)]
    new_row = {
        "task_set_id": taskset["id"],
        "display_name": taskset["display_name"],
        "summary": taskset["summary"],
        "order": int(taskset.get("order", 500)),
    }
    for row in rows:
        if row.get("task_set_id") == taskset["id"]:
            comparable = {
                "task_set_id": row.get("task_set_id"),
                "display_name": row.get("display_name"),
                "summary": row.get("summary"),
                "order": int(row.get("order", 500)),
            }
            if comparable != new_row:
                raise WorkRegistrationError([f"{_rel(root, path)}: taskset-definition-conflict:{taskset['id']}"])
            return
    rows.append(new_row)
    rows.sort(key=lambda row: (int(row.get("order", 500)), str(row.get("task_set_id") or "")))
    payload["schema"] = TASKSET_REGISTRY_SCHEMA
    payload["tasksets"] = rows
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ensure_owner_doc(root: Path, review_path: Path) -> None:
    rel_review = _rel(root, review_path)
    path = root / OWNER_DOCS_PATH
    if not path.exists():
        path.write_text("schema: agent-runtime-owner-docs/v1\nowner_docs:\n", encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    if rel_review in text:
        return
    if "owner_docs:" not in text:
        text = text.rstrip() + "\nowner_docs:\n"
    lines = text.rstrip().splitlines()
    insert_at = None
    for index, line in enumerate(lines):
        if line.strip() == "owner_docs:":
            insert_at = index + 1
            break
    if insert_at is None:
        lines.append("owner_docs:")
        insert_at = len(lines)
    lines.insert(insert_at, f"  - {rel_review}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _refresh_generated_views(root: Path) -> None:
    tasks = backlog_board.load_tasks(root / TASKS_DIR)
    (root / "BACKLOG-BOARD.md").write_text(backlog_board.render(tasks, root=root), encoding="utf-8")

    classification = work_item_classifier.collect(root)
    json_out = root / work_item_classifier.DEFAULT_JSON
    md_out = root / work_item_classifier.DEFAULT_MD
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(classification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_out.write_text(work_item_classifier.render_markdown(classification), encoding="utf-8")

    index_out = root / evidence_index_generator.DEFAULT_OUT
    index_out.parent.mkdir(parents=True, exist_ok=True)
    index_out.write_text(
        evidence_index_generator.render(root, evidence_index_generator.collect(root)),
        encoding="utf-8",
    )


def _refresh_evidence_index(root: Path) -> None:
    index_out = root / evidence_index_generator.DEFAULT_OUT
    index_out.parent.mkdir(parents=True, exist_ok=True)
    index_out.write_text(
        evidence_index_generator.render(root, evidence_index_generator.collect(root)),
        encoding="utf-8",
    )


def _assign_missing_display_ids(
    root: Path,
    payload: dict[str, Any],
    tasks: list[dict[str, Any]],
    now: datetime,
) -> None:
    explicit = {str(task.get("display_id") or "").strip() for task in tasks if str(task.get("display_id") or "").strip()}
    assigned: set[str] = set(explicit)
    for task in tasks:
        if str(task.get("display_id") or "").strip():
            continue
        while True:
            candidate = task_identity._next_numeric_display_id(root, payload)  # noqa: SLF001
            number = task_identity._display_id_number(candidate)  # noqa: SLF001
            while candidate in assigned:
                if number is None:
                    raise WorkRegistrationError([f"task-id:auto-allocation-failed:{candidate}"])
                number += 1
                candidate = f"TASK-AR-{number:03d}"
            active = task_identity._active_reservation_for_display(payload, candidate, now)  # noqa: SLF001
            if active:
                assigned.add(candidate)
                continue
            task["display_id"] = candidate
            assigned.add(candidate)
            break


def _units_for(task: dict[str, Any]) -> list[dict[str, Any]]:
    units = task.get("units")
    if isinstance(units, list):
        return [unit for unit in units if isinstance(unit, dict)]
    return []


def _assign_unit_ids(tasks: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    findings: list[str] = []
    for task in tasks:
        task_id = str(task["display_id"])
        units = _units_for(task)
        for index, unit in enumerate(units, start=1):
            unit_id = str(unit.get("unit_id") or "").strip() or f"UNIT-{task_id}-{index:03d}"
            match = UNIT_DISPLAY_RE.match(unit_id)
            if not match:
                findings.append(f"input:tasks:{task_id}:units:invalid-unit-id:{unit_id}")
                continue
            if match.group(1) != task_id:
                findings.append(f"input:tasks:{task_id}:units:unit-task-mismatch:{unit_id}")
                continue
            if unit_id in seen:
                findings.append(f"input:tasks:{task_id}:units:duplicate-unit-id:{unit_id}")
                continue
            seen.add(unit_id)
            unit["unit_id"] = unit_id
        if units:
            task["unit_spec"] = _unit_rel_path(task_id, str(units[0]["unit_id"]))
    if findings:
        raise WorkRegistrationError(findings)


def _unit_targets(root: Path, tasks: list[dict[str, Any]]) -> list[Path]:
    targets: list[Path] = []
    for task in tasks:
        task_id = str(task["display_id"])
        for unit in _units_for(task):
            targets.append(_unit_path(root, task_id, str(unit["unit_id"])))
    return targets


def _existing_unit_matches(path: Path, task_id: str, unit_id: str) -> bool:
    if not path.exists():
        return False
    meta, _ = backlog_board.parse_frontmatter(path.read_text(encoding="utf-8"))
    return str(meta.get("unit_id") or path.stem) == unit_id and str(meta.get("task_id") or "") == task_id


def _preflight_existing(
    root: Path,
    initiative: dict[str, Any],
    taskset: dict[str, Any],
    tasks: list[dict[str, Any]],
    initiative_path: Path,
    plan_path: Path,
    review_path: Path,
) -> str:
    targets = [
        initiative_path,
        plan_path,
        review_path,
        *[_task_path(root, str(task["display_id"])) for task in tasks],
        *_unit_targets(root, tasks),
    ]
    existing = [path for path in targets if path.exists()]
    if not existing:
        return "create"
    if len(existing) != len(targets):
        raise WorkRegistrationError([f"work-new:partial-existing-records:{','.join(_rel(root, path) for path in existing)}"])
    findings: list[str] = []
    if not _existing_simple_record_matches(initiative_path, str(initiative["id"])):
        findings.append(f"{_rel(root, initiative_path)}: existing-record-conflict:{initiative['id']}")
    if not _existing_simple_record_matches(plan_path, str(taskset["id"])):
        findings.append(f"{_rel(root, plan_path)}: existing-record-conflict:{taskset['id']}")
    for task in tasks:
        task_path = _task_path(root, str(task["display_id"]))
        if not _existing_task_matches(task_path, str(taskset["id"]), str(initiative["id"])):
            findings.append(f"{_rel(root, task_path)}: existing-task-conflict:{task['display_id']}")
        for unit in _units_for(task):
            unit_id = str(unit["unit_id"])
            unit_path = _unit_path(root, str(task["display_id"]), unit_id)
            if not _existing_unit_matches(unit_path, str(task["display_id"]), unit_id):
                findings.append(f"{_rel(root, unit_path)}: existing-unit-conflict:{unit_id}")
    if findings:
        raise WorkRegistrationError(findings)
    return "already_exists"


def register(root: Path, input_path: Path, *, now: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    payload = _read_json(input_path)
    initiative, taskset, tasks = _validate_payload(payload)
    now_text = _now_text(now or str(payload.get("now") or ""))
    if not now_text:
        now_text = _now_text(None)
    now_dt = _parse_datetime(now_text)

    ledger_path = task_identity._reservation_path(root)  # noqa: SLF001
    lock_path = task_identity._lock_path(ledger_path)  # noqa: SLF001
    try:
        fd = task_identity._acquire_lock(lock_path)  # noqa: SLF001
    except TimeoutError as exc:
        raise WorkRegistrationError([f"task-reservation:lock-timeout:{exc}"]) from exc
    try:
        ledger, error = task_identity._read_json(ledger_path)  # noqa: SLF001
        if error:
            raise WorkRegistrationError([f"{_rel(root, ledger_path)}: invalid-ledger"])
        _assign_missing_display_ids(root, ledger, tasks, now_dt)
        _assign_unit_ids(tasks)

        display_ids = [str(task["display_id"]) for task in tasks]
        if len(display_ids) != len(set(display_ids)):
            duplicates = sorted({display_id for display_id in display_ids if display_ids.count(display_id) > 1})
            raise WorkRegistrationError([f"input:tasks:duplicate-display-id:{display_id}" for display_id in duplicates])
        task_displays = task_identity._task_display_ids(root)  # noqa: SLF001
        for display_id in display_ids:
            if display_id in task_displays:
                task_path = _task_path(root, display_id)
                if not _existing_task_matches(task_path, str(taskset["id"]), str(initiative["id"])):
                    raise WorkRegistrationError([f"task-id:display-id-exists:{display_id}"])
            active = task_identity._active_reservation_for_display(ledger, display_id, now_dt)  # noqa: SLF001
            if active:
                raise WorkRegistrationError([f"task-id:reservation-active:{display_id}:{active.get('reservation_id', '')}"])

        initiative_path = _initiative_path(root, str(initiative["id"]))
        plan_path = _plan_path(root, now_text, taskset)
        review_path = _review_path(root, now_text, taskset)
        mode = _preflight_existing(root, initiative, taskset, tasks, initiative_path, plan_path, review_path)
        if mode == "already_exists":
            _write_taskset_registry(root, taskset)
            _ensure_owner_doc(root, review_path)
            _refresh_generated_views(root)
            return {
                "status": "already_exists",
                "initiative": _rel(root, initiative_path),
                "plan": _rel(root, plan_path),
                "review": _rel(root, review_path),
                "tasks": [_rel(root, _task_path(root, str(task["display_id"]))) for task in tasks],
                "units": [_rel(root, path) for path in _unit_targets(root, tasks)],
            }

        prepared_tasks: list[dict[str, Any]] = []
        prepared_units: list[dict[str, Any]] = []
        group_id = f"RES-{now_dt.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        for index, task in enumerate(tasks, start=1):
            display_id = str(task["display_id"])
            task_uid = str(uuid.uuid4())
            reservation_id = f"{group_id}-{index:02d}"
            task["title"] = _title_from_task(task, display_id)
            prepared_tasks.append(
                {
                    "task": task,
                    "task_uid": task_uid,
                    "reservation_id": reservation_id,
                    "path": _task_path(root, display_id),
                    "text": _render_task(
                        now_text=now_text,
                        payload=payload,
                        initiative=initiative,
                        taskset=taskset,
                        task=task,
                        task_uid=task_uid,
                        reservation_id=reservation_id,
                    ),
                }
            )
            for unit in _units_for(task):
                unit_uid = str(uuid.uuid4())
                unit_id = str(unit["unit_id"])
                prepared_units.append(
                    {
                        "unit": unit,
                        "unit_uid": unit_uid,
                        "path": _unit_path(root, display_id, unit_id),
                        "text": _render_unit(
                            now_text=now_text,
                            payload=payload,
                            initiative=initiative,
                            taskset=taskset,
                            task=task,
                            unit=unit,
                            unit_uid=unit_uid,
                        ),
                    }
                )

        initiative_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.parent.mkdir(parents=True, exist_ok=True)
        initiative_path.write_text(_render_initiative(now_text, payload, initiative), encoding="utf-8")
        plan_path.write_text(
            _render_plan(now_text=now_text, payload=payload, initiative=initiative, taskset=taskset, tasks=tasks),
            encoding="utf-8",
        )
        for prepared in prepared_tasks:
            prepared["path"].parent.mkdir(parents=True, exist_ok=True)
            prepared["path"].write_text(str(prepared["text"]), encoding="utf-8")
        for prepared in prepared_units:
            prepared["path"].parent.mkdir(parents=True, exist_ok=True)
            prepared["path"].write_text(str(prepared["text"]), encoding="utf-8")
        review_path.write_text(
            _render_review(now_text=now_text, payload=payload, initiative=initiative, taskset=taskset, tasks=tasks),
            encoding="utf-8",
        )

        for prepared in prepared_tasks:
            task = prepared["task"]
            reservation = {
                "schema": "agent-runtime-task-id-reservation/v1",
                "reservation_id": prepared["reservation_id"],
                "reservation_group_id": group_id,
                "kind": "task",
                "display_id": task["display_id"],
                "status": "fulfilled",
                "owner_id": payload["created_by"],
                "task_set_id": taskset["id"],
                "initiative_id": initiative["id"],
                "reserved_at": now_text,
                "expires_at": (now_dt + timedelta(seconds=RESERVATION_TTL_SECONDS)).astimezone().isoformat(timespec="seconds"),
                "ttl_seconds": RESERVATION_TTL_SECONDS,
                "reason": f"work registration {taskset['id']}",
                "fulfilled_by": _rel(root, prepared["path"]),
                "fulfilled_task_id": task["display_id"],
                "fulfilled_task_uid": prepared["task_uid"],
                "fulfilled_at": now_text,
            }
            ledger.setdefault("reservations", []).append(reservation)
        ledger["schema"] = task_identity.RESERVATION_SCHEMA
        ledger["updated_at"] = now_text
        task_identity._write_json_atomic(ledger_path, ledger)  # noqa: SLF001
    finally:
        task_identity._release_lock(lock_path, fd)  # noqa: SLF001

    _write_taskset_registry(root, taskset)
    _ensure_owner_doc(root, review_path)
    _refresh_generated_views(root)
    return {
        "status": "created",
        "initiative": _rel(root, initiative_path),
        "plan": _rel(root, plan_path),
        "review": _rel(root, review_path),
        "tasks": [_rel(root, _task_path(root, str(task["display_id"]))) for task in tasks],
        "units": [_rel(root, path) for path in _unit_targets(root, tasks)],
        "reservation_group_id": group_id,
    }


def _is_plan_flow_script(entry: str) -> bool:
    normalized = entry.replace("\\", "/").strip()
    return normalized.startswith("scripts/") and normalized.endswith(".py")


def _plan_snapshot_design_record(root: Path, payload: dict[str, Any], review_rel: str) -> str:
    origin_ref = str(payload.get("origin_ref") or "").strip().replace("\\", "/")
    if origin_ref and (root / origin_ref).is_file():
        return origin_ref
    return review_rel


def _plan_snapshot_anchors(payload: dict[str, Any], design_record: str) -> list[str]:
    anchors = {design_record, *PLAN_SNAPSHOT_DEFAULT_ANCHORS}
    tasks = payload.get("tasks")
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            continue
        sources = [task.get("target_files")]
        units = task.get("units")
        for unit in units if isinstance(units, list) else []:
            if isinstance(unit, dict):
                sources.append(unit.get("target_files"))
        for source in sources:
            for entry in _text_lines(source):
                if _is_plan_flow_script(entry):
                    anchors.add(entry.replace("\\", "/").strip())
    return sorted(anchors)


def record_plan_snapshot(root: Path, input_path: Path, result: dict[str, Any]) -> dict[str, Any]:
    """T0: record the plan-assumption snapshot for a freshly registered taskset.

    Default anchor set: the design record (the input's ``origin_ref`` when that
    file exists, otherwise the generated registration review) plus the
    registration/dispatch flow scripts and every ``scripts/*.py`` the taskset's
    tasks/units declare in ``target_files``. Deferred revalidation: drift
    against these anchors blocks claim creation at T2
    (``task_claim_dispatcher.py create``) until a replan review re-records.
    """
    payload = _read_json(input_path)
    taskset = payload.get("taskset") if isinstance(payload.get("taskset"), dict) else {}
    taskset_id = str(taskset.get("id") or "").strip()
    design_record = _plan_snapshot_design_record(root, payload, str(result.get("review") or ""))
    anchors = _plan_snapshot_anchors(payload, design_record)
    plan_assumption_gate.cmd_record(root, taskset_id, design_record, anchors)
    return {
        "status": "recorded",
        "taskset_id": taskset_id,
        "design_record": design_record,
        "anchors": anchors,
        "registry": plan_assumption_gate.REGISTRY_REL,
    }


def _candidate_work_paths(root: Path, work_id: str) -> list[Path]:
    raw = Path(work_id)
    if raw.exists():
        return [raw.resolve()]
    if not raw.is_absolute() and (root / raw).exists():
        return [(root / raw).resolve()]
    candidates: list[Path] = []
    if UNIT_DISPLAY_RE.match(work_id):
        candidates.extend(sorted((root / UNITS_DIR).glob(f"*/{work_id}.md")))
    if TASK_DISPLAY_RE.match(work_id):
        candidates.append(root / TASKS_DIR / f"{work_id}.md")
        candidates.extend(sorted((root / UNITS_DIR / work_id).glob("UNIT-*.md")))
    return [path for path in candidates if path.exists()]


def _load_work_item(root: Path, work_id: str, *, command_name: str) -> tuple[Path, dict[str, Any], str]:
    paths = _candidate_work_paths(root, work_id)
    if not paths:
        raise WorkRegistrationError([f"{command_name}:not-found:{work_id}"])
    if len(paths) > 1 and not UNIT_DISPLAY_RE.match(work_id):
        raise WorkRegistrationError([f"{command_name}:ambiguous:{work_id}:{','.join(_rel(root, path) for path in paths)}"])
    path = paths[0]
    text = path.read_text(encoding="utf-8")
    meta, body = backlog_board.parse_frontmatter(text)
    if not meta:
        raise WorkRegistrationError([f"{_rel(root, path)}: missing-frontmatter"])
    return path, dict(meta), body


def _load_verifiable_work(root: Path, work_id: str) -> tuple[Path, dict[str, Any], str]:
    return _load_work_item(root, work_id, command_name="work-verify")


def _work_id_from_meta(path: Path, meta: dict[str, Any]) -> str:
    return str(
        meta.get("unit_id")
        or meta.get("work_id")
        or meta.get("id")
        or meta.get("display_id")
        or path.stem
    ).strip()


def _verification_commands(meta: dict[str, Any]) -> list[str]:
    return _text_lines(meta.get("verification"))


def _acceptance_criteria(meta: dict[str, Any], body: str) -> list[str]:
    return _text_lines(meta.get("acceptance")) or _section_list(body, "Acceptance Criteria", "Acceptance")


def _criteria_verification_commands(meta: dict[str, Any], body: str) -> list[str]:
    return _verification_commands(meta) or _section_list(body, "Verification")


def _is_executable_verification(command: str) -> bool:
    text = command.strip()
    if not text:
        return False
    lower = text.lower()
    if lower.startswith(("manual:", "owner:", "note:", "n/a", "none")):
        return False
    return bool(
        re.match(r"^(python|pytest|git|gh|npm|node|pwsh|powershell|cmd|cargo|ruff|mypy)\b", text)
        or " scripts/" in f" {text}"
        or " scripts\\" in f" {text}"
    )


def _criteria_gap_rows(acceptance: list[str], commands: list[str]) -> list[dict[str, Any]]:
    executable = [command for command in commands if _is_executable_verification(command)]
    rows: list[dict[str, Any]] = []
    for criterion in acceptance:
        rows.append(
            {
                "acceptance": criterion,
                "verification_commands": executable,
                "verifiable": bool(executable),
            }
        )
    return rows


def _proposal_rel(path: Path, root: Path) -> str:
    return _rel(root, path)


def _render_criteria_draft(proposal: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    evidence = "\n".join(f"- {item.get('summary', '')}" for item in proposal.get("evidence", [])) or "- No evidence."
    verifiers = "\n".join(f"- `{item}`" for item in proposal.get("verifier_list", []))
    criteria_rows = "\n".join(
        "| "
        + " | ".join(
            [
                str(index),
                row["acceptance"].replace("|", "/"),
                "yes" if row["verifiable"] else "no",
                ", ".join(f"`{cmd}`" for cmd in row["verification_commands"]) or "-",
            ]
        )
        + " |"
        for index, row in enumerate(rows, start=1)
    )
    return "\n".join(
        [
            "---",
            "status: draft",
            "origin_type: planning_proposal",
            f"origin_ref: agents/planning/outbox/{proposal['id']}.json",
            "tags:",
            "  - proposal-draft",
            "  - work-criteria",
            "---",
            "",
            f"# {proposal['title']}",
            "",
            "## Goal",
            "",
            proposal["suggested_next_action"],
            "",
            "## Criteria Map",
            "",
            "| # | Acceptance | Verifiable | Verification Commands |",
            "| --- | --- | --- | --- |",
            criteria_rows or "| - | - | - | - |",
            "",
            "## Source Evidence",
            "",
            evidence,
            "",
            "## Verifier List",
            "",
            verifiers,
            "",
            "## Risk Boundary",
            "",
            proposal["owner_boundary"],
            "",
        ]
    )


def _write_criteria_proposal(
    root: Path,
    *,
    work_id: str,
    work_path: str,
    rows: list[dict[str, Any]],
    actor: str,
    now_text: str,
    outbox: Path,
    draft_dir: Path,
) -> tuple[dict[str, Any], str, str]:
    gaps = [row for row in rows if not row["verifiable"]]
    proposal_core = {
        "action_type": "plan_update",
        "work_id": work_id,
        "work_path": work_path,
        "gaps": gaps,
    }
    proposal_id = _stable_id("PROP", proposal_core)
    evidence_hash = _stable_hash(gaps)
    proposal_path = outbox / f"{proposal_id}.json"
    draft_path = draft_dir / f"{proposal_id}.md"
    summaries = [
        {
            "summary": f"{work_id} acceptance criterion lacks an executable verification command: {row['acceptance']}",
            "confidence": 0.86,
            "severity": "watch",
        }
        for row in gaps
    ]
    verifier_list = [
        f"python scripts/work.py criteria {work_id} --json",
        "python scripts/owner_governance_gate.py",
    ]
    proposal: dict[str, Any] = {
        "id": proposal_id,
        "mode": "B",
        "status": "proposed",
        "action_type": "plan_update",
        "proposal_output": "plan",
        "risk_tier": "low",
        "title": f"work criteria: {work_id}",
        "created_at": now_text,
        "updated_at": now_text,
        "trace_id": None,
        "dedupe_key": f"work-criteria:{work_id}:{evidence_hash}",
        "evidence_hash": evidence_hash,
        "source_refs": [{"path": work_path, "kind": "work_criteria"}],
        "evidence": summaries,
        "target_files": [work_path],
        "rollback_path": f"agents/planning/rollback/{proposal_id}.json",
        "verifier_list": verifier_list,
        "expected_verification_command": verifier_list[0],
        "owner_boundary": "B-mode proposal only; do not mutate canonical work item criteria without approved apply.",
        "affected_owner_boundary": "Local planning/work item criteria only after approved apply.",
        "blast_radius": "Local work item acceptance and verification metadata/body only.",
        "rejection_reason": None,
        "department": "planning-office",
        "reviewer_opinions": [],
        "suggested_next_action": "Add executable verification commands so every acceptance criterion is measurable before closeout.",
        "supersedes": [],
        "draft_task_path": _proposal_rel(draft_path, root),
    }
    proposal_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    proposal_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    draft_path.write_text(_render_criteria_draft(proposal, rows), encoding="utf-8")
    return proposal, _proposal_rel(proposal_path, root), _proposal_rel(draft_path, root)


def _load_team_leads(root: Path) -> dict[str, str]:
    teams_path = root / "agents" / "project" / "TEAMS.md"
    if not teams_path.exists():
        return {}
    team_leads: dict[str, str] = {}
    current_team = ""
    for raw in teams_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        team_match = re.match(r"^-\s+team_id:\s*(\S+)\s*$", line)
        if team_match:
            current_team = team_match.group(1)
            continue
        lead_match = re.match(r"^lead:\s*(\S+)\s*$", line)
        if current_team and lead_match:
            team_leads[current_team] = lead_match.group(1)
    return team_leads


def _assignment_text(meta: dict[str, Any], body: str) -> str:
    values: list[str] = []
    scalar_fields = (
        "work_id",
        "kind",
        "title",
        "summary",
        "context",
        "scope",
        "handoff",
        "stop_condition",
        "owner",
        "team",
        "team_id",
    )
    for field in scalar_fields:
        value = meta.get(field)
        if value is not None:
            values.append(str(value))
    for field in ("tags", "inputs", "target_files", "acceptance", "verification", "escalation_triggers"):
        values.extend(_text_lines(meta.get(field)))
    values.append(body)
    return "\n".join(values).lower()


def _recommend_assignment(root: Path, meta: dict[str, Any], body: str) -> tuple[str, str, str]:
    team_leads = _load_team_leads(root)
    text = _assignment_text(meta, body)
    for team, default_owner, needles in ASSIGNMENT_RULES:
        if any(needle in text for needle in needles):
            return team, team_leads.get(team, default_owner), f"matched assignment rule for {team}"
    current_team = str(meta.get("team") or meta.get("team_id") or "").strip()
    current_owner = str(meta.get("owner") or "").strip()
    if current_team:
        return current_team, current_owner or team_leads.get(current_team, "planning-coordinator"), "kept existing team"
    return "planning-office", team_leads.get("planning-office", "planning-coordinator"), "defaulted to planning-office"


def _active_claim_workload(root: Path) -> dict[str, Any]:
    claims_dir = root / "agents" / "runtime" / "task_claims"
    by_team: dict[str, int] = {}
    by_role: dict[str, int] = {}
    total = 0
    if claims_dir.is_dir():
        for path in sorted(claims_dir.glob("*.json"), key=lambda item: item.name.lower()):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict):
                continue
            status = str(payload.get("status") or "").strip().lower()
            if status not in ACTIVE_CLAIM_STATUSES:
                continue
            total += 1
            team = str(payload.get("team_id") or "unassigned").strip() or "unassigned"
            role = str(payload.get("agent_role") or "unassigned").strip() or "unassigned"
            by_team[team] = by_team.get(team, 0) + 1
            by_role[role] = by_role.get(role, 0) + 1
    return {
        "active_claim_count": total,
        "by_team": dict(sorted(by_team.items())),
        "by_role": dict(sorted(by_role.items())),
    }


def _render_assign_draft(proposal: dict[str, Any]) -> str:
    evidence = "\n".join(f"- {item.get('summary', '')}" for item in proposal.get("evidence", [])) or "- No evidence."
    verifiers = "\n".join(f"- `{item}`" for item in proposal.get("verifier_list", []))
    workload = proposal.get("workload") if isinstance(proposal.get("workload"), dict) else {}
    by_team = workload.get("by_team") if isinstance(workload.get("by_team"), dict) else {}
    workload_rows = "\n".join(f"| {team} | {count} |" for team, count in by_team.items())
    if not workload_rows:
        workload_rows = "| - | 0 |"
    return "\n".join(
        [
            "---",
            "status: draft",
            "origin_type: planning_proposal",
            f"origin_ref: agents/planning/outbox/{proposal['id']}.json",
            "tags:",
            "  - proposal-draft",
            "  - work-assign",
            "---",
            "",
            f"# {proposal['title']}",
            "",
            "## Goal",
            "",
            proposal["suggested_next_action"],
            "",
            "## Assignment",
            "",
            "| Field | Current | Recommended |",
            "| --- | --- | --- |",
            f"| Team | {proposal.get('current_team') or '-'} | {proposal.get('recommended_team') or '-'} |",
            f"| Owner | {proposal.get('current_owner') or '-'} | {proposal.get('recommended_owner') or '-'} |",
            "",
            "## Workload",
            "",
            "| Team | Active Claims |",
            "| --- | ---: |",
            workload_rows,
            "",
            "## Source Evidence",
            "",
            evidence,
            "",
            "## Verifier List",
            "",
            verifiers,
            "",
            "## Risk Boundary",
            "",
            proposal["owner_boundary"],
            "",
        ]
    )


def _write_assign_proposal(
    root: Path,
    *,
    work_id: str,
    work_path: str,
    current_team: str,
    current_owner: str,
    recommended_team: str,
    recommended_owner: str,
    reason: str,
    workload: dict[str, Any],
    actor: str,
    now_text: str,
    outbox: Path,
    draft_dir: Path,
) -> tuple[dict[str, Any], str, str]:
    proposal_core = {
        "action_type": "plan_update",
        "work_id": work_id,
        "work_path": work_path,
        "current_team": current_team,
        "current_owner": current_owner,
        "recommended_team": recommended_team,
        "recommended_owner": recommended_owner,
        "reason": reason,
    }
    proposal_id = _stable_id("PROP", proposal_core)
    evidence_hash = _stable_hash(proposal_core)
    proposal_path = outbox / f"{proposal_id}.json"
    draft_path = draft_dir / f"{proposal_id}.md"
    missing = []
    if not current_team:
        missing.append("team")
    if not current_owner:
        missing.append("owner")
    missing_summary = ", ".join(missing) if missing else "assignment"
    verifier_list = [
        f"python scripts/work.py assign {work_id} --json",
        "python scripts/owner_governance_gate.py",
    ]
    proposal: dict[str, Any] = {
        "id": proposal_id,
        "mode": "B",
        "status": "proposed",
        "action_type": "plan_update",
        "proposal_output": "plan",
        "risk_tier": "low",
        "title": f"work assign: {work_id}",
        "created_at": now_text,
        "updated_at": now_text,
        "trace_id": None,
        "dedupe_key": f"work-assign:{work_id}:{evidence_hash}",
        "evidence_hash": evidence_hash,
        "source_refs": [{"path": work_path, "kind": "work_assignment"}],
        "evidence": [
            {
                "summary": f"{work_id} is missing {missing_summary}; recommend {recommended_team}/{recommended_owner} because {reason}.",
                "confidence": 0.82,
                "severity": "watch",
            },
            {
                "summary": f"Current active claim count: {workload.get('active_claim_count', 0)}.",
                "confidence": 0.78,
                "severity": "info",
            },
        ],
        "target_files": [work_path],
        "rollback_path": f"agents/planning/rollback/{proposal_id}.json",
        "verifier_list": verifier_list,
        "expected_verification_command": verifier_list[0],
        "owner_boundary": "B-mode assignment proposal only; do not mutate canonical work item metadata or create claims without approved apply.",
        "affected_owner_boundary": "Local work item team/owner metadata only after approved apply.",
        "blast_radius": "Local work item assignment metadata and dispatcher input only.",
        "rejection_reason": None,
        "department": "planning-office",
        "reviewer_opinions": [],
        "suggested_next_action": f"Assign `{work_id}` to `{recommended_team}` / `{recommended_owner}` before dispatch.",
        "supersedes": [],
        "draft_task_path": _proposal_rel(draft_path, root),
        "current_team": current_team,
        "current_owner": current_owner,
        "recommended_team": recommended_team,
        "recommended_owner": recommended_owner,
        "recommendation_reason": reason,
        "workload": workload,
        "proposed_by": actor,
    }
    proposal_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    proposal_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    draft_path.write_text(_render_assign_draft(proposal), encoding="utf-8")
    return proposal, _proposal_rel(proposal_path, root), _proposal_rel(draft_path, root)


def assign_work(
    root: Path,
    work_id: str,
    *,
    actor: str,
    now: str | None = None,
    outbox: Path | None = None,
    draft_dir: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    now_text = _now_text(now)
    path, meta, body = _load_work_item(root, work_id, command_name="work-assign")
    resolved_id = _work_id_from_meta(path, meta)
    rel_path = _rel(root, path)
    current_team = str(meta.get("team") or meta.get("team_id") or "").strip()
    current_owner = str(meta.get("owner") or "").strip()
    recommended_team, recommended_owner, reason = _recommend_assignment(root, meta, body)
    if current_team and current_owner:
        recommended_team = current_team
        recommended_owner = current_owner
        reason = "existing assignment is explicit"
    workload = _active_claim_workload(root)
    needs_proposal = not (current_team and current_owner)
    result: dict[str, Any] = {
        "status": "pass" if not needs_proposal else "proposed",
        "work_id": resolved_id,
        "work_path": rel_path,
        "current_team": current_team,
        "current_owner": current_owner,
        "recommended_team": recommended_team,
        "recommended_owner": recommended_owner,
        "recommendation_reason": reason,
        "workload": workload,
        "proposal": "",
        "draft": "",
    }
    if needs_proposal:
        proposal, proposal_ref, draft_ref = _write_assign_proposal(
            root,
            work_id=resolved_id,
            work_path=rel_path,
            current_team=current_team,
            current_owner=current_owner,
            recommended_team=recommended_team,
            recommended_owner=recommended_owner,
            reason=reason,
            workload=workload,
            actor=actor,
            now_text=now_text,
            outbox=(outbox if outbox and outbox.is_absolute() else root / (outbox or PLANNING_OUTBOX_DIR)),
            draft_dir=(draft_dir if draft_dir and draft_dir.is_absolute() else root / (draft_dir or PLANNING_DRAFTS_DIR)),
        )
        result["proposal"] = proposal_ref
        result["draft"] = draft_ref
        result["proposal_id"] = proposal["id"]
    return result


def _load_task_for_split(root: Path, task_ref: str) -> tuple[Path, dict[str, Any], str]:
    raw = Path(task_ref)
    if raw.exists():
        path = raw.resolve()
    elif not raw.is_absolute() and (root / raw).exists():
        path = (root / raw).resolve()
    elif TASK_DISPLAY_RE.match(task_ref):
        path = (root / TASKS_DIR / f"{task_ref}.md").resolve()
    else:
        raise WorkRegistrationError([f"work-split:not-found:{task_ref}"])
    if not path.exists():
        raise WorkRegistrationError([f"work-split:not-found:{task_ref}"])
    text = path.read_text(encoding="utf-8")
    meta, body = backlog_board.parse_frontmatter(text)
    if not meta:
        raise WorkRegistrationError([f"{_rel(root, path)}: missing-frontmatter"])
    kind = str(meta.get("kind") or ("task" if TASK_DISPLAY_RE.match(path.stem) else "")).strip()
    if kind and kind != "task":
        raise WorkRegistrationError([f"work-split:not-task:{task_ref}:{kind}"])
    return path, dict(meta), body


def _existing_unit_paths(root: Path, task_id: str) -> list[Path]:
    unit_dir = root / UNITS_DIR / task_id
    if not unit_dir.is_dir():
        return []
    return sorted(unit_dir.glob("UNIT-*.md"), key=lambda item: item.name.lower())


def _short_text(value: str, limit: int = 72) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _task_target_files(meta: dict[str, Any], body: str) -> list[str]:
    return _text_lines(meta.get("target_files")) or _section_list(body, "Target Files")


def _task_inputs(meta: dict[str, Any], body: str, target_files: list[str]) -> list[str]:
    return _text_lines(meta.get("inputs")) or _section_list(body, "Inputs") or target_files


def _proposed_split_units(task_id: str, meta: dict[str, Any], body: str) -> list[dict[str, Any]]:
    title = str(meta.get("title") or task_id).strip()
    context = str(meta.get("summary") or meta.get("context") or "").strip()
    if not context:
        sections = _section_blocks(body)
        context = sections.get("goal") or sections.get("context") or f"Implement {title}."
    target_files = _task_target_files(meta, body)
    inputs = _task_inputs(meta, body, target_files)
    acceptance = _acceptance_criteria(meta, body) or [f"Complete {title} in a verifiable implementation unit."]
    commands = [command for command in _criteria_verification_commands(meta, body) if _is_executable_verification(command)]
    if not commands:
        commands = [f"python scripts/work.py split {task_id} --json"]

    units: list[dict[str, Any]] = []
    max_units = 5
    for index, criterion in enumerate(acceptance[:max_units], start=1):
        extra = acceptance[max_units:] if index == max_units else []
        criteria = [criterion, *extra]
        scope = " ".join(criteria)
        units.append(
            {
                "proposed_unit_ref": f"{task_id}-PROPOSED-{index:03d}",
                "title": f"{_short_text(title, 44)} - {_short_text(criterion, 64)}",
                "context": context,
                "inputs": inputs,
                "target_files": target_files,
                "scope": scope,
                "steps": [
                    f"Implement the bounded outcome: {_short_text(scope, 96)}",
                    "Update the focused tests, docs, or evidence required by the touched surface.",
                    "Run the declared verification commands and record handoff notes.",
                ],
                "acceptance": criteria,
                "verification": commands,
                "handoff": f"Report files changed, verification results, and any follow-up split needed for {task_id}.",
                "stop_condition": "Stop after this proposed unit is implemented, verified, and ready for closeout.",
            }
        )
        if index == max_units:
            break
    return units


def _proposed_unit_readiness_findings(units: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for index, unit in enumerate(units, start=1):
        ref = str(unit.get("proposed_unit_ref") or f"proposed-{index}")
        for field in sorted(UNIT_REQUIRED_FIELDS):
            value = unit.get(field)
            if isinstance(value, list):
                ready = any(str(item).strip() for item in value)
            else:
                ready = bool(str(value or "").strip())
            if not ready:
                findings.append(f"{ref}:split-readiness:missing:{field}")
        commands = _text_lines(unit.get("verification"))
        if not any(_is_executable_verification(command) for command in commands):
            findings.append(f"{ref}:split-readiness:no-executable-verification")
    return findings


def _render_split_draft(proposal: dict[str, Any]) -> str:
    evidence = "\n".join(f"- {item.get('summary', '')}" for item in proposal.get("evidence", [])) or "- No evidence."
    verifiers = "\n".join(f"- `{item}`" for item in proposal.get("verifier_list", []))
    unit_sections: list[str] = []
    for unit in proposal.get("proposed_units", []):
        if not isinstance(unit, dict):
            continue
        unit_sections.extend(
            [
                f"### {unit.get('proposed_unit_ref')} - {unit.get('title')}",
                "",
                f"- Scope: {unit.get('scope')}",
                "- Target files:",
                *[f"  - `{item}`" for item in _text_lines(unit.get("target_files"))],
                "- Acceptance:",
                *[f"  - {item}" for item in _text_lines(unit.get("acceptance"))],
                "- Verification:",
                *[f"  - `{item}`" for item in _text_lines(unit.get("verification"))],
                "",
            ]
        )
    readiness = "\n".join(f"- {item}" for item in proposal.get("readiness_findings", [])) or "- pass"
    return "\n".join(
        [
            "---",
            "status: draft",
            "origin_type: planning_proposal",
            f"origin_ref: agents/planning/outbox/{proposal['id']}.json",
            "tags:",
            "  - proposal-draft",
            "  - work-split",
            "---",
            "",
            f"# {proposal['title']}",
            "",
            "## Goal",
            "",
            proposal["suggested_next_action"],
            "",
            "## Proposed Units",
            "",
            *unit_sections,
            "## Readiness Check",
            "",
            readiness,
            "",
            "## Source Evidence",
            "",
            evidence,
            "",
            "## Verifier List",
            "",
            verifiers,
            "",
            "## Risk Boundary",
            "",
            proposal["owner_boundary"],
            "",
        ]
    )


def _write_split_proposal(
    root: Path,
    *,
    task_id: str,
    task_path: str,
    proposed_units: list[dict[str, Any]],
    readiness_findings: list[str],
    actor: str,
    now_text: str,
    outbox: Path,
    draft_dir: Path,
) -> tuple[dict[str, Any], str, str]:
    proposal_core = {
        "action_type": "plan_update",
        "task_id": task_id,
        "task_path": task_path,
        "proposed_units": proposed_units,
        "readiness_findings": readiness_findings,
    }
    proposal_id = _stable_id("PROP", proposal_core)
    evidence_hash = _stable_hash(proposal_core)
    proposal_path = outbox / f"{proposal_id}.json"
    draft_path = draft_dir / f"{proposal_id}.md"
    verifier_list = [
        f"python scripts/work.py split {task_id} --json",
        "python scripts/task_unit_readiness_gate.py --task-id <approved-task-id> --require-ready --check",
        "python scripts/owner_governance_gate.py",
    ]
    readiness_status = "pass" if not readiness_findings else "watch"
    proposal: dict[str, Any] = {
        "id": proposal_id,
        "mode": "B",
        "status": "proposed",
        "action_type": "plan_update",
        "proposal_output": "plan",
        "risk_tier": "medium" if readiness_findings else "low",
        "title": f"work split: {task_id}",
        "created_at": now_text,
        "updated_at": now_text,
        "trace_id": None,
        "dedupe_key": f"work-split:{task_id}:{evidence_hash}",
        "evidence_hash": evidence_hash,
        "source_refs": [{"path": task_path, "kind": "work_split"}],
        "evidence": [
            {
                "summary": f"{task_id} has no registered unit specs; propose {len(proposed_units)} worker-ready unit draft(s).",
                "confidence": 0.82,
                "severity": "watch",
            },
            {
                "summary": f"Internal split readiness status: {readiness_status}.",
                "confidence": 0.8,
                "severity": "watch" if readiness_findings else "info",
            },
        ],
        "target_files": [task_path],
        "rollback_path": f"agents/planning/rollback/{proposal_id}.json",
        "verifier_list": verifier_list,
        "expected_verification_command": verifier_list[0],
        "owner_boundary": "B-mode split proposal only; do not create unit files, reserve IDs, or mutate canonical work items without approved apply.",
        "affected_owner_boundary": "Local task-to-unit planning metadata only after approved apply.",
        "blast_radius": "Proposed unit specs for the target task only.",
        "rejection_reason": None,
        "department": "planning-office",
        "reviewer_opinions": [],
        "suggested_next_action": f"Review and approve proposed unit specs for `{task_id}` before creating canonical unit files.",
        "supersedes": [],
        "draft_task_path": _proposal_rel(draft_path, root),
        "task_id": task_id,
        "proposed_units": proposed_units,
        "readiness_status": readiness_status,
        "readiness_findings": readiness_findings,
        "proposed_by": actor,
    }
    proposal_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    proposal_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    draft_path.write_text(_render_split_draft(proposal), encoding="utf-8")
    return proposal, _proposal_rel(proposal_path, root), _proposal_rel(draft_path, root)


def split_work(
    root: Path,
    task_ref: str,
    *,
    actor: str,
    now: str | None = None,
    outbox: Path | None = None,
    draft_dir: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    now_text = _now_text(now)
    path, meta, body = _load_task_for_split(root, task_ref)
    task_id = str(meta.get("display_id") or meta.get("id") or meta.get("work_id") or path.stem).strip()
    rel_path = _rel(root, path)
    existing_units = [_rel(root, item) for item in _existing_unit_paths(root, task_id)]
    result: dict[str, Any] = {
        "status": "pass" if existing_units else "proposed",
        "task_id": task_id,
        "task_path": rel_path,
        "existing_unit_count": len(existing_units),
        "existing_units": existing_units,
        "proposed_unit_count": 0,
        "readiness_status": "pass",
        "readiness_findings": [],
        "proposal": "",
        "draft": "",
    }
    if existing_units:
        return result

    proposed_units = _proposed_split_units(task_id, meta, body)
    readiness_findings = _proposed_unit_readiness_findings(proposed_units)
    proposal, proposal_ref, draft_ref = _write_split_proposal(
        root,
        task_id=task_id,
        task_path=rel_path,
        proposed_units=proposed_units,
        readiness_findings=readiness_findings,
        actor=actor,
        now_text=now_text,
        outbox=(outbox if outbox and outbox.is_absolute() else root / (outbox or PLANNING_OUTBOX_DIR)),
        draft_dir=(draft_dir if draft_dir and draft_dir.is_absolute() else root / (draft_dir or PLANNING_DRAFTS_DIR)),
    )
    result.update(
        {
            "proposed_unit_count": len(proposed_units),
            "readiness_status": proposal["readiness_status"],
            "readiness_findings": readiness_findings,
            "proposal": proposal_ref,
            "draft": draft_ref,
            "proposal_id": proposal["id"],
        }
    )
    return result


def _compact_stamp(now_text: str) -> str:
    return re.sub(r"[^0-9]", "", now_text)[:14] or now_util.epoch_seconds()


def _evidence_path(root: Path, work_id: str, now_text: str) -> Path:
    date_part = _parse_datetime(now_text).date().isoformat()
    stamp = _compact_stamp(now_text)
    return root / REVIEWS_DIR / f"VERIFY-{date_part}-{_slug(work_id)}-{stamp}.json"


def _resolve_ref(root: Path, ref: str) -> Path:
    path = Path(ref)
    return path if path.is_absolute() else root / path


def _validate_actual_number(value: str | int | None, field: str, findings: list[str]) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        findings.append(f"work-close:missing-{field}")
        return ""
    try:
        parsed = Decimal(text)
    except InvalidOperation:
        findings.append(f"work-close:invalid-{field}:{text}")
        return ""
    if parsed < 0:
        findings.append(f"work-close:negative-{field}:{text}")
        return ""
    return text


def _validate_done_closeout(
    root: Path,
    path: Path,
    meta: dict[str, Any],
    resolved_id: str,
    *,
    actual_hours: str | None,
    actual_tokens: int | None,
) -> list[str]:
    findings: list[str] = []
    rel_path = _rel(root, path)
    status = str(meta.get("verification_status") or "").strip()
    if status != "passed":
        findings.append(f"{rel_path}: closeout:verification-status-not-passed:{status or 'missing'}")
    _validate_actual_number(actual_hours, "actual-hours", findings)
    _validate_actual_number(actual_tokens, "actual-tokens", findings)

    refs = _list_value(meta.get("evidence_refs"))
    if not refs:
        findings.append(f"{rel_path}: closeout:no-evidence-refs")
        return findings

    passed_refs: list[str] = []
    for ref in refs:
        ref_path = _resolve_ref(root, ref)
        if not ref_path.exists():
            findings.append(f"{ref}: closeout:evidence-missing")
            continue
        try:
            payload = json.loads(ref_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"{ref}: closeout:evidence-invalid-json:{exc}")
            continue
        if not isinstance(payload, dict):
            findings.append(f"{ref}: closeout:evidence-invalid-root")
            continue
        evidence_work_id = str(payload.get("work_id") or "").strip()
        if evidence_work_id and evidence_work_id != resolved_id:
            findings.append(f"{ref}: closeout:evidence-work-mismatch:{evidence_work_id}:{resolved_id}")
            continue
        evidence_status = str(payload.get("status") or "").strip()
        evidence_signal = str(payload.get("signal") or "").strip()
        if evidence_status == "passed" and evidence_signal in {"", "pass", "passed"}:
            passed_refs.append(ref)
            continue
        findings.append(f"{ref}: closeout:evidence-not-passed:{evidence_status or 'missing'}")

    if not passed_refs:
        findings.append(f"{rel_path}: closeout:no-passed-verification-evidence:{resolved_id}")
    return findings


def _closeout_block(
    *,
    completed_at: str,
    resolution: str,
    actual_hours: str,
    actual_tokens: str,
    actual_cost: str,
    closed_by: str,
    evidence_refs: list[str],
) -> str:
    lines = [
        CLOSEOUT_START,
        "## Closeout",
        "",
        f"- Completed at: `{completed_at}`",
        f"- Resolution: `{resolution}`",
        f"- Actual hours: `{actual_hours or '-'}`",
        f"- Actual tokens: `{actual_tokens or '-'}`",
    ]
    if actual_cost:
        lines.append(f"- Actual cost: `{actual_cost}`")
    lines.append(f"- Closed by: `{closed_by}`")
    lines.extend(["- Evidence:", *[f"  - `{ref}`" for ref in evidence_refs], CLOSEOUT_END])
    return "\n".join(lines)


def _replace_closeout_block(body: str, block: str) -> str:
    if CLOSEOUT_START in body and CLOSEOUT_END in body:
        pattern = re.compile(
            rf"{re.escape(CLOSEOUT_START)}.*?{re.escape(CLOSEOUT_END)}",
            flags=re.DOTALL,
        )
        return pattern.sub(block, body, count=1)
    return body.rstrip() + "\n\n" + block + "\n"


def _run_verification_command(root: Path, command: str, timeout: int) -> dict[str, Any]:
    started_at = now_util.local_iso()
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        finished_at = now_util.local_iso()
        return {
            "command": command,
            "status": "passed" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "started_at": started_at,
            "finished_at": finished_at,
            "stdout": (completed.stdout or "")[-4000:],
            "stderr": (completed.stderr or "")[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        finished_at = now_util.local_iso()
        return {
            "command": command,
            "status": "timeout",
            "returncode": None,
            "started_at": started_at,
            "finished_at": finished_at,
            "stdout": str(exc.stdout or "")[-4000:],
            "stderr": str(exc.stderr or "")[-4000:],
        }


def verify_work(root: Path, work_id: str, *, actor: str, now: str | None = None, timeout: int = 300) -> dict[str, Any]:
    root = root.resolve()
    now_text = _now_text(now)
    path, meta, body = _load_verifiable_work(root, work_id)
    resolved_id = _work_id_from_meta(path, meta)
    commands = _verification_commands(meta)
    if not commands:
        raise WorkRegistrationError([f"{_rel(root, path)}: verification:no-commands"])

    results = [_run_verification_command(root, command, timeout) for command in commands]
    passed = all(result["status"] == "passed" for result in results)
    status = "passed" if passed else "failed"
    evidence_path = _evidence_path(root, resolved_id, now_text)
    evidence = {
        "schema": "agent-runtime-work-verification/v1",
        "id": evidence_path.stem,
        "work_id": resolved_id,
        "work_path": _rel(root, path),
        "kind": str(meta.get("kind") or ("unit" if resolved_id.startswith("UNIT-") else "task")),
        "task_id": str(meta.get("task_id") or meta.get("id") or meta.get("display_id") or ""),
        "unit_id": str(meta.get("unit_id") or ""),
        "status": status,
        "signal": "pass" if passed else "fail",
        "verified_at": now_text,
        "verified_by": actor,
        "command_count": len(results),
        "commands": results,
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    existing_refs = _list_value(meta.get("evidence_refs"))
    evidence_ref = _rel(root, evidence_path)
    if evidence_ref not in existing_refs:
        existing_refs.append(evidence_ref)
    meta["verification_status"] = status
    meta["verified_at"] = now_text
    meta["verified_by"] = actor
    meta["evidence_refs"] = existing_refs
    meta["updated_at"] = now_text
    _rewrite_frontmatter(path, meta, body)
    _refresh_evidence_index(root)
    return {
        "status": status,
        "work_id": resolved_id,
        "work_path": _rel(root, path),
        "evidence": evidence_ref,
        "command_count": len(results),
        "commands": results,
    }


def criteria_work(
    root: Path,
    work_id: str,
    *,
    actor: str,
    now: str | None = None,
    outbox: Path | None = None,
    draft_dir: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    now_text = _now_text(now)
    path, meta, body = _load_work_item(root, work_id, command_name="work-criteria")
    resolved_id = _work_id_from_meta(path, meta)
    rel_path = _rel(root, path)
    acceptance = _acceptance_criteria(meta, body)
    commands = _criteria_verification_commands(meta, body)
    rows = _criteria_gap_rows(acceptance, commands)
    if not acceptance:
        rows = [
            {
                "acceptance": "missing acceptance criteria",
                "verification_commands": [command for command in commands if _is_executable_verification(command)],
                "verifiable": False,
            }
        ]
    gaps = [row for row in rows if not row["verifiable"]]
    result: dict[str, Any] = {
        "status": "pass" if not gaps else "proposed",
        "work_id": resolved_id,
        "work_path": rel_path,
        "criterion_count": len(acceptance),
        "verification_count": len(commands),
        "gap_count": len(gaps),
        "criteria": rows,
        "proposal": "",
        "draft": "",
    }
    if gaps:
        proposal, proposal_ref, draft_ref = _write_criteria_proposal(
            root,
            work_id=resolved_id,
            work_path=rel_path,
            rows=rows,
            actor=actor,
            now_text=now_text,
            outbox=(outbox if outbox and outbox.is_absolute() else root / (outbox or PLANNING_OUTBOX_DIR)),
            draft_dir=(draft_dir if draft_dir and draft_dir.is_absolute() else root / (draft_dir or PLANNING_DRAFTS_DIR)),
        )
        result["proposal"] = proposal_ref
        result["draft"] = draft_ref
        result["proposal_id"] = proposal["id"]
    return result


def close_work(
    root: Path,
    work_id: str,
    *,
    actor: str,
    resolution: str = "done",
    actual_hours: str | None = None,
    actual_tokens: int | None = None,
    actual_cost: str | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    now_text = _now_text(now)
    if resolution not in RESOLUTION_VALUES:
        raise WorkRegistrationError([f"work-close:invalid-resolution:{resolution}"])
    path, meta, body = _load_work_item(root, work_id, command_name="work-close")
    resolved_id = _work_id_from_meta(path, meta)
    findings: list[str] = []
    actual_hours_text = "" if actual_hours is None else str(actual_hours).strip()
    actual_tokens_text = "" if actual_tokens is None else str(actual_tokens).strip()
    actual_cost_text = "" if actual_cost is None else str(actual_cost).strip()

    if resolution == "done":
        findings.extend(
            _validate_done_closeout(
                root,
                path,
                meta,
                resolved_id,
                actual_hours=actual_hours_text,
                actual_tokens=actual_tokens,
            )
        )
    if actual_cost_text:
        _validate_actual_number(actual_cost_text, "actual-cost", findings)
    if findings:
        raise WorkRegistrationError(findings)

    refs = _list_value(meta.get("evidence_refs"))
    meta["status"] = "completed"
    meta["resolution"] = resolution
    meta["completed_at"] = now_text
    meta["updated_at"] = now_text
    meta["closed_by"] = actor
    if resolution != "done" and not str(meta.get("verification_status") or "").strip():
        meta["verification_status"] = "not_applicable"
    if actual_hours_text:
        meta["actual_hours"] = actual_hours_text
    if actual_tokens_text:
        meta["actual_tokens"] = actual_tokens_text
    if actual_cost_text:
        meta["actual_cost"] = actual_cost_text

    closeout = _closeout_block(
        completed_at=now_text,
        resolution=resolution,
        actual_hours=actual_hours_text,
        actual_tokens=actual_tokens_text,
        actual_cost=actual_cost_text,
        closed_by=actor,
        evidence_refs=refs,
    )
    _rewrite_frontmatter(path, meta, _replace_closeout_block(body, closeout))
    _refresh_generated_views(root)
    return {
        "status": "closed",
        "work_id": resolved_id,
        "work_path": _rel(root, path),
        "resolution": resolution,
        "completed_at": now_text,
        "evidence_refs": refs,
        "actual_hours": actual_hours_text,
        "actual_tokens": actual_tokens_text,
        "actual_cost": actual_cost_text,
    }


def _iter_work_item_records(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    paths: dict[Path, None] = {}
    for pattern in WORK_ITEM_PATH_PATTERNS:
        for path in (root / pattern.parent).glob(pattern.name) if "**" not in pattern.as_posix() else root.glob(pattern.as_posix()):
            if path.is_file():
                paths[path] = None
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(paths):
        try:
            meta, _body = backlog_board.parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if str(meta.get("schema_version") or "").strip() != WORK_ITEM_SCHEMA:
            continue
        records.append((path, dict(meta)))
    return records


def _stats_group_fields(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _stats_multi_values(raw: list[str] | None) -> list[str]:
    return [item for value in raw or [] for item in _stats_group_fields(value)]


def _stats_metrics(raw: str | None) -> list[str]:
    parts = _stats_group_fields(raw) or ["count"]
    metrics: list[str] = []
    findings: list[str] = []
    for part in parts:
        if part not in STATS_METRICS:
            findings.append(f"work-stats:invalid-metric:{part}")
        elif part not in metrics:
            metrics.append(part)
    if findings:
        raise WorkRegistrationError(findings)
    return metrics


def _validate_stats_fields(group_fields: list[str], filters: list[tuple[str, str]]) -> None:
    findings: list[str] = []
    for field in group_fields:
        if field in STATS_COMPUTED_ONLY_FIELDS:
            findings.append(f"work-stats:computed-only-dimension:{field}")
        elif field not in STATS_DIMENSIONS:
            findings.append(f"work-stats:invalid-dimension:{field}")
    for key, _value in filters:
        if key in STATS_COMPUTED_ONLY_FIELDS:
            findings.append(f"work-stats:computed-only-filter:{key}")
        elif key not in STATS_FILTERABLE_FIELDS:
            # Non-fatal: unknown keys keep matching nothing by design.
            print(
                f"work-stats: warning unknown-filter-key:{key} "
                f"(valid dimensions: {', '.join(sorted(STATS_DIMENSIONS))})",
                file=sys.stderr,
            )
    if findings:
        raise WorkRegistrationError(findings)


def _stats_where_filters(raw: list[str] | None) -> list[tuple[str, str]]:
    filters: list[tuple[str, str]] = []
    for item in raw or []:
        if "=" not in item:
            raise WorkRegistrationError([f"work-stats:invalid-where:{item}"])
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise WorkRegistrationError([f"work-stats:invalid-where:{item}"])
        filters.append((key, value.strip()))
    return filters


def _stats_matches(meta: dict[str, Any], *, kinds: list[str], statuses: list[str], filters: list[tuple[str, str]]) -> bool:
    if kinds and str(meta.get("kind") or "") not in kinds:
        return False
    if statuses and str(meta.get("status") or "") not in statuses:
        return False
    for key, value in filters:
        current = meta.get(key)
        if isinstance(current, list):
            if value not in [str(item) for item in current]:
                return False
        elif str(current or "") != value:
            return False
    return True


def _stats_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = Decimal(text)
    except InvalidOperation:
        return None
    return parsed


def _stats_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return _parse_datetime(text)
    except ValueError:
        return None


def _stats_metric_value(meta: dict[str, Any], metric: str, now_dt: datetime) -> Decimal | None:
    if metric == "count":
        return Decimal(1)
    if metric in STATS_NUMERIC_METRICS:
        return _stats_decimal(meta.get(metric))
    if metric == "lead_time":
        # Naming note (W4b AR-517): this metric prefers started_at and only
        # falls back to created_at, so for claimed items it is closer to
        # cycle time than lead time. Semantics are intentionally unchanged
        # here; the lead_time/cycle_time rename is deferred.
        finished = _stats_datetime(meta.get("completed_at"))
        started = _stats_datetime(meta.get("started_at")) or _stats_datetime(meta.get("created_at"))
        if not finished or not started or finished < started:
            return None
        return Decimal(str((finished - started).total_seconds() / 3600))
    if metric == "age":
        created = _stats_datetime(meta.get("created_at"))
        if not created or now_dt < created:
            return None
        return Decimal(str((now_dt - created).total_seconds() / 3600))
    raise WorkRegistrationError([f"work-stats:invalid-metric:{metric}"])


def _stats_json_number(value: Decimal | None) -> int | float | None:
    if value is None:
        return None
    normalized = value.normalize()
    if normalized == normalized.to_integral_value():
        return int(normalized)
    return float(normalized)


def _stats_text_number(value: Decimal | None) -> str:
    if value is None:
        return ""
    normalized = value.normalize()
    if normalized == normalized.to_integral_value():
        return str(int(normalized))
    return format(normalized, "f")


def _stats_item_record(root: Path, path: Path, meta: dict[str, Any], now_dt: datetime) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for field in STATS_EXPORT_TEXT_FIELDS:
        record[field] = str(meta.get(field) or "").strip()
    record["tags"] = _text_lines(meta.get("tags"))
    for field in STATS_EXPORT_NUMERIC_FIELDS:
        record[field] = _stats_json_number(_stats_decimal(meta.get(field)))
    record["lead_time_hours"] = _stats_json_number(_stats_metric_value(meta, "lead_time", now_dt))
    record["age_hours"] = _stats_json_number(_stats_metric_value(meta, "age", now_dt))
    record["path"] = _rel(root, path)
    return record


def work_stats(
    root: Path,
    *,
    by: str | None = None,
    metric: str = "count",
    kinds: list[str] | None = None,
    statuses: list[str] | None = None,
    where: list[str] | None = None,
    now: str | None = None,
    include_items: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    metrics = _stats_metrics(metric)
    group_fields = _stats_group_fields(by)
    filters = _stats_where_filters(where)
    _validate_stats_fields(group_fields, filters)
    kinds = _stats_multi_values(kinds)
    statuses = _stats_multi_values(statuses)
    now_dt = _parse_datetime(_now_text(now))

    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    items: list[dict[str, Any]] = []
    violations: list[str] = []
    total_items = 0
    for path, meta in _iter_work_item_records(root):
        if not _stats_matches(meta, kinds=kinds, statuses=statuses, filters=filters):
            continue
        stored_computed = sorted(STATS_COMPUTED_ONLY_FIELDS & set(meta))
        if stored_computed:
            violations.extend(
                f"{_rel(root, path)}: work-stats:computed-field-stored:{field}" for field in stored_computed
            )
            continue
        total_items += 1
        key = tuple(str(meta.get(field) or MISSING_GROUP_VALUE).strip() or MISSING_GROUP_VALUE for field in group_fields)
        group = groups.setdefault(
            key,
            {
                "group": {field: key[index] for index, field in enumerate(group_fields)},
                "count": 0,
                "values": {name: [] for name in metrics},
            },
        )
        group["count"] += 1
        for name in metrics:
            value = _stats_metric_value(meta, name, now_dt)
            if value is not None:
                group["values"][name].append(value)
        if include_items:
            items.append(_stats_item_record(root, path, meta, now_dt))
    if violations:
        raise WorkRegistrationError(violations)

    rows: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        values: dict[str, list[Decimal]] = group.pop("values")
        row: dict[str, Any] = {
            "group": group["group"],
            "count": int(group["count"]),
            "metrics": {},
        }
        for name in metrics:
            metric_values = values[name]
            value_count = len(metric_values)
            total = sum(metric_values, Decimal(0)) if metric_values else Decimal(0)
            avg = (total / Decimal(value_count)) if value_count else None
            row["metrics"][name] = {
                "value_count": value_count,
                "sum": _stats_json_number(total),
                "avg": _stats_json_number(avg),
                "min": _stats_json_number(min(metric_values) if metric_values else None),
                "max": _stats_json_number(max(metric_values) if metric_values else None),
            }
        if len(metrics) == 1:
            row.update(row["metrics"][metrics[0]])
        rows.append(row)

    result: dict[str, Any] = {
        "status": "pass",
        "metric": ",".join(metrics),
        "metrics": metrics,
        "group_by": group_fields,
        "filters": {
            "kind": kinds,
            "status": statuses,
            "where": [f"{key}={value}" for key, value in filters],
        },
        "total_items": total_items,
        "group_count": len(rows),
        "rows": rows,
    }
    if include_items:
        items.sort(key=lambda item: (str(item.get("work_id") or ""), str(item.get("path") or "")))
        result["items"] = items
    return result


def _resolve_out_path(root: Path, out: str) -> Path:
    path = Path(out)
    return path if path.is_absolute() else root / path


def _stats_export_format(export_format: str | None, out_path: Path) -> str:
    if export_format:
        if export_format not in STATS_EXPORT_FORMATS:
            raise WorkRegistrationError([f"work-stats:invalid-format:{export_format}"])
        return export_format
    return "csv" if out_path.suffix.lower() == ".csv" else "json"


def _stats_csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        text = "|".join(str(item) for item in value)
    else:
        text = str(value)
    return _neutralize_csv_formula(text)


def _neutralize_csv_formula(text: str) -> str:
    """Neutralize spreadsheet formula injection in file-exported CSV cells.

    Cells starting with ``=``, ``+``, or ``@`` are prefixed with a single
    quote. A leading ``-`` is prefixed only when the cell is not a plain
    number, so negative numeric values stay machine-readable.
    """
    if not text:
        return text
    first = text[0]
    if first in ("=", "+", "@"):
        return "'" + text
    if first == "-":
        try:
            float(text)
        except ValueError:
            return "'" + text
    return text


def _write_stats_export(
    root: Path,
    *,
    out: str,
    export_format: str,
    result: dict[str, Any],
    items: list[dict[str, Any]],
    now_text: str,
) -> dict[str, Any]:
    out_path = _resolve_out_path(root, out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if export_format == "csv":
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(STATS_EXPORT_COLUMNS), lineterminator="\n")
            writer.writeheader()
            for item in items:
                writer.writerow({column: _stats_csv_cell(item.get(column)) for column in STATS_EXPORT_COLUMNS})
    else:
        payload = {
            "schema": STATS_EXPORT_SCHEMA,
            "generated_at": now_text,
            "query": {
                "by": result["group_by"],
                "metrics": result["metrics"],
                "kind": result["filters"]["kind"],
                "status": result["filters"]["status"],
                "where": result["filters"]["where"],
            },
            "summary": result,
            "item_count": len(items),
            "items": items,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "export": _rel(root, out_path),
        "export_format": export_format,
        "export_items": len(items),
    }


def _execute_stats_query(
    root: Path,
    *,
    by: str | None = None,
    metric: str = "count",
    kinds: list[str] | None = None,
    statuses: list[str] | None = None,
    where: list[str] | None = None,
    now: str | None = None,
    out: str | None = None,
    export_format: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    now_text = _now_text(now)
    out_text = str(out or "").strip()
    if export_format and not out_text:
        raise WorkRegistrationError(["work-stats:format-requires-out"])
    result = work_stats(
        root,
        by=by,
        metric=metric,
        kinds=kinds,
        statuses=statuses,
        where=where,
        now=now_text,
        include_items=bool(out_text),
    )
    if out_text:
        items = result.pop("items", [])
        resolved_format = _stats_export_format(export_format, _resolve_out_path(root, out_text))
        result.update(
            _write_stats_export(
                root,
                out=out_text,
                export_format=resolved_format,
                result=result,
                items=items,
                now_text=now_text,
            )
        )
    return result


def _load_work_views(root: Path) -> dict[str, Any]:
    path = root / WORK_VIEWS_PATH
    if not path.exists():
        return {"schema": WORK_VIEWS_SCHEMA, "updated_at": "", "views": []}
    payload = _read_json(path)
    if str(payload.get("schema") or "") != WORK_VIEWS_SCHEMA:
        raise WorkRegistrationError([f"{_rel(root, path)}: work-view:invalid-schema:{payload.get('schema')}"])
    views = payload.get("views")
    if not isinstance(views, list):
        raise WorkRegistrationError([f"{_rel(root, path)}: work-view:invalid-views"])
    payload["views"] = [view for view in views if isinstance(view, dict)]
    return payload


def _find_view(payload: dict[str, Any], name: str) -> dict[str, Any] | None:
    for view in payload["views"]:
        if str(view.get("name") or "") == name:
            return view
    return None


def save_view(
    root: Path,
    name: str,
    *,
    by: str | None = None,
    metric: str = "count",
    kinds: list[str] | None = None,
    statuses: list[str] | None = None,
    where: list[str] | None = None,
    export_format: str | None = None,
    out: str | None = None,
    force: bool = False,
    now: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if not VIEW_NAME_RE.match(name or ""):
        raise WorkRegistrationError([f"work-view:invalid-name:{name}"])
    metrics = _stats_metrics(metric)
    group_fields = _stats_group_fields(by)
    filters = _stats_where_filters(where)
    _validate_stats_fields(group_fields, filters)
    out_text = str(out or "").strip()
    if export_format and not out_text:
        raise WorkRegistrationError(["work-view:format-requires-out"])

    now_text = _now_text(now)
    payload = _load_work_views(root)
    existing = _find_view(payload, name)
    if existing and not force:
        raise WorkRegistrationError([f"work-view:exists:{name}"])
    view: dict[str, Any] = {
        "name": name,
        "created_at": str(existing.get("created_at") or now_text) if existing else now_text,
        "updated_at": now_text,
        "query": {
            "by": group_fields,
            "metrics": metrics,
            "kind": _stats_multi_values(kinds),
            "status": _stats_multi_values(statuses),
            "where": [f"{key}={value}" for key, value in filters],
        },
    }
    if out_text:
        view["export"] = {
            "format": _stats_export_format(export_format, Path(out_text)),
            "out": Path(out_text).as_posix(),
        }
    payload["schema"] = WORK_VIEWS_SCHEMA
    payload["updated_at"] = now_text
    payload["views"] = sorted(
        [item for item in payload["views"] if str(item.get("name") or "") != name] + [view],
        key=lambda item: str(item.get("name") or ""),
    )
    views_path = root / WORK_VIEWS_PATH
    views_path.parent.mkdir(parents=True, exist_ok=True)
    views_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "updated" if existing else "saved",
        "name": name,
        "path": _rel(root, views_path),
        "view": view,
    }


def run_view(
    root: Path,
    name: str,
    *,
    now: str | None = None,
    out: str | None = None,
    export_format: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    payload = _load_work_views(root)
    view = _find_view(payload, name)
    if view is None:
        raise WorkRegistrationError([f"work-view:not-found:{name}"])
    query = view.get("query") if isinstance(view.get("query"), dict) else {}
    export = view.get("export") if isinstance(view.get("export"), dict) else {}
    effective_out = str(out or "").strip() or str(export.get("out") or "").strip() or None
    effective_format = str(export_format or "").strip() or str(export.get("format") or "").strip() or None
    result = _execute_stats_query(
        root,
        by=",".join(_text_lines(query.get("by"))) or None,
        metric=",".join(_text_lines(query.get("metrics"))) or "count",
        kinds=_text_lines(query.get("kind")),
        statuses=_text_lines(query.get("status")),
        where=_text_lines(query.get("where")),
        now=now,
        out=effective_out,
        export_format=effective_format,
    )
    result["view"] = name
    return result


def list_views(root: Path) -> dict[str, Any]:
    root = root.resolve()
    payload = _load_work_views(root)
    views = sorted(payload["views"], key=lambda item: str(item.get("name") or ""))
    return {
        "status": "pass",
        "path": _rel(root, root / WORK_VIEWS_PATH),
        "view_count": len(views),
        "views": views,
    }


def _stats_flat_headers(result: dict[str, Any]) -> list[str]:
    metrics = list(result.get("metrics") or ["count"])
    headers = list(result["group_by"]) + ["count"]
    if len(metrics) == 1:
        headers.extend(STATS_ROW_AGGREGATES)
    else:
        for name in metrics:
            headers.extend(f"{name}_{aggregate}" for aggregate in STATS_ROW_AGGREGATES)
    return headers


def _stats_flat_row(result: dict[str, Any], row: dict[str, Any]) -> dict[str, str]:
    metrics = list(result.get("metrics") or ["count"])
    values = {field: str(row["group"].get(field, "")) for field in result["group_by"]}
    values["count"] = str(row["count"])
    for name in metrics:
        stats = row["metrics"][name]
        prefix = "" if len(metrics) == 1 else f"{name}_"
        for aggregate in STATS_ROW_AGGREGATES:
            number = stats[aggregate]
            values[f"{prefix}{aggregate}"] = "" if number is None else str(number)
    return values


def _print_stats_csv(result: dict[str, Any]) -> None:
    # Write CSV bytes as UTF-8 regardless of the console encoding so cp949
    # consoles neither mangle non-ASCII group values nor crash on them.
    buffer = getattr(sys.stdout, "buffer", None)
    stream = io.TextIOWrapper(buffer, encoding="utf-8", newline="") if buffer is not None else sys.stdout
    writer = csv.DictWriter(stream, fieldnames=_stats_flat_headers(result), lineterminator="\n")
    writer.writeheader()
    for row in result["rows"]:
        writer.writerow(_stats_flat_row(result, row))
    if stream is not sys.stdout:
        stream.flush()
        stream.detach()  # keep the underlying stdout buffer open


def _print_stats_table(result: dict[str, Any]) -> None:
    headers = _stats_flat_headers(result)
    print(f"work-stats: {result['status']}")
    print(f"metric={result['metric']}")
    print(f"total_items={result['total_items']}")
    if result.get("export"):
        print(f"export={result['export']} ({result.get('export_format')}, {result.get('export_items')} items)")
    print("\t".join(headers))
    for row in result["rows"]:
        values = _stats_flat_row(result, row)
        print("\t".join(values.get(header, "") for header in headers))


def cmd_new(args: argparse.Namespace) -> int:
    try:
        result = register(args.root, args.input, now=args.now)
    except WorkRegistrationError as exc:
        print("work-new: fail", file=sys.stderr)
        print(f"findings={len(exc.findings)}", file=sys.stderr)
        for finding in exc.findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print("work-new: pass")
    if args.no_plan_snapshot:
        print(
            "plan-snapshot: skipped (--no-plan-snapshot); record one before dispatch:"
            " python scripts/plan_assumption_gate.py record --taskset <id>"
            " --design-record <review> --anchor <path>"
        )
        result["plan_snapshot"] = {"status": "skipped", "reason": "--no-plan-snapshot"}
    elif result.get("status") != "created":
        print("plan-snapshot: skipped (records already existed; existing snapshot preserved)")
        result["plan_snapshot"] = {"status": "skipped", "reason": "already_exists"}
    else:
        result["plan_snapshot"] = record_plan_snapshot(args.root, args.input, result)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}={value}")
    return 0


def cmd_now(args: argparse.Namespace) -> int:
    print(now_util.value(utc=args.utc, date=args.date, epoch=args.epoch))
    return 0


def _ascii_status(value: Any) -> str:
    return str(value if value is not None else "").encode("ascii", "replace").decode("ascii")


def _git_worktrees(root: Path) -> list[dict[str, str]] | None:
    """List git worktrees for root; None when git/worktree info is unavailable."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, FileNotFoundError):
        return None
    if proc.returncode != 0:
        return None
    worktrees: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue
        if line.startswith("worktree "):
            if current:
                worktrees.append(current)
            current = {"path": line[len("worktree "):], "branch": ""}
        elif line.startswith("branch ") and current:
            branch = line[len("branch "):]
            if branch.startswith("refs/heads/"):
                branch = branch[len("refs/heads/"):]
            current["branch"] = branch
        elif line == "detached" and current:
            current["branch"] = "(detached)"
    if current:
        worktrees.append(current)
    return worktrees


def _active_claim_rows(root: Path) -> list[dict[str, Any]]:
    claims_dir = root / "agents" / "runtime" / "task_claims"
    rows: list[dict[str, Any]] = []
    if claims_dir.is_dir():
        for path in sorted(claims_dir.glob("*.json"), key=lambda item: item.name.lower()):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict):
                continue
            if str(payload.get("status") or "").strip().lower() not in ACTIVE_CLAIM_STATUSES:
                continue
            rows.append(
                {
                    "task_id": str(payload.get("task_id") or ""),
                    "task_set_id": str(payload.get("task_set_id") or ""),
                    "claim_id": str(payload.get("claim_id") or path.stem),
                    "status": str(payload.get("status") or ""),
                    "agent": str(payload.get("display_name") or payload.get("agent_instance_id") or ""),
                    "worktree_path": str(payload.get("worktree_path") or ""),
                    "path": _rel(root, path),
                }
            )
    rows.sort(key=lambda row: (row["task_id"], row["claim_id"]))
    return rows


def status_work(root: Path) -> dict[str, Any]:
    """W0 session-start visibility: active claims + worktrees + in-flight branches.

    Read-only. This is the lifecycle entrypoint: never start on a problem
    that already has an active claim here.
    """
    overlay = inflight_overlay.build_overlay(root)
    return {
        "status": "ok",
        "root": str(root),
        "active_claims": _active_claim_rows(root),
        "worktrees": _git_worktrees(root),
        "inflight": {
            "summary": inflight_overlay.summary_line(overlay),
            "counts": overlay.get("summary", {}),
        },
    }


def cmd_status(args: argparse.Namespace) -> int:
    result = status_work(args.root)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    print("work-status: ok")
    print(f"root={_ascii_status(result['root'])}")
    claims = result["active_claims"]
    print(f"active_claims={len(claims)}")
    for claim in claims:
        print(
            f"- task={_ascii_status(claim['task_id'])}"
            f" status={_ascii_status(claim['status'])}"
            f" agent={_ascii_status(claim['agent'])}"
            f" claim={_ascii_status(claim['claim_id'])}"
            f" worktree={_ascii_status(claim['worktree_path'])}"
        )
    worktrees = result["worktrees"]
    if worktrees is None:
        print("worktrees=unavailable")
    else:
        print(f"worktrees={len(worktrees)}")
        for tree in worktrees:
            print(f"- path={_ascii_status(tree['path'])} branch={_ascii_status(tree.get('branch'))}")
    print(_ascii_status(result["inflight"]["summary"]))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        result = verify_work(args.root, args.work_id, actor=args.actor, now=args.now, timeout=args.timeout)
    except WorkRegistrationError as exc:
        print("work-verify: fail", file=sys.stderr)
        print(f"findings={len(exc.findings)}", file=sys.stderr)
        for finding in exc.findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print(f"work-verify: {result['status']}")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            if key != "commands":
                print(f"{key}={value}")
    return 0 if result["status"] == "passed" else 1


def cmd_criteria(args: argparse.Namespace) -> int:
    try:
        result = criteria_work(
            args.root,
            args.work_id,
            actor=args.actor,
            now=args.now,
            outbox=args.outbox,
            draft_dir=args.draft_dir,
        )
    except WorkRegistrationError as exc:
        print("work-criteria: fail", file=sys.stderr)
        print(f"findings={len(exc.findings)}", file=sys.stderr)
        for finding in exc.findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print(f"work-criteria: {result['status']}")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            if key != "criteria":
                print(f"{key}={value}")
    return 0


def cmd_assign(args: argparse.Namespace) -> int:
    try:
        result = assign_work(
            args.root,
            args.work_id,
            actor=args.actor,
            now=args.now,
            outbox=args.outbox,
            draft_dir=args.draft_dir,
        )
    except WorkRegistrationError as exc:
        print("work-assign: fail", file=sys.stderr)
        print(f"findings={len(exc.findings)}", file=sys.stderr)
        for finding in exc.findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print(f"work-assign: {result['status']}")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            if key != "workload":
                print(f"{key}={value}")
    return 0


def cmd_split(args: argparse.Namespace) -> int:
    try:
        result = split_work(
            args.root,
            args.task_id,
            actor=args.actor,
            now=args.now,
            outbox=args.outbox,
            draft_dir=args.draft_dir,
        )
    except WorkRegistrationError as exc:
        print("work-split: fail", file=sys.stderr)
        print(f"findings={len(exc.findings)}", file=sys.stderr)
        for finding in exc.findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print(f"work-split: {result['status']}")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            if key not in {"existing_units", "readiness_findings"}:
                print(f"{key}={value}")
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    try:
        result = close_work(
            args.root,
            args.work_id,
            actor=args.actor,
            resolution=args.resolution,
            actual_hours=args.actual_hours,
            actual_tokens=args.actual_tokens,
            actual_cost=args.actual_cost,
            now=args.now,
        )
    except WorkRegistrationError as exc:
        print("work-close: fail", file=sys.stderr)
        print(f"findings={len(exc.findings)}", file=sys.stderr)
        for finding in exc.findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print(f"work-close: {result['status']}")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}={value}")
    return 0


def _print_findings(command: str, exc: WorkRegistrationError) -> None:
    print(f"{command}: fail", file=sys.stderr)
    print(f"findings={len(exc.findings)}", file=sys.stderr)
    for finding in exc.findings:
        print(f"- {finding}", file=sys.stderr)


def _combined_filters(args: argparse.Namespace) -> list[str]:
    return list(args.where or []) + list(args.filter or [])


def cmd_stats(args: argparse.Namespace) -> int:
    try:
        result = _execute_stats_query(
            args.root,
            by=args.by,
            metric=args.metric,
            kinds=args.kind,
            statuses=args.status,
            where=_combined_filters(args),
            now=args.now,
            out=str(args.out) if args.out else None,
            export_format=args.format,
        )
    except WorkRegistrationError as exc:
        _print_findings("work-stats", exc)
        return 1
    if args.csv:
        _print_stats_csv(result)
    elif args.json:
        print(f"work-stats: {result['status']}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_stats_table(result)
    return 0


def cmd_view_save(args: argparse.Namespace) -> int:
    try:
        result = save_view(
            args.root,
            args.name,
            by=args.by,
            metric=args.metric,
            kinds=args.kind,
            statuses=args.status,
            where=_combined_filters(args),
            export_format=args.format,
            out=str(args.out) if args.out else None,
            force=args.force,
            now=args.now,
        )
    except WorkRegistrationError as exc:
        _print_findings("work-view-save", exc)
        return 1
    print(f"work-view-save: {result['status']}")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"name={result['name']}")
        print(f"path={result['path']}")
    return 0


def cmd_view_run(args: argparse.Namespace) -> int:
    try:
        result = run_view(
            args.root,
            args.name,
            now=args.now,
            out=str(args.out) if args.out else None,
            export_format=args.format,
        )
    except WorkRegistrationError as exc:
        _print_findings("work-view-run", exc)
        return 1
    if args.csv:
        _print_stats_csv(result)
    elif args.json:
        print(f"work-view-run: {result['status']}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"work-view-run: view={result['view']}")
        _print_stats_table(result)
    return 0


def cmd_view_list(args: argparse.Namespace) -> int:
    try:
        result = list_views(args.root)
    except WorkRegistrationError as exc:
        _print_findings("work-view-list", exc)
        return 1
    print(f"work-view-list: {result['status']}")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"path={result['path']}")
        print(f"view_count={result['view_count']}")
        for view in result["views"]:
            query = view.get("query") if isinstance(view.get("query"), dict) else {}
            summary = json.dumps(query, ensure_ascii=False, sort_keys=True)
            print(f"- {view.get('name')}: {summary}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and manage Work Items")
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    no_snapshot_help = (
        "Opt out of the automatic T0 plan-assumption snapshot (discouraged); "
        "without a snapshot the T2 dispatch drift check has nothing to verify"
    )
    new = sub.add_parser("new", help="Create work records from structured JSON input")
    new.add_argument("--input", type=Path, required=True)
    new.add_argument("--now")
    new.add_argument("--no-plan-snapshot", action="store_true", help=no_snapshot_help)
    new.add_argument("--json", action="store_true")
    new.set_defaults(func=cmd_new)

    register_cmd = sub.add_parser("register", help="Alias for new")
    register_cmd.add_argument("--input", type=Path, required=True)
    register_cmd.add_argument("--now")
    register_cmd.add_argument("--no-plan-snapshot", action="store_true", help=no_snapshot_help)
    register_cmd.add_argument("--json", action="store_true")
    register_cmd.set_defaults(func=cmd_new)

    status_cmd = sub.add_parser(
        "status",
        help=(
            "W0 session-start visibility: active claims, git worktrees, and "
            "in-flight (unmerged agent branch) divergence in one read-only view"
        ),
    )
    status_cmd.add_argument("--json", action="store_true")
    status_cmd.set_defaults(func=cmd_status)

    now_cmd = sub.add_parser("now", help="Print the canonical project timestamp")
    now_group = now_cmd.add_mutually_exclusive_group()
    now_group.add_argument("--utc", action="store_true", help="UTC timestamp with Z suffix")
    now_group.add_argument("--date", action="store_true", help="local date only, YYYY-MM-DD")
    now_group.add_argument("--epoch", action="store_true", help="Unix epoch seconds")
    now_cmd.set_defaults(func=cmd_now)

    verify_cmd = sub.add_parser("verify", help="Run a work item's verification commands and write evidence")
    verify_cmd.add_argument("work_id", help="Unit ID, task ID, or path to a verifiable work item")
    verify_cmd.add_argument("--actor", default="work.py verify")
    verify_cmd.add_argument("--now")
    verify_cmd.add_argument("--timeout", type=int, default=300)
    verify_cmd.add_argument("--json", action="store_true")
    verify_cmd.set_defaults(func=cmd_verify)

    criteria_cmd = sub.add_parser("criteria", help="Evaluate criteria verifiability and write B-mode proposals for gaps")
    criteria_cmd.add_argument("work_id", help="Unit ID, task ID, or path to a work item")
    criteria_cmd.add_argument("--actor", default="work.py criteria")
    criteria_cmd.add_argument("--now")
    criteria_cmd.add_argument("--outbox", type=Path)
    criteria_cmd.add_argument("--draft-dir", type=Path)
    criteria_cmd.add_argument("--json", action="store_true")
    criteria_cmd.set_defaults(func=cmd_criteria)

    assign_cmd = sub.add_parser("assign", help="Recommend team/owner assignment and write B-mode proposals for gaps")
    assign_cmd.add_argument("work_id", help="Unit ID, task ID, or path to a work item")
    assign_cmd.add_argument("--actor", default="work.py assign")
    assign_cmd.add_argument("--now")
    assign_cmd.add_argument("--outbox", type=Path)
    assign_cmd.add_argument("--draft-dir", type=Path)
    assign_cmd.add_argument("--json", action="store_true")
    assign_cmd.set_defaults(func=cmd_assign)

    split_cmd = sub.add_parser("split", help="Propose worker-ready unit specs for a task without canonical unit files")
    split_cmd.add_argument("task_id", help="Task ID or path to a task work item")
    split_cmd.add_argument("--actor", default="work.py split")
    split_cmd.add_argument("--now")
    split_cmd.add_argument("--outbox", type=Path)
    split_cmd.add_argument("--draft-dir", type=Path)
    split_cmd.add_argument("--json", action="store_true")
    split_cmd.set_defaults(func=cmd_split)

    close_cmd = sub.add_parser("close", help="Close a work item after passed verification evidence")
    close_cmd.add_argument("work_id", help="Unit ID, task ID, or path to a work item")
    close_cmd.add_argument("--actor", default="work.py close")
    close_cmd.add_argument("--resolution", choices=sorted(RESOLUTION_VALUES), default="done")
    close_cmd.add_argument("--actual-hours")
    close_cmd.add_argument("--actual-tokens", type=int)
    close_cmd.add_argument("--actual-cost")
    close_cmd.add_argument("--now")
    close_cmd.add_argument("--json", action="store_true")
    close_cmd.set_defaults(func=cmd_close)

    def add_stats_query_arguments(target: argparse.ArgumentParser) -> None:
        target.add_argument("--by", help=f"Comma-separated group-by dimensions: {', '.join(sorted(STATS_DIMENSIONS))}")
        target.add_argument(
            "--metric",
            default="count",
            help=f"Comma-separated metrics to aggregate: {', '.join(sorted(STATS_METRICS))}",
        )
        target.add_argument("--kind", action="append", help="Filter by kind; accepts comma-separated values and may repeat")
        target.add_argument("--status", action="append", help="Filter by status; accepts comma-separated values and may repeat")
        target.add_argument("--filter", action="append", help="Filter by exact field=value; may repeat")
        target.add_argument("--where", action="append", help="Alias of --filter; may repeat")
        target.add_argument("--format", choices=sorted(STATS_EXPORT_FORMATS), help="Export format for --out (default inferred from suffix)")
        target.add_argument("--out", type=Path, help="Export matched item rows to this path (relative paths resolve under --root)")
        target.add_argument("--now", help="Override the timestamp used for computed metrics such as age")

    stats_cmd = sub.add_parser("stats", help="Aggregate v1 Work Item metadata without mutating files")
    add_stats_query_arguments(stats_cmd)
    output_group = stats_cmd.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true")
    output_group.add_argument("--csv", action="store_true")
    stats_cmd.set_defaults(func=cmd_stats)

    view_cmd = sub.add_parser("view", help="Save, list, and run reusable work stats views")
    view_sub = view_cmd.add_subparsers(dest="view_command", required=True)

    view_save = view_sub.add_parser("save", help="Persist a stats query as a named view in WORK-VIEWS.json")
    view_save.add_argument("name", help="View name (letters, digits, dot, dash, underscore)")
    add_stats_query_arguments(view_save)
    view_save.add_argument("--force", action="store_true", help="Overwrite an existing view with the same name")
    view_save.add_argument("--json", action="store_true")
    view_save.set_defaults(func=cmd_view_save)

    view_run = view_sub.add_parser("run", help="Execute a saved view exactly as stored")
    view_run.add_argument("name", help="Saved view name")
    view_run.add_argument("--format", choices=sorted(STATS_EXPORT_FORMATS), help="Override the saved export format")
    view_run.add_argument("--out", type=Path, help="Override the saved export path")
    view_run.add_argument("--now", help="Override the timestamp used for computed metrics such as age")
    run_output_group = view_run.add_mutually_exclusive_group()
    run_output_group.add_argument("--json", action="store_true")
    run_output_group.add_argument("--csv", action="store_true")
    view_run.set_defaults(func=cmd_view_run)

    view_list = view_sub.add_parser("list", help="List saved views")
    view_list.add_argument("--json", action="store_true")
    view_list.set_defaults(func=cmd_view_list)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.root = args.root.resolve()
    if hasattr(args, "input") and not args.input.is_absolute():
        args.input = (Path.cwd() / args.input).resolve()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
