"""Smoke test for the shipped template work_item_classifier + backlog_board pair.

Regression for issue #211: the v0.5.0 template backlog_board.py dropped the
``Task.initiative_id`` property while the template work_item_classifier.py
still reads ``task.initiative_id``, so a consumer adopting both files got an
AttributeError. This test runs the template pair exactly the way a consumer
does (both scripts side by side, classifier importing the sibling board).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_SCRIPTS = REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_consumer_repo(root: Path) -> None:
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    # status_alias.py rides along: backlog_board consumes the shared status
    # vocabulary (#121 item 4), and a consumer syncs the whole scripts/ dir.
    for name in ("backlog_board.py", "work_item_classifier.py", "status_alias.py"):
        shutil.copy(TEMPLATE_SCRIPTS / name, scripts / name)
    _write(
        root / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md",
        """---
id: TASK-AR-901
display_id: TASK-AR-901
task_uid: 11111111-1111-4111-8111-000000000001
registered_at: 2026-06-12T00:00:01+09:00
created_at: 2026-06-12T00:00:01+09:00
updated_at: 2026-06-12T00:00:01+09:00
status: planned
priority: P1
difficulty: M
est_hours: 1
est_tokens: 100
initiative_id: INIT-TEST
task_set_id: TASKSET-TEMPLATE-SMOKE
tags: []
---

# TASK-AR-901 - Template smoke task

## Goal

Template classifier smoke coverage.
""",
    )


def test_template_classifier_runs_against_template_board(tmp_path: Path) -> None:
    _seed_consumer_repo(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(tmp_path / "scripts" / "work_item_classifier.py"),
            "--root",
            str(tmp_path),
            "--write",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    payload = tmp_path / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json"
    assert payload.is_file()
    assert "INIT-TEST" in payload.read_text(encoding="utf-8")


def test_template_board_task_exposes_initiative_id(tmp_path: Path) -> None:
    _seed_consumer_repo(tmp_path)
    probe = (
        "import sys; from pathlib import Path; sys.path.insert(0, r'%s');"
        "import backlog_board;"
        "tasks = backlog_board.load_tasks(Path(r'%s'));"
        "assert tasks, 'expected seeded task';"
        "assert tasks[0].initiative_id == 'INIT-TEST', tasks[0].initiative_id"
    ) % (tmp_path / "scripts", tmp_path / "agents" / "lead_engineer" / "tasks")
    result = subprocess.run(
        [sys.executable, "-c", probe],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
