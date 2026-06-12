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


def _write_unit(root: Path, *, include_verification: bool = True, include_acceptance: bool = True) -> Path:
    task_id = "TASK-AR-901"
    unit_id = "UNIT-TASK-AR-901-001"
    path = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id / f"{unit_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    acceptance = (
        "acceptance:\n  - \"The command writes a B-mode proposal for unverifiable criteria.\"\n"
        if include_acceptance
        else ""
    )
    verification = "verification:\n  - \"python scripts/work.py criteria UNIT-TASK-AR-901-001 --json\"\n" if include_verification else ""
    body_acceptance = (
        "## Acceptance Criteria\n\n- The command writes a B-mode proposal for unverifiable criteria.\n\n"
        if include_acceptance
        else ""
    )
    body_verification = (
        "## Verification\n\n- `python scripts/work.py criteria UNIT-TASK-AR-901-001 --json`\n\n"
        if include_verification
        else ""
    )
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
context: "Evaluate criteria."
inputs:
  - scripts/work.py
target_files:
  - scripts/work.py
scope: "Write a criteria proposal only when needed."
{acceptance}{verification}handoff: "Report proposal path."
stop_condition: "Stop after proposal output."
---

# {unit_id} - Criteria Test

## Context

Evaluate criteria.

{body_acceptance}{body_verification}## Handoff

Report proposal path.

## Stop Boundary

Stop after proposal output.
""",
        encoding="utf-8",
    )
    return path


def test_work_criteria_writes_b_mode_proposal_without_mutating_work_item(tmp_path: Path) -> None:
    unit_path = _write_unit(tmp_path, include_verification=False)
    before = unit_path.read_text(encoding="utf-8")

    result = _run(
        tmp_path,
        "criteria",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:45:00+09:00",
        "--actor",
        "planner-test",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-criteria: proposed" in result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["status"] == "proposed"
    assert payload["gap_count"] == 1
    assert payload["criterion_count"] == 1
    assert payload["verification_count"] == 0
    assert payload["proposal"].startswith("agents/planning/outbox/PROP-")
    assert payload["draft"].startswith("agents/planning/drafts/PROP-")
    assert unit_path.read_text(encoding="utf-8") == before
    assert not (tmp_path / "BACKLOG-BOARD.md").exists()

    proposal = json.loads((tmp_path / payload["proposal"]).read_text(encoding="utf-8"))
    assert proposal["mode"] == "B"
    assert proposal["status"] == "proposed"
    assert proposal["action_type"] == "plan_update"
    assert proposal["proposal_output"] == "plan"
    assert proposal["risk_tier"] == "low"
    assert proposal["target_files"] == [
        "agents/lead_engineer/tasks/units/TASK-AR-901/UNIT-TASK-AR-901-001.md"
    ]
    assert proposal["expected_verification_command"] == "python scripts/work.py criteria UNIT-TASK-AR-901-001 --json"
    assert "without approved apply" in proposal["owner_boundary"]
    assert "lacks an executable verification command" in proposal["evidence"][0]["summary"]
    assert (tmp_path / proposal["draft_task_path"]).exists()


def test_work_criteria_passes_without_proposal_when_verification_is_executable(tmp_path: Path) -> None:
    unit_path = _write_unit(tmp_path, include_verification=True)
    before = unit_path.read_text(encoding="utf-8")

    result = _run(tmp_path, "criteria", "UNIT-TASK-AR-901-001", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-criteria: pass" in result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["status"] == "pass"
    assert payload["gap_count"] == 0
    assert payload["proposal"] == ""
    assert unit_path.read_text(encoding="utf-8") == before
    assert not (tmp_path / "agents" / "planning").exists()


def test_work_criteria_blocks_missing_work_without_writes(tmp_path: Path) -> None:
    result = _run(tmp_path, "criteria", "UNIT-TASK-AR-901-001", "--json")

    assert result.returncode == 1
    assert "work-criteria:not-found:UNIT-TASK-AR-901-001" in result.stderr
    assert not (tmp_path / "agents").exists()
