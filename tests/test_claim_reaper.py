"""Tests for claim_reaper — safe recovery of dead-worker claims (deadlock breaker).

Safety invariants under test:
  - a claim whose lease is still valid (heartbeating, or within grace) is NEVER touched;
  - orchestrator claims are never reaped;
  - claims with no lease info are skipped (cannot prove death), not reaped;
  - reaping is idempotent and the reaped status leaves the unit re-dispatchable;
  - the sweep processes ALL claims, skipping the un-actionable and recovering the rest.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import claim_reaper  # noqa: E402

NOW = "2026-06-14T12:00:00+09:00"


def _claim(tmp_path: Path, claim_id: str, *, status: str = "claimed",
           expires_at: str | None = "2026-06-14T11:00:00+09:00",
           agent_role: str = "lead-engineer", task_id: str = "TASK-AR-1",
           include_lease: bool = True, **extra) -> Path:
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": task_id,
        "agent_role": agent_role,
        "agent_instance_id": f"ai-{claim_id}",
        "status": status,
        "worktree_path": f".worktrees/{task_id}",
        "branch": f"codex/{task_id}",
    }
    if expires_at is not None:
        payload["expires_at"] = expires_at
        if include_lease:
            payload["lease"] = {"expires_at": expires_at, "heartbeat_at": expires_at}
    payload.update(extra)
    path = claim_dir / f"{claim_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_live_claim_is_never_touched(tmp_path):
    # expires_at well in the future -> heartbeating worker, must not reap.
    path = _claim(tmp_path, "CLAIM-live", expires_at="2026-06-14T13:00:00+09:00")
    report = claim_reaper.sweep(tmp_path, now=NOW, apply=True)
    assert report["reaped"] == []
    assert any(c["claim_id"] == "CLAIM-live" for c in report["live"])
    assert _load(path)["status"] == "claimed"


def test_provably_dead_claim_is_reaped_on_apply(tmp_path):
    # expired 60min ago, well beyond grace -> provably dead.
    path = _claim(tmp_path, "CLAIM-dead", expires_at="2026-06-14T11:00:00+09:00")
    report = claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=600)
    assert [c["claim_id"] for c in report["reaped"]] == ["CLAIM-dead"]
    reaped = _load(path)
    assert reaped["status"] == "expired"
    assert reaped["recovered_from_status"] == "claimed"
    assert reaped["reaped_by"] == "claim_reaper"
    assert "reaped_at" in reaped


def test_reaped_status_outside_all_active_sets(tmp_path):
    # The chosen terminal status must make the unit re-dispatchable (pending),
    # i.e. it is in none of the dispatcher/footprint active sets nor done set.
    import footprint_conflict_gate
    import task_claim_dispatcher
    import wave_dispatcher
    assert "expired" not in footprint_conflict_gate.ACTIVE_CLAIM_STATUSES
    assert "expired" not in task_claim_dispatcher.ACTIVE_STATUSES
    assert "expired" not in wave_dispatcher.ACTIVE_CLAIM_STATUSES
    assert "expired" not in wave_dispatcher.DONE_CLAIM_STATUSES


def test_dry_run_writes_nothing(tmp_path):
    path = _claim(tmp_path, "CLAIM-dead", expires_at="2026-06-14T11:00:00+09:00")
    report = claim_reaper.sweep(tmp_path, now=NOW, apply=False, grace_seconds=600)
    assert [c["claim_id"] for c in report["would_reap"]] == ["CLAIM-dead"]
    assert _load(path)["status"] == "claimed"  # untouched
    # no counters file written in dry-run
    assert not (tmp_path / "agents" / "runtime" / "stop_counters.json").exists()


def test_orchestrator_claim_is_skipped(tmp_path):
    path = _claim(tmp_path, "CLAIM-orch", agent_role="orchestrator",
                  expires_at="2026-06-14T11:00:00+09:00")
    report = claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=600)
    assert report["reaped"] == []
    assert any(c["claim_id"] == "CLAIM-orch" for c in report["skipped"])
    assert _load(path)["status"] == "claimed"


def test_terminal_claim_is_skipped(tmp_path):
    path = _claim(tmp_path, "CLAIM-rel", status="released",
                  expires_at="2026-06-14T11:00:00+09:00")
    report = claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=600)
    assert report["reaped"] == []
    assert _load(path)["status"] == "released"


def test_no_lease_info_is_skipped_not_reaped(tmp_path):
    path = _claim(tmp_path, "CLAIM-nolease", expires_at=None)
    report = claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=600)
    assert report["reaped"] == []
    assert any(c["claim_id"] == "CLAIM-nolease" and c["reason"] == "no-lease-info"
               for c in report["skipped"])
    assert _load(path)["status"] == "claimed"


def test_within_grace_is_treated_as_live(tmp_path):
    # expired only 5min ago, grace 600s(10min) -> still live, do not reap.
    _claim(tmp_path, "CLAIM-grace", expires_at="2026-06-14T11:55:00+09:00")
    report = claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=600)
    assert report["reaped"] == []
    assert any(c["claim_id"] == "CLAIM-grace" for c in report["live"])


def test_idempotent_second_run_reaps_nothing(tmp_path):
    _claim(tmp_path, "CLAIM-dead", expires_at="2026-06-14T11:00:00+09:00")
    first = claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=600)
    assert len(first["reaped"]) == 1
    second = claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=600)
    assert second["reaped"] == []


def test_sweep_processes_all_claims_mixed(tmp_path):
    _claim(tmp_path, "CLAIM-dead1", task_id="TASK-AR-1", expires_at="2026-06-14T11:00:00+09:00")
    _claim(tmp_path, "CLAIM-dead2", task_id="TASK-AR-2", expires_at="2026-06-14T10:00:00+09:00")
    _claim(tmp_path, "CLAIM-live", task_id="TASK-AR-3", expires_at="2026-06-14T13:00:00+09:00")
    _claim(tmp_path, "CLAIM-orch", task_id="TASK-AR-4", agent_role="orchestrator",
           expires_at="2026-06-14T11:00:00+09:00")
    report = claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=600)
    assert sorted(c["claim_id"] for c in report["reaped"]) == ["CLAIM-dead1", "CLAIM-dead2"]
    assert any(c["claim_id"] == "CLAIM-live" for c in report["live"])
    assert any(c["claim_id"] == "CLAIM-orch" for c in report["skipped"])


def test_apply_records_stop_events_and_counters(tmp_path):
    _claim(tmp_path, "CLAIM-dead", expires_at="2026-06-14T11:00:00+09:00")
    claim_reaper.sweep(tmp_path, now=NOW, apply=True, grace_seconds=600)
    import stop_events
    summary = stop_events.summarize(tmp_path)
    assert summary["by_action"].get("reaped") == 1
    assert summary["by_reason"].get("dead_claim") == 1


def test_cli_dry_run_default_and_apply(tmp_path, capsys):
    _claim(tmp_path, "CLAIM-dead", expires_at="2026-06-14T11:00:00+09:00")
    rc = claim_reaper.main(["--root", str(tmp_path), "--now", NOW,
                            "--grace-seconds", "600", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "would_reap" in out
    # still untouched after dry-run
    path = tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-dead.json"
    assert _load(path)["status"] == "claimed"
    rc = claim_reaper.main(["--root", str(tmp_path), "--now", NOW,
                            "--grace-seconds", "600", "--apply", "--json"])
    assert rc == 0
    assert _load(path)["status"] == "expired"
