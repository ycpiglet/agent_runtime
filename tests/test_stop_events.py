"""Tests for stop_events — stop-reason classification, events, and counters."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import stop_events  # noqa: E402

NOW = "2026-06-14T10:00:00+09:00"


def test_classify_recoverable_intentional_and_unknown():
    assert stop_events.classify("dead_claim") == "recoverable"
    assert stop_events.classify("dirty_worktree") == "recoverable"
    assert stop_events.classify("lease_expired") == "recoverable"
    assert stop_events.classify("max_failures") == "intentional"
    assert stop_events.classify("taskset_boundary") == "intentional"
    assert stop_events.classify("dirty_worktree_main") == "intentional"
    assert stop_events.classify("who_knows") == "unknown"


def test_record_stop_event_appends_and_auto_classifies(tmp_path):
    event = stop_events.record_stop_event(
        tmp_path,
        source="claim_reaper",
        reason_code="dead_claim",
        action="reaped",
        claim_id="CLAIM-x",
        task_id="TASK-AR-1",
        now=NOW,
    )
    assert event["class"] == "recoverable"
    assert event["action"] == "reaped"
    assert event["source"] == "claim_reaper"
    events = stop_events.load_events(tmp_path, now=NOW)
    assert len(events) == 1
    assert events[0]["reason_code"] == "dead_claim"
    assert events[0]["claim_id"] == "CLAIM-x"


def test_explicit_class_overrides_classification(tmp_path):
    # dirty_worktree on main is intentional even though base code is recoverable.
    event = stop_events.record_stop_event(
        tmp_path,
        source="agent_loop",
        reason_code="dirty_worktree_main",
        action="stopped",
        now=NOW,
    )
    assert event["class"] == "intentional"


def test_counters_accumulate_across_calls(tmp_path):
    for _ in range(3):
        stop_events.record_stop_event(
            tmp_path, source="claim_reaper", reason_code="dead_claim",
            action="reaped", now=NOW,
        )
    stop_events.record_stop_event(
        tmp_path, source="goal_supervisor", reason_code="dirty_worktree",
        action="resumed", goal="ship X", now="2026-06-14T10:05:00+09:00",
    )
    summary = stop_events.summarize(tmp_path)
    assert summary["by_action"]["reaped"] == 3
    assert summary["by_action"]["resumed"] == 1
    assert summary["by_class"]["recoverable"] == 4
    assert summary["by_reason"]["dead_claim"] == 3
    assert summary["goal_restarts"]["ship X"] == 1


def test_load_counters_tolerates_missing_and_corrupt(tmp_path):
    assert stop_events.load_counters(tmp_path)["by_action"] == {}
    stop_events.counters_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    stop_events.counters_path(tmp_path).write_text("{ broken", encoding="utf-8")
    assert stop_events.load_counters(tmp_path)["by_action"] == {}


def test_cli_record_and_summary(tmp_path, capsys):
    rc = stop_events.main([
        "--root", str(tmp_path), "record", "--source", "agent_loop",
        "--reason-code", "max_failures", "--action", "stopped",
        "--now", NOW, "--json",
    ])
    assert rc == 0
    rc = stop_events.main(["--root", str(tmp_path), "summary", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "max_failures" in out
