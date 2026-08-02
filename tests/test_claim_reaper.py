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

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import claim_reaper  # noqa: E402

NOW = "2026-06-14T12:00:00+09:00"


def _claim_store_markers(root: Path) -> tuple[Path, Path]:
    return (
        root / "agents" / "runtime" / "task_claims" / ".claim-store",
        claim_reaper.claim_store.outer_marker_path(root),
    )


def _ensure_claim_store(root: Path, witness_claim_id: str) -> None:
    inner, outer = _claim_store_markers(root)
    raw = (
        json.dumps(
            {
                "schema": claim_reaper.claim_store.MARKER_SCHEMA,
                "generation_id": "11111111-1111-4111-8111-111111111111",
                "witness_claim_id": witness_claim_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    for marker in (inner, outer):
        marker.parent.mkdir(parents=True, exist_ok=True)
        if not marker.is_file():
            marker.write_bytes(raw)
    assert inner.read_bytes() == outer.read_bytes()


def _reaper_mutation_snapshot(root: Path) -> dict[str, bytes | None]:
    paths = [
        *_claim_store_markers(root),
        *sorted((root / "agents/runtime/task_claims").glob("CLAIM-*.json")),
        root / "agents/runtime/pane_events/pane-events.jsonl",
        root / "agents/runtime/stop_counters.json",
        *sorted((root / "agents/runtime/events").glob("*.jsonl")),
    ]
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in paths
    }


def _assert_claim_store_failure(report: dict, state: str) -> None:
    authority = report["claim_store"]
    assert authority["state"] == state
    finding = authority["finding"]
    assert isinstance(finding, str) and finding
    assert len(finding) <= 256
    assert "\n" not in finding
    assert "Traceback" not in finding
    assert report["reaped"] == []
    assert report["would_reap"] == []


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
    _ensure_claim_store(tmp_path, claim_id)
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
    assert report["claim_store"] == {
        "state": "initialized",
        "finding": None,
    }


@pytest.mark.parametrize("payload_kind", ("oversized", "deep", "invalid-utf8"))
def test_apply_refuses_unbounded_non_witness_claim_without_any_mutation(
    tmp_path,
    payload_kind,
):
    _claim(
        tmp_path,
        "CLAIM-retained-witness",
        expires_at="2026-06-14T13:00:00+09:00",
    )
    path = (
        tmp_path
        / "agents"
        / "runtime"
        / "task_claims"
        / f"CLAIM-unbounded-{payload_kind}.json"
    )
    base = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": f"CLAIM-unbounded-{payload_kind}",
        "task_id": "TASK-AR-unbounded",
        "agent_role": "lead-engineer",
        "status": "claimed",
        "expires_at": "2026-06-14T11:00:00+09:00",
        "lease": {"expires_at": "2026-06-14T11:00:00+09:00"},
    }
    if payload_kind == "oversized":
        base["padding"] = "x" * (claim_reaper.claim_store.CLAIM_MAX_BYTES + 1)
        raw = json.dumps(base).encode("utf-8")
    elif payload_kind == "deep":
        prefix = json.dumps(base)[:-1]
        raw = (
            prefix + ',"nested":' + "[" * 1100 + "0" + "]" * 1100 + "}"
        ).encode("utf-8")
    else:
        raw = json.dumps(base).encode("utf-8") + b"\xff"
    path.write_bytes(raw)
    before = _reaper_mutation_snapshot(tmp_path)

    report = claim_reaper.sweep(
        tmp_path,
        now=NOW,
        apply=True,
        grace_seconds=600,
    )

    _assert_claim_store_failure(report, "integrity-invalid")
    assert path.read_bytes() == raw
    assert _reaper_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize("status", ("mystery", ["claimed"], None))
def test_apply_refuses_unknown_or_nonstring_claim_status_without_any_mutation(
    tmp_path,
    status,
):
    path = _claim(
        tmp_path,
        "CLAIM-invalid-status",
        status=status,
        expires_at="2026-06-14T11:00:00+09:00",
    )
    before = _reaper_mutation_snapshot(tmp_path)

    report = claim_reaper.sweep(
        tmp_path,
        now=NOW,
        apply=True,
        grace_seconds=600,
    )

    _assert_claim_store_failure(report, "integrity-invalid")
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == status
    assert _reaper_mutation_snapshot(tmp_path) == before


def test_reap_audit_failure_does_not_misreport_successful_authority_mutation(
    tmp_path,
    monkeypatch,
):
    path = _claim(
        tmp_path,
        "CLAIM-dead-audit-failure",
        expires_at="2026-06-14T11:00:00+09:00",
    )

    def fail_stop_event(*_args, **_kwargs):
        raise OSError("injected stop-event write failure")

    monkeypatch.setattr(
        claim_reaper.stop_events,
        "record_stop_event",
        fail_stop_event,
    )

    report = claim_reaper.sweep(
        tmp_path,
        now=NOW,
        apply=True,
        grace_seconds=600,
    )

    assert [entry["claim_id"] for entry in report["reaped"]] == [
        "CLAIM-dead-audit-failure"
    ]
    assert report["claim_store"] == {
        "state": "initialized",
        "finding": None,
    }
    assert _load(path)["status"] == "expired"


def test_apply_refuses_markerless_populated_store_without_any_mutation(tmp_path):
    path = _claim(
        tmp_path,
        "CLAIM-markerless",
        expires_at="2026-06-14T11:00:00+09:00",
    )
    inner, outer = _claim_store_markers(tmp_path)
    inner.unlink()
    outer.unlink()
    before = _reaper_mutation_snapshot(tmp_path)

    report = claim_reaper.sweep(
        tmp_path,
        now=NOW,
        apply=True,
        grace_seconds=600,
    )

    _assert_claim_store_failure(report, "migration-required")
    assert _load(path)["status"] == "claimed"
    assert _reaper_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    ("missing_side", "expected_state"),
    (("inner", "integrity-invalid"), ("outer", "migration-required")),
)
def test_apply_refuses_one_sided_store_without_any_mutation(
    tmp_path,
    missing_side,
    expected_state,
):
    path = _claim(
        tmp_path,
        f"CLAIM-one-sided-{missing_side}",
        expires_at="2026-06-14T11:00:00+09:00",
    )
    inner, outer = _claim_store_markers(tmp_path)
    {"inner": inner, "outer": outer}[missing_side].unlink()
    before = _reaper_mutation_snapshot(tmp_path)

    report = claim_reaper.sweep(
        tmp_path,
        now=NOW,
        apply=True,
        grace_seconds=600,
    )

    _assert_claim_store_failure(report, expected_state)
    assert _load(path)["status"] == "claimed"
    assert _reaper_mutation_snapshot(tmp_path) == before


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


