from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "pane_event_log.py"


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_pane_event_log_appends_monotonic_events_and_summarizes_taskset(tmp_path: Path) -> None:
    first = _run(
        tmp_path,
        "record",
        "--event",
        "claim_created",
        "--actor",
        "lead-engineer",
        "--task-id",
        "TASK-AR-251",
        "--task-set-id",
        "TASKSET-AR-COLLAB-CONCURRENCY",
        "--claim-id",
        "CLAIM-1",
        "--worktree-path",
        ".worktrees/TASK-AR-251",
        "--now",
        "2026-06-10T23:00:00+09:00",
        "--json",
    )
    second = _run(
        tmp_path,
        "record",
        "--event",
        "worktree_ready",
        "--actor",
        "worktree-dispatcher",
        "--task-id",
        "TASK-AR-251",
        "--task-set-id",
        "TASKSET-AR-COLLAB-CONCURRENCY",
        "--claim-id",
        "CLAIM-1",
        "--worktree-path",
        ".worktrees/TASK-AR-251",
        "--now",
        "2026-06-10T23:01:00+09:00",
        "--json",
    )

    assert first.returncode == 0, first.stderr or first.stdout
    assert second.returncode == 0, second.stderr or second.stdout
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["event"]["seq"] == 1
    assert second_payload["event"]["seq"] == 2

    log_path = tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert [record["event"] for record in records] == ["claim_created", "worktree_ready"]
    assert all(record["schema"] == "agent-runtime-pane-event/v1" for record in records)

    summary = _run(tmp_path, "summary", "--json")

    assert summary.returncode == 0, summary.stderr or summary.stdout
    payload = json.loads(summary.stdout)
    assert payload["summary"]["event_count"] == 2
    assert payload["task_sets"][0]["task_set_id"] == "TASKSET-AR-COLLAB-CONCURRENCY"
    assert payload["task_sets"][0]["event_count"] == 2
    assert payload["task_sets"][0]["active_claim_ids"] == ["CLAIM-1"]
