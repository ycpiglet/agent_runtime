from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "taskset_prompt_hook.py"


def test_taskset_prompt_hook_injects_dispatcher_instruction_for_korean_prompt() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--text", "taskset-quality-loop 진행해줘"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "taskset" in context.lower()
    assert "scripts/taskset_dispatcher.py" in context.replace("\\", "/")
    assert "quality-loop" in context
    assert "worktree" in context.lower()
