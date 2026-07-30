from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import backlog_board, org_model_gate


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "work.py"
TASKSET_DISPATCHER = REPO_ROOT / "scripts" / "taskset_dispatcher.py"
UNIT_GATE = REPO_ROOT / "scripts" / "task_unit_readiness_gate.py"


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


def _run_work(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_dispatcher(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TASKSET_DISPATCHER), "--root", str(root), *args],
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


def _payload(
    *,
    duplicate: bool = False,
    missing_goal: bool = False,
    include_units: bool = False,
    missing_unit_context: bool = False,
) -> dict[str, object]:
    units: list[dict[str, object]] = []
    if include_units:
        units = [
            {
                "title": "Worker-ready implementation unit",
                "context": "Create a focused unit from structured registration input.",
                "inputs": ["registration.json", "agents/lead_engineer/tasks/TASK-AR-901.md"],
                "target_files": ["scripts/work.py", "tests/test_work_registration.py"],
                "scope": "Generate one worker-ready unit spec for the first registered task.",
                "steps": ["Add unit rendering.", "Run the readiness gate."],
                "acceptance": ["The unit spec file exists.", "The readiness gate passes for the generated unit."],
                "verification": [
                    "python scripts/task_unit_readiness_gate.py --task-id TASK-AR-901 --unit-id UNIT-TASK-AR-901-001 --require-ready --check"
                ],
                "handoff": "Report the generated unit path and gate result.",
                "stop_condition": "Stop after this generated unit spec is verified.",
            }
        ]
        if missing_unit_context:
            units[0].pop("context")
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
                "units": units,
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


def _run_unit_gate(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(UNIT_GATE), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


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


def test_work_new_task_round_trips_into_verify_without_frontmatter_repair(tmp_path: Path) -> None:
    payload = _payload()
    payload["tasks"] = [payload["tasks"][0]]  # type: ignore[index]
    command = "python scripts/registered_check.py"
    payload["tasks"][0]["verification"] = [command]  # type: ignore[index]
    script = tmp_path / "scripts" / "registered_check.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('registered task verified')\n", encoding="utf-8")
    input_path = _write_input(tmp_path, payload)

    registered = _run(tmp_path, input_path)

    assert registered.returncode == 0, registered.stderr or registered.stdout
    task_path = tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md"
    task_meta, _ = backlog_board.parse_frontmatter(task_path.read_text(encoding="utf-8"))
    assert task_meta["acceptance"] == ["First task exists."]
    assert task_meta["verification"] == [command]

    verified = _run_work(
        tmp_path,
        "verify",
        "TASK-AR-901",
        "--now",
        "2026-06-12T12:20:00+09:00",
        "--actor",
        "round-trip-test",
        "--json",
    )

    assert verified.returncode == 0, verified.stderr or verified.stdout
    result = json.loads(verified.stdout[verified.stdout.index("{") :])
    evidence = json.loads((tmp_path / result["evidence"]).read_text(encoding="utf-8"))
    assert evidence["commands"][0]["command"] == command
    assert evidence["commands"][0]["stdout"].strip() == "registered task verified"


def test_work_new_preserves_task_dependencies_and_replays_exactly(
    tmp_path: Path,
) -> None:
    payload = _payload(include_units=True)
    payload["tasks"][1]["units"] = payload["tasks"][0].pop("units")  # type: ignore[index]
    payload["tasks"][1]["depends_on"] = ["TASK-AR-901"]  # type: ignore[index]
    input_path = _write_input(tmp_path, payload)

    registered = _run(tmp_path, input_path)
    replayed = _run(tmp_path, input_path)

    assert registered.returncode == 0, registered.stderr or registered.stdout
    assert replayed.returncode == 0, replayed.stderr or replayed.stdout
    assert '"status": "already_exists"' in replayed.stdout
    task_path = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "TASK-AR-902.md"
    )
    task_meta, _ = backlog_board.parse_frontmatter(
        task_path.read_text(encoding="utf-8")
    )
    assert task_meta["depends_on"] == ["TASK-AR-901"]
    unit_path = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-AR-902"
        / "UNIT-TASK-AR-902-001.md"
    )
    unit_meta, _ = backlog_board.parse_frontmatter(
        unit_path.read_text(encoding="utf-8")
    )
    assert unit_meta["depends_on"] == ["TASK-AR-901"]


