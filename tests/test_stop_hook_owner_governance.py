import json
import os
import subprocess
import sys
from pathlib import Path
import importlib.util


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
SPEC = REPO_ROOT / "scripts" / "stop_hook_owner_governance.py"
MODULE_SPEC = importlib.util.spec_from_file_location("stop_hook_owner_governance", SPEC)
assert MODULE_SPEC and MODULE_SPEC.loader
owner_hook = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(owner_hook)


def test_stop_hook_owner_governance_emits_stop_decision_json(tmp_path):
    result = subprocess.CompletedProcess(
        args=[sys.executable, "scripts/owner_governance_gate.py"],
        returncode=0,
        stdout="owner-governance: result: scripts/example.py --check -> 0\nfindings=0\n",
        stderr="",
    )

    payload = owner_hook.build_payload(result, diagnostic_path=tmp_path / "diag.json")

    assert payload["decision"] == "approve"
    assert "owner governance gate passed" in payload["reason"]
    assert "owner governance summary: returncode=0" in payload["systemMessage"]
    assert "findings=" in payload["systemMessage"]
    assert "hook diagnostic:" in payload["systemMessage"]

    diagnostic_path = owner_hook.write_diagnostic(result, payload, log_dir=tmp_path / "hook-logs")
    assert diagnostic_path is not None
    diagnostic = json.loads(diagnostic_path.read_text(encoding="utf-8"))
    assert diagnostic["schema"] == "agent-runtime-stop-hook-diagnostic/v1"
    assert diagnostic["returncode"] == 0
    assert diagnostic["payload"]["decision"] == "approve"


def test_codex_hooks_include_session_closeout_guards():
    hooks = json.loads((REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    commands = [
        hook["command"]
        for entries in hooks.get("hooks", {}).values()
        for entry in entries
        for hook in entry.get("hooks", [])
        if isinstance(hook, dict) and "command" in hook
    ]

    assert "python3 -m agent_runtime.hook_runtime session-start" in commands
    assert "python3 -m agent_runtime.hook_runtime stop-dirty" in commands
    assert "python3 -m agent_runtime.hook_runtime posttool-owner-doc" in commands
    from agent_runtime.hook_runtime import SCRIPTS
    assert SCRIPTS["session-start"] == "scripts/session_start_hook.py"
    assert SCRIPTS["stop-dirty"] == "scripts/stop_hook_dirty_intake.py"


def test_stop_hook_dirty_intake_emits_stop_json_without_exit_failure():
    result = subprocess.run(
        [
            sys.executable,
            "scripts/stop_hook_dirty_intake.py",
            "--status-line",
            " M scripts/backlog_board.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["decision"] == "block"
    assert "dirty intake requires preservation" in payload["reason"]
    assert '"route": "archive_required"' in payload["systemMessage"]


def test_stop_hook_owner_governance_skips_question_only_session(tmp_path):
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status --short"}}) + "\n",
        encoding="utf-8",
    )
    hook_input = json.dumps(
        {
            "hook_event_name": "Stop",
            "transcript_path": str(transcript),
            "stop_hook_active": False,
            "background_tasks": [],
            "session_crons": [],
        }
    )

    result = subprocess.run(
        [sys.executable, "scripts/stop_hook_owner_governance.py"],
        cwd=REPO_ROOT,
        input=hook_input,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
