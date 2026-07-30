from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import taskset_dispatcher as dispatcher  # noqa: E402


def _write_task(
    root: Path,
    task_id: str,
    task_set_id: str,
    *,
    status: str = "planned",
    priority: str = "P1",
    depends_on: list[str] | None = None,
) -> None:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    dependency_line = (
        f"depends_on: [{', '.join(depends_on)}]\n" if depends_on is not None else ""
    )
    (tasks_dir / f"{task_id}.md").write_text(
        f"""---
id: {task_id}
status: {status}
priority: {priority}
difficulty: M
est_hours: 2
est_tokens: 200
task_set_id: {task_set_id}
project_id: PROJECT-TEST
{dependency_line}tags: [test]
---

## Goal

Test task for {task_set_id}.
""",
        encoding="utf-8",
    )


def _write_taskset(
    root: Path,
    task_set_id: str,
    *,
    filename: str | None = None,
    schema_version: str = "agent-runtime-work-item/v1",
    kind: str = "taskset",
    title: str = "Runtime Liaison",
    tasks: list[str] | str | None = None,
    status: str = "active",
) -> None:
    tasksets_dir = root / "agents" / "project" / "initiatives"
    tasksets_dir.mkdir(parents=True, exist_ok=True)
    target = tasksets_dir / f"{filename or task_set_id}.md"
    if tasks is None:
        task_lines = ""
    elif isinstance(tasks, list) and tasks:
        task_lines = "tasks:\n" + "".join(f"  - {task_id}\n" for task_id in tasks)
    elif isinstance(tasks, list):
        task_lines = "tasks: []\n"
    else:
        task_lines = f"tasks: {tasks}\n"
    target.write_text(
        f"""---
schema_version: {schema_version}
work_id: {task_set_id}
kind: {kind}
title: {title}
summary: Test dynamic task set.
status: {status}
{task_lines}---
""",
        encoding="utf-8",
    )


def _write_unit(
    root: Path,
    task_id: str,
    *,
    status: str = "worker_ready",
    **metadata: str | bool | list[str],
) -> None:
    units_dir = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id
    units_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"unit_id: UNIT-{task_id}-001",
        f"task_id: {task_id}",
        f"status: {status}",
        "model_tier: worker_standard",
    ]
    for key, value in metadata.items():
        if isinstance(value, list):
            encoded = f"[{', '.join(value)}]"
        elif isinstance(value, bool):
            encoded = str(value).lower()
        else:
            encoded = value
        lines.append(f"{key}: {encoded}")
    lines.extend(["---", ""])
    (units_dir / f"UNIT-{task_id}-001.md").write_text("\n".join(lines), encoding="utf-8")


def _write_dispatch_ready_unit(
    root: Path,
    task_id: str,
    task_set_id: str,
    *,
    status: str,
) -> Path:
    units_dir = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id
    units_dir.mkdir(parents=True, exist_ok=True)
    unit_id = f"UNIT-{task_id}-001"
    path = units_dir / f"{unit_id}.md"
    path.write_text(
        f"""---
unit_id: {unit_id}
task_id: {task_id}
task_set_id: {task_set_id}
project_id: PROJECT-TEST
status: {status}
model_tier: worker_standard
context: Test localized ready dispatch.
inputs: [README.md]
target_files: [README.md]
scope: Test only.
acceptance: [Start succeeds.]
verification: [pytest]
handoff: Report result.
stop_condition: stop_after:{unit_id}:test
---

## Context

Localized ready start fixture.

## Inputs

- README.md

## Target Files

- README.md

## Scope

Test only.

## Steps

1. Start the taskset.

## Acceptance Criteria

- Start succeeds.

## Verification

- pytest

## Handoff

Report result.

## Stop Boundary

Stop after this test.
""",
        encoding="utf-8",
    )
    return path


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "taskset_dispatcher.py"), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _tree_snapshot(root: Path) -> tuple[tuple[str, ...], dict[str, bytes]]:
    directories = tuple(
        sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())
    )
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    return directories, files


def _write_t0(root: Path, taskset: str, anchor: str) -> None:
    target = root / anchor
    payload = {
        "schema": "agent-runtime-plan-assumptions/v1",
        "updated_at": "2026-07-14T18:49:00+09:00",
        "assumption_sets": [
            {
                "taskset_id": taskset,
                "design_record": anchor,
                "recorded_at": "2026-07-14T18:49:00+09:00",
                "revalidation_policy": "block_dispatch_on_drift",
                "anchors": [
                    {
                        "path": anchor,
                        "kind": "sha256",
                        "value": hashlib.sha256(target.read_bytes()).hexdigest(),
                    }
                ],
            }
        ],
    }
    path = root / "agents/project/work-items/PLAN-ASSUMPTIONS.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("task_status", "unit_status", "taskset_status", "reason"),
    [
        ("planned", "planned", "active", "unit_not_ready"),
        ("planned", "blocked", "active", "unit_blocked"),
        ("planned", "held", "active", "unit_blocked"),
        ("planned", "blocked/R3", "active", "unit_blocked"),
        ("보류", "worker_ready", "active", "task_blocked"),
        ("held", "worker_ready", "active", "task_blocked"),
        ("blocked/R3", "worker_ready", "active", "task_blocked"),
        ("planned", "worker_ready", "blocked", "taskset_blocked"),
        ("planned", "worker_ready", "held", "taskset_blocked"),
        ("planned", "worker_ready", "blocked/R3", "taskset_blocked"),
    ],
)
def test_plan_refuses_non_dispatchable_status_before_claim_command_without_mutation(
    tmp_path: Path,
    task_status: str,
    unit_status: str,
    taskset_status: str,
    reason: str,
) -> None:
    taskset = "TASKSET-DISPATCH-REFUSAL"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901"], status=taskset_status)
    _write_task(tmp_path, "TASK-901", taskset, status=task_status)
    _write_unit(tmp_path, "TASK-901", status=unit_status)
    before = _tree_snapshot(tmp_path)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert result.stdout == ""
    refusal = json.loads(result.stderr)
    assert refusal["status"] == "refused"
    assert refusal["reason"] == reason
    assert "claim_command" not in refusal
    assert _tree_snapshot(tmp_path) == before


