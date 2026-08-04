from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
REGISTRY = REPO_ROOT / "scripts" / "agent_instance_registry.py"
GATE = REPO_ROOT / "scripts" / "agent_identity_gate.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import agent_instance_registry  # noqa: E402


def _run_registry(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REGISTRY), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_gate(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _claim_payload(**overrides: str) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": "CLAIM-20260612-145000-task-ar-901-aa11",
        "task_id": "TASK-AR-901",
        "agent_role": "qa",
        "team_id": "evaluation-office",
        "agent_instance_id": "qa-20260612-145000-kst-aa11",
        "display_name": "qa@review-01",
        "callsite_id": "terminal:wt-task-ar-901:tab-01",
        "pane_id": "terminal:wt-task-ar-901:tab-01",
        "status": "claimed",
        "task_set_id": "TASKSET-TEST",
        "project_id": "PROJECT-TEST",
        "unit_id": "UNIT-TASK-AR-901-001",
        "unit_spec": "agents/lead_engineer/tasks/units/TASK-AR-901/UNIT-TASK-AR-901-001.md",
        "model_tier": "worker_standard",
        "worktree_path": ".worktrees/TASK-AR-901",
        "claimed_at": "2026-06-12T14:50:00+09:00",
        "updated_at": "2026-06-12T14:50:00+09:00",
    }
    payload.update(overrides)
    return payload


def _write_claim(root: Path, payload: dict[str, object] | None = None) -> Path:
    claim = payload or _claim_payload()
    path = root / "agents" / "runtime" / "task_claims" / f"{claim['claim_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _record_claim_instance(
    root: Path,
    claim: dict[str, object],
) -> tuple[Path, dict[str, object]]:
    return agent_instance_registry.record_claim_instance(
        root,
        claim,
        emit_spawn_event=False,
    )


def _assert_bounded_registry_refusal_without_mutation(
    root: Path,
    instance_path: Path,
    claim: dict[str, object],
) -> None:
    before = instance_path.read_bytes()
    error: agent_instance_registry.AgentInstanceRegistryError | None = None
    try:
        _record_claim_instance(root, claim)
    except agent_instance_registry.AgentInstanceRegistryError as exc:
        error = exc
    after = instance_path.read_bytes()

    assert error is not None, (
        "non-idempotent or incoherent claim revision was accepted; "
        f"record_changed={after != before}"
    )
    assert 0 < len(error.findings) <= 8
    for finding in error.findings:
        assert isinstance(finding, str) and finding
        assert len(finding) <= 256
        assert "\n" not in finding
        assert "\r" not in finding
        assert "Traceback" not in finding
    assert after == before


def test_agent_instance_registry_records_claim_and_is_idempotent(tmp_path: Path) -> None:
    claim_path = _write_claim(tmp_path)

    first = _run_registry(tmp_path, "record", "--claim", claim_path.relative_to(tmp_path).as_posix(), "--json")
    second = _run_registry(tmp_path, "record", "--claim", claim_path.relative_to(tmp_path).as_posix(), "--json")

    assert first.returncode == 0, first.stderr or first.stdout
    assert second.returncode == 0, second.stderr or second.stdout
    payload = json.loads(first.stdout[first.stdout.index("{") :])
    instance_path = tmp_path / payload["path"]
    instance = json.loads(instance_path.read_text(encoding="utf-8"))
    assert instance["schema"] == "agent-runtime-agent-instance/v1"
    assert instance["role"] == "qa"
    assert instance["team_id"] == "evaluation-office"
    assert instance["agent_instance_id"] == "qa-20260612-145000-kst-aa11"
    assert instance["display_name"] == "qa@review-01"
    assert instance["callsign"] == "qa@review-01"
    assert instance["callsite_id"] == "terminal:wt-task-ar-901:tab-01"
    assert instance["pane_id"] == "terminal:wt-task-ar-901:tab-01"
    assert instance["spawned_at"] == "2026-06-12T14:50:00+09:00"
    assert instance["spawned_by"] == "task_claim_dispatcher"
    assert instance["task_id"] == "TASK-AR-901"
    assert instance["task_set_id"] == "TASKSET-TEST"
    assert instance["worktree_path"] == ".worktrees/TASK-AR-901"
    assert instance["model_tier"] == "worker_standard"
    assert instance["claim_refs"] == [claim_path.relative_to(tmp_path).as_posix()]

    gate = _run_gate(tmp_path, "--check")
    assert gate.returncode == 0, gate.stdout + gate.stderr
    assert "agent-identity-gate: pass" in gate.stdout
    assert json.loads(instance_path.read_text(encoding="utf-8"))["claim_refs"] == [
        claim_path.relative_to(tmp_path).as_posix()
    ]


