"""Detect — and loudly surface — an agent loop that was interrupted by a crash.

Why this exists: a clean stop appends a ``loop_stop`` event and writes a
``stopped`` heartbeat. A hard crash (power loss, OOM kill, terminal closed)
writes *neither* — the last ``loop_start`` simply has no matching ``loop_stop``.
``goal_supervisor.latest_goal_run`` reads that as ``stopped=False`` and cannot
tell "still running" from "crashed", and nothing reads the heartbeat. So after a
hard shutdown a new session has no automatic signal that a run was abandoned.

This detector closes that gap. It is **detection only** — it never resumes or
spawns anything. Wired into the SessionStart hook chain, it prints a clear
"이 실행이 중단된 것으로 보입니다 + 재개 명령" block whenever it can prove the prior
loop is gone, so the operator (or a later supervisor run) knows exactly where to
pick up.

Proof of "gone" = there is an in-flight run (a ``loop_start`` with no following
``loop_stop`` today) AND either the heartbeat's recorded PID is no longer alive,
or — when no PID is available — the last recorded activity is older than the
staleness window (default 600s, env ``AGENT_RUNTIME_INTERRUPT_STALE_SECONDS``).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

EVENTS_DIR_REL = Path("agents/runtime/events")
HEARTBEAT_REL = Path("agents/runtime/heartbeat.json")

TERMINAL_EVENTS = {"loop_stop", "loop_halt_max_failures"}
TERMINAL_HB_STATUSES = {"stopped"}
DEFAULT_STALE_SECONDS = 600
STALE_ENV = "AGENT_RUNTIME_INTERRUPT_STALE_SECONDS"

KST = timezone(timedelta(hours=9))


def default_stale_seconds() -> int:
    raw = os.environ.get(STALE_ENV, "").strip()
    if not raw:
        return DEFAULT_STALE_SECONDS
    try:
        return max(0, int(raw))
    except ValueError:
        return DEFAULT_STALE_SECONDS


def _coerce_now(now: str | datetime | None) -> datetime:
    if isinstance(now, datetime):
        moment = now
    elif isinstance(now, str) and now.strip():
        moment = datetime.fromisoformat(now)
    else:
        moment = datetime.now(KST)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=KST)
    return moment


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=KST)
    return moment


def _read_heartbeat(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _latest_inflight_run(events_dir: Path, date: str) -> dict[str, Any] | None:
    """Return the last ``loop_start`` that has no following terminal event today.

    Returns ``{goal, mode, iteration, ts}`` for an in-flight run, or ``None`` when
    there is no run or the last run stopped cleanly.
    """
    path = events_dir / f"agent_loop-{date}.jsonl"
    if not path.exists():
        return None
    events: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return None

    start_idx: int | None = None
    for index, event in enumerate(events):
        if event.get("event") == "loop_start":
            start_idx = index
    if start_idx is None:
        return None

    tail = events[start_idx + 1:]
    if any(event.get("event") in TERMINAL_EVENTS for event in tail):
        return None  # last run stopped cleanly

    start = events[start_idx]
    iteration: int | None = None
    last_ts = _parse_ts(start.get("ts"))
    for event in tail:
        if isinstance(event.get("iteration"), int):
            iteration = event["iteration"]
        ts = _parse_ts(event.get("ts"))
        if ts is not None:
            last_ts = ts
    return {
        "goal": start.get("goal"),
        "mode": start.get("mode") or "build",
        "iteration": iteration,
        "ts": last_ts.isoformat() if last_ts else None,
    }


def _pid_alive(pid: Any) -> bool:
    """Best-effort liveness probe. Conservative: unknown => alive (avoid false alarms)."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        ERROR_ACCESS_DENIED = 5
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            # No handle: access-denied means the process exists; anything else
            # (invalid parameter) means it's gone.
            return kernel32.GetLastError() == ERROR_ACCESS_DENIED
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True  # cannot determine -> assume alive
            return code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return True
    return True


def _last_activity_ts(hb: dict[str, Any] | None, run: dict[str, Any] | None) -> datetime | None:
    if hb is not None:
        ts = _parse_ts(hb.get("ts"))
        if ts is not None:
            return ts
    if run is not None:
        return _parse_ts(run.get("ts"))
    return None


