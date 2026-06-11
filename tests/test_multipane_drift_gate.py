from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts import multipane_drift_gate


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "multipane_drift_gate.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def test_drift_gate_flags_future_heartbeat_released_progress_and_missing_worktree(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "agents" / "runtime" / "task_claims" / "active.json",
        {
            "claim_id": "active",
            "status": "working",
            "phase": "implement",
            "progress_pct": 40,
            "last_heartbeat": "2026-06-11T12:30:00+09:00",
            "worktree_path": ".worktrees/MISSING",
        },
    )
    _write_json(
        tmp_path / "agents" / "runtime" / "task_claims" / "released.json",
        {
            "claim_id": "released",
            "status": "released",
            "phase": "claim-released",
            "progress_pct": 80,
            "last_heartbeat": "2026-06-11T12:00:00+09:00",
        },
    )

    report = multipane_drift_gate.check_root(tmp_path, now="2026-06-11T12:00:00+09:00")

    assert "future-heartbeat:active" in report["watch"]
    assert "active-worktree-missing:active" in report["watch"]
    assert "released-claim-incomplete:released" in report["watch"]
    assert report["status"] == "watch"


def test_drift_gate_cli_check_fails_only_block_findings(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "agents" / "runtime" / "task_claims" / "released.json",
        {"claim_id": "released", "status": "released", "phase": "claim-released", "progress_pct": 80},
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(tmp_path),
            "--now",
            "2026-06-11T12:00:00+09:00",
            "--check",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    assert "multipane-drift-gate: watch" in result.stdout
    assert "released-claim-incomplete:released" in result.stdout