def test_work_new_rejects_missing_task_dependency_before_writes(
    tmp_path: Path,
) -> None:
    payload = _payload()
    payload["tasks"][1]["depends_on"] = ["TASK-AR-999"]  # type: ignore[index]
    input_path = _write_input(tmp_path, payload)

    result = _run(tmp_path, input_path)

    assert result.returncode != 0
    assert "depends_on:missing:TASK-AR-999" in result.stderr
    assert not (
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md"
    ).exists()


def test_work_new_rejects_task_dependency_cycle_before_writes(
    tmp_path: Path,
) -> None:
    payload = _payload()
    payload["tasks"][0]["depends_on"] = ["TASK-AR-902"]  # type: ignore[index]
    payload["tasks"][1]["depends_on"] = ["TASK-AR-901"]  # type: ignore[index]
    input_path = _write_input(tmp_path, payload)

    result = _run(tmp_path, input_path)

    assert result.returncode != 0
    assert "depends_on:cycle:TASK-AR-901->TASK-AR-902->TASK-AR-901" in result.stderr
    assert not (
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md"
    ).exists()


@pytest.mark.parametrize(
    "depends_on,code",
    [
        (["TASK-AR-902"], "depends_on:self:TASK-AR-902"),
        (
            ["TASK-AR-901", "TASK-AR-901"],
            "depends_on:duplicate:TASK-AR-901",
        ),
        (["not-a-task"], "depends_on:invalid:not-a-task"),
    ],
)
def test_work_new_rejects_invalid_task_dependencies(
    tmp_path: Path,
    depends_on: list[str],
    code: str,
) -> None:
    payload = _payload()
    payload["tasks"][1]["depends_on"] = depends_on  # type: ignore[index]
    input_path = _write_input(tmp_path, payload)

    result = _run(tmp_path, input_path)

    assert result.returncode != 0
    assert code in result.stderr


