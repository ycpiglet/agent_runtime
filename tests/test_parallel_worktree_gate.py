from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "parallel_worktree_gate.py"


def _run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_claim(root: Path, name: str, **overrides: object) -> Path:
    claim_dir = root / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": name,
        "task_id": "TASK-AR-246",
        "task_set_id": "TASKSET-AR-PANE-PROGRESS",
        "agent_role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "agent_instance_id": "lead-engineer-A",
        "display_name": "lead_engineer@design-01",
        "callsite_id": "terminal-1",
        "pane_id": "terminal-1",
        "status": "working",
        "phase": "implement",
        "progress_pct": 10,
        "status_text": "Implementing task claim support",
        "worktree_path": ".worktrees/TASK-AR-246",
        "branch": "codex/task-ar-246-parallel-runtime",
        "claimed_at": "2026-06-10T12:00:00+09:00",
        "last_heartbeat": "2026-06-10T12:05:00+09:00",
        "handoff_path": "STATUS.md",
        "log_path": "reviews/REVIEW-2026-06-10-agent-runtime-parallel-session-protocol.md",
    }
    payload.update(overrides)
    worktree_value = str(payload.get("worktree_path") or "")
    if worktree_value and worktree_value != "." and not overrides.get("skip_worktree_marker"):
        worktree = root / worktree_value
        worktree.mkdir(parents=True, exist_ok=True)
        (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")
    path = claim_dir / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_gate_passes_when_no_parallel_task_claims_exist(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")

    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "parallel-worktree-gate: pass" in result.stdout
    assert "findings=0" in result.stdout


def test_gate_passes_fresh_host_without_status_when_no_claims_exist(tmp_path: Path):
    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "parallel-worktree-gate: pass" in result.stdout


def test_gate_blocks_duplicate_active_claims_for_one_task(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1")
    _write_claim(
        tmp_path,
        "CLAIM-2",
        claim_id="CLAIM-2",
        agent_instance_id="lead-engineer-B",
        callsite_id="terminal-2",
        worktree_path=".worktrees/TASK-AR-246-B",
        branch="codex/task-ar-246-parallel-runtime-b",
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:duplicate-active-task:TASK-AR-246" in result.stdout


def test_gate_allows_same_role_with_distinct_instances_and_worktrees(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    review = tmp_path / "reviews" / "REVIEW-2026-06-10-agent-runtime-parallel-session-protocol.md"
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text("parallel session handoff log\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", task_id="TASK-AR-246")
    _write_claim(
        tmp_path,
        "CLAIM-2",
        claim_id="CLAIM-2",
        task_id="TASK-AR-247",
        task_set_id="TASKSET-AR-QUALITY-LOOP",
        agent_instance_id="lead-engineer-B",
        callsite_id="terminal-2",
        worktree_path=".worktrees/TASK-AR-247",
        branch="codex/task-ar-247-other",
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "findings=0" in result.stdout


def test_gate_blocks_worker_claim_in_main_checkout(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", worktree_path=".")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:main-checkout-worker" in result.stdout


def test_gate_blocks_missing_worktree_for_active_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", skip_worktree_marker=True)

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:worktree-path-missing" in result.stdout


def test_gate_blocks_non_git_worktree_for_active_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    worktree = tmp_path / ".worktrees" / "TASK-AR-246"
    worktree.mkdir(parents=True, exist_ok=True)
    _write_claim(tmp_path, "CLAIM-1", skip_worktree_marker=True)

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:worktree-not-git-worktree" in result.stdout


def test_gate_blocks_missing_handoff_pointer_for_active_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Current State\n- active\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", handoff_path="")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:missing-handoff-path" in result.stdout
    assert "continuity:status-handoff-missing" in result.stdout


def test_gate_blocks_missing_display_name_for_active_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", display_name="")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:missing-display-name" in result.stdout


def test_gate_blocks_duplicate_active_claims_for_one_task_set(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", task_id="TASK-AR-205", worktree_path=".worktrees/TASK-AR-205")
    _write_claim(
        tmp_path,
        "CLAIM-2",
        claim_id="CLAIM-2",
        task_id="TASK-AR-206",
        agent_instance_id="qa-B",
        callsite_id="terminal-2",
        worktree_path=".worktrees/TASK-AR-206",
        branch="codex/task-ar-206-quality-loop",
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:duplicate-active-task-set:TASKSET-AR-PANE-PROGRESS" in result.stdout


def test_gate_blocks_missing_taskset_progress_fields_for_active_claim(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_claim(tmp_path, "CLAIM-1", task_set_id="", status_text="")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "task-claim:missing-task-set-id" in result.stdout
    assert "task-claim:missing-status-text" in result.stdout


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _init_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "gate-test@example.com")
    _git(repo, "config", "user.name", "Gate Test")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    review = repo / "reviews" / "REVIEW-2026-06-10-agent-runtime-parallel-session-protocol.md"
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text("parallel session handoff log\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "init")
    return repo


def _add_task_worktree(repo: Path, name: str = "TASK-AR-900", branch: str = "claude/task-ar-900-demo") -> Path:
    path = repo / ".worktrees" / name
    _git(repo, "worktree", "add", "-b", branch, str(path), "main")
    return path


def test_gate_watches_claimless_clean_task_worktree(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    _add_task_worktree(repo)

    result = _run_gate(repo)

    assert result.returncode == 0, result.stdout
    assert "worktree:missing-claim" in result.stdout
    assert "worktree:missing-claim-dirty" not in result.stdout
    assert "worktree:missing-claim-ahead" not in result.stdout
    assert "block=0" in result.stdout
    assert "- watch" in result.stdout


def test_gate_blocks_claimless_dirty_task_worktree(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(repo)
    (worktree / "wip.txt").write_text("uncommitted work without a claim\n", encoding="utf-8")

    result = _run_gate(repo)

    assert result.returncode == 1
    assert "worktree:missing-claim-dirty" in result.stdout
    assert "- block" in result.stdout


def test_gate_blocks_claimless_ahead_task_worktree(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(repo)
    (worktree / "done.txt").write_text("committed work without a claim\n", encoding="utf-8")
    _git(worktree, "add", "done.txt")
    _git(worktree, "commit", "-m", "work without claim")

    result = _run_gate(repo)

    assert result.returncode == 1
    assert "worktree:missing-claim-ahead" in result.stdout


def test_gate_passes_claimed_task_worktree(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    _add_task_worktree(repo, name="TASK-AR-900", branch="claude/task-ar-900-demo")
    _write_claim(
        repo,
        "CLAIM-1",
        task_id="TASK-AR-900",
        worktree_path=".worktrees/TASK-AR-900",
        branch="claude/task-ar-900-demo",
        skip_worktree_marker=True,
    )
    _git(repo, "add", "agents")
    _git(repo, "commit", "-m", "open claim")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stdout
    assert "worktree:missing-claim" not in result.stdout
    assert "findings=0" in result.stdout


def test_gate_blocks_untracked_claim_file(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    _write_claim(repo, "CLAIM-1")

    result = _run_gate(repo)

    assert result.returncode == 1
    assert "task-claim:claim-not-committed" in result.stdout
    assert "2026-06-12" in result.stdout


def test_gate_exempts_spike_marker_worktree_with_watch_note(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(repo)
    (worktree / "SPIKE").write_text("experimental spike worktree\n", encoding="utf-8")
    (worktree / "wip.txt").write_text("spike experiment in flight\n", encoding="utf-8")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stdout
    assert "worktree:spike-exempt" in result.stdout
    assert "worktree:missing-claim" not in result.stdout
    assert "block=0" in result.stdout


def test_gate_exempts_spike_tagged_claim_worktree_with_watch_note(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(repo, name="TASK-AR-901", branch="claude/task-ar-901-spike")
    (worktree / "wip.txt").write_text("spike experiment in flight\n", encoding="utf-8")
    _write_claim(
        repo,
        "CLAIM-1",
        task_id="TASK-AR-901",
        worktree_path=".worktrees/TASK-AR-901",
        branch="claude/task-ar-901-spike",
        status="released",
        tags=["spike"],
        skip_worktree_marker=True,
    )
    _git(repo, "add", "agents")
    _git(repo, "commit", "-m", "spike claim")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stdout
    assert "worktree:spike-exempt" in result.stdout
    assert "worktree:missing-claim" not in result.stdout


def test_gate_caps_missing_claim_at_watch_when_run_from_linked_worktree(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree = _add_task_worktree(repo)
    (worktree / "wip.txt").write_text("work whose claim may postdate this snapshot\n", encoding="utf-8")

    result = _run_gate(worktree)

    assert result.returncode == 0, result.stdout
    assert "worktree:missing-claim" in result.stdout
    assert "block=0" in result.stdout
    assert "snapshot may predate the claim commit" in result.stdout


def test_gate_resolves_claim_worktree_path_against_primary_checkout(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    _write_claim(
        repo,
        "CLAIM-1",
        task_id="TASK-AR-900",
        worktree_path=".worktrees/TASK-AR-900",
        branch="claude/task-ar-900-demo",
        skip_worktree_marker=True,
    )
    _git(repo, "add", "agents")
    _git(repo, "commit", "-m", "open claim before worktree")
    worktree = _add_task_worktree(repo, name="TASK-AR-900", branch="claude/task-ar-900-demo")

    result = _run_gate(worktree)

    assert result.returncode == 0, result.stdout
    assert "task-claim:worktree-path-missing" not in result.stdout
    assert "findings=0" in result.stdout
