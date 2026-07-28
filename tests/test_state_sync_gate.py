from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "state_sync_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("state_sync_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


def write_unit(root: Path, task_id: str, unit_id: str, *, verified: bool = False, recovery: str = "") -> None:
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
task_set_id: TASKSET-AR-GOVERNANCE-OPS
status: review
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


def write_claim(root: Path, *, task_id: str, unit_id: str, overlay: object | None = None) -> str:
    claim_id = "CLAIM-TEST-001"
    claim_path = f"agents/runtime/task_claims/{claim_id}.json"
    worktree = root / ".worktrees" / task_id
    repository = root / ".fixture-repository"
    subprocess.run(["git", "init", "-q", "-b", "base", str(repository)], check=True)
    subprocess.run(["git", "-C", str(repository), "config", "user.email", "tests@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repository), "config", "user.name", "State Sync Tests"], check=True)
    subprocess.run(["git", "-C", str(repository), "commit", "--allow-empty", "-qm", "fixture"], check=True)
    subprocess.run(["git", "-C", str(repository), "worktree", "add", "-q", "-b", "worker", str(worktree)], check=True)
    claim = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": task_id,
        "task_set_id": "TASKSET-AR-GOVERNANCE-OPS",
        "unit_id": unit_id,
        "agent_role": "lead-engineer",
        "agent_instance_id": "worker-test",
        "status": "claimed",
        "worktree_path": f".worktrees/{task_id}",
        "branch": "worker",
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