def detect(
    root: Path,
    *,
    now: str | datetime | None = None,
    pid_alive: Callable[[Any], bool] | None = None,
    stale_seconds: int | None = None,
    heartbeat_file: Path | None = None,
) -> dict[str, Any] | None:
    """Return interruption details, or ``None`` when no interrupted run is provable."""
    root = Path(root)
    moment = _coerce_now(now)
    stale = default_stale_seconds() if stale_seconds is None else int(stale_seconds)
    alive_fn = pid_alive or _pid_alive

    hb = _read_heartbeat(heartbeat_file or (root / HEARTBEAT_REL))
    run = _latest_inflight_run(root / EVENTS_DIR_REL, moment.date().isoformat())

    hb_inflight = hb is not None and str(hb.get("status")) not in TERMINAL_HB_STATUSES
    log_inflight = run is not None
    if not (hb_inflight or log_inflight):
        return None

    pid: int | None = None
    if hb is not None and hb.get("pid") is not None:
        try:
            pid = int(hb["pid"])
        except (TypeError, ValueError):
            pid = None

    alive: bool | None = None
    if pid is not None:
        alive = alive_fn(pid)
        if alive:
            return None  # process still running -> not interrupted
    else:
        last_ts = _last_activity_ts(hb, run)
        if last_ts is None:
            return None  # cannot prove staleness; don't false-alarm
        if (moment - last_ts).total_seconds() < stale:
            return None  # too fresh; likely still running

    goal = (run or {}).get("goal")
    mode = (run or {}).get("mode") or (hb or {}).get("mode") or "build"
    iteration = (run or {}).get("iteration")
    if iteration is None and hb is not None:
        iteration = hb.get("iteration")
    last_ts = _last_activity_ts(hb, run)
    age = int((moment - last_ts).total_seconds()) if last_ts else None

    resume_command = _resume_command(mode, goal)
    return {
        "interrupted": True,
        "goal": goal,
        "mode": mode,
        "iteration": iteration,
        "last_activity": last_ts.isoformat() if last_ts else None,
        "age_seconds": age,
        "pid": pid,
        "pid_alive": alive,
        "source": "heartbeat" if (hb_inflight and not log_inflight) else ("event_log" if (log_inflight and hb is None) else "both"),
        "resume_command": resume_command,
        "supervisor_command": "python scripts/goal_supervisor.py --apply",
    }


def _resume_command(mode: str, goal: str | None) -> str:
    if goal:
        return f'python scripts/agent_loop.py --mode {mode} --goal "{goal}" --checkpoint-dirty'
    return "python scripts/agent_loop.py --checkpoint-dirty   # (goal unknown — see event log)"


def format_report(info: dict[str, Any]) -> str:
    age = info.get("age_seconds")
    age_str = f"{age}s" if age is not None else "?"
    pid = info.get("pid")
    alive = info.get("pid_alive")
    if pid is None:
        pid_str = "기록 없음"
    else:
        pid_str = f"{pid} ({'실행 중' if alive else '종료됨'})"
    lines = [
        "⚠️  직전 agent loop 실행이 중단된 것으로 보입니다 (PC 비정상 종료 가능).",
        f"     goal       : {info.get('goal') or '(알 수 없음)'}",
        f"     mode       : {info.get('mode')}",
        f"     마지막 활동: iteration {info.get('iteration')} @ {info.get('last_activity')} ({age_str} 경과)",
        f"     heartbeat  : pid {pid_str}",
        f"     재개(자동) : {info.get('supervisor_command')}",
        f"     재개(수동) : {info.get('resume_command')}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect an interrupted (crashed) agent loop")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--stale-seconds", type=int, default=None)
    parser.add_argument("--heartbeat-file", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        info = detect(
            args.root.resolve(),
            stale_seconds=args.stale_seconds,
            heartbeat_file=args.heartbeat_file,
        )
    except Exception as exc:  # noqa: BLE001 — a detector must never break session start
        if args.json:
            print(json.dumps({"interrupted": False, "error": repr(exc)}, ensure_ascii=False))
        return 0

    if info is None:
        if args.json:
            print(json.dumps({"interrupted": False}, ensure_ascii=False))
        return 0

    print(json.dumps(info, ensure_ascii=False) if args.json else format_report(info))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
