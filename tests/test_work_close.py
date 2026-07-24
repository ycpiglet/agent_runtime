from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts import backlog_board


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


def _write_task(root: Path, task_id: str = "TASK-AR-901") -> Path:
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
title: Closeout parent task
status: in_progress
priority: P1
difficulty: M
est_hours: 1
est_tokens: 100
owner: lead_engineer
initiative_id: INIT-TEST
project_id: PROJECT-TEST
task_set_id: TASKSET-TEST
origin_type: owner_request
origin_ref: reviews/REVIEW-TEST.md
created_by: planner-test
summary: Parent task for closeout tests.
tags:
  - test
---

# {task_id} - Closeout parent task

## Goal

- Parent task for closeout tests.
""",
        encoding="utf-8",
    )
    return path


def _write_unit(
    root: Path,
    *,
    verification_status: str = "passed",
    evidence_ref: str = "reviews/VERIFY-2026-06-12-unit-task-ar-901-001-20260612131000.json",
) -> Path:
    task_id = "TASK-AR-901"
    unit_id = "UNIT-TASK-AR-901-001"
    _write_task(root, task_id)
    path = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id / f"{unit_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    evidence_block = f"evidence_refs:\n  - {evidence_ref}\n" if evidence_ref else ""
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
verification_status: {verification_status}
owner: lead_engineer
created_at: 2026-06-12T12:00:00+09:00
updated_at: 2026-06-12T12:00:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-TEST.md
created_by: planner-test
horizon: unit
model_tier: worker_standard
context: "Close a verified unit."
inputs:
  - scripts/work.py
target_files:
  - scripts/work.py
scope: "Record deterministic closeout metadata."
acceptance:
  - "Closeout metadata is written."
verification:
  - "python scripts/work.py --help"
handoff: "Report closeout metadata."
stop_condition: "Stop after closeout."
verified_at: 2026-06-12T13:10:00+09:00
verified_by: tester-instance
{evidence_block}---

# {unit_id} - Closeout Test

## Context

Close a verified unit.

## Inputs

- scripts/work.py

## Target Files

- scripts/work.py

## Scope

Record deterministic closeout metadata.

## Steps

1. Close the unit.

## Acceptance Criteria

- Closeout metadata is written.

## Verification

- `python scripts/work.py --help`

## Handoff

Report closeout metadata.

## Stop Boundary

Stop after closeout.
""",
        encoding="utf-8",
    )
    return path


