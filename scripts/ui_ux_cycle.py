"""UI/UX continuous improvement cycle conductor.

This command is intentionally read-first. It does not implement UI changes and
does not fabricate seminar or beta-tester evidence. It composes current repo
signals into a stable assessment that can pick the next UI refactor, name the
required review roles, and plan a report artifact for the next implementation
cycle.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import backlog_board  # noqa: E402


ASSESS_SCHEMA = "agent-runtime-ui-ux-cycle-assessment/v1"
REPORT_SCHEMA = "agent-runtime-ui-ux-cycle-report/v1"
ACTIVE_CLAIM_STATUSES = {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}
OPEN_TASK_STATUSES = {"planned", "worker_ready", "claimed", "in_progress", "review", "waiting_review", "working"}
UI_ROLE_IDS = ("lead-designer", "design-system-steward", "interface-designer", "ux-evaluator")
CYCLE_TASKSET_ID = "TASKSET-AR-UI-UX-CYCLE-AUTOMATION"
UI_TASKSET_PRIORITY = (
    "TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION",
    "TASKSET-AR-UI-DESIGN-IMPLEMENTATION",
    "TASKSET-AR-UI-DESIGN-SYSTEM",
    "TASKSET-AR-UI-UX-V2",
    "TASKSET-AR-UI-PLATFORM-EXTENSIONS",
    "TASKSET-AR-UI-LIVING-CONSOLE",
)
KNOWN_UI_FILE_MAP = {
    "DESIGN-SYSTEM.md": "docs/design/agent-runtime/DESIGN-SYSTEM.md",
    "design_system_gate.py": "scripts/design_system_gate.py",
    "test_design_system_gate.py": "tests/test_design_system_gate.py",
    "test_ui_console.py": "tests/test_ui_console.py",
    "test_ui_design_assets.py": "tests/test_ui_design_assets.py",
    "ui_console.py": "src/agent_runtime/ui_console.py",
    "ui_console_assets.py": "src/agent_runtime/ui_console_assets.py",
    "ui_design_assets.py": "src/agent_runtime/ui_design_assets.py",
}

QUALITY_DIMENSIONS = [
    ("typography", "Font family, type scale, weight, line-height, truncation, and reading density."),
    ("size_spacing", "Spacing, component sizing, density modes, responsive constraints, and touch targets."),
    ("color", "Theme tokens, semantic status colors, contrast, and non-color status cues."),
    ("motion", "Animation duration, easing, reduced-motion behavior, and live-state movement."),
    ("effects", "Shadow, border, focus, hover, depth, loading, and transition effects."),
    ("schema", "State/API schema, task metadata, route contracts, and write boundaries."),
    ("assets", "Design tokens, UI components, pattern components, icons, and served assets."),
    ("accessibility", "Keyboard flow, focus order, labels, landmarks, contrast, and screen-reader state."),
    ("responsiveness", "Desktop/mobile layout, overflow, wrapping, stable dimensions, and viewport fit."),
    ("interaction", "Core workflows, error recovery, empty states, beta-tester click/type paths, and undo/safety affordances."),
]

BETA_TESTER_REQUIREMENTS = [
    "Record what was clicked or typed, not just DOM presence.",
    "Exercise edge cases and recovery attempts.",
    "Capture environment, viewport, and data state.",
    "Create BTC-style failure IDs for user-visible defects.",
    "Attach or reference multi-step evidence; a single screenshot is not enough.",
]


def _parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).astimezone()
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _today(now: datetime) -> str:
    return now.date().isoformat()


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _frontmatter(path: Path) -> dict[str, Any]:
    text = _read_text(path)
    if not text:
        return {}
    meta, _body = backlog_board.parse_frontmatter(text)
    return dict(meta)


def _normalize_paths(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted({str(value).replace("\\", "/").strip() for value in values if str(value).strip()})


def _infer_target_files(text: str) -> list[str]:
    found: set[str] = set()
    for basename, rel in KNOWN_UI_FILE_MAP.items():
        if basename in text:
            found.add(rel)
    return sorted(found)


def _priority_rank(value: Any) -> int:
    text = str(value or "").upper()
    if text.startswith("P") and text[1:].isdigit():
        return int(text[1:])
    return 9


def _task_number(task_id: str) -> int:
    try:
        return int(task_id.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 999999


def _is_ui_task(meta: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(meta.get(key) or "")
        for key in ("id", "title", "summary", "task_set_id", "initiative_id", "team", "owner")
    ).lower()
    if str(meta.get("team") or "").lower() == "ui-ux":
        return True
    return any(token in haystack for token in ("ui", "ux", "design", "console", "component", "token", "pattern"))


def _is_refactor_candidate(meta: dict[str, Any]) -> bool:
    taskset = str(meta.get("task_set_id") or "")
    title = str(meta.get("title") or "").lower()
    summary = str(meta.get("summary") or "").lower()
    if taskset == "TASKSET-AR-UI-UX-CYCLE-AUTOMATION":
        return False
    return any(token in " ".join([taskset.lower(), title, summary]) for token in ("design-system", "refactor", "token", "renderer", "component", "pattern", "ui"))


def _load_tasks(root: Path) -> list[dict[str, Any]]:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks: list[dict[str, Any]] = []
    if not tasks_dir.is_dir():
        return tasks
    for path in sorted(tasks_dir.glob("TASK-*.md"), key=lambda item: item.name):
        text = _read_text(path)
        meta = _frontmatter(path)
        task_id = str(meta.get("id") or meta.get("work_id") or path.stem)
        status = str(meta.get("status") or "").strip()
        if status not in OPEN_TASK_STATUSES or not _is_ui_task(meta):
            continue
        tasks.append(
            {
                "task_id": task_id,
                "title": str(meta.get("title") or task_id),
                "task_set_id": str(meta.get("task_set_id") or ""),
                "status": status,
                "priority": str(meta.get("priority") or ""),
                "team": str(meta.get("team") or ""),
                "owner": str(meta.get("owner") or ""),
                "path": _rel(root, path),
                "target_files": _normalize_paths(meta.get("target_files")) or _infer_target_files(text),
                "is_refactor_candidate": _is_refactor_candidate(meta),
            }
        )
    return tasks


def _load_active_claims(root: Path) -> list[dict[str, Any]]:
    claims_dir = root / "agents" / "runtime" / "task_claims"
    claims: list[dict[str, Any]] = []
    if not claims_dir.is_dir():
        return claims
    for path in sorted(claims_dir.glob("*.json"), key=lambda item: item.name):
        payload = _read_json(path)
        status = str(payload.get("status") or "").strip()
        if status not in ACTIVE_CLAIM_STATUSES:
            continue
        claims.append(
            {
                "claim_id": str(payload.get("claim_id") or path.stem),
                "task_id": str(payload.get("task_id") or ""),
                "status": status,
                "agent_role": str(payload.get("agent_role") or ""),
                "task_set_id": str(payload.get("task_set_id") or ""),
                "target_files": _normalize_paths(payload.get("target_files")),
                "path": _rel(root, path),
            }
        )
    return claims


def _conflicts(candidate: dict[str, Any], claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target_files = set(candidate.get("target_files") or [])
    if not target_files:
        return []
    conflicts: list[dict[str, Any]] = []
    for claim in claims:
        overlap = sorted(target_files & set(claim.get("target_files") or []))
        if overlap:
            conflicts.append(
                {
                    "claim_id": claim["claim_id"],
                    "task_id": claim["task_id"],
                    "task_set_id": claim.get("task_set_id") or "",
                    "status": claim["status"],
                    "cycle_claim": claim.get("task_set_id") == CYCLE_TASKSET_ID,
                    "overlap": overlap,
                }
            )
    return conflicts


def _candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, int, int]:
    taskset = str(candidate.get("task_set_id") or "")
    taskset_rank = UI_TASKSET_PRIORITY.index(taskset) if taskset in UI_TASKSET_PRIORITY else len(UI_TASKSET_PRIORITY)
    return (taskset_rank, _priority_rank(candidate.get("priority")), _task_number(str(candidate.get("task_id") or "")))


def _next_refactor(tasks: list[dict[str, Any]], claims: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [task for task in tasks if task.get("is_refactor_candidate")]
    if not candidates:
        return {
            "status": "missing",
            "reason": "no open UI refactor candidate found",
            "task": None,
            "conflicts": [],
        }
    selected = sorted(candidates, key=_candidate_sort_key)[0]
    conflicts = _conflicts(selected, claims)
    external_conflicts = [conflict for conflict in conflicts if not conflict.get("cycle_claim")]
    if external_conflicts:
        status = "blocked_by_active_claim"
        reason = "active non-cycle claim owns overlapping target files"
    elif conflicts:
        status = "ready_after_cycle_release"
        reason = "current UI/UX cycle claim owns overlapping files until release"
    else:
        status = "ready"
        reason = "next open UI refactor candidate"
    return {
        "status": status,
        "reason": reason,
        "task": selected,
        "conflicts": conflicts,
    }


def _run_design_gate(root: Path) -> dict[str, Any]:
    gate = root / "scripts" / "design_system_gate.py"
    if not gate.exists():
        return {"status": "missing", "command": "python scripts/design_system_gate.py --all-ui --check --json", "findings": None}
    result = subprocess.run(
        [sys.executable, str(gate), "--all-ui", "--check", "--json"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {}
    return {
        "status": str(payload.get("status") or ("pass" if result.returncode == 0 else "fail")),
        "returncode": result.returncode,
        "command": "python scripts/design_system_gate.py --all-ui --check --json",
        "scanned": payload.get("scanned"),
        "findings": len(payload.get("findings") or []),
    }


def _role_coverage(root: Path) -> dict[str, Any]:
    model = root / "agents" / "project" / "ORG-MODEL.yml"
    text = model.read_text(encoding="utf-8", errors="replace") if model.exists() else ""
    roles = [{"role": role, "present": role in text} for role in UI_ROLE_IDS]
    return {"status": "pass" if all(role["present"] for role in roles) else "fail", "roles": roles}


def _recent_artifacts(root: Path, *, limit: int = 10) -> list[dict[str, Any]]:
    reviews = root / "reviews"
    if not reviews.is_dir():
        return []
    prefixes = ("MEETING-", "SEMINAR-", "REVIEW-", "RETRO-", "REPORT-", "W4B-")
    rows: list[dict[str, Any]] = []
    for path in sorted(reviews.glob("*.md"), key=lambda item: item.name, reverse=True):
        if not path.name.startswith(prefixes):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not any(token in text.lower() for token in ("ui", "ux", "design", "console", "self improvement")):
            continue
        rows.append({"path": _rel(root, path), "kind": path.name.split("-", 1)[0].lower(), "title": path.stem})
        if len(rows) >= limit:
            break
    return rows


def _quality_checklist() -> list[dict[str, str]]:
    return [{"dimension": name, "evidence_required": evidence} for name, evidence in QUALITY_DIMENSIONS]


def _review_plan(next_refactor: dict[str, Any]) -> dict[str, Any]:
    task = next_refactor.get("task") or {}
    task_id = task.get("task_id") or "next-ui-task"
    return {
        "task_id": task_id,
        "seminar": {
            "participants": ["lead-designer", "design-system-steward", "interface-designer", "ux-evaluator"],
            "purpose": "derive next UI/UX delta before implementation",
        },
        "meeting": {
            "participants": ["lead-engineer", "design-system-steward", "interface-designer"],
            "purpose": "align implementation scope, target files, and verification commands",
        },
        "beta_tester": {
            "participants": ["beta-tester", "ux-evaluator"],
            "requirements": list(BETA_TESTER_REQUIREMENTS),
        },
    }


def _cycle_score(design_gate: dict[str, Any], roles: dict[str, Any], next_refactor: dict[str, Any], artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    score = 0
    score += 30 if design_gate.get("status") == "pass" else 0
    score += 20 if roles.get("status") == "pass" else 0
    if next_refactor.get("status") == "ready":
        score += 25
    elif next_refactor.get("status") == "ready_after_cycle_release":
        score += 20
    elif next_refactor.get("task"):
        score += 10
    score += 10 if artifacts else 0
    score += 15
    if next_refactor.get("status") == "blocked_by_active_claim":
        level = "blocked"
    elif next_refactor.get("status") == "ready_after_cycle_release":
        level = "ready_after_cycle_release"
    elif score >= 85:
        level = "ready"
    elif score >= 60:
        level = "usable"
    else:
        level = "immature"
    return {"value": score, "level": level}


def assess(root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    root = root.resolve()
    timestamp = (now or datetime.now(timezone.utc).astimezone()).isoformat(timespec="seconds")
    tasks = _load_tasks(root)
    claims = _load_active_claims(root)
    design_gate = _run_design_gate(root)
    roles = _role_coverage(root)
    artifacts = _recent_artifacts(root)
    next_refactor = _next_refactor(tasks, claims)
    return {
        "schema": ASSESS_SCHEMA,
        "generated_at": timestamp,
        "root": str(root),
        "status": "blocked" if next_refactor["status"] == "blocked_by_active_claim" else next_refactor["status"],
        "score": _cycle_score(design_gate, roles, next_refactor, artifacts),
        "design_system_gate": design_gate,
        "role_coverage": roles,
        "open_ui_tasks": tasks,
        "active_claims": claims,
        "next_refactor": next_refactor,
        "quality_checklist": _quality_checklist(),
        "review_plan": _review_plan(next_refactor),
        "recent_artifacts": artifacts,
    }


def _render_report(payload: dict[str, Any], *, today: str) -> str:
    next_refactor = payload["next_refactor"]
    task = next_refactor.get("task") or {}
    lines = [
        "---",
        "type: report",
        f"id: REPORT-{today}-ui-ux-cycle",
        "status: planned",
        "tags: [ui, ux, design-system, cycle]",
        "---",
        "",
        f"# UI/UX Cycle Report {today}",
        "",
        "## Bottom Line",
        "",
        f"- Cycle readiness: `{payload['score']['level']}` at `{payload['score']['value']}/100`.",
        f"- Design-system gate: `{payload['design_system_gate']['status']}`.",
        f"- Next UI refactor: `{task.get('task_id', 'none')}` ({next_refactor['status']}).",
        "",
        "## Signal",
        "",
        "| Dimension | Evidence Required |",
        "| --- | --- |",
    ]
    for row in payload["quality_checklist"]:
        lines.append(f"| `{row['dimension']}` | {row['evidence_required']} |")
    lines.extend(["", "## Review Plan", ""])
    plan = payload["review_plan"]
    lines.append(f"- Seminar participants: {', '.join(plan['seminar']['participants'])}")
    lines.append(f"- Meeting participants: {', '.join(plan['meeting']['participants'])}")
    lines.append(f"- Beta tester participants: {', '.join(plan['beta_tester']['participants'])}")
    lines.extend(["", "## Beta Tester Evidence Requirements", ""])
    for req in plan["beta_tester"]["requirements"]:
        lines.append(f"- {req}")
    lines.extend(["", "## Decision", ""])
    if next_refactor["status"] == "ready":
        lines.append(f"- Claim and execute `{task.get('task_id')}` next, then run seminar/meeting/beta-tester review before the following implementation round.")
    elif next_refactor["status"] == "ready_after_cycle_release":
        lines.append(f"- Release the current UI/UX cycle claim, then claim and execute `{task.get('task_id')}` next.")
    elif next_refactor["status"] == "blocked_by_active_claim":
        lines.append(f"- Wait for the overlapping claim to release before claiming `{task.get('task_id')}`.")
    else:
        lines.append("- Register the next UI refactor task before another implementation cycle.")
    lines.append("")
    return "\n".join(lines)


def report(root: Path, *, now: datetime, dry_run: bool = False, overwrite: bool = False) -> dict[str, Any]:
    root = root.resolve()
    today = _today(now)
    generated_at = now.isoformat(timespec="seconds")
    rel_path = f"reviews/REPORT-{today}-ui-ux-cycle.md"
    target = root / rel_path
    payload = assess(root, now=now)
    content = _render_report(payload, today=today)
    artifact_status = "planned"
    if not dry_run:
        if target.exists() and not overwrite:
            artifact_status = "exists"
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            artifact_status = "recorded"
    return {
        "schema": REPORT_SCHEMA,
        "generated_at": generated_at,
        "root": str(root),
        "status": "planned" if dry_run else artifact_status,
        "dry_run": dry_run,
        "assessment": payload,
        "artifact": {"path": rel_path, "status": artifact_status},
    }


def render_text(payload: dict[str, Any]) -> str:
    task = (payload["next_refactor"].get("task") or {}).get("task_id", "none")
    return "\n".join(
        [
            "UI/UX Cycle Assessment",
            f"- Status: {payload['status']}",
            f"- Readiness: {payload['score']['level']} ({payload['score']['value']}/100)",
            f"- Design-system gate: {payload['design_system_gate']['status']}",
            f"- Next refactor: {task} ({payload['next_refactor']['status']})",
        ]
    )


def render_report_text(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "UI/UX Cycle Report",
            f"- Status: {payload['status']}",
            f"- Report: {payload['artifact']['status']} -> {payload['artifact']['path']}",
            f"- Next refactor: {(payload['assessment']['next_refactor'].get('task') or {}).get('task_id', 'none')}",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UI/UX continuous improvement cycle conductor")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--now", help="ISO timestamp for deterministic output")
    sub = parser.add_subparsers(dest="command", required=True)
    assess_parser = sub.add_parser("assess", help="assess current UI/UX cycle signals")
    assess_parser.add_argument("--json", action="store_true")
    report_parser = sub.add_parser("report", help="plan or write the UI/UX cycle report")
    report_parser.add_argument("--dry-run", action="store_true")
    report_parser.add_argument("--overwrite", action="store_true")
    report_parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    now = _parse_now(args.now)
    if args.command == "assess":
        payload = assess(args.root, now=now)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(render_text(payload))
        return 0
    if args.command == "report":
        payload = report(args.root, now=now, dry_run=args.dry_run, overwrite=args.overwrite)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(render_report_text(payload))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
