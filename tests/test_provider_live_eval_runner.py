from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "provider_live_eval_runner.py"


def _env_without_provider_keys() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def test_provider_live_eval_writes_advisory_record_when_provider_unconfigured(tmp_path: Path) -> None:
    out = tmp_path / "provider-live.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_env_without_provider_keys(),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "agent-runtime-provider-live-eval/v1"
    assert payload["task_ref"] == "TASK-AR-315"
    assert payload["provider_live_configured"] is False
    assert payload["scope_boundary"] == "local_replay_provider_live_unconfigured"
    assert payload["metric_name"] == "model_output_accuracy"
    assert payload["correction_proposals"]


def test_provider_live_eval_strict_blocks_when_provider_unconfigured(tmp_path: Path) -> None:
    out = tmp_path / "provider-live.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out), "--strict"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_env_without_provider_keys(),
    )

    assert result.returncode == 1
    assert out.exists()
