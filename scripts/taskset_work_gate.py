"""Validate task-set routing rules for backlog and parallel pane work."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import backlog_board


ACTIVE_CLAIM_STATUSES = {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}
DONE_TASK_STATUSES = {"completed", "done", "released"}

# Board fields derived from the current wall clock rather than from task/claim
# records. They drift with the passage of time even when no record changed, so
# the freshness comparison masks them on both sides. Record-derived fields
# (task rows, lane counts, WIP `active` counts) stay unmasked so real
# staleness — task add/remove, status change, claim change — is still caught.
_WALL_CLOCK_GENERATED_AT = re.compile(r"^generated_at: \d{4}-\d{2}-\d{2}$", re.MULTILINE)
_WALL_CLOCK_WIP = re.compile(
    r"^(- WIP: active `[^`\n]*`; oldest `)[0-9.]+h(`; stale `)\d+(`\.)$",
    re.MULTILINE,
)


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


def _mask_wall_clock_fields(text: str) -> str:
    """Mask wall-clock derived tokens so only record changes affect freshness."""
    text = _WALL_CLOCK_GENERATED_AT.sub("generated_at: <wall-clock>", text)
    text = _WALL_CLOCK_WIP.sub(r"\g<1><wall-clock>\g<2><wall-clock>\g<3>", text)
    return text


def _backlog_board_is_fresh(root: Path, board: Path, tasks: list[backlog_board.Task]) -> bool:
    generated = backlog_board.render(tasks, root=root)
    try:
        existing = board.read_text(encoding="utf-8")
    except OSError:
        return False
    return _mask_wall_clock_fields(_normalize(existing)) == _mask_wall_clock_fields(_normalize(generated))


def _load_claims(root: Path) -> list[dict]:
    claims_dir = root / "agents" / "runtime" / "task_claims"
    claims: list[dict] = []
    if not claims_dir.exists():
        return claims
    for path in sorted(claims_dir.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            claims.append({"_path": path, "_load_error": str(exc)})
            continue
        if isinstance(value, dict):
            value["_path"] = path
            claims.append(value)
    return claims


def check_root(root: Path, task_set_id: str = "", require_complete: bool = False) -> list[str]:
    root = root.resolve()
    findings: list[str] = []
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks = backlog_board.load_tasks(tasks_dir)

    for task in tasks:
        raw_task_set = str(task.meta.get("task_set_id") or "").strip()
        if not raw_task_set:
            findings.append(f"{_rel(root, task.path)}: taskset:missing-task-set-id:{task.task_id}")

    if require_complete:
        if not task_set_id:
            findings.append("taskset:require-complete-missing-task-set-id")
        else:
            matching_tasks = [task for task in tasks if str(task.meta.get("task_set_id") or "").strip() == task_set_id]
            if not matching_tasks:
                findings.append(f"taskset:no-tasks-for-task-set:{task_set_id}")
            for task in matching_tasks:
                status = str(task.meta.get("status") or "").strip()
                if status not in DONE_TASK_STATUSES:
                    findings.append(
                        f"{_rel(root, task.path)}: taskset:incomplete-task:{task_set_id}:{task.task_id}:{status or 'missing-status'}"
                    )

            for claim in _load_claims(root):
                claim_path = claim.get("_path")
                if claim.get("_load_error"):
                    path_text = _rel(root, claim_path) if isinstance(claim_path, Path) else "unknown-claim"
                    findings.append(f"{path_text}: taskset:claim-json-invalid:{claim['_load_error']}")
                    continue
                if str(claim.get("task_set_id") or "").strip() != task_set_id:
                    continue
                claim_id = str(claim.get("claim_id") or "unknown-claim")
                status = str(claim.get("status") or "").strip()
                phase = str(claim.get("phase") or "").strip()
                progress = claim.get("progress_pct")
                path_text = _rel(root, claim_path) if isinstance(claim_path, Path) else claim_id
                if status in ACTIVE_CLAIM_STATUSES:
                    findings.append(f"{path_text}: taskset:active-claim:{task_set_id}:{claim_id}:{status}")
                if status in DONE_TASK_STATUSES:
                    if phase != "taskset-completed":
                        findings.append(f"{path_text}: taskset:released-claim-phase-not-complete:{task_set_id}:{claim_id}:{phase}")
                    try:
                        progress_value = int(progress)
                    except (TypeError, ValueError):
                        progress_value = -1
                    if progress_value != 100:
                        findings.append(
                            f"{path_text}: taskset:released-claim-progress-not-100:{task_set_id}:{claim_id}:{progress}"
                        )

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
    parser.add_argument("--task-set-id", default="", help="Task set to check for set-specific completion")
    parser.add_argument("--require-complete", action="store_true", help="Fail unless every task and claim in --task-set-id is complete")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings = check_root(root, task_set_id=args.task_set_id, require_complete=args.require_complete)
    status = "fail" if findings else "pass"
    print(f"taskset-work-gate: {status}")
    print(f"root={root}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
