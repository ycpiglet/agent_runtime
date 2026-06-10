import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_stop_hook_owner_governance_emits_stop_decision_json():
    result = subprocess.run(
        [sys.executable, "scripts/stop_hook_owner_governance.py"],
        cwd=REPO_ROOT,
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
