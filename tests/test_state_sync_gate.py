from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agent_runtime import state_projection


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "state_sync_gate.py"
AR655_LIVENESS_NOW = datetime(2026, 8, 3, 0, 0, tzinfo=timezone.utc)
AR655_FIXTURE_EXPIRY = "2099-01-01T00:00:00+00:00"


def load_module():
    spec = importlib.util.spec_from_file_location("state_sync_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_gate(root: Path, *, now: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--check",
            "--now",
            now,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_task(root: Path, task_id: str, task_set_id: str, status: str = "in_progress", verified: bool = False) -> None:
    write(
        root / f"agents/lead_engineer/tasks/{task_id}.md",
        f"""---
id: {task_id}
status: {status}
task_set_id: {task_set_id}
verification_status: {"passed" if verified else "pending"}
---

## Goal

Test task.
""",
    )


def write_surfaces(root: Path, task_set_id: str, active_task: str) -> None:
    write(
        root / "agents/project/NEXT-SESSION-POINTER.yml",
        f"""current_state:
  status: active
  task_set_id: {task_set_id}
resume:
  active_task: {active_task}
  active_task_set: {task_set_id}
""",
    )
    write(root / "BACKLOG-BOARD.md", f"# Board\n\n{task_set_id}\n{active_task}\n")
    write(root / "BACKLOG.md", f"# Backlog\n\n{task_set_id}\n")
    write(root / "STATUS.md", f"# Status\n\n{task_set_id}\n{active_task}\n")


def write_v2_state_adapter(root: Path, *, source: str = "BACKLOG.md") -> None:
    write(
        root / "agent_runtime.yml",
        f"""schema: agent-runtime-config/v2
project: state-sync-test
upstream:
  package: agent-runtime
  ref: test
sync:
  mode: preserve-local
  allow_silent_overwrite: false
profiles:
  - core
host:
  state_adapters:
    host-state: {source}
""",
    )


def write_unit(root: Path, task_id: str, unit_id: str, *, task_set_id: str = "TASKSET-AR-GOVERNANCE-OPS", status: str = "review", verified: bool = False, recovery: str = "") -> None:
    verification = "passed" if verified else "pending"
    extra = recovery
    write(
        root / f"agents/lead_engineer/tasks/units/{task_id}/{unit_id}.md",
        f"""---
schema_version: agent-runtime-work-item/v1
work_id: {unit_id}
kind: unit
parent_id: {task_id}
task_id: {task_id}
unit_id: {unit_id}
task_set_id: {task_set_id}
status: {status}
verification_status: {verification}
owner: lead-engineer
created_at: 2026-07-28T00:00:00+09:00
updated_at: 2026-07-28T00:00:00+09:00
origin_type: owner_request
origin_ref: reviews/TEST.md
created_by: tester
{extra}---
""",
    )


def write_claim(
    root: Path,
    *,
    task_id: str,
    unit_id: str,
    claim_id: str = "CLAIM-TEST-001",
    task_set_id: str = "TASKSET-AR-GOVERNANCE-OPS",
    agent_instance_id: str = "worker-test",
    overlay: object | None = None,
) -> str:
    claim_path = f"agents/runtime/task_claims/{claim_id}.json"
    worktree = root / ".worktrees" / claim_id
    repository = root / ".fixture-repository"
    if not repository.exists():
        subprocess.run(["git", "init", "-q", "-b", "base", str(repository)], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.email", "tests@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repository), "config", "user.name", "State Sync Tests"], check=True)
        subprocess.run(["git", "-C", str(repository), "commit", "--allow-empty", "-qm", "fixture"], check=True)
    branch = "worker-" + claim_id.lower().replace("claim-", "")
    subprocess.run(["git", "-C", str(repository), "worktree", "add", "-q", "-b", branch, str(worktree)], check=True)
    claim = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": task_id,
        "task_set_id": task_set_id,
        "unit_id": unit_id,
        "agent_role": "lead-engineer",
        "agent_instance_id": agent_instance_id,
        "status": "claimed",
        # Existing non-liveness tests model a healthy active claim. Keep that
        # authority explicit now that missing lease copies are indeterminate.
        "expires_at": AR655_FIXTURE_EXPIRY,
        "lease": {"expires_at": AR655_FIXTURE_EXPIRY},
        "worktree_path": f".worktrees/{claim_id}",
        "branch": branch,
    }
    if overlay is not None:
        claim["overlay"] = overlay
    write(root / claim_path, json.dumps(claim))
    return claim_path


