"""Tests for goal_supervisor — classify a stopped goal loop and resume within guardrails."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import goal_supervisor  # noqa: E402
import stop_events  # noqa: E402

NOW = "2026-06-14T12:00:00+09:00"
GOAL = "ship the feature"


def _write_loop_events(tmp_path: Path, lines: list[dict], date: str = "2026-06-14") -> None:
    path = tmp_path / "agents" / "runtime" / "events" / f"agent_loop-{date}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")


def test_reason_to_code_mapping():
    assert goal_supervisor.reason_to_code("max_iterations reached (5)") == "max_iterations"
    assert goal_supervisor.reason_to_code("max_failures reached (2)") == "max_failures"
    assert goal_supervisor.reason_to_code("dirty worktree (use --allow-dirty): x") == "dirty_worktree"
    assert goal_supervisor.reason_to_code("stop file present: STOP_LOOP") == "emergency_stop"
    assert goal_supervisor.reason_to_code("orchestrator emergency stop present: x") == "orchestrator_stop"


def test_resumability_split():
    assert goal_supervisor.is_resumable("max_iterations") is True
    assert goal_supervisor.is_resumable("dirty_worktree") is True
    assert goal_supervisor.is_resumable("max_failures") is False
    assert goal_supervisor.is_resumable("emergency_stop") is False


def test_no_goal_run_is_noop(tmp_path):
    report = goal_supervisor.supervise(tmp_path, now=NOW, apply=True)
    assert report["action"] == "none"


def test_running_loop_is_not_resumed(tmp_path):
    _write_loop_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build"},
        {"event": "iteration_done", "iteration": 1},
    ])
    report = goal_supervisor.supervise(tmp_path, now=NOW, apply=True)
    assert report["action"] == "none"
    assert "still running" in report["detail"]


def test_max_iterations_stop_is_resumed(tmp_path):
    _write_loop_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build"},
        {"event": "loop_stop", "iteration": 6, "reason": "max_iterations reached (5)"},
    ])
    captured = {}

    def fake_runner(cmd, root):
        captured["cmd"] = cmd
        return 0, "ok"

    report = goal_supervisor.supervise(tmp_path, now=NOW, apply=True, runner=fake_runner)
    assert report["action"] == "resume"
    assert "--checkpoint-dirty" in captured["cmd"]
    assert "--goal" in captured["cmd"] and GOAL in captured["cmd"]
    # resume bumped the per-goal restart counter
    assert stop_events.summarize(tmp_path)["goal_restarts"][GOAL] == 1


def test_max_failures_stop_is_halted_not_resumed(tmp_path):
    _write_loop_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build"},
        {"event": "loop_halt_max_failures", "iteration": 3},
    ])

    def fake_runner(cmd, root):
        raise AssertionError("must not resume an intentional max_failures halt")

    report = goal_supervisor.supervise(tmp_path, now=NOW, apply=True, runner=fake_runner)
    assert report["action"] == "halt"
    assert report["reason_code"] == "max_failures"


def test_restart_cap_blocks_further_resume(tmp_path):
    _write_loop_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build"},
        {"event": "loop_stop", "iteration": 6, "reason": "max_iterations reached (5)"},
    ])
    # seed 3 prior resumes
    for _ in range(3):
        stop_events.bump_counter(tmp_path, reason_code="max_iterations", action="resumed",
                                 klass="intentional", goal=GOAL, now=NOW)

    def fake_runner(cmd, root):
        raise AssertionError("must not resume past the cap")

    report = goal_supervisor.supervise(tmp_path, now=NOW, apply=True, max_restarts=3, runner=fake_runner)
    assert report["action"] == "cap"
    assert report["restart_count"] == 3


def test_dry_run_does_not_resume_or_write(tmp_path):
    _write_loop_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build"},
        {"event": "loop_stop", "iteration": 6, "reason": "max_iterations reached (5)"},
    ])

    def fake_runner(cmd, root):
        raise AssertionError("dry-run must not resume")

    report = goal_supervisor.supervise(tmp_path, now=NOW, apply=False, runner=fake_runner)
    assert report["action"] == "resume"  # decision computed
    assert not (tmp_path / "agents" / "runtime" / "stop_counters.json").exists()  # but nothing written


def test_cli_dry_run_default(tmp_path, capsys):
    _write_loop_events(tmp_path, [
        {"event": "loop_start", "goal": GOAL, "mode": "build"},
        {"event": "loop_stop", "iteration": 6, "reason": "max_iterations reached (5)"},
    ])
    rc = goal_supervisor.main(["--root", str(tmp_path), "--now", NOW, "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"action": "resume"' in out
    assert not (tmp_path / "agents" / "runtime" / "stop_counters.json").exists()
