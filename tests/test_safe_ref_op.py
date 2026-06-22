"""Tests for safe_ref_op.py — safe destructive-ref wrapper.

Guard purpose: prevent silent commit loss when a concurrent agent has advanced a
branch tip between the time the SHA was cached and the time a destructive operation
(branch delete, reset --hard, push --delete) is actually executed.

RETRO background: a `git branch -D` on a stale cached tip deleted a concurrent
agent's unmerged commits (COMPOUND-2026-06-22).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "safe_ref_op.py"


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _init_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with an initial commit and return its path."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    _git("add", "README.md", cwd=repo)
    _git("commit", "-m", "init", cwd=repo)
    return repo


def _branch_sha(repo: Path, branch: str) -> str:
    out = _git("rev-parse", branch, cwd=repo)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def _branch_exists(repo: Path, branch: str) -> bool:
    out = _git("branch", "--list", branch, cwd=repo)
    return bool(out.stdout.strip())


# ---------------------------------------------------------------------------
# delete-branch subcommand
# ---------------------------------------------------------------------------


def test_delete_branch_with_correct_sha_succeeds(tmp_path):
    """delete-branch with a matching --expect-sha must delete the branch and exit 0."""
    repo = _init_repo(tmp_path)
    # Create a feature branch off main
    _git("checkout", "-b", "feature/x", cwd=repo)
    (repo / "f.txt").write_text("hello\n", encoding="utf-8")
    _git("add", "f.txt", cwd=repo)
    _git("commit", "-m", "add f", cwd=repo)
    sha = _branch_sha(repo, "feature/x")
    _git("checkout", "-", cwd=repo)  # go back to previous branch

    result = _run(["delete-branch", "feature/x", "--expect-sha", sha], cwd=repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not _branch_exists(repo, "feature/x")


def test_delete_branch_with_stale_sha_is_refused(tmp_path):
    """delete-branch with a stale --expect-sha must refuse (exit 1) and leave branch intact."""
    repo = _init_repo(tmp_path)
    _git("checkout", "-b", "feature/y", cwd=repo)
    (repo / "f1.txt").write_text("v1\n", encoding="utf-8")
    _git("add", "f1.txt", cwd=repo)
    _git("commit", "-m", "v1", cwd=repo)
    old_sha = _branch_sha(repo, "feature/y")

    # Advance the branch (simulates a concurrent agent pushing another commit)
    (repo / "f2.txt").write_text("v2\n", encoding="utf-8")
    _git("add", "f2.txt", cwd=repo)
    _git("commit", "-m", "v2", cwd=repo)

    _git("checkout", "-", cwd=repo)

    result = _run(["delete-branch", "feature/y", "--expect-sha", old_sha], cwd=repo)
    assert result.returncode == 1, result.stdout + result.stderr
    # Branch must still be present — no data loss
    assert _branch_exists(repo, "feature/y")
    # Message should mention the mismatch
    combined = result.stdout + result.stderr
    assert "mismatch" in combined.lower() or "stale" in combined.lower() or "refuse" in combined.lower()


def test_delete_branch_force_flag_overrides_sha_check(tmp_path):
    """--force must skip the SHA check and delete regardless of tip."""
    repo = _init_repo(tmp_path)
    _git("checkout", "-b", "feature/z", cwd=repo)
    (repo / "g.txt").write_text("x\n", encoding="utf-8")
    _git("add", "g.txt", cwd=repo)
    _git("commit", "-m", "g", cwd=repo)
    old_sha = _branch_sha(repo, "feature/z")

    # Advance the branch
    (repo / "g2.txt").write_text("y\n", encoding="utf-8")
    _git("add", "g2.txt", cwd=repo)
    _git("commit", "-m", "g2", cwd=repo)

    _git("checkout", "-", cwd=repo)

    result = _run(["delete-branch", "feature/z", "--expect-sha", old_sha, "--force"], cwd=repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not _branch_exists(repo, "feature/z")


# ---------------------------------------------------------------------------
# verify-tip subcommand
# ---------------------------------------------------------------------------


def test_verify_tip_matching_sha_exits_0(tmp_path):
    """verify-tip must exit 0 when the ref tip matches --expect-sha."""
    repo = _init_repo(tmp_path)
    _git("checkout", "-b", "check-me", cwd=repo)
    sha = _branch_sha(repo, "check-me")
    _git("checkout", "-", cwd=repo)

    result = _run(["verify-tip", "check-me", "--expect-sha", sha], cwd=repo)
    assert result.returncode == 0, result.stdout + result.stderr


def test_verify_tip_stale_sha_exits_1(tmp_path):
    """verify-tip must exit 1 when the ref tip does not match --expect-sha."""
    repo = _init_repo(tmp_path)
    _git("checkout", "-b", "check-stale", cwd=repo)
    old_sha = _branch_sha(repo, "check-stale")

    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    _git("add", "new.txt", cwd=repo)
    _git("commit", "-m", "new", cwd=repo)

    _git("checkout", "-", cwd=repo)

    result = _run(["verify-tip", "check-stale", "--expect-sha", old_sha], cwd=repo)
    assert result.returncode == 1, result.stdout + result.stderr
