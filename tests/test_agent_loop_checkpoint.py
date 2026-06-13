"""Tests for agent_loop dirty-worktree checkpoint (opt-in deadlock guardrail)."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_loop  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not available")


def _run(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


@pytest.fixture
def git_repo(tmp_path):
    _run(tmp_path, "init")
    _run(tmp_path, "config", "user.email", "t@example.com")
    _run(tmp_path, "config", "user.name", "Tester")
    _run(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    _run(tmp_path, "add", "-A")
    _run(tmp_path, "commit", "-m", "init")
    _run(tmp_path, "checkout", "-b", "feature/x")
    return tmp_path


# --- real git helpers ---

def test_current_branch_reports_feature_branch(git_repo):
    assert agent_loop.current_branch(git_repo) == "feature/x"


def test_checkpoint_commit_saves_dirty_worktree(git_repo):
    (git_repo / "a.txt").write_text("changed", encoding="utf-8")
    (git_repo / "new.txt").write_text("added", encoding="utf-8")
    committed, detail = agent_loop.git_checkpoint_commit(git_repo, "wip: test checkpoint")
    assert committed, detail
    assert _run(git_repo, "status", "--porcelain").stdout.strip() == ""  # clean now


def test_checkpoint_commit_nothing_to_commit_returns_false(git_repo):
    committed, _detail = agent_loop.git_checkpoint_commit(git_repo, "wip: nothing")
    assert committed is False


# --- maybe_checkpoint_dirty policy (isolated from REPO_ROOT/git) ---

def test_maybe_checkpoint_skips_protected_branch(monkeypatch):
    calls = []
    monkeypatch.setattr(agent_loop, "is_worktree_dirty", lambda: (True, "dirty"))
    monkeypatch.setattr(agent_loop, "current_branch", lambda root=None: "main")
    monkeypatch.setattr(agent_loop, "git_checkpoint_commit",
                        lambda root, msg: (calls.append(msg), (True, "x"))[1])
    monkeypatch.setattr(agent_loop, "_record_stop_event", lambda *a, **k: None)
    cfg = agent_loop.LoopConfig(mode="plan", checkpoint_dirty=True)
    assert agent_loop.maybe_checkpoint_dirty(cfg, 1) is None
    assert calls == []  # never auto-commits on a protected branch


def test_maybe_checkpoint_commits_on_feature_branch(monkeypatch):
    monkeypatch.setattr(agent_loop, "is_worktree_dirty", lambda: (True, "dirty"))
    monkeypatch.setattr(agent_loop, "current_branch", lambda root=None: "feature/x")
    monkeypatch.setattr(agent_loop, "git_checkpoint_commit", lambda root, msg: (True, "abc123"))
    monkeypatch.setattr(agent_loop, "append_event", lambda *a, **k: None)
    monkeypatch.setattr(agent_loop, "_record_stop_event", lambda *a, **k: None)
    cfg = agent_loop.LoopConfig(mode="build", checkpoint_dirty=True, goal="ship")
    assert agent_loop.maybe_checkpoint_dirty(cfg, 2) == "abc123"


def test_maybe_checkpoint_noop_when_clean(monkeypatch):
    monkeypatch.setattr(agent_loop, "is_worktree_dirty", lambda: (False, "clean"))
    cfg = agent_loop.LoopConfig(mode="plan", checkpoint_dirty=True)
    assert agent_loop.maybe_checkpoint_dirty(cfg, 1) is None


# --- config + CLI plumbing ---

def test_config_default_off_and_cli_flag():
    assert agent_loop.LoopConfig(mode="plan").checkpoint_dirty is False
    args = agent_loop.build_parser().parse_args(["--mode", "build", "--checkpoint-dirty"])
    assert args.checkpoint_dirty is True
    args2 = agent_loop.build_parser().parse_args(["--mode", "build"])
    assert args2.checkpoint_dirty is False
