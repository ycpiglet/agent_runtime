"""TDD for scripts/role_routing.py — flag-gated dormant-role / beta routing.

SAFETY CONTRACT (the reason this module exists): other instances of this
autonomous system run LIVE in the same repo concurrently. Every behavior here
that changes *who gets work* MUST be flag-gated and DEFAULT-OFF, so that merging
the capability is INERT until the Owner enables it. These tests prove both:

  * flag OFF  -> dispatch behavior is unchanged; NO additive claim is written
                 (inertness is the load-bearing assertion);
  * flag ON   -> the additive review / scout / council / beta claims appear,
                 WITHOUT removing or mutating the original lead-engineer claim.

All state is synthetic and lives under tmp_path; nothing touches the real repo.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from agent_runtime import claim_store


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

# role_routing imports sibling scripts (atomic_io, pane_event_log) by bare name,
# matching the established pattern for scripts run with scripts/ on the path.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load():
    spec = importlib.util.spec_from_file_location(
        "role_routing", SCRIPTS_DIR / "role_routing.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _claims_dir(root: Path) -> Path:
    return root / "agents" / "runtime" / "task_claims"


def _seed_lead_claim(
    root: Path,
    *,
    task_id: str = "TASK-AR-900",
    task_set_id: str = "TASKSET-AR-900",
    initialize_authority: bool = True,
) -> dict:
    """Write a pre-existing lead-engineer claim, as the live loop would."""
    claims = _claims_dir(root)
    claims.mkdir(parents=True, exist_ok=True)
    claim = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": f"CLAIM-LEAD-{task_id}",
        "task_id": task_id,
        "task_set_id": task_set_id,
        "active_scope": task_set_id,
        "agent_role": "lead-engineer",
        "agent_instance_id": "le-seed-0001",
        "display_name": "lead_engineer@work-01",
        "status": "in_progress",
        "worktree_path": f".worktrees/{task_id}",
        "branch": f"codex/{task_id.lower()}",
    }
    (claims / f"{claim['claim_id']}.json").write_text(
        json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if initialize_authority:
        claim_store.initialize_store(root, witness_claim_id=claim["claim_id"])
    return claim


def _load_claims(root: Path) -> list[dict]:
    base = _claims_dir(root)
    if not base.is_dir():
        return []
    out: list[dict] = []
    for path in sorted(base.glob("*.json")):
        out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


def _events(root: Path) -> list[dict]:
    log = root / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def _claim_store_marker_bytes(witness_claim_id: str) -> bytes:
    return (
        json.dumps(
            {
                "schema": claim_store.MARKER_SCHEMA,
                "generation_id": "12345678-1234-4234-9234-123456789abc",
                "witness_claim_id": witness_claim_id,
            },
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _overlay_mutation_snapshot(root: Path) -> dict[str, bytes]:
    paths: list[Path] = []
    for directory in (
        _claims_dir(root),
        root / "agents" / "runtime" / "pane_events",
    ):
        if directory.is_dir():
            paths.extend(path for path in directory.rglob("*") if path.is_file())
    outer = claim_store.outer_marker_path(root)
    if outer.is_file():
        paths.append(outer)
    return {
        str(path.resolve()): path.read_bytes()
        for path in sorted(set(paths), key=lambda item: str(item))
    }


def _assert_bounded_claim_store_refusal(result: dict) -> None:
    assert result["enabled"] is True
    assert result["created"] == []
    finding = result.get("finding")
    assert isinstance(finding, str)
    assert 0 < len(finding) <= 256
    assert "\n" not in finding
    assert "Traceback" not in finding
    assert "claim-store" in finding


# ---------------------------------------------------------------------------
# Flag names are part of the public contract; pin them so a rename is caught.
# ---------------------------------------------------------------------------


def test_flag_names_are_the_documented_ones():
    mod = _load()
    assert mod.ROLE_ROUTING_FLAG == "AR_ROLE_ROUTING"
    assert mod.SCOUT_COUNCIL_FLAG == "AR_SCOUT_COUNCIL"
    assert mod.BETA_ACTIVATION_FLAG == "AR_BETA_ACTIVATION"


def test_flags_default_off(monkeypatch):
    mod = _load()
    for flag in (mod.ROLE_ROUTING_FLAG, mod.SCOUT_COUNCIL_FLAG, mod.BETA_ACTIVATION_FLAG):
        monkeypatch.delenv(flag, raising=False)
    assert mod.role_routing_enabled() is False
    assert mod.scout_council_enabled() is False
    assert mod.beta_activation_enabled() is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_flag_truthy_values_enable(monkeypatch, value):
    mod = _load()
    monkeypatch.setenv(mod.ROLE_ROUTING_FLAG, value)
    assert mod.role_routing_enabled() is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off", ""])
def test_flag_falsy_values_stay_off(monkeypatch, value):
    mod = _load()
    monkeypatch.setenv(mod.ROLE_ROUTING_FLAG, value)
    assert mod.role_routing_enabled() is False


# ---------------------------------------------------------------------------
# 1. Review-role routing (skeptic / independent-auditor) — additive.
# ---------------------------------------------------------------------------


def test_review_routing_off_is_inert(tmp_path, monkeypatch):
    monkeypatch.delenv("AR_ROLE_ROUTING", raising=False)
    mod = _load()
    _seed_lead_claim(tmp_path)
    before = _load_claims(tmp_path)

    result = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="merge", now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is False
    assert result["created"] == []
    # INERTNESS: no new claim file, the lead claim is byte-for-byte unchanged.
    after = _load_claims(tmp_path)
    assert after == before


@pytest.mark.parametrize(
    ("config_value", "env_value", "expected"),
    [(True, "0", False), (False, "1", True)],
)
def test_explicit_environment_value_overrides_committed_config(
    tmp_path, monkeypatch, config_value, env_value, expected
):
    config = tmp_path / "agents" / "project" / "role-routing.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({"role_routing": config_value}), encoding="utf-8")
    monkeypatch.setenv("AR_ROLE_ROUTING", env_value)
    mod = _load()

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is expected
    assert bool(result["created"]) is expected


def test_first_pristine_review_overlay_initializes_retained_store_witness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    assert len(result["created"]) == 1
    claim_id = result["created"][0]["claim_id"]
    inner = _claims_dir(tmp_path) / ".claim-store"
    outer = claim_store.outer_marker_path(tmp_path)
    assert inner.read_bytes() == outer.read_bytes()
    witness = json.loads(inner.read_text(encoding="utf-8"))
    assert witness["witness_claim_id"] == claim_id
    inspected = claim_store.inspect_store(tmp_path)
    assert inspected.state == "initialized"
    assert inspected.witness_claim_id == claim_id


def test_review_overlay_emits_canonical_live_renewable_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    created_at = datetime.fromisoformat("2026-06-22T10:00:00+09:00")

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now=created_at.isoformat(),
    )

    assert len(result["created"]) == 1
    overlay = result["created"][0]
    assert overlay["mutation_revision"] == 0
    assert overlay["claimed_at"] == overlay["lease"]["claimed_at"]
    assert overlay["last_heartbeat"] == overlay["lease"]["heartbeat_at"]
    assert overlay["expires_at"] == overlay["lease"]["expires_at"]
    assert datetime.fromisoformat(overlay["expires_at"]) - created_at == timedelta(
        minutes=30
    )
    liveness = claim_store.classify_claim_liveness(
        overlay,
        now=created_at + timedelta(minutes=1),
        grace_seconds=0,
    )
    assert liveness.state == "live"
    assert liveness.reason == "lease-valid"


@pytest.mark.parametrize(
    "store_state",
    ("markerless-populated", "outer-only", "malformed-pair"),
)
def test_review_overlay_refuses_untrusted_store_without_mutating_surfaces(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    store_state: str,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    lead = _seed_lead_claim(tmp_path, initialize_authority=False)
    inner = _claims_dir(tmp_path) / ".claim-store"
    outer = claim_store.outer_marker_path(tmp_path)
    if store_state == "outer-only":
        outer.parent.mkdir(parents=True, exist_ok=True)
        outer.write_bytes(_claim_store_marker_bytes(lead["claim_id"]))
    elif store_state == "malformed-pair":
        outer.parent.mkdir(parents=True, exist_ok=True)
        inner.parent.mkdir(parents=True, exist_ok=True)
        outer.write_bytes(b"{\n")
        inner.write_bytes(b"{\n")

    before = _overlay_mutation_snapshot(tmp_path)
    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_claim_store_refusal(result)
    assert _overlay_mutation_snapshot(tmp_path) == before


def test_initialized_overlay_idempotency_runs_under_lock_and_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    first = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )
    assert first["created"]
    before = _overlay_mutation_snapshot(tmp_path)
    calls = {"lock": 0, "verify_snapshot": 0}
    original_lock = mod.claim_store.store_lock
    original_verify = mod.claim_store.verify_snapshot

    @contextmanager
    def observed_lock(*args, **kwargs):
        calls["lock"] += 1
        with original_lock(*args, **kwargs):
            yield

    def observed_verify(*args, **kwargs):
        calls["verify_snapshot"] += 1
        return original_verify(*args, **kwargs)

    monkeypatch.setattr(mod.claim_store, "store_lock", observed_lock)
    monkeypatch.setattr(mod.claim_store, "verify_snapshot", observed_verify)
    second = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    assert second["created"] == []
    assert calls["lock"] >= 1
    assert calls["verify_snapshot"] >= 1
    assert _overlay_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize("suffix", ("handoff", "log"))
def test_initialized_overlay_idempotency_refuses_corrupted_regular_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    suffix: str,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    first = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )
    assert first["created"]
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    artifact = _claims_dir(tmp_path) / f"{claim_id}.{suffix}.md"
    artifact.write_bytes(f"corrupted {suffix} body\n".encode("utf-8"))
    before = _overlay_mutation_snapshot(tmp_path)

    second = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:05:00+09:00",
    )

    _assert_bounded_claim_store_refusal(second)
    assert _overlay_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize("suffix", ("handoff", "log"))
def test_initialized_overlay_idempotency_allows_append_after_required_prefix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    suffix: str,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    first = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )
    assert first["created"]
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    artifact = _claims_dir(tmp_path) / f"{claim_id}.{suffix}.md"
    appended = b"\n## Progress\n\n- independently appended evidence\n"
    with artifact.open("ab") as handle:
        handle.write(appended)
    before = _overlay_mutation_snapshot(tmp_path)

    second = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:05:00+09:00",
    )

    assert second == {"enabled": True, "created": []}
    assert artifact.read_bytes().endswith(appended)
    assert _overlay_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize("field", ["team_id", "schema"])
def test_initialized_overlay_idempotency_refuses_missing_stable_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    first = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )
    assert first["created"]
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    path = _claims_dir(tmp_path) / f"{claim_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop(field)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    before = _overlay_mutation_snapshot(tmp_path)

    second = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:05:00+09:00",
    )

    _assert_bounded_claim_store_refusal(second)
    assert _overlay_mutation_snapshot(tmp_path) == before


def test_initialized_overlay_idempotency_allows_documented_lifecycle_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    first = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )
    assert first["created"]
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    path = _claims_dir(tmp_path) / f"{claim_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(
        {
            "status": "review",
            "phase": "independent-review",
            "progress_pct": 50,
            "last_heartbeat": "2026-06-22T10:04:00+09:00",
            "updated_at": "2026-06-22T10:04:00+09:00",
        }
    )
    assert not {
        "released_at",
        "verified_by",
        "verifier_role",
        "verification_evidence",
    } & payload.keys()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    before = _overlay_mutation_snapshot(tmp_path)

    second = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:05:00+09:00",
    )

    assert second == {"enabled": True, "created": []}
    assert _overlay_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "missing_field",
    (
        "released_at",
        "verified_by",
        "verifier_role",
        "verification_evidence",
    ),
)
def test_initialized_released_overlay_refuses_missing_terminal_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing_field: str,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    first = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )
    assert first["created"]
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    path = _claims_dir(tmp_path) / f"{claim_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(
        {
            "status": "released",
            "phase": "released",
            "progress_pct": 100,
            "last_heartbeat": "2026-06-22T10:04:00+09:00",
            "updated_at": "2026-06-22T10:04:00+09:00",
            "released_at": "2026-06-22T10:04:00+09:00",
            "verified_by": "qa-20260622-100400-kst-w4b1",
            "verifier_role": "qa-reviewer",
            "verification_evidence": "reviews/VERIFY-TASK-AR-900.json",
        }
    )
    payload.pop(missing_field)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    before = _overlay_mutation_snapshot(tmp_path)

    second = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:05:00+09:00",
    )

    _assert_bounded_claim_store_refusal(second)
    assert _overlay_mutation_snapshot(tmp_path) == before
    assert missing_field not in json.loads(path.read_text(encoding="utf-8"))


def test_initialized_released_overlay_allows_complete_terminal_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    first = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )
    assert first["created"]
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    path = _claims_dir(tmp_path) / f"{claim_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(
        {
            "status": "released",
            "phase": "released",
            "progress_pct": 100,
            "last_heartbeat": "2026-06-22T10:04:00+09:00",
            "updated_at": "2026-06-22T10:04:00+09:00",
            "released_at": "2026-06-22T10:04:00+09:00",
            "verified_by": "qa-20260622-100400-kst-w4b1",
            "verifier_role": "qa-reviewer",
            "verification_evidence": "reviews/VERIFY-TASK-AR-900.json",
        }
    )
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    before = _overlay_mutation_snapshot(tmp_path)

    second = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:05:00+09:00",
    )

    assert second == {"enabled": True, "created": []}
    assert _overlay_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "existing_kind",
    ("malformed", "symlink", "identity-mismatch", "directory"),
)
def test_initialized_overlay_refuses_noncanonical_existing_claim_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    existing_kind: str,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    overlay = (
        _claims_dir(tmp_path)
        / "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge.json"
    )
    if existing_kind == "malformed":
        overlay.write_text("{not-json\n", encoding="utf-8")
    elif existing_kind == "symlink":
        outside = tmp_path / "outside-overlay.json"
        outside.write_text("{}\n", encoding="utf-8")
        try:
            overlay.symlink_to(outside)
        except OSError as exc:
            pytest.skip(f"symlink creation unavailable: {exc}")
    elif existing_kind == "identity-mismatch":
        overlay.write_text(
            json.dumps(
                {
                    "schema": "agent-runtime-task-claim/v1",
                    "claim_id": "CLAIM-REVIEW-DIFFERENT",
                    "status": "claimed",
                }
            )
            + "\n",
            encoding="utf-8",
        )
    else:
        overlay.mkdir()
    before = _overlay_mutation_snapshot(tmp_path)

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_claim_store_refusal(result)
    assert _overlay_mutation_snapshot(tmp_path) == before


def test_initialized_overlay_refuses_incomplete_matching_claim_instead_of_idempotency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    overlay = _claims_dir(tmp_path) / f"{claim_id}.json"
    overlay.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": claim_id,
                "status": "claimed",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    before = _overlay_mutation_snapshot(tmp_path)

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_claim_store_refusal(result)
    assert _overlay_mutation_snapshot(tmp_path) == before


@pytest.mark.parametrize("suffix", ("handoff", "log"))
def test_initialized_overlay_refuses_stale_artifact_without_overwriting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    suffix: str,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    stale = _claims_dir(tmp_path) / f"{claim_id}.{suffix}.md"
    stale_payload = f"pre-existing {suffix} must survive\n".encode()
    stale.write_bytes(stale_payload)
    before = _overlay_mutation_snapshot(tmp_path)

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_claim_store_refusal(result)
    assert stale.read_bytes() == stale_payload
    assert not (_claims_dir(tmp_path) / f"{claim_id}.json").exists()
    assert _overlay_mutation_snapshot(tmp_path) == before


def test_first_overlay_marker_failure_rolls_back_claim_artifacts_and_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    outer = claim_store.outer_marker_path(tmp_path)
    original_write = mod.claim_store._write_immutable

    def fail_outer(path: Path, payload: bytes) -> claim_store.PathIdentity:
        if Path(path) == outer:
            raise claim_store.ClaimStoreError("injected outer marker failure")
        return original_write(path, payload)

    monkeypatch.setattr(mod.claim_store, "_write_immutable", fail_outer)

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_claim_store_refusal(result)
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    assert not (_claims_dir(tmp_path) / f"{claim_id}.json").exists()
    assert not (_claims_dir(tmp_path) / f"{claim_id}.handoff.md").exists()
    assert not (_claims_dir(tmp_path) / f"{claim_id}.log.md").exists()
    assert not (_claims_dir(tmp_path) / ".claim-store").exists()
    assert not outer.exists()
    assert claim_store.inspect_store(tmp_path).state == "pristine"


def test_first_overlay_preserves_witness_when_inner_marker_cleanup_is_incomplete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    outer = claim_store.outer_marker_path(tmp_path)
    original_write = mod.claim_store._write_immutable
    original_remove_marker = mod.claim_store._remove_created_marker

    def fail_outer(path: Path, payload: bytes) -> claim_store.PathIdentity:
        if Path(path) == outer:
            raise claim_store.ClaimStoreError("injected outer marker failure")
        return original_write(path, payload)

    def fail_inner_marker_cleanup(
        path: Path,
        identity: claim_store.PathIdentity,
        payload: bytes,
    ) -> bool:
        if Path(path).name == ".claim-store":
            return False
        return original_remove_marker(path, identity, payload)

    monkeypatch.setattr(mod.claim_store, "_write_immutable", fail_outer)
    monkeypatch.setattr(
        mod.claim_store,
        "_remove_created_marker",
        fail_inner_marker_cleanup,
    )

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_claim_store_refusal(result)
    assert "recovery-required" in result["finding"]
    assert "witness" in result["finding"]
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    claim_dir = _claims_dir(tmp_path)
    assert (claim_dir / f"{claim_id}.json").is_file()
    assert (claim_dir / f"{claim_id}.handoff.md").is_file()
    assert (claim_dir / f"{claim_id}.log.md").is_file()
    assert (claim_dir / ".claim-store").is_file()
    assert not outer.exists()
    inspection = claim_store.inspect_store(tmp_path)
    assert inspection.state == "migration-required"
    assert inspection.witness_claim_id == claim_id


def test_overlay_writer_refuses_noncanonical_generated_claim_id_without_escape(
    tmp_path: Path,
) -> None:
    mod = _load()
    before = _overlay_mutation_snapshot(tmp_path)

    claim, finding = mod._try_write_overlay_claim(
        tmp_path,
        operation="test overlay",
        claim_id="../../ESCAPE",
        task_id="REVIEW-TASK-AR-900",
        agent_role="independent-auditor",
        mode="review",
        status_text="invalid identifier regression",
        now="2026-06-22T10:00:00+09:00",
    )

    assert claim is None
    assert isinstance(finding, str) and "claim-store" in finding
    assert not _claims_dir(tmp_path).exists()
    assert not (tmp_path / "agents" / "ESCAPE.json").exists()
    assert _overlay_mutation_snapshot(tmp_path) == before


def test_json_publish_failure_rolls_back_overlay_artifacts(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()

    def fail_json(*_args, **_kwargs):
        raise OSError("injected claim JSON failure")

    monkeypatch.setattr(mod.atomic_io, "publish_json_owned_atomic", fail_json)

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="closeout",
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_claim_store_refusal(result)
    claim_dir = _claims_dir(tmp_path)
    assert not list(claim_dir.glob("CLAIM-REVIEW-TASK-AR-900-*"))


def test_overlay_creation_has_no_fallible_post_publish_ownership_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    capture_calls: list[Path] = []

    def fail_legacy_capture(path: Path, _expected: bytes) -> None:
        capture_calls.append(Path(path))
        raise OSError("injected post-publication ownership capture failure")

    monkeypatch.setattr(
        mod,
        "_capture_created_overlay_publication",
        fail_legacy_capture,
        raising=False,
    )

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    assert "finding" not in result
    assert capture_calls == []
    assert len(result["created"]) == 1
    claim = result["created"][0]
    claim_dir = _claims_dir(tmp_path)
    assert (claim_dir / f"{claim['claim_id']}.handoff.md").is_file()
    assert (claim_dir / f"{claim['claim_id']}.log.md").is_file()
    assert (claim_dir / f"{claim['claim_id']}.json").is_file()


@pytest.mark.parametrize("failure_stage", ("claim-publication", "outer-marker"))
def test_overlay_rollback_preserves_same_bytes_competitor_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    claim_id = "CLAIM-REVIEW-TASK-AR-900-independent-auditor-merge"
    claim_dir = _claims_dir(tmp_path)
    handoff = claim_dir / f"{claim_id}.handoff.md"
    log = claim_dir / f"{claim_id}.log.md"
    claim_path = claim_dir / f"{claim_id}.json"
    replacement_identity: list[tuple[int, int]] = []
    replacement_payload: list[bytes] = []

    def replace_handoff_with_same_bytes() -> None:
        payload = handoff.read_bytes()
        competitor = handoff.with_name(f"{handoff.name}.competitor")
        competitor.write_bytes(payload)
        os.replace(competitor, handoff)
        metadata = handoff.lstat()
        replacement_identity.append((int(metadata.st_dev), int(metadata.st_ino)))
        replacement_payload.append(payload)

    if failure_stage == "claim-publication":

        def fail_claim_publication(*_args: object, **_kwargs: object) -> None:
            replace_handoff_with_same_bytes()
            raise OSError("injected claim publication failure")

        monkeypatch.setattr(
            mod.atomic_io,
            "publish_json_owned_atomic",
            fail_claim_publication,
        )
    else:
        outer = claim_store.outer_marker_path(tmp_path)
        original_write = mod.claim_store._write_immutable

        def fail_outer_marker(path: Path, payload: bytes) -> claim_store.PathIdentity:
            if Path(path) == outer:
                replace_handoff_with_same_bytes()
                raise OSError("injected outer marker publication failure")
            return original_write(path, payload)

        monkeypatch.setattr(mod.claim_store, "_write_immutable", fail_outer_marker)

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="merge",
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_claim_store_refusal(result)
    assert len(replacement_identity) == 1
    assert handoff.read_bytes() == replacement_payload[0]
    metadata = handoff.lstat()
    assert (int(metadata.st_dev), int(metadata.st_ino)) == replacement_identity[0]
    assert not log.exists()
    assert not claim_path.exists()


def test_event_log_failure_does_not_misreport_persisted_overlay(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()

    def fail_event(*_args, **_kwargs):
        raise OSError("injected pane-event write failure")

    monkeypatch.setattr(mod, "append_event", fail_event)

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="closeout",
        now="2026-06-22T10:00:00+09:00",
    )

    assert "finding" not in result
    assert len(result["created"]) == 1
    claim = result["created"][0]
    assert (_claims_dir(tmp_path) / f"{claim['claim_id']}.json").is_file()
    assert claim_store.inspect_store(tmp_path).state == "initialized"


def test_event_log_runs_after_claim_store_lock_is_released(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    lock_depth = {"value": 0}
    observed_event_depths: list[int] = []
    real_lock = mod.claim_store.store_lock
    real_event = mod.append_event

    @contextmanager
    def observed_lock(*args, **kwargs):
        with real_lock(*args, **kwargs):
            lock_depth["value"] += 1
            try:
                yield
            finally:
                lock_depth["value"] -= 1

    def observed_event(*args, **kwargs):
        observed_event_depths.append(lock_depth["value"])
        return real_event(*args, **kwargs)

    monkeypatch.setattr(mod.claim_store, "store_lock", observed_lock)
    monkeypatch.setattr(mod, "append_event", observed_event)

    result = mod.route_review_pass(
        tmp_path,
        task_id="TASK-AR-900",
        task_set_id="TASKSET-AR-900",
        event="closeout",
        now="2026-06-22T10:00:00+09:00",
    )

    assert len(result["created"]) == 1
    assert observed_event_depths == [0]


def test_review_routing_on_creates_additive_claim_without_touching_lead(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    lead = _seed_lead_claim(tmp_path)

    result = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="merge", now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    assert len(result["created"]) >= 1
    claims = _load_claims(tmp_path)
    roles = {c["agent_role"] for c in claims}
    # lead-engineer claim is still present and UNCHANGED (parallel, not replaced)
    assert "lead-engineer" in roles
    lead_after = next(c for c in claims if c["claim_id"] == lead["claim_id"])
    assert lead_after["status"] == "in_progress"
    assert lead_after["agent_role"] == "lead-engineer"
    # an additive review claim now exists for a review role
    review = [c for c in claims if c["agent_role"] in {"skeptic", "independent-auditor"}]
    assert review, f"expected a review-role claim, got roles={roles}"
    rc = review[0]
    assert rc["task_id"] != lead["task_id"], "review claim must be a distinct, additive task id"
    assert rc.get("mode") == "review" or "review" in (rc.get("tags") or [])
    assert (tmp_path / rc["handoff_path"]).is_file()
    assert (tmp_path / rc["log_path"]).is_file()
    assert rc["claim_id"] in (tmp_path / rc["handoff_path"]).read_text(encoding="utf-8")
    assert rc["claim_id"] in (tmp_path / rc["log_path"]).read_text(encoding="utf-8")
    # an event is logged so the live loop / UI can see the parallel pass
    assert any(e.get("event") == "review_pass_dispatched" for e in _events(tmp_path))


def test_review_routing_on_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    first = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="merge", now="2026-06-22T10:00:00+09:00",
    )
    second = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="merge", now="2026-06-22T10:00:00+09:00",
    )
    assert first["created"]
    assert second["created"] == [], "re-dispatch must not duplicate the review claim"


# ---------------------------------------------------------------------------
# 1b. HIGH-RISK skeptic escalation (additive on top of the auditor pass).
#
# On a high-risk closeout/merge (the claim carries an escalation_trigger in
# HIGH_RISK_TRIGGERS) the auditor pass is created as always AND an ADDITIVE
# skeptic adversarial pass is ALSO dispatched. Non-high-risk closeouts (no
# triggers, or only scope-clarity "ambiguity") stay auditor-only — fully
# back-compatible with callers that never pass triggers.
# ---------------------------------------------------------------------------


def test_high_risk_triggers_constant_excludes_bare_ambiguity():
    mod = _load()
    assert mod.HIGH_RISK_TRIGGERS == {
        "high_risk", "security", "external_effect", "cross_cutting", "repeated_failure",
    }
    # ambiguity is scope-clarity, not merge danger: deliberately NOT a skeptic trigger.
    assert "ambiguity" not in mod.HIGH_RISK_TRIGGERS


def test_high_risk_trigger_adds_skeptic_overlay_alongside_auditor(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)

    result = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="closeout", triggers=["high_risk"], now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    roles = {c["agent_role"] for c in result["created"]}
    # BOTH the default auditor pass and the additive skeptic pass are created.
    assert "independent-auditor" in roles
    assert "skeptic" in roles
    assert len(result["created"]) == 2
    for overlay in result["created"]:
        assert overlay["callsite_id"]
        assert overlay["pane_id"]
        assert overlay["phase"] == "claim-created"
        assert overlay["progress_pct"] == 0
        assert overlay["allow_parallel_task_set"] is True
        assert overlay["persistence"] == {
            "mode": "working_tree",
            "scm_commit_authorized": False,
        }
        assert overlay["parent_task_id"] == "TASK-AR-900"
        assert overlay["parent_task_set_id"] == "TASKSET-AR-900"
        assert "worktree_path" not in overlay
        assert "branch" not in overlay

    claims = _load_claims(tmp_path)
    skeptics = [c for c in claims if c["agent_role"] == "skeptic"]
    assert skeptics, "expected a skeptic overlay claim on a high-risk closeout"
    sk = skeptics[0]
    assert sk["mode"] == "review"
    assert sk.get("overlay") is True
    tags = sk.get("tags") or []
    assert "high-risk" in tags
    assert "high_risk" in tags, "the matched trigger should be tagged"
    # distinct deterministic claim id, distinct from the auditor pass.
    assert sk["claim_id"] == "CLAIM-REVIEW-TASK-AR-900-skeptic-closeout"
    auditors = [c for c in claims if c["agent_role"] == "independent-auditor"]
    assert auditors and auditors[0]["claim_id"] != sk["claim_id"]


def test_non_high_risk_trigger_is_auditor_only(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)

    result = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="closeout", triggers=["ambiguity"], now="2026-06-22T10:00:00+09:00",
    )

    roles = {c["agent_role"] for c in result["created"]}
    assert roles == {"independent-auditor"}, "ambiguity is not a merge-danger trigger"
    assert not [c for c in _load_claims(tmp_path) if c["agent_role"] == "skeptic"]


@pytest.mark.parametrize("triggers", [None, []])
def test_no_triggers_is_back_compatible_auditor_only(tmp_path, monkeypatch, triggers):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)

    result = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="closeout", triggers=triggers, now="2026-06-22T10:00:00+09:00",
    )

    roles = {c["agent_role"] for c in result["created"]}
    assert roles == {"independent-auditor"}
    assert not [c for c in _load_claims(tmp_path) if c["agent_role"] == "skeptic"]


def test_review_role_already_skeptic_does_not_double_create(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)

    result = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="closeout", review_role="skeptic", triggers=["security"],
        now="2026-06-22T10:00:00+09:00",
    )

    skeptics = [c for c in _load_claims(tmp_path) if c["agent_role"] == "skeptic"]
    assert len(skeptics) == 1, "a skeptic lead pass must not be doubled by the escalation"
    assert len(result["created"]) == 1


def test_high_risk_skeptic_overlay_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    first = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="closeout", triggers=["high_risk"], now="2026-06-22T10:00:00+09:00",
    )
    second = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="closeout", triggers=["high_risk"], now="2026-06-22T10:00:00+09:00",
    )
    assert {c["agent_role"] for c in first["created"]} == {"independent-auditor", "skeptic"}
    assert second["created"] == [], "re-dispatch must not duplicate auditor or skeptic"


def test_high_risk_off_creates_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv("AR_ROLE_ROUTING", raising=False)
    mod = _load()
    _seed_lead_claim(tmp_path)
    before = _load_claims(tmp_path)

    result = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="closeout", triggers=["high_risk"], now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is False
    assert result["created"] == []
    assert _load_claims(tmp_path) == before


# ---------------------------------------------------------------------------
# 2. progress-scout per wave + council at W6.
# ---------------------------------------------------------------------------


def test_wave_hooks_off_is_inert(tmp_path, monkeypatch):
    monkeypatch.delenv("AR_SCOUT_COUNCIL", raising=False)
    mod = _load()
    _seed_lead_claim(tmp_path)
    before = _load_claims(tmp_path)

    result = mod.dispatch_wave_hooks(
        tmp_path, task_set_id="TASKSET-AR-900", wave_no=2,
        is_w6=True, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is False
    assert result["created"] == []
    assert _load_claims(tmp_path) == before


def test_wave_hooks_on_dispatches_scout_per_wave(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_SCOUT_COUNCIL", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)

    result = mod.dispatch_wave_hooks(
        tmp_path, task_set_id="TASKSET-AR-900", wave_no=2,
        is_w6=False, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    claims = _load_claims(tmp_path)
    scouts = [c for c in claims if c["agent_role"] == "progress-scout"]
    assert scouts, "a progress-scout sweep claim should be created for the wave"
    # not W6, so NO council deliberation yet
    assert not [c for c in claims if c["agent_role"] == "council"]
    assert any(e.get("event") == "progress_scout_sweep" for e in _events(tmp_path))


def test_wave_hooks_on_at_w6_adds_council(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_SCOUT_COUNCIL", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)

    result = mod.dispatch_wave_hooks(
        tmp_path, task_set_id="TASKSET-AR-900", wave_no=6,
        is_w6=True, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    claims = _load_claims(tmp_path)
    assert [c for c in claims if c["agent_role"] == "progress-scout"]
    assert [c for c in claims if c["agent_role"] == "council"], "W6 boundary should add a council deliberation"
    events = {e.get("event") for e in _events(tmp_path)}
    assert "progress_scout_sweep" in events
    assert "council_deliberation" in events


# ---------------------------------------------------------------------------
# 3. beta activation when beta_tester_due reports due/overdue.
# ---------------------------------------------------------------------------


def test_beta_activation_off_is_inert(tmp_path, monkeypatch):
    monkeypatch.delenv("AR_BETA_ACTIVATION", raising=False)
    mod = _load()
    before = _load_claims(tmp_path)

    result = mod.maybe_activate_beta(
        tmp_path, due_state="overdue", cycle=7, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is False
    assert result["created"] == []
    assert _load_claims(tmp_path) == before
    # no BTC scaffold either
    assert not list((tmp_path / "agents" / "beta_tester" / "test_cases").glob("BTC-*.md")) \
        if (tmp_path / "agents" / "beta_tester" / "test_cases").is_dir() else True


def test_beta_activation_on_but_not_due_is_inert(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_BETA_ACTIVATION", "1")
    mod = _load()
    before = _load_claims(tmp_path)

    result = mod.maybe_activate_beta(
        tmp_path, due_state="ok", cycle=7, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    assert result["due"] is False
    assert result["created"] == []
    assert _load_claims(tmp_path) == before


@pytest.mark.parametrize("due_state", ["due", "overdue"])
def test_beta_activation_on_and_due_emits_claim_and_btc_scaffold(tmp_path, monkeypatch, due_state):
    monkeypatch.setenv("AR_BETA_ACTIVATION", "1")
    mod = _load()

    result = mod.maybe_activate_beta(
        tmp_path, due_state=due_state, cycle=7, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    assert result["due"] is True
    assert result["created"], "a beta_tester claim should be emitted when due/overdue + flag on"
    claims = _load_claims(tmp_path)
    beta = [c for c in claims if c["agent_role"] in {"beta-tester", "beta_tester"}]
    assert beta, "expected a beta_tester claim"
    # BTC-* scaffold appears under the beta_tester test_cases dir
    btc = list((tmp_path / "agents" / "beta_tester" / "test_cases").glob("BTC-*.md"))
    assert btc, "expected a BTC-* scaffold file"
    assert any(e.get("event") == "beta_round_dispatched" for e in _events(tmp_path))


def test_beta_activation_on_and_due_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_BETA_ACTIVATION", "1")
    mod = _load()
    first = mod.maybe_activate_beta(tmp_path, due_state="overdue", cycle=7,
                                    now="2026-06-22T10:00:00+09:00")
    second = mod.maybe_activate_beta(tmp_path, due_state="overdue", cycle=7,
                                     now="2026-06-22T10:00:00+09:00")
    assert first["created"]
    assert first["scaffold"]["status"] == "created"
    assert second["created"] == [], "the same cycle's beta round must not be dispatched twice"
    assert second["scaffold"]["status"] == "existing"


def _assert_bounded_beta_scaffold_refusal(result: dict) -> None:
    finding = result.get("finding")
    assert isinstance(finding, str) and finding
    assert len(finding) <= 256
    assert "traceback" not in finding.casefold()
    assert result["scaffold"]["status"] == "refused"


@pytest.mark.parametrize("unsafe_parent", ["file", "alias"])
@pytest.mark.parametrize("force_portable", [False, True])
def test_beta_scaffold_refuses_non_directory_or_alias_parent_without_escape(
    tmp_path,
    monkeypatch,
    unsafe_parent,
    force_portable,
):
    monkeypatch.setenv("AR_BETA_ACTIVATION", "1")
    mod = _load()
    if force_portable:
        monkeypatch.setattr(mod, "_secure_dir_fd_available", lambda: False)
    beta_root = tmp_path / "agents" / "beta_tester"
    beta_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    test_cases = beta_root / "test_cases"
    if unsafe_parent == "file":
        test_cases.write_text("not a directory", encoding="utf-8")
    else:
        test_cases.symlink_to(outside, target_is_directory=True)

    result = mod.maybe_activate_beta(
        tmp_path,
        due_state="overdue",
        cycle=8,
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_beta_scaffold_refusal(result)
    assert result["created"], "the already-persisted claim must remain truthfully reported"
    assert not list(outside.iterdir()), "an aliased parent must never receive a BTC file"
    inspection = claim_store.inspect_store(tmp_path)
    assert inspection.state == "initialized"
    assert inspection.witness_claim_id == result["created"][0]["claim_id"]


@pytest.mark.parametrize("force_portable", [False, True])
def test_beta_scaffold_refuses_dangling_final_symlink_without_escape(
    tmp_path,
    monkeypatch,
    force_portable,
):
    monkeypatch.setenv("AR_BETA_ACTIVATION", "1")
    mod = _load()
    if force_portable:
        monkeypatch.setattr(mod, "_secure_dir_fd_available", lambda: False)
    test_cases = tmp_path / "agents" / "beta_tester" / "test_cases"
    test_cases.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    escaped = outside / "escaped.md"
    btc = test_cases / "BTC-CYCLE-009-001.md"
    btc.symlink_to(escaped)

    result = mod.maybe_activate_beta(
        tmp_path,
        due_state="due",
        cycle=9,
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_beta_scaffold_refusal(result)
    assert result["created"], "the already-persisted claim must remain truthfully reported"
    assert btc.is_symlink()
    assert not escaped.exists(), "a dangling BTC alias must never be followed"


def test_beta_scaffold_failure_preserves_created_claim_in_result(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_BETA_ACTIVATION", "1")
    mod = _load()

    def fail_scaffold(*_args, **_kwargs):
        raise OSError("simulated scaffold publication failure")

    # ``raising=False`` keeps this failure-first test red before the dedicated
    # publication boundary exists; the production path must call the helper.
    monkeypatch.setattr(mod, "_write_btc_scaffold_atomic", fail_scaffold, raising=False)
    result = mod.maybe_activate_beta(
        tmp_path,
        due_state="overdue",
        cycle=10,
        now="2026-06-22T10:00:00+09:00",
    )

    _assert_bounded_beta_scaffold_refusal(result)
    assert [item["claim_id"] for item in result["created"]] == [
        "CLAIM-BETA-CYCLE-010"
    ]
    persisted = _load_claims(tmp_path)
    assert [item["claim_id"] for item in persisted] == ["CLAIM-BETA-CYCLE-010"]
    inspection = claim_store.inspect_store(tmp_path)
    assert inspection.state == "initialized"
    assert inspection.witness_claim_id == "CLAIM-BETA-CYCLE-010"
