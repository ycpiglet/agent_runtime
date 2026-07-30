from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "wave_dispatcher.py"
TEMPLATE_SCRIPT = (
    REPO_ROOT
    / "src"
    / "agent_runtime"
    / "templates"
    / "project"
    / "scripts"
    / "wave_dispatcher.py"
)
TASKSET = "TASKSET-AR-WAVE-TEST"
HOST_REPO_ROOT = REPO_ROOT
HOST_SCRIPTS = HOST_REPO_ROOT / "scripts"
HOST_TASKSET = "TASKSET-DYNAMIC-WAVE"
HOST_PROJECT = "PROJECT-WAVE-TEST"

if str(HOST_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(HOST_SCRIPTS))

import wave_dispatcher as host_dispatcher  # noqa: E402


def _routing_off_env() -> dict[str, str]:
    """Pin the dormant-role routing flags OFF so these baseline tests assert the
    unchanged dispatch behavior deterministically, regardless of an ambient flag
    in the developer's shell (the live flags are exercised in
    tests/test_role_routing_wiring.py)."""
    env = dict(os.environ)
    for flag in ("AR_ROLE_ROUTING", "AR_SCOUT_COUNCIL", "AR_BETA_ACTIVATION"):
        env.pop(flag, None)
    env.pop("AGENT_RUNTIME_GIT", None)
    return env


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_routing_off_env(),
    )


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _init_git_repo(root: Path) -> None:
    assert _git(root, "init", "-q").returncode == 0
    assert _git(root, "config", "user.email", "wave-test@example.com").returncode == 0
    assert _git(root, "config", "user.name", "Wave Test").returncode == 0
    (root / "README.md").write_text("wave dispatcher fixture\n", encoding="utf-8")
    assert _git(root, "add", "-A").returncode == 0
    assert _git(root, "commit", "-q", "-m", "init").returncode == 0


def _write_canonical_taskset(root: Path) -> None:
    path = root / "agents" / "project" / "initiatives" / f"{TASKSET}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
schema_version: agent-runtime-work-item/v1
work_id: {TASKSET}
kind: taskset
title: Wave Test
summary: Synthetic upstream wave dispatcher lane.
---
""",
        encoding="utf-8",
    )


def _write_task(root: Path, task_id: str, *, status: str = "planned") -> None:
    _write_canonical_taskset(root)
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.md").write_text(
        f"""---
id: {task_id}
status: {status}
priority: P1
difficulty: M
est_hours: 2
est_tokens: 200
task_set_id: {TASKSET}
tags: []
---

## Goal
- Wave dispatcher fixture task.
""",
        encoding="utf-8",
    )


def _write_unit(
    root: Path,
    task_id: str,
    index: int,
    *,
    target_files: list[str],
    depends_on: list[str] | None = None,
    status: str = "worker_ready",
) -> str:
    unit_id = f"UNIT-{task_id}-{index:03d}"
    path = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id / f"{unit_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    for entry in target_files:
        if entry.startswith("new:") or "*" in entry:
            continue
        declared = root / entry
        declared.parent.mkdir(parents=True, exist_ok=True)
        if not declared.exists():
            declared.write_text("fixture\n", encoding="utf-8")
    targets = "\n".join(f"  - {entry}" for entry in target_files)
    depends_block = ""
    if depends_on:
        refs = "\n".join(f"  - {ref}" for ref in depends_on)
        depends_block = f"depends_on:\n{refs}\n"
    path.write_text(
        f"""---
unit_id: {unit_id}
task_id: {task_id}
task_set_id: {TASKSET}
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: {status}
horizon: unit
model_tier: worker_standard
context: "Wave dispatcher fixture unit."
inputs:
  - agents/lead_engineer/tasks/{task_id}.md
target_files:
{targets}
{depends_block}scope: "Only this fixture unit."
acceptance:
  - "It passes."
verification:
  - "python -m pytest tests/test_wave_dispatcher.py -q"
handoff: "Report the result."
stop_condition: "stop_after:{unit_id}:no_adjacent_taskset"
---

# {unit_id}

## Context

Wave dispatcher fixture unit.

## Inputs

- agents/lead_engineer/tasks/{task_id}.md

## Target Files

{targets}

## Scope

Only this fixture unit.

## Steps

1. Edit.
2. Verify.

## Acceptance Criteria

- It passes.

## Verification

- python -m pytest tests/test_wave_dispatcher.py -q

## Handoff

Report the result.

## Stop Boundary

