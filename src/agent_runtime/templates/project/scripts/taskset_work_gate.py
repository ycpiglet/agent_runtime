"""Validate task-set routing rules for backlog and parallel pane work."""

from __future__ import annotations

import argparse
from pathlib import Path

import backlog_board


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


def _backlog_board_is_fresh(root: Path, board: Path, tasks: list[backlog_board.Task]) -> bool:
    generated = backlog_board.render(tasks)
    try:
        existing = board.read_text(encoding="utf-8")
    except OSError:
        return False
    return _normalize(existing) == _normalize(generated)


def check_root(root: Path) -> list[str]:
    root = root.resolve()
    findings: list[str] = []
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks = backlog_board.load_tasks(tasks_dir)

    for task in tasks:
        raw_task_set = str(task.meta.get("task_set_id") or "").strip()
        if not raw_task_set:
            findings.append(f"{_rel(root, task.path)}: taskset:missing-task-set-id:{task.task_id}")

    board = root / "BACKLOG-BOARD.md"
    if board.exists():
        text = board.read_text(encoding="utf-8")
        if "task_set_count:" not in text:
            findings.append("BACKLOG-BOARD.md: taskset:missing-task-set-count")
        if "Recommended next:" in text:
            findings.append("BACKLOG-BOARD.md: taskset:global-recommended-next")
        if "Routing rule: choose a task set first" not in text:
            findings.append("BACKLOG-BOARD.md: taskset:missing-routing-rule")
        if not _backlog_board_is_fresh(root, board, tasks):
            findings.append(
                "BACKLOG-BOARD.md: stale:content-mismatch: run python scripts/backlog_board.py --write"
            )
    else:
        findings.append("BACKLOG-BOARD.md: missing")

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task-set routing gate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository or host root")
    parser.add_argument("--check", action="store_true", help="Return non-zero when findings exist")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings = check_root(root)
    status = "fail" if findings else "pass"
    print(f"taskset-work-gate: {status}")
    print(f"root={root}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
