"""Failure-first contract tests for durable task-claim store authority.

These tests intentionally describe the TASK-AR-654 continuity contract before
``agent_runtime.claim_store`` exists.  A claim store is either genuinely
pristine, explicitly migration-required, initialized by a matching immutable
marker pair, or integrity-invalid.  In particular, a newly-created empty
directory must not erase the remembered authority of a previously initialized
store.  A valid tracked inner marker in a fresh Git clone is an explicit
checkout-activation migration, while an outer-only marker remains invalid.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

from agent_runtime import claim_store


ROOT = Path(__file__).resolve().parents[1]
INNER_MARKER_NAME = ".claim-store"


def _runtime_root(tmp_path: Path, name: str = "host") -> Path:
    root = tmp_path / name
    (root / "agents" / "runtime").mkdir(parents=True)
    return root


def _store(root: Path) -> Path:
    return root / "agents" / "runtime" / "task_claims"


def _marker_paths(root: Path) -> tuple[Path, Path]:
    outer = claim_store.outer_marker_path(root)
    inner = _store(root) / INNER_MARKER_NAME
    return outer, inner


def _write_claim(root: Path, claim_id: str, *, status: str = "claimed") -> Path:
    store = _store(root)
    store.mkdir(parents=True, exist_ok=True)
    path = store / f"{claim_id}.json"
    path.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": claim_id,
                "task_id": "TASK-AR-654",
                "unit_id": "UNIT-TASK-AR-654-001",
                "agent_instance_id": f"worker-{claim_id.lower()}",
                "status": status,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _assert_bounded_finding(result: object, expected_state: str) -> str:
    assert result.state == expected_state
    assert isinstance(result.finding, str)
    assert result.finding
    assert len(result.finding) <= 256
    assert "\n" not in result.finding
    assert "Traceback" not in result.finding
    return result.finding


def _assert_integrity_invalid(result: object) -> str:
    return _assert_bounded_finding(result, "integrity-invalid")


def _assert_initialized_pair(
    root: Path,
    *,
    witness_claim_id: str,
) -> tuple[dict[str, object], bytes]:
    outer, inner = _marker_paths(root)
    assert outer.name == "task-claim-store"
    assert outer.suffix != ".json"
    assert inner.name == INNER_MARKER_NAME
    assert inner.suffix != ".json"
    assert outer.is_file()
    assert inner.is_file()

    outer_bytes = outer.read_bytes()
    assert outer_bytes == inner.read_bytes()
    assert len(outer_bytes) <= claim_store.MARKER_MAX_BYTES

    payload = json.loads(outer_bytes.decode("utf-8"))
    assert set(payload) == {"schema", "generation_id", "witness_claim_id"}
    assert payload["schema"] == "agent-runtime-task-claim-store/v1"
    generation = uuid.UUID(str(payload["generation_id"]))
    assert generation.version == 4
    assert str(generation) == payload["generation_id"]
    assert payload["witness_claim_id"] == witness_claim_id
    return payload, outer_bytes


def _raw_marker_bytes(witness_claim_id: str) -> bytes:
    return (
        json.dumps(
            {
                "schema": "agent-runtime-task-claim-store/v1",
                "generation_id": str(uuid.uuid4()),
                "witness_claim_id": witness_claim_id,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


@pytest.mark.parametrize("store_state", ("absent", "empty"))
def test_absent_or_truly_empty_never_used_store_is_pristine(
    tmp_path: Path,
    store_state: str,
) -> None:
    root = _runtime_root(tmp_path)
    if store_state == "empty":
        _store(root).mkdir()

    result = claim_store.inspect_store(root)

    assert result.state == "pristine"
    assert result.finding is None
    assert result.generation_id is None
    assert result.witness_claim_id is None
    assert result.snapshot is not None
    outer, inner = _marker_paths(root)
    assert not outer.exists()
    assert not inner.exists()


@pytest.mark.parametrize("entry_name", ("CLAIM-legacy.json", "legacy-artifact"))
def test_nonempty_markerless_store_requires_explicit_migration(
    tmp_path: Path,
    entry_name: str,
) -> None:
    root = _runtime_root(tmp_path)
    store = _store(root)
    store.mkdir()
    (store / entry_name).write_text("{}\n", encoding="utf-8")

    result = claim_store.inspect_store(root)

    finding = _assert_bounded_finding(result, "migration-required")
    assert "migration" in finding
    assert result.generation_id is None
    assert result.witness_claim_id is None


def test_explicit_legacy_adoption_creates_one_canonical_marker_pair(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-older", status="released")
    _write_claim(root, "CLAIM-retained")
    assert claim_store.inspect_store(root).state == "migration-required"

    claim_store.adopt_legacy_store(root, witness_claim_id="CLAIM-retained")

    payload, _ = _assert_initialized_pair(
        root,
        witness_claim_id="CLAIM-retained",
    )
    result = claim_store.inspect_store(root)
    assert result.state == "initialized"
    assert result.finding is None
    assert result.generation_id == payload["generation_id"]
    assert result.witness_claim_id == "CLAIM-retained"
    assert result.snapshot is not None


def test_adoption_candidate_enumeration_is_bounded_by_store_entry_limit(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    store = _store(root)
    store.mkdir()
    for index in range(claim_store.MAX_STORE_ENTRIES + 1):
        (store / f"artifact-{index:05d}").write_bytes(b"")

    with pytest.raises(claim_store.ClaimStoreError, match="bounded limit"):
        claim_store._adoption_candidates(root)


def test_first_claim_initialization_creates_a_valid_initialized_pair(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-first")

    claim_store.initialize_store(root, witness_claim_id="CLAIM-first")

    payload, _ = _assert_initialized_pair(root, witness_claim_id="CLAIM-first")
    result = claim_store.inspect_store(root)
    assert result.state == "initialized"
    assert result.generation_id == payload["generation_id"]
    assert claim_store.verify_snapshot(root, result.snapshot) is True


def test_initialization_rejects_witness_with_unknown_status_without_markers(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-invalid-status", status="mystery")
    outer, inner = _marker_paths(root)

    with pytest.raises(claim_store.ClaimStoreError):
        claim_store.initialize_store(
            root,
            witness_claim_id="CLAIM-invalid-status",
        )

    assert not outer.exists()
    assert not inner.exists()
    assert claim_store.inspect_store(root).state == "migration-required"


@pytest.mark.parametrize(
    "raw_claim",
    (
        pytest.param(
            '{"schema":"agent-runtime-task-claim/v1",'
            '"claim_id":"CLAIM-strict-json",'
            '"status":"claimed","progress_pct":NaN}\n',
            id="non-finite-number",
        ),
        pytest.param(
            '{"schema":"agent-runtime-task-claim/v1",'
            '"claim_id":"CLAIM-strict-json",'
            '"status":"claimed","progress_pct":1e9999}\n',
            id="positive-exponent-overflow",
        ),
        pytest.param(
            '{"schema":"agent-runtime-task-claim/v1",'
            '"claim_id":"CLAIM-strict-json",'
            '"status":"claimed","progress_pct":-1e9999}\n',
            id="negative-exponent-overflow",
        ),
        pytest.param(
            '{"schema":"agent-runtime-task-claim/v1",'
            '"claim_id":"CLAIM-strict-json",'
            '"claim_id":"CLAIM-strict-json",'
            '"status":"claimed"}\n',
            id="duplicate-key",
        ),
    ),
)
def test_shared_claim_reader_rejects_nonstandard_json_values(
    tmp_path: Path,
    raw_claim: str,
) -> None:
    root = _runtime_root(tmp_path)
    path = _write_claim(root, "CLAIM-strict-json")
    path.write_text(raw_claim, encoding="utf-8")

    with pytest.raises(claim_store.ClaimStoreError):
        claim_store.read_claim_payload(path)


def test_initialization_is_idempotent_but_never_rebinds_an_existing_pair(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-first")
    _write_claim(root, "CLAIM-second")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-first")
    outer, inner = _marker_paths(root)
    before = (outer.read_bytes(), inner.read_bytes())

    claim_store.initialize_store(root, witness_claim_id="CLAIM-first")
    assert (outer.read_bytes(), inner.read_bytes()) == before

    with pytest.raises(claim_store.ClaimStoreError):
        claim_store.initialize_store(root, witness_claim_id="CLAIM-second")
    assert (outer.read_bytes(), inner.read_bytes()) == before


def test_adoption_refuses_to_bless_a_missing_witness_without_writing_markers(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-present")
    outer, inner = _marker_paths(root)

    with pytest.raises(claim_store.ClaimStoreError):
        claim_store.adopt_legacy_store(root, witness_claim_id="CLAIM-missing")

    assert not outer.exists()
    assert not inner.exists()
    assert claim_store.inspect_store(root).state == "migration-required"


def test_inner_only_initialized_store_requires_explicit_checkout_activation(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, inner = _marker_paths(root)
    marker_bytes = inner.read_bytes()
    outer.unlink()

    result = claim_store.inspect_store(root)

    finding = _assert_bounded_finding(result, "migration-required")
    assert "activation" in finding or "checkout" in finding
    assert result.generation_id == json.loads(marker_bytes)["generation_id"]
    assert result.witness_claim_id == "CLAIM-retained"
    assert result.snapshot is not None
    assert claim_store.verify_snapshot(root, result.snapshot) is True
    assert inner.read_bytes() == marker_bytes
    assert not outer.exists()


def test_explicit_adoption_activates_inner_only_store_with_identical_outer_marker(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, inner = _marker_paths(root)
    marker_bytes = inner.read_bytes()
    outer.unlink()

    result = claim_store.adopt_legacy_store(root)

    assert result.state == "initialized"
    assert result.witness_claim_id == "CLAIM-retained"
    assert inner.read_bytes() == marker_bytes
    assert outer.read_bytes() == marker_bytes


def test_inner_only_activation_rejects_witness_rebinding_without_mutation(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    _write_claim(root, "CLAIM-other")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, inner = _marker_paths(root)
    marker_bytes = inner.read_bytes()
    outer.unlink()

    with pytest.raises(claim_store.ClaimStoreError, match="rebound"):
        claim_store.adopt_legacy_store(root, witness_claim_id="CLAIM-other")

    assert inner.read_bytes() == marker_bytes
    assert not outer.exists()


def test_initialize_does_not_implicitly_activate_an_inner_only_checkout(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, inner = _marker_paths(root)
    marker_bytes = inner.read_bytes()
    outer.unlink()

    with pytest.raises(claim_store.ClaimStoreError, match="explicit legacy adoption"):
        claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")

    assert inner.read_bytes() == marker_bytes
    assert not outer.exists()


@pytest.mark.parametrize(
    "marker_bytes",
    (
        b"{\n",
        b'{"generation_id":"8b42e19f-0143-4aa5-88cd-c4ce5a2c1e10",'
        b'"schema":"wrong","witness_claim_id":"CLAIM-retained"}\n',
        b'{"generation_id":"not-a-uuid",'
        b'"schema":"agent-runtime-task-claim-store/v1",'
        b'"witness_claim_id":"CLAIM-retained"}\n',
        b'{"generation_id":"8b42e19f-0143-4aa5-88cd-c4ce5a2c1e10",'
        b'"schema":"agent-runtime-task-claim-store/v1",'
        b'"witness_claim_id":"invalid"}\n',
        b" " * (claim_store.MARKER_MAX_BYTES + 1),
    ),
)
def test_inner_only_store_with_invalid_bounded_marker_is_integrity_invalid(
    tmp_path: Path,
    marker_bytes: bytes,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    inner = _store(root) / INNER_MARKER_NAME
    inner.write_bytes(marker_bytes)

    finding = _assert_integrity_invalid(claim_store.inspect_store(root))

    assert "marker" in finding or "malformed" in finding or "size" in finding


def test_inner_only_store_without_retained_witness_is_integrity_invalid(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    witness = _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, _ = _marker_paths(root)
    outer.unlink()
    witness.unlink()

    finding = _assert_integrity_invalid(claim_store.inspect_store(root))

    assert "witness" in finding or "missing" in finding


@pytest.mark.parametrize("operation", ("initialize", "adopt"))
def test_mutation_api_never_repairs_or_blesses_an_outer_only_pair(
    tmp_path: Path,
    operation: str,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, inner = _marker_paths(root)
    outer_before = outer.read_bytes()
    inner.unlink()

    mutate = {
        "initialize": claim_store.initialize_store,
        "adopt": claim_store.adopt_legacy_store,
    }[operation]
    with pytest.raises(claim_store.ClaimStoreError):
        mutate(root, witness_claim_id="CLAIM-retained")

    assert outer.read_bytes() == outer_before
    assert not inner.exists()
    _assert_integrity_invalid(claim_store.inspect_store(root))


def test_outer_only_marker_pair_is_integrity_invalid(tmp_path: Path) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, inner = _marker_paths(root)
    inner.unlink()

    result = claim_store.inspect_store(root)

    finding = _assert_integrity_invalid(result)
    assert "marker" in finding or "witness" in finding


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("CLAIM-valid-1", True),
        ("CLAIM-a.b_c", True),
        ("CLAIM-", False),
        ("claim-lower", False),
        (None, False),
        (123, False),
    ),
)
def test_public_claim_id_validator_uses_canonical_contract(
    value: object,
    expected: bool,
) -> None:
    assert claim_store.valid_claim_id(value) is expected


def test_byte_mismatched_marker_pair_is_integrity_invalid(tmp_path: Path) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, inner = _marker_paths(root)
    inner.write_bytes(outer.read_bytes() + b" ")

    result = claim_store.inspect_store(root)

    finding = _assert_integrity_invalid(result)
    assert "mismatch" in finding or "marker" in finding


@pytest.mark.parametrize("aliased_side", ("outer", "inner"))
def test_marker_alias_is_integrity_invalid_even_when_bytes_match(
    tmp_path: Path,
    aliased_side: str,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, inner = _marker_paths(root)
    alias, target = (outer, inner) if aliased_side == "outer" else (inner, outer)
    alias.unlink()
    try:
        alias.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    result = claim_store.inspect_store(root)

    finding = _assert_integrity_invalid(result)
    assert "alias" in finding or "marker" in finding or "link" in finding


@pytest.mark.parametrize(
    "marker_bytes",
    (
        b"{",
        b"\xff",
        b'{"schema":"wrong"}',
    ),
)
def test_identical_but_malformed_marker_pair_is_integrity_invalid(
    tmp_path: Path,
    marker_bytes: bytes,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    outer, inner = _marker_paths(root)
    outer.parent.mkdir(parents=True, exist_ok=True)
    inner.parent.mkdir(parents=True, exist_ok=True)
    outer.write_bytes(marker_bytes)
    inner.write_bytes(marker_bytes)

    result = claim_store.inspect_store(root)

    finding = _assert_integrity_invalid(result)
    assert "marker" in finding or "schema" in finding


def test_oversized_marker_pair_is_rejected_with_a_bounded_finding(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    outer, inner = _marker_paths(root)
    outer.parent.mkdir(parents=True, exist_ok=True)
    oversized = b" " * (claim_store.MARKER_MAX_BYTES + 1)
    outer.write_bytes(oversized)
    inner.write_bytes(oversized)

    result = claim_store.inspect_store(root)

    finding = _assert_integrity_invalid(result)
    assert "large" in finding or "size" in finding or "marker" in finding


def test_initialized_pair_without_retained_witness_is_integrity_invalid(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    witness = _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    witness.unlink()

    result = claim_store.inspect_store(root)

    finding = _assert_integrity_invalid(result)
    assert "witness" in finding or "claim" in finding


def test_initialized_pair_rejects_aliased_retained_witness(tmp_path: Path) -> None:
    root = _runtime_root(tmp_path)
    witness = _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    hidden = root / "hidden-witness.json"
    witness.rename(hidden)
    try:
        witness.symlink_to(hidden)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    result = claim_store.inspect_store(root)

    finding = _assert_integrity_invalid(result)
    assert "witness" in finding or "alias" in finding or "link" in finding


def test_replacing_initialized_store_with_a_direct_empty_directory_is_invalid(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, _ = _marker_paths(root)
    outer_before = outer.read_bytes()
    hidden = root / "hidden-populated-claim-store"
    _store(root).rename(hidden)
    _store(root).mkdir()

    result = claim_store.inspect_store(root)

    _assert_integrity_invalid(result)
    assert outer.read_bytes() == outer_before
    assert (hidden / "CLAIM-retained.json").is_file()


@pytest.mark.parametrize("replaced_target", ("store", "outer-marker"))
def test_snapshot_revalidation_rejects_byte_identical_authority_replacement(
    tmp_path: Path,
    replaced_target: str,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    inspected = claim_store.inspect_store(root)
    assert inspected.state == "initialized"
    assert claim_store.verify_snapshot(root, inspected.snapshot) is True

    if replaced_target == "store":
        hidden = root / "original-claim-store"
        _store(root).rename(hidden)
        shutil.copytree(hidden, _store(root))
        assert (_store(root) / INNER_MARKER_NAME).read_bytes() == (
            hidden / INNER_MARKER_NAME
        ).read_bytes()
    else:
        outer, _ = _marker_paths(root)
        hidden = outer.with_name("original-task-claim-store")
        outer.rename(hidden)
        shutil.copy2(hidden, outer)
        assert outer.read_bytes() == hidden.read_bytes()

    assert claim_store.verify_snapshot(root, inspected.snapshot) is False


def test_snapshot_revalidation_rejects_non_witness_mutation_during_final_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    other = _write_claim(root, "CLAIM-other")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    inspected = claim_store.inspect_store(root)
    assert inspected.state == "initialized"
    assert claim_store.verify_snapshot(root, inspected.snapshot) is True
    original_validate = claim_store._validate_snapshot_identity
    mutated = False

    def validate_after_non_witness_mutation(
        path: Path,
        identity: object,
        kind: str,
        **kwargs: object,
    ) -> None:
        nonlocal mutated
        if not mutated:
            other.write_text(
                json.dumps(
                    {
                        "schema": "agent-runtime-task-claim/v1",
                        "claim_id": "CLAIM-other",
                        "status": "released",
                        "mutation": "during-final-validation",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            mutated = True
        original_validate(path, identity, kind, **kwargs)

    monkeypatch.setattr(
        claim_store,
        "_validate_snapshot_identity",
        validate_after_non_witness_mutation,
    )

    assert claim_store.verify_snapshot(root, inspected.snapshot) is False
    assert mutated is True


@pytest.mark.parametrize("replaced_ancestor", ("agents", "runtime", "outer-anchor"))
def test_snapshot_revalidation_rejects_ancestor_alias_replacement(
    tmp_path: Path,
    replaced_ancestor: str,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    inspected = claim_store.inspect_store(root)
    assert inspected.state == "initialized"
    assert claim_store.verify_snapshot(root, inspected.snapshot) is True

    targets = {
        "agents": root / "agents",
        "runtime": root / "agents" / "runtime",
        "outer-anchor": claim_store.outer_marker_path(root).parent,
    }
    target = targets[replaced_ancestor]
    hidden = tmp_path / f"original-{replaced_ancestor}"
    target.rename(hidden)
    try:
        target.symlink_to(hidden, target_is_directory=True)
    except OSError as exc:
        hidden.rename(target)
        pytest.skip(f"directory symlink creation unavailable: {exc}")

    assert claim_store.verify_snapshot(root, inspected.snapshot) is False
    _assert_integrity_invalid(claim_store.inspect_store(root))


def test_pristine_absence_snapshot_is_invalidated_when_store_appears(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    inspected = claim_store.inspect_store(root)
    assert inspected.state == "pristine"
    assert claim_store.verify_snapshot(root, inspected.snapshot) is True

    _store(root).mkdir()

    assert claim_store.verify_snapshot(root, inspected.snapshot) is False


def test_inspection_rejects_store_swap_between_snapshot_and_revalidation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    original_loads = claim_store.json.loads
    swapped = False

    def loads_after_swap(value: object, *args: object, **kwargs: object) -> object:
        nonlocal swapped
        if not swapped:
            hidden = root / "store-before-inspection-swap"
            _store(root).rename(hidden)
            shutil.copytree(hidden, _store(root))
            swapped = True
        return original_loads(value, *args, **kwargs)

    monkeypatch.setattr(claim_store.json, "loads", loads_after_swap)

    result = claim_store.inspect_store(root)

    assert swapped is True
    finding = _assert_integrity_invalid(result)
    assert "changed" in finding or "snapshot" in finding or "replaced" in finding


def test_inspection_rejects_population_after_missing_agents_was_observed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "host"
    root.mkdir()
    agents = root / "agents"
    outer = claim_store.outer_marker_path(root)
    original_lstat = Path.lstat
    populated = False

    def lstat_then_populate(path: Path) -> os.stat_result:
        nonlocal populated
        try:
            return original_lstat(path)
        except FileNotFoundError:
            if path == agents and not populated:
                populated = True
                witness = _write_claim(root, "CLAIM-late")
                assert witness.is_file()
                marker = _raw_marker_bytes("CLAIM-late")
                (_store(root) / INNER_MARKER_NAME).write_bytes(marker)
                outer.parent.mkdir(parents=True, exist_ok=True)
                outer.write_bytes(marker)
            raise

    monkeypatch.setattr(Path, "lstat", lstat_then_populate)

    result = claim_store.inspect_store(root)

    assert populated is True
    finding = _assert_integrity_invalid(result)
    assert "changed" in finding or "snapshot" in finding or "inconsistent" in finding


@pytest.mark.parametrize(
    "replaced_ancestor",
    ("agents", "runtime", "store", "outer-anchor"),
)
def test_inspection_rejects_ancestor_alias_installed_after_directness_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replaced_ancestor: str,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    targets = {
        "agents": root / "agents",
        "runtime": root / "agents" / "runtime",
        "store": _store(root),
        "outer-anchor": claim_store.outer_marker_path(root).parent,
    }
    target = targets[replaced_ancestor]
    hidden = tmp_path / f"direct-{replaced_ancestor}"
    original_require_direct = claim_store._require_direct
    replaced = False

    def require_then_replace(
        path: Path,
        kind: str,
        *,
        missing_ok: bool = False,
    ) -> claim_store.PathIdentity:
        nonlocal replaced
        identity = original_require_direct(path, kind, missing_ok=missing_ok)
        if path == target and not replaced:
            target.rename(hidden)
            try:
                target.symlink_to(hidden, target_is_directory=True)
            except OSError as exc:
                hidden.rename(target)
                pytest.skip(f"directory symlink creation unavailable: {exc}")
            replaced = True
        return identity

    monkeypatch.setattr(claim_store, "_require_direct", require_then_replace)

    result = claim_store.inspect_store(root)

    assert replaced is True
    finding = _assert_integrity_invalid(result)
    assert "alias" in finding or "changed" in finding or "snapshot" in finding


@pytest.mark.parametrize("replaced_entry", ("witness", "artifact"))
def test_markerless_adoption_rolls_back_its_pair_when_store_entries_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replaced_entry: str,
) -> None:
    root = _runtime_root(tmp_path)
    witness = _write_claim(root, "CLAIM-retained")
    artifact = _store(root) / "retained.log.md"
    artifact.write_text("retained\n", encoding="utf-8")
    selected = witness if replaced_entry == "witness" else artifact
    hidden = tmp_path / f"original-{selected.name}"
    outer, inner = _marker_paths(root)
    original_write = claim_store._write_immutable
    replaced = False

    def write_then_replace(path: Path, payload: bytes) -> object:
        nonlocal replaced
        result = original_write(path, payload)
        if path == outer and not replaced:
            selected.rename(hidden)
            shutil.copy2(hidden, selected)
            replaced = True
        return result

    monkeypatch.setattr(claim_store, "_write_immutable", write_then_replace)

    with pytest.raises(claim_store.ClaimStoreError, match="changed|continuity"):
        claim_store.adopt_legacy_store(
            root,
            witness_claim_id="CLAIM-retained",
        )

    assert replaced is True
    assert not inner.exists()
    assert not outer.exists()
    assert selected.read_bytes() == hidden.read_bytes()


def test_markerless_adoption_rolls_back_inner_when_outer_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _runtime_root(tmp_path)
    witness = _write_claim(root, "CLAIM-retained")
    witness_before = witness.read_bytes()
    outer, inner = _marker_paths(root)
    original_write = claim_store._write_immutable

    def fail_outer(path: Path, payload: bytes) -> object:
        if path == outer:
            raise claim_store.ClaimStoreError("injected outer marker failure")
        return original_write(path, payload)

    monkeypatch.setattr(claim_store, "_write_immutable", fail_outer)

    with pytest.raises(claim_store.ClaimStoreError, match="injected"):
        claim_store.adopt_legacy_store(
            root,
            witness_claim_id="CLAIM-retained",
        )

    assert witness.read_bytes() == witness_before
    assert not inner.exists()
    assert not outer.exists()
    assert claim_store.inspect_store(root).state == "migration-required"


@pytest.mark.parametrize("failure", ("write", "fsync"))
def test_immutable_marker_write_cleans_up_its_inode_on_io_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    root = _runtime_root(tmp_path)
    marker = _store(root) / INNER_MARKER_NAME
    marker.parent.mkdir()
    payload = _raw_marker_bytes("CLAIM-retained")

    if failure == "write":
        def fail_write(_descriptor: int, _payload: object) -> int:
            raise OSError("injected marker write failure")

        monkeypatch.setattr(claim_store.os, "write", fail_write)
    else:
        def fail_fsync(_descriptor: int) -> None:
            raise OSError("injected marker fsync failure")

        monkeypatch.setattr(claim_store.os, "fsync", fail_fsync)

    with pytest.raises(claim_store.ClaimStoreError, match="marker write failed"):
        claim_store._write_immutable(marker, payload)

    assert not marker.exists()


@pytest.mark.parametrize("replaced_entry", ("witness", "artifact"))
def test_checkout_activation_rolls_back_outer_when_store_entries_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replaced_entry: str,
) -> None:
    root = _runtime_root(tmp_path)
    witness = _write_claim(root, "CLAIM-retained")
    artifact = _store(root) / "retained.log.md"
    artifact.write_text("retained\n", encoding="utf-8")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, inner = _marker_paths(root)
    inner_before = inner.read_bytes()
    outer.unlink()
    selected = witness if replaced_entry == "witness" else artifact
    hidden = tmp_path / f"original-activation-{selected.name}"
    original_write = claim_store._write_immutable
    replaced = False

    def write_then_replace(path: Path, payload: bytes) -> object:
        nonlocal replaced
        result = original_write(path, payload)
        if path == outer and not replaced:
            selected.rename(hidden)
            shutil.copy2(hidden, selected)
            replaced = True
        return result

    monkeypatch.setattr(claim_store, "_write_immutable", write_then_replace)

    with pytest.raises(claim_store.ClaimStoreError, match="changed|continuity"):
        claim_store.adopt_legacy_store(root)

    assert replaced is True
    assert inner.read_bytes() == inner_before
    assert not outer.exists()
    assert selected.read_bytes() == hidden.read_bytes()
    assert claim_store.inspect_store(root).state == "migration-required"


def test_store_lock_is_reentrant_for_nested_same_thread_transactions(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)

    with claim_store.store_lock(root, timeout_seconds=0.5):
        with claim_store.store_lock(root, timeout_seconds=0.5):
            assert True

    with claim_store.store_lock(root, timeout_seconds=0.5):
        assert True


def test_store_lock_close_error_after_completed_body_does_not_reverse_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _runtime_root(tmp_path)
    original_validate = claim_store._validate_lock_file_identity
    original_close = claim_store.os.close
    lock_descriptor: int | None = None
    body_completed = False

    def capture_lock_descriptor(path: Path, descriptor: int) -> os.stat_result:
        nonlocal lock_descriptor
        lock_descriptor = descriptor
        return original_validate(path, descriptor)

    def close_then_raise(descriptor: int) -> None:
        original_close(descriptor)
        if descriptor == lock_descriptor:
            raise OSError("lock descriptor close failed after close")

    monkeypatch.setattr(
        claim_store,
        "_validate_lock_file_identity",
        capture_lock_descriptor,
    )
    monkeypatch.setattr(claim_store.os, "close", close_then_raise)

    with claim_store.store_lock(root, timeout_seconds=0.5):
        body_completed = True

    assert body_completed is True
    assert lock_descriptor is not None


def test_store_lock_contention_times_out_boundedly_across_processes(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    ready = tmp_path / "lock-holder-ready"
    release = tmp_path / "lock-holder-release"
    code = """
