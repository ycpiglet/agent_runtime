"""Validate worker-ready task unit specifications."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import backlog_board


READY_STATUSES = {"worker_ready", "ready", "in_progress", "completed"}
ACTIVE_WORKER_STATUSES = {"assigned", "claimed", "in_progress", "working"}
REQUIRED_META = {
    "unit_id",
    "task_id",
    "task_set_id",
    "project_id",
    "status",
    "model_tier",
    "context",
    "inputs",
    "target_files",
    "scope",
    "acceptance",
    "verification",
    "handoff",
    "stop_condition",
}
REQUIRED_SECTIONS = {
    "context": "Context",
    "inputs": "Inputs",
    "target_files": "Target Files",
    "scope": "Scope",
    "steps": "Steps",
    "acceptance": "Acceptance Criteria",
    "verification": "Verification",
    "handoff": "Handoff",
    "stop_boundary": "Stop Boundary",
}


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


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


def _has_text(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    return bool(str(value).strip())


def depends_on_refs(meta: dict[str, Any]) -> list[str]:
    """Return the optional `depends_on` references (unit and/or task ids)."""
    value = meta.get("depends_on")
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def load_unit_specs(root: Path) -> list[tuple[Path, dict[str, Any], str]]:
    base = root / "agents" / "lead_engineer" / "tasks" / "units"
    if not base.is_dir():
        return []
    units: list[tuple[Path, dict[str, Any], str]] = []
    for path in sorted(base.glob("TASK-*/UNIT-*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = backlog_board.parse_frontmatter(text)
        units.append((path, meta, body))
    return units


def _load_claims(root: Path) -> list[dict[str, Any]]:
    claim_dir = root / "agents" / "runtime" / "task_claims"
    if not claim_dir.is_dir():
        return []
    claims: list[dict[str, Any]] = []
    for path in sorted(claim_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            payload["_path"] = path
            claims.append(payload)
    return claims


def validate_unit(root: Path, path: Path, meta: dict[str, Any], body: str, *, require_ready: bool = False) -> list[str]:
    findings: list[str] = []
    rel = _rel(root, path)
    missing = sorted(field for field in REQUIRED_META if not _has_text(meta.get(field)))
    for field in missing:
        findings.append(f"{rel}: unit:missing-field:{field}")

    status = str(meta.get("status") or "").strip()
    if require_ready and status not in READY_STATUSES:
        findings.append(f"{rel}: unit:not-worker-ready:{status or 'missing-status'}")

    sections = _section_blocks(body)
    for key, display in REQUIRED_SECTIONS.items():
        normalized = display.lower()
        if not _has_text(sections.get(normalized)):
            findings.append(f"{rel}: unit:missing-section:{key}")

    unit_task = str(meta.get("task_id") or "").strip()
    if unit_task and f"/{unit_task}/" not in rel:
        findings.append(f"{rel}: unit:path-task-mismatch:{unit_task}")
    return findings


def _depends_on_findings(
    root: Path,
    units: list[tuple[Path, dict[str, Any], str]],
    selected_units: list[tuple[Path, dict[str, Any], str]],
) -> list[str]:
    """Validate optional `depends_on` references against known unit/task ids."""
    findings: list[str] = []
    known_unit_ids = {str(meta.get("unit_id") or "").strip() for _, meta, _ in units}
    known_unit_ids.discard("")
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    for path, meta, _body in selected_units:
        rel = _rel(root, path)
        own_unit_id = str(meta.get("unit_id") or "").strip()
        for ref in depends_on_refs(meta):
            if own_unit_id and ref == own_unit_id:
                findings.append(f"{rel}: unit:depends-on-self:{ref}")
            elif ref not in known_unit_ids and not (tasks_dir / f"{ref}.md").is_file():
                findings.append(f"{rel}: unit:depends-on-unknown-ref:{ref}")
    return findings


def _task_units(units: list[tuple[Path, dict[str, Any], str]], task_id: str) -> list[tuple[Path, dict[str, Any], str]]:
    return [unit for unit in units if str(unit[1].get("task_id") or "").strip() == task_id]


def _active_worker_tasks_from_claims(root: Path) -> set[str]:
    tasks: set[str] = set()
    for claim in _load_claims(root):
        status = str(claim.get("status") or "").strip().lower()
        model_tier = str(claim.get("model_tier") or "").strip()
        task_id = str(claim.get("task_id") or "").strip()
        if task_id and status in ACTIVE_WORKER_STATUSES and model_tier.startswith("worker_"):
            tasks.add(task_id)
    return tasks


def check_root(
    root: Path,
    *,
    task_id: str = "",
    unit_id: str = "",
    require_ready: bool = False,
    strict_migration: bool = False,
) -> list[str]:
    root = root.resolve()
    units = load_unit_specs(root)
    findings: list[str] = []

    selected_units = units
    if task_id:
        selected_units = _task_units(units, task_id)
        if not selected_units:
            findings.append(f"agents/lead_engineer/tasks/{task_id}.md: unit:no-unit-spec:{task_id}")
    if unit_id:
        selected_units = [unit for unit in selected_units if str(unit[1].get("unit_id") or "") == unit_id]
        if not selected_units:
            findings.append(f"unit:no-matching-unit-id:{unit_id}")

    for path, meta, body in selected_units:
        findings.extend(validate_unit(root, path, meta, body, require_ready=require_ready))

    findings.extend(_depends_on_findings(root, units, selected_units))

    if strict_migration:
        tasks = backlog_board.load_tasks(root / "agents" / "lead_engineer" / "tasks")
        for task in tasks:
            status = str(task.meta.get("status") or "").strip().lower()
            worker_tier = str(task.meta.get("worker_model_tier") or "").strip()
            if status in {"planned", *ACTIVE_WORKER_STATUSES} and worker_tier.startswith("worker_"):
                if not _task_units(units, task.task_id):
                    findings.append(f"{_rel(root, task.path)}: unit:migration-missing-unit-spec:{task.task_id}")

    for active_task_id in sorted(_active_worker_tasks_from_claims(root)):
        if not _task_units(units, active_task_id):
            findings.append(f"agents/lead_engineer/tasks/{active_task_id}.md: unit:active-worker-missing-unit-spec")

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task unit readiness gate")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--task-id", default="")
    parser.add_argument("--unit-id", default="")
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--strict-migration", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    findings = check_root(
        args.root,
        task_id=args.task_id,
        unit_id=args.unit_id,
        require_ready=args.require_ready,
        strict_migration=args.strict_migration,
    )
    status = "fail" if findings else "pass"
    print(f"task-unit-readiness-gate: {status}")
    print(f"root={args.root.resolve()}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
