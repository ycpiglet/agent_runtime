from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "taskset_work_gate.py"


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_require_complete(root: Path, task_set_id: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--task-set-id",
            task_set_id,
            "--require-complete",
            "--check",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_gate_blocks_task_without_task_set_id(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TASK-AR-901.md").write_text(
        """---
id: TASK-AR-901
status: planned
priority: P0
difficulty: M
est_hours: 1
est_tokens: 100
tags: []
---

## Goal
- Missing task set.
""",
        encoding="utf-8",
    )

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "taskset:missing-task-set-id:TASK-AR-901" in result.stdout


def test_gate_blocks_backlog_board_without_taskset_routing(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TASK-AR-901.md").write_text(
        """---
id: TASK-AR-901
status: planned
priority: P0
difficulty: M
est_hours: 1
est_tokens: 100
task_set_id: TASKSET-AR-QUALITY-LOOP
tags: []
---

## Goal
- Has task set.
""",
        encoding="utf-8",
    )
    (tmp_path / "BACKLOG-BOARD.md").write_text("## Bottom Line\n- Recommended next: TASK-AR-901\n", encoding="utf-8")

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "BACKLOG-BOARD.md: taskset:missing-task-set-count" in result.stdout
    assert "BACKLOG-BOARD.md: taskset:global-recommended-next" in result.stdout


def test_gate_blocks_incomplete_required_task_set(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    claims_dir = tmp_path / "agents" / "runtime" / "task_claims"
    tasks_dir.mkdir(parents=True)
    claims_dir.mkdir(parents=True)
    (tasks_dir / "TASK-AR-901.md").write_text(
        """---
id: TASK-AR-901
status: planned
priority: P0
difficulty: M
est_hours: 1
est_tokens: 100
task_set_id: TASKSET-AR-QUALITY-LOOP
tags: []
---
""",
        encoding="utf-8",
    )
    (claims_dir / "CLAIM-901.json").write_text(
        """{
  "claim_id": "CLAIM-901",
  "task_id": "TASK-AR-901",
  "task_set_id": "TASKSET-AR-QUALITY-LOOP",
  "status": "released",
  "phase": "taskset-in-progress",
  "progress_pct": 0
}
""",
        encoding="utf-8",
    )

    result = _run_require_complete(tmp_path, "TASKSET-AR-QUALITY-LOOP")

    assert result.returncode == 1
    assert "taskset:incomplete-task:TASKSET-AR-QUALITY-LOOP:TASK-AR-901:planned" in result.stdout
    assert "taskset:released-claim-phase-not-complete:TASKSET-AR-QUALITY-LOOP:CLAIM-901:taskset-in-progress" in result.stdout
    assert "taskset:released-claim-progress-not-100:TASKSET-AR-QUALITY-LOOP:CLAIM-901:0" in result.stdout
