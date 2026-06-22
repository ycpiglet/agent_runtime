"""Plan topological unit waves and batch-issue claim+worktree for one wave.

TASK-AR-501. A planner decomposes a unit dependency DAG (optional unit
frontmatter field ``depends_on``: list of unit and/or task ids) into
topological waves. Within one wave no unit depends on another and all unit
``target_files`` footprints are pairwise disjoint, verified with
``footprints_overlap`` from scripts/footprint_conflict_gate.py. A unit whose
footprint overlaps an earlier unit of the same wave is deferred to a later
wave (the first unit by id keeps its slot).

Commands:
  --plan                          print waves as a table (or JSON); read-only.
  --dispatch --mode cascade       issue exactly the next single unit
                                  claim+worktree (sequential parity; default).
  --dispatch --mode parallel --max-panes N
                                  batch-issue up to N units of the next wave.
  --status                        show wave progress derived from task claims.

Claim creation is delegated to scripts/task_claim_dispatcher.py, which logs
``claim_created`` pane events itself; this script intentionally writes no
pane events (no double logging). Output is ASCII-only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import backlog_board
import model_routing
from footprint_conflict_gate import footprints_overlap
from task_unit_readiness_gate import depends_on_refs, load_unit_specs

try:
    # Dormant-role routing (TASK-AR-592): source-repo-only module. Consumers
    # that vendor this dispatcher via the template do NOT ship role_routing, so
    # the import is guarded — when absent, the per-wave scout/council hooks are
    # simply unavailable (no behavior change, no breakage).
    import role_routing
except ImportError:  # pragma: no cover - consumer parity guard
    role_routing = None  # type: ignore[assignment]


DONE_UNIT_STATUSES = {"completed", "done"}
DONE_CLAIM_STATUSES = {"completed", "done", "released"}
ACTIVE_CLAIM_STATUSES = {
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "waiting_review",
    "working",
}
DEFAULT_AGENT_ROLE = "lead-engineer"
DEFAULT_TEAM_ID = "agent-runtime-core"


class WaveError(SystemExit):
    """Raised for plan/dispatch failures with a printable message."""

    def __init__(self, message: str) -> None:
        print("wave-dispatcher: error", file=sys.stderr)
        print(message, file=sys.stderr)
        super().__init__(1)


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return path.as_posix()


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower())
    text = re.sub(r"-+", "-", text)
    return text.strip("-") or "unit"


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


@dataclass
class UnitNode:
    path: Path
    meta: dict[str, Any]

    @property
    def unit_id(self) -> str:
        return str(self.meta.get("unit_id") or "").strip()

    @property
    def task_id(self) -> str:
        return str(self.meta.get("task_id") or "").strip()

    @property
    def task_set_id(self) -> str:
        return str(self.meta.get("task_set_id") or "").strip()

    @property
    def project_id(self) -> str:
        return str(self.meta.get("project_id") or "").strip()

    @property
    def status(self) -> str:
        return str(self.meta.get("status") or "").strip().lower()

    @property
    def target_files(self) -> list[str]:
        return _as_list(self.meta.get("target_files"))

    @property
    def depends_on(self) -> list[str]:
        return depends_on_refs(self.meta)

    @property
    def stop_condition(self) -> str:
        value = str(self.meta.get("stop_condition") or "").strip()
        return value or f"stop_after:{self.unit_id}:no_adjacent_taskset"


@dataclass
class WavePlan:
    nodes: list[UnitNode]
    waves: list[list[UnitNode]]
    deferrals: list[dict[str, Any]]
    external_deps: list[tuple[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Unit selection
# ---------------------------------------------------------------------------


def _all_units(root: Path) -> list[UnitNode]:
    return [UnitNode(path=path, meta=meta) for path, meta, _body in load_unit_specs(root)]


def _resolve_taskset_id(value: str) -> str:
    text = value.strip()
    if text.upper().startswith("TASKSET-"):
        return text
    import taskset_dispatcher

    return taskset_dispatcher._resolve_taskset(text).task_set_id


def _load_unit_from_path(root: Path, value: str) -> UnitNode:
    path = Path(value)
    if not path.is_absolute():
        path = root / value
    if not path.is_file():
        raise WaveError(f"unit spec file not found: {value}")
    meta, _body = backlog_board.parse_frontmatter(path.read_text(encoding="utf-8"))
    return UnitNode(path=path, meta=meta)


def select_units(root: Path, *, taskset: str = "", units: list[str] | None = None) -> tuple[list[UnitNode], str]:
    """Return (selected unit nodes, selection label)."""
    repo_units = _all_units(root)
    selected: list[UnitNode] = []
    if taskset:
        task_set_id = _resolve_taskset_id(taskset)
        tasks = backlog_board.load_tasks(root / "agents" / "lead_engineer" / "tasks")
        task_ids = {task.task_id for task in tasks if task.task_set_id == task_set_id}
        selected = [
            node
            for node in repo_units
            if node.task_id in task_ids or node.task_set_id == task_set_id
        ]
        if not selected:
            raise WaveError(f"no unit specs found for task set: {task_set_id}")
        label = f"taskset:{task_set_id}"
    else:
        by_id = {node.unit_id: node for node in repo_units if node.unit_id}
        for value in units or []:
            text = value.strip()
            if not text:
                continue
            if "/" in text or "\\" in text or text.lower().endswith(".md"):
                selected.append(_load_unit_from_path(root, text))
            elif text in by_id:
                selected.append(by_id[text])
            else:
                raise WaveError(f"unknown unit id: {text}")
        if not selected:
            raise WaveError("no units selected; pass --taskset or at least one --unit")
        label = f"units:{len(selected)}"

    seen: set[str] = set()
    unique: list[UnitNode] = []
    for node in sorted(selected, key=lambda item: item.unit_id):
        if not node.unit_id:
            raise WaveError(f"unit spec is missing unit_id: {_rel(root, node.path)}")
        if node.unit_id in seen:
            continue
        seen.add(node.unit_id)
        unique.append(node)
    return unique, label


# ---------------------------------------------------------------------------
# Wave computation
# ---------------------------------------------------------------------------


def _validate_refs(root: Path, nodes: list[UnitNode], repo_unit_ids: set[str]) -> None:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    known_task_ids = {node.task_id for node in nodes if node.task_id}
    problems: list[str] = []
    for node in nodes:
        for ref in node.depends_on:
            if ref in repo_unit_ids or ref in known_task_ids:
                continue
            if (tasks_dir / f"{ref}.md").is_file():
                continue
            problems.append(f"unknown depends_on reference: {node.unit_id} -> {ref}")
    if problems:
        raise WaveError("\n".join(problems))


def _selection_deps(node: UnitNode, by_id: dict[str, UnitNode], by_task: dict[str, list[UnitNode]]) -> set[str]:
    deps: set[str] = set()
    for ref in node.depends_on:
        if ref == node.unit_id:
            deps.add(ref)  # self-dependency surfaces as a cycle below
        elif ref in by_id:
            deps.add(ref)
        elif ref in by_task:
            deps.update(unit.unit_id for unit in by_task[ref] if unit.unit_id != node.unit_id)
    return deps


def compute_waves(root: Path, nodes: list[UnitNode]) -> WavePlan:
    """List-schedule units into waves honoring depends_on + footprint disjointness."""
    repo_unit_ids = {node.unit_id for node in _all_units(root) if node.unit_id}
    repo_unit_ids.update(node.unit_id for node in nodes)
    _validate_refs(root, nodes, repo_unit_ids)

    by_id = {node.unit_id: node for node in nodes}
    by_task: dict[str, list[UnitNode]] = {}
    for node in nodes:
        by_task.setdefault(node.task_id, []).append(node)

    deps = {node.unit_id: _selection_deps(node, by_id, by_task) for node in nodes}
    external: list[tuple[str, str]] = []
    in_selection = set(by_id) | set(by_task)
    for node in nodes:
        for ref in node.depends_on:
            if ref not in in_selection:
                external.append((node.unit_id, ref))

    scheduled: set[str] = set()
    remaining = dict(by_id)
    waves: list[list[UnitNode]] = []
    deferrals: list[dict[str, Any]] = []
    while remaining:
        ready = sorted(
            (node for node in remaining.values() if deps[node.unit_id] <= scheduled),
            key=lambda item: item.unit_id,
        )
        if not ready:
            lines = ["dependency cycle detected among units:"]
            for unit_id in sorted(remaining):
                blocked_on = sorted(deps[unit_id] - scheduled)
                lines.append(f"- {unit_id} waits on {', '.join(blocked_on)}")
            raise WaveError("\n".join(lines))
        wave: list[UnitNode] = []
        for node in ready:
            conflict: tuple[UnitNode, list[tuple[str, str]]] | None = None
            for kept in wave:
                pairs = footprints_overlap(node.target_files, kept.target_files)
                if pairs:
                    conflict = (kept, pairs)
                    break
            if conflict is None:
                wave.append(node)
            else:
                kept, pairs = conflict
                deferrals.append(
                    {
                        "unit_id": node.unit_id,
                        "deferred_from_wave": len(waves) + 1,
                        "conflicts_with": kept.unit_id,
                        "overlap": [f"{a} <-> {b}" for a, b in pairs],
                    }
                )
        waves.append(wave)
        for node in wave:
            scheduled.add(node.unit_id)
            remaining.pop(node.unit_id, None)
    return WavePlan(nodes=nodes, waves=waves, deferrals=deferrals, external_deps=external)


# ---------------------------------------------------------------------------
# Claim state
# ---------------------------------------------------------------------------


def _load_claims(root: Path) -> list[dict[str, Any]]:
    claim_dir = root / "agents" / "runtime" / "task_claims"
    if not claim_dir.is_dir():
        return []
    claims: list[dict[str, Any]] = []
    for path in sorted(claim_dir.glob("*.json"), key=lambda item: item.name.lower()):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            claims.append(payload)
    return claims


def _unit_state(node: UnitNode, claims: list[dict[str, Any]]) -> str:
    """Classify a unit as done | active | pending from spec status + claims."""
    if node.status in DONE_UNIT_STATUSES:
        return "done"
    released = False
    for claim in claims:
        if str(claim.get("unit_id") or "").strip() != node.unit_id:
            continue
        status = str(claim.get("status") or "").strip().lower()
        if status in ACTIVE_CLAIM_STATUSES:
            return "active"
        if status in DONE_CLAIM_STATUSES:
            released = True
    return "done" if released else "pending"


def _active_task_ids(claims: list[dict[str, Any]]) -> set[str]:
    return {
        str(claim.get("task_id") or "").strip()
        for claim in claims
        if str(claim.get("status") or "").strip().lower() in ACTIVE_CLAIM_STATUSES
    }


def _wave_states(plan: WavePlan, claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    current_found = False
    for index, wave in enumerate(plan.waves, start=1):
        states = {node.unit_id: _unit_state(node, claims) for node in wave}
        done = sum(1 for value in states.values() if value == "done")
        active = sum(1 for value in states.values() if value == "active")
        pending = sum(1 for value in states.values() if value == "pending")
        if done == len(wave):
            label = "complete"
        elif not current_found:
            label = "current"
            current_found = True
        else:
            label = "queued"
        summaries.append(
            {
                "wave": index,
                "unit_states": states,
                "done": done,
                "active": active,
                "pending": pending,
                "state": label,
            }
        )
    return summaries


def _full_cycle_guidance(next_wave: int | None) -> list[str]:
    target = f"wave {next_wave}" if next_wave else "closeout"
    return [
        f"wave-boundary: all issued units of the previous wave are completed/released; run the full cycle before {target}",
        "full-cycle: 1) python -m pytest tests -q  2) python scripts/precommit_check.py",
        "full-cycle: 3) integrate released wave branches (merge policy: TASK-AR-502)",
        "full-cycle: 4) re-run --plan, then --dispatch the next wave",
    ]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_plan(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    nodes, label = select_units(root, taskset=args.taskset, units=args.unit)
    plan = compute_waves(root, nodes)
    if args.json:
        payload = {
            "command": "plan",
            "selection": label,
            "units": len(plan.nodes),
            "waves": [
                [
                    {
                        "unit_id": node.unit_id,
                        "task_id": node.task_id,
                        "status": node.status,
                        "target_files": node.target_files,
                        "depends_on": node.depends_on,
                    }
                    for node in wave
                ]
                for wave in plan.waves
            ],
            "deferrals": plan.deferrals,
            "external_deps": [
                {"unit_id": unit_id, "ref": ref} for unit_id, ref in plan.external_deps
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("wave-dispatcher: plan")
    print(f"root={root}")
    print(f"selection={label}")
    print(f"units={len(plan.nodes)} waves={len(plan.waves)} deferrals={len(plan.deferrals)}")
    rows = [("wave", "unit", "task", "status", "files", "depends_on")]
    for index, wave in enumerate(plan.waves, start=1):
        for node in wave:
            rows.append(
                (
                    str(index),
                    node.unit_id,
                    node.task_id,
                    node.status or "-",
                    str(len(node.target_files)),
                    ",".join(node.depends_on) or "-",
                )
            )
    widths = [max(len(row[col]) for row in rows) for col in range(len(rows[0]))]
    for row_index, row in enumerate(rows):
        print(" | ".join(cell.ljust(widths[col]) for col, cell in enumerate(row)).rstrip())
        if row_index == 0:
            print("-+-".join("-" * width for width in widths))
    for deferral in plan.deferrals:
        print(
            f"deferral: {deferral['unit_id']} deferred from wave {deferral['deferred_from_wave']} "
            f"(footprint overlap with {deferral['conflicts_with']}: {'; '.join(deferral['overlap'])})"
        )
    for unit_id, ref in plan.external_deps:
        print(f"external-dep: {unit_id} -> {ref} (outside selection; not used for wave ordering)")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    nodes, label = select_units(root, taskset=args.taskset, units=args.unit)
    plan = compute_waves(root, nodes)
    claims = _load_claims(root)
    summaries = _wave_states(plan, claims)
    current = next((entry for entry in summaries if entry["state"] == "current"), None)
    guidance: list[str] = []
    if current is None:
        guidance = _full_cycle_guidance(None)
    else:
        previous_done = current["wave"] == 1 or summaries[current["wave"] - 2]["state"] == "complete"
        unissued = current["active"] == 0 and current["done"] == 0
        if current["wave"] > 1 and previous_done and unissued:
            guidance = _full_cycle_guidance(current["wave"])

    if args.json:
        payload = {
            "command": "status",
            "selection": label,
            "units": len(plan.nodes),
            "current_wave": current["wave"] if current else None,
            "all_waves_complete": current is None,
            "waves": summaries,
            "guidance": guidance,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("wave-dispatcher: status")
    print(f"root={root}")
    print(f"selection={label}")
    print(f"units={len(plan.nodes)} waves={len(plan.waves)}")
    for entry in summaries:
        print(
            f"wave {entry['wave']}: done={entry['done']} active={entry['active']} "
            f"pending={entry['pending']} state={entry['state']}"
        )
        for unit_id, state in sorted(entry["unit_states"].items()):
            print(f"  - {unit_id} [{state}]")
    if current is None:
        print("all_waves_complete=true")
    for line in guidance:
        print(line)
    return 0


def _ensure_worktree(root: Path, worktree_path: str, branch: str) -> str | None:
    worktree = root / worktree_path
    if worktree.is_dir() and (worktree / ".git").exists():
        return None
    git = os.environ.get("AGENT_RUNTIME_GIT") or "git"
    result = subprocess.run(
        [git, "worktree", "add", "-b", branch, worktree_path],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return f"git worktree add failed for {worktree_path}: {detail}"
    if not (worktree / ".git").exists():
        return f"worktree is not ready after add: {worktree_path}"
    return None


def _claim_command(
    root: Path,
    node: UnitNode,
    *,
    wave_no: int,
    worktree_path: str,
    branch: str,
    args: argparse.Namespace,
    allow_parallel_task_set: bool,
    suffix: str | None,
) -> list[str]:
    task_meta: dict[str, Any] = {}
    agent_role = args.agent_role or DEFAULT_AGENT_ROLE
    team_id = args.team_id or DEFAULT_TEAM_ID
    task_path = root / "agents" / "lead_engineer" / "tasks" / f"{node.task_id}.md"
    if task_path.is_file():
        meta, body = backlog_board.parse_frontmatter(task_path.read_text(encoding="utf-8"))
        task_meta = meta
        task = backlog_board.Task(path=task_path, meta=meta, goal="")
        if not args.agent_role:
            agent_role = backlog_board.agent_for(task)
        if not args.team_id:
            team_id = backlog_board.team_for(task)
    routing = model_routing.resolve_work_item_tier(task_meta, node.meta)
    command = [
        sys.executable or "python",
        str(Path(__file__).resolve().with_name("task_claim_dispatcher.py")),
        "--root",
        str(root),
        "create",
        "--task-id",
        node.task_id,
        "--task-set-id",
        node.task_set_id,
        "--project-id",
        node.project_id,
        "--unit-id",
        node.unit_id,
        "--unit-spec",
        _rel(root, node.path),
        "--model-tier",
        str(routing["selected_tier"]),
        "--stop-condition",
        node.stop_condition,
        "--agent-role",
        agent_role,
        "--team-id",
        team_id,
        "--mode",
        "wave",
        "--phase",
        "wave-claimed",
        "--status-text",
        f"Wave {wave_no} dispatch: {node.unit_id}",
        "--worktree-path",
        worktree_path,
        "--branch",
        branch,
        "--json",
    ]
    for entry in node.target_files:
        command.extend(["--target-file", entry])
    if allow_parallel_task_set:
        command.append("--allow-parallel-task-set")
    if args.now:
        command.extend(["--now", args.now])
    if suffix:
        command.extend(["--suffix", suffix])
    return command


def cmd_dispatch(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    parallel = args.mode == "parallel"
    batch_limit = args.max_panes if parallel else 1
    if batch_limit < 1:
        raise WaveError("--max-panes must be at least 1")

    nodes, label = select_units(root, taskset=args.taskset, units=args.unit)
    plan = compute_waves(root, nodes)
    claims = _load_claims(root)
    summaries = _wave_states(plan, claims)
    current = next((entry for entry in summaries if entry["state"] == "current"), None)

    if current is None:
        guidance = _full_cycle_guidance(None)
        if args.json:
            print(
                json.dumps(
                    {
                        "command": "dispatch",
                        "selection": label,
                        "mode": args.mode,
                        "all_waves_complete": True,
                        "issued": [],
                        "guidance": guidance,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        print("wave-dispatcher: complete")
        print(f"root={root}")
        print(f"selection={label}")
        print("all_waves_complete=true")
        for line in guidance:
            print(line)
        return 0

    wave_no = current["wave"]
    guidance: list[str] = []
    if wave_no > 1 and summaries[wave_no - 2]["state"] == "complete" and current["active"] == 0 and current["done"] == 0:
        guidance = _full_cycle_guidance(wave_no)
        if not args.json:
            for line in guidance:
                print(line)

    wave_nodes = plan.waves[wave_no - 1]
    active_tasks = _active_task_ids(claims)
    candidates: list[UnitNode] = []
    skipped: list[str] = []
    used_tasks: set[str] = set()
    for node in sorted(wave_nodes, key=lambda item: item.unit_id):
        state = current["unit_states"][node.unit_id]
        if state != "pending":
            continue
        if node.task_id in active_tasks:
            skipped.append(f"{node.unit_id} (task {node.task_id} already has an active claim)")
            continue
        if node.task_id in used_tasks:
            skipped.append(f"{node.unit_id} (task {node.task_id} already issued in this batch)")
            continue
        candidates.append(node)
        used_tasks.add(node.task_id)
        if len(candidates) >= batch_limit:
            break

    if not candidates:
        if args.json:
            print(
                json.dumps(
                    {
                        "command": "dispatch",
                        "selection": label,
                        "mode": args.mode,
                        "wave": wave_no,
                        "wave_total": len(plan.waves),
                        "state": "in_flight",
                        "issued": [],
                        "skipped": skipped,
                        "guidance": guidance,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        print("wave-dispatcher: waiting")
        print(f"root={root}")
        print(f"selection={label}")
        print(f"wave={wave_no}/{len(plan.waves)} state=in_flight")
        print("no dispatchable units in the current wave; wait for active claims to complete/release")
        for note in skipped:
            print(f"skipped: {note}")
        return 0

    issued: list[dict[str, Any]] = []
    for index, node in enumerate(candidates, start=1):
        # A shared --suffix would collide on agent_instance_id within one
        # batch (same role + same --now); disambiguate per unit.
        suffix = args.suffix
        if suffix and len(candidates) > 1:
            suffix = f"{suffix}{index}"
        worktree_path = f".worktrees/{node.task_id}"
        branch = f"codex/{_slug(node.unit_id)}-wave"
        error = _ensure_worktree(root, worktree_path, branch)
        if error:
            print(error, file=sys.stderr)
            _print_dispatch_summary(root, label, wave_no, len(plan.waves), issued, skipped, args, guidance)
            return 1
        result = subprocess.run(
            _claim_command(
                root,
                node,
                wave_no=wave_no,
                worktree_path=worktree_path,
                branch=branch,
                args=args,
                allow_parallel_task_set=parallel,
                suffix=suffix,
            ),
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
            _print_dispatch_summary(root, label, wave_no, len(plan.waves), issued, skipped, args, guidance)
            return 1
        try:
            claim = json.loads(result.stdout)["claim"]
        except (json.JSONDecodeError, KeyError, TypeError):
            claim = {"raw": result.stdout.strip()}
        issued.append(
            {
                "unit_id": node.unit_id,
                "task_id": node.task_id,
                "claim_id": claim.get("claim_id", ""),
                "worktree_path": worktree_path,
                "branch": branch,
                "target_files": node.target_files,
            }
        )

    # Dormant-role routing seam (TASK-AR-592): when AR_SCOUT_COUNCIL is ON,
    # dispatch a per-wave progress-scout sweep (and, at the W6 boundary, a
    # council deliberation) as ADDITIVE overlay claims. These run alongside the
    # worker claims this batch just issued and never remove or mutate them.
    # Flag-OFF (default), an absent module, and any routing fault are no-ops:
    # a routing failure must NEVER break the wave dispatch.
    if role_routing is not None:
        try:
            # Prefer an explicit taskset id; for a --unit selection fall back to
            # the issued units' own task_set_id, then the selection label, so the
            # overlay claim id is stable and attributable.
            task_set_id = (
                label.split(":", 1)[1]
                if label.startswith("taskset:")
                else (next((n.task_set_id for n in wave_nodes if n.task_set_id), "") or label)
            )
            role_routing.dispatch_wave_hooks(
                root,
                task_set_id=task_set_id,
                wave_no=wave_no,
                is_w6=(wave_no == 6),
                now=args.now,
            )
        except Exception:  # noqa: BLE001 - routing is best-effort overlay only
            pass

    _print_dispatch_summary(root, label, wave_no, len(plan.waves), issued, skipped, args, guidance)
    return 0


def _print_dispatch_summary(
    root: Path,
    label: str,
    wave_no: int,
    wave_total: int,
    issued: list[dict[str, Any]],
    skipped: list[str],
    args: argparse.Namespace,
    guidance: list[str] | None = None,
) -> None:
    if args.json:
        print(
            json.dumps(
                {
                    "command": "dispatch",
                    "selection": label,
                    "mode": args.mode,
                    "wave": wave_no,
                    "wave_total": wave_total,
                    "issued": issued,
                    "skipped": skipped,
                    "guidance": guidance or [],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    print("wave-dispatcher: dispatched")
    print(f"root={root}")
    print(f"selection={label}")
    print(f"mode={args.mode} wave={wave_no}/{wave_total} issued={len(issued)}")
    for entry in issued:
        print(
            f"- unit={entry['unit_id']} task={entry['task_id']} claim_id={entry['claim_id']} "
            f"worktree={entry['worktree_path']} branch={entry['branch']}"
        )
    for note in skipped:
        print(f"skipped: {note}")
    print("next: track wave progress with --status; claim creation already logged pane events")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decompose unit depends_on DAG into topological waves and dispatch claim+worktree batches"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    selection = parser.add_argument_group("selection")
    selection.add_argument("--taskset", default="", help="Task set id or alias to discover units from")
    selection.add_argument(
        "--unit",
        action="append",
        default=[],
        help="Explicit unit id or unit spec path (repeatable; alternative to --taskset)",
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--plan", action="store_true", help="Print waves as table/JSON; no side effects")
    action.add_argument("--dispatch", action="store_true", help="Issue claim+worktree for the next wave")
    action.add_argument("--status", action="store_true", help="Show wave progress from claims")
    parser.add_argument("--mode", choices=("cascade", "parallel"), default="cascade")
    parser.add_argument("--max-panes", type=int, default=2, help="Parallel batch size (parallel mode only)")
    parser.add_argument("--agent-role", default="")
    parser.add_argument("--team-id", default="")
    parser.add_argument("--now")
    parser.add_argument("--suffix")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.taskset and not args.unit:
        parser.error("select units with --taskset or --unit")
    if args.taskset and args.unit:
        parser.error("--taskset and --unit are mutually exclusive")
    if args.plan:
        return cmd_plan(args)
    if args.status:
        return cmd_status(args)
    return cmd_dispatch(args)


if __name__ == "__main__":
    raise SystemExit(main())
