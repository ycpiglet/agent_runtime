"""RED contract for immutable, receipt-first claim recovery transactions.

The recovery journal is a write-ahead log, not a mutable status document:

* ``<id>.prepared.json`` is published without replacement before the subject
  callback may run;
* a successful or uncertain outcome is a second immutable
  ``<id>.committed.json`` or ``<id>.indeterminate.json`` witness;
* the prepared record is never rewritten to advance state; and
* a post-commit observation gap is explicitly non-retry-safe.

These tests intentionally precede ``scripts/recovery_receipt.py``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import recovery_receipt  # noqa: E402
import atomic_io  # noqa: E402


RECEIPT_ID = "RECOVERY-20260809-130000-claim-ar-660-test"
RECORDED_AT = "2026-08-09T13:00:00+09:00"
SUBJECT_REF = "agents/runtime/task_claims/CLAIM-test.json"
OWNER_ID = "owner-recovery-test"
REASON = "recover one explicitly approved claim"
COMMIT_WITNESS = {
    "claim_id": "CLAIM-test",
    "expected_mutation_revision": 6,
    "next_mutation_revision": 7,
}


def _json_bytes(payload: object, *, indent: int | None = 2) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=indent,
            sort_keys=False,
            separators=(",", ":") if indent is None else None,
        )
        + "\n"
    ).encode("utf-8")


def _before_after() -> tuple[bytes, bytes]:
    before = _json_bytes(
        {
            "schema": "agent-runtime-task-claim/v1",
            "claim_id": "CLAIM-test",
            "status": "claimed",
            "mutation_revision": 6,
            "note": "café",
        }
    )
    after = _json_bytes(
        {
            "schema": "agent-runtime-task-claim/v1",
            "claim_id": "CLAIM-test",
            "status": "expired",
            "mutation_revision": 7,
            "note": "café",
        },
        indent=None,
    )
    return before, after


def _prepare(receipt_dir: Path) -> Path:
    before, after = _before_after()
    return recovery_receipt.prepare_recovery_receipt(
        receipt_dir=receipt_dir,
        receipt_id=RECEIPT_ID,
        operation="terminalize",
        subject_ref=SUBJECT_REF,
        before_bytes=before,
        predicted_after_bytes=after,
        owner_id=OWNER_ID,
        reason=REASON,
        recorded_at=RECORDED_AT,
        commit_witness=COMMIT_WITNESS,
    )


def _execute(
    receipt_dir: Path,
    *,
    mutate_subject: Callable[[], None],
    read_subject: Callable[[], bytes],
    transition_required: bool = True,
) -> dict[str, object]:
    before, after = _before_after()
    return recovery_receipt.execute_recovery(
        receipt_dir=receipt_dir,
        receipt_id=RECEIPT_ID,
        operation="terminalize",
        subject_ref=SUBJECT_REF,
        before_bytes=before,
        predicted_after_bytes=after,
        owner_id=OWNER_ID,
        reason=REASON,
        recorded_at=RECORDED_AT,
        commit_witness=COMMIT_WITNESS,
        mutate_subject=mutate_subject,
        read_subject=read_subject,
        transition_required=transition_required,
    )


def _load(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _assert_self_digest(payload: dict[str, object]) -> None:
    core = {key: value for key, value in payload.items() if key != "receipt_digest"}
    expected = hashlib.sha256(
        recovery_receipt.canonical_json_bytes(core)
    ).hexdigest()
    assert payload["receipt_digest"] == expected


def test_canonical_digest_keeps_semantic_and_exact_byte_identity_separate() -> None:
    left = b'{\n  "z": 1, "a": "caf\xc3\xa9"\n}\n'
    right = b'{"a":"caf\\u00e9","z":1}'

    assert recovery_receipt.raw_digest(left) == hashlib.sha256(left).hexdigest()
    assert recovery_receipt.raw_digest(right) == hashlib.sha256(right).hexdigest()
    assert recovery_receipt.raw_digest(left) != recovery_receipt.raw_digest(right)
    assert recovery_receipt.semantic_digest(left) == recovery_receipt.semantic_digest(
        right
    )
    assert recovery_receipt.canonical_json_bytes(json.loads(left)) == (
        b'{"a":"caf\xc3\xa9","z":1}'
    )


def test_prepare_publishes_immutable_receipt_with_exact_transition_digests(
    tmp_path: Path,
) -> None:
    receipt_dir = tmp_path / "agents" / "runtime" / "recovery_receipts"
    before, after = _before_after()

    prepared_path = _prepare(receipt_dir)

    assert prepared_path == receipt_dir / f"{RECEIPT_ID}.prepared.json"
    prepared_bytes = prepared_path.read_bytes()
    prepared = _load(prepared_path)
    assert prepared["schema"] == "agent-runtime-recovery-receipt/v1"
    assert prepared["receipt_id"] == RECEIPT_ID
    assert prepared["state"] == "prepared"
    assert prepared["operation"] == "terminalize"
    assert prepared["subject_ref"] == SUBJECT_REF
    assert prepared["owner_id"] == OWNER_ID
    assert prepared["reason"] == REASON
    assert prepared["commit_witness"] == COMMIT_WITNESS
    assert prepared["before"] == {
        "raw_sha256": hashlib.sha256(before).hexdigest(),
        "semantic_sha256": recovery_receipt.semantic_digest(before),
        "byte_length": len(before),
    }
    assert prepared["after"] == {
        "raw_sha256": hashlib.sha256(after).hexdigest(),
        "semantic_sha256": recovery_receipt.semantic_digest(after),
        "byte_length": len(after),
    }
    _assert_self_digest(prepared)
    assert recovery_receipt.validate_receipt(prepared_path) == prepared

    # No code path may turn the WAL into a last-writer-wins status document.
    with pytest.raises(OSError):
        _prepare(receipt_dir)
    assert prepared_path.read_bytes() == prepared_bytes


def test_validate_rejects_missing_and_self_digest_tampered_receipts(
    tmp_path: Path,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    missing = receipt_dir / f"{RECEIPT_ID}.prepared.json"

    with pytest.raises((FileNotFoundError, ValueError)):
        recovery_receipt.validate_receipt(missing)

    prepared_path = _prepare(receipt_dir)
    tampered = _load(prepared_path)
    tampered["owner_id"] = "different-owner"
    prepared_path.write_text(
        json.dumps(tampered, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="digest|tamper|integrity"):
        recovery_receipt.validate_receipt(prepared_path)


def test_execute_orders_prepared_subject_and_committed_witness(
    tmp_path: Path,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, after = _before_after()
    subject.write_bytes(before)
    prepared_path = receipt_dir / f"{RECEIPT_ID}.prepared.json"
    committed_path = receipt_dir / f"{RECEIPT_ID}.committed.json"
    observed: dict[str, bytes] = {}
    mutation_calls = 0

    def mutate() -> None:
        nonlocal mutation_calls
        mutation_calls += 1
        assert prepared_path.is_file()
        assert not committed_path.exists()
        observed["prepared_before_subject"] = prepared_path.read_bytes()
        subject.write_bytes(after)

    outcome = _execute(
        receipt_dir,
        mutate_subject=mutate,
        read_subject=subject.read_bytes,
    )

    assert outcome["status"] == "committed"
    assert mutation_calls == 1
    assert subject.read_bytes() == after
    assert prepared_path.read_bytes() == observed["prepared_before_subject"]
    assert committed_path.is_file()
    assert not (receipt_dir / f"{RECEIPT_ID}.indeterminate.json").exists()

    prepared = _load(prepared_path)
    committed = _load(committed_path)
    assert committed["state"] == "committed"
    assert committed["prepared_receipt_digest"] == prepared["receipt_digest"]
    assert committed["observed_after_raw_sha256"] == hashlib.sha256(after).hexdigest()
    assert committed["commit_witness"] == COMMIT_WITNESS
    _assert_self_digest(committed)
    assert recovery_receipt.verify_receipt_store(receipt_dir) == []

    # Replaying an id cannot overwrite either immutable record or call the
    # subject a second time.
    prepared_bytes = prepared_path.read_bytes()
    committed_bytes = committed_path.read_bytes()
    with pytest.raises(OSError):
        _execute(
            receipt_dir,
            mutate_subject=mutate,
            read_subject=subject.read_bytes,
        )
    assert mutation_calls == 1
    assert prepared_path.read_bytes() == prepared_bytes
    assert committed_path.read_bytes() == committed_bytes


def test_missing_prepared_record_invalidates_a_terminal_witness(tmp_path: Path) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, after = _before_after()
    subject.write_bytes(before)

    def mutate() -> None:
        subject.write_bytes(after)

    outcome = _execute(
        receipt_dir,
        mutate_subject=mutate,
        read_subject=subject.read_bytes,
    )
    assert outcome["status"] == "committed"
    assert recovery_receipt.verify_receipt_store(receipt_dir) == []

    (receipt_dir / f"{RECEIPT_ID}.prepared.json").unlink()
    findings = recovery_receipt.verify_receipt_store(receipt_dir)
    assert findings
    assert "missing" in " ".join(str(item).lower() for item in findings)


def test_prepared_publication_failure_occurs_before_subject_mutation(
    tmp_path: Path,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    receipt_dir.mkdir(parents=True)
    subject = tmp_path / "claim.json"
    before, _after = _before_after()
    subject.write_bytes(before)
    prepared_path = receipt_dir / f"{RECEIPT_ID}.prepared.json"
    sentinel = b"existing immutable owner\n"
    prepared_path.write_bytes(sentinel)
    mutation_calls = 0

    def mutate() -> None:
        nonlocal mutation_calls
        mutation_calls += 1
        raise AssertionError("subject callback ran before receipt publication")

    with pytest.raises(OSError):
        _execute(
            receipt_dir,
            mutate_subject=mutate,
            read_subject=subject.read_bytes,
        )

    assert mutation_calls == 0
    assert subject.read_bytes() == before
    assert prepared_path.read_bytes() == sentinel
    assert list(receipt_dir.glob(f"{RECEIPT_ID}.committed.json")) == []
    assert list(receipt_dir.glob(f"{RECEIPT_ID}.indeterminate.json")) == []


def test_subject_failure_leaves_prepared_receipt_only(tmp_path: Path) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, _after = _before_after()
    subject.write_bytes(before)

    def fail_subject() -> None:
        assert (receipt_dir / f"{RECEIPT_ID}.prepared.json").is_file()
        raise OSError("subject publication failed before commit")

    with pytest.raises(OSError, match="subject publication failed"):
        _execute(
            receipt_dir,
            mutate_subject=fail_subject,
            read_subject=subject.read_bytes,
        )

    assert subject.read_bytes() == before
    assert (receipt_dir / f"{RECEIPT_ID}.prepared.json").is_file()
    assert not (receipt_dir / f"{RECEIPT_ID}.committed.json").exists()
    assert not (receipt_dir / f"{RECEIPT_ID}.indeterminate.json").exists()
    assert _load(receipt_dir / f"{RECEIPT_ID}.prepared.json")["state"] == "prepared"
    findings = recovery_receipt.verify_receipt_store(receipt_dir)
    assert findings, "a legitimate pre-commit failure still needs operator resolution"
    finding_text = " ".join(str(finding).lower() for finding in findings)
    assert "prepared" in finding_text
    assert any(
        token in finding_text
        for token in ("unresolved", "incomplete", "missing terminal", "no terminal")
    )


def test_post_commit_read_uncertainty_is_indeterminate_and_not_retry_safe(
    tmp_path: Path,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, after = _before_after()
    subject.write_bytes(before)
    prepared_path = receipt_dir / f"{RECEIPT_ID}.prepared.json"

    def mutate() -> None:
        subject.write_bytes(after)

    def uncertain_read() -> bytes:
        raise OSError("readback unavailable after subject callback returned")

    outcome = _execute(
        receipt_dir,
        mutate_subject=mutate,
        read_subject=uncertain_read,
    )

    assert outcome["status"] == "indeterminate"
    assert outcome["retry_safe"] is False
    assert subject.read_bytes() == after
    assert not (receipt_dir / f"{RECEIPT_ID}.committed.json").exists()
    indeterminate_path = receipt_dir / f"{RECEIPT_ID}.indeterminate.json"
    assert indeterminate_path.is_file()

    prepared = _load(prepared_path)
    indeterminate = _load(indeterminate_path)
    assert indeterminate["state"] == "indeterminate"
    assert indeterminate["retry_safe"] is False
    assert indeterminate["prepared_receipt_digest"] == prepared["receipt_digest"]
    assert "readback" in str(indeterminate["finding"]).lower()
    _assert_self_digest(indeterminate)
    assert recovery_receipt.verify_receipt_store(receipt_dir) == []


def test_existing_store_activation_emits_no_false_recovery_receipt(
    tmp_path: Path,
) -> None:
    """An already initialized activation is a no-op, not a recovery event."""
    receipt_dir = tmp_path / "agents" / "runtime" / "recovery_receipts"
    mutation_calls = 0

    def must_not_mutate() -> None:
        nonlocal mutation_calls
        mutation_calls += 1
        raise AssertionError("already initialized store was mutated")

    outcome = _execute(
        receipt_dir,
        mutate_subject=must_not_mutate,
        read_subject=lambda: b"",
        transition_required=False,
    )

    assert outcome["status"] == "not_required"
    assert outcome["retry_safe"] is True
    assert mutation_calls == 0
    assert not receipt_dir.exists() or list(receipt_dir.iterdir()) == []


def test_split_phase_commit_matches_prepared_after_and_refuses_replay(
    tmp_path: Path,
) -> None:
    """Claim-store activation can prepare under lock and finalize afterward."""
    receipt_dir = tmp_path / "recovery_receipts"
    _before, after = _before_after()
    prepared_path = _prepare(receipt_dir)

    outcome = recovery_receipt.commit_prepared_recovery(
        prepared_path=prepared_path,
        observed_after_bytes=after,
    )

    assert outcome["status"] == "committed"
    assert outcome["retry_safe"] is False
    committed_path = receipt_dir / f"{RECEIPT_ID}.committed.json"
    assert committed_path.is_file()
    assert recovery_receipt.verify_receipt_store(receipt_dir) == []
    with pytest.raises((FileExistsError, ValueError)):
        recovery_receipt.commit_prepared_recovery(
            prepared_path=prepared_path,
            observed_after_bytes=after,
        )
    assert not (receipt_dir / f"{RECEIPT_ID}.indeterminate.json").exists()


def test_split_phase_mismatch_is_indeterminate_not_a_false_commit(
    tmp_path: Path,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    prepared_path = _prepare(receipt_dir)
    unexpected = _json_bytes({"claim_id": "CLAIM-test", "status": "other"})

    outcome = recovery_receipt.commit_prepared_recovery(
        prepared_path=prepared_path,
        observed_after_bytes=unexpected,
    )

    assert outcome["status"] == "indeterminate"
    assert outcome["retry_safe"] is False
    assert not (receipt_dir / f"{RECEIPT_ID}.committed.json").exists()
    indeterminate_path = receipt_dir / f"{RECEIPT_ID}.indeterminate.json"
    assert indeterminate_path.is_file()
    assert recovery_receipt.verify_receipt_store(receipt_dir) == []


def test_committed_subject_atomic_error_gets_indeterminate_witness(
    tmp_path: Path,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, after = _before_after()
    subject.write_bytes(before)

    def mutate_then_report_uncertainty() -> None:
        subject.write_bytes(after)
        raise atomic_io.AtomicWriteError(
            "parent fsync failed after rename",
            stage="parent-fsync",
            committed=True,
            retry_safe=False,
        )

    outcome = _execute(
        receipt_dir,
        mutate_subject=mutate_then_report_uncertainty,
        read_subject=subject.read_bytes,
    )

    assert outcome["status"] == "indeterminate"
    assert outcome["retry_safe"] is False
    assert subject.read_bytes() == after
    assert (receipt_dir / f"{RECEIPT_ID}.prepared.json").is_file()
    assert (receipt_dir / f"{RECEIPT_ID}.indeterminate.json").is_file()
    assert not (receipt_dir / f"{RECEIPT_ID}.committed.json").exists()
    assert recovery_receipt.verify_receipt_store(receipt_dir) == []


def test_concurrent_split_phase_finalizers_publish_exactly_one_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Committed and indeterminate outcomes share one transaction namespace.

    Checking both terminal names and then publishing one of them is a TOCTOU:
    the paths differ, so per-file exclusive creation cannot arbitrate the
    transaction.  The bounded barrier widens that exact window without making
    the test incompatible with an implementation that serializes the whole
    finalize operation (the first waiter simply times out while holding the
    transaction lock).
    """

    receipt_dir = tmp_path / "recovery_receipts"
    _before, after = _before_after()
    prepared_path = _prepare(receipt_dir)
    original_prepare_finalize = recovery_receipt._prepared_for_finalize
    ready = threading.Barrier(2)

    def synchronized_prepare_finalize(path: Path):
        result = original_prepare_finalize(path)
        try:
            ready.wait(timeout=1.0)
        except threading.BrokenBarrierError:
            pass
        return result

    monkeypatch.setattr(
        recovery_receipt,
        "_prepared_for_finalize",
        synchronized_prepare_finalize,
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures: tuple[Future[dict[str, object]], ...] = (
            executor.submit(
                recovery_receipt.commit_prepared_recovery,
                prepared_path=prepared_path,
                observed_after_bytes=after,
            ),
            executor.submit(
                recovery_receipt.indeterminate_prepared_recovery,
                prepared_path=prepared_path,
                finding="concurrent observer cannot confirm the subject",
            ),
        )
        successes: list[dict[str, object]] = []
        failures: list[Exception] = []
        for future in futures:
            try:
                successes.append(future.result(timeout=5))
            except Exception as exc:  # noqa: BLE001 - the losing API may vary
                failures.append(exc)

    terminals = sorted(
        [
            *receipt_dir.glob(f"{RECEIPT_ID}.committed.json"),
            *receipt_dir.glob(f"{RECEIPT_ID}.indeterminate.json"),
        ]
    )
    assert len(successes) == 1, (
        "exactly one concurrent finalizer may report success; "
        f"successes={successes!r} failures={failures!r}"
    )
    assert len(failures) == 1
    assert len(terminals) == 1, [path.name for path in terminals]
    assert successes[0]["status"] in terminals[0].name
    assert recovery_receipt.verify_receipt_store(receipt_dir) == []


def test_terminal_publication_plain_oserror_is_non_retry_safe_after_subject_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A plain sidecar error must not disguise an already-committed subject."""

    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    _before, after = _before_after()
    subject.write_bytes(after)  # split-phase caller already crossed commit
    prepared_path = _prepare(receipt_dir)
    original_publish = recovery_receipt._publish_record

    def fail_committed_publication(path: Path, payload: object):
        if str(path).endswith(".committed.json"):
            raise OSError("plain committed receipt publication failure")
        return original_publish(path, payload)

    monkeypatch.setattr(recovery_receipt, "_publish_record", fail_committed_publication)
    outcome: dict[str, object] | None = None
    caught: Exception | None = None
    try:
        outcome = recovery_receipt.commit_prepared_recovery(
            prepared_path=prepared_path,
            observed_after_bytes=after,
        )
    except Exception as exc:  # noqa: BLE001 - assert the public error below
        caught = exc

    assert subject.read_bytes() == after
    if caught is not None:
        assert isinstance(caught, recovery_receipt.RecoveryReceiptError)
        assert caught.committed is True
        assert caught.retry_safe is False
    else:
        assert outcome is not None
        assert outcome["status"] == "indeterminate"
        assert outcome["retry_safe"] is False
        assert (receipt_dir / f"{RECEIPT_ID}.indeterminate.json").is_file()
    assert not (receipt_dir / f"{RECEIPT_ID}.committed.json").exists()


def test_terminal_readback_plain_oserror_is_typed_after_visible_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Readback uncertainty after terminal publication is also a commit point."""

    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    _before, after = _before_after()
    subject.write_bytes(after)
    prepared_path = _prepare(receipt_dir)
    original_validate = recovery_receipt.validate_receipt

    def fail_terminal_readback(path: Path) -> dict[str, object]:
        if str(path).endswith(".committed.json"):
            raise OSError("plain receipt readback failure after publication")
        return original_validate(path)

    monkeypatch.setattr(
        recovery_receipt,
        "validate_receipt",
        fail_terminal_readback,
    )

    with pytest.raises(recovery_receipt.RecoveryReceiptError) as exc_info:
        recovery_receipt.commit_prepared_recovery(
            prepared_path=prepared_path,
            observed_after_bytes=after,
        )

    assert exc_info.value.committed is True
    assert exc_info.value.retry_safe is False
    assert subject.read_bytes() == after
    assert (receipt_dir / f"{RECEIPT_ID}.committed.json").is_file()
    assert not (receipt_dir / f"{RECEIPT_ID}.indeterminate.json").exists()


def test_execute_recovery_raw_cas_blocks_subject_drift_before_callback(
    tmp_path: Path,
) -> None:
    """Prepared.before is an exact-byte CAS input, not descriptive metadata."""

    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, after = _before_after()
    drifted = recovery_receipt.canonical_json_bytes(json.loads(before))
    assert drifted != before
    assert recovery_receipt.semantic_digest(drifted) == (
        recovery_receipt.semantic_digest(before)
    )
    subject.write_bytes(drifted)
    mutation_calls = 0
    outcome: dict[str, object] | None = None
    caught: Exception | None = None

    def mutate() -> None:
        nonlocal mutation_calls
        mutation_calls += 1
        subject.write_bytes(after)

    try:
        outcome = _execute(
            receipt_dir,
            mutate_subject=mutate,
            read_subject=subject.read_bytes,
        )
    except Exception as exc:  # noqa: BLE001 - prepared-only may raise
        caught = exc

    assert mutation_calls == 0, "subject callback ran despite before-image drift"
    assert subject.read_bytes() == drifted
    assert (receipt_dir / f"{RECEIPT_ID}.prepared.json").is_file()
    assert not (receipt_dir / f"{RECEIPT_ID}.committed.json").exists()
    if outcome is not None:
        assert outcome["status"] != "committed"
        assert outcome.get("finding") or outcome["status"] in {
            "conflict",
            "not_applied",
        }
    else:
        assert caught is not None


def test_verify_receipt_store_blocks_a_symlinked_directory(tmp_path: Path) -> None:
    real_store = tmp_path / "real-recovery-receipts"
    real_store.mkdir()
    linked_store = tmp_path / "linked-recovery-receipts"
    linked_store.symlink_to(real_store, target_is_directory=True)

    findings = recovery_receipt.verify_receipt_store(linked_store)

    assert findings
    assert any(
        token in " ".join(str(item).lower() for item in findings)
        for token in ("symlink", "reparse", "alias")
    )
