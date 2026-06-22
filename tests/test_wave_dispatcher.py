from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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


def _routing_off_env() -> dict[str, str]:
    """Pin the dormant-role routing flags OFF so these baseline tests assert the
    unchanged dispatch behavior deterministically, regardless of an ambient flag
    in the developer's shell (the live flags are exercised in
    tests/test_role_routing_wiring.py)."""
    env = dict(os.environ)
    for flag in ("AR_ROLE_ROUTING", "AR_SCOUT_COUNCIL", "AR_BETA_ACTIVATION"):
        env.pop(flag, None)
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


def _write_task(root: Path, task_id: str, *, status: str = "planned") -> None:
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
