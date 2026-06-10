from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "state_sync_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("state_sync_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_task(root: Path, task_id: str, task_set_id: str, status: str = "in_progress") -> None:
    write(
        root / f"agents/lead_engineer/tasks/{task_id}.md",
        f"""---
id: {task_id}
status: {status}
task_set_id: {task_set_id}
---

## Goal

Test task.
""",
    )


def write_surfaces(root: Path, task_set_id: str, active_task: str) -> None:
    write(
        root / "agents/project/NEXT-SESSION-POINTER.yml",
        f"""current_state:
  status: active
  task_set_id: {task_set_id}
resume:
  active_task: {active_task}
  active_task_set: {task_set_id}
""",
    )
    write(root / "BACKLOG-BOARD.md", f"# Board\n\n{task_set_id}\n{active_task}\n")
    write(root / "BACKLOG.md", f"# Backlog\n\n{task_set_id}\n")
    write(root / "STATUS.md", f"# Status\n\n{task_set_id}\n{active_task}\n")


def test_consistent_active_pointer_passes(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-260", "TASKSET-AR-GOVERNANCE-OPS")
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "TASK-AR-260")

    findings = gate.analyze(tmp_path)

    assert not [finding for finding in findings if finding.severity == "block"]


def test_active_task_missing_blocks(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-261", "TASKSET-AR-GOVERNANCE-OPS")
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "TASK-AR-260")

    findings = gate.analyze(tmp_path)

    assert any(finding.subject == "active-task:missing:TASK-AR-260" for finding in findings)


def test_board_missing_active_taskset_blocks(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-260", "TASKSET-AR-GOVERNANCE-OPS")
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "TASK-AR-260")
    write(tmp_path / "BACKLOG-BOARD.md", "# Board\n\nOTHER-TASKSET\n")

    findings = gate.analyze(tmp_path)

    assert any(finding.subject == "surface:missing-taskset:BACKLOG-BOARD.md" for finding in findings)


def test_pointer_active_but_all_tasks_done_blocks(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-260", "TASKSET-AR-GOVERNANCE-OPS", status="completed")
    write_surfaces(tmp_path, "TASKSET-AR-GOVERNANCE-OPS", "TASK-AR-260")

    findings = gate.analyze(tmp_path)

    assert any(finding.subject == "taskset:active-but-complete:TASKSET-AR-GOVERNANCE-OPS" for finding in findings)


def test_completed_taskset_may_be_hidden_from_live_board(tmp_path):
    gate = load_module()
    write_task(tmp_path, "TASK-AR-260", "TASKSET-AR-GOVERNANCE-OPS", status="completed")
    write(
        tmp_path / "agents/project/NEXT-SESSION-POINTER.yml",
        """current_state:
  status: complete
  task_set_id: TASKSET-AR-GOVERNANCE-OPS
resume:
  active_task: none
  active_task_set: TASKSET-AR-GOVERNANCE-OPS
""",
    )
    write(tmp_path / "BACKLOG-BOARD.md", "# Board\n\ncompleted tasksets hidden\n")
    write(tmp_path / "BACKLOG.md", "# Backlog\n\nTASKSET-AR-GOVERNANCE-OPS\n")
    write(tmp_path / "STATUS.md", "# Status\n\nTASKSET-AR-GOVERNANCE-OPS\n")

    findings = gate.analyze(tmp_path)

    assert not [finding for finding in findings if finding.severity == "block"]
