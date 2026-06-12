"""Deterministic Work Item registration CLI.

This is the scaffolded, non-LLM path for planner-approved work intake. It
creates stable records first; generated views such as hierarchy numbers and the
backlog board are refreshed afterward.
"""

from __future__ import annotations

import argparse
import hashlib
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
import now as now_util
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


def _frontmatter(meta: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif value is not None and str(value) != "":
            lines.append(f"{key}: {value}")
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
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}={value}")
    return 0


def cmd_now(args: argparse.Namespace) -> int:
    print(now_util.value(utc=args.utc, date=args.date, epoch=args.epoch))
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and manage Work Items")
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="Create work records from structured JSON input")
    new.add_argument("--input", type=Path, required=True)
    new.add_argument("--now")
    new.add_argument("--json", action="store_true")
    new.set_defaults(func=cmd_new)

    register_cmd = sub.add_parser("register", help="Alias for new")
    register_cmd.add_argument("--input", type=Path, required=True)
    register_cmd.add_argument("--now")
    register_cmd.add_argument("--json", action="store_true")
    register_cmd.set_defaults(func=cmd_new)

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
