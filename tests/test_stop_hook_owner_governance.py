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
