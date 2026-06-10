"""Validate active taskset sync across pointer, tasks, board, backlog, and status."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


POINTER = Path("agents/project/NEXT-SESSION-POINTER.yml")
TASKS_DIR = Path("agents/lead_engineer/tasks")
BOARD = Path("BACKLOG-BOARD.md")
BACKLOG = Path("BACKLOG.md")
STATUS = Path("STATUS.md")
DONE_STATUSES = {"completed", "done", "released", "완료"}


@dataclass(frozen=True)
class Finding:
    severity: str
    subject: str
    path: str
    detail: str


@dataclass(frozen=True)
class Task:
    task_id: str
    path: Path
    status: str
    task_set_id: str


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _scalar(text: str, key: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*['\"]?([^'\"\n#]+)", text)
    return match.group(1).strip() if match else ""


def _frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if match:
            out[match.group(1)] = match.group(2).strip().strip("'\"")
    return out


def load_tasks(root: Path) -> list[Task]:
    tasks: list[Task] = []
    task_dir = root / TASKS_DIR
    if not task_dir.is_dir():
        return tasks
    for path in sorted(task_dir.glob("TASK-*.md")):
        meta = _frontmatter(_read(path))
        task_id = meta.get("id") or path.stem
        tasks.append(
            Task(
                task_id=task_id,
                path=path,
                status=meta.get("status", "unknown"),
                task_set_id=meta.get("task_set_id", ""),
            )
        )
    return tasks


def active_pointer(root: Path) -> tuple[str, str, str]:
    text = _read(root / POINTER)
    return (
        _scalar(text, "active_task_set") or _scalar(text, "task_set_id"),
        _scalar(text, "active_task"),
        _scalar(text, "status"),
    )


def _contains(root: Path, path: Path, needle: str) -> bool:
    if not needle or needle == "none":
        return True
    return needle in _read(root / path)


def analyze(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    pointer_path = root / POINTER
    if not pointer_path.exists():
        return [Finding("block", "pointer:missing", POINTER.as_posix(), "NEXT-SESSION-POINTER.yml is required")]

    task_set_id, active_task, pointer_status = active_pointer(root)
    tasks = load_tasks(root)
    by_id = {task.task_id: task for task in tasks}
    taskset_tasks = [task for task in tasks if task.task_set_id == task_set_id]

    if not task_set_id or task_set_id == "none":
        findings.append(Finding("watch", "pointer:no-active-taskset", POINTER.as_posix(), "pointer has no active taskset"))
        return findings

    if not taskset_tasks:
        findings.append(Finding("block", f"taskset:missing:{task_set_id}", TASKS_DIR.as_posix(), "active taskset has no canonical task files"))

    if active_task and active_task != "none":
        task = by_id.get(active_task)
        if task is None:
            findings.append(Finding("block", f"active-task:missing:{active_task}", POINTER.as_posix(), "active task is not present in task files"))
        elif task.task_set_id != task_set_id:
            findings.append(
                Finding(
                    "block",
                    f"active-task:taskset-mismatch:{active_task}",
                    task.path.as_posix(),
                    f"active task belongs to {task.task_set_id}, pointer says {task_set_id}",
                )
            )

    open_tasks = [task for task in taskset_tasks if task.status.lower() not in DONE_STATUSES]
    taskset_is_complete = bool(taskset_tasks) and not open_tasks
    if pointer_status in {"active", "in_progress"} and taskset_tasks:
        if not open_tasks:
            findings.append(Finding("block", f"taskset:active-but-complete:{task_set_id}", POINTER.as_posix(), "pointer says active but all taskset tasks are done"))

    for path in (BOARD, BACKLOG, STATUS):
        if not (root / path).exists():
            findings.append(Finding("block", f"surface:missing:{path.as_posix()}", path.as_posix(), "required state surface is missing"))
            continue
        if path == BOARD and taskset_is_complete and pointer_status not in {"active", "in_progress"}:
            continue
        if not _contains(root, path, task_set_id):
            findings.append(Finding("block", f"surface:missing-taskset:{path.as_posix()}", path.as_posix(), f"{path.as_posix()} does not mention active taskset {task_set_id}"))

    if active_task and active_task != "none":
        for path in (BOARD, STATUS):
            if (root / path).exists() and not _contains(root, path, active_task):
                findings.append(Finding("watch", f"surface:missing-active-task:{path.as_posix()}", path.as_posix(), f"{path.as_posix()} does not mention active task {active_task}"))

    return findings


def render(root: Path, findings: list[Finding]) -> str:
    counts = Counter(f.severity for f in findings)
    status = "fail" if counts.get("block", 0) else "pass"
    lines = [
        f"state-sync-gate: {status}",
        f"root={root.resolve()}",
        f"findings={len(findings)}",
        f"block={counts.get('block', 0)}",
        f"watch={counts.get('watch', 0)}",
    ]
    for finding in findings:
        lines.append(f"- {finding.severity} {finding.subject} {finding.path}: {finding.detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Active state sync gate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--check", action="store_true", help="Fail on block findings")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = analyze(args.root)
    print(render(args.root, findings))
    if args.check and any(finding.severity == "block" for finding in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