Stop after this unit.
""",
        encoding="utf-8",
    )
    return unit_id


def test_plan_groups_dependent_units_into_later_waves(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901")
    _write_task(tmp_path, "TASK-AR-902")
    _write_task(tmp_path, "TASK-AR-903")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"])
    u2 = _write_unit(tmp_path, "TASK-AR-902", 1, target_files=["scripts/b.py"], depends_on=[u1])
    u3 = _write_unit(tmp_path, "TASK-AR-903", 1, target_files=["docs/c.md"])

    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    waves = [[unit["unit_id"] for unit in wave] for wave in payload["waves"]]
    assert waves == [[u1, u3], [u2]]
    assert payload["deferrals"] == []


def test_plan_task_id_dependency_orders_after_all_units_of_that_task(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901")
    _write_task(tmp_path, "TASK-AR-902")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"])
    u2 = _write_unit(tmp_path, "TASK-AR-901", 2, target_files=["scripts/b.py"])
    u3 = _write_unit(tmp_path, "TASK-AR-902", 1, target_files=["docs/c.md"], depends_on=["TASK-AR-901"])

    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    waves = [[unit["unit_id"] for unit in wave] for wave in json.loads(result.stdout)["waves"]]
    assert waves == [[u1, u2], [u3]]


def test_plan_defers_footprint_conflicts_to_a_later_wave(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901")
    _write_task(tmp_path, "TASK-AR-902")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/shared.py"])
    u2 = _write_unit(tmp_path, "TASK-AR-902", 1, target_files=["scripts/shared.py"])

    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    waves = [[unit["unit_id"] for unit in wave] for wave in payload["waves"]]
    assert waves == [[u1], [u2]]
    assert len(payload["deferrals"]) == 1
    deferral = payload["deferrals"][0]
    assert deferral["unit_id"] == u2
    assert deferral["conflicts_with"] == u1
    assert deferral["deferred_from_wave"] == 1
    assert "scripts/shared.py <-> scripts/shared.py" in deferral["overlap"]


def test_plan_reports_dependency_cycle_as_clear_error(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901")
    _write_task(tmp_path, "TASK-AR-902")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"], depends_on=["UNIT-TASK-AR-902-001"])
    u2 = _write_unit(tmp_path, "TASK-AR-902", 1, target_files=["scripts/b.py"], depends_on=[u1])

    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")

    assert result.returncode == 1
    assert "dependency cycle detected" in result.stderr
    assert u1 in result.stderr
    assert u2 in result.stderr


def test_plan_rejects_unknown_depends_on_reference(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901")
    _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"], depends_on=["UNIT-TASK-AR-999-001"])

    result = _run(tmp_path, "--taskset", TASKSET, "--plan", "--json")

    assert result.returncode == 1
    assert "unknown depends_on reference" in result.stderr
    assert "UNIT-TASK-AR-999-001" in result.stderr


def test_plan_is_read_only_and_creates_no_side_effects(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901")
    _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"])

    result = _run(tmp_path, "--taskset", TASKSET, "--plan")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "wave-dispatcher: plan" in result.stdout
    assert not (tmp_path / "agents" / "runtime" / "task_claims").exists()
    assert not (tmp_path / "agents" / "runtime" / "pane_events").exists()
    assert not (tmp_path / ".worktrees").exists()


def test_plan_accepts_explicit_unit_list(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901")
    _write_task(tmp_path, "TASK-AR-902")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"])
    u2 = _write_unit(tmp_path, "TASK-AR-902", 1, target_files=["scripts/b.py"], depends_on=[u1])

    result = _run(tmp_path, "--unit", u1, "--unit", u2, "--plan", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    waves = [[unit["unit_id"] for unit in wave] for wave in json.loads(result.stdout)["waves"]]
    assert waves == [[u1], [u2]]


def test_dispatch_parallel_batch_creates_claims_and_worktrees(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    _write_task(tmp_path, "TASK-AR-901")
    _write_task(tmp_path, "TASK-AR-902")
    _write_task(tmp_path, "TASK-AR-903")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"])
    u2 = _write_unit(tmp_path, "TASK-AR-902", 1, target_files=["scripts/b.py"])
    _write_unit(tmp_path, "TASK-AR-903", 1, target_files=["docs/c.md"])

    result = _run(
        tmp_path,
        "--taskset",
        TASKSET,
        "--dispatch",
        "--mode",
        "parallel",
        "--max-panes",
        "2",
        "--now",
        "2026-06-13T10:00:00+09:00",
        "--suffix",
        "wv1",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["mode"] == "parallel"
    assert payload["wave"] == 1
    issued = payload["issued"]
    assert [entry["unit_id"] for entry in issued] == [u1, u2]
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("CLAIM-*.json"))
    assert len(claim_files) == 2
    for entry in issued:
        assert entry["claim_id"]
        worktree = tmp_path / entry["worktree_path"]
        assert worktree.is_dir()
        assert (worktree / ".git").exists()
    claims = [json.loads(path.read_text(encoding="utf-8")) for path in claim_files]
    assert {claim["unit_id"] for claim in claims} == {u1, u2}
    for claim in claims:
        assert claim["target_files"], claim["unit_id"]

    # Claim creation logs pane events itself; the wave dispatcher must not double-log.
    event_log = tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    created = [event for event in events if event.get("event") == "claim_created"]
    assert len(created) == 2


def test_dispatch_cascade_issues_exactly_one_unit(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    _write_task(tmp_path, "TASK-AR-901")
    _write_task(tmp_path, "TASK-AR-902")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"])
    _write_unit(tmp_path, "TASK-AR-902", 1, target_files=["scripts/b.py"])

    result = _run(
        tmp_path,
        "--taskset",
        TASKSET,
        "--dispatch",
        "--mode",
        "cascade",
        "--now",
        "2026-06-13T11:00:00+09:00",
        "--suffix",
        "wv2",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["mode"] == "cascade"
    issued = payload["issued"]
    assert [entry["unit_id"] for entry in issued] == [u1]
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("CLAIM-*.json"))
    assert len(claim_files) == 1


def test_status_reports_wave_boundary_guidance_after_wave_completes(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", status="completed")
    _write_task(tmp_path, "TASK-AR-902")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"], status="completed")
    u2 = _write_unit(tmp_path, "TASK-AR-902", 1, target_files=["scripts/b.py"], depends_on=[u1])

    result = _run(tmp_path, "--taskset", TASKSET, "--status", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["current_wave"] == 2
    assert payload["waves"][0]["state"] == "complete"
    assert payload["waves"][1]["unit_states"][u2] == "pending"
    assert any("wave-boundary" in line for line in payload["guidance"])
    assert any("full-cycle" in line for line in payload["guidance"])


def _run_readiness_gate(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    gate = REPO_ROOT / "scripts" / "task_unit_readiness_gate.py"
    return subprocess.run(
        [sys.executable, str(gate), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_readiness_gate_flags_unknown_and_self_depends_on_refs(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901")
    u1 = _write_unit(
        tmp_path,
        "TASK-AR-901",
        1,
        target_files=["scripts/a.py"],
        depends_on=["UNIT-TASK-AR-901-001", "UNIT-TASK-AR-999-001"],
    )

    result = _run_readiness_gate(tmp_path, "--task-id", "TASK-AR-901", "--check")

    assert result.returncode == 1
    assert f"unit:depends-on-self:{u1}" in result.stdout
    assert "unit:depends-on-unknown-ref:UNIT-TASK-AR-999-001" in result.stdout


def test_readiness_gate_accepts_existing_unit_and_task_refs(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901")
    _write_task(tmp_path, "TASK-AR-902")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"])
    _write_unit(tmp_path, "TASK-AR-902", 1, target_files=["scripts/b.py"], depends_on=[u1, "TASK-AR-901"])

    result = _run_readiness_gate(tmp_path, "--task-id", "TASK-AR-902", "--require-ready", "--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "task-unit-readiness-gate: pass" in result.stdout


def test_template_mirror_is_identical() -> None:
    root_script = SCRIPT.read_text(encoding="utf-8")
    template_script = TEMPLATE_SCRIPT.read_text(encoding="utf-8")
    assert root_script == template_script


def test_readiness_gate_template_mirror_is_identical() -> None:
    root = (REPO_ROOT / "scripts" / "task_unit_readiness_gate.py").read_text(encoding="utf-8")
    template = (
        REPO_ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "task_unit_readiness_gate.py"
    ).read_text(encoding="utf-8")
    assert root == template


def test_units_readme_mirrors_document_depends_on() -> None:
    for path in (
        REPO_ROOT / "agents" / "lead_engineer" / "tasks" / "units" / "README.md",
        REPO_ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "README.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "## Optional Frontmatter" in text, path
        assert "depends_on" in text, path


# TASK-230 host golden oracles. Keep these fixtures namespaced so the
# original upstream tests retain their late-bound module globals.
def _host_write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _host_write_taskset(
    root: Path,
    taskset: str = HOST_TASKSET,
    *,
    filename: str | None = None,
    schema: str = "agent-runtime-work-item/v1",
    kind: str = "taskset",
    title: str = "Dynamic Wave",
) -> None:
    _host_write(
        root / "agents/project/initiatives" / f"{filename or taskset}.md",
        [
            "---",
            f"schema_version: {schema}",
            f"work_id: {taskset}",
            f"kind: {kind}",
            f"title: {title}",
            "summary: Test lane.",
            "---",
        ],
    )


def _host_write_task(
    root: Path,
    task: str,
    *,
    taskset: str = HOST_TASKSET,
    status: str = "planned",
) -> None:
    _host_write(
        root / "agents/lead_engineer/tasks" / f"{task}.md",
        [
            "---",
            f"id: {task}",
            f"status: {status}",
            "priority: P1",
            "difficulty: M",
            "est_hours: 2",
            "est_tokens: 200",
            f"task_set_id: {taskset}",
            f"project_id: {HOST_PROJECT}",
            "tags: [test]",
            "---",
        ],
    )


def _host_write_unit(
    root: Path,
    task: str,
    index: int = 1,
    *,
    taskset: str = HOST_TASKSET,
    targets: list[str] | None = None,
    depends: list[str] | None = None,
    status: str = "worker_ready",
    metadata: dict[str, object] | None = None,
) -> str:
    unit = f"UNIT-{task}-{index:03d}"
    selected_targets = targets or [f"scripts/{task.lower()}.py"]
    for target in selected_targets:
        if target.startswith("new:") or "*" in target:
            continue
        path = root / target
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("fixture\n", encoding="utf-8")
    fields: dict[str, object] = {
        "unit_id": unit,
        "task_id": task,
        "task_set_id": taskset,
        "project_id": HOST_PROJECT,
        "status": status,
        "model_tier": "worker_standard",
        "context": "Wave dispatcher host fixture.",
        "inputs": [f"agents/lead_engineer/tasks/{task}.md"],
        "target_files": selected_targets,
        "scope": "Only this host fixture.",
        "acceptance": ["Dispatch is safe."],
        "verification": ["pytest"],
        "handoff": "Report the result.",
        "stop_condition": f"stop_after:{unit}:no_adjacent_taskset",
    }
    if depends:
        fields["depends_on"] = depends
    fields.update(metadata or {})
    encoded = [
        f"{key}: [{', '.join(value)}]" if isinstance(value, list) else f"{key}: {value}"
        for key, value in fields.items()
    ]
    _host_write(
        root / "agents/lead_engineer/tasks/units" / task / f"{unit}.md",
        [
            "---",
            *encoded,
            "---",
            "",
            "## Context",
            "",
            "Wave dispatcher host fixture.",
            "",
            "## Inputs",
            "",
            f"- agents/lead_engineer/tasks/{task}.md",
            "",
            "## Target Files",
            "",
            *(f"- {target}" for target in selected_targets),
            "",
            "## Scope",
            "",
            "Only this host fixture.",
            "",
            "## Steps",
            "",
            "1. Dispatch safely.",
            "",
            "## Acceptance Criteria",
            "",
            "- Dispatch is safe.",
            "",
            "## Verification",
            "",
            "- pytest",
            "",
            "## Handoff",
            "",
            "Report the result.",
            "",
            "## Stop Boundary",
            "",
            "Stop after this fixture.",
        ],
    )
    return unit


def _host_run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOST_SCRIPTS / "wave_dispatcher.py"), "--root", str(root), *args],
        cwd=HOST_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_routing_off_env(),
    )


def _host_init_repo(root: Path) -> None:
    def git(*args: str) -> int:
        return subprocess.run(["git", "-C", str(root), *args], check=False).returncode

    assert git("init", "-q") == 0
    assert git("config", "user.email", "wave-test@example.com") == 0
    assert git("config", "user.name", "Wave Test") == 0
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    assert git("add", "-A") == git("commit", "-q", "-m", "init") == 0
    assert git("update-ref", "refs/remotes/origin/main", "HEAD") == 0


def test_plan_resolves_canonical_id_and_slug_to_same_validated_units(tmp_path: Path) -> None:
    _host_write_taskset(tmp_path)
    _host_write_task(tmp_path, "TASK-901")
    unit_id = _host_write_unit(tmp_path, "TASK-901")

    canonical = _host_run(tmp_path, "--taskset", HOST_TASKSET, "--plan", "--json")
    slug = _host_run(tmp_path, "--taskset", "dynamic-wave", "--plan", "--json")

    assert canonical.returncode == slug.returncode == 0
    first, second = json.loads(canonical.stdout), json.loads(slug.stdout)
    assert first == second
    unit = first["waves"][0][0]
    assert first["selection"] == f"taskset:{HOST_TASKSET}"
    assert unit["unit_id"] == unit_id
    assert unit["repository_path"] == str(tmp_path.resolve())
    assert unit["worktree_path"] == ".worktrees/TASK-901"
    assert unit["base_ref"] == ""


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [({"schema": "wrong/v1"}, "schema_version"), ({"kind": "initiative"}, "kind"),
     ({"filename": "TASKSET-WRONG"}, "filename")],
)
def test_plan_rejects_malformed_canonical_taskset(
    tmp_path: Path, kwargs: dict[str, str], message: str
) -> None:
    _host_write_taskset(tmp_path, **kwargs)
    _host_write_task(tmp_path, "TASK-901")
    _host_write_unit(tmp_path, "TASK-901")
    result = _host_run(tmp_path, "--taskset", HOST_TASKSET, "--plan", "--json")
    assert result.returncode == 1
    assert "invalid canonical task set record" in result.stderr
    assert message in result.stderr


def test_plan_rejects_duplicate_canonical_aliases(tmp_path: Path) -> None:
    _host_write_taskset(tmp_path, "TASKSET-ONE", title="Shared Lane")
    _host_write_taskset(tmp_path, "TASKSET-TWO", title="Shared Lane")
    result = _host_run(tmp_path, "--taskset", "TASKSET-ONE", "--plan", "--json")
    assert result.returncode == 1
    assert "duplicate task set alias" in result.stderr


def _host_external(root: Path) -> tuple[dict[str, object], Path, Path]:
    repo = (root / "external").resolve()
    repo.mkdir()
    worktree = repo / ".worktrees/TASK-901"
    return {
        "repository_path": str(repo),
        "worktree_path": str(worktree),
        "branch": "fix/task-901",
        "base_ref": "origin/main",
    }, repo, worktree


def test_plan_uses_complete_structured_external_tuple(tmp_path: Path) -> None:
    metadata, repo, worktree = _host_external(tmp_path)
    _host_write_taskset(tmp_path)
    _host_write_task(tmp_path, "TASK-901")
    _host_write_unit(tmp_path, "TASK-901", metadata=metadata)
    result = _host_run(tmp_path, "--taskset", HOST_TASKSET, "--plan", "--json")
    unit = json.loads(result.stdout)["waves"][0][0]
    assert result.returncode == 0
    assert (unit["repository_path"], unit["worktree_path"], unit["branch"], unit["base_ref"]) == (
        str(repo), str(worktree), "fix/task-901", "origin/main"
    )
    assert unit["adopt_existing_branch"] is False


def test_plan_and_dispatch_payload_preserve_adopt_existing_branch(tmp_path: Path) -> None:
    metadata, repo, _worktree = _host_external(tmp_path)
    _host_init_repo(repo)
    metadata["adopt_existing_branch"] = True
    _host_write_taskset(tmp_path)
    _host_write_task(tmp_path, "TASK-901")
    _host_write_unit(tmp_path, "TASK-901", metadata=metadata)

    result = _host_run(tmp_path, "--taskset", HOST_TASKSET, "--plan", "--json")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["waves"][0][0]["adopt_existing_branch"] is True
    node = _host_node(tmp_path, metadata=metadata)
    payload = host_dispatcher._dispatch_payload(  # noqa: SLF001
        tmp_path,
        node,
        wave_no=1,
        args=_host_args(tmp_path),
        allow_parallel_task_set=False,
        suffix=None,
    )
    assert payload["adopt_existing_branch"] is True


@pytest.mark.parametrize("missing", ["repository_path", "worktree_path", "branch", "base_ref"])
def test_plan_rejects_partial_structured_tuple(tmp_path: Path, missing: str) -> None:
    metadata, _, _ = _host_external(tmp_path)
    metadata.pop(missing)
    _host_write_taskset(tmp_path)
    _host_write_task(tmp_path, "TASK-901")
    _host_write_unit(tmp_path, "TASK-901", metadata=metadata)
    result = _host_run(tmp_path, "--taskset", HOST_TASKSET, "--plan", "--json")
    assert result.returncode == 1
    assert missing in result.stderr
    assert "structured worktree metadata must define all fields" in result.stderr


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        ({"repository_path": "/tmp/repo", "worktree_path": "/tmp/out/TASK-901",
          "branch": "fix/task", "base_ref": "origin/main"}, "worktree_path must be under"),
        ({"repository_path": "/tmp/repo", "worktree_path": "/tmp/repo/.worktrees/TASK-901",
          "branch": "main", "base_ref": "origin/main"}, "protected branch"),
        ({"repository_path": "/tmp/repo", "worktree_path": "/tmp/repo/.worktrees/TASK-901",
          "branch": "fix/task", "base_ref": "--unsafe"}, "unsafe base_ref"),
    ],
)
def test_plan_rejects_unsafe_structured_tuple(
    tmp_path: Path, metadata: dict[str, str], message: str
) -> None:
    repository = str((tmp_path / "repository").resolve())
    outside = str((tmp_path / "outside").resolve())
    metadata = {
        key: value.replace("/tmp/repo", repository).replace("/tmp/out", outside)
        for key, value in metadata.items()
    }
    _host_write_taskset(tmp_path)
    _host_write_task(tmp_path, "TASK-901")
    _host_write_unit(tmp_path, "TASK-901", metadata=metadata)
    result = _host_run(tmp_path, "--taskset", HOST_TASKSET, "--plan", "--json")
    assert result.returncode == 1
    assert message in result.stderr


def test_plan_preserves_static_alias_explicit_dag_and_footprint(tmp_path: Path) -> None:
    taskset = "TASKSET-AR-QUALITY-LOOP"
    for task in ("TASK-AR-901", "TASK-AR-902"):
        _host_write_task(tmp_path, task, taskset=taskset)
    first = _host_write_unit(tmp_path, "TASK-AR-901", taskset=taskset, targets=["shared.py"])
    second = _host_write_unit(tmp_path, "TASK-AR-902", taskset=taskset, targets=["shared.py"])
    alias = _host_run(tmp_path, "--taskset", "quality-loop", "--plan", "--json")
    explicit = _host_run(tmp_path, "--unit", first, "--unit", second, "--plan", "--json")
    assert alias.returncode == explicit.returncode == 0
    assert [[u["unit_id"] for u in wave] for wave in json.loads(alias.stdout)["waves"]] == [
        [first], [second]
    ]
    assert json.loads(explicit.stdout)["deferrals"][0]["conflicts_with"] == first


def test_status_preserves_wave_boundary_guidance(tmp_path: Path) -> None:
    _host_write_taskset(tmp_path)
    _host_write_task(tmp_path, "TASK-901", status="completed")
    _host_write_task(tmp_path, "TASK-902")
    first = _host_write_unit(tmp_path, "TASK-901", status="completed")
    second = _host_write_unit(tmp_path, "TASK-902", depends=[first])
    result = _host_run(tmp_path, "--taskset", HOST_TASKSET, "--status", "--json")
    payload = json.loads(result.stdout)
    assert payload["current_wave"] == 2
    assert payload["waves"][1]["unit_states"][second] == "pending"
    assert {line.split(":", 1)[0] for line in payload["guidance"]} == {
        "wave-boundary", "full-cycle"
    }


@pytest.mark.parametrize(
    ("mode", "panes", "expected"),
    [("cascade", "1", ["TASK-901"]), ("parallel", "2", ["TASK-901", "TASK-902"])],
)
def test_dispatch_preserves_cascade_and_parallel_contracts(
    tmp_path: Path, mode: str, panes: str, expected: list[str]
) -> None:
    _host_init_repo(tmp_path)
    _host_write_taskset(tmp_path)
    for task in ("TASK-901", "TASK-902"):
        _host_write_task(tmp_path, task)
        _host_write_unit(tmp_path, task, targets=[f"{task}.py"])
    result = _host_run(
        tmp_path, "--taskset", HOST_TASKSET, "--dispatch", "--mode", mode,
        "--max-panes", panes, "--now", "2026-07-14T21:00:00+09:00",
        "--suffix", mode, "--json",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert [item["task_id"] for item in payload["issued"]] == expected
    claims = [json.loads(path.read_text()) for path in
              (tmp_path / "agents/runtime/task_claims").glob("*.json")]
    assert {claim["mode"] for claim in claims} == {"orchestrator"}
    assert {claim["task_id"] for claim in claims} == set(expected)
    assert all((tmp_path / item["worktree_path"] / ".git").exists() for item in payload["issued"])


def _host_args(root: Path, mode: str = "cascade") -> argparse.Namespace:
    return argparse.Namespace(
        root=root, taskset=HOST_TASKSET, unit=[], mode=mode, max_panes=2,
        agent_role="", team_id="", now=None, suffix=None, json=True,
    )


def _host_node(
    root: Path,
    task: str = "TASK-901",
    metadata: dict[str, object] | None = None,
) -> host_dispatcher.UnitNode:
    unit = f"UNIT-{task}-001"
    meta: dict[str, object] = {
        "unit_id": unit, "task_id": task, "task_set_id": HOST_TASKSET,
        "project_id": HOST_PROJECT, "status": "worker_ready", "model_tier": "worker_standard",
        "target_files": [f"{task}.py"], "stop_condition": f"stop_after:{unit}",
    }
    meta.update(metadata or {})
    return host_dispatcher.UnitNode(root / f"{unit}.md", meta)


def _host_prepare(monkeypatch: pytest.MonkeyPatch, root: Path, nodes: list[host_dispatcher.UnitNode]) -> None:
    monkeypatch.delenv("AGENT_RUNTIME_GIT", raising=False)
    plan = host_dispatcher.WavePlan(nodes, [nodes], [])
    monkeypatch.setattr(host_dispatcher, "select_units", lambda *_a, **_k: (nodes, f"taskset:{HOST_TASKSET}"))
    monkeypatch.setattr(host_dispatcher, "compute_waves", lambda *_a, **_k: plan)
    monkeypatch.setattr(host_dispatcher, "_load_claims", lambda _root: [])
    monkeypatch.setattr(
        host_dispatcher,
        "_candidate_preflight_findings",
        lambda *_a, **_k: [],
    )
    monkeypatch.setattr(host_dispatcher, "role_routing", None)


def _host_claim_result(
    root: Path, node: host_dispatcher.UnitNode, worktree: Path, *, persist: bool = True,
    returncode: int = 0, stdout: str | None = None,
    persisted: dict[str, str] | None = None, declared: dict[str, str] | None = None,
    path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    if returncode:
        return subprocess.CompletedProcess(["claim"], returncode, "", "claim refused\n")
    claim_id = f"CLAIM-test-{node.task_id.lower()}"
    claim_path = path or root / "agents/runtime/task_claims" / f"{claim_id}.json"
    claim = {
        "claim_id": claim_id, "task_id": node.task_id, "task_set_id": node.task_set_id,
        "unit_id": node.unit_id, "project_id": node.project_id, "status": "claimed",
        "mode": "orchestrator", "worktree_path": str(worktree), "branch": "fix/task-901",
    }
    claim.update(persisted or {})
    if persist:
        _host_write(claim_path, [json.dumps(claim)])
    response = {**claim, **(declared or {})}
    envelope = {
        "status": "created",
        "path": claim_path.relative_to(root).as_posix() if claim_path.is_relative_to(root) else str(claim_path),
        "claim": response,
    }
    return subprocess.CompletedProcess(["claim"], 0, stdout or json.dumps(envelope), "")


def _host_success_runner(
    root: Path, node: host_dispatcher.UnitNode, worktree: Path,
    calls: list[tuple[str, Path]], *, fail_git: bool = False,
):
    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((command[0], Path(str(kwargs["cwd"]))))
        if command[0] != "git":
            return _host_claim_result(root, node, worktree)
        if fail_git:
            return subprocess.CompletedProcess(command, 23, "", "worktree failed\n")
        worktree.mkdir(parents=True)
        (worktree / ".git").write_text("gitdir: fake\n")
        return subprocess.CompletedProcess(command, 0, "", "")
    return run


def test_claim_command_uses_orchestrator_reservation_mode(tmp_path: Path) -> None:
    command = host_dispatcher._claim_command(
        tmp_path, _host_node(tmp_path), wave_no=1, worktree_path=".worktrees/TASK-901",
        branch="fix/task-901", args=_host_args(tmp_path), allow_parallel_task_set=False, suffix=None,
    )
    assert command[command.index("--mode") + 1] == "orchestrator"
    assert command[-1] == "--json"


def test_claim_command_propagates_explicit_scope_transition_approval(
    tmp_path: Path,
) -> None:
    args = _host_args(tmp_path)
    args.scope_transition_approved = True

    command = host_dispatcher._claim_command(
        tmp_path,
        _host_node(tmp_path),
        wave_no=1,
        worktree_path=".worktrees/TASK-901",
        branch="fix/task-901",
        args=args,
        allow_parallel_task_set=False,
        suffix=None,
    )

    assert "--scope-transition-approved" in command
    assert command[-1] == "--json"


def test_dispatch_preflights_all_candidates_before_claim_or_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nodes = [_host_node(tmp_path), _host_node(tmp_path, "TASK-902", {"repository_path": "/tmp/repo"})]
    _host_prepare(monkeypatch, tmp_path, nodes)
    calls: list[list[str]] = []
    monkeypatch.setattr(host_dispatcher.subprocess, "run", lambda command, **_k: calls.append(command))
    with pytest.raises(SystemExit, match="structured worktree metadata must define all fields"):
        host_dispatcher.cmd_dispatch(_host_args(tmp_path, "parallel"))
    assert calls == []


HOST_FAILURES = [
    ("process", "claim refused"), ("json", "invalid JSON"),
    ("missing", "persisted claim is missing"), ("inactive", "not active"),
    ("task", "field mismatch: task_id"), ("taskset", "field mismatch: task_set_id"),
    ("unit", "field mismatch: unit_id"), ("project", "field mismatch: project_id"),
    ("worktree", "field mismatch: worktree_path"), ("branch", "field mismatch: branch"),
    ("mode", "field mismatch: mode"), ("status", "field mismatch: status"),
    ("path", "field mismatch: path"), ("outside", "persisted claim path is outside"),
]


@pytest.mark.parametrize(("case", "message"), HOST_FAILURES)
def test_claim_failures_never_run_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    case: str, message: str,
) -> None:
    metadata, _, worktree = _host_external(tmp_path)
    node = _host_node(tmp_path, metadata=metadata)
    _host_prepare(monkeypatch, tmp_path, [node])
    bad = {
        "task": ("task_id", "TASK-X", node.task_id),
        "taskset": ("task_set_id", "TASKSET-X", node.task_set_id),
        "unit": ("unit_id", "UNIT-X", node.unit_id),
        "project": ("project_id", "PROJECT-X", node.project_id),
        "worktree": ("worktree_path", str(worktree.parent / "X"), str(worktree)),
        "branch": ("branch", "fix/x", "fix/task-901"),
        "mode": ("mode", "wave", "orchestrator"),
    }

    def run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        assert command[0] != "git"
        if case == "process":
            return _host_claim_result(tmp_path, node, worktree, returncode=17)
        if case == "json":
            return _host_claim_result(tmp_path, node, worktree, stdout="{bad")
        if case == "missing":
            return _host_claim_result(tmp_path, node, worktree, persist=False)
        if case == "inactive":
            return _host_claim_result(tmp_path, node, worktree, persisted={"status": "released"})
        if case in bad:
            field, persisted, declared = bad[case]
            return _host_claim_result(
                tmp_path, node, worktree,
                persisted={field: persisted}, declared={field: declared},
            )
        if case == "status":
            return _host_claim_result(
                tmp_path, node, worktree,
                persisted={"status": "assigned"}, declared={"status": "claimed"},
            )
        if case == "path":
            return _host_claim_result(
                tmp_path, node, worktree,
                path=tmp_path / "agents/runtime/task_claims/CLAIM-wrong.json",
            )
        return _host_claim_result(tmp_path, node, worktree, path=tmp_path.parent / "outside.json")

    monkeypatch.setattr(host_dispatcher.subprocess, "run", run)
    assert host_dispatcher.cmd_dispatch(_host_args(tmp_path)) != 0
    assert message in capsys.readouterr().err


def test_dispatch_creates_external_worktree_once_after_exact_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    metadata, repo, worktree = _host_external(tmp_path)
    node = _host_node(tmp_path, metadata=metadata)
    _host_prepare(monkeypatch, tmp_path, [node])
    calls: list[tuple[str, Path]] = []
    monkeypatch.setattr(host_dispatcher.subprocess, "run", _host_success_runner(tmp_path, node, worktree, calls))
    assert host_dispatcher.cmd_dispatch(_host_args(tmp_path)) == 0
    assert [call[0] for call in calls] == [sys.executable, "git"]
    assert calls[1][1] == repo
    assert json.loads(capsys.readouterr().out)["issued"][0]["worktree_path"] == str(worktree)


def test_dispatch_preserves_dormant_role_routing_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metadata, _, worktree = _host_external(tmp_path)
    node = _host_node(tmp_path, metadata=metadata)
    _host_prepare(monkeypatch, tmp_path, [node])
    routed: list[dict[str, object]] = []

    class Routing:
        dispatch_wave_hooks = staticmethod(lambda _root, **kwargs: routed.append(kwargs))

    monkeypatch.setattr(host_dispatcher.subprocess, "run", _host_success_runner(tmp_path, node, worktree, []))
    monkeypatch.setattr(host_dispatcher, "role_routing", Routing())
    assert host_dispatcher.cmd_dispatch(_host_args(tmp_path)) == 0
    assert routed == [{"task_set_id": HOST_TASKSET, "wave_no": 1, "is_w6": False, "now": None}]


def test_worktree_failure_reports_claim_id_and_retry_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    metadata, _, worktree = _host_external(tmp_path)
    node = _host_node(tmp_path, metadata=metadata)
    _host_prepare(monkeypatch, tmp_path, [node])
    calls: list[tuple[str, Path]] = []
    monkeypatch.setattr(
        host_dispatcher.subprocess, "run", _host_success_runner(tmp_path, node, worktree, calls, fail_git=True)
    )
    assert host_dispatcher.cmd_dispatch(_host_args(tmp_path)) == 1
    assert [call[0] for call in calls] == [sys.executable, "git"]
    stderr = capsys.readouterr().err
    assert "CLAIM-test-task-901" in stderr and "retry" in stderr and "release" in stderr
