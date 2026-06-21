"""Tests for state_machine_gate.py --optional-path handling (issue #185).

`--optional-path` lets one chain reference paths that exist in the Agent Runtime
source repo (e.g. src/agent_runtime/templates/**) but not in generated consumer
projects: a missing optional path is skipped, not a finding. Required `--path`
entries keep their strict missing-is-a-finding behaviour.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "state_machine_gate.py"

_REQUIRED_MACHINES = (
    "health_signal", "cycle", "task", "task_claim", "agent_job", "gate",
    "review", "release", "owner_decision", "hook_enforcement", "ci", "document",
)
VALID_SSOT = "\n".join(
    ["score: 0", "transitions: {}", "signals: pass watch block"]
    + [f"- id: {m}" for m in _REQUIRED_MACHINES]
) + "\n"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_optional_path_missing_is_skipped(tmp_path: Path):
    _write(tmp_path / "agents" / "project" / "STATE-MACHINES.yml", VALID_SSOT)

    result = _run(
        ["--optional-path", "src/agent_runtime/templates/project/agents/project/STATE-MACHINES.yml"],
        tmp_path,
    )

    assert result.returncode == 0, result.stdout
    assert "file:missing" not in result.stdout


def test_required_path_missing_is_a_finding(tmp_path: Path):
    result = _run(["--path", "does/not/exist.yml"], tmp_path)

    assert result.returncode == 1
    assert "file:missing" in result.stdout


def test_optional_path_present_is_validated(tmp_path: Path):
    _write(tmp_path / "agents" / "project" / "STATE-MACHINES.yml", VALID_SSOT)
    _write(tmp_path / "extra.json", "{not valid json")

    result = _run(["--optional-path", "extra.json"], tmp_path)

    assert result.returncode == 1
    assert "json:invalid" in result.stdout