def test_start_refuses_planned_unit_before_subprocess_or_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    taskset = "TASKSET-DISPATCH-START-REFUSAL"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_unit(tmp_path, "TASK-901", status="planned")
    before = _tree_snapshot(tmp_path)
    args = argparse.Namespace(
        root=tmp_path,
        taskset=taskset,
        agent_role=None,
        team_id=None,
        mode=None,
        now=None,
        suffix=None,
        json=True,
    )

    def forbidden_subprocess(*_args: object, **_kwargs: object) -> None:
        pytest.fail("status refusal must happen before any subprocess")

    monkeypatch.setattr(dispatcher.subprocess, "run", forbidden_subprocess)

    with pytest.raises(dispatcher.DispatchRefusal) as raised:
        dispatcher.cmd_start(args)

    assert raised.value.reason == "unit_not_ready"
    assert _tree_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "taskset_status",
    ["blocked/R3", "hold/R3", "held/R3", "보류/R3"],
)
def test_start_refuses_composite_taskset_blocked_token_before_subprocess_or_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    taskset_status: str,
) -> None:
    taskset = "TASKSET-DISPATCH-COMPOSITE-START-REFUSAL"
    _write_taskset(
        tmp_path,
        taskset,
        tasks=["TASK-901"],
        status=taskset_status,
    )
    _write_task(tmp_path, "TASK-901", taskset)
    _write_unit(tmp_path, "TASK-901")
    before = _tree_snapshot(tmp_path)
    args = argparse.Namespace(
        root=tmp_path,
        taskset=taskset,
        agent_role=None,
        team_id=None,
        mode=None,
        now=None,
        suffix=None,
        json=True,
    )

    def forbidden_subprocess(*_args: object, **_kwargs: object) -> None:
        pytest.fail("composite status refusal must happen before any subprocess")

    monkeypatch.setattr(dispatcher.subprocess, "run", forbidden_subprocess)

    with pytest.raises(dispatcher.DispatchRefusal) as raised:
        dispatcher.cmd_start(args)

    assert raised.value.reason == "taskset_blocked"
    assert raised.value.subject_status == taskset_status
    assert _tree_snapshot(tmp_path) == before


def test_plan_does_not_substring_match_unblocked_status(tmp_path: Path) -> None:
    taskset = "TASKSET-DISPATCH-NON-BLOCKED-TOKEN"
    _write_taskset(
        tmp_path,
        taskset,
        tasks=["TASK-901"],
        status="unblocked/R3",
    )
    _write_task(tmp_path, "TASK-901", taskset)
    _write_unit(tmp_path, "TASK-901")
    before = _tree_snapshot(tmp_path)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["unit_id"] == "UNIT-TASK-901-001"
    assert _tree_snapshot(tmp_path) == before


@pytest.mark.parametrize("unit_status", ["worker_ready", "준비", "진행 중"])
def test_plan_preserves_ready_unit_claim_command_compatibility(
    tmp_path: Path,
    unit_status: str,
) -> None:
    taskset = "TASKSET-DISPATCH-READY"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_unit(tmp_path, "TASK-901", status=unit_status)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["unit_id"] == "UNIT-TASK-901-001"
    assert payload["next_task_status"] == "planned"
    command = payload["claim_command"]
    assert command[command.index("--unit-id") + 1] == "UNIT-TASK-901-001"
    assert command[-1] == "--json"


def test_plan_resolves_canonical_dynamic_taskset_without_static_alias(tmp_path: Path) -> None:
    task_set_id = "TASKSET-AGENT-RUNTIME-DOWNSTREAM-INTAKE"
    _write_taskset(tmp_path, task_set_id, title="Downstream Intake Repair")
    _write_task(tmp_path, "TASK-229", task_set_id)

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["task_set_id"] == task_set_id
    assert payload["display_name"] == "Downstream Intake Repair"
    assert payload["next_task_id"] == "TASK-229"

    by_slug = _run(tmp_path, "plan", "agent-runtime-downstream-intake", "--json")
    assert by_slug.returncode == 0, by_slug.stderr or by_slug.stdout
    assert json.loads(by_slug.stdout)["task_set_id"] == task_set_id


