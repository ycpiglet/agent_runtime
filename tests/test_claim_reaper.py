"""Tests for claim_reaper — safe recovery of dead-worker claims (deadlock breaker).

Safety invariants under test:
  - a claim whose lease is still valid (heartbeating, or within grace) is NEVER touched;
  - orchestrator claims are never reaped;
  - claims with no lease info are skipped (cannot prove death), not reaped;
  - reaping is idempotent and the reaped status leaves the unit re-dispatchable;
  - the sweep processes ALL claims, skipping the un-actionable and recovering the rest.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "claim_reaper.py"
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


def _run_reaper_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    source_root = str((ROOT / "src").resolve())
    ambient_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        os.pathsep.join((source_root, ambient_pythonpath))
        if ambient_pythonpath
        else source_root
    )
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def test_negative_explicit_grace_api_is_rejected_before_future_live_mutation(
    tmp_path: Path,
) -> None:
    path = _claim(
        tmp_path,
        "CLAIM-future-live-negative-api",
        expires_at="2026-06-14T12:05:00+09:00",
    )
    before = _reaper_mutation_snapshot(tmp_path)
    error: ValueError | None = None

    try:
        claim_reaper.sweep(
            tmp_path,
            now=NOW,
            apply=True,
            grace_seconds=-600,
        )
    except ValueError as exc:
        error = exc

    assert _reaper_mutation_snapshot(tmp_path) == before
    assert _load(path)["status"] == "claimed"
    assert error is not None


def test_negative_explicit_grace_cli_is_rejected_without_traceback_or_mutation(
    tmp_path: Path,
) -> None:
    path = _claim(
        tmp_path,
        "CLAIM-future-live-negative-cli",
        expires_at="2026-06-14T12:05:00+09:00",
    )
    before = _reaper_mutation_snapshot(tmp_path)

    result = _run_reaper_cli(
        tmp_path,
        "--now",
        NOW,
        "--grace-seconds",
        "-600",
        "--apply",
        "--json",
    )

    assert result.returncode != 0
    assert "Traceback" not in result.stdout + result.stderr
    assert _reaper_mutation_snapshot(tmp_path) == before
    assert _load(path)["status"] == "claimed"


@pytest.mark.parametrize("grace_seconds", (True, False, 0.0, "0"))
def test_explicit_grace_api_refuses_boolean_and_noninteger_values(
    tmp_path: Path,
    grace_seconds: object,
) -> None:
    _claim(
        tmp_path,
        "CLAIM-live-invalid-grace-api",
        expires_at="2026-06-14T13:00:00+09:00",
    )
    before = _reaper_mutation_snapshot(tmp_path)
    error: ValueError | None = None

    try:
        claim_reaper.sweep(
            tmp_path,
            now=NOW,
            apply=True,
            grace_seconds=grace_seconds,  # type: ignore[arg-type]
        )
    except ValueError as exc:
        error = exc

    assert _reaper_mutation_snapshot(tmp_path) == before
    assert error is not None


def test_zero_grace_keeps_deadline_equality_live_then_reaps_afterward(
    tmp_path: Path,
) -> None:
    path = _claim(tmp_path, "CLAIM-zero-grace", expires_at=NOW)

    equal = claim_reaper.sweep(
        tmp_path,
        now=NOW,
        apply=True,
        grace_seconds=0,
    )

    assert equal["reaped"] == []
    assert [entry["claim_id"] for entry in equal["live"]] == [
        "CLAIM-zero-grace"
    ]
    assert _load(path)["status"] == "claimed"

    afterward = claim_reaper.sweep(
        tmp_path,
        now="2026-06-14T12:00:01+09:00",
        apply=True,
        grace_seconds=0,
    )

    assert [entry["claim_id"] for entry in afterward["reaped"]] == [
        "CLAIM-zero-grace"
    ]
    assert _load(path)["status"] == "expired"


def test_positive_grace_keeps_equality_live(tmp_path: Path) -> None:
    path = _claim(
        tmp_path,
        "CLAIM-positive-grace-equality",
        expires_at="2026-06-14T11:50:00+09:00",
    )

    report = claim_reaper.sweep(
        tmp_path,
        now=NOW,
        apply=True,
        grace_seconds=600,
    )

    assert report["reaped"] == []
    assert [entry["claim_id"] for entry in report["live"]] == [
        "CLAIM-positive-grace-equality"
    ]
    assert _load(path)["status"] == "claimed"


def test_default_grace_preserves_environment_compatibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(claim_reaper.GRACE_ENV, raising=False)
    assert claim_reaper.default_grace() == 600
    monkeypatch.setenv(claim_reaper.GRACE_ENV, "malformed")
    assert claim_reaper.default_grace() == 600
    monkeypatch.setenv(claim_reaper.GRACE_ENV, "-1")
    assert claim_reaper.default_grace() == 0
    monkeypatch.setenv(claim_reaper.GRACE_ENV, "0")
    assert claim_reaper.default_grace() == 0


@pytest.mark.parametrize(
    ("status", "top", "nested", "expected_state", "expected_decision"),
    (
        (
            "claimed",
            "2026-06-14T12:00:00+09:00",
            "2026-06-14T12:00:00+09:00",
            "live",
            "live",
        ),
        (
            "claimed",
            "2026-06-14T11:49:59.999999+09:00",
            "2026-06-14T11:49:59.999999+09:00",
            "expired",
            "dead",
        ),
        ("claimed", None, None, "indeterminate", "skip"),
        (
            "released",
            "2026-06-14T11:00:00+09:00",
            "2026-06-14T11:00:00+09:00",
            "inactive",
            "skip",
        ),
    ),
)
def test_ar655_reaper_wrapper_matches_shared_claim_liveness(
    status: str,
    top: str | None,
    nested: str | None,
    expected_state: str,
    expected_decision: str,
) -> None:
    claim: dict[str, object] = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": "CLAIM-AR655-REAPER-PARITY",
        "task_id": "TASK-AR-655",
        "agent_instance_id": "worker-ar655-reaper-parity",
        "status": status,
    }
    if top is not None:
        claim["expires_at"] = top
    if nested is not None:
        claim["lease"] = {"expires_at": nested}
    now = claim_reaper._parse_now(NOW)

    shared = claim_reaper.claim_store.classify_claim_liveness(
        claim,
        now=now,
        grace_seconds=600,
    )
    decision, reason = claim_reaper.classify_claim(claim, now, 600)

    assert shared.state == expected_state
    assert decision == expected_decision
    assert isinstance(reason, str) and reason
    if shared.state == "indeterminate":
        assert "indeterminate" in reason


def test_ar655_reaper_uses_shared_latest_deadline_and_grace_equality() -> None:
    claim = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": "CLAIM-AR655-REAPER-LATEST",
        "task_id": "TASK-AR-655",
        "agent_instance_id": "worker-ar655-reaper-latest",
        "status": "claimed",
        "expires_at": "2026-06-14T11:00:00+09:00",
        "lease": {"expires_at": "2026-06-14T11:50:00+09:00"},
    }
    now = claim_reaper._parse_now(NOW)

    shared = claim_reaper.claim_store.classify_claim_liveness(
        claim,
        now=now,
        grace_seconds=600,
    )
    decision, reason = claim_reaper.classify_claim(claim, now, 600)

    assert shared.state == "live"
    assert shared.effective_deadline == claim_reaper._parse_now(
        "2026-06-14T11:50:00+09:00"
    )
    assert any("mismatch" in finding for finding in shared.findings)
    assert (decision, reason) == ("live", "lease-valid")


@pytest.mark.parametrize(
    ("environment", "expected"),
    (
        ({}, 600),
        ({claim_reaper.GRACE_ENV: "malformed"}, 600),
        ({claim_reaper.GRACE_ENV: "-1"}, 0),
    ),
)
def test_ar655_reaper_default_grace_is_shared_resolver_parity(
    monkeypatch: pytest.MonkeyPatch,
    environment: dict[str, str],
    expected: int,
) -> None:
    monkeypatch.delenv(claim_reaper.GRACE_ENV, raising=False)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)

    assert claim_reaper.default_grace() == expected
    assert claim_reaper.default_grace() == claim_reaper.claim_store.resolve_claim_grace()


def test_huge_nonnegative_grace_conservatively_retains_live_claim(
    tmp_path: Path,
) -> None:
    path = _claim(
        tmp_path,
        "CLAIM-huge-grace",
        expires_at="2026-06-14T11:00:00+09:00",
    )

    report = claim_reaper.sweep(
        tmp_path,
        now=NOW,
        apply=True,
        grace_seconds=10**100,
    )

    assert report["reaped"] == []
    assert [entry["claim_id"] for entry in report["live"]] == [
        "CLAIM-huge-grace"
    ]
    assert _load(path)["status"] == "claimed"


def test_dead_then_max_deadline_sweep_completes_and_records_reap_audit(
    tmp_path: Path,
) -> None:
    dead = _claim(
        tmp_path,
        "CLAIM-a-dead-before-max",
        task_id="TASK-AR-dead-before-max",
        expires_at="2026-06-14T11:00:00+09:00",
    )
    maximum = _claim(
        tmp_path,
        "CLAIM-z-maximum-deadline",
        task_id="TASK-AR-maximum-deadline",
        expires_at="9999-12-31T23:59:59+00:00",
    )

    report = claim_reaper.sweep(
        tmp_path,
        now=NOW,
        apply=True,
        grace_seconds=600,
    )

    assert [entry["claim_id"] for entry in report["reaped"]] == [
        "CLAIM-a-dead-before-max"
    ]
    assert [entry["claim_id"] for entry in report["live"]] == [
        "CLAIM-z-maximum-deadline"
    ]
    assert report["claim_store"] == {"state": "initialized", "finding": None}
    assert _load(dead)["status"] == "expired"
    assert _load(maximum)["status"] == "claimed"

    pane_events_path = (
        tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    )
    pane_events = [
        json.loads(line)
        for line in pane_events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [
        event["claim_id"]
        for event in pane_events
        if event.get("event") == "claim_reaped"
    ] == ["CLAIM-a-dead-before-max"]

    import stop_events

    summary = stop_events.summarize(tmp_path)
    assert summary["by_action"].get("reaped") == 1
    assert summary["by_reason"].get("dead_claim") == 1


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


# --- TASK-AR-659 RED: an expired orchestrator claim must not be an invisible skip ---
#
# Regression source: CLAIM-20260803-002651-task-ar-655-5f27 sat expired for 5.4h
# while every reaper report filed it as a plain `orchestrator-claim` skip, i.e.
# indistinguishable from a healthy orchestrator claim. Nothing surfaced that the
# taskset was deadlocked. The safety invariant (orchestrator claims are never
# auto-reaped) stays intact; only the blind spot is removed.


def test_red_expired_orchestrator_claim_is_surfaced_for_owner_recovery(tmp_path):
    _claim(
        tmp_path,
        "CLAIM-orch-dead",
        mode="orchestrator",
        expires_at="2026-06-14T11:00:00+09:00",
    )

    report = claim_reaper.sweep(tmp_path, now=NOW, apply=False, grace_seconds=600)

    # Safety invariant preserved: still never a reap candidate.
    assert report["reaped"] == []
    assert report["would_reap"] == []
    # Blind spot removed: the dead claim is explicitly surfaced.
    surfaced = {entry["claim_id"] for entry in report.get("needs_owner_recovery", [])}
    assert "CLAIM-orch-dead" in surfaced


def test_red_live_orchestrator_claim_is_not_flagged_for_owner_recovery(tmp_path):
    _claim(
        tmp_path,
        "CLAIM-orch-live",
        mode="orchestrator",
        expires_at="2026-06-14T12:30:00+09:00",
    )

    report = claim_reaper.sweep(tmp_path, now=NOW, apply=False, grace_seconds=600)

    surfaced = {entry["claim_id"] for entry in report.get("needs_owner_recovery", [])}
    assert "CLAIM-orch-live" not in surfaced


def test_red_expired_orchestrator_skip_reason_differs_from_healthy_one(tmp_path):
    _claim(
        tmp_path,
        "CLAIM-orch-dead-reason",
        mode="orchestrator",
        expires_at="2026-06-14T11:00:00+09:00",
    )
    _claim(
        tmp_path,
        "CLAIM-orch-live-reason",
        task_id="TASK-AR-2",
        mode="orchestrator",
        expires_at="2026-06-14T12:30:00+09:00",
    )

    report = claim_reaper.sweep(tmp_path, now=NOW, apply=False, grace_seconds=600)
    reasons = {entry["claim_id"]: entry["reason"] for entry in report["skipped"]}

    assert reasons["CLAIM-orch-live-reason"] == "orchestrator-claim"
    assert reasons["CLAIM-orch-dead-reason"] == "orchestrator-claim-expired"


def test_red_terminal_orchestrator_claim_is_not_flagged_for_owner_recovery(tmp_path):
    """A claim already terminalized to `expired` is resolved, not outstanding."""
    _claim(
        tmp_path,
        "CLAIM-orch-terminal",
        mode="orchestrator",
        status="expired",
        expires_at="2026-06-14T11:00:00+09:00",
    )

    report = claim_reaper.sweep(tmp_path, now=NOW, apply=False, grace_seconds=600)

    surfaced = {entry["claim_id"] for entry in report.get("needs_owner_recovery", [])}
    assert "CLAIM-orch-terminal" not in surfaced


# --- TASK-AR-659 W4b P1: a claim with no deadline is worse than an expired one ---


def test_deadline_missing_orchestrator_claim_surfaces_for_owner_recovery(tmp_path):
    """No deadline means it can never expire, never be reaped, never be proven
    live. Reporting it as a plain `orchestrator-claim` hides a permanent
    deadlock that is strictly worse than the AR-655 case.
    """
    _claim(
        tmp_path,
        "CLAIM-orch-nolease",
        mode="orchestrator",
        expires_at=None,
    )

    report = claim_reaper.sweep(tmp_path, now=NOW, apply=False, grace_seconds=600)

    assert report["reaped"] == []
    assert report["would_reap"] == []
    reasons = {entry["claim_id"]: entry["reason"] for entry in report["skipped"]}
    assert reasons["CLAIM-orch-nolease"] == "no-lease-info"
    surfaced = {entry["claim_id"] for entry in report["needs_owner_recovery"]}
    assert "CLAIM-orch-nolease" in surfaced


def test_deadline_missing_worker_claim_surfaces_for_owner_recovery(tmp_path):
    """The same hole exists for a non-orchestrator claim with no lease info."""
    _claim(tmp_path, "CLAIM-worker-nolease", expires_at=None)

    report = claim_reaper.sweep(tmp_path, now=NOW, apply=False, grace_seconds=600)

    assert report["reaped"] == []
    surfaced = {entry["claim_id"] for entry in report["needs_owner_recovery"]}
    assert "CLAIM-worker-nolease" in surfaced


def test_owner_recovery_signal_reaches_the_session_start_hook(tmp_path, capsys):
    """The visibility fix must reach the automated consumers, not just the CLI.

    deadlock_watchdog is documented as the component that breaks wave
    deadlocks, and the hook is what an owner actually sees at session start.
    """
    import claim_reaper_hook
    import deadlock_watchdog

    _claim(
        tmp_path,
        "CLAIM-orch-hook",
        mode="orchestrator",
        expires_at="2026-06-14T11:00:00+09:00",
    )

    claim_reaper_hook.main(["--root", str(tmp_path)])
    hook_out = capsys.readouterr().out
    assert "need owner recovery" in hook_out
    assert "CLAIM-orch-hook" in hook_out
    assert "terminalize" in hook_out

    report = {
        "apply": False,
        "reaper": claim_reaper.sweep(tmp_path, now=NOW, apply=False, grace_seconds=600),
        "supervisor": {"action": "none"},
    }
    assert "needs_owner_recovery=1" in deadlock_watchdog._summary_line(report)


@pytest.mark.parametrize(
    "label, mutate",
    [
        # The pre-`lease`-nesting legacy claim: top-level deadline only. This is
        # the most likely real-world member of the AR-655 family.
        ("legacy-top-only", lambda c: c.pop("lease", None)),
        ("malformed-top", lambda c: c.update({"expires_at": "not-a-timestamp"})),
        ("lease-deadline-removed", lambda c: c["lease"].pop("expires_at", None)),
        ("no-deadline-at-all", lambda c: (c.pop("lease", None), c.pop("expires_at", None))),
    ],
)
def test_every_indeterminate_lease_shape_surfaces_for_owner_recovery(
    tmp_path, label, mutate
):
    """Fixing only the wholly-absent case would leave the common shapes hidden."""
    path = _claim(
        tmp_path,
        f"CLAIM-orch-{label}",
        mode="orchestrator",
        expires_at="2026-06-14T11:00:00+09:00",
    )
    payload = _load(path)
    mutate(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = claim_reaper.sweep(tmp_path, now=NOW, apply=False, grace_seconds=600)

    assert report["reaped"] == []
    reasons = {entry["claim_id"]: entry["reason"] for entry in report["skipped"]}
    assert reasons[f"CLAIM-orch-{label}"] == "no-lease-info", label
    surfaced = {entry["claim_id"] for entry in report["needs_owner_recovery"]}
    assert f"CLAIM-orch-{label}" in surfaced, label
