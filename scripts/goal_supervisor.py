"""Detect a stopped-but-incomplete goal loop and auto-resume it within guardrails.

Reads the agent_loop event log + heartbeat to find the most recent ``--goal`` run
and why it stopped, classifies the stop, and — only for *resumable* stops and only
under a restart cap — re-arms the loop. Every decision is recorded through
``stop_events`` (and each resume bumps a per-goal counter) so the *appropriate*
restart cap can be judged later from real data instead of guessed now.

Resumability vs. safety class are deliberately separate:
  - ``recoverable`` stops (dirty worktree, transient error, ...) are resumable;
  - ``max_iterations`` is an *intentional per-run cap* but still resumable — each
    resume is itself a fresh hard-capped run, and the NUMBER of resumes is what the
    restart cap bounds and the counters track;
  - ``max_failures`` / emergency / orchestrator stops are intentional AND
    non-resumable — the supervisor never overrides them.

Guardrails: dry-run by default (no resume, no writes); resume is bounded by
``--max-restarts`` (env ``AGENT_RUNTIME_GOAL_MAX_RESTARTS``, default 3); a resume
re-arms agent_loop with ``--checkpoint-dirty`` so the next round self-heals a dirty
worktree instead of stalling again.

Usage:
  python scripts/goal_supervisor.py                 # dry-run: classify + decide
  python scripts/goal_supervisor.py --apply         # resume if safe and under cap
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import stop_events

EVENTS_DIR_REL = "agents/runtime/events"
DEFAULT_MAX_RESTARTS = 3
MAX_RESTARTS_ENV = "AGENT_RUNTIME_GOAL_MAX_RESTARTS"

# max_iterations is intentional-but-resumable; the recoverable reasons are resumable.
RESUMABLE_REASONS = set(stop_events.RECOVERABLE_REASONS) | {"max_iterations"}


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


def default_max_restarts() -> int:
    raw = os.environ.get(MAX_RESTARTS_ENV)
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            pass
    return DEFAULT_MAX_RESTARTS


def reason_to_code(reason: str) -> str:
    """Map an agent_loop stop ``reason`` string to a stop_events reason_code."""
    text = str(reason or "").strip().lower()
    if "max_iterations" in text:
        return "max_iterations"
    if "max_failures" in text:
        return "max_failures"
    if "orchestrator emergency stop" in text:
        return "orchestrator_stop"
    if "stop file" in text:
        return "emergency_stop"
    if "dirty worktree" in text:
        return "dirty_worktree"
    return "unknown"


def is_resumable(reason_code: str) -> bool:
    return reason_code in RESUMABLE_REASONS


def latest_goal_run(root: Path, now: str | datetime | None = None) -> dict[str, Any] | None:
    """Return the most recent goal run from today's agent_loop event log.

    Returns ``{goal, mode, stopped, reason}`` or ``None`` when there is no goal run
    to supervise.
    """
    moment = _coerce_now(now)
    path = Path(root) / EVENTS_DIR_REL / f"agent_loop-{moment.date().isoformat()}.jsonl"
    if not path.exists():
        return None
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    start_idx: int | None = None
    for index, event in enumerate(events):
        if event.get("event") == "loop_start":
            start_idx = index
    if start_idx is None:
        return None
    last_start = events[start_idx]
    reason = ""
    stopped = False
    for event in events[start_idx + 1:]:
        name = event.get("event")
        if name == "loop_halt_max_failures":
            reason, stopped = "max_failures reached", True
        elif name == "loop_stop":
            reason, stopped = str(event.get("reason") or ""), True
    return {
        "goal": last_start.get("goal"),
        "mode": last_start.get("mode") or "build",
        "stopped": stopped,
        "reason": reason,
    }


def restart_count(root: Path, goal: str) -> int:
    return int(stop_events.summarize(root).get("goal_restarts", {}).get(goal, 0))


def _resume_command(root: Path, mode: str, goal: str) -> list[str]:
    return [
        sys.executable or "python",
        str(Path(root) / "scripts" / "agent_loop.py"),
        "--mode", mode or "build",
        "--goal", goal,
        "--explicit-auth",
        "--checkpoint-dirty",
    ]


def _default_runner(cmd: list[str], root: Path) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd, cwd=str(root), capture_output=True, text=True,
            timeout=900, encoding="utf-8", errors="replace",
        )
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except Exception as exc:  # noqa: BLE001
        return 1, repr(exc)


def supervise(
    root: Path,
    *,
    now: str | datetime | None = None,
    apply: bool = False,
    max_restarts: int | None = None,
    runner: Callable[[list[str], Path], tuple[int, str]] | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    moment = _coerce_now(now)
    cap = default_max_restarts() if max_restarts is None else int(max_restarts)
    report: dict[str, Any] = {
        "now": moment.isoformat(timespec="seconds"),
        "max_restarts": cap,
        "apply": apply,
        "action": "none",
        "goal": None,
        "reason_code": None,
        "restart_count": 0,
        "detail": "",
    }

    run = latest_goal_run(root, moment)
    if run is None or not run.get("goal"):
        report["detail"] = "no goal run found"
        return report
    report["goal"] = run["goal"]
    if not run["stopped"]:
        report["detail"] = "goal loop still running"
        return report

    goal = str(run["goal"])
    reason_code = reason_to_code(run["reason"])
    count = restart_count(root, goal)
    report.update(reason_code=reason_code, restart_count=count, stop_reason=run["reason"])

    if not is_resumable(reason_code):
        report["action"] = "halt"
        report["detail"] = f"intentional stop ({reason_code}); not resuming"
        if apply:
            stop_events.record_stop_event(
                root, source="goal_supervisor", reason_code=reason_code,
                action="stopped", goal=goal, now=moment,
                message="intentional stop; not resuming",
            )
        return report

    if count >= cap:
        report["action"] = "cap"
        report["detail"] = f"restart cap reached ({count}/{cap})"
        if apply:
            stop_events.record_stop_event(
                root, source="goal_supervisor", reason_code=reason_code,
                action="restart_cap_reached", goal=goal, restart_count=count, now=moment,
                message=f"max_restarts={cap} reached",
            )
        return report

    report["action"] = "resume"
    report["detail"] = f"resuming goal (restart {count + 1}/{cap})"
    if apply:
        cmd = _resume_command(root, run["mode"], goal)
        run_fn = runner or _default_runner
        rc, detail = run_fn(cmd, root)
        report["resume_rc"] = rc
        report["resume_detail"] = detail[:200]
        stop_events.record_stop_event(
            root, source="goal_supervisor", reason_code=reason_code,
            action="resumed", goal=goal, restart_count=count + 1, now=moment,
            message=f"re-armed via agent_loop (mode={run['mode']}, rc={rc})",
        )
    return report


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auto-resume a stopped-but-incomplete goal loop within guardrails."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--apply", action="store_true", help="perform the resume (default: dry-run)")
    parser.add_argument("--max-restarts", type=int, default=None,
                        help=f"resume cap (default {DEFAULT_MAX_RESTARTS} or ${MAX_RESTARTS_ENV})")
    parser.add_argument("--now", help="ISO timestamp override (testing/determinism)")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = supervise(args.root, now=args.now, apply=args.apply, max_restarts=args.max_restarts)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"goal-supervisor: action={report['action']} goal={report['goal']!r} "
              f"reason={report.get('reason_code')} restarts={report['restart_count']}/{report['max_restarts']}")
        if report["detail"]:
            print(f"  {report['detail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