@pytest.mark.parametrize(
    ("record_kwargs", "message"),
    [
        ({"schema_version": "wrong/v1"}, "schema_version"),
        ({"kind": "initiative"}, "kind"),
        ({"filename": "TASKSET-WRONG"}, "filename"),
    ],
)
def test_dynamic_taskset_parser_rejects_malformed_canonical_record(
    tmp_path: Path,
    record_kwargs: dict[str, str],
    message: str,
) -> None:
    task_set_id = "TASKSET-DYNAMIC-ONE"
    _write_taskset(tmp_path, task_set_id, **record_kwargs)
    _write_task(tmp_path, "TASK-901", task_set_id)

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 1
    assert message in (result.stderr or result.stdout)
    assert "invalid canonical task set record" in (result.stderr or result.stdout)


def test_dynamic_taskset_parser_rejects_duplicate_aliases(tmp_path: Path) -> None:
    _write_taskset(tmp_path, "TASKSET-DYNAMIC-ONE", title="Shared Lane")
    _write_taskset(tmp_path, "TASKSET-DYNAMIC-TWO", title="Shared Lane")
    _write_task(tmp_path, "TASK-901", "TASKSET-DYNAMIC-ONE")

    result = _run(tmp_path, "plan", "TASKSET-DYNAMIC-ONE", "--json")

    assert result.returncode == 1
    assert "duplicate task set alias" in (result.stderr or result.stdout)
    assert "shared-lane" in (result.stderr or result.stdout)