def test_work_new_preserves_type_like_strings_for_org_model_consumers(tmp_path: Path) -> None:
    payload = _payload(include_units=True)
    first_task = payload["tasks"][0]
    first_task["title"] = "true"
    unit = first_task["units"][0]
    unit["context"] = "False"
    unit["target_files"] = ["007"]
    unit["acceptance"] = ["-7"]
    input_path = _write_input(tmp_path, payload)

    result = _run(tmp_path, input_path)

    assert result.returncode == 0, result.stderr or result.stdout
    task_path = tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md"
    unit_path = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-AR-901"
        / "UNIT-TASK-AR-901-001.md"
    )
    task_meta = org_model_gate.parse_frontmatter(task_path.read_text(encoding="utf-8"))
    unit_meta = org_model_gate.parse_frontmatter(unit_path.read_text(encoding="utf-8"))
    assert task_meta["title"] == "true"
    assert task_meta["est_tokens"] == 1000
    assert task_meta["est_hours"] == 1
    assert unit_meta["context"] == "False"
    assert unit_meta["target_files"] == ["007"]
    assert unit_meta["acceptance"] == ["-7"]
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
    assert registry["tasksets"][0]["tasks"] == ["TASK-AR-901", "TASK-AR-902"]

    board = (tmp_path / "BACKLOG-BOARD.md").read_text(encoding="utf-8")
    assert "### Work CLI Test (`TASKSET-TEST-WORK-CLI`)" in board
    assert "TASK-AR-901" in board
    classification = (tmp_path / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "`TASK-AR-901`" in classification
    owner_docs = (tmp_path / "owner-docs.yml").read_text(encoding="utf-8")
    assert "reviews/REVIEW-2026-06-12-taskset-test-work-cli-registration.md" in owner_docs


def test_work_new_taskset_registry_is_immediately_dispatchable(tmp_path: Path) -> None:
    input_path = _write_input(tmp_path, _payload())

    registered = _run(tmp_path, input_path)
    planned = _run_dispatcher(tmp_path, "plan", "test-work-cli", "--json")

    assert registered.returncode == 0, registered.stderr or registered.stdout
    assert planned.returncode == 0, planned.stderr or planned.stdout
    payload = json.loads(planned.stdout)
    assert payload["task_set_id"] == "TASKSET-TEST-WORK-CLI"
    assert payload["display_name"] == "Work CLI Test"
    assert payload["next_task_id"] == "TASK-AR-901"


def test_work_new_preserves_registration_order_before_score_fallback(
    tmp_path: Path,
) -> None:
    payload = _payload()
    payload["tasks"][0]["priority"] = "P2"
    payload["tasks"][1]["priority"] = "P0"
    input_path = _write_input(tmp_path, payload)

    registered = _run(tmp_path, input_path)
    planned = _run_dispatcher(tmp_path, "plan", "test-work-cli", "--json")

    assert registered.returncode == 0, registered.stderr or registered.stdout
    assert planned.returncode == 0, planned.stderr or planned.stdout
    assert json.loads(planned.stdout)["next_task_id"] == "TASK-AR-901"


def test_work_new_idempotently_upgrades_legacy_registry_order(
    tmp_path: Path,
) -> None:
    input_path = _write_input(tmp_path, _payload())
    first = _run(tmp_path, input_path)
    assert first.returncode == 0, first.stderr or first.stdout
    registry_path = (
        tmp_path
        / "agents"
        / "project"
        / "work-items"
        / "TASKSET-DEFINITIONS.json"
    )
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["tasksets"][0].pop("tasks")
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    second = _run(tmp_path, input_path)

    assert second.returncode == 0, second.stderr or second.stdout
    upgraded = json.loads(registry_path.read_text(encoding="utf-8"))
    assert upgraded["tasksets"][0]["tasks"] == ["TASK-AR-901", "TASK-AR-902"]


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


def test_work_new_creates_worker_ready_unit_specs_from_task_input(tmp_path: Path) -> None:
    input_path = _write_input(tmp_path, _payload(include_units=True))

    result = _run(tmp_path, input_path)

    assert result.returncode == 0, result.stderr or result.stdout
    created = json.loads(result.stdout[result.stdout.index("{") :])
    assert created["units"] == [
        "agents/lead_engineer/tasks/units/TASK-AR-901/UNIT-TASK-AR-901-001.md"
    ]
    task_meta = _frontmatter(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md")
    assert task_meta["unit_spec"] == "agents/lead_engineer/tasks/units/TASK-AR-901/UNIT-TASK-AR-901-001.md"

    unit_path = tmp_path / "agents" / "lead_engineer" / "tasks" / "units" / "TASK-AR-901" / "UNIT-TASK-AR-901-001.md"
    assert unit_path.exists()
    unit_meta = _frontmatter(unit_path)
    assert unit_meta["schema_version"] == "agent-runtime-work-item/v1"
    assert unit_meta["kind"] == "unit"
    assert unit_meta["work_id"] == "UNIT-TASK-AR-901-001"
    assert unit_meta["parent_id"] == "TASK-AR-901"
    assert unit_meta["status"] == "worker_ready"
    assert unit_meta["verification_status"] == "pending"
    assert task_meta["worker_model_tier"] == "worker_low"
    assert unit_meta["model_tier"] == "worker_low"
    parsed_unit = org_model_gate.parse_frontmatter(unit_path.read_text(encoding="utf-8"))
    assert parsed_unit["escalation_triggers"] == []

    body = unit_path.read_text(encoding="utf-8")
    for heading in (
        "## Context",
        "## Inputs",
        "## Target Files",
        "## Scope",
        "## Steps",
        "## Acceptance Criteria",
        "## Verification",
        "## Handoff",
        "## Stop Boundary",
    ):
        assert heading in body

    # The gate now verifies declared target_files/inputs paths exist (GH #125);
    # materialize the fixture's declared paths in the tmp root.
    for rel in ("scripts/work.py", "tests/test_work_registration.py", "registration.json"):
        declared = tmp_path / rel
        declared.parent.mkdir(parents=True, exist_ok=True)
        if not declared.exists():
            declared.write_text("fixture\n", encoding="utf-8")

    gate = _run_unit_gate(
        tmp_path,
        "--task-id",
        "TASK-AR-901",
        "--unit-id",
        "UNIT-TASK-AR-901-001",
        "--require-ready",
        "--check",
    )
    assert gate.returncode == 0, gate.stdout + gate.stderr
    assert "task-unit-readiness-gate: pass" in gate.stdout

    classification = (tmp_path / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "`UNIT-TASK-AR-901-001`" in classification


def test_work_new_preserves_only_explicit_escalation_triggers(tmp_path: Path) -> None:
    payload = _payload(include_units=True)
    first_task = payload["tasks"][0]
    first_task["worker_model_tier"] = "worker_low"
    first_task["units"][0]["escalation_triggers"] = ["data_integrity"]
    input_path = _write_input(tmp_path, payload)

    result = _run(tmp_path, input_path)

    assert result.returncode == 0, result.stderr or result.stdout
    task_path = (
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md"
    )
    unit_path = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-AR-901"
        / "UNIT-TASK-AR-901-001.md"
    )
    task_meta = org_model_gate.parse_frontmatter(task_path.read_text(encoding="utf-8"))
    unit_meta = org_model_gate.parse_frontmatter(unit_path.read_text(encoding="utf-8"))
    assert task_meta["worker_model_tier"] == "worker_low"
    assert unit_meta["model_tier"] == "worker_low"
    assert unit_meta["escalation_triggers"] == ["data_integrity"]

    second = _run(tmp_path, input_path)
    assert second.returncode == 0, second.stderr or second.stdout
    again = json.loads(second.stdout[second.stdout.index("{") :])
    assert again["status"] == "already_exists"
    assert again["units"] == [
        "agents/lead_engineer/tasks/units/TASK-AR-901/UNIT-TASK-AR-901-001.md"
    ]


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


def test_work_new_blocks_missing_unit_required_fields_without_partial_files(tmp_path: Path) -> None:
    input_path = _write_input(tmp_path, _payload(include_units=True, missing_unit_context=True))

    result = _run(tmp_path, input_path)

    assert result.returncode == 1
    assert "input:tasks[1].units[1]:missing:context" in result.stderr
    assert not (tmp_path / "agents").exists()


def test_work_new_round_trips_hash_and_quote_bearing_frontmatter_values(tmp_path: Path) -> None:
    payload = _payload(include_units=True)
    origin_ref = "reviews/REVIEW-TEST.md#issue-167"
    task_summary = 'Preserve issue #167 with both \'single\' and "double" quotes.'
    unit_context = 'Keep issue #168 with both \'single\' and "double" quotes.'
    splitline_values = [
        f"left{separator}right"
        for separator in (
            "\n",
            "\r",
            "\r\n",
            "\v",
            "\f",
            "\x1c",
            "\x1d",
            "\x1e",
            "\x85",
            "\u2028",
            "\u2029",
        )
    ]
    acceptance = [
        "Preserve PR #167 and Owner's note.",
        'Preserve PR #168 and the "reviewed" label.',
        *splitline_values,
    ]
    bracketed_summary = "[planned, done]"
    payload["origin_ref"] = origin_ref
    payload["tasks"][0]["summary"] = task_summary  # type: ignore[index]
    payload["tasks"][0]["units"][0]["context"] = unit_context  # type: ignore[index]
    payload["tasks"][0]["units"][0]["acceptance"] = acceptance  # type: ignore[index]
    payload["tasks"][1]["summary"] = bracketed_summary  # type: ignore[index]
    input_path = _write_input(tmp_path, payload)

    result = _run(tmp_path, input_path)

    assert result.returncode == 0, result.stderr or result.stdout
    task_path = tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md"
    unit_path = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-AR-901"
        / "UNIT-TASK-AR-901-001.md"
    )
    task_meta, _ = backlog_board.parse_frontmatter(task_path.read_text(encoding="utf-8"))
    unit_meta, _ = backlog_board.parse_frontmatter(unit_path.read_text(encoding="utf-8"))
    second_meta, _ = backlog_board.parse_frontmatter(
        (tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-902.md").read_text(
            encoding="utf-8"
        )
    )
    assert task_meta["summary"] == task_summary
    assert task_meta["origin_ref"] == origin_ref
    assert unit_meta["context"] == unit_context
    assert unit_meta["origin_ref"] == origin_ref
    assert unit_meta["acceptance"] == acceptance
    assert second_meta["summary"] == bracketed_summary
    encoded_prefix = json.dumps(backlog_board.ENCODED_WORK_SCALAR_PREFIX)[1:-1]
    assert encoded_prefix in task_path.read_text(encoding="utf-8")
