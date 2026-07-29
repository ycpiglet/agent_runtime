"""Tests for claim_guard — commit claim artifacts so a concurrent reset/clean can't lose them.

Regression target (incident 2026-06-12): a freshly created claim JSON was left
*untracked*, so a sibling session's ``git reset --hard && git clean -fd`` erased it
and the claim had to be recreated. Committing the claim the instant it is written
makes it part of HEAD, which survives both reset and clean.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import claim_guard  # noqa: E402


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)


def _init_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed")
    return tmp_path


def _write_claim(root: Path, name: str = "CLAIM-test.json") -> Path:
    claims = root / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    path = claims / name
    path.write_text('{"claim_id": "CLAIM-test"}\n', encoding="utf-8")
    return path


def _write_runtime_claim(root: Path) -> tuple[Path, Path, Path]:
    claims = root / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    claim = claims / "CLAIM-runtime-hook.json"
    handoff = claims / "CLAIM-runtime-hook.handoff.md"
    log = claims / "CLAIM-runtime-hook.log.md"
    handoff.write_text("# Handoff\n\n- Next Steps: verify\n", encoding="utf-8")
    log.write_text("# Claim Log\n\n- transaction test\n", encoding="utf-8")
    claim.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-runtime-hook",
                "task_id": "TASK-AR-648",
                "task_set_id": "TASKSET-AR-V080-ADOPTION-ENFORCEMENT",
                "agent_role": "orchestrator",
                "team_id": "evaluation-office",
                "agent_instance_id": "claim-hook-test",
                "display_name": "claim-hook@test",
                "callsite_id": "pytest:claim-hook",
                "pane_id": "pytest:claim-hook",
                "mode": "orchestrator",
                "status": "claimed",
                "phase": "claim-created",
                "progress_pct": 0,
                "status_text": "Verify explicit claim commit transaction",
                "worktree_path": ".",
                "branch": "test/claim-hook",
                "claimed_at": "2026-07-29T19:00:00+09:00",
                "last_heartbeat": "2026-07-29T19:00:00+09:00",
                "handoff_path": handoff.relative_to(root).as_posix(),
                "log_path": log.relative_to(root).as_posix(),
                "persistence": {
                    "mode": "scm_commit",
                    "scm_commit_authorized": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return claim, handoff, log


def test_is_git_repo(tmp_path):
    assert claim_guard.is_git_repo(tmp_path) is False
    _init_repo(tmp_path)
    assert claim_guard.is_git_repo(tmp_path) is True


def test_commit_claim_artifacts_tracks_the_file(tmp_path):
    _init_repo(tmp_path)
    claim = _write_claim(tmp_path)
    result = claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")
    assert result["ok"] is True
    assert result["committed"] is True
    tracked = _git(tmp_path, "ls-files", "agents/runtime/task_claims").stdout
    assert "CLAIM-test.json" in tracked


def test_committed_claim_survives_reset_and_clean(tmp_path):
    """The actual incident regression: committed claim must outlive reset+clean."""
    _init_repo(tmp_path)
    claim = _write_claim(tmp_path)
    claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")

    # A sibling session does the destructive cleanup that caused the 2026-06-12 loss.
    _git(tmp_path, "reset", "--hard", "HEAD")
    _git(tmp_path, "clean", "-fd")

    assert claim.exists(), "committed claim was lost by reset+clean"


def test_uncommitted_claim_is_lost_by_clean(tmp_path):
    """Control: prove the hazard is real when the guard does NOT run."""
    _init_repo(tmp_path)
    claim = _write_claim(tmp_path, "CLAIM-orphan.json")
    _git(tmp_path, "clean", "-fd")
    assert not claim.exists()


def test_not_a_git_repo_is_reported_not_raised(tmp_path):
    claim = _write_claim(tmp_path)
    result = claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")
    assert result["ok"] is False
    assert result["reason"] == "not-a-git-repo"
    assert result["committed"] is False


def test_commit_is_idempotent(tmp_path):
    _init_repo(tmp_path)
    claim = _write_claim(tmp_path)
    claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")
    # Second call with no new changes must not error.
    again = claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")
    assert again["ok"] is True
    assert again["committed"] is False


def test_sweep_commits_orphan_claims(tmp_path):
    _init_repo(tmp_path)
    _write_claim(tmp_path, "CLAIM-a.json")
    _write_claim(tmp_path, "CLAIM-b.json")
    result = claim_guard.sweep(tmp_path, apply=True)
    assert result["committed"] is True
    assert len(result["paths"]) == 2
    tracked = _git(tmp_path, "ls-files", "agents/runtime/task_claims").stdout
    assert "CLAIM-a.json" in tracked and "CLAIM-b.json" in tracked


def test_sweep_dry_run_does_not_commit(tmp_path):
    _init_repo(tmp_path)
    _write_claim(tmp_path, "CLAIM-a.json")
    result = claim_guard.sweep(tmp_path, apply=False)
    assert result["committed"] is False
    tracked = _git(tmp_path, "ls-files", "agents/runtime/task_claims").stdout
    assert "CLAIM-a.json" not in tracked


def test_commit_only_touches_claim_paths(tmp_path):
    """A pre-existing unrelated working-tree change must remain uncommitted."""
    _init_repo(tmp_path)
    (tmp_path / "other.txt").write_text("dirty\n", encoding="utf-8")
    claim = _write_claim(tmp_path)
    claim_guard.commit_claim_artifacts(tmp_path, claim, claim_id="CLAIM-test")
    status = _git(tmp_path, "status", "--porcelain").stdout
    assert "other.txt" in status  # still uncommitted / untracked


def test_runtime_precommit_allows_exact_explicit_claim_transaction(tmp_path):
    """The Runtime gate must not reject the claim-only commit it is guarding."""
    _init_repo(tmp_path)
    (tmp_path / "STATUS.md").write_text(
        "## Next Steps\n- finish the claim transaction\n",
        encoding="utf-8",
    )
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "parallel_worktree_gate.py").write_text(
        (ROOT / "scripts" / "parallel_worktree_gate.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    hooks = tmp_path / ".githooks"
    hooks.mkdir()
    hook = hooks / "pre-commit"
    hook.write_text(
        "#!/bin/sh\nexec python3 scripts/parallel_worktree_gate.py --check\n",
        encoding="utf-8",
    )
    hook.chmod(0o755)
    _git(tmp_path, "config", "core.hooksPath", ".githooks")
    _git(tmp_path, "add", "STATUS.md", "scripts/parallel_worktree_gate.py", ".githooks/pre-commit")
    assert _git(tmp_path, "commit", "-m", "runtime hook fixture").returncode == 0

    claim, handoff, log = _write_runtime_claim(tmp_path)
    before = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    result = claim_guard.commit_claim_artifacts(
        tmp_path,
        claim,
        extra_paths=(handoff, log),
        claim_id="CLAIM-runtime-hook",
    )

    assert result["ok"] is True, result
    assert result["committed"] is True
    assert _git(tmp_path, "rev-parse", "HEAD").stdout.strip() != before
    assert "AGENT_RUNTIME_CLAIM_COMMIT_TRANSACTION" not in os.environ
    transaction_dir = Path(
        _git(tmp_path, "rev-parse", "--git-path", "agent-runtime/claim-commit").stdout.strip()
    )
    if not transaction_dir.is_absolute():
        transaction_dir = tmp_path / transaction_dir
    assert not list(transaction_dir.glob("*.json"))
