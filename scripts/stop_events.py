"""Stop-reason instrumentation for goal loops, claim recovery, and supervision.

Foundation module (Phase 1) for deadlock recovery and goal auto-resume. Every
place that can halt autonomous work records a classified *stop event* here, so
the *appropriate* auto-resume cap can be judged later from real data instead of
guessed now.

Two classes:
  - ``recoverable``  accidental stalls that are safe to auto-recover or resume
                     (dirty worktree on a feature branch, a dead worker's stale
                     claim, an expired lease, a transient iteration error).
  - ``intentional``  deliberate safety guards that MUST be preserved and never
                     auto-overridden (hard iteration cap, max-failures halt,
                     emergency stop file, owner-governance block, plan-assumption
                     drift, footprint conflict, taskset boundary completion,
                     dirty worktree on the main checkout).

Events append to ``agents/runtime/events/stop_events-{date}.jsonl``; a rolling
aggregate lives in ``agents/runtime/stop_counters.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_EVENT = "agent-runtime-stop-event/v1"
SCHEMA_COUNTERS = "agent-runtime-stop-counters/v1"

EVENTS_DIR_REL = "agents/runtime/events"
COUNTERS_REL = "agents/runtime/stop_counters.json"

# reason_code -> class. Callers pass a reason_code; classification is centralized
# so the recoverable/intentional split stays consistent across modules.
RECOVERABLE_REASONS = {
    "dirty_worktree",   # uncommitted changes on a feature branch (checkpointable)
    "dead_claim",       # worker process/pane died; claim stuck in an active status
    "lease_expired",    # claim lease TTL elapsed with no heartbeat
    "transient_error",  # one iteration raised; backoff+retry is safe
}
INTENTIONAL_REASONS = {
    "max_iterations",          # agent_loop hard/explicit iteration cap
    "max_failures",            # repeated failures halt (runaway guard)
    "emergency_stop",          # STOP_LOOP present
    "orchestrator_stop",       # .orchestrator-stop emergency stop
    "owner_governance_block",  # Stop-hook owner governance gate refused
    "plan_assumption_drift",   # T2 dispatch gate
    "footprint_conflict",      # overlapping target_files
    "taskset_boundary",        # taskset completed; stop-and-report
    "dirty_worktree_main",     # uncommitted changes on the main checkout (never auto-commit)
}

ACTIONS = {
    "stopped",              # work halted
    "reaped",               # dead claim recovered -> expired
    "skipped",              # could not safely act; left as-is and continued
    "resumed",              # goal loop re-armed
    "checkpointed",         # dirty worktree committed as wip; loop continued
    "restart_cap_reached",  # auto-resume cap hit; no further restart
}


def classify(reason_code: str) -> str:
    code = str(reason_code or "").strip()
    if code in RECOVERABLE_REASONS:
        return "recoverable"
    if code in INTENTIONAL_REASONS:
        return "intentional"
    return "unknown"


def _parse_now(value: str | None = None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).astimezone()
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _coerce_now(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        return value
    return _parse_now(value)


def events_path(root: Path, *, now: str | datetime | None = None) -> Path:
    moment = _coerce_now(now)
    return Path(root) / EVENTS_DIR_REL / f"stop_events-{moment.date().isoformat()}.jsonl"


def counters_path(root: Path) -> Path:
    return Path(root) / COUNTERS_REL


try:  # bare import when run as a script (scripts/ on sys.path); package path under pytest
    import atomic_io
except ModuleNotFoundError:  # pragma: no cover
    from scripts import atomic_io


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    # Shared durable primitive: temp -> fsync -> atomic rename (TASK crash-recovery).
    atomic_io.write_json_atomic(path, payload, sort_keys=True)


def _empty_counters() -> dict[str, Any]:
    return {
        "schema": SCHEMA_COUNTERS,
        "updated_at": "",
        "by_class": {},
        "by_action": {},
        "by_reason": {},
        "goal_restarts": {},  # goal text -> resume count, for cap tuning
    }


def load_counters(root: Path) -> dict[str, Any]:
    path = counters_path(root)
    if not path.exists():
        return _empty_counters()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_counters()
    if not isinstance(payload, dict):
        return _empty_counters()
    base = _empty_counters()
    base.update(payload)
    for key in ("by_class", "by_action", "by_reason", "goal_restarts"):
        if not isinstance(base.get(key), dict):
            base[key] = {}
    return base


def _bump(bucket: dict[str, Any], key: str, amount: int = 1) -> None:
    if not key:
        return
    bucket[key] = int(bucket.get(key, 0)) + amount


def bump_counter(
    root: Path,
    *,
    reason_code: str,
    action: str,
    klass: str,
    goal: str | None = None,
    now: str | datetime | None = None,
) -> dict[str, Any]:
    moment = _coerce_now(now)
    counters = load_counters(root)
    _bump(counters["by_class"], klass)
    _bump(counters["by_action"], action)
    _bump(counters["by_reason"], reason_code)
    if action == "resumed" and goal:
        _bump(counters["goal_restarts"], goal)
    counters["schema"] = SCHEMA_COUNTERS
    counters["updated_at"] = moment.isoformat(timespec="seconds")
    _write_json_atomic(counters_path(root), counters)
    return counters


def record_stop_event(
    root: Path,
    *,
    source: str,
    reason_code: str,
    action: str,
    klass: str | None = None,
    goal: str | None = None,
    claim_id: str = "",
    task_id: str = "",
    iteration: int | None = None,
    restart_count: int | None = None,
    message: str = "",
    now: str | datetime | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Append one classified stop event and bump the rolling counters.

    ``klass`` defaults to :func:`classify` of ``reason_code`` but can be
    overridden (e.g. a dirty worktree is recoverable on a feature branch but
    intentional on main).
    """
    root = Path(root).resolve()
    moment = _coerce_now(now)
    resolved_class = klass or classify(reason_code)
    event: dict[str, Any] = {
        "schema": SCHEMA_EVENT,
        "ts": moment.isoformat(timespec="seconds"),
        "source": source,
        "reason_code": reason_code,
        "class": resolved_class,
        "action": action,
        "goal": goal or "",
        "claim_id": claim_id,
        "task_id": task_id,
        "iteration": iteration,
        "restart_count": restart_count,
        "message": message,
    }
    for key, value in extra.items():
        if value not in (None, ""):
            event[key] = value
    path = events_path(root, now=moment)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    bump_counter(
        root, reason_code=reason_code, action=action,
        klass=resolved_class, goal=goal, now=moment,
    )
    return event


