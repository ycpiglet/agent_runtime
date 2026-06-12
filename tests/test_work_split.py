from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "work.py"


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_task(root: Path) -> Path:
    task_id = "TASK-AR-901"
    path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
schema_version: agent-runtime-work-item/v1
id: {task_id}
display_id: {task_id}
task_uid: 22222222-2222-4222-8222-000000000001
work_id: {task_id}
work_uid: 22222222-2222-4222-8222-000000000001
kind: task
parent_id: TASKSET-TEST
registered_at: 2026-06-12T12:00:00+09:00
created_at: 2026-06-12T12:00:00+09:00
updated_at: 2026-06-12T12:00:00+09:00
title: Split parent task
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 200
owner: lead_engineer
initiative_id: INIT-TEST
project_id: PROJECT-TEST
task_set_id: TASKSET-TEST
origin_type: owner_request
origin_ref: reviews/REVIEW-TEST.md
created_by: planner-test
summary: Parent task for split tests.
tags:
  - work-cli
target_files:
  - scripts/work.py
acceptance:
  - "The command proposes worker-ready unit specs."
  - "The command writes only planning proposal files."
verification:
  - "python scripts/work.py split TASK-AR-901 --json"
---

# {task_id} - Split parent task

## Goal

- Parent task for split tests.

## Target Files

- scripts/work.py

## Acceptance Criteria

- The command proposes worker-ready unit specs.
- The command writes only planning proposal files.

## Verification

- `python scripts/work.py split TASK-AR-901 --json`
""",
        encoding="utf-8",
    )
    return path


def _write_existing_unit(root: Path) -> Path:
    task_id = "TASK-AR-901"
    unit_id = "UNIT-TASK-AR-901-001"
    path = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id / f"{unit_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
schema_version: agent-runtime-work-item/v1
work_id: {unit_id}
work_uid: 11111111-1111-4111-8111-000000000001
kind: unit
parent_id: {task_id}
unit_id: {unit_id}
task_id: {task_id}
task_set_id: TASKSET-TEST
initiative_id: INIT-TEST
project_id: PROJECT-TEST
status: worker_ready
verification_status: pending
owner: lead_engineer
created_at: 2026-06-12T12:00:00+09:00
updated_at: 2026-06-12T12:00:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-TEST.md
created_by: planner-test
horizon: unit
model_tier: worker_standard
context: "Existing split unit."
inputs:
  - scripts/work.py
target_files:
  - scripts/work.py
scope: "Existing unit prevents duplicate split proposals."
acceptance:
  - "Existing unit is detected."
verification:
  - "python scripts/work.py split TASK-AR-901 --json"
handoff: "Report pass."
stop_condition: "Stop after detection."
---

# {unit_id} - Existing Split Unit
""",
        encoding="utf-8",
    )
    return path


def test_work_split_writes_b_mode_proposal_without_creating_unit_files(tmp_path: Path) -> None:
    task_path = _write_task(tmp_path)
    before = task_path.read_text(encoding="utf-8")

    result = _run(
        tmp_path,
        "split",
        "TASK-AR-901",
        "--now",
        "2026-06-12T15:00:00+09:00",
        "--actor",
        "planner-test",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-split: proposed" in result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["status"] == "proposed"
    assert payload["existing_unit_count"] == 0
    assert payload["proposed_unit_count"] == 2
    assert payload["readiness_status"] == "pass"
    assert payload["readiness_findings"] == []
    assert payload["proposal"].startswith("agents/planning/outbox/PROP-")
    assert payload["draft"].startswith("agents/planning/drafts/PROP-")
    assert task_path.read_text(encoding="utf-8") == before
    assert not (tmp_path / "agents" / "lead_engineer" / "tasks" / "units" / "TASK-AR-901").exists()
    assert not (tmp_path / "BACKLOG-BOARD.md").exists()

    proposal = json.loads((tmp_path / payload["proposal"]).read_text(encoding="utf-8"))
    assert proposal["mode"] == "B"
    assert proposal["status"] == "proposed"
    assert proposal["action_type"] == "plan_update"
    assert proposal["proposal_output"] == "plan"
    assert proposal["target_files"] == ["agents/lead_engineer/tasks/TASK-AR-901.md"]
    assert proposal["readiness_status"] == "pass"
    assert len(proposal["proposed_units"]) == 2
    assert proposal["proposed_units"][0]["target_files"] == ["scripts/work.py"]
    assert proposal["expected_verification_command"] == "python scripts/work.py split TASK-AR-901 --json"
    assert "do not create unit files" in proposal["owner_boundary"]
    assert "reserve IDs" in proposal["owner_boundary"]
    assert (tmp_path / proposal["draft_task_path"]).exists()


def test_work_split_passes_without_proposal_when_units_already_exist(tmp_path: Path) -> None:
    task_path = _write_task(tmp_path)
    unit_path = _write_existing_unit(tmp_path)
    before = task_path.read_text(encoding="utf-8")

    result = _run(tmp_path, "split", "TASK-AR-901", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-split: pass" in result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["status"] == "pass"
    assert payload["existing_unit_count"] == 1
    assert payload["existing_units"] == [unit_path.relative_to(tmp_path).as_posix()]
    assert payload["proposal"] == ""
    assert payload["draft"] == ""
    assert task_path.read_text(encoding="utf-8") == before
    assert not (tmp_path / "agents" / "planning").exists()


def test_work_split_blocks_missing_task_without_writes(tmp_path: Path) -> None:
    result = _run(tmp_path, "split", "TASK-AR-901", "--json")

    assert result.returncode == 1
    assert "work-split:not-found:TASK-AR-901" in result.stderr
    assert not (tmp_path / "agents").exists()
