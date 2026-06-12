from __future__ import annotations

import json
from pathlib import Path

from scripts import session_baseline


def test_session_baseline_schema_has_required_fields() -> None:
    schema = json.loads(Path("schemas/session-baseline.schema.json").read_text(encoding="utf-8"))
    required = set(schema["required"])
    assert {
        "schema",
        "captured_at",
        "cwd",
        "head",
        "branch",
        "status_fingerprint",
        "stash_count",
        "worktrees",
        "active_codex_branches",
    } <= required


def test_capture_baseline_uses_git_state(tmp_path: Path, monkeypatch) -> None:
    outputs = {
        ("git", "rev-parse", "--short", "HEAD"): "abc1234\n",
        ("git", "branch", "--show-current"): "main\n",
        ("git", "status", "--porcelain=v1"): " M BACKLOG.md\n",
        ("git", "stash", "list", "--format=%H"): "111\n222\n",
        ("git", "worktree", "list", "--porcelain"): "worktree C:/repo\nbranch refs/heads/main\n",
        ("git", "branch", "--list", "codex/*", "claude/*"): "  codex/task\n  claude/task-ar-508\n",
    }

    def fake_run(args: list[str], cwd: Path) -> str:
        return outputs[tuple(args)]

    monkeypatch.setattr(session_baseline, "run_git", fake_run)
    data = session_baseline.capture(tmp_path)

    assert data["schema"] == "agent-runtime-session-baseline/v1"
    assert data["head"] == "abc1234"
    assert data["branch"] == "main"
    assert data["stash_count"] == 2
    assert data["active_codex_branches"] == ["codex/task", "claude/task-ar-508"]
    assert data["status_fingerprint"]
    assert data["worktrees"][0]["path"] == "C:/repo"


def test_agent_branch_patterns_cover_codex_and_claude() -> None:
    from scripts.session_baseline import AGENT_BRANCH_PATTERNS, AGENT_BRANCH_PREFIXES

    assert "codex/" in AGENT_BRANCH_PREFIXES
    assert "claude/" in AGENT_BRANCH_PREFIXES
    assert "codex/*" in AGENT_BRANCH_PATTERNS
    assert "claude/*" in AGENT_BRANCH_PATTERNS