def attach_claim_refs(root: Path, task_id: str, unit_id: str, claim_path: str) -> None:
    for path in (
        root / f"agents/lead_engineer/tasks/{task_id}.md",
        root / f"agents/lead_engineer/tasks/units/{task_id}/{unit_id}.md",
    ):
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("---\n", f"---\nclaim_refs:\n  - {claim_path}\n", 1), encoding="utf-8")


def write_claim_pointer(root: Path, task_id: str, claim_path: str) -> None:
    write(
        root / "agents/project/NEXT-SESSION-POINTER.yml",
        f"""current_state:
  status: in_progress
  task_set_id: TASKSET-AR-GOVERNANCE-OPS
active_work:
  current_agents:
    - claim_id: CLAIM-TEST-001
      agent_role: lead-engineer
      agent_instance_id: worker-test
resume:
  active_task: {task_id}
  active_task_set: TASKSET-AR-GOVERNANCE-OPS
pointers:
  active_claims:
    - {claim_path}
""",
    )


def write_multi_claim_pointer(root: Path, *, task_set_id: str, primary_task: str, claims: list[dict[str, str]]) -> None:
    agents = "\n".join(
        "    - claim_id: {claim_id}\n      agent_role: lead-engineer\n      agent_instance_id: {agent_instance_id}".format(**claim)
        for claim in claims
    )
    refs = "\n".join(f"    - {claim['path']}" for claim in claims)
    write(
        root / "agents/project/NEXT-SESSION-POINTER.yml",
        f"""current_state:
  status: in_progress
  task_set_id: {task_set_id}
active_work:
  current_agents:
{agents}
resume:
  active_task: {primary_task}
  active_task_set: {task_set_id}
pointers:
  active_claims:
{refs}
""",
    )


