"""One-shot deadlock watchdog: reap dead claims + auto-resume stopped goal loops.

A single, scheduler-independent entry point meant to be run periodically (Windows
Task Scheduler, cron, or the harness ``/loop`` / ``schedule``). One cycle:

  1. ``claim_reaper.sweep``      — recover provably-dead claims (break wave deadlocks)
  2. ``goal_supervisor.supervise`` — re-arm a stopped-but-incomplete goal loop

Each step is individually best-effort (a failure in one never blocks the other)
and safe by construction (dry-run by default; provably-dead claims only;
restart-capped resume). Schedule it with ``--apply`` to actually act:

  python scripts/deadlock_watchdog.py --apply        # one cycle, acting
  python scripts/deadlock_watchdog.py                # dry-run report

Relevant env: AGENT_RUNTIME_REAPER_GRACE_SECONDS, AGENT_RUNTIME_GOAL_MAX_RESTARTS.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable


def run_cycle(
    root: Path,
    *,
    apply: bool = False,
    now: str | None = None,
    grace_seconds: int | None = None,
    max_restarts: int | None = None,
    runner: Callable[[list[str], Path], tuple[int, str]] | None = None,
) -> dict[str, Any]:
    import claim_reaper

    if grace_seconds is not None:
        claim_reaper.claim_store.require_duration(
            grace_seconds,
            field="grace_seconds",
            minimum=0,
        )

    import goal_supervisor

    report: dict[str, Any] = {"apply": apply}
    try:
        report["reaper"] = claim_reaper.sweep(
            root, now=now, apply=apply, grace_seconds=grace_seconds
        )
    except Exception as exc:  # noqa: BLE001 - step isolation
        report["reaper"] = {"error": repr(exc)}
    try:
        report["supervisor"] = goal_supervisor.supervise(
            root, now=now, apply=apply, max_restarts=max_restarts, runner=runner
        )
    except Exception as exc:  # noqa: BLE001 - step isolation
        report["supervisor"] = {"error": repr(exc)}
    return report


def _summary_line(report: dict[str, Any]) -> str:
    reaper = report.get("reaper", {})
    supervisor = report.get("supervisor", {})
    reaped = reaper.get("reaped") if report.get("apply") else reaper.get("would_reap")
    return (
        "deadlock-watchdog: "
        + ("apply" if report.get("apply") else "dry-run")
        + f" | claims {'reaped' if report.get('apply') else 'would-reap'}={len(reaped or [])}"
        + f" live={len(reaper.get('live', []))} skipped={len(reaper.get('skipped', []))}"
        # Claims no automated path can end. This watchdog exists to break wave
        # deadlocks, so it is the one place that must not stay quiet about them.
        + f" needs_owner_recovery={len(reaper.get('needs_owner_recovery', []))}"
        # A torn lease is the same class: never reapable, and not terminalizable
        # while the later deadline stands. Splitting it out of
        # needs_owner_recovery silently dropped it from this line, which is the
        # one place a scheduled run surfaces anything.
        + f" torn_lease={len(reaper.get('torn_lease', []))}"
        + f" | goal action={supervisor.get('action')}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="One-shot deadlock watchdog (reaper + goal supervisor)")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--apply", action="store_true", help="act (default: dry-run report)")
    parser.add_argument("--grace-seconds", type=int, default=None)
    parser.add_argument("--max-restarts", type=int, default=None)
    parser.add_argument("--now", help="ISO timestamp override (testing/determinism)")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run_cycle(
            args.root,
            apply=args.apply,
            now=args.now,
            grace_seconds=args.grace_seconds,
            max_restarts=args.max_restarts,
        )
    except ValueError as exc:
        print(f"deadlock-watchdog: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_summary_line(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
