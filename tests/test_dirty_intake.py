from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.dirty_intake import build_plan, classify_status


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_log_only_changes_are_archive_optional() -> None:
    result = classify_status(["?? agents/runtime/hook-logs/stop-owner-governance-1.json"])

    assert result.route == "log_only"
    assert result.side_effect == "drop_allowed_after_owner_policy"


def test_owner_docs_are_in_scope_when_declared() -> None:
    result = classify_status([" M BACKLOG.md"], declared_paths={"BACKLOG.md"})

    assert result.route == "in_scope"
    assert result.side_effect == "commit_path"


def test_unknown_dirty_requires_preservation() -> None:
    result = classify_status([" M scripts/backlog_board.py"])

    assert result.route == "archive_required"
    assert result.side_effect == "stash_push_issue_pointer"


def test_archive_plan_lists_preservation_before_cleanup() -> None:
    plan = build_plan(
        [" M scripts/backlog_board.py"],
        declared_paths=set(),
        active_codex_branches=["codex/task-ar-999"],
        extra_worktrees=[{"path": "C:/repo/.worktrees/task-ar-999", "branch": "refs/heads/codex/task-ar-999"}],
        stash_count=1,
        stamp="20260611T010203Z",
    )

    assert plan["route"] == "archive_required"
    assert plan["side_effect"] == "stash_push_issue_pointer"
    assert plan["files"] == ["scripts/backlog_board.py"]
    assert plan["residue"]["branches"] == ["codex/task-ar-999"]
    assert plan["residue"]["worktrees"] == ["C:/repo/.worktrees/task-ar-999"]
    assert plan["residue"]["stashes"] == 1
    assert plan["commands"][0].startswith("git stash push -u -m")
    assert "refs/heads/archive/stashes/20260611" in plan["commands"][1]
    assert "GitHub issue" in plan["issue_handoff"]


def test_cli_check_blocks_unknown_dirty_state(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dirty_intake.py",
            "--status-line",
            " M scripts/backlog_board.py",
            "--check",
            "--stamp",
            "20260611T010203Z",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["decision"] == "block"
    assert payload["route"] == "archive_required"
