"""Failure-first contract tests for durable task-claim store authority.

These tests intentionally describe the TASK-AR-654 continuity contract before
``agent_runtime.claim_store`` exists.  A claim store is either genuinely
pristine, explicitly migration-required, initialized by a matching immutable
marker pair, or integrity-invalid.  In particular, a newly-created empty
directory must not erase the remembered authority of a previously initialized
store.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

from agent_runtime import claim_store


ROOT = Path(__file__).resolve().parents[1]
INNER_MARKER_NAME = ".claim-store"
OUTER_MARKER_PARTS = ("agent-runtime", "task-claim-store")


def _runtime_root(tmp_path: Path, name: str = "host") -> Path:
    root = tmp_path / name
    (root / "agents" / "runtime").mkdir(parents=True)
    return root


def _store(root: Path) -> Path:
    return root / "agents" / "runtime" / "task_claims"


def _marker_paths(root: Path) -> tuple[Path, Path]:
    outer = claim_store.checkout_git_admin_dir(root).joinpath(*OUTER_MARKER_PARTS)
    inner = _store(root) / INNER_MARKER_NAME
    return outer, inner


def _write_claim(root: Path, claim_id: str, *, status: str = "claimed") -> Path:
    store = _store(root)
    store.mkdir(parents=True, exist_ok=True)
    path = store / f"{claim_id}.json"
    path.write_text(
        json.dumps(
            {
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
    assert isinstance(payload["schema"], str)
    assert payload["schema"].endswith("/v1")
    generation = uuid.UUID(str(payload["generation_id"]))
    assert generation.version == 4
    assert str(generation) == payload["generation_id"]
    assert payload["witness_claim_id"] == witness_claim_id
    return payload, outer_bytes


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


@pytest.mark.parametrize("missing_side", ("outer", "inner"))
def test_one_sided_marker_pair_is_integrity_invalid(
    tmp_path: Path,
    missing_side: str,
) -> None:
    root = _runtime_root(tmp_path)
    _write_claim(root, "CLAIM-retained")
    claim_store.initialize_store(root, witness_claim_id="CLAIM-retained")
    outer, inner = _marker_paths(root)
    {"outer": outer, "inner": inner}[missing_side].unlink()

    result = claim_store.inspect_store(root)

    finding = _assert_integrity_invalid(result)
    assert "marker" in finding or "witness" in finding


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


def test_store_lock_is_reentrant_for_nested_same_thread_transactions(
    tmp_path: Path,
) -> None:
    root = _runtime_root(tmp_path)

    with claim_store.store_lock(root, timeout_seconds=0.5):
        with claim_store.store_lock(root, timeout_seconds=0.5):
            assert True

    with claim_store.store_lock(root, timeout_seconds=0.5):
        assert True


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

    primary_outer = primary_admin.joinpath(*OUTER_MARKER_PARTS)
    linked_outer = linked_admin.joinpath(*OUTER_MARKER_PARTS)
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
