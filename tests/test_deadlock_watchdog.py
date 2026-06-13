"""Tests for deadlock_watchdog — one cycle of reaper + goal supervisor."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import deadlock_watchdog  # noqa: E402

NOW = "2026-06-14T12:00:00+09:00"


def _dead_claim(tmp_path: Path) -> Path:
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    path = claim_dir / "CLAIM-dead.json"
    path.write_text(json.dumps({
        "claim_id": "CLAIM-dead", "task_id": "TASK-AR-1", "agent_role": "lead-engineer",
        "status": "claimed", "expires_at": "2026-06-14T11:00:00+09:00",
        "lease": {"expires_at": "2026-06-14T11:00:00+09:00"},
    }), encoding="utf-8")
    return path


def _halted_goal(tmp_path: Path) -> None:
    path = tmp_path / "agents" / "runtime" / "events" / "agent_loop-2026-06-14.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(line) for line in [
        {"event": "loop_start", "goal": "ship", "mode": "build"},
        {"event": "loop_halt_max_failures", "iteration": 3},
    ]) + "\n", encoding="utf-8")


def test_cycle_reaps_and_reports_goal(tmp_path):
    claim = _dead_claim(tmp_path)
    _halted_goal(tmp_path)  # max_failures -> supervisor halts (no spawn)
    report = deadlock_watchdog.run_cycle(tmp_path, now=NOW, apply=True, grace_seconds=600)
    assert [c["claim_id"] for c in report["reaper"]["reaped"]] == ["CLAIM-dead"]
    assert json.loads(claim.read_text(encoding="utf-8"))["status"] == "expired"
    assert report["supervisor"]["action"] == "halt"  # intentional stop, not resumed


def test_dry_run_acts_on_nothing(tmp_path):
    claim = _dead_claim(tmp_path)
    report = deadlock_watchdog.run_cycle(tmp_path, now=NOW, apply=False, grace_seconds=600)
    assert report["reaper"]["would_reap"]
    assert json.loads(claim.read_text(encoding="utf-8"))["status"] == "claimed"


def test_cli_smoke(tmp_path, capsys):
    _dead_claim(tmp_path)
    rc = deadlock_watchdog.main(["--root", str(tmp_path), "--now", NOW,
                                 "--grace-seconds", "600", "--json"])
    assert rc == 0
    assert "would_reap" in capsys.readouterr().out
