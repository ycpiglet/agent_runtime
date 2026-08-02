from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
TASK_ID = "TASK-901"
TASKSET_ID = "TASKSET-CLAIM-PREFLIGHT"
UNIT_ID = "UNIT-TASK-901-001"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_task(root: Path, *, status: str = "planned") -> Path:
    path = root / "agents/lead_engineer/tasks" / f"{TASK_ID}-fixture.md"
    _write(
        path,
        f"""---
id: {TASK_ID}
status: {status}
priority: P1
difficulty: M
est_hours: 1
est_tokens: 100
task_set_id: {TASKSET_ID}
project_id: PROJECT-TEST
tags: [test]
---

# Fixture
""",
    )
    return path


def _write_taskset(root: Path, *, status: str = "active") -> Path:
    path = root / "agents/project/initiatives" / f"{TASKSET_ID}.md"
    _write(
        path,
        f"""---
schema_version: agent-runtime-work-item/v1
work_id: {TASKSET_ID}
kind: taskset
status: {status}
title: Claim Preflight
summary: Test claim preflight.
tasks: [{TASK_ID}]
---
""",
    )
    return path


def _write_unit(
    root: Path,
    *,
    status: str = "worker_ready",
    task_set_id: str = TASKSET_ID,
) -> Path:
    path = (
        root
        / "agents/lead_engineer/tasks/units"
        / TASK_ID
        / f"{UNIT_ID}.md"
    )
    _write(
        path,
        f"""---
unit_id: {UNIT_ID}
task_id: {TASK_ID}
task_set_id: {task_set_id}
project_id: PROJECT-TEST
status: {status}
model_tier: worker_standard
context: Test claim readiness.
inputs: [README.md]
target_files: [README.md]
scope: Test only.
acceptance: [Preflight passes.]
verification: [pytest]
handoff: Report result.
stop_condition: stop_after:{UNIT_ID}:test
---

## Context

Fixture context.

## Inputs

Fixture input.

## Target Files

Fixture target.

## Scope

Fixture scope.

## Steps

1. Verify.

## Acceptance Criteria

Fixture acceptance.

## Verification

Run pytest.

## Handoff

Report result.

## Stop Boundary

Test only.
""",
    )
    return path


def _write_t0(root: Path, *, anchor: str = "README.md") -> None:
    target = root / anchor
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    payload = {
        "schema": "agent-runtime-plan-assumptions/v1",
        "updated_at": "2026-07-27T00:00:00+09:00",
        "assumption_sets": [
            {
                "taskset_id": TASKSET_ID,
                "design_record": "README.md",
                "recorded_at": "2026-07-27T00:00:00+09:00",
                "revalidation_policy": "block_dispatch_on_drift",
                "anchors": [{"path": anchor, "kind": "sha256", "value": digest}],
            }
        ],
    }
    _write(
        root / "agents/project/work-items/PLAN-ASSUMPTIONS.json",
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


def _fixture(
    root: Path,
    *,
    task_status: str = "planned",
    taskset_status: str = "active",
    unit_status: str = "worker_ready",
    unit_taskset_id: str = TASKSET_ID,
    with_t0: bool = True,
) -> Path:
    _write(root / "README.md", "fixture\n")
    _write_task(root, status=task_status)
    _write_taskset(root, status=taskset_status)
    unit_path = _write_unit(root, status=unit_status, task_set_id=unit_taskset_id)
    if with_t0:
        _write_t0(root)
    return unit_path


def _snapshot(root: Path) -> tuple[tuple[str, ...], dict[str, bytes]]:
    directories = tuple(
        sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())
    )
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    return directories, files


def _run_create(
    root: Path,
    unit_path: Path,
    *,
    include_taskset_arg: bool = True,
    include_unit_args: bool = True,
    skip_plan_check: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["AGENT_RUNTIME_CLAIM_AUTOCOMMIT"] = "0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [
        sys.executable,
        str(SCRIPTS_DIR / "task_claim_dispatcher.py"),
        "--root",
        str(root),
        "create",
        "--task-id",
        TASK_ID,
    ]
    if include_taskset_arg:
        command.extend(["--task-set-id", TASKSET_ID])
    if include_unit_args:
        command.extend(
            [
                "--unit-id",
                UNIT_ID,
                "--unit-spec",
                unit_path.relative_to(root).as_posix(),
            ]
        )
    command.extend(
        [
        "--model-tier",
        "worker_standard",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "orchestrator",
        "--status-text",
        "Claim preflight fixture",
        "--worktree-path",
        ".worktrees/TASK-901",
        "--branch",
        "codex/task-901-fixture",
        "--now",
        "2026-07-27T12:00:00+09:00",
        "--suffix",
        "fixture",
        ]
    )
    if skip_plan_check:
        command.append("--skip-plan-check")
    command.append("--json")
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _assert_refusal_without_mutation(
    root: Path,
    unit_path: Path,
    *,
    message: str,
) -> None:
    before = _snapshot(root)
    result = _run_create(root, unit_path)
    assert result.returncode == 1
    assert result.stdout == ""
    assert message in result.stderr
    assert _snapshot(root) == before


