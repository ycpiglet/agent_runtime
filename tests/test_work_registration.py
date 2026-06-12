from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "work.py"


def _run(root: Path, input_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "new", "--input", str(input_path), "--json", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_input(root: Path, payload: dict[str, object]) -> Path:
    path = root / "registration.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _payload(*, duplicate: bool = False, missing_goal: bool = False) -> dict[str, object]:
    task_two_id = "TASK-AR-901" if duplicate else "TASK-AR-902"
    task_two: dict[str, object] = {
        "display_id": task_two_id,
        "title": "Second registered task",
        "goal": "Create the second task from structured input.",
        "acceptance": ["Second task exists."],
        "verification": ["python scripts/task_identity.py check --check"],
    }
    if missing_goal:
        task_two.pop("goal")
    return {
        "schema_version": "agent-runtime-work-registration/v1",
        "project_id": "PROJECT-TEST",
        "origin_type": "owner_request",
        "origin_ref": "reviews/REVIEW-TEST.md",
        "created_by": "planner-test",
        "now": "2026-06-12T12:10:00+09:00",
        "initiative": {
            "id": "INIT-TEST-WORK-CLI",
            "title": "Test Work CLI Initiative",
            "summary": "Exercise the deterministic work registration path.",
            "owner": "lead_engineer",
        },
        "taskset": {
            "id": "TASKSET-TEST-WORK-CLI",
            "display_name": "Work CLI Test",
            "summary": "Structured registration test taskset.",
            "order": 501,
            "plan_slug": "2026-06-12-test-work-cli",
        },
        "tasks": [
            {
                "display_id": "TASK-AR-901",
                "title": "First registered task",
                "goal": "Create the first task from structured input.",
                "acceptance": ["First task exists."],
                "verification": ["python scripts/task_identity.py check --check"],
            },
            task_two,
        ],
    }


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


def test_work_new_creates_initiative_taskset_tasks_review_and_views(tmp_path: Path) -> None:
    input_path = _write_input(tmp_path, _payload())

    result = _run(tmp_path, input_path)

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-new: pass" in result.stdout
    created = json.loads(result.stdout[result.stdout.index("{") :])
    assert created["status"] == "created"
    assert (tmp_path / "agents" / "project" / "initiatives" / "INIT-TEST-WORK-CLI.md").exists()
    assert (tmp_path / "docs" / "superpowers" / "plans" / "2026-06-12-test-work-cli.md").exists()
    assert (tmp_path / "reviews" / "REVIEW-2026-06-12-taskset-test-work-cli-registration.md").exists()
    first = tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md"
    second = tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-902.md"
    assert first.exists()
    assert second.exists()

    meta = _frontmatter(first)
    assert meta["schema_version"] == "agent-runtime-work-item/v1"
    assert meta["kind"] == "task"
    assert meta["work_id"] == "TASK-AR-901"
    assert meta["parent_id"] == "TASKSET-TEST-WORK-CLI"
    assert meta["origin_type"] == "owner_request"
    assert meta["created_by"] == "planner-test"
    assert meta["project_id"] == "PROJECT-TEST"
    assert meta["reservation_id"].startswith("RES-20260612-121000-")

    ledger = json.loads(
        (tmp_path / "agents" / "project" / "work-items" / "TASK-ID-RESERVATIONS.json").read_text(
            encoding="utf-8"
        )
    )
    assert [row["status"] for row in ledger["reservations"]] == ["fulfilled", "fulfilled"]
    assert [row["display_id"] for row in ledger["reservations"]] == ["TASK-AR-901", "TASK-AR-902"]

    registry = json.loads(
        (tmp_path / "agents" / "project" / "work-items" / "TASKSET-DEFINITIONS.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry["tasksets"][0]["task_set_id"] == "TASKSET-TEST-WORK-CLI"

    board = (tmp_path / "BACKLOG-BOARD.md").read_text(encoding="utf-8")
    assert "### Work CLI Test (`TASKSET-TEST-WORK-CLI`)" in board
    assert "TASK-AR-901" in board
    classification = (tmp_path / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "`TASK-AR-901`" in classification
    owner_docs = (tmp_path / "owner-docs.yml").read_text(encoding="utf-8")
    assert "reviews/REVIEW-2026-06-12-taskset-test-work-cli-registration.md" in owner_docs


def test_work_new_is_idempotent_for_same_structured_input(tmp_path: Path) -> None:
    input_path = _write_input(tmp_path, _payload())
    first = _run(tmp_path, input_path)
    second = _run(tmp_path, input_path)

    assert first.returncode == 0, first.stderr or first.stdout
    assert second.returncode == 0, second.stderr or second.stdout
    payload = json.loads(second.stdout[second.stdout.index("{") :])
    assert payload["status"] == "already_exists"
    ledger = json.loads(
        (tmp_path / "agents" / "project" / "work-items" / "TASK-ID-RESERVATIONS.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(ledger["reservations"]) == 2


def test_work_new_allocates_missing_display_ids_through_reservation_ledger(tmp_path: Path) -> None:
    payload = _payload()
    for task in payload["tasks"]:  # type: ignore[index]
        task.pop("display_id")  # type: ignore[union-attr]
    input_path = _write_input(tmp_path, payload)

    result = _run(tmp_path, input_path)

    assert result.returncode == 0, result.stderr or result.stdout
    assert (tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-001.md").exists()
    assert (tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-002.md").exists()
    ledger = json.loads(
        (tmp_path / "agents" / "project" / "work-items" / "TASK-ID-RESERVATIONS.json").read_text(
            encoding="utf-8"
        )
    )
    assert [row["display_id"] for row in ledger["reservations"]] == ["TASK-AR-001", "TASK-AR-002"]
    assert [row["status"] for row in ledger["reservations"]] == ["fulfilled", "fulfilled"]


def test_work_new_blocks_duplicate_display_ids_without_partial_files(tmp_path: Path) -> None:
    input_path = _write_input(tmp_path, _payload(duplicate=True))

    result = _run(tmp_path, input_path)

    assert result.returncode == 1
    assert "input:tasks:duplicate-display-id:TASK-AR-901" in result.stderr
    assert not (tmp_path / "agents").exists()


def test_work_new_blocks_missing_required_fields_without_partial_files(tmp_path: Path) -> None:
    input_path = _write_input(tmp_path, _payload(missing_goal=True))

    result = _run(tmp_path, input_path)

    assert result.returncode == 1
    assert "input:tasks[2]:missing:goal" in result.stderr
    assert not (tmp_path / "agents").exists()