def _write_passed_evidence(
    root: Path,
    *,
    ref: str = "reviews/VERIFY-2026-06-12-unit-task-ar-901-001-20260612131000.json",
    status: str = "passed",
) -> Path:
    path = root / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "agent-runtime-work-verification/v1",
        "id": path.stem,
        "work_id": "UNIT-TASK-AR-901-001",
        "work_path": "agents/lead_engineer/tasks/units/TASK-AR-901/UNIT-TASK-AR-901-001.md",
        "kind": "unit",
        "task_id": "TASK-AR-901",
        "unit_id": "UNIT-TASK-AR-901-001",
        "status": status,
        "signal": "pass" if status == "passed" else "fail",
        "verified_at": "2026-06-12T13:10:00+09:00",
        "verified_by": "tester-instance",
        "command_count": 1,
        "commands": [{"command": "python scripts/work.py --help", "status": status, "returncode": 0}],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _frontmatter(path: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "---" and meta:
            break
        if ":" not in line or line.strip() == "---":
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    return meta


def test_work_close_requires_passed_evidence_and_writes_closeout_metadata(tmp_path: Path) -> None:
    unit_path = _write_unit(tmp_path)
    evidence = _write_passed_evidence(tmp_path)

    result = _run(
        tmp_path,
        "close",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:30:00+09:00",
        "--actor",
        "tester-instance",
        "--actual-hours",
        "1.25",
        "--actual-tokens",
        "321",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-close: closed" in result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["status"] == "closed"
    assert payload["work_id"] == "UNIT-TASK-AR-901-001"
    assert payload["resolution"] == "done"
    assert payload["evidence_refs"] == [evidence.relative_to(tmp_path).as_posix()]

    meta = _frontmatter(unit_path)
    assert meta["status"] == "completed"
    assert meta["resolution"] == "done"
    assert meta["completed_at"] == "2026-06-12T13:30:00+09:00"
    assert meta["closed_by"] == "tester-instance"
    assert meta["actual_hours"] == "1.25"
    assert meta["actual_tokens"] == "321"

    text = unit_path.read_text(encoding="utf-8")
    assert "<!-- work-close:start -->" in text
    assert "## Closeout" in text
    assert "- Actual hours: `1.25`" in text
    assert evidence.relative_to(tmp_path).as_posix() in text
    assert (tmp_path / "BACKLOG-BOARD.md").exists()
    assert (tmp_path / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.md").exists()
    assert evidence.relative_to(tmp_path).as_posix() in (tmp_path / "reviews" / "INDEX.md").read_text(encoding="utf-8")


def test_work_close_preserves_quoted_hash_metadata(tmp_path: Path) -> None:
    unit_path = _write_unit(tmp_path)
    _write_passed_evidence(tmp_path)
    expected = 'Close issue #167 with both \'single\' and "double" quotes.'
    encoded = json.dumps(backlog_board.ENCODED_WORK_SCALAR_PREFIX + expected)
    text = unit_path.read_text(encoding="utf-8").replace(
        'context: "Close a verified unit."',
        f"context: {encoded}",
    )
    unit_path.write_text(text, encoding="utf-8")

    result = _run(
        tmp_path,
        "close",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:31:00+09:00",
        "--actor",
        "tester-instance",
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    after, _ = backlog_board.parse_frontmatter(unit_path.read_text(encoding="utf-8"))
    assert after["context"] == expected


def test_work_close_rejects_unsafe_legacy_hash_scalar_without_mutating(tmp_path: Path) -> None:
    unit_path = _write_unit(tmp_path)
    _write_passed_evidence(tmp_path)
    text = unit_path.read_text(encoding="utf-8").replace(
        'context: "Close a verified unit."',
        "context: Preserve GitHub issue #274 before closeout.",
    )
    unit_path.write_text(text, encoding="utf-8")
    before = unit_path.read_bytes()

    result = _run(
        tmp_path,
        "close",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:31:30+09:00",
        "--actor",
        "tester-instance",
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--json",
    )

    assert result.returncode == 1
    assert "work-close:unsafe-legacy-frontmatter-scalar:" in result.stderr
    assert ":context:line-" in result.stderr
    assert unit_path.read_bytes() == before
    assert not (tmp_path / "BACKLOG-BOARD.md").exists()


def test_work_close_blocks_without_passed_verification_or_evidence_refs(tmp_path: Path) -> None:
    unit_path = _write_unit(tmp_path, verification_status="pending", evidence_ref="")
    before = unit_path.read_text(encoding="utf-8")

    result = _run(
        tmp_path,
        "close",
        "UNIT-TASK-AR-901-001",
        "--actual-hours",
        "1",
        "--actual-tokens",
        "10",
        "--json",
    )

    assert result.returncode == 1
    assert "closeout:verification-status-not-passed:pending" in result.stderr
    assert "closeout:no-evidence-refs" in result.stderr
    assert unit_path.read_text(encoding="utf-8") == before
    assert not (tmp_path / "BACKLOG-BOARD.md").exists()


def test_work_close_blocks_done_without_actuals_without_mutating(tmp_path: Path) -> None:
    unit_path = _write_unit(tmp_path)
    _write_passed_evidence(tmp_path)
    before = unit_path.read_text(encoding="utf-8")

    result = _run(tmp_path, "close", "UNIT-TASK-AR-901-001", "--json")

    assert result.returncode == 1
    assert "work-close:missing-actual-hours" in result.stderr
    assert "work-close:missing-actual-tokens" in result.stderr
    assert unit_path.read_text(encoding="utf-8") == before


def test_work_close_exact_task_id_ignores_descendant_unit(tmp_path: Path) -> None:
    unit_path = _write_unit(tmp_path)
    unit_before = unit_path.read_text(encoding="utf-8")
    task_path = tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md"

    result = _run(
        tmp_path,
        "close",
        "TASK-AR-901",
        "--resolution",
        "superseded",
        "--now",
        "2026-06-12T13:40:00+09:00",
        "--actor",
        "tester-instance",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["work_id"] == "TASK-AR-901"
    assert payload["work_path"] == "agents/lead_engineer/tasks/TASK-AR-901.md"
    assert payload["resolution"] == "superseded"
    assert _frontmatter(task_path)["status"] == "completed"
    assert unit_path.read_text(encoding="utf-8") == unit_before
