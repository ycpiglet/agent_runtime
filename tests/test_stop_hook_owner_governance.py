import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_stop_hook_owner_governance_emits_stop_decision_json(tmp_path):
    env = os.environ.copy()
    env["AGENT_RUNTIME_HOOK_LOG_DIR"] = str(tmp_path / "hook-logs")
    result = subprocess.run(
        [sys.executable, "scripts/stop_hook_owner_governance.py"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["decision"] == "approve"
    assert "owner governance gate passed" in payload["reason"]
    assert "findings=0" in payload["systemMessage"]
    assert "hook diagnostic:" in payload["systemMessage"]
    logs = list((tmp_path / "hook-logs").glob("stop-owner-governance-*.json"))
    assert logs
    diagnostic = json.loads(logs[-1].read_text(encoding="utf-8"))
    assert diagnostic["schema"] == "agent-runtime-stop-hook-diagnostic/v1"
    assert diagnostic["returncode"] == 0
    assert diagnostic["payload"]["decision"] == "approve"


def test_codex_hooks_include_session_closeout_guards():
    hooks = json.loads((REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    text = json.dumps(hooks)
    commands = [
        hook["command"]
        for entries in hooks.get("hooks", {}).values()
        for entry in entries
        for hook in entry.get("hooks", [])
        if isinstance(hook, dict) and "command" in hook
    ]

    assert "scripts/session_baseline.py" in text
    assert "scripts\\stop_hook_dirty_intake.cmd" in commands
    assert "scripts/dirty_intake.py" not in text
    assert "scripts/owner_doc_format_gate.py" in text


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