def load_events(root: Path, *, now: str | datetime | None = None) -> list[dict[str, Any]]:
    path = events_path(root, now=now)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def summarize(root: Path) -> dict[str, Any]:
    counters = load_counters(root)
    return {
        "by_class": counters.get("by_class", {}),
        "by_action": counters.get("by_action", {}),
        "by_reason": counters.get("by_reason", {}),
        "goal_restarts": counters.get("goal_restarts", {}),
        "updated_at": counters.get("updated_at", ""),
    }


# --------------------------------------------------------------------------- CLI


def cmd_record(args: argparse.Namespace) -> int:
    event = record_stop_event(
        args.root,
        source=args.source,
        reason_code=args.reason_code,
        action=args.action,
        klass=args.klass or None,
        goal=args.goal or None,
        claim_id=args.claim_id,
        task_id=args.task_id,
        message=args.message,
        now=args.now,
    )
    if args.json:
        print(json.dumps(event, ensure_ascii=False, indent=2))
    else:
        print(f"stop-events: recorded {event['reason_code']} [{event['class']}] action={event['action']}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    payload = summarize(args.root)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        by_action = payload["by_action"]
        print("stop-events: " + (", ".join(f"{k}={v}" for k, v in sorted(by_action.items())) or "no events"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record/aggregate classified stop events")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record", help="Append one classified stop event")
    record.add_argument("--source", required=True, help="agent_loop | claim_reaper | goal_supervisor")
    record.add_argument("--reason-code", dest="reason_code", required=True)
    record.add_argument("--action", required=True)
    record.add_argument("--klass", default="", help="override class (recoverable|intentional)")
    record.add_argument("--goal", default="")
    record.add_argument("--claim-id", dest="claim_id", default="")
    record.add_argument("--task-id", dest="task_id", default="")
    record.add_argument("--message", default="")
    record.add_argument("--now")
    record.add_argument("--json", action="store_true")
    record.set_defaults(func=cmd_record)

    summary = sub.add_parser("summary", help="Show rolling stop counters")
    summary.add_argument("--json", action="store_true")
    summary.set_defaults(func=cmd_summary)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001 - CLI surface, never traceback
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
