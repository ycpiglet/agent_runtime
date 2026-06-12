"""Deterministic Work Item registration CLI.

This is the scaffolded, non-LLM path for planner-approved work intake. It
creates stable records first; generated views such as hierarchy numbers and the
backlog board are refreshed afterward.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import backlog_board
import evidence_index_generator
import task_identity
import work_item_classifier


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_SCHEMA = "agent-runtime-work-registration/v1"
WORK_ITEM_SCHEMA = "agent-runtime-work-item/v1"
TASKSET_REGISTRY_SCHEMA = "agent-runtime-taskset-definitions/v1"
TASKSET_REGISTRY_PATH = Path("agents/project/work-items/TASKSET-DEFINITIONS.json")
TASKS_DIR = Path("agents/lead_engineer/tasks")
INITIATIVES_DIR = Path("agents/project/initiatives")
PLANS_DIR = Path("docs/superpowers/plans")
REVIEWS_DIR = Path("reviews")
OWNER_DOCS_PATH = Path("owner-docs.yml")
RESERVATION_TTL_SECONDS = 86400
TASK_DISPLAY_RE = re.compile(r"^TASK-AR-\d+$")


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
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


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


def _title_from_task(task: dict[str, Any], display_id: str) -> str:
    return str(task.get("title") or display_id).strip()


def _task_path(root: Path, display_id: str) -> Path:
    return root / TASKS_DIR / f"{display_id}.md"


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
`{taskset['id']}`, and `{len(tasks)}` task records from one input file.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Input schema | pass | `{REGISTRATION_SCHEMA}` |
| Reservation ledger | pass | task display IDs fulfilled during registration |
| Generated records | pass | initiative, taskset plan, task files, and generated views refreshed |

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
- Additional work is still needed for units and closeout automation.

## Next

- Run `python scripts/work_item_classifier.py --check` and
  `python scripts/taskset_work_gate.py --check` before handoff.
- Keep AI `split`, `criteria`, and `assign` tools behind B-mode proposal review.
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


def _preflight_existing(
    root: Path,
    initiative: dict[str, Any],
    taskset: dict[str, Any],
    tasks: list[dict[str, Any]],
    initiative_path: Path,
    plan_path: Path,
    review_path: Path,
) -> str:
    targets = [initiative_path, plan_path, review_path, *[_task_path(root, str(task["display_id"])) for task in tasks]]
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
            }

        prepared_tasks: list[dict[str, Any]] = []
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
        "reservation_group_id": group_id,
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.root = args.root.resolve()
    if not args.input.is_absolute():
        args.input = (Path.cwd() / args.input).resolve()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
