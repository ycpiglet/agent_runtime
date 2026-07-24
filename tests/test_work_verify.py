from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

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


def _write_unit(root: Path, *, command: str, unit_id: str = "UNIT-TASK-AR-901-001") -> Path:
    task_id = "TASK-AR-901"
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
context: "Verify command execution."
inputs:
  - scripts/check.py
target_files:
  - scripts/check.py
scope: "Run one verification command."
acceptance:
  - "Verification evidence is written."
verification:
  - "{command}"
handoff: "Report evidence path."
stop_condition: "Stop after verification."
---

# {unit_id} - Verification Test

## Context

Verify command execution.

## Inputs

- scripts/check.py

## Target Files

- scripts/check.py

## Scope

Run one verification command.

## Steps

1. Run the command.

## Acceptance Criteria

- Verification evidence is written.

## Verification

- `{command}`

## Handoff

Report evidence path.

## Stop Boundary

Stop after verification.
""",
        encoding="utf-8",
    )
    return path


def _write_task(root: Path, *, command: str, task_id: str = "TASK-AR-901") -> Path:
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
status: in_progress
owner: lead-engineer
created_at: 2026-06-12T12:00:00+09:00
updated_at: 2026-06-12T12:00:00+09:00
acceptance:
  - "Task verification evidence is written."
verification:
  - "{command}"
---

# {task_id} - Verification Test
""",
        encoding="utf-8",
    )
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


