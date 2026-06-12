"""Plan and claim a task-set lane for parallel pane work.

This script is the user-friendly entrypoint behind prompts like
``taskset-quality-loop 진행해줘``. It resolves human aliases, selects the next
task inside that task set, and creates a task claim with progress metadata.

For multi-unit wave execution (topological waves over unit ``depends_on``
plus cascade/parallel batch dispatch) use ``scripts/wave_dispatcher.py``;
the plan payload exposes the matching planner command as
``wave_plan_command`` (TASK-AR-501).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import backlog_board
import model_routing


ACTIVE_STATUSES = {
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "waiting_review",
    "working",
}

DONE_STATUSES = {
    "completed",
    "done",
}


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


def _normalize_status(value: str) -> str:
    return str(value or "").strip().lower()


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _taskset_aliases() -> dict[str, backlog_board.TaskSetInfo]:
    aliases: dict[str, backlog_board.TaskSetInfo] = {}
    for index, info in enumerate(backlog_board.TASK_SET_DEFINITIONS, start=1):
        letter = _letter_alias(index)
        values = {
            info.task_set_id,
            info.task_set_id.lower(),
            str(index),
            letter,
            f"taskset {index}",
            f"taskset-{index}",
            f"taskset {letter}",
            f"taskset-{letter}",
            _taskset_slug(info.task_set_id),
            _slug(info.display_name),
            _slug(info.task_set_id.replace("TASKSET-AR-", "")),
        }
        for value in values:
            aliases[value.lower()] = info
    return aliases


def _resolve_taskset(value: str) -> backlog_board.TaskSetInfo:
    normalized = value.strip().lower()
    normalized = re.sub(r"^taskset[-_: ]*", "", normalized)
    aliases = _taskset_aliases()
    if value.strip().lower() in aliases:
        return aliases[value.strip().lower()]
    if normalized in aliases:
        return aliases[normalized]
    raise SystemExit(f"unknown task set alias: {value}")


def _tasks_for(root: Path, task_set_id: str) -> list[backlog_board.Task]:
    tasks = backlog_board.load_tasks(root / "agents" / "lead_engineer" / "tasks")
    return sorted([task for task in tasks if task.task_set_id == task_set_id], key=backlog_board.task_set_sort_key)


def _next_task(tasks: list[backlog_board.Task]) -> backlog_board.Task:
    for task in tasks:
        if _normalize_status(task.status) in DONE_STATUSES:
            continue
        if backlog_board.lane_for(task) != "Done":
            return task
    raise SystemExit("task set has no open tasks")


def _unit_specs_for_task(root: Path, task_id: str) -> list[tuple[Path, dict[str, Any], str]]:
    units_dir = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id
    if not units_dir.is_dir():
        return []
    specs: list[tuple[Path, dict[str, Any], str]] = []
    for path in sorted(units_dir.glob("UNIT-*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = backlog_board.parse_frontmatter(text)
        specs.append((path, meta, body))
    return specs


def _ready_unit_for_task(root: Path, task_id: str) -> tuple[Path, dict[str, Any], str] | None:
    units = _unit_specs_for_task(root, task_id)
    if not units:
        return None
    ready = [
        unit
        for unit in units
        if str(unit[1].get("status") or "").strip() in {"worker_ready", "ready", "in_progress"}
    ]
    return (ready or units)[0]


def _project_id_for(task: backlog_board.Task, unit_meta: dict[str, Any] | None = None) -> str:
    unit_meta = unit_meta or {}
    return str(unit_meta.get("project_id") or task.meta.get("project_id") or "PROJECT-AGENT-RUNTIME").strip()


def _stop_condition_for(task: backlog_board.Task, unit_id: str) -> str:
    target = unit_id or task.task_id
    return f"stop_after:{target}:no_adjacent_taskset"


def _read_claim(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _active_claims(root: Path) -> list[dict[str, Any]]:
    claim_dir = root / "agents" / "runtime" / "task_claims"
    if not claim_dir.is_dir():
        return []
    claims: list[dict[str, Any]] = []
    for path in sorted(claim_dir.glob("*.json"), key=lambda item: item.name.lower()):
        payload = _read_claim(path)
        if not payload:
            continue
        if str(payload.get("status") or "").strip().lower() in ACTIVE_STATUSES:
            payload["_path"] = _rel(root, path)
            claims.append(payload)
    return claims


def _active_taskset_claims(root: Path, task_set_id: str) -> list[dict[str, Any]]:
    return [claim for claim in _active_claims(root) if str(claim.get("task_set_id") or "") == task_set_id]


def _target_status_for_work_start(current: str | None) -> str | None:
    normalized = _normalize_status(current)
    if normalized in {"completed", "done"}:
        return None
    if normalized.startswith("hold") or normalized == "blocked":
        return normalized
    if normalized in {"review", "waiting_review", "ready_for_governance_review"}:
        return normalized
    if not normalized:
        return "in_progress"
    return "in_progress"


def _set_task_status(task_path: Path, next_status: str) -> bool:
    try:
        original = task_path.read_text(encoding="utf-8")
    except OSError:
        print(f"failed_to_read_task_file:{_rel(Path.cwd(), task_path)}", file=sys.stderr)
        return False
    lines = original.splitlines()
    if not lines or lines[0].strip() != "---":
        return False

    close = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            close = idx
            break
    if close is None or close == 1:
        return False

    header = lines[1:close]
    updated = False
    for idx, line in enumerate(header):
        if re.match(r"^\s*status\s*:\s*", line):
            prefix = re.match(r"^(\s*)", line)
            indent = prefix.group(1) if prefix else ""
            header[idx] = f"{indent}status: {next_status}"
            updated = True
            break

    if not updated:
        insert = 1
        while insert < len(header) and not header[insert].strip():
            insert += 1
        header.insert(insert, f"status: {next_status}")

    output = "\n".join(["---", *header, "---", *lines[close + 1 :]])
    if original.endswith("\n"):
        output += "\n"
    if output == original:
        return False
    task_path.write_text(output, encoding="utf-8")
    return True


def _sync_backlog_board(root: Path) -> bool:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().with_name("backlog_board.py")), "--write"],
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


def _worktree_preflight_error(root: Path, payload: dict[str, Any]) -> str | None:
    worktree_value = str(payload.get("worktree_path") or "").strip()
    if not worktree_value:
        return "task worktree is not ready: missing worktree_path"
    worktree = Path(worktree_value)
    if not worktree.is_absolute():
        worktree = root / worktree
    if not worktree.is_dir():
        return f"task worktree is not ready: {worktree_value} does not exist"
    if not (worktree / ".git").exists():
        return f"task worktree is not ready: {worktree_value} is not a git worktree"
    return None


def _ensure_worktree(root: Path, payload: dict[str, Any]) -> bool:
    if not _worktree_preflight_error(root, payload):
        return True
    worktree_command = list(payload["worktree_command"])
    worktree_command[0] = os.environ.get("AGENT_RUNTIME_GIT") or worktree_command[0]
    result = subprocess.run(
        worktree_command,
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
    worktree_error = _worktree_preflight_error(root, payload)
    if worktree_error:
        print(worktree_error, file=sys.stderr)
        return False
    return True


def _plan_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    info = _resolve_taskset(args.taskset)
    tasks = _tasks_for(root, info.task_set_id)
    task = _next_task(tasks)
    task_set_slug = _taskset_slug(info.task_set_id)
    task_slug = _slug(task.task_id)
    worktree_path = f".worktrees/{task.task_id}"
    branch = f"codex/{task_slug}-{task_set_slug}"
    step_index = tasks.index(task) + 1
    step_total = len(tasks)
    unit = _ready_unit_for_task(root, task.task_id)
    unit_path = unit[0] if unit else None
    unit_meta = unit[1] if unit else {}
    unit_id = str(unit_meta.get("unit_id") or task.meta.get("unit_id") or "").strip()
    project_id = _project_id_for(task, unit_meta)
    routing_decision = model_routing.resolve_work_item_tier(task.meta, unit_meta)
    active_claims = _active_taskset_claims(root, info.task_set_id)
    wip_slot = len(active_claims) + 1
    stop_condition = str(unit_meta.get("stop_condition") or task.meta.get("stop_condition") or _stop_condition_for(task, unit_id)).strip()
    status_text = f"Starting {info.display_name}: {task.task_id}"
    mode = args.mode or task_set_slug
    agent_role = args.agent_role or backlog_board.agent_for(task)
    team_id = args.team_id or backlog_board.team_for(task)

    claim_command = [
        sys.executable or "python",
        str(Path(__file__).resolve().with_name("task_claim_dispatcher.py")),
        "--root",
        str(root),
        "create",
        "--task-id",
        task.task_id,
        "--task-set-id",
        info.task_set_id,
        "--project-id",
        project_id,
        "--unit-id",
        unit_id,
        "--unit-spec",
        _rel(root, unit_path) if unit_path else str(task.meta.get("unit_spec") or ""),
        "--model-tier",
        str(routing_decision["selected_tier"]),
        "--wip-slot",
        str(wip_slot),
        "--stop-condition",
        stop_condition,
        "--agent-role",
        agent_role,
        "--team-id",
        team_id,
        "--mode",
        mode,
        "--phase",
        "taskset-claimed",
        "--progress-pct",
        "0",
        "--step-index",
        str(step_index),
        "--step-total",
        str(step_total),
        "--status-text",
        status_text,
        "--worktree-path",
        worktree_path,
        "--branch",
        branch,
    ]
    if args.now:
        claim_command.extend(["--now", args.now])
    if args.suffix:
        claim_command.extend(["--suffix", args.suffix])
    if args.json:
        claim_command.append("--json")

    return {
        "task_set_id": info.task_set_id,
        "display_name": info.display_name,
        "summary": info.summary,
        "next_task_id": task.task_id,
        "step_index": step_index,
        "step_total": step_total,
        "next_task_status": task.status,
        "next_task_path": str((root / "agents" / "lead_engineer" / "tasks" / f"{task.task_id}.md")),
        "project_id": project_id,
        "unit_id": unit_id,
        "unit_spec_path": _rel(root, unit_path) if unit_path else str(task.meta.get("unit_spec") or ""),
        "model_routing": routing_decision,
        "model_tier": str(routing_decision["selected_tier"]),
        "wip_slot": wip_slot,
        "stop_condition": stop_condition,
        "status_text": status_text,
        "worktree_path": worktree_path,
        "branch": branch,
        "worktree_command": [
            "git",
            "worktree",
            "add",
            "-b",
            branch,
            worktree_path,
        ],
        "claim_command": claim_command,
        "wave_plan_command": [
            sys.executable or "python",
            str(Path(__file__).resolve().with_name("wave_dispatcher.py")),
            "--root",
            str(root),
            "--taskset",
            info.task_set_id,
            "--plan",
        ],
    }


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"taskset-dispatcher: {payload['display_name']} ({payload['task_set_id']})")
    print(f"next_task={payload['next_task_id']}")
    print(f"project_id={payload.get('project_id', '')}")
    print(f"unit_id={payload.get('unit_id', '')}")
    print(f"model_tier={payload.get('model_tier', '')}")
    print(f"wip_slot={payload.get('wip_slot', '')}")
    print(f"stop_condition={payload.get('stop_condition', '')}")
    print(f"progress={payload['step_index']}/{payload['step_total']}")
    print(f"status_text={payload['status_text']}")
    print("worktree_command=" + " ".join(payload["worktree_command"]))
    print("claim_command=" + " ".join(payload["claim_command"]))
    if payload.get("wave_plan_command"):
        print("wave_plan_command=" + " ".join(payload["wave_plan_command"]))


def cmd_plan(args: argparse.Namespace) -> int:
    payload = _plan_payload(args)
    _emit(payload, as_json=args.json)
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    payload = _plan_payload(args)
    active = _active_taskset_claims(root, payload["task_set_id"])
    if active:
        claim_paths = ", ".join(str(claim.get("_path") or claim.get("claim_id") or "?") for claim in active)
        print(
            f"task set already has an active claim: {payload['task_set_id']} ({claim_paths})",
            file=sys.stderr,
        )
        return 1

    if str(payload.get("unit_spec_path") or "").strip() and str(payload.get("model_tier") or "").startswith("worker_"):
        gate = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve().with_name("task_unit_readiness_gate.py")),
                "--root",
                str(root),
                "--task-id",
                str(payload["next_task_id"]),
                "--unit-id",
                str(payload.get("unit_id") or ""),
                "--require-ready",
                "--check",
            ],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if gate.returncode != 0:
            if gate.stdout:
                print(gate.stdout, file=sys.stderr, end="")
            if gate.stderr:
                print(gate.stderr, file=sys.stderr, end="")
            return gate.returncode

    if not _ensure_worktree(root, payload):
        print("worktree_command=" + " ".join(payload["worktree_command"]), file=sys.stderr)
        return 1

    result = subprocess.run(
        payload["claim_command"],
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
        return result.returncode

    task_path = Path(payload["next_task_path"])
    target_status = _target_status_for_work_start(payload["next_task_status"])
    status_updated = False
    if target_status and target_status != _normalize_status(payload["next_task_status"]):
        status_updated = _set_task_status(task_path, target_status)

    if not _sync_backlog_board(root):
        print("failed to rewrite BACKLOG-BOARD.md after task start", file=sys.stderr)
        return 1

    claim_payload: dict[str, Any]
    try:
        claim_payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        claim_payload = {"raw": result.stdout.strip()}
    payload["claim"] = claim_payload
    payload["task_status_updated"] = status_updated
    payload["task_status"] = target_status
    _emit(payload, as_json=args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or claim one task set for parallel pane work")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository or host root")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, func in (("plan", cmd_plan), ("start", cmd_start)):
        command = sub.add_parser(name, help=f"{name} a task set")
        command.add_argument("taskset", help="Task set id or human alias, e.g. 2, B, quality-loop")
        command.add_argument("--agent-role")
        command.add_argument("--team-id")
        command.add_argument("--mode")
        command.add_argument("--now")
        command.add_argument("--suffix")
        command.add_argument("--json", action="store_true")
        command.set_defaults(func=func)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
