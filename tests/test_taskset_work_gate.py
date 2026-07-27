from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "taskset_work_gate.py"

TASK_TEMPLATE = """---
id: {task_id}
status: {status}
priority: P0
difficulty: M
est_hours: 1
est_tokens: 100
task_set_id: TASKSET-AR-QUALITY-LOOP
tags: []
---

## Goal
- Sample task for board freshness tests.
"""


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


def _write_task(root: Path, task_id: str, status: str) -> None:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.md").write_text(
        TASK_TEMPLATE.format(task_id=task_id, status=status), encoding="utf-8"
    )


def _write_claim(root: Path, claim_id: str, claimed_at: str) -> None:
    claims_dir = root / "agents" / "runtime" / "task_claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    (claims_dir / f"{claim_id}.json").write_text(
        json.dumps(
            {
                "claim_id": claim_id,
                "task_id": "TASK-AR-901",
                "task_set_id": "TASKSET-AR-QUALITY-LOOP",
                "status": "claimed",
                "claimed_at": claimed_at,
            }
        ),
        encoding="utf-8",
    )


def _write_rendered_board(root: Path) -> str:
    from scripts import backlog_board

    tasks = backlog_board.load_tasks(root / "agents" / "lead_engineer" / "tasks")
    text = backlog_board.render(tasks, root=root)
    (root / "BACKLOG-BOARD.md").write_text(text, encoding="utf-8")
    return text


def test_gate_accepts_board_with_only_wall_clock_drift(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "planned")
    claimed_at = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    _write_claim(tmp_path, "CLAIM-901", claimed_at)
    board = _write_rendered_board(tmp_path)

    # Simulate a board generated hours/days earlier: younger WIP age, no stale
    # claims yet, older generated_at date. Only wall-clock derived tokens differ.
    aged = re.sub(r"oldest `[0-9.]+h`; stale `\d+`", "oldest `0.1h`; stale `0`", board)
    aged = re.sub(r"(?m)^generated_at: .*$", "generated_at: 2026-06-01", aged)
    assert aged != board
    (tmp_path / "BACKLOG-BOARD.md").write_text(aged, encoding="utf-8")

    result = _run(tmp_path)

    assert "stale:content-mismatch" not in result.stdout
    assert result.returncode == 0


def test_gate_flags_stale_board_after_task_status_change(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "planned")
    _write_rendered_board(tmp_path)

    _write_task(tmp_path, "TASK-AR-901", "in_progress")

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "stale:content-mismatch" in result.stdout


def test_gate_flags_stale_board_after_task_added(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "planned")
    _write_rendered_board(tmp_path)

    _write_task(tmp_path, "TASK-AR-902", "planned")

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "stale:content-mismatch" in result.stdout


def test_gate_flags_stale_board_after_new_claim(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-901", "planned")
    _write_rendered_board(tmp_path)

    _write_claim(tmp_path, "CLAIM-901", datetime.now(timezone.utc).isoformat())

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "stale:content-mismatch" in result.stdout


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


def test_session_closeout_verifier_runs_taskset_and_owner_governance() -> None:
    from scripts import verify_session_closeout_taskset

    commands = [" ".join(command) for command in verify_session_closeout_taskset.COMMANDS]

    assert any("TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION" in command for command in commands)
    assert any("--require-complete" in command for command in commands)
    assert any("scripts/owner_governance_gate.py" in command for command in commands)


def test_session_closeout_verifier_invokes_taskset_and_owner_gates() -> None:
    script = (REPO_ROOT / "scripts" / "verify_session_closeout_taskset.py").read_text(encoding="utf-8")

    assert "TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION" in script
    assert "scripts/taskset_work_gate.py" in script
    assert "scripts/owner_governance_gate.py" in script


def test_ar630_attention_line_is_wall_clock_masked():
    # TASK-AR-630: the canonical attention rollup includes the time-decaying
    # stale group; the freshness diff must not go red purely by time passing.
    import taskset_work_gate as gate
    a = gate._mask_wall_clock_fields("- Needs attention: `3` — stale `3` (single source: scripts/attention_inbox.py = console cockpit, TASK-AR-630).")
    b = gate._mask_wall_clock_fields("- Needs attention: `4` — stale `4` (single source: scripts/attention_inbox.py = console cockpit, TASK-AR-630).")
    assert a == b == "- Needs attention: <wall-clock>"
