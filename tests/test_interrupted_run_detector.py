"""Tests for interrupted_run_detector — surface an interrupted run on the next session.

The detector is *detection only* (it never spawns or resumes anything). It answers:
"did the previous agent loop die without a clean stop?" by combining the append-only
event log (a ``loop_start`` with no following ``loop_stop``) with the heartbeat
(pid liveness + staleness). ``pid_alive`` is injected so the tests are deterministic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import interrupted_run_detector as ird  # noqa: E402

NOW = "2026-06-21T12:00:00+09:00"
DATE = "2026-06-21"
GOAL = "ship the feature"

DEAD = lambda pid: False  # noqa: E731
ALIVE = lambda pid: True  # noqa: E731


def _write_events(tmp_path: Path, lines: list[dict], date: str = DATE) -> None:
    path = tmp_path / "agents" / "runtime" / "events" / f"agent_loop-{date}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")


def _write_heartbeat(tmp_path: Path, record: dict) -> None:
    path = tmp_path / "agents" / "runtime" / "heartbeat.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


def test_clean_repo_returns_none(tmp_path):
    assert ird.detect(tmp_path, now=NOW, pid_alive=DEAD) is None


def test_completed_run_not_flagged(tmp_path):
    _write_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build", "ts": "2026-06-21T11:00:00+09:00"},
        {"event": "loop_stop", "iteration": 3, "reason": "max_iterations reached (3)", "ts": "2026-06-21T11:30:00+09:00"},
    ])
    assert ird.detect(tmp_path, now=NOW, pid_alive=DEAD) is None


def test_inflight_with_dead_pid_is_flagged(tmp_path):
    _write_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build", "ts": "2026-06-21T11:00:00+09:00"},
        {"event": "iteration_done", "iteration": 3, "ts": "2026-06-21T11:50:00+09:00"},
    ])
    _write_heartbeat(tmp_path, {"ts": "2026-06-21T11:50:00+09:00", "iteration": 3,
                                "status": "iteration_done", "pid": 999999, "mode": "build"})
    info = ird.detect(tmp_path, now=NOW, pid_alive=DEAD)
    assert info is not None
    assert info["goal"] == GOAL
    assert info["iteration"] == 3
    assert info["pid_alive"] is False
    assert "--checkpoint-dirty" in info["resume_command"]


def test_inflight_with_live_pid_not_flagged(tmp_path):
    _write_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build", "ts": "2026-06-21T11:00:00+09:00"},
        {"event": "iteration_done", "iteration": 3, "ts": "2026-06-21T11:50:00+09:00"},
    ])
    _write_heartbeat(tmp_path, {"ts": "2026-06-21T11:50:00+09:00", "iteration": 3,
                                "status": "iteration_done", "pid": 4242, "mode": "build"})
    # pid still alive => the loop is simply still running, not interrupted.
    assert ird.detect(tmp_path, now=NOW, pid_alive=ALIVE) is None


def test_inflight_no_heartbeat_stale_is_flagged(tmp_path):
    # No heartbeat (or a heartbeat-less loop): fall back to staleness of last activity.
    _write_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build", "ts": "2026-06-21T09:00:00+09:00"},
        {"event": "iteration_done", "iteration": 2, "ts": "2026-06-21T09:05:00+09:00"},
    ])
    info = ird.detect(tmp_path, now=NOW, pid_alive=DEAD, stale_seconds=600)
    assert info is not None
    assert info["goal"] == GOAL


def test_inflight_no_heartbeat_fresh_not_flagged(tmp_path):
    # Last activity 1 minute ago and no pid to probe => assume still running.
    _write_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build", "ts": "2026-06-21T11:58:00+09:00"},
        {"event": "iteration_done", "iteration": 1, "ts": "2026-06-21T11:59:00+09:00"},
    ])
    assert ird.detect(tmp_path, now=NOW, pid_alive=DEAD, stale_seconds=600) is None


def test_heartbeat_stopped_no_inflight_log_not_flagged(tmp_path):
    _write_heartbeat(tmp_path, {"ts": "2026-06-21T11:50:00+09:00", "iteration": 5,
                                "status": "stopped", "pid": 999999, "mode": "build"})
    assert ird.detect(tmp_path, now=NOW, pid_alive=DEAD) is None


def test_report_is_human_readable(tmp_path):
    _write_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build", "ts": "2026-06-21T11:00:00+09:00"},
        {"event": "iteration_done", "iteration": 3, "ts": "2026-06-21T11:50:00+09:00"},
    ])
    _write_heartbeat(tmp_path, {"ts": "2026-06-21T11:50:00+09:00", "iteration": 3,
                                "status": "iteration_done", "pid": 999999, "mode": "build"})
    info = ird.detect(tmp_path, now=NOW, pid_alive=DEAD)
    report = ird.format_report(info)
    assert GOAL in report
    assert "agent_loop.py" in report


def test_pid_alive_self_is_true_and_bogus_is_false():
    import os
    assert ird._pid_alive(os.getpid()) is True
    # An almost-certainly-unused high PID should read as dead on every platform.
    assert ird._pid_alive(2_000_000_000) is False


def test_main_clean_exits_zero(tmp_path, capsys):
    rc = ird.main(["--root", str(tmp_path)])
    assert rc == 0
