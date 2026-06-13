"""Audit conversation-to-work traceability for planning records.

Owner/Claude/Codex planning discussions recorded in ``reviews/`` (frontmatter
``type: meeting``/``type: planning`` or tags containing ``planning-record``)
must provably map to durable work records: task files under
``agents/lead_engineer/tasks/``, task-set rows in ``BACKLOG-BOARD.md``, and a
consistent ``agents/project/NEXT-SESSION-POINTER.yml``. Follow-up work must
never stay hidden in chat.

Findings:

- ``watch unmapped-planning-record``: the record declares follow-up work (a
  ``Proposed Follow-Up`` table row, or an ``Action Board`` row whose status
  cell is Next/Action/Planned/Follow-up/Todo/Open) but references no
  ``TASK-AR-*``/``TASKSET-AR-*``/``INIT-AR-*`` work-item id.
- ``block missing-task-file``: the record references a ``TASK-AR-*`` id whose
  canonical task file does not exist.
- ``watch board-taskset-missing`` and ``watch pointer-*``: referenced task
  sets missing from the board, or internally inconsistent pointer entries.

This audit is report-only (B-mode boundary): it never creates or mutates work
records. ``--check`` exits nonzero only when block findings exist.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

TASKS_DIR = "agents/lead_engineer/tasks"
BOARD_PATH = "BACKLOG-BOARD.md"
POINTER_PATH = "agents/project/NEXT-SESSION-POINTER.yml"
REVIEWS_DIR = "reviews"

PLANNING_TYPES = {"meeting", "planning"}
PLANNING_TAG = "planning-record"

FOLLOW_UP_HEADING = re.compile(r"^#{1,6}\s.*(proposed follow-up|action board)", re.IGNORECASE)
PROPOSED_FOLLOW_UP = re.compile(r"proposed follow-up", re.IGNORECASE)
ANY_HEADING = re.compile(r"^#{1,6}\s")
FOLLOW_UP_STATUS_CELLS = {"next", "action", "planned", "follow-up", "todo", "open"}

TASK_ID_RE = re.compile(r"TASK-AR-\d{8}-\d{6}-[0-9a-f]{8}|TASK-AR-\d+")
TASKSET_ID_RE = re.compile(r"TASKSET-AR-[A-Z0-9]+(?:-[A-Z0-9]+)*")
INIT_ID_RE = re.compile(r"INIT-AR-[A-Z0-9]+(?:-[A-Z0-9]+)*")
POINTER_TASK_FILE_RE = re.compile(r"agents/lead_engineer/tasks/[A-Za-z0-9._-]+\.md")


@dataclass(frozen=True)
class Finding:
    severity: str  # "watch" or "block"
    kind: str
    path: str
    detail: str


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parse_frontmatter(text: str) -> dict[str, object]:
    """Parse the minimal frontmatter subset used by review records."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict[str, object] = {}
    current_list: str | None = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and current_list is not None:
            existing = meta.setdefault(current_list, [])
            if isinstance(existing, list):
                existing.append(item.group(1).strip().strip("\"'"))
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key] = [part.strip().strip("\"'") for part in value[1:-1].split(",") if part.strip()]
            current_list = None
        elif value:
            meta[key] = value.strip("\"'")
            current_list = None
        else:
            meta[key] = []
            current_list = key
    return meta


def is_planning_record(meta: dict[str, object]) -> bool:
    record_type = str(meta.get("type") or "").strip().lower()
    if record_type in PLANNING_TYPES:
        return True
    tags = meta.get("tags")
    if isinstance(tags, str):
        tags = [tags]
    if isinstance(tags, list):
        return any(str(tag).strip().lower() == PLANNING_TAG for tag in tags)
    return False


def _table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell) and any(cells)


def declares_follow_up(text: str) -> bool:
    """Heuristic: a Proposed Follow-Up/Action Board section with follow-up rows.

    Proposed Follow-Up sections declare follow-up work with any data row.
    Action Board sections declare follow-up work only when a row carries a
    Next/Action/Planned/Follow-up/Todo/Open status cell, so records whose
    actions are all Done/Watch do not require new work-item registration.
    """
    in_section = False
    proposed_section = False
    seen_header = False
    for line in text.splitlines():
        if ANY_HEADING.match(line):
            heading = FOLLOW_UP_HEADING.match(line)
            in_section = bool(heading)
            proposed_section = bool(heading and PROPOSED_FOLLOW_UP.search(line))
            seen_header = False
            continue
        if not in_section or not line.strip().startswith("|"):
            continue
        cells = _table_cells(line)
        if _is_separator_row(cells):
            continue
        if not seen_header:
            seen_header = True
            continue
        if proposed_section and any(cells):
            return True
        if any(cell.strip("`").strip().lower() in FOLLOW_UP_STATUS_CELLS for cell in cells):
            return True
    return False