def test_dry_run_reports_markerless_migration_without_creating_markers(tmp_path):
    path = _claim(
        tmp_path,
        "CLAIM-dry-run-markerless",
        expires_at="2026-06-14T11:00:00+09:00",
    )
    inner, outer = _claim_store_markers(tmp_path)
    inner.unlink()
    outer.unlink()
    before = _reaper_mutation_snapshot(tmp_path)

    report = claim_reaper.sweep(
        tmp_path,
        now=NOW,
        apply=False,
        grace_seconds=600,
    )

    _assert_claim_store_failure(report, "migration-required")
    assert _load(path)["status"] == "claimed"
    assert not inner.exists()
    assert not outer.exists()
    assert _reaper_mutation_snapshot(tmp_path) == before


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


def test_cli_apply_reports_bounded_store_failure_without_traceback_or_mutation(
    tmp_path,
    capsys,
):
    path = _claim(
        tmp_path,
        "CLAIM-cli-markerless",
        expires_at="2026-06-14T11:00:00+09:00",
    )
    inner, outer = _claim_store_markers(tmp_path)
    inner.unlink()
    outer.unlink()
    before = _reaper_mutation_snapshot(tmp_path)

    rc = claim_reaper.main(
        [
            "--root",
            str(tmp_path),
            "--now",
            NOW,
            "--grace-seconds",
            "600",
            "--apply",
            "--json",
        ]
    )
    captured = capsys.readouterr()

    assert rc == 1
    assert "Traceback" not in captured.out + captured.err
    report = json.loads(captured.out)
    _assert_claim_store_failure(report, "migration-required")
    assert _load(path)["status"] == "claimed"
    assert _reaper_mutation_snapshot(tmp_path) == before