def test_create_refuses_missing_t0_without_any_mutation(tmp_path: Path) -> None:
    unit_path = _fixture(tmp_path, with_t0=False)

    _assert_refusal_without_mutation(
        tmp_path,
        unit_path,
        message=f"claim-preflight:t0:registry:missing-taskset:{TASKSET_ID}",
    )


def test_create_does_not_bypass_missing_t0_with_skip_without_any_mutation(
    tmp_path: Path,
) -> None:
    unit_path = _fixture(tmp_path, with_t0=False)
    before = _snapshot(tmp_path)

    result = _run_create(tmp_path, unit_path, skip_plan_check=True)

    assert result.returncode == 1
    assert result.stdout == ""
    assert f"claim-preflight:t0:registry:missing-taskset:{TASKSET_ID}" in result.stderr
    assert _snapshot(tmp_path) == before


def test_create_derives_taskset_and_refuses_missing_t0_without_optional_args(
    tmp_path: Path,
) -> None:
    unit_path = _fixture(tmp_path, with_t0=False)
    before = _snapshot(tmp_path)

    result = _run_create(
        tmp_path,
        unit_path,
        include_taskset_arg=False,
        include_unit_args=False,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert f"claim-preflight:t0:registry:missing-taskset:{TASKSET_ID}" in result.stderr
    assert _snapshot(tmp_path) == before


def test_create_refuses_planned_registered_unit_without_optional_args(
    tmp_path: Path,
) -> None:
    unit_path = _fixture(tmp_path, unit_status="planned")
    before = _snapshot(tmp_path)

    result = _run_create(
        tmp_path,
        unit_path,
        include_taskset_arg=False,
        include_unit_args=False,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "unit:not-worker-ready:planned" in result.stderr
    assert _snapshot(tmp_path) == before


def test_create_does_not_bypass_unreadable_t0_with_skip_without_any_mutation(
    tmp_path: Path,
) -> None:
    unit_path = _fixture(tmp_path)
    _write(
        tmp_path / "agents/project/work-items/PLAN-ASSUMPTIONS.json",
        "{not-json\n",
    )
    before = _snapshot(tmp_path)

    result = _run_create(tmp_path, unit_path, skip_plan_check=True)

    assert result.returncode == 1
    assert result.stdout == ""
    assert "claim-preflight:t0:registry-unreadable:" in result.stderr
    assert _snapshot(tmp_path) == before


def test_create_does_not_bypass_invalid_anchor_kind_with_skip(
    tmp_path: Path,
) -> None:
    unit_path = _fixture(tmp_path)
    registry_path = tmp_path / "agents/project/work-items/PLAN-ASSUMPTIONS.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["assumption_sets"][0]["anchors"][0]["kind"] = "unknown"
    _write(registry_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    before = _snapshot(tmp_path)

    result = _run_create(tmp_path, unit_path, skip_plan_check=True)

    assert result.returncode == 1
    assert result.stdout == ""
    assert f"claim-preflight:t0:registry:invalid-anchor:{TASKSET_ID}:0" in result.stderr
    assert _snapshot(tmp_path) == before


def test_create_typed_refusal_for_non_string_anchor_path_without_mutation(
    tmp_path: Path,
) -> None:
    unit_path = _fixture(tmp_path)
    registry_path = tmp_path / "agents/project/work-items/PLAN-ASSUMPTIONS.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["assumption_sets"][0]["anchors"][0]["path"] = []
    _write(registry_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    before = _snapshot(tmp_path)

    result = _run_create(tmp_path, unit_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert f"claim-preflight:t0:registry:invalid-anchor:{TASKSET_ID}:0" in result.stderr
    assert _snapshot(tmp_path) == before


def test_create_does_not_bypass_non_object_t0_registry_with_skip(
    tmp_path: Path,
) -> None:
    unit_path = _fixture(tmp_path)
    registry_path = tmp_path / "agents/project/work-items/PLAN-ASSUMPTIONS.json"
    _write(registry_path, "[]\n")
    before = _snapshot(tmp_path)

    result = _run_create(tmp_path, unit_path, skip_plan_check=True)

    assert result.returncode == 1
    assert result.stdout == ""
    assert "claim-preflight:t0:registry:invalid-root" in result.stderr
    assert _snapshot(tmp_path) == before


def test_create_refuses_drifted_t0_without_any_mutation(tmp_path: Path) -> None:
    unit_path = _fixture(tmp_path)
    _write(tmp_path / "README.md", "drifted\n")

    _assert_refusal_without_mutation(
        tmp_path,
        unit_path,
        message=f"claim-preflight:t0:{TASKSET_ID}: anchor-hash-changed:README.md",
    )


def test_create_emits_skip_plan_warning_once_on_authoritative_pass(
    tmp_path: Path,
) -> None:
    unit_path = _fixture(tmp_path)
    _write(tmp_path / "README.md", "drifted\n")

    result = _run_create(tmp_path, unit_path, skip_plan_check=True)

    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stderr.count("WARNING: --skip-plan-check used") == 1


@pytest.mark.parametrize("status", ["planned", "blocked"])
def test_create_refuses_non_ready_unit_without_any_mutation(
    tmp_path: Path,
    status: str,
) -> None:
    unit_path = _fixture(tmp_path, unit_status=status)

    _assert_refusal_without_mutation(
        tmp_path,
        unit_path,
        message=f"unit:not-worker-ready:{status}",
    )


@pytest.mark.parametrize(
    ("task_status", "taskset_status", "message"),
    [
        ("보류", "active", "claim-preflight:readiness:task:blocked-status:보류"),
        ("held", "active", "claim-preflight:readiness:task:blocked-status:held"),
        (
            "blocked/R3",
            "active",
            "claim-preflight:readiness:task:blocked-status:blocked/R3",
        ),
        ("planned", "blocked", "claim-preflight:readiness:taskset:blocked-status:blocked"),
        ("planned", "held", "claim-preflight:readiness:taskset:blocked-status:held"),
        (
            "planned",
            "blocked/R3",
            "claim-preflight:readiness:taskset:blocked-status:blocked/R3",
        ),
    ],
)
def test_create_refuses_blocked_parent_without_any_mutation(
    tmp_path: Path,
    task_status: str,
    taskset_status: str,
    message: str,
) -> None:
    unit_path = _fixture(
        tmp_path,
        task_status=task_status,
        taskset_status=taskset_status,
    )

    _assert_refusal_without_mutation(tmp_path, unit_path, message=message)


@pytest.mark.parametrize(
    ("task_status", "taskset_status"),
    [("unblocked/R3", "active"), ("planned", "unblocked/R3")],
)
def test_create_does_not_substring_match_unblocked_parent(
    tmp_path: Path,
    task_status: str,
    taskset_status: str,
) -> None:
    unit_path = _fixture(
        tmp_path,
        task_status=task_status,
        taskset_status=taskset_status,
    )

    result = _run_create(tmp_path, unit_path)

    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["status"] == "created"


@pytest.mark.parametrize(
    ("task_status", "taskset_status"),
    [("unblocked/R3", "active"), ("planned", "unblocked/R3")],
)
def test_create_reports_only_unit_readiness_for_unblocked_parent(
    tmp_path: Path,
    task_status: str,
    taskset_status: str,
) -> None:
    unit_path = _fixture(
        tmp_path,
        task_status=task_status,
        taskset_status=taskset_status,
        unit_status="planned",
    )
    before = _snapshot(tmp_path)

    result = _run_create(tmp_path, unit_path)

    assert result.returncode == 1
    assert "unit:not-worker-ready:planned" in result.stderr
    assert "blocked-status:unblocked/R3" not in result.stderr
    assert _snapshot(tmp_path) == before


def test_create_refuses_unit_taskset_binding_mismatch_without_any_mutation(
    tmp_path: Path,
) -> None:
    unit_path = _fixture(tmp_path, unit_taskset_id="TASKSET-OTHER")

    _assert_refusal_without_mutation(
        tmp_path,
        unit_path,
        message=f"claim-preflight:readiness:unit-taskset-mismatch:TASKSET-OTHER:{TASKSET_ID}",
    )


@pytest.mark.parametrize("unit_status", ["worker_ready", "준비", "진행 중"])
def test_create_preserves_valid_ready_path(
    tmp_path: Path,
    unit_status: str,
) -> None:
    unit_path = _fixture(tmp_path, unit_status=unit_status)
    task_before = (tmp_path / "agents/lead_engineer/tasks/TASK-901-fixture.md").read_bytes()
    unit_before = unit_path.read_bytes()

    result = _run_create(tmp_path, unit_path)

    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stderr.count(f"plan-assumption-gate: pass ({TASKSET_ID})") == 1
    envelope = json.loads(result.stdout)
    assert envelope["status"] == "created"
    claim = envelope["claim"]
    assert claim["task_id"] == TASK_ID
    assert claim["task_set_id"] == TASKSET_ID
    assert claim["unit_id"] == UNIT_ID
    assert (tmp_path / envelope["path"]).is_file()
    assert (tmp_path / claim["handoff_path"]).is_file()
    assert (tmp_path / claim["log_path"]).is_file()
    instance = tmp_path / "agents/runtime/instances" / f"{claim['agent_instance_id']}.json"
    assert instance.is_file()
    events_path = tmp_path / "agents/runtime/pane_events/pane-events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    assert [event["event"] for event in events] == ["instance_spawned", "claim_created"]
    assert (tmp_path / "agents/lead_engineer/tasks/TASK-901-fixture.md").read_bytes() == task_before
    assert unit_path.read_bytes() == unit_before
    assert not (tmp_path / ".worktrees/TASK-901").exists()