def _planning_records(root: Path) -> list[Path]:
    reviews = root / REVIEWS_DIR
    if not reviews.is_dir():
        return []
    records: list[Path] = []
    for path in sorted(reviews.glob("*.md")):
        meta = parse_frontmatter(_read(path))
        if is_planning_record(meta):
            records.append(path)
    return records


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _audit_record(root: Path, path: Path, board_text: str, findings: list[Finding]) -> None:
    rel = _rel(root, path)
    text = _read(path)
    task_ids = sorted(set(TASK_ID_RE.findall(text)))
    taskset_ids = sorted(set(TASKSET_ID_RE.findall(text)))
    init_ids = sorted(set(INIT_ID_RE.findall(text)))

    if declares_follow_up(text) and not (task_ids or taskset_ids or init_ids):
        findings.append(
            Finding(
                "watch",
                "unmapped-planning-record",
                rel,
                "record declares follow-up work but references no TASK-AR/TASKSET-AR/INIT-AR id",
            )
        )

    for task_id in task_ids:
        task_file = root / TASKS_DIR / f"{task_id}.md"
        if not task_file.exists():
            findings.append(
                Finding(
                    "block",
                    "missing-task-file",
                    rel,
                    f"references {task_id} but {TASKS_DIR}/{task_id}.md does not exist",
                )
            )

    for taskset_id in taskset_ids:
        if not board_text:
            findings.append(
                Finding(
                    "watch",
                    "board-missing",
                    rel,
                    f"references {taskset_id} but {BOARD_PATH} is missing or empty",
                )
            )
        elif taskset_id not in board_text:
            findings.append(
                Finding(
                    "watch",
                    "board-taskset-missing",
                    rel,
                    f"references {taskset_id} but it does not appear in {BOARD_PATH}",
                )
            )


def _audit_pointer(root: Path, board_text: str, findings: list[Finding]) -> None:
    pointer = root / POINTER_PATH
    if not pointer.exists():
        findings.append(Finding("watch", "pointer-missing", POINTER_PATH, "next-session pointer file not found"))
        return
    text = _read(pointer)

    active_task = re.search(r"(?m)^\s*active_task:\s*[\"']?([A-Za-z0-9-]+)", text)
    if active_task:
        task_id = active_task.group(1)
        # `none`/empty and other non-task-id sentinels mean "no active task";
        # only a real TASK-* id should be resolved to a file on disk.
        if task_id.startswith("TASK-") and not (root / TASKS_DIR / f"{task_id}.md").exists():
            findings.append(
                Finding(
                    "watch",
                    "pointer-task-missing",
                    POINTER_PATH,
                    f"resume.active_task {task_id} has no file {TASKS_DIR}/{task_id}.md",
                )
            )

    for key in ("active_task_set", "task_set_id"):
        for match in re.finditer(rf"(?m)^\s*{key}:\s*[\"']?(TASKSET-[A-Z0-9-]+)", text):
            taskset_id = match.group(1)
            if not board_text or taskset_id not in board_text:
                findings.append(
                    Finding(
                        "watch",
                        "pointer-board-mismatch",
                        POINTER_PATH,
                        f"{key} {taskset_id} does not appear in {BOARD_PATH}",
                    )
                )

    for rel in sorted(set(POINTER_TASK_FILE_RE.findall(text))):
        if not (root / rel).exists():
            findings.append(
                Finding(
                    "watch",
                    "pointer-task-file-missing",
                    POINTER_PATH,
                    f"pointer references missing task file {rel}",
                )
            )


def analyze(root: Path) -> tuple[list[Path], list[Finding]]:
    root = root.resolve()
    findings: list[Finding] = []
    board_text = _read(root / BOARD_PATH)
    records = _planning_records(root)
    for path in records:
        _audit_record(root, path, board_text, findings)
    _audit_pointer(root, board_text, findings)
    deduped = sorted(set(findings), key=lambda f: (f.severity != "block", f.kind, f.path, f.detail))
    return records, deduped


def render(root: Path, records: list[Path], findings: list[Finding]) -> str:
    block_count = sum(1 for finding in findings if finding.severity == "block")
    watch_count = len(findings) - block_count
    status = "block" if block_count else ("watch" if watch_count else "pass")
    lines = [
        f"conversation-work-audit: {status}",
        f"root={root.resolve()}",
        f"planning_records={len(records)}",
        f"findings={len(findings)} block={block_count} watch={watch_count}",
    ]
    for finding in findings:
        lines.append(f"- {finding.severity} {finding.kind} {finding.path}: {finding.detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit conversation-to-work traceability for planning records")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--check", action="store_true", help="Exit nonzero when block findings exist")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    records, findings = analyze(args.root)
    print(render(args.root, records, findings))
    if args.check and any(finding.severity == "block" for finding in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