def test_plan_uses_canonical_tasks_order_before_backlog_score(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-ORDERED"
    _write_taskset(tmp_path, taskset, tasks=["TASK-902", "TASK-901"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_task(tmp_path, "TASK-902", taskset)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["next_task_id"] == "TASK-902"
    assert (payload["step_index"], payload["step_total"]) == (1, 2)


def test_plan_advances_to_next_canonical_task_after_first_is_complete(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-ADVANCE"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-901", taskset, status="completed")
    _write_task(tmp_path, "TASK-902", taskset)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["next_task_id"] == "TASK-902"
    assert (payload["step_index"], payload["step_total"]) == (2, 2)


def test_plan_rejects_non_list_canonical_tasks_field(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-TASKS-SCALAR"
    _write_taskset(tmp_path, taskset, tasks="TASK-901")
    _write_task(tmp_path, "TASK-901", taskset)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert "tasks must be a YAML list" in (result.stderr or result.stdout)


def test_plan_preserves_score_based_fallback_without_tasks_field(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-LEGACY"
    _write_taskset(tmp_path, taskset)
    _write_task(tmp_path, "TASK-901", taskset, priority="P3")
    _write_task(tmp_path, "TASK-902", taskset, priority="P0")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["next_task_id"] == "TASK-902"


@pytest.mark.parametrize(
    ("declared", "task_records", "message"),
    [
        (
            ["TASK-901", "TASK-901"],
            [("TASK-901", "TASKSET-DYNAMIC-MEMBERS")],
            "duplicate task ids",
        ),
        (["TASK-999"], [], "unknown task ids"),
        (
            ["TASK-901"],
            [("TASK-901", "TASKSET-OTHER")],
            "wrong task_set_id membership",
        ),
        (
            ["TASK-901"],
            [
                ("TASK-901", "TASKSET-DYNAMIC-MEMBERS"),
                ("TASK-902", "TASKSET-DYNAMIC-MEMBERS"),
            ],
            "omitted",
        ),
    ],
)
def test_plan_rejects_invalid_canonical_task_membership(
    tmp_path: Path,
    declared: list[str],
    task_records: list[tuple[str, str]],
    message: str,
) -> None:
    taskset = "TASKSET-DYNAMIC-MEMBERS"
    _write_taskset(tmp_path, taskset, tasks=declared)
    for task_id, membership in task_records:
        _write_task(tmp_path, task_id, membership)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert message in (result.stderr or result.stdout)


def test_plan_blocks_on_first_open_task_dependency_instead_of_skipping(
    tmp_path: Path,
) -> None:
    taskset = "TASKSET-DYNAMIC-DEPENDENCY"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-900", "TASKSET-OTHER", status="planned")
    _write_task(tmp_path, "TASK-901", taskset, depends_on=["TASK-900"])
    _write_task(tmp_path, "TASK-902", taskset)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert "TASK-901 has incomplete dependencies" in (result.stderr or result.stdout)
    assert "refusing to skip ahead: TASK-900" in (result.stderr or result.stdout)


@pytest.mark.parametrize("dependency", ["TASK-999", "TASK-901"], ids=["unknown", "self"])
def test_plan_rejects_invalid_selected_task_dependency(
    tmp_path: Path,
    dependency: str,
) -> None:
    taskset = "TASKSET-DYNAMIC-TASK-DEPS-INVALID"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901"])
    _write_task(tmp_path, "TASK-901", taskset, depends_on=[dependency])

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    message = result.stderr or result.stdout
    assert "depend" in message.lower()
    assert "TASK-901" in message
    assert dependency in message


def test_plan_allows_completed_selected_task_dependency(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-TASK-DEPS-COMPLETE"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-901", taskset, depends_on=["TASK-902"])
    _write_task(tmp_path, "TASK-902", taskset, status="completed")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["next_task_id"] == "TASK-901"


def test_plan_blocks_when_selected_unit_dependency_is_not_complete(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-UNIT-DEPS"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_task(tmp_path, "TASK-902", taskset)
    _write_unit(tmp_path, "TASK-901", depends_on=["UNIT-TASK-902-001"])
    _write_unit(tmp_path, "TASK-902")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    message = result.stderr or result.stdout
    assert "UNIT-TASK-901-001" in message
    assert "UNIT-TASK-902-001" in message


def test_plan_allows_completed_selected_unit_dependency(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-UNIT-DEPS-COMPLETE"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_task(tmp_path, "TASK-902", taskset)
    _write_unit(tmp_path, "TASK-901", depends_on=["UNIT-TASK-902-001"])
    _write_unit(tmp_path, "TASK-902", status="completed")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["unit_id"] == "UNIT-TASK-901-001"


@pytest.mark.parametrize(
    "dependency",
    ["UNIT-TASK-999-001", "UNIT-TASK-901-001"],
    ids=["unknown", "self"],
)
def test_plan_rejects_invalid_selected_unit_dependency(
    tmp_path: Path,
    dependency: str,
) -> None:
    taskset = "TASKSET-DYNAMIC-UNIT-DEPS-INVALID"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_unit(tmp_path, "TASK-901", depends_on=[dependency])

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    message = result.stderr or result.stdout
    assert "UNIT-TASK-901-001" in message
    assert dependency in message


def test_plan_allows_completed_task_dependency_for_selected_unit(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-UNIT-TASK-DEPS-COMPLETE"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901", "TASK-902"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_task(tmp_path, "TASK-902", taskset, status="completed")
    _write_unit(tmp_path, "TASK-901", depends_on=["TASK-902"])

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["unit_id"] == "UNIT-TASK-901-001"


def test_plan_rejects_open_task_when_all_unit_specs_are_completed(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-COMPLETED-UNIT"
    _write_taskset(tmp_path, taskset, tasks=["TASK-901"])
    _write_task(tmp_path, "TASK-901", taskset)
    _write_unit(tmp_path, "TASK-901", status="completed")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert "TASK-901 has unit specs but no open unit" in (result.stderr or result.stdout)


def test_resolve_taskset_preserves_static_alias_import_contract() -> None:
    resolved = dispatcher._resolve_taskset("quality-loop")  # noqa: SLF001

    assert resolved.task_set_id == "TASKSET-AR-QUALITY-LOOP"
    assert resolved.display_name == "Quality Sentinel"


def test_plan_uses_complete_structured_worktree_tuple(tmp_path: Path) -> None:
    task_set_id = "TASKSET-DYNAMIC-EXTERNAL"
    task_id = "TASK-902"
    repository = (tmp_path / "external-repository").resolve()
    repository.mkdir()
    worktree = repository / ".worktrees" / task_id
    _write_taskset(tmp_path, task_set_id)
    _write_task(tmp_path, task_id, task_set_id)
    _write_unit(
        tmp_path,
        task_id,
        repository_path=str(repository),
        worktree_path=str(worktree),
        branch="fix/task-902",
        base_ref="origin/main",
    )

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["repository_path"] == str(repository)
    assert payload["worktree_path"] == str(worktree)
    assert payload["branch"] == "fix/task-902"
    assert payload["base_ref"] == "origin/main"
    assert payload["worktree_command"] == [
        "git",
        "worktree",
        "add",
        "-b",
        "fix/task-902",
        str(worktree),
        "origin/main",
    ]
    claim_command = payload["claim_command"]
    assert claim_command[claim_command.index("--mode") + 1] == "orchestrator"
    assert claim_command[claim_command.index("--worktree-path") + 1] == str(worktree)


def _git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _init_repository(repository: Path) -> None:
    repository.mkdir()
    _git(repository, "init", "-q", "-b", "main")
    _git(repository, "config", "user.email", "taskset-test@example.com")
    _git(repository, "config", "user.name", "Taskset Test")
    (repository / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(repository, "add", "README.md")
    _git(repository, "commit", "-q", "-m", "fixture")


def test_adoption_reuses_existing_local_branch_without_dash_b(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    _git(repository, "branch", "fix/existing")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/fix/existing",
        "refs/heads/fix/existing",
    )
    worktree = repository / ".worktrees" / "TASK-905"
    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "fix/existing",
            "base_ref": "origin/fix/existing",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )

    assert payload["adopt_existing_branch"] is True
    assert payload["worktree_command"] == [
        "git", "worktree", "add", str(worktree), "fix/existing"
    ]
    assert dispatcher._ensure_worktree(tmp_path, payload) is True  # noqa: SLF001
    assert _git(worktree, "branch", "--show-current").stdout.strip() == "fix/existing"


def test_adoption_normalizes_full_local_ref_before_worktree_add(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    _git(repository, "branch", "fix/existing")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/fix/existing",
        "refs/heads/fix/existing",
    )
    worktree = repository / ".worktrees" / "TASK-905-FULL-REF"
    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "refs/heads/fix/existing",
            "base_ref": "origin/fix/existing",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )

    assert dispatcher._ensure_worktree(tmp_path, payload) is True  # noqa: SLF001
    assert payload["worktree_command"] == [
        "git", "worktree", "add", str(worktree), "fix/existing"
    ]
    assert _git(worktree, "branch", "--show-current").stdout.strip() == "fix/existing"


def test_adoption_normalizes_full_ref_before_fresh_branch_creation(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    worktree = repository / ".worktrees" / "TASK-905-FRESH-FULL-REF"
    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "refs/heads/fix/fresh",
            "base_ref": "main",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )

    assert dispatcher._ensure_worktree(tmp_path, payload) is True  # noqa: SLF001
    assert payload["worktree_command"] == [
        "git", "worktree", "add", "-b", "fix/fresh", str(worktree), "main"
    ]
    assert _git(worktree, "branch", "--show-current").stdout.strip() == "fix/fresh"


@pytest.mark.parametrize(
    "branch",
    [
        "refs/heads/HEAD",
        "refs/heads/-danger",
        "refs/heads/.hidden",
        "refs/heads/foo/.hidden",
    ],
)
def test_adoption_rejects_invalid_normalized_local_branch_before_worktree_add(
    tmp_path: Path,
    branch: str,
) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    if branch == "refs/heads/HEAD":
        _git(repository, "update-ref", branch, "refs/heads/main")
    worktree = repository / ".worktrees" / "TASK-905-INVALID-FULL-REF"

    with pytest.raises(SystemExit, match="invalid local branch name"):
        dispatcher._worktree_tuple(  # noqa: SLF001
            tmp_path,
            {
                "repository_path": str(repository),
                "worktree_path": str(worktree),
                "branch": branch,
                "base_ref": "main",
                "adopt_existing_branch": True,
            },
            default_worktree="unused",
            default_branch="unused",
        )

    assert not worktree.exists()
    assert str(worktree) not in _git(repository, "worktree", "list", "--porcelain").stdout


def test_adoption_rejects_local_branch_behind_declared_base_ref(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    _git(repository, "branch", "fix/existing")
    (repository / "NEXT.md").write_text("remote advance\n", encoding="utf-8")
    _git(repository, "add", "NEXT.md")
    _git(repository, "commit", "-q", "-m", "advance remote base")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/fix/existing",
        "refs/heads/main",
    )

    with pytest.raises(SystemExit, match="behind or diverged"):
        dispatcher._worktree_tuple(  # noqa: SLF001
            tmp_path,
            {
                "repository_path": str(repository),
                "worktree_path": str(repository / ".worktrees" / "TASK-905"),
                "branch": "fix/existing",
                "base_ref": "origin/fix/existing",
                "adopt_existing_branch": True,
            },
            default_worktree="unused",
            default_branch="unused",
        )


def test_adoption_accepts_local_branch_ahead_of_declared_base_ref(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    base_sha = _git(repository, "rev-parse", "HEAD").stdout.strip()
    _git(repository, "branch", "fix/existing")
    _git(repository, "update-ref", "refs/remotes/origin/fix/existing", base_sha)
    _git(repository, "switch", "-q", "fix/existing")
    (repository / "AHEAD.md").write_text("local advance\n", encoding="utf-8")
    _git(repository, "add", "AHEAD.md")
    _git(repository, "commit", "-q", "-m", "advance local branch")
    _git(repository, "switch", "-q", "main")
    worktree = repository / ".worktrees" / "TASK-905"

    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "fix/existing",
            "base_ref": "origin/fix/existing",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )

    assert payload["worktree_command"] == [
        "git", "worktree", "add", str(worktree), "fix/existing"
    ]
    assert dispatcher._ensure_worktree(tmp_path, payload) is True  # noqa: SLF001


def test_adoption_rejects_missing_base_before_fresh_branch_creation(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)

    with pytest.raises(SystemExit, match="base_ref is missing or not a commit"):
        dispatcher._worktree_tuple(  # noqa: SLF001
            tmp_path,
            {
                "repository_path": str(repository),
                "worktree_path": str(repository / ".worktrees" / "TASK-905"),
                "branch": "fix/missing",
                "base_ref": "origin/fix/missing",
                "adopt_existing_branch": True,
            },
            default_worktree="unused",
            default_branch="unused",
        )


def test_adoption_rechecks_preexisting_worktree_after_base_moves(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    base_sha = _git(repository, "rev-parse", "HEAD").stdout.strip()
    _git(repository, "branch", "fix/existing")
    _git(repository, "update-ref", "refs/remotes/origin/fix/existing", base_sha)
    worktree = repository / ".worktrees" / "TASK-905"
    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "fix/existing",
            "base_ref": "origin/fix/existing",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )
    assert dispatcher._ensure_worktree(tmp_path, payload) is True  # noqa: SLF001

    (repository / "NEXT.md").write_text("remote advance\n", encoding="utf-8")
    _git(repository, "add", "NEXT.md")
    _git(repository, "commit", "-q", "-m", "advance remote base")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/fix/existing",
        "refs/heads/main",
    )

    assert dispatcher._ensure_worktree(tmp_path, payload) is False  # noqa: SLF001
    assert "behind or diverged" in capsys.readouterr().err


def test_adoption_rejects_preexisting_worktree_on_wrong_branch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = tmp_path / "repository"
    _init_repository(repository)
    _git(repository, "branch", "fix/expected")
    _git(
        repository,
        "update-ref",
        "refs/remotes/origin/fix/expected",
        "refs/heads/fix/expected",
    )
    worktree = repository / ".worktrees" / "TASK-906"
    _git(repository, "worktree", "add", "-q", "-b", "fix/actual", str(worktree), "main")
    payload = dispatcher._worktree_tuple(  # noqa: SLF001
        tmp_path,
        {
            "repository_path": str(repository),
            "worktree_path": str(worktree),
            "branch": "fix/expected",
            "base_ref": "origin/fix/expected",
            "adopt_existing_branch": True,
        },
        default_worktree="unused",
        default_branch="unused",
    )

    assert dispatcher._ensure_worktree(tmp_path, payload) is False  # noqa: SLF001
    assert "worktree branch mismatch" in capsys.readouterr().err


def test_adoption_requires_complete_structured_tuple() -> None:
    with pytest.raises(SystemExit, match="requires a complete structured worktree tuple"):
        dispatcher._worktree_tuple(  # noqa: SLF001
            Path.cwd(),
            {"adopt_existing_branch": True},
            default_worktree=".worktrees/TASK-907",
            default_branch="fix/task-907",
        )


def test_plan_treats_explicit_false_adoption_as_legacy_default(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-ADOPT-FALSE"
    task_id = "TASK-907"
    _write_taskset(tmp_path, taskset, tasks=[task_id])
    _write_task(tmp_path, task_id, taskset)
    _write_unit(tmp_path, task_id, adopt_existing_branch=False)

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["adopt_existing_branch"] is False
    assert payload["worktree_path"] == f".worktrees/{task_id}"


def test_plan_rejects_non_boolean_adoption_flag(tmp_path: Path) -> None:
    taskset = "TASKSET-DYNAMIC-ADOPT-INVALID"
    task_id = "TASK-908"
    _write_taskset(tmp_path, taskset, tasks=[task_id])
    _write_task(tmp_path, task_id, taskset)
    _write_unit(tmp_path, task_id, adopt_existing_branch="invalid")

    result = _run(tmp_path, "plan", taskset, "--json")

    assert result.returncode == 1
    assert "adopt_existing_branch must be a boolean" in (result.stderr or result.stdout)


@pytest.mark.parametrize("missing", ["repository_path", "worktree_path", "branch", "base_ref"])
def test_plan_rejects_partial_structured_worktree_tuple(tmp_path: Path, missing: str) -> None:
    task_set_id = "TASKSET-DYNAMIC-PARTIAL"
    task_id = "TASK-903"
    repository = (tmp_path / "external-repository").resolve()
    worktree = repository / ".worktrees" / task_id
    metadata = {
        "repository_path": str(repository),
        "worktree_path": str(worktree),
        "branch": "fix/task-903",
        "base_ref": "origin/main",
    }
    metadata.pop(missing)
    _write_taskset(tmp_path, task_set_id)
    _write_task(tmp_path, task_id, task_set_id)
    _write_unit(tmp_path, task_id, **metadata)

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 1
    assert "structured worktree metadata must define all fields" in (result.stderr or result.stdout)
    assert missing in (result.stderr or result.stdout)


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        (
            {
                "repository_path": "relative/repository",
                "worktree_path": "/tmp/repository/.worktrees/TASK-904",
                "branch": "fix/task-904",
                "base_ref": "origin/main",
            },
            "repository_path must be absolute",
        ),
        (
            {
                "repository_path": "/tmp/repository",
                "worktree_path": "/tmp/outside/TASK-904",
                "branch": "fix/task-904",
                "base_ref": "origin/main",
            },
            "worktree_path must be under",
        ),
        (
            {
                "repository_path": "/tmp/repository",
                "worktree_path": "/tmp/repository/.worktrees/TASK-904",
                "branch": "main",
                "base_ref": "origin/main",
            },
            "protected branch",
        ),
        (
            {
                "repository_path": "/tmp/repository",
                "worktree_path": "/tmp/repository/.worktrees/TASK-904",
                "branch": "fix/task-904",
                "base_ref": "--upload-pack=unsafe",
            },
            "unsafe base_ref",
        ),
    ],
)
def test_plan_rejects_unsafe_structured_worktree_tuple(
    tmp_path: Path,
    metadata: dict[str, str],
    message: str,
) -> None:
    repository = str((tmp_path / "repository").resolve())
    outside = str((tmp_path / "outside").resolve())
    metadata = {
        key: value.replace("/tmp/repository", repository).replace("/tmp/outside", outside)
        for key, value in metadata.items()
    }
    task_set_id = "TASKSET-DYNAMIC-UNSAFE"
    task_id = "TASK-904"
    _write_taskset(tmp_path, task_set_id)
    _write_task(tmp_path, task_id, task_set_id)
    _write_unit(tmp_path, task_id, **metadata)

    result = _run(tmp_path, "plan", task_set_id, "--json")

    assert result.returncode == 1
    assert message in (result.stderr or result.stdout)


def test_plan_preserves_legacy_static_alias_and_host_worktree_defaults(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP")

    result = _run(tmp_path, "plan", "quality-loop", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["task_set_id"] == "TASKSET-AR-QUALITY-LOOP"
    assert payload["worktree_path"] == ".worktrees/TASK-AR-901"
    assert payload["branch"] == "codex/task-ar-901-quality-loop"


def _start_args(root: Path) -> argparse.Namespace:
    return argparse.Namespace(root=root, taskset="unused", json=True)


def _start_payload(root: Path) -> dict[str, object]:
    worktree = root / ".worktrees" / "TASK-905"
    return {
        "task_set_id": "TASKSET-DYNAMIC-START",
        "next_task_id": "TASK-905",
        "next_task_path": str(root / "agents" / "lead_engineer" / "tasks" / "TASK-905.md"),
        "next_task_status": "planned",
        "unit_spec_path": "",
        "model_tier": "planner",
        "repository_path": str(root),
        "worktree_path": str(worktree),
        "branch": "fix/task-905",
        "base_ref": "origin/main",
        "worktree_command": [
            "git",
            "worktree",
            "add",
            "-b",
            "fix/task-905",
            str(worktree),
            "origin/main",
        ],
        "claim_command": ["claim"],
    }


def _claim_result(
    root: Path,
    *,
    persist: bool,
    persisted_overrides: dict[str, str] | None = None,
    declared_overrides: dict[str, str] | None = None,
    path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    claim_id = "CLAIM-test-task-905"
    claim_path = path or root / "agents" / "runtime" / "task_claims" / f"{claim_id}.json"
    claim = {
        "claim_id": claim_id,
        "task_id": "TASK-905",
        "task_set_id": "TASKSET-DYNAMIC-START",
        "status": "claimed",
        "mode": "orchestrator",
        "worktree_path": str(root / ".worktrees" / "TASK-905"),
        "branch": "fix/task-905",
    }
    claim.update(persisted_overrides or {})
    if persist:
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        claim_path.write_text(json.dumps(claim), encoding="utf-8")
    declared = {**claim, **(declared_overrides or {})}
    stdout = json.dumps(
        {
            "status": "created",
            "path": claim_path.relative_to(root).as_posix(),
            "claim": declared,
        }
    )
    return subprocess.CompletedProcess(["claim"], 0, stdout=stdout, stderr="")


def _prepare_start(monkeypatch: pytest.MonkeyPatch, root: Path) -> dict[str, object]:
    payload = _start_payload(root)
    monkeypatch.setattr(dispatcher, "_plan_payload", lambda _args: payload)
    monkeypatch.setattr(dispatcher, "_active_taskset_claims", lambda _root, _taskset: [])
    monkeypatch.setattr(dispatcher, "_sync_backlog_board", lambda _root: True)
    monkeypatch.delenv("AGENT_RUNTIME_GIT", raising=False)
    return payload


def test_start_claim_failure_does_not_run_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return subprocess.CompletedProcess(command, 17, stdout="", stderr="claim refused\n")
        raise AssertionError("worktree command must not run after claim failure")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 17
    assert calls == ["claim"]


def test_start_missing_persisted_claim_does_not_run_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=False)
        raise AssertionError("worktree command must not run without a persisted claim")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert calls == ["claim"]
    assert "persisted claim is missing" in capsys.readouterr().err


def test_start_creates_worktree_once_after_persisted_orchestrator_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=True)
        worktree = Path(str(payload["worktree_path"]))
        worktree.mkdir(parents=True)
        (worktree / ".git").write_text("gitdir: fake\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 0
    assert calls == ["claim", "git"]


def test_start_worktree_failure_leaves_persisted_claim_for_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=True)
        return subprocess.CompletedProcess(command, 23, stdout="", stderr="worktree failed\n")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    claim_path = tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-test-task-905.json"
    assert claim_path.is_file()
    assert calls == ["claim", "git"]
    stderr = capsys.readouterr().err
    assert "reservation claim remains active" in stderr
    assert "CLAIM-test-task-905" in stderr


def test_start_worktree_spawn_error_leaves_persisted_claim_for_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_start(monkeypatch, tmp_path)

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=True)
        raise FileNotFoundError("external repository is unavailable")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    claim_path = tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-test-task-905.json"
    assert claim_path.is_file()
    stderr = capsys.readouterr().err
    assert "failed to run worktree command" in stderr
    assert "reservation claim remains active" in stderr


@pytest.mark.parametrize(
    ("stdout", "message"),
    [
        ("{not-json", "invalid JSON"),
        ("[]", "non-object JSON"),
    ],
)
def test_start_rejects_invalid_claim_json_without_running_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stdout: str,
    message: str,
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
        raise AssertionError("worktree command must not run for invalid claim JSON")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert calls == ["claim"]
    assert message in capsys.readouterr().err


def test_start_rejects_claim_path_outside_canonical_claim_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    outside = tmp_path / "outside-claim.json"

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=True, path=outside)
        raise AssertionError("worktree command must not run for an unsafe claim path")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert "persisted claim path is outside" in capsys.readouterr().err


def test_start_rejects_persisted_claim_field_mismatch_without_running_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_start(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return _claim_result(
                tmp_path,
                persist=True,
                persisted_overrides={"branch": "fix/other"},
                declared_overrides={"branch": "fix/task-905"},
            )
        raise AssertionError("worktree command must not run for a mismatched claim")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert calls == ["claim"]
    assert "persisted claim field mismatch: branch" in capsys.readouterr().err


def test_start_accepts_preexisting_worktree_after_persisting_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _prepare_start(monkeypatch, tmp_path)
    worktree = Path(str(payload["worktree_path"]))
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: existing\n", encoding="utf-8")
    calls: list[str] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command[0])
        if command[0] == "claim":
            return _claim_result(tmp_path, persist=True)
        raise AssertionError("git must not run for a pre-existing valid worktree")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 0
    assert calls == ["claim"]


def test_plan_keeps_machine_readable_claim_response_for_non_json_outer_cli(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP")
    args = argparse.Namespace(
        root=tmp_path,
        taskset="quality-loop",
        agent_role=None,
        team_id=None,
        mode="implement",
        now=None,
        suffix=None,
        json=False,
    )

    payload = dispatcher._plan_payload(args)  # noqa: SLF001

    assert payload["claim_command"][-1] == "--json"
    mode_index = payload["claim_command"].index("--mode")
    assert payload["claim_command"][mode_index + 1] == "orchestrator"


def test_non_json_start_integrates_with_claim_dispatcher_and_existing_worktree(
    tmp_path: Path,
) -> None:
    (tmp_path / "STATUS.md").write_text(
        "## Handoff Checklist\n- continue here\n",
        encoding="utf-8",
    )
    _write_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP")
    _write_t0(tmp_path, "TASKSET-AR-QUALITY-LOOP", "STATUS.md")
    worktree = tmp_path / ".worktrees" / "TASK-AR-901"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: existing\n", encoding="utf-8")

    result = _run(
        tmp_path,
        "start",
        "quality-loop",
        "--now",
        "2026-07-14T18:50:00+09:00",
        "--suffix",
        "integration",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "taskset-dispatcher: Quality Sentinel" in result.stdout
    claim_paths = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_paths) == 1
    claim = json.loads(claim_paths[0].read_text(encoding="utf-8"))
    assert claim["mode"] == "orchestrator"
    assert claim["task_id"] == "TASK-AR-901"
    assert claim["worktree_path"] == ".worktrees/TASK-AR-901"
    assert (tmp_path / "BACKLOG-BOARD.md").is_file()


def test_ensure_worktree_runs_git_in_declared_external_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "external-repository"
    repository.mkdir()
    worktree = repository / ".worktrees" / "TASK-906"
    payload = {
        "repository_path": str(repository),
        "worktree_path": str(worktree),
        "worktree_command": [
            "git",
            "worktree",
            "add",
            "-b",
            "fix/task-906",
            str(worktree),
            "origin/main",
        ],
    }
    observed_cwd: list[Path] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed_cwd.append(Path(str(kwargs["cwd"])))
        worktree.mkdir(parents=True)
        (worktree / ".git").write_text("gitdir: external\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(dispatcher.subprocess, "run", fake_run)
    monkeypatch.delenv("AGENT_RUNTIME_GIT", raising=False)

    assert dispatcher._ensure_worktree(tmp_path, payload)  # noqa: SLF001
    assert observed_cwd == [repository.resolve()]


def test_start_readiness_failure_blocks_claim_and_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _prepare_start(monkeypatch, tmp_path)
    payload["unit_spec_path"] = "agents/lead_engineer/tasks/units/TASK-905/UNIT-001.md"
    payload["unit_id"] = "UNIT-001"
    payload["model_tier"] = "worker_standard"
    calls: list[list[str]] = []

    def forbidden_subprocess(command: list[str], **_kwargs: object) -> None:
        calls.append(command)
        pytest.fail("readiness refusal must happen before the claim subprocess")

    monkeypatch.setattr(dispatcher.subprocess, "run", forbidden_subprocess)
    monkeypatch.setattr(
        dispatcher.task_claim_dispatcher,
        "_claim_readiness_findings",
        lambda *_args, **_kwargs: ["fixture:not-ready"],
    )

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert calls == []


@pytest.mark.parametrize("unit_status", ["준비", "진행 중"])
def test_start_preserves_localized_ready_status_compatibility(
    tmp_path: Path,
    unit_status: str,
) -> None:
    taskset = "TASKSET-DISPATCH-LOCALIZED-READY"
    task = "TASK-901"
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    _write_taskset(tmp_path, taskset, tasks=[task])
    _write_task(tmp_path, task, taskset)
    _write_dispatch_ready_unit(tmp_path, task, taskset, status=unit_status)
    _write_t0(tmp_path, taskset, "README.md")
    worktree = tmp_path / ".worktrees" / task
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: existing\n", encoding="utf-8")

    result = _run(
        tmp_path,
        "start",
        taskset,
        "--now",
        "2026-07-27T16:00:00+09:00",
        "--suffix",
        "localized",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["unit_id"] == f"UNIT-{task}-001"
    claim = payload["claim"]["claim"]
    assert claim["task_set_id"] == taskset
    assert claim["unit_id"] == f"UNIT-{task}-001"


def test_start_active_taskset_claim_blocks_before_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _prepare_start(monkeypatch, tmp_path)
    monkeypatch.setattr(
        dispatcher,
        "_active_taskset_claims",
        lambda _root, _taskset: [{"claim_id": "CLAIM-existing", "_path": "claim.json"}],
    )
    monkeypatch.setattr(
        dispatcher.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("no subprocess may run while the taskset is already claimed")
        ),
    )

    assert dispatcher.cmd_start(_start_args(tmp_path)) == 1
    assert payload["task_set_id"] in capsys.readouterr().err
