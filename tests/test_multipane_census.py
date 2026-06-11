from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts import multipane_census


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "multipane_census.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def test_census_classifies_active_and_historical_claims(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "agents" / "runtime" / "task_claims" / "active.json",
        {
            "claim_id": "active",
            "task_id": "TASK-1",
            "task_set_id": "SET",
            "agent_role": "lead-engineer",
            "status": "in_progress",
            "phase": "implement",
            "progress_pct": 50,
            "worktree_path": ".worktrees/TASK-1",
            "branch": "task/TASK-1",
            "handoff_path": "handoff.md",
            "log_path": "log.md",
            "last_heartbeat": "2026-06-11T01:00:00+09:00",
        },
    )
    _write_json(
        tmp_path / "agents" / "runtime" / "task_claims" / "released.json",
        {
            "claim_id": "released",
            "task_id": "TASK-2",
            "task_set_id": "SET",
            "agent_role": "qa",
            "status": "released",
            "phase": "taskset-completed",
            "progress_pct": 100,
            "worktree_path": ".worktrees/TASK-2",
            "branch": "task/TASK-2",
            "handoff_path": "handoff.md",
            "log_path": "log.md",
        },
    )

    report = multipane_census.build_report(tmp_path)

    assert report["claims_total"] == 2
    assert report["active_claims"] == 1
    assert report["historical_claims"] == 1
    assert report["active_panes_threshold"] == 5
    assert report["active_panes_threshold_met"] is False
    assert report["task_sets"]["SET"]["claims_total"] == 2


def test_census_cli_emits_json_and_watch_status_for_missing_sources(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--json", "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "watch"
    assert "agents/runtime/task_claims" in payload["data_gaps"]
