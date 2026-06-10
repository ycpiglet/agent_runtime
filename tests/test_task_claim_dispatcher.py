from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "task_claim_dispatcher.py"
GATE = REPO_ROOT / "scripts" / "parallel_worktree_gate.py"


def _run_dispatcher(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_worktree(root: Path, task_id: str) -> None:
    worktree = root / ".worktrees" / task_id
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")


def test_create_claim_separates_system_identity_from_readable_display_name(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "design",
        "--tag",
        "planning",
        "--tag",
        "no-ssot-write",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "a7f3",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    claim = payload["claim"]
    assert claim["agent_role"] == "lead-engineer"
    assert claim["team_id"] == "agent-runtime-core"
    assert claim["agent_instance_id"] == "le-20260610-143012-kst-a7f3"
    assert claim["display_name"] == "lead_engineer@design-01"
    assert claim["callsite_id"] == "terminal:wt-task-ar-246:tab-01"
    assert claim["pane_id"] == "terminal:wt-task-ar-246:tab-01"
    assert claim["mode"] == "design"
    assert claim["phase"] == "claim-created"
    assert claim["progress_pct"] == 0
    assert claim["task_set_id"] == ""
    assert claim["step_index"] == 1
    assert claim["step_total"] == 6
    assert claim["status_text"] == "Claim created"
    assert claim["updated_at"] == "2026-06-10T14:30:12+09:00"
    assert claim["tags"] == ["planning", "no-ssot-write"]
    assert claim["worktree_path"] == ".worktrees/TASK-AR-246"
    assert claim["branch"] == "codex/task-ar-246-design-01"

    claim_path = tmp_path / payload["path"]
    assert claim_path.exists()
    assert (tmp_path / claim["handoff_path"]).exists()
    assert (tmp_path / claim["log_path"]).exists()

    gate = _run_gate(tmp_path)
    assert gate.returncode == 0, gate.stdout


def test_create_claim_refuses_task_that_is_already_active(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")
    first = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "design",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "a7f3",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "qa-reviewer",
        "--mode",
        "review",
        "--now",
        "2026-06-10T14:35:12+09:00",
        "--suffix",
        "b8c4",
        "--json",
    )

    assert second.returncode == 1
    assert "task already has an active claim" in (second.stderr or second.stdout)
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == 1


def test_release_claim_requires_existing_handoff_and_log_files(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-246")
    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "design",
        "--now",
        "2026-06-10T14:30:12+09:00",
        "--suffix",
        "a7f3",
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    payload = json.loads(created.stdout)
    claim = payload["claim"]
    (tmp_path / claim["handoff_path"]).unlink()

    failed = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--now",
        "2026-06-10T14:45:12+09:00",
        "--json",
    )

    assert failed.returncode == 1
    assert "handoff/log pointer is missing" in (failed.stderr or failed.stdout)
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "claimed"


def test_create_claim_accepts_taskset_progress_fields(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-248")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-248",
        "--task-set-id",
        "TASKSET-AR-PANE-PROGRESS",
        "--agent-role",
        "lead-engineer",
        "--team-id",
        "agent-runtime-core",
        "--mode",
        "implement",
        "--phase",
        "implement",
        "--progress-pct",
        "48",
        "--step-index",
        "3",
        "--step-total",
        "6",
        "--status-text",
        "Rendering task-set progress in UI state",
        "--now",
        "2026-06-10T19:45:00+09:00",
        "--suffix",
        "p2",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["task_set_id"] == "TASKSET-AR-PANE-PROGRESS"
    assert claim["step_index"] == 3
    assert claim["step_total"] == 6
    assert claim["status_text"] == "Rendering task-set progress in UI state"
    assert claim["updated_at"] == "2026-06-10T19:45:00+09:00"


def test_create_claim_rejects_missing_worktree(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-246",
        "--agent-role",
        "lead-engineer",
    )

    assert result.returncode == 1
    assert "task worktree is not ready" in result.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_create_claim_refuses_duplicate_active_taskset(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-248")
    _write_worktree(tmp_path, "TASK-AR-249")
    first = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-248",
        "--task-set-id",
        "TASKSET-AR-PANE-PROGRESS",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-10T19:45:00+09:00",
        "--suffix",
        "p2",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout

    second = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--task-set-id",
        "TASKSET-AR-PANE-PROGRESS",
        "--agent-role",
        "qa-reviewer",
        "--now",
        "2026-06-10T19:46:00+09:00",
        "--suffix",
        "p3",
        "--json",
    )

    assert second.returncode == 1
    assert "task set already has an active claim" in second.stderr


def test_create_claim_rejects_invalid_progress_and_step_state(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    bad_progress = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--agent-role",
        "lead-engineer",
        "--progress-pct",
        "104",
    )
    bad_step = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--agent-role",
        "lead-engineer",
        "--step-index",
        "7",
        "--step-total",
        "6",
    )
    bad_done = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--agent-role",
        "lead-engineer",
        "--phase",
        "completed",
        "--step-index",
        "2",
        "--step-total",
        "6",
    )

    assert bad_progress.returncode == 1
    assert "progress_pct must be between 0 and 100" in bad_progress.stderr
    assert bad_step.returncode == 1
    assert "step_index must be between 1 and step_total" in bad_step.stderr
    assert bad_done.returncode == 1
    assert "completion phase requires step_index to equal step_total" in bad_done.stderr
