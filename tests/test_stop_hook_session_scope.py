from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from scripts import stop_hook_session_scope as scope


REPO_ROOT = Path(__file__).resolve().parents[1]


def _transcript(tmp_path: Path, *events: dict) -> Path:
    path = tmp_path / "transcript.jsonl"
    path.write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8",
    )
    return path


def _hook_input(transcript_path: Path) -> str:
    return json.dumps(
        {
            "hook_event_name": "Stop",
            "transcript_path": str(transcript_path),
            "stop_hook_active": False,
            "background_tasks": [],
            "session_crons": [],
        },
        ensure_ascii=False,
    )


def test_read_only_transcript_is_question_only(tmp_path: Path) -> None:
    transcript = _transcript(
        tmp_path,
        {"tool_name": "Bash", "tool_input": {"command": "git status --short"}},
        {"tool_name": "functions.shell_command", "tool_input": {"command": "rg -n stop_hook scripts"}},
    )

    result = scope.assess({"transcript_path": str(transcript)})

    assert result["bypass"] is True
    assert result["reason"] == "question-only-session"


def test_write_tool_transcript_enforces_closeout(tmp_path: Path) -> None:
    transcript = _transcript(
        tmp_path,
        {"type": "tool_use", "name": "Write", "input": {"file_path": "scripts/example.py"}},
    )

    result = scope.assess({"transcript_path": str(transcript)})

    assert result["bypass"] is False
    assert result["reason"] == "session-has-mutating-activity"


def test_codex_apply_patch_transcript_enforces_closeout(tmp_path: Path) -> None:
    transcript = _transcript(
        tmp_path,
        {"type": "function_call", "name": "functions.apply_patch", "arguments": "*** Begin Patch"},
    )

    assert scope.assess({"transcript_path": str(transcript)})["bypass"] is False


def test_mutating_shell_command_enforces_closeout(tmp_path: Path) -> None:
    transcript = _transcript(
        tmp_path,
        {"tool_name": "Bash", "tool_input": {"command": "git add scripts/stop_hook_dirty_intake.py"}},
    )

    assert scope.assess({"transcript_path": str(transcript)})["bypass"] is False


def test_missing_transcript_fails_closed() -> None:
    result = scope.assess({})

    assert result["bypass"] is False
    assert result["reason"] == "missing-transcript-path"


def test_mutating_session_skips_unrelated_dirty_paths(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "reviews").mkdir()
    (tmp_path / "reviews" / "other.md").write_text("other pane\n", encoding="utf-8")
    transcript = _transcript(
        tmp_path,
        {"tool_name": "Write", "tool_input": {"file_path": "scripts/current.py"}},
    )

    result = scope.assess({"transcript_path": str(transcript)}, root=tmp_path)

    assert result["bypass"] is True
    assert result["reason"] == "dirty-state-unrelated-to-session"


def test_temp_file_shell_write_skips_unrelated_repo_dirty_paths(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "reviews").mkdir()
    (tmp_path / "reviews" / "other.md").write_text("other pane\n", encoding="utf-8")
    transcript = _transcript(
        tmp_path,
        {
            "tool_name": "functions.shell_command",
            "tool_input": {
                "command": (
                    "$tmp=Join-Path $env:TEMP 'agent-runtime-question-only-transcript.jsonl'; "
                    "Set-Content -LiteralPath $tmp -Value '{\"type\":\"message\"}' -Encoding UTF8"
                )
            },
        },
    )

    result = scope.assess({"transcript_path": str(transcript)}, root=tmp_path)

    assert result["bypass"] is True
    assert result["reason"] == "dirty-state-unrelated-to-session"


def test_shell_write_to_dirty_repo_path_enforces_closeout(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "current.py").write_text("dirty\n", encoding="utf-8")
    transcript = _transcript(
        tmp_path,
        {
            "tool_name": "functions.shell_command",
            "tool_input": {
                "command": "$target='scripts/current.py'; Set-Content -LiteralPath $target -Value 'dirty'"
            },
        },
    )

    result = scope.assess({"transcript_path": str(transcript)}, root=tmp_path)

    assert result["bypass"] is False
    assert result["reason"] == "session-has-mutating-activity"


def test_git_add_paths_skip_unrelated_repo_dirty_after_commit(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "reviews").mkdir()
    (tmp_path / "reviews" / "other.md").write_text("other pane\n", encoding="utf-8")
    transcript = _transcript(
        tmp_path,
        {
            "tool_name": "functions.shell_command",
            "tool_input": {
                "command": "git add scripts/stop_hook_session_scope.py tests/test_stop_hook_session_scope.py"
            },
        },
        {"tool_name": "functions.shell_command", "tool_input": {"command": "git commit -m hook-scope"}},
    )

    result = scope.assess({"transcript_path": str(transcript)}, root=tmp_path)

    assert result["bypass"] is True
    assert result["reason"] == "dirty-state-unrelated-to-session"


def test_mutating_session_enforces_overlapping_dirty_paths(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "current.py").write_text("dirty\n", encoding="utf-8")
    transcript = _transcript(
        tmp_path,
        {"tool_name": "Write", "tool_input": {"file_path": "scripts/current.py"}},
    )

    result = scope.assess({"transcript_path": str(transcript)}, root=tmp_path)

    assert result["bypass"] is False
    assert result["reason"] == "session-has-mutating-activity"


def test_dirty_intake_hook_skips_question_only_session(tmp_path: Path) -> None:
    transcript = _transcript(
        tmp_path,
        {"tool_name": "Bash", "tool_input": {"command": "git status --short"}},
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/stop_hook_dirty_intake.py",
            "--status-line",
            " M scripts/backlog_board.py",
        ],
        cwd=REPO_ROOT,
        input=_hook_input(transcript),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_dirty_intake_hook_keeps_block_for_mutating_session(tmp_path: Path) -> None:
    transcript = _transcript(
        tmp_path,
        {"tool_name": "Write", "tool_input": {"file_path": "scripts/example.py"}},
    )

    env = dict(os.environ, AGENT_RUNTIME_STOP_SCOPE_DISABLE="1")
    result = subprocess.run(
        [
            sys.executable,
            "scripts/stop_hook_dirty_intake.py",
            "--status-line",
            " M scripts/backlog_board.py",
        ],
        cwd=REPO_ROOT,
        env=env,
        input=_hook_input(transcript),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["decision"] == "block"
    assert "dirty intake requires preservation" in payload["reason"]


def test_closure_hook_skips_question_only_session(tmp_path: Path) -> None:
    transcript = _transcript(
        tmp_path,
        {"tool_name": "Bash", "tool_input": {"command": "rg -n closure_gate scripts"}},
    )

    result = subprocess.run(
        [sys.executable, "scripts/stop_hook_closure_gate.py"],
        cwd=REPO_ROOT,
        input=_hook_input(transcript),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
