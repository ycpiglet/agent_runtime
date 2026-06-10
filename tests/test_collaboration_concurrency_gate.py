from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "scripts" / "collaboration_concurrency_gate.py"


def _run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_event(root: Path, payload: dict[str, object]) -> None:
    path = root / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def test_collaboration_concurrency_gate_blocks_worker_ssot_write_attempt(tmp_path: Path) -> None:
    _write_event(
        tmp_path,
        {
            "schema": "agent-runtime-pane-event/v1",
            "seq": 1,
            "ts": "2026-06-10T23:05:00+09:00",
            "event": "ssot_write_attempted",
            "actor": "lead-engineer",
            "task_id": "TASK-AR-252",
            "task_set_id": "TASKSET-AR-COLLAB-CONCURRENCY",
            "claim_id": "CLAIM-1",
            "ssot_path": "BACKLOG.md",
        },
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "collab-concurrency:ssot-write-not-orchestrator" in result.stdout


def test_collaboration_concurrency_gate_accepts_orchestrator_ssot_write_event(tmp_path: Path) -> None:
    _write_event(
        tmp_path,
        {
            "schema": "agent-runtime-pane-event/v1",
            "seq": 1,
            "ts": "2026-06-10T23:05:00+09:00",
            "event": "ssot_write_attempted",
            "actor": "orchestrator",
            "task_id": "TASK-AR-252",
            "task_set_id": "TASKSET-AR-COLLAB-CONCURRENCY",
            "claim_id": "CLAIM-1",
            "ssot_path": "BACKLOG.md",
            "orchestrator_approved": True,
        },
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 0
    assert "collaboration-concurrency-gate: pass" in result.stdout