def _ar655_state_sync_claim_fixture(tmp_path: Path) -> tuple[object, Path]:
    gate = load_module()
    task_id = "TASK-AR-631"
    unit_id = "UNIT-TASK-AR-631-001"
    write_task(tmp_path, task_id, "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(tmp_path, task_id, unit_id)
    claim_ref = write_claim(tmp_path, task_id=task_id, unit_id=unit_id)
    attach_claim_refs(tmp_path, task_id, unit_id, claim_ref)
    write_claim_pointer(tmp_path, task_id, claim_ref)
    write(tmp_path / "BACKLOG-BOARD.md", f"TASKSET-AR-GOVERNANCE-OPS\n{task_id}\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", f"TASKSET-AR-GOVERNANCE-OPS\n{task_id}\n")
    return gate, tmp_path / claim_ref


def _set_ar655_claim_deadlines(
    path: Path,
    *,
    top: object,
    nested: object,
) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if top is None:
        payload.pop("expires_at", None)
    else:
        payload["expires_at"] = top
    if nested is None:
        payload.pop("lease", None)
    else:
        payload["lease"] = {"expires_at": nested}
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_ar655_state_sync_expired_claim_blocks_with_exact_pointer(tmp_path: Path) -> None:
    gate, claim_path = _ar655_state_sync_claim_fixture(tmp_path)
    expired = (AR655_LIVENESS_NOW - timedelta(seconds=601)).isoformat()
    _set_ar655_claim_deadlines(claim_path, top=expired, nested=expired)

    findings = gate.analyze(
        tmp_path,
        now=AR655_LIVENESS_NOW,
        grace_seconds=600,
    )

    assert any(
        finding.severity == "block"
        and finding.subject == "claim:liveness-expired:CLAIM-TEST-001"
        for finding in findings
    )


def test_ar655_state_sync_cli_uses_explicit_aware_now_for_liveness(tmp_path: Path) -> None:
    _, claim_path = _ar655_state_sync_claim_fixture(tmp_path)
    expired = (AR655_LIVENESS_NOW - timedelta(seconds=601)).isoformat()
    _set_ar655_claim_deadlines(claim_path, top=expired, nested=expired)

    result = _run_gate(tmp_path, now=AR655_LIVENESS_NOW.isoformat())

    assert result.returncode == 1, result.stderr or result.stdout
    assert "claim:liveness-expired:CLAIM-TEST-001" in result.stdout


@pytest.mark.parametrize("now", ("not-a-timestamp", "2026-08-03T00:00:00"))
def test_ar655_state_sync_cli_refuses_malformed_or_naive_now_without_traceback(
    tmp_path: Path,
    now: str,
) -> None:
    result = _run_gate(tmp_path, now=now)
    output = (result.stdout or "") + (result.stderr or "")

    assert result.returncode != 0
    assert "invalid --now" in output
    assert "timezone-aware" in output
    assert "unrecognized arguments" not in output
    assert "Traceback" not in output


def test_ar655_state_sync_positive_grace_equality_remains_active(tmp_path: Path) -> None:
    gate, claim_path = _ar655_state_sync_claim_fixture(tmp_path)
    equality = (AR655_LIVENESS_NOW - timedelta(seconds=600)).isoformat()
    _set_ar655_claim_deadlines(claim_path, top=equality, nested=equality)

    findings = gate.analyze(
        tmp_path,
        now=AR655_LIVENESS_NOW,
        grace_seconds=600,
    )

    assert not [finding for finding in findings if finding.severity == "block"]


@pytest.mark.parametrize(
    ("top", "nested"),
    (
        (None, None),
        (AR655_FIXTURE_EXPIRY, None),
        (AR655_FIXTURE_EXPIRY, "not-a-deadline"),
    ),
)
def test_ar655_state_sync_indeterminate_claim_retains_authority_but_blocks(
    tmp_path: Path,
    top: object,
    nested: object,
) -> None:
    gate, claim_path = _ar655_state_sync_claim_fixture(tmp_path)
    _set_ar655_claim_deadlines(claim_path, top=top, nested=nested)

    findings = gate.analyze(
        tmp_path,
        now=AR655_LIVENESS_NOW,
        grace_seconds=600,
    )
    subjects = {finding.subject for finding in findings}

    assert "claim:liveness-indeterminate:CLAIM-TEST-001" in subjects
    assert "pointer:primary-worker-missing:TASK-AR-631" not in subjects
    assert "pointer:primary-worker-missing-task" not in subjects


def test_consistent_active_pointer_passes(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-260", "TASKSET-AR-GOVERNANCE-OPS")
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "TASK-AR-260")

    findings = gate.analyze(tmp_path)

    assert not [finding for finding in findings if finding.severity == "block"]


def test_active_task_missing_blocks(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-261", "TASKSET-AR-GOVERNANCE-OPS")
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "TASK-AR-260")

    findings = gate.analyze(tmp_path)

    assert any(finding.subject == "active-task:missing:TASK-AR-260" for finding in findings)


def test_board_missing_active_taskset_blocks(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-260", "TASKSET-AR-GOVERNANCE-OPS")
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "TASK-AR-260")
    write(tmp_path / "BACKLOG-BOARD.md", "# Board\n\nOTHER-TASKSET\n")

    findings = gate.analyze(tmp_path)

    assert any(finding.subject == "surface:missing-taskset:BACKLOG-BOARD.md" for finding in findings)


def test_configured_v2_adapter_uses_fresh_projection_without_runtime_ids_or_status(tmp_path):
    gate = load_module()
    task_id = "TASK-AR-260"
    task_set_id = "TASKSET-AR-GOVERNANCE-OPS"
    write_task(tmp_path, task_id, task_set_id)
    write_surfaces(tmp_path, task_set_id, task_id)
    write(tmp_path / "BACKLOG.md", "# Host backlog\n\n- Editorial queue\n")
    (tmp_path / "STATUS.md").unlink()
    write_v2_state_adapter(tmp_path)
    state_projection.write_projection(
        tmp_path,
        now="2026-07-29T08:00:00+00:00",
    )

    findings = gate.analyze(tmp_path)

    assert not [finding for finding in findings if finding.severity == "block"]
    assert not any(finding.path in {"BACKLOG.md", "STATUS.md"} for finding in findings)


def test_configured_v2_adapter_blocks_missing_or_stale_projection(tmp_path):
    gate = load_module()
    task_id = "TASK-AR-260"
    task_set_id = "TASKSET-AR-GOVERNANCE-OPS"
    write_task(tmp_path, task_id, task_set_id)
    write_surfaces(tmp_path, task_set_id, task_id)
    write(tmp_path / "BACKLOG.md", "# Host backlog\n\n- Initial item\n")
    write_v2_state_adapter(tmp_path)

    missing = gate.analyze(tmp_path)

    assert any(
        finding.subject == "state-projection:projection-missing"
        and finding.severity == "block"
        for finding in missing
    )

    state_projection.write_projection(
        tmp_path,
        now="2026-07-29T08:00:00+00:00",
    )
    write(tmp_path / "BACKLOG.md", "# Host backlog\n\n- Changed after projection\n")

    stale = gate.analyze(tmp_path)

    assert any(
        finding.subject == "state-projection:projection-stale"
        and finding.severity == "block"
        for finding in stale
    )


def test_configured_v2_adapter_blocks_invalid_configuration(tmp_path):
    gate = load_module()
    task_id = "TASK-AR-260"
    task_set_id = "TASKSET-AR-GOVERNANCE-OPS"
    write_task(tmp_path, task_id, task_set_id)
    write_surfaces(tmp_path, task_set_id, task_id)
    write(tmp_path / "docs/HOST-STATE.md", "# Host state\n")
    write_v2_state_adapter(tmp_path, source="docs/HOST-STATE.md")

    findings = gate.analyze(tmp_path)

    assert any(
        finding.subject == "state-projection:config-invalid"
        and finding.severity == "block"
        for finding in findings
    )


def test_legacy_state_contract_still_requires_backlog_and_status(tmp_path):
    gate = load_module()
    task_id = "TASK-AR-260"
    task_set_id = "TASKSET-AR-GOVERNANCE-OPS"
    write_task(tmp_path, task_id, task_set_id)
    write_surfaces(tmp_path, task_set_id, task_id)
    (tmp_path / "BACKLOG.md").unlink()
    (tmp_path / "STATUS.md").unlink()

    findings = gate.analyze(tmp_path)

    subjects = {finding.subject for finding in findings}
    assert "surface:missing:BACKLOG.md" in subjects
    assert "surface:missing:STATUS.md" in subjects


def test_pointer_active_but_all_tasks_done_blocks(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-260", "TASKSET-AR-GOVERNANCE-OPS", status="completed")
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "TASK-AR-260")

    findings = gate.analyze(tmp_path)

    assert any(finding.subject == "taskset:active-but-complete:TASKSET-AR-GOVERNANCE-OPS" for finding in findings)


def test_completed_taskset_may_be_hidden_from_live_board(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-260", "TASKSET-AR-GOVERNANCE-OPS", status="completed")
    write(
        tmp_path / "agents/project/NEXT-SESSION-POINTER.yml",
        """current_state:
  status: complete
  task_set_id: TASKSET-AR-GOVERNANCE-OPS
resume:
  active_task: none
  active_task_set: TASKSET-AR-GOVERNANCE-OPS
""",
    )
    write(tmp_path / "BACKLOG-BOARD.md", "# Board\n\ncompleted tasksets hidden\n")
    write(tmp_path / "BACKLOG.md", "# Backlog\n\nTASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "# Status\n\nTASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert not [finding for finding in findings if finding.severity == "block"]


def test_active_worker_claim_correlates_task_unit_pointer_and_refs(tmp_path):
    gate = load_module()
    task_id = "TASK-AR-631"
    unit_id = "UNIT-TASK-AR-631-001"
    write_task(tmp_path, task_id, "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(tmp_path, task_id, unit_id)
    claim_path = write_claim(tmp_path, task_id=task_id, unit_id=unit_id)
    attach_claim_refs(tmp_path, task_id, unit_id, claim_path)
    write_claim_pointer(tmp_path, task_id, claim_path)
    write(tmp_path / "BACKLOG-BOARD.md", f"# Board\n\nTASKSET-AR-GOVERNANCE-OPS\n{task_id}\n")
    write(tmp_path / "BACKLOG.md", "# Backlog\n\nTASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", f"# Status\n\nTASKSET-AR-GOVERNANCE-OPS\n{task_id}\n")

    findings = gate.analyze(tmp_path)

    assert not [finding for finding in findings if finding.severity == "block"]


def test_active_pointer_blocks_completed_task_even_with_open_taskset_sibling(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS", status="completed")
    write_task(tmp_path, "TASK-AR-632", "TASKSET-AR-GOVERNANCE-OPS", status="in_progress")
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "TASK-AR-631")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "active-task:done:TASK-AR-631" for f in findings)


def test_active_worker_claim_blocks_completed_task_even_with_open_taskset_sibling(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS", status="completed")
    write_task(tmp_path, "TASK-AR-632", "TASKSET-AR-GOVERNANCE-OPS", status="in_progress")
    write_unit(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001")
    path = write_claim(tmp_path, task_id="TASK-AR-631", unit_id="UNIT-TASK-AR-631-001")
    attach_claim_refs(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", path)
    write_claim_pointer(tmp_path, "TASK-AR-631", path)
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "claim:task-invalid-lifecycle:CLAIM-TEST-001:completed" for f in findings)


def test_active_worker_claim_blocks_completed_unit(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", status="completed")
    path = write_claim(tmp_path, task_id="TASK-AR-631", unit_id="UNIT-TASK-AR-631-001")
    attach_claim_refs(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", path)
    write_claim_pointer(tmp_path, "TASK-AR-631", path)
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "claim:unit-invalid-lifecycle:CLAIM-TEST-001:completed" for f in findings)


def test_active_worker_claim_blocks_predispatch_or_unknown_canonical_statuses(tmp_path):
    gate = load_module()
    for index, status in enumerate(("planned", "worker_ready", "unknown", ""), start=1):
        task_id = f"TASK-AR-63{index}"
        unit_id = f"UNIT-TASK-AR-63{index}-001"
        claim_id = f"CLAIM-TEST-00{index}"
        write_task(tmp_path, task_id, "TASKSET-AR-GOVERNANCE-OPS", status=status)
        write_unit(tmp_path, task_id, unit_id, status=status)
        path = write_claim(tmp_path, task_id=task_id, unit_id=unit_id, claim_id=claim_id)
        attach_claim_refs(tmp_path, task_id, unit_id, path)
    write_multi_claim_pointer(
        tmp_path,
        task_set_id="TASKSET-AR-GOVERNANCE-OPS",
        primary_task="TASK-AR-631",
        claims=[
            {"claim_id": f"CLAIM-TEST-00{index}", "agent_instance_id": "worker-test", "path": f"agents/runtime/task_claims/CLAIM-TEST-00{index}.json"}
            for index in range(1, 5)
        ],
    )
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    subjects = {f.subject for f in findings}
    for index, status in enumerate(("planned", "worker_ready", "unknown", "unknown"), start=1):
        assert f"claim:task-invalid-lifecycle:CLAIM-TEST-00{index}:{status}" in subjects
        assert f"claim:unit-invalid-lifecycle:CLAIM-TEST-00{index}:{status}" in subjects


def test_active_worker_claim_blocks_missing_canonical_statuses(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001")
    for path in (
        tmp_path / "agents/lead_engineer/tasks/TASK-AR-631.md",
        tmp_path / "agents/lead_engineer/tasks/units/TASK-AR-631/UNIT-TASK-AR-631-001.md",
    ):
        path.write_text(path.read_text(encoding="utf-8").replace("status: in_progress\n", "").replace("status: review\n", ""), encoding="utf-8")
    claim_path = write_claim(tmp_path, task_id="TASK-AR-631", unit_id="UNIT-TASK-AR-631-001")
    attach_claim_refs(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", claim_path)
    write_claim_pointer(tmp_path, "TASK-AR-631", claim_path)
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "claim:task-invalid-lifecycle:CLAIM-TEST-001:unknown" for f in findings)
    assert any(f.subject == "claim:unit-invalid-lifecycle:CLAIM-TEST-001:unknown" for f in findings)


def test_active_worker_claim_accepts_normalized_korean_lifecycle_aliases(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS", status="진행중")
    write_unit(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", status="차단됨")
    path = write_claim(tmp_path, task_id="TASK-AR-631", unit_id="UNIT-TASK-AR-631-001")
    attach_claim_refs(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", path)
    write_claim_pointer(tmp_path, "TASK-AR-631", path)
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert not [f for f in findings if "invalid-lifecycle" in f.subject]


def test_linked_checkout_resolves_relative_worker_path_from_primary_checkout(tmp_path):
    gate = load_module()
    primary = tmp_path / "primary"
    subprocess.run(["git", "init", "-q", "-b", "base", str(primary)], check=True)
    subprocess.run(["git", "-C", str(primary), "config", "user.email", "tests@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(primary), "config", "user.name", "State Sync Tests"], check=True)
    subprocess.run(["git", "-C", str(primary), "commit", "--allow-empty", "-qm", "base"], check=True)
    write_task(primary, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(primary, "TASK-AR-631", "UNIT-TASK-AR-631-001")
    claim_path = "agents/runtime/task_claims/CLAIM-TEST-001.json"
    write(
        primary / claim_path,
        json.dumps({
            "schema": "agent-runtime-task-claim/v1",
            "claim_id": "CLAIM-TEST-001",
            "task_id": "TASK-AR-631",
            "task_set_id": "TASKSET-AR-GOVERNANCE-OPS",
            "unit_id": "UNIT-TASK-AR-631-001",
            "agent_role": "lead-engineer",
            "agent_instance_id": "worker-test",
            "status": "claimed",
            "expires_at": AR655_FIXTURE_EXPIRY,
            "lease": {"expires_at": AR655_FIXTURE_EXPIRY},
            "worktree_path": ".worktrees/TASK-AR-631",
            "branch": "worker",
        }),
    )
    attach_claim_refs(primary, "TASK-AR-631", "UNIT-TASK-AR-631-001", claim_path)
    write_claim_pointer(primary, "TASK-AR-631", claim_path)
    write(primary / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(primary / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(primary / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    subprocess.run(["git", "-C", str(primary), "add", "."], check=True)
    subprocess.run(["git", "-C", str(primary), "commit", "-qm", "fixture state"], check=True)
    worker = primary / ".worktrees" / "TASK-AR-631"
    reviewer = tmp_path / "reviewer"
    subprocess.run(["git", "-C", str(primary), "worktree", "add", "-q", "-b", "worker", str(worker)], check=True)
    subprocess.run(["git", "-C", str(primary), "worktree", "add", "-q", "-b", "reviewer", str(reviewer)], check=True)

    findings = gate.analyze(reviewer)

    assert not any(f.subject == "claim:invalid-worktree:CLAIM-TEST-001" for f in findings)
    assert not any(f.subject == "claim:branch-mismatch:CLAIM-TEST-001" for f in findings)
    assert not [f for f in findings if f.severity == "block"]


def test_active_worker_claim_targeting_primary_checkout_blocks_with_portable_git_detection(tmp_path):
    gate = load_module()
    primary = tmp_path / "primary"
    subprocess.run(["git", "init", "-q", "-b", "base", str(primary)], check=True)
    subprocess.run(["git", "-C", str(primary), "config", "user.email", "tests@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(primary), "config", "user.name", "State Sync Tests"], check=True)
    subprocess.run(["git", "-C", str(primary), "commit", "--allow-empty", "-qm", "base"], check=True)
    write_task(primary, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(primary, "TASK-AR-631", "UNIT-TASK-AR-631-001")
    claim_path = "agents/runtime/task_claims/CLAIM-TEST-001.json"
    write(
        primary / claim_path,
        json.dumps({
            "schema": "agent-runtime-task-claim/v1",
            "claim_id": "CLAIM-TEST-001",
            "task_id": "TASK-AR-631",
            "task_set_id": "TASKSET-AR-GOVERNANCE-OPS",
            "unit_id": "UNIT-TASK-AR-631-001",
            "agent_role": "lead-engineer",
            "agent_instance_id": "worker-test",
            "status": "claimed",
            "expires_at": AR655_FIXTURE_EXPIRY,
            "lease": {"expires_at": AR655_FIXTURE_EXPIRY},
            "worktree_path": ".",
            "branch": "base",
        }),
    )
    attach_claim_refs(primary, "TASK-AR-631", "UNIT-TASK-AR-631-001", claim_path)
    write_claim_pointer(primary, "TASK-AR-631", claim_path)
    write(primary / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(primary / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(primary / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(primary)

    assert any(f.subject == "claim:main-worktree:CLAIM-TEST-001" for f in findings)
    assert not any(f.subject == "claim:branch-mismatch:CLAIM-TEST-001" for f in findings)


def test_two_active_workers_can_share_one_primary_pointer_when_both_are_projected(tmp_path):
    gate = load_module()
    primary = ("TASK-AR-631", "UNIT-TASK-AR-631-001", "TASKSET-AR-GOVERNANCE-OPS", "CLAIM-TEST-001", "worker-test")
    secondary = ("TASK-AR-632", "UNIT-TASK-AR-632-001", "TASKSET-AR-SECONDARY", "CLAIM-TEST-002", "worker-test-2")
    claims = []
    for task_id, unit_id, taskset_id, claim_id, agent_id in (primary, secondary):
        write_task(tmp_path, task_id, taskset_id)
        write_unit(tmp_path, task_id, unit_id, task_set_id=taskset_id)
        path = write_claim(
            tmp_path,
            task_id=task_id,
            unit_id=unit_id,
            task_set_id=taskset_id,
            claim_id=claim_id,
            agent_instance_id=agent_id,
        )
        attach_claim_refs(tmp_path, task_id, unit_id, path)
        claims.append({"claim_id": claim_id, "agent_instance_id": agent_id, "path": path})
    write_multi_claim_pointer(tmp_path, task_set_id=primary[2], primary_task=primary[0], claims=claims)
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert not [finding for finding in findings if finding.severity == "block"]


def test_active_worker_with_no_pointer_taskset_still_validates_and_blocks(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001")
    path = write_claim(tmp_path, task_id="TASK-AR-631", unit_id="UNIT-TASK-AR-631-001")
    attach_claim_refs(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", path)
    write(tmp_path / "agents/project/NEXT-SESSION-POINTER.yml", "resume:\n  active_task: none\n")
    write(tmp_path / "BACKLOG-BOARD.md", "# Board\n")
    write(tmp_path / "BACKLOG.md", "# Backlog\n")
    write(tmp_path / "STATUS.md", "# Status\n")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "pointer:primary-worker-missing-taskset" for f in findings)
    assert any(f.subject == "claim:pointer-missing-active-ref:CLAIM-TEST-001" for f in findings)


def test_active_worker_with_pointer_task_none_blocks(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001")
    path = write_claim(tmp_path, task_id="TASK-AR-631", unit_id="UNIT-TASK-AR-631-001")
    attach_claim_refs(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", path)
    write_multi_claim_pointer(
        tmp_path,
        task_set_id="TASKSET-AR-GOVERNANCE-OPS",
        primary_task="none",
        claims=[{"claim_id": "CLAIM-TEST-001", "agent_instance_id": "worker-test", "path": path}],
    )
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "pointer:primary-worker-missing-task" for f in findings)


def test_verified_current_work_without_claim_or_recovery_blocks(tmp_path):
    gate = load_module()
    task_id = "TASK-AR-631"
    write_task(tmp_path, task_id, "TASKSET-AR-GOVERNANCE-OPS", status="review", verified=True)
    write_unit(tmp_path, task_id, "UNIT-TASK-AR-631-001", verified=True)
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "none")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "verified-work:missing-lifecycle:TASK-AR-631" for f in findings)


def test_recovered_without_claim_requires_existing_independent_evidence_and_watches(tmp_path):
    gate = load_module()
    task_id = "TASK-AR-631"
    recovery = """recovered_without_claim: true
recovery_reason: Historical W2 claim is absent; durable W4a and W4b evidence exists.
recovered_at: 2026-07-28T16:30:00+09:00
recovered_by: independent-auditor
recovery_independent_evidence_refs:
  - reviews/W4B-TEST.md
"""
    write(tmp_path / "reviews/W4B-TEST.md", "# independent W4b\n")
    write_task(tmp_path, task_id, "TASKSET-AR-GOVERNANCE-OPS", status="review", verified=True)
    task_path = tmp_path / f"agents/lead_engineer/tasks/{task_id}.md"
    task_path.write_text(task_path.read_text(encoding="utf-8").replace("---\n", "---\n" + recovery, 1), encoding="utf-8")
    write_unit(tmp_path, task_id, "UNIT-TASK-AR-631-001", verified=True, recovery=recovery)
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "none")

    findings = gate.analyze(tmp_path)

    assert not [f for f in findings if f.severity == "block"]
    assert any(f.subject == "recovery:without-claim:TASK-AR-631" for f in findings)


def test_recovery_with_a_missing_independent_evidence_ref_blocks(tmp_path):
    gate = load_module()
    recovery = """recovered_without_claim: true
recovery_reason: Historical claim absent.
recovered_at: 2026-07-28T16:30:00+09:00
recovered_by: independent-auditor
recovery_independent_evidence_refs:
  - reviews/W4B-EXISTS.md
  - reviews/W4B-MISSING.md
"""
    write(tmp_path / "reviews/W4B-EXISTS.md", "# evidence\n")
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS", status="review", verified=True)
    task = tmp_path / "agents/lead_engineer/tasks/TASK-AR-631.md"
    task.write_text(task.read_text(encoding="utf-8").replace("---\n", "---\n" + recovery, 1), encoding="utf-8")
    write_unit(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", verified=True, recovery=recovery)
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "none")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "recovery:invalid:TASK-AR-631" and "W4B-MISSING" in f.detail for f in findings)


def test_malformed_worker_claim_cannot_use_overlay_omission_to_bypass_requirements(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001")
    claim_path = write_claim(tmp_path, task_id="TASK-AR-631", unit_id="UNIT-TASK-AR-631-001")
    payload = json.loads((tmp_path / claim_path).read_text(encoding="utf-8"))
    payload.pop("worktree_path")
    (tmp_path / claim_path).write_text(json.dumps(payload), encoding="utf-8")
    attach_claim_refs(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", claim_path)
    write_claim_pointer(tmp_path, "TASK-AR-631", claim_path)
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "claim:missing-worker-field:CLAIM-TEST-001:worktree_path" for f in findings)


def test_false_or_string_true_overlay_markers_remain_worker_claims(tmp_path):
    gate = load_module()
    for index, overlay in enumerate((False, "true"), start=1):
        task_id = f"TASK-AR-63{index}"
        unit_id = f"UNIT-TASK-AR-63{index}-001"
        claim_id = f"CLAIM-TEST-00{index}"
        write_task(tmp_path, task_id, "TASKSET-AR-GOVERNANCE-OPS")
        write_unit(tmp_path, task_id, unit_id)
        path = write_claim(tmp_path, task_id=task_id, unit_id=unit_id, claim_id=claim_id, overlay=overlay)
        payload = json.loads((tmp_path / path).read_text(encoding="utf-8"))
        payload.pop("worktree_path")
        (tmp_path / path).write_text(json.dumps(payload), encoding="utf-8")
        attach_claim_refs(tmp_path, task_id, unit_id, path)
    write_multi_claim_pointer(
        tmp_path,
        task_set_id="TASKSET-AR-GOVERNANCE-OPS",
        primary_task="TASK-AR-631",
        claims=[
            {"claim_id": "CLAIM-TEST-001", "agent_instance_id": "worker-test", "path": "agents/runtime/task_claims/CLAIM-TEST-001.json"},
            {"claim_id": "CLAIM-TEST-002", "agent_instance_id": "worker-test", "path": "agents/runtime/task_claims/CLAIM-TEST-002.json"},
        ],
    )
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert {f.subject for f in findings if "missing-worker-field" in f.subject} == {
        "claim:missing-worker-field:CLAIM-TEST-001:worktree_path",
        "claim:missing-worker-field:CLAIM-TEST-002:worktree_path",
    }


def test_matching_explicit_overlay_does_not_satisfy_verified_worker_lifecycle(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS", status="review", verified=True)
    write_unit(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", verified=True)
    write_claim(
        tmp_path,
        task_id="TASK-AR-631",
        unit_id="UNIT-TASK-AR-631-001",
        overlay=True,
    )
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "none")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "verified-work:missing-lifecycle:TASK-AR-631" for f in findings)


def test_active_worker_claim_blocks_unit_taskset_mismatch(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(
        tmp_path,
        "TASK-AR-631",
        "UNIT-TASK-AR-631-001",
        task_set_id="TASKSET-AR-OTHER",
    )
    claim_path = write_claim(tmp_path, task_id="TASK-AR-631", unit_id="UNIT-TASK-AR-631-001")
    attach_claim_refs(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", claim_path)
    write_claim_pointer(tmp_path, "TASK-AR-631", claim_path)
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "claim:unit-taskset-mismatch:CLAIM-TEST-001" for f in findings)


def test_worker_claim_branch_must_match_the_real_worktree_branch(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS")
    write_unit(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001")
    claim_path = write_claim(tmp_path, task_id="TASK-AR-631", unit_id="UNIT-TASK-AR-631-001")
    payload = json.loads((tmp_path / claim_path).read_text(encoding="utf-8"))
    payload["branch"] = "codex/not-checked-out"
    (tmp_path / claim_path).write_text(json.dumps(payload), encoding="utf-8")
    attach_claim_refs(tmp_path, "TASK-AR-631", "UNIT-TASK-AR-631-001", claim_path)
    write_claim_pointer(tmp_path, "TASK-AR-631", claim_path)
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert any(f.subject == "claim:branch-mismatch:CLAIM-TEST-001" for f in findings)


def test_explicit_overlay_with_synthetic_review_scope_is_exempt_from_worker_tuple(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-631", "TASKSET-AR-GOVERNANCE-OPS")
    claim_path = write_claim(tmp_path, task_id="TASK-OVERLAY-SCOUT", unit_id="", overlay=True)
    payload = json.loads((tmp_path / claim_path).read_text(encoding="utf-8"))
    payload.pop("worktree_path")
    payload.pop("branch")
    (tmp_path / claim_path).write_text(json.dumps(payload), encoding="utf-8")
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "none")
    write(tmp_path / "BACKLOG-BOARD.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "BACKLOG.md", "TASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "TASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert not [finding for finding in findings if finding.severity == "block"]