import sys
import time
from pathlib import Path
from agent_runtime.claim_store import store_lock

root, ready, release = map(Path, sys.argv[1:])
with store_lock(root, timeout_seconds=2.0):
    ready.write_text("ready", encoding="utf-8")
    while not release.exists():
        time.sleep(0.01)
"""
    env = os.environ.copy()
    pythonpath = [str(ROOT / "src"), str(ROOT)]
    if env.get("PYTHONPATH"):
        pythonpath.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    holder = subprocess.Popen(
        [sys.executable, "-c", code, str(root), str(ready), str(release)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 5.0
    while not ready.exists() and holder.poll() is None and time.monotonic() < deadline:
        time.sleep(0.01)
    if not ready.exists():
        stdout, stderr = holder.communicate(timeout=5)
        pytest.fail(f"lock holder did not start: rc={holder.returncode} {stdout=} {stderr=}")

    started = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            with claim_store.store_lock(root, timeout_seconds=0.05):
                pytest.fail("contended lock was acquired")
    finally:
        release.write_text("release", encoding="utf-8")
        try:
            stdout, stderr = holder.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            holder.kill()
            stdout, stderr = holder.communicate(timeout=5)
            pytest.fail(f"lock holder did not exit: {stdout=} {stderr=}")

    assert time.monotonic() - started < 1.0
    assert holder.returncode == 0, (stdout, stderr)


def test_store_lock_revalidates_lock_path_after_kernel_wait(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _runtime_root(tmp_path)
    lock_path = claim_store.outer_marker_path(root).with_name(
        "task-claim-store.lock"
    )
    hidden = tmp_path / "original-task-claim-store.lock"
    calls = 0

    def acquire_after_replacement(_descriptor: int) -> bool:
        nonlocal calls
        calls += 1
        if calls == 1:
            lock_path.rename(hidden)
            lock_path.write_bytes(b"\0")
            return False
        return True

    monkeypatch.setattr(
        claim_store,
        "_try_kernel_lock",
        acquire_after_replacement,
    )

    entered = False
    with pytest.raises(claim_store.ClaimStoreError, match="lock file changed"):
        with claim_store.store_lock(root, timeout_seconds=0.5):
            entered = True

    assert entered is False
    assert calls == 2
    assert hidden.is_file()
    assert lock_path.is_file()


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, (args, result.stdout, result.stderr)
    return result.stdout.strip()


@pytest.mark.skipif(shutil.which("git") is None, reason="Git is required")
def test_outer_anchor_isolated_in_each_checkouts_own_git_admin_directory(
    tmp_path: Path,
) -> None:
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init")
    _git(primary, "config", "user.name", "Claim Store Test")
    _git(primary, "config", "user.email", "claim-store@example.invalid")
    (primary / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(primary, "add", "seed.txt")
    _git(primary, "commit", "-m", "seed")
    linked = tmp_path / "linked"
    _git(primary, "worktree", "add", "-b", "claim-store-linked", str(linked))

    (primary / "agents" / "runtime").mkdir(parents=True)
    (linked / "agents" / "runtime").mkdir(parents=True)
    _write_claim(primary, "CLAIM-primary")
    _write_claim(linked, "CLAIM-linked")
    claim_store.initialize_store(primary, witness_claim_id="CLAIM-primary")
    claim_store.initialize_store(linked, witness_claim_id="CLAIM-linked")

    primary_admin = claim_store.checkout_git_admin_dir(primary)
    linked_admin = claim_store.checkout_git_admin_dir(linked)
    assert primary_admin.resolve() == Path(
        _git(primary, "rev-parse", "--absolute-git-dir")
    ).resolve()
    assert linked_admin.resolve() == Path(
        _git(linked, "rev-parse", "--absolute-git-dir")
    ).resolve()
    assert primary_admin != linked_admin

    primary_outer = claim_store.outer_marker_path(primary)
    linked_outer = claim_store.outer_marker_path(linked)
    assert primary_outer.is_file()
    assert linked_outer.is_file()
    assert primary_outer != linked_outer
    primary_payload, _ = _assert_initialized_pair(
        primary,
        witness_claim_id="CLAIM-primary",
    )
    linked_payload, _ = _assert_initialized_pair(
        linked,
        witness_claim_id="CLAIM-linked",
    )
    assert primary_payload["generation_id"] != linked_payload["generation_id"]


@pytest.mark.skipif(shutil.which("git") is None, reason="Git is required")
def test_fresh_clone_requires_explicit_activation_and_preserves_inner_generation(
    tmp_path: Path,
) -> None:
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init")
    _git(primary, "config", "user.name", "Claim Store Test")
    _git(primary, "config", "user.email", "claim-store@example.invalid")
    (primary / "agents" / "runtime").mkdir(parents=True)
    _write_claim(primary, "CLAIM-retained")
    claim_store.initialize_store(primary, witness_claim_id="CLAIM-retained")
    _, primary_inner = _marker_paths(primary)
    marker_bytes = primary_inner.read_bytes()
    _git(primary, "add", "agents/runtime/task_claims")
    _git(primary, "commit", "-m", "initialize claim store")

    cloned = tmp_path / "cloned"
    cloned_result = subprocess.run(
        ["git", "clone", "-q", str(primary), str(cloned)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert cloned_result.returncode == 0, cloned_result.stdout + cloned_result.stderr
    cloned_outer, cloned_inner = _marker_paths(cloned)
    assert cloned_inner.read_bytes() == marker_bytes
    assert not cloned_outer.exists()

    before_activation = claim_store.inspect_store(cloned)

    assert before_activation.state == "migration-required"
    assert before_activation.witness_claim_id == "CLAIM-retained"
    assert not cloned_outer.exists()

    activated = claim_store.adopt_legacy_store(cloned)

    assert activated.state == "initialized"
    assert activated.generation_id == json.loads(marker_bytes)["generation_id"]
    assert cloned_inner.read_bytes() == marker_bytes
    assert cloned_outer.read_bytes() == marker_bytes
    assert _git(cloned, "status", "--porcelain") == ""


@pytest.mark.skipif(shutil.which("git") is None, reason="Git is required")
def test_new_linked_worktree_requires_explicit_activation_and_preserves_inner_generation(
    tmp_path: Path,
) -> None:
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init")
    _git(primary, "config", "user.name", "Claim Store Test")
    _git(primary, "config", "user.email", "claim-store@example.invalid")
    (primary / "agents" / "runtime").mkdir(parents=True)
    _write_claim(primary, "CLAIM-retained")
    claim_store.initialize_store(primary, witness_claim_id="CLAIM-retained")
    _, primary_inner = _marker_paths(primary)
    marker_bytes = primary_inner.read_bytes()
    _git(primary, "add", "agents/runtime/task_claims")
    _git(primary, "commit", "-m", "initialize claim store")

    linked = tmp_path / "linked"
    _git(primary, "worktree", "add", "-b", "claim-store-linked", str(linked))
    linked_outer, linked_inner = _marker_paths(linked)

    before_activation = claim_store.inspect_store(linked)

    assert linked_inner.read_bytes() == marker_bytes
    assert not linked_outer.exists()
    assert before_activation.state == "migration-required"
    assert before_activation.witness_claim_id == "CLAIM-retained"

    activated = claim_store.adopt_legacy_store(linked)

    assert activated.state == "initialized"
    assert activated.generation_id == json.loads(marker_bytes)["generation_id"]
    assert linked_inner.read_bytes() == marker_bytes
    assert linked_outer.read_bytes() == marker_bytes
    assert _git(linked, "status", "--porcelain") == ""


def _create_windows_junction(link: Path, target: Path) -> None:
    created = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert created.returncode == 0, created.stdout + created.stderr
    metadata = os.lstat(link)
    assert metadata.st_file_attributes & getattr(
        stat,
        "FILE_ATTRIBUTE_REPARSE_POINT",
        0x00000400,
    )


def _remove_windows_junction(link: Path) -> None:
    removed = subprocess.run(
        ["cmd.exe", "/d", "/c", "rmdir", str(link)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert removed.returncode == 0, removed.stdout + removed.stderr


@pytest.mark.skipif(os.name != "nt", reason="native Windows junction required")
def test_snapshot_revalidation_rejects_native_windows_runtime_junction(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    inspected = claim_store.inspect_store(root)
    assert inspected.state == "initialized"
    runtime = root / "agents" / "runtime"
    original = tmp_path / "original-runtime"
    runtime.replace(original)
    try:
        _create_windows_junction(runtime, original)
        assert claim_store.verify_snapshot(root, inspected.snapshot) is False
        _assert_integrity_invalid(claim_store.inspect_store(root))
    finally:
        try:
            os.lstat(runtime)
        except FileNotFoundError:
            pass
        else:
            _remove_windows_junction(runtime)
        if original.exists():
            original.replace(runtime)


@pytest.mark.skipif(os.name != "nt", reason="native Windows junction required")
def test_store_lock_rejects_native_windows_outer_anchor_junction(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    anchor = claim_store.outer_marker_path(root).parent
    original = tmp_path / "original-outer-anchor"
    anchor.replace(original)
    try:
        _create_windows_junction(anchor, original)
        with pytest.raises(claim_store.ClaimStoreError):
            with claim_store.store_lock(root, timeout_seconds=0.5):
                pytest.fail("junction-backed lock anchor was accepted")
    finally:
        try:
            os.lstat(anchor)
        except FileNotFoundError:
            pass
        else:
            _remove_windows_junction(anchor)
        if original.exists():
            original.replace(anchor)
