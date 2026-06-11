import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import backlog_board  # noqa: E402


def _write_task(tasks_dir: Path, task_id: str, task_set_id: str, status: str = "planned", priority: str = "P0") -> None:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.md").write_text(
        f"""---
id: {task_id}
task_uid: 11111111-1111-4111-8111-{task_id[-3:]}000000000
registered_at: 2026-06-10T12:00:00+09:00
status: {status}
priority: {priority}
difficulty: M
est_hours: 2
est_tokens: 200
task_set_id: {task_set_id}
tags:
  - test
---

## Goal
- Keep this task inside its task set.
""",
        encoding="utf-8",
    )


def test_backlog_board_groups_tasks_by_task_set_before_lane(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    _write_task(tasks_dir, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="in_progress")
    _write_task(tasks_dir, "TASK-AR-902", "TASKSET-AR-QUALITY-LOOP", status="planned", priority="P1")
    _write_task(tasks_dir, "TASK-AR-903", "TASKSET-AR-PANE-PROGRESS", status="planned")

    tasks = backlog_board.load_tasks(tasks_dir)
    board = backlog_board.render(tasks)

    assert "task_set_count: 2" in board
    assert "Recommended next:" not in board
    assert "Routing rule: choose a task set first" in board
    assert "## Action Board" in board
    assert "### Quality Sentinel (`TASKSET-AR-QUALITY-LOOP`)" in board
    assert "### Progress Scout (`TASKSET-AR-PANE-PROGRESS`)" in board
    assert "| Task | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |" in board

    quality_section = board.split("### Quality Sentinel (`TASKSET-AR-QUALITY-LOOP`)", 1)[1].split("### Progress Scout", 1)[0]
    assert quality_section.index("TASK-AR-901") < quality_section.index("TASK-AR-902")


def test_backlog_board_hides_completed_tasks_and_completed_task_sets(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    _write_task(tasks_dir, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", status="completed")
    _write_task(tasks_dir, "TASK-AR-902", "TASKSET-AR-QUALITY-LOOP", status="done")
    _write_task(tasks_dir, "TASK-AR-903", "TASKSET-AR-RELEASE-STEWARD", status="in_progress")

    tasks = backlog_board.load_tasks(tasks_dir)
    board = backlog_board.render(tasks)

    assert "task_count: 3" in board
    assert "open_count: 1" in board
    assert "task_set_count: 1" in board
    assert "completed_count: 2" in board
    assert "completed_task_set_count: 1" in board
    action_board = board.split("## Action Board", 1)[1].split("## Archived Task Sets", 1)[0]
    assert "### Quality Sentinel (`TASKSET-AR-QUALITY-LOOP`)" not in action_board
    assert "TASK-AR-901" not in action_board
    assert "TASK-AR-902" not in action_board
    assert "### Release Steward (`TASKSET-AR-RELEASE-STEWARD`)" in board
    assert "TASK-AR-903" in board
    assert "## Archived Task Sets" in board
    archived_sets = board.split("## Archived Task Sets", 1)[1]
    assert "| Quality Sentinel (`TASKSET-AR-QUALITY-LOOP`) |" in archived_sets
    assert "| `2/2` done |" in archived_sets
    archived_set_summary = archived_sets.split("## Archived Task Files", 1)[0]
    assert "TASK-AR-901" not in archived_set_summary
    assert "TASK-AR-902" not in archived_set_summary
    archived_files = board.split("## Archived Task Files", 1)[1]
    assert "TASK-AR-901" in archived_files
    assert "TASK-AR-902" in archived_files
    assert "registered_at" in archived_files


def test_real_backlog_tasks_are_classified_into_twenty_two_task_sets() -> None:
    tasks = backlog_board.load_tasks(ROOT / "agents" / "lead_engineer" / "tasks")
    task_set_ids = {task.task_set_id for task in tasks}

    assert len(tasks) >= 55
    assert task_set_ids == {
        "TASKSET-AR-CONTEXT-KNOWLEDGE",
        "TASKSET-AR-QUALITY-LOOP",
        "TASKSET-AR-MIGRATION-PARITY",
        "TASKSET-AR-RELEASE-STEWARD",
        "TASKSET-AR-UI-CONSOLE",
        "TASKSET-AR-RSI-PLANNING",
        "TASKSET-AR-RSI-OPERATING-SYSTEM",
        "TASKSET-AR-PANE-PROGRESS",
        "TASKSET-AR-COLLAB-CONCURRENCY",
        "TASKSET-AR-GOVERNANCE-OPS",
        "TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE",
        "TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION",
        "TASKSET-AR-TASK-IDENTITY",
        "TASKSET-AR-UI-DESIGN-SYSTEM",
        "TASKSET-AR-UI-DESIGN-IMPLEMENTATION",
        "TASKSET-AR-REPO-HYGIENE",
        "TASKSET-AR-OPS-FEEDBACK-ANALYSIS",
        "TASKSET-AR-VISION-GAP-CLOSURE",
        "TASKSET-AR-UI-UX-V2",
        "TASKSET-AR-UI-PLATFORM-EXTENSIONS",
        "TASKSET-AR-UI-LIVING-CONSOLE",
        "TASKSET-AR-PM-OPERATING-SYSTEM",
    }