def test_agent_identity_gate_fails_missing_instance_record(tmp_path: Path) -> None:
    _write_claim(tmp_path)

    result = _run_gate(tmp_path, "--check")

    assert result.returncode == 1
    assert "agent-identity:instance-missing:CLAIM-20260612-145000-task-ar-901-aa11" in result.stdout


def test_agent_identity_gate_fails_mismatched_instance_record(tmp_path: Path) -> None:
    claim_path = _write_claim(tmp_path)
    recorded = _run_registry(tmp_path, "record", "--claim", claim_path.relative_to(tmp_path).as_posix(), "--json")
    assert recorded.returncode == 0, recorded.stderr or recorded.stdout
    instance_path = tmp_path / json.loads(recorded.stdout[recorded.stdout.index("{") :])["path"]
    instance = json.loads(instance_path.read_text(encoding="utf-8"))
    instance["role"] = "lead-engineer"
    instance_path.write_text(json.dumps(instance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = _run_gate(tmp_path, "--check")

    assert result.returncode == 1
    assert "agent-identity:instance-field-mismatch:CLAIM-20260612-145000-task-ar-901-aa11:role" in result.stdout


def test_agent_identity_gate_reports_role_only_attribution(tmp_path: Path) -> None:
    _write_claim(tmp_path, _claim_payload(agent_instance_id=""))

    result = _run_gate(tmp_path, "--check")

    assert result.returncode == 1
    assert "agent-identity:claim-missing:CLAIM-20260612-145000-task-ar-901-aa11:agent_instance_id" in result.stdout
    assert "agent-identity:role-only-attribution:CLAIM-20260612-145000-task-ar-901-aa11" in result.stdout


def test_agent_instance_registry_refreshes_from_committed_claim_heartbeat(
    tmp_path: Path,
) -> None:
    claim_path = _write_claim(
        tmp_path,
        _claim_payload(
            claimed_at="2026-06-12T14:50:00+09:00",
            updated_at="2026-06-12T14:50:00+09:00",
            last_heartbeat="2026-06-12T14:50:00+09:00",
            mutation_revision=0,
        ),
    )
    first = _run_registry(
        tmp_path,
        "record",
        "--claim",
        claim_path.relative_to(tmp_path).as_posix(),
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout

    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    claim["updated_at"] = "2026-06-12T15:00:00+09:00"
    claim["last_heartbeat"] = "2026-06-12T15:00:00+09:00"
    claim["mutation_revision"] = 1
    claim_path.write_text(
        json.dumps(claim, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    refreshed = _run_registry(
        tmp_path,
        "record",
        "--claim",
        claim_path.relative_to(tmp_path).as_posix(),
        "--json",
    )

    assert refreshed.returncode == 0, refreshed.stderr or refreshed.stdout
    response = json.loads(refreshed.stdout[refreshed.stdout.index("{") :])
    instance = json.loads((tmp_path / response["path"]).read_text(encoding="utf-8"))
    assert instance["spawned_at"] == "2026-06-12T14:50:00+09:00"
    assert instance["created_at"] == "2026-06-12T14:50:00+09:00"
    assert instance["updated_at"] == "2026-06-12T15:00:00+09:00"
    assert instance["last_heartbeat"] == "2026-06-12T15:00:00+09:00"
    assert instance["claim_revision"] == 1


def test_ar655_registry_revision_concurrent_newer_write_cannot_be_rolled_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial = _claim_payload(
        claimed_at="2026-06-12T14:50:00+09:00",
        updated_at="2026-06-12T14:50:00+09:00",
        last_heartbeat="2026-06-12T14:50:00+09:00",
        mutation_revision=0,
    )
    instance_path, _ = _record_claim_instance(tmp_path, initial)
    revision_one = {
        **initial,
        "updated_at": "2026-06-12T15:10:00+09:00",
        "last_heartbeat": "2026-06-12T15:10:00+09:00",
        "mutation_revision": 1,
    }
    revision_two = {
        **initial,
        "updated_at": "2026-06-12T15:20:00+09:00",
        "last_heartbeat": "2026-06-12T15:20:00+09:00",
        "mutation_revision": 2,
    }

    original_read_json = agent_instance_registry._read_json
    reader_revision = threading.local()
    both_read_revision_zero = threading.Barrier(2)
    older_entered_read = threading.Event()
    newer_write_completed = threading.Event()
    errors: list[BaseException] = []
    results: dict[int, dict[str, object]] = {}

    def controlled_read(path: Path) -> dict[str, object]:
        snapshot = original_read_json(path)
        revision = getattr(reader_revision, "value", None)
        if revision in {1, 2}:
            if revision == 1:
                older_entered_read.set()
            rendezvoused = False
            try:
                both_read_revision_zero.wait(timeout=2)
                rendezvoused = True
            except threading.BrokenBarrierError:
                # A coarse per-instance lock serializes the reads. Let the older
                # write finish so the newer writer can observe and advance it.
                pass
            if (
                revision == 1
                and rendezvoused
                and not newer_write_completed.wait(timeout=5)
            ):
                raise AssertionError("newer registry write did not complete")
        return snapshot

    monkeypatch.setattr(agent_instance_registry, "_read_json", controlled_read)

    def record_revision(revision: int, claim: dict[str, object]) -> None:
        reader_revision.value = revision
        try:
            _, payload = _record_claim_instance(tmp_path, claim)
            results[revision] = payload
        except BaseException as exc:  # thread failures are asserted in the parent
            errors.append(exc)
        finally:
            if revision == 2:
                newer_write_completed.set()

    older = threading.Thread(target=record_revision, args=(1, revision_one))
    newer = threading.Thread(target=record_revision, args=(2, revision_two))
    older.start()
    assert older_entered_read.wait(timeout=5), "older registry worker did not read"
    newer.start()
    older.join(timeout=10)
    newer.join(timeout=10)

    assert not older.is_alive() and not newer.is_alive(), "bounded registry workers did not finish"
    assert errors == []
    assert set(results) == {1, 2}
    persisted = json.loads(instance_path.read_text(encoding="utf-8"))
    assert persisted["claim_revision"] == 2
    assert persisted["updated_at"] == "2026-06-12T15:20:00+09:00"
    assert persisted["last_heartbeat"] == "2026-06-12T15:20:00+09:00"


def test_ar655_registry_revision_equal_revision_exact_replay_is_idempotent(
    tmp_path: Path,
) -> None:
    claim = _claim_payload(
        claimed_at="2026-06-12T14:50:00+09:00",
        updated_at="2026-06-12T15:00:00+09:00",
        last_heartbeat="2026-06-12T15:00:00+09:00",
        mutation_revision=1,
    )
    instance_path, first = _record_claim_instance(tmp_path, claim)
    before = instance_path.read_bytes()

    replay_path, replay = _record_claim_instance(tmp_path, dict(claim))

    assert replay_path == instance_path
    assert replay == first
    assert instance_path.read_bytes() == before


def test_ar655_registry_revision_equal_revision_nonidentical_tuple_is_refused(
    tmp_path: Path,
) -> None:
    initial = _claim_payload(
        claimed_at="2026-06-12T14:50:00+09:00",
        updated_at="2026-06-12T15:00:00+09:00",
        last_heartbeat="2026-06-12T15:00:00+09:00",
        mutation_revision=1,
    )
    instance_path, _ = _record_claim_instance(tmp_path, initial)
    non_idempotent = {
        **initial,
        "updated_at": "2026-06-12T15:01:00+09:00",
        "last_heartbeat": "2026-06-12T15:01:00+09:00",
    }

    _assert_bounded_registry_refusal_without_mutation(
        tmp_path,
        instance_path,
        non_idempotent,
    )


@pytest.mark.parametrize(
    ("updated_at", "last_heartbeat"),
    (
        (
            "2026-06-12T15:20:00+09:00",
            "2026-06-12T14:59:00+09:00",
        ),
        (
            "2026-06-12T14:59:00+09:00",
            "2026-06-12T14:59:00+09:00",
        ),
        (
            "not-a-timestamp",
            "2026-06-12T15:20:00+09:00",
        ),
        (
            "2026-06-12T15:20:00",
            "2026-06-12T15:20:00",
        ),
    ),
    ids=("torn", "regressed", "malformed", "naive"),
)
def test_ar655_registry_revision_higher_revision_invalid_timestamp_tuple_is_refused(
    tmp_path: Path,
    updated_at: str,
    last_heartbeat: str,
) -> None:
    initial = _claim_payload(
        claimed_at="2026-06-12T14:50:00+09:00",
        updated_at="2026-06-12T15:00:00+09:00",
        last_heartbeat="2026-06-12T15:00:00+09:00",
        mutation_revision=1,
    )
    instance_path, _ = _record_claim_instance(tmp_path, initial)
    invalid = {
        **initial,
        "updated_at": updated_at,
        "last_heartbeat": last_heartbeat,
        "mutation_revision": 2,
    }

    _assert_bounded_registry_refusal_without_mutation(
        tmp_path,
        instance_path,
        invalid,
    )


def test_agent_instance_registry_never_rolls_back_on_late_claim_revision(
    tmp_path: Path,
) -> None:
    claim_path = _write_claim(
        tmp_path,
        _claim_payload(
            claimed_at="2026-06-12T14:50:00+09:00",
            updated_at="2026-06-12T14:50:00+09:00",
            last_heartbeat="2026-06-12T14:50:00+09:00",
            mutation_revision=0,
        ),
    )
    initial = _run_registry(
        tmp_path,
        "record",
        "--claim",
        claim_path.relative_to(tmp_path).as_posix(),
        "--json",
    )
    assert initial.returncode == 0, initial.stderr or initial.stdout
    instance_path = tmp_path / json.loads(initial.stdout[initial.stdout.index("{") :])["path"]

    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    claim.update(
        updated_at="2026-06-12T15:20:00+09:00",
        last_heartbeat="2026-06-12T15:20:00+09:00",
        mutation_revision=2,
    )
    claim_path.write_text(
        json.dumps(claim, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    newer = _run_registry(
        tmp_path,
        "record",
        "--claim",
        claim_path.relative_to(tmp_path).as_posix(),
        "--json",
    )
    assert newer.returncode == 0, newer.stderr or newer.stdout
    newest_instance = json.loads(instance_path.read_text(encoding="utf-8"))
    assert newest_instance["updated_at"] == "2026-06-12T15:20:00+09:00"
    assert newest_instance["last_heartbeat"] == "2026-06-12T15:20:00+09:00"
    assert newest_instance["claim_revision"] == 2

    claim.update(
        updated_at="2026-06-12T15:10:00+09:00",
        last_heartbeat="2026-06-12T15:10:00+09:00",
        mutation_revision=1,
    )
    claim_path.write_text(
        json.dumps(claim, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    late = _run_registry(
        tmp_path,
        "record",
        "--claim",
        claim_path.relative_to(tmp_path).as_posix(),
        "--json",
    )

    assert late.returncode in {0, 1}
    persisted = json.loads(instance_path.read_text(encoding="utf-8"))
    assert persisted["updated_at"] == newest_instance["updated_at"]
    assert persisted["last_heartbeat"] == newest_instance["last_heartbeat"]
    assert persisted["claim_revision"] == newest_instance["claim_revision"]