def test_work_verify_runs_unit_commands_writes_evidence_and_updates_frontmatter(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "check.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('verify ok')\n", encoding="utf-8")
    command = f"{sys.executable} scripts/check.py"
    unit_path = _write_unit(tmp_path, command=command)

    result = _run(
        tmp_path,
        "verify",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:10:00+09:00",
        "--actor",
        "tester-instance",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-verify: passed" in result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["status"] == "passed"
    evidence = tmp_path / payload["evidence"]
    assert evidence.exists()
    evidence_payload = json.loads(evidence.read_text(encoding="utf-8"))
    assert evidence_payload["schema"] == "agent-runtime-work-verification/v1"
    assert evidence_payload["work_id"] == "UNIT-TASK-AR-901-001"
    assert evidence_payload["status"] == "passed"
    assert evidence_payload["verified_at"] == "2026-06-12T13:10:00+09:00"
    assert evidence_payload["verified_by"] == "tester-instance"
    assert evidence_payload["commands"][0]["status"] == "passed"
    assert "verify ok" in evidence_payload["commands"][0]["stdout"]

    meta = _frontmatter(unit_path)
    assert meta["verification_status"] == "passed"
    assert meta["verified_at"] == "2026-06-12T13:10:00+09:00"
    assert meta["verified_by"] == "tester-instance"
    assert payload["evidence"] in unit_path.read_text(encoding="utf-8")
    assert payload["evidence"] in (tmp_path / "reviews" / "INDEX.md").read_text(encoding="utf-8")


def test_work_verify_returns_failure_and_records_failed_evidence(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "check.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "import sys\n"
        "print('bad check')\n"
        "print('bad error', file=sys.stderr)\n"
        "sys.exit(7)\n",
        encoding="utf-8",
    )
    command = f"{sys.executable} scripts/check.py"
    unit_path = _write_unit(tmp_path, command=command)

    result = _run(
        tmp_path,
        "verify",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:11:00+09:00",
        "--json",
    )

    assert result.returncode == 1
    assert "work-verify: failed" in result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    evidence_payload = json.loads((tmp_path / payload["evidence"]).read_text(encoding="utf-8"))
    assert evidence_payload["status"] == "failed"
    assert evidence_payload["commands"][0]["returncode"] == 7
    assert "bad check" in evidence_payload["commands"][0]["stdout"]
    assert "bad error" in evidence_payload["commands"][0]["stderr"]
    assert _frontmatter(unit_path)["verification_status"] == "failed"


def test_work_verify_preserves_caret_bearing_revision_argument(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "check.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "import json\n"
        "import sys\n"
        "print(json.dumps(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    revision = "v0.7.0^{}"
    command = f"{sys.executable} scripts/check.py {revision}"
    _write_unit(tmp_path, command=command)

    result = _run(
        tmp_path,
        "verify",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:11:30+09:00",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    evidence_payload = json.loads((tmp_path / payload["evidence"]).read_text(encoding="utf-8"))
    command_result = evidence_payload["commands"][0]
    assert command_result["command"] == command
    assert json.loads(command_result["stdout"]) == [revision]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows command-line compatibility")
def test_work_verify_keeps_legacy_terminal_quote_command_executable(tmp_path: Path) -> None:
    command = f'{sys.executable} -c "print(\'legacy-ok\')"'
    _write_unit(tmp_path, command=command)

    result = _run(
        tmp_path,
        "verify",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:11:40+09:00",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    evidence_payload = json.loads((tmp_path / payload["evidence"]).read_text(encoding="utf-8"))
    command_result = evidence_payload["commands"][0]
    assert command_result["command"] == command[:-1]
    assert command_result["status"] == "passed"
    assert command_result["returncode"] == 0
    assert command_result["stdout"].strip() == "legacy-ok"


def test_work_verify_timeout_retains_result_evidence_fields(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "check.py"
    script.parent.mkdir(parents=True)
    script.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
    command = f"{sys.executable} scripts/check.py"
    _write_unit(tmp_path, command=command)

    result = _run(
        tmp_path,
        "verify",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:11:45+09:00",
        "--timeout",
        "1",
        "--json",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    evidence_payload = json.loads((tmp_path / payload["evidence"]).read_text(encoding="utf-8"))
    command_result = evidence_payload["commands"][0]
    assert command_result["command"] == command
    assert command_result["status"] == "timeout"
    assert command_result["returncode"] is None
    assert set(command_result) == {
        "command",
        "status",
        "returncode",
        "started_at",
        "finished_at",
        "stdout",
        "stderr",
    }


def test_work_verify_preserves_quoted_hash_scalar_and_list_values(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "check.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('verify ok')\n", encoding="utf-8")
    unit_path = _write_unit(tmp_path, command=f"{sys.executable} scripts/check.py")
    expected = "Preserve issue #167 and Owner's note."
    text = unit_path.read_text(encoding="utf-8")
    text = text.replace(
        'context: "Verify command execution."',
        'context: "Preserve issue #167 and Owner\'s note." # reviewed YAML comment',
    ).replace(
        '  - "Verification evidence is written."',
        '  - "Preserve issue #167 and Owner\'s note."',
    )
    unit_path.write_text(text, encoding="utf-8")
    before, _ = backlog_board.parse_frontmatter(text)
    assert before["context"] == expected
    assert before["acceptance"] == [expected]

    result = _run(
        tmp_path,
        "verify",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:12:00+09:00",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    after, _ = backlog_board.parse_frontmatter(unit_path.read_text(encoding="utf-8"))
    assert after["context"] == expected
    assert after["acceptance"] == [expected]


def test_work_verify_rejects_unsafe_legacy_hash_scalar_without_mutating(tmp_path: Path) -> None:
    unit_path = _write_unit(tmp_path, command=f"{sys.executable} -c \"print('must not run')\"")
    text = unit_path.read_text(encoding="utf-8").replace(
        'context: "Verify command execution."',
        "context: #274 must survive before verification.",
    ).replace(
        '  - "Verification evidence is written."',
        "    - #275 must survive before verification.",
    )
    unit_path.write_text(text, encoding="utf-8")
    before = unit_path.read_bytes()

    result = _run(
        tmp_path,
        "verify",
        "UNIT-TASK-AR-901-001",
        "--now",
        "2026-06-12T13:12:30+09:00",
        "--json",
    )

    assert result.returncode == 1
    assert "work-verify:unsafe-legacy-frontmatter-scalar:" in result.stderr
    assert ":context:line-" in result.stderr
    assert ":acceptance:line-" in result.stderr
    assert unit_path.read_bytes() == before
    assert not (tmp_path / "reviews").exists()


def test_work_verify_blocks_unit_without_commands(tmp_path: Path) -> None:
    unit_path = _write_unit(tmp_path, command="")

    result = _run(tmp_path, "verify", "UNIT-TASK-AR-901-001", "--json")

    assert result.returncode == 1
    assert "verification:no-commands" in result.stderr
    assert "verification_status: pending" in unit_path.read_text(encoding="utf-8")
    assert not (tmp_path / "reviews").exists()


def test_work_verify_exact_task_id_ignores_descendant_unit(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "check.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('verify task ok')\n", encoding="utf-8")
    command = f"{sys.executable} scripts/check.py"
    unit_path = _write_unit(tmp_path, command=command)
    unit_before = unit_path.read_text(encoding="utf-8")
    task_path = _write_task(tmp_path, command=command)

    result = _run(
        tmp_path,
        "verify",
        "TASK-AR-901",
        "--now",
        "2026-06-12T13:20:00+09:00",
        "--actor",
        "tester-instance",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["work_id"] == "TASK-AR-901"
    assert payload["work_path"] == "agents/lead_engineer/tasks/TASK-AR-901.md"
    assert _frontmatter(task_path)["verification_status"] == "passed"
    assert unit_path.read_text(encoding="utf-8") == unit_before


def test_work_verify_duplicate_unit_id_is_ambiguous(tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "check.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('verify unit ok')\n", encoding="utf-8")
    first = _write_unit(tmp_path, command=f"{sys.executable} scripts/check.py")
    second = (
        tmp_path
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-AR-902"
        / "UNIT-TASK-AR-901-001.md"
    )
    second.parent.mkdir(parents=True, exist_ok=True)
    second.write_text(first.read_text(encoding="utf-8"), encoding="utf-8")

    result = _run(tmp_path, "verify", "UNIT-TASK-AR-901-001", "--json")

    assert result.returncode == 1
    assert (
        "work-verify:ambiguous:UNIT-TASK-AR-901-001:"
        "agents/lead_engineer/tasks/units/TASK-AR-901/UNIT-TASK-AR-901-001.md,"
        "agents/lead_engineer/tasks/units/TASK-AR-902/UNIT-TASK-AR-901-001.md"
    ) in result.stderr
