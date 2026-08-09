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

import errno
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

    read_calls = 0

    def uncertain_read() -> bytes:
        nonlocal read_calls
        read_calls += 1
        if read_calls == 1:
            # The receipt-first executor must establish an exact raw before-CAS
            # immediately before invoking the mutation callback.
            return before
        raise OSError("readback unavailable after subject callback returned")

    outcome = _execute(
        receipt_dir,
        mutate_subject=mutate,
        read_subject=uncertain_read,
    )

    assert outcome["status"] == "indeterminate"
    assert read_calls == 2
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


@pytest.mark.parametrize("finalizer", ("commit", "indeterminate"))
def test_split_phase_lock_acquisition_failure_is_typed_after_subject_commit(
    tmp_path: Path,
    finalizer: str,
) -> None:
    """Public split-phase APIs begin after the subject commit point.

    Losing the prepared lock authority must therefore never leak a plain
    retry-looking filesystem exception to a caller.
    """

    receipt_dir = tmp_path / "recovery_receipts"
    _before, after = _before_after()
    prepared_path = _prepare(receipt_dir)
    prepared_path.unlink()

    with pytest.raises(recovery_receipt.RecoveryReceiptError) as exc_info:
        if finalizer == "commit":
            recovery_receipt.commit_prepared_recovery(
                prepared_path=prepared_path,
                observed_after_bytes=after,
            )
        else:
            recovery_receipt.indeterminate_prepared_recovery(
                prepared_path=prepared_path,
                finding="subject committed but prepared lock authority vanished",
            )

    assert exc_info.value.stage == "terminal-transaction-lock"
    assert exc_info.value.committed is True
    assert exc_info.value.retry_safe is False
    assert exc_info.value.receipt_committed is False


def test_windows_style_locked_descriptor_payload_avoids_second_prepared_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Locked helpers consume the prepared bytes from the locking handle.

    A Windows byte-range lock can reject a second handle in the locking process,
    so this fake lock makes any path-based prepared read fail while held.
    """

    receipt_dir = tmp_path / "recovery_receipts"
    _before, after = _before_after()
    prepared_path = _prepare(receipt_dir)
    original_validate = recovery_receipt.validate_receipt
    lock_held = False

    def fake_msvcrt_lock(descriptor: int) -> Callable[[], None]:
        nonlocal lock_held
        assert descriptor >= 0
        lock_held = True

        def unlock() -> None:
            nonlocal lock_held
            lock_held = False

        return unlock

    def reject_second_prepared_handle(path: Path) -> dict[str, object]:
        if lock_held and Path(path) == prepared_path:
            raise PermissionError(
                "Windows byte-range lock rejected a second prepared handle"
            )
        return original_validate(path)

    monkeypatch.setattr(
        recovery_receipt,
        "_lock_prepared_descriptor",
        fake_msvcrt_lock,
    )
    monkeypatch.setattr(
        recovery_receipt,
        "validate_receipt",
        reject_second_prepared_handle,
    )

    outcome = recovery_receipt.commit_prepared_recovery(
        prepared_path=prepared_path,
        observed_after_bytes=after,
    )

    assert outcome["status"] == "committed"
    assert lock_held is False
    assert (receipt_dir / f"{RECEIPT_ID}.committed.json").is_file()


def test_execute_lock_acquisition_failure_is_typed_before_subject_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, _after = _before_after()
    subject.write_bytes(before)
    mutation_calls = 0

    @recovery_receipt.contextmanager
    def fail_lock(_path: Path):
        raise OSError("process-shared transaction lock unavailable")
        yield  # pragma: no cover - contextmanager shape only

    def mutate() -> None:
        nonlocal mutation_calls
        mutation_calls += 1

    monkeypatch.setattr(recovery_receipt, "_terminal_transaction_lock", fail_lock)

    with pytest.raises(recovery_receipt.RecoveryReceiptError) as exc_info:
        _execute(
            receipt_dir,
            mutate_subject=mutate,
            read_subject=subject.read_bytes,
        )

    assert exc_info.value.stage == "terminal-transaction-lock"
    assert exc_info.value.committed is False
    assert exc_info.value.retry_safe is True
    assert exc_info.value.receipt_committed is True
    assert mutation_calls == 0
    assert subject.read_bytes() == before


def test_execute_holds_transaction_lock_from_raw_cas_through_terminal(
    tmp_path: Path,
) -> None:
    """An external finalizer cannot seize the prepared record mid-execution."""

    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, after = _before_after()
    subject.write_bytes(before)
    prepared_path = receipt_dir / f"{RECEIPT_ID}.prepared.json"
    external_started = threading.Event()
    external_done = threading.Event()
    external: dict[str, object] = {}

    def finalize_externally() -> None:
        external_started.set()
        try:
            external["outcome"] = recovery_receipt.indeterminate_prepared_recovery(
                prepared_path=prepared_path,
                finding="external observer raced the subject mutation",
            )
        except Exception as exc:  # noqa: BLE001 - losing finalizer is expected
            external["error"] = exc
        finally:
            external_done.set()

    with ThreadPoolExecutor(max_workers=1) as executor:
        def mutate() -> None:
            subject.write_bytes(after)
            executor.submit(finalize_externally)
            assert external_started.wait(timeout=1.0)
            # An unlocked executor lets the external finalizer finish here.
            # A correct executor keeps it blocked until its own terminal is
            # durable, so this bounded wait intentionally times out.
            external_done.wait(timeout=0.25)

        outcome = _execute(
            receipt_dir,
            mutate_subject=mutate,
            read_subject=subject.read_bytes,
        )
        assert external_done.wait(timeout=2.0)

    assert outcome["status"] == "committed"
    assert isinstance(external.get("error"), FileExistsError)
    assert "outcome" not in external
    assert (receipt_dir / f"{RECEIPT_ID}.committed.json").is_file()
    assert not (receipt_dir / f"{RECEIPT_ID}.indeterminate.json").exists()
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

    def fail_committed_publication(
        path: Path,
        payload: object,
        **kwargs: object,
    ):
        if str(path).endswith(".committed.json"):
            raise OSError("plain committed receipt publication failure")
        return original_publish(path, payload, **kwargs)

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
    original_validate_at = recovery_receipt._validate_receipt_at

    def fail_terminal_readback(
        directory_fd: int,
        name: str,
        display_path: Path,
    ) -> dict[str, object]:
        if name.endswith(".committed.json"):
            raise OSError("plain receipt readback failure after publication")
        return original_validate_at(directory_fd, name, display_path)

    monkeypatch.setattr(
        recovery_receipt,
        "_validate_receipt_at",
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


def test_validate_receipt_rejects_a_stable_ancestor_alias(tmp_path: Path) -> None:
    real_parent = tmp_path / "real-parent"
    receipt_dir = real_parent / "recovery_receipts"
    prepared_path = _prepare(receipt_dir)
    alias_parent = tmp_path / "alias-parent"
    alias_parent.symlink_to(real_parent, target_is_directory=True)
    alias_path = alias_parent / "recovery_receipts" / prepared_path.name

    with pytest.raises((OSError, ValueError), match="alias|symlink|unsafe"):
        recovery_receipt.validate_receipt(alias_path)


def test_verify_store_rejects_parent_gateway_swap_during_enumeration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A verified lexical gateway cannot be swapped to a hidden valid store."""

    gateway = tmp_path / "gateway"
    visible_store = gateway / "recovery_receipts"
    visible_store.mkdir(parents=True)
    hidden_gateway = tmp_path / "hidden-gateway"
    hidden_store = hidden_gateway / "recovery_receipts"
    hidden_subject = tmp_path / "hidden-claim.json"
    before, after = _before_after()
    hidden_subject.write_bytes(before)

    def mutate_hidden() -> None:
        hidden_subject.write_bytes(after)

    hidden_outcome = _execute(
        hidden_store,
        mutate_subject=mutate_hidden,
        read_subject=hidden_subject.read_bytes,
    )
    assert hidden_outcome["status"] == "committed"
    assert recovery_receipt.verify_receipt_store(hidden_store) == []

    original_listdir = recovery_receipt.os.listdir
    moved_gateway = tmp_path / "original-gateway"
    swapped = False

    def swap_before_enumeration(path: object):
        nonlocal swapped
        if not swapped:
            swapped = True
            gateway.rename(moved_gateway)
            gateway.symlink_to(hidden_gateway, target_is_directory=True)
        return original_listdir(path)

    monkeypatch.setattr(
        recovery_receipt.os,
        "listdir",
        swap_before_enumeration,
    )

    findings = recovery_receipt.verify_receipt_store(visible_store)

    assert swapped is True
    assert findings
    finding_text = " ".join(str(item).lower() for item in findings)
    assert any(token in finding_text for token in ("alias", "identity", "changed"))


def test_execute_gateway_swap_after_subject_commit_is_typed_and_pinned(
    tmp_path: Path,
) -> None:
    gateway = tmp_path / "gateway"
    receipt_dir = gateway / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, after = _before_after()
    subject.write_bytes(before)
    moved_gateway = tmp_path / "original-gateway"

    def mutate_and_swap_gateway() -> None:
        subject.write_bytes(after)
        gateway.rename(moved_gateway)
        receipt_dir.mkdir(parents=True)

    with pytest.raises(recovery_receipt.RecoveryReceiptError) as exc_info:
        _execute(
            receipt_dir,
            mutate_subject=mutate_and_swap_gateway,
            read_subject=subject.read_bytes,
        )

    assert exc_info.value.committed is True
    assert exc_info.value.retry_safe is False
    assert subject.read_bytes() == after
    original_store = moved_gateway / "recovery_receipts"
    assert (original_store / f"{RECEIPT_ID}.prepared.json").is_file()
    assert (original_store / f"{RECEIPT_ID}.committed.json").is_file()
    assert list(receipt_dir.iterdir()) == []


def test_execute_gateway_swap_before_callback_preserves_precommit_truth(
    tmp_path: Path,
) -> None:
    gateway = tmp_path / "gateway"
    receipt_dir = gateway / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, _after = _before_after()
    subject.write_bytes(before)
    moved_gateway = tmp_path / "original-gateway"
    mutation_calls = 0

    def fail_before_cas() -> bytes:
        gateway.rename(moved_gateway)
        receipt_dir.mkdir(parents=True)
        raise OSError("subject before-CAS read unavailable")

    def mutate() -> None:
        nonlocal mutation_calls
        mutation_calls += 1

    with pytest.raises(recovery_receipt.RecoveryReceiptError) as exc_info:
        _execute(
            receipt_dir,
            mutate_subject=mutate,
            read_subject=fail_before_cas,
        )

    assert exc_info.value.committed is False
    assert exc_info.value.retry_safe is True
    assert mutation_calls == 0
    assert subject.read_bytes() == before
    assert (
        moved_gateway
        / "recovery_receipts"
        / f"{RECEIPT_ID}.prepared.json"
    ).is_file()
    assert list(receipt_dir.iterdir()) == []


def test_split_finalize_gateway_swap_is_typed_and_pinned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = tmp_path / "gateway"
    receipt_dir = gateway / "recovery_receipts"
    _before, after = _before_after()
    prepared_path = _prepare(receipt_dir)
    moved_gateway = tmp_path / "original-gateway"
    original_commit = recovery_receipt._commit_prepared_recovery_locked
    swapped = False

    def swap_then_commit(**kwargs: object) -> dict[str, object]:
        nonlocal swapped
        if not swapped:
            swapped = True
            gateway.rename(moved_gateway)
            receipt_dir.mkdir(parents=True)
        return original_commit(**kwargs)

    monkeypatch.setattr(
        recovery_receipt,
        "_commit_prepared_recovery_locked",
        swap_then_commit,
    )

    with pytest.raises(recovery_receipt.RecoveryReceiptError) as exc_info:
        recovery_receipt.commit_prepared_recovery(
            prepared_path=prepared_path,
            observed_after_bytes=after,
        )

    assert swapped is True
    assert exc_info.value.committed is True
    assert exc_info.value.retry_safe is False
    original_store = moved_gateway / "recovery_receipts"
    assert (original_store / f"{RECEIPT_ID}.prepared.json").is_file()
    assert (original_store / f"{RECEIPT_ID}.committed.json").is_file()
    assert list(receipt_dir.iterdir()) == []


def test_split_finalize_terminal_stat_uncertainty_is_typed_post_subject(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    _before, after = _before_after()
    prepared_path = _prepare(receipt_dir)
    original_stat = recovery_receipt.os.stat

    def fail_terminal_stat(path: object, *args: object, **kwargs: object):
        if isinstance(path, str) and path.endswith(".committed.json"):
            raise OSError(errno.EIO, "terminal authority stat unavailable")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(recovery_receipt.os, "stat", fail_terminal_stat)

    with pytest.raises(recovery_receipt.RecoveryReceiptError) as exc_info:
        recovery_receipt.commit_prepared_recovery(
            prepared_path=prepared_path,
            observed_after_bytes=after,
        )

    assert exc_info.value.stage == "terminal-authority-stat"
    assert exc_info.value.committed is True
    assert exc_info.value.retry_safe is False


def test_execute_terminal_stat_uncertainty_before_callback_is_retry_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    subject = tmp_path / "claim.json"
    before, _after = _before_after()
    subject.write_bytes(before)
    original_stat = recovery_receipt.os.stat
    mutation_calls = 0

    def fail_terminal_stat(path: object, *args: object, **kwargs: object):
        if isinstance(path, str) and path.endswith(".committed.json"):
            raise OSError(errno.EIO, "terminal authority stat unavailable")
        return original_stat(path, *args, **kwargs)

    def mutate() -> None:
        nonlocal mutation_calls
        mutation_calls += 1

    monkeypatch.setattr(recovery_receipt.os, "stat", fail_terminal_stat)

    with pytest.raises(recovery_receipt.RecoveryReceiptError) as exc_info:
        _execute(
            receipt_dir,
            mutate_subject=mutate,
            read_subject=subject.read_bytes,
        )

    assert exc_info.value.stage == "terminal-authority-stat"
    assert exc_info.value.committed is False
    assert exc_info.value.retry_safe is True
    assert mutation_calls == 0


def test_terminal_visibility_probe_eio_does_not_mask_publication_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    _before, after = _before_after()
    prepared_path = _prepare(receipt_dir)
    original_stat = recovery_receipt.os.stat
    committed_stats = 0

    def fail_second_committed_stat(
        path: object,
        *args: object,
        **kwargs: object,
    ):
        nonlocal committed_stats
        if isinstance(path, str) and path.endswith(".committed.json"):
            committed_stats += 1
            if committed_stats >= 2:
                raise OSError(errno.EIO, "terminal visibility probe unavailable")
        return original_stat(path, *args, **kwargs)

    def fail_publication(
        path: Path,
        _payload: object,
        **_kwargs: object,
    ) -> dict[str, object]:
        if path.name.endswith(".committed.json"):
            raise OSError(errno.ENOSPC, "committed publication failed")
        raise AssertionError(f"unexpected publication path: {path}")

    monkeypatch.setattr(recovery_receipt.os, "stat", fail_second_committed_stat)
    monkeypatch.setattr(recovery_receipt, "_publish_record", fail_publication)

    with pytest.raises(recovery_receipt.RecoveryReceiptError) as exc_info:
        recovery_receipt.commit_prepared_recovery(
            prepared_path=prepared_path,
            observed_after_bytes=after,
        )

    assert committed_stats >= 2
    assert exc_info.value.committed is True
    assert exc_info.value.retry_safe is False
    assert "publication" in str(exc_info.value).lower()


def test_prepared_descriptor_close_failure_does_not_mask_typed_body_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    _before, after = _before_after()
    prepared_path = _prepare(receipt_dir)
    prepared_inode = prepared_path.stat().st_ino
    original_close = recovery_receipt.os.close
    marker = recovery_receipt.RecoveryReceiptError(
        "typed subject outcome",
        stage="typed-body",
        committed=True,
        retry_safe=False,
    )

    def fail_prepared_close(descriptor: int) -> None:
        metadata = recovery_receipt.os.fstat(descriptor)
        if metadata.st_ino == prepared_inode and recovery_receipt.stat.S_ISREG(
            metadata.st_mode
        ):
            original_close(descriptor)
            raise OSError(errno.EIO, "prepared descriptor close uncertain")
        original_close(descriptor)

    def fail_body(**_kwargs: object) -> dict[str, object]:
        raise marker

    monkeypatch.setattr(recovery_receipt.os, "close", fail_prepared_close)
    monkeypatch.setattr(
        recovery_receipt,
        "_commit_prepared_recovery_locked",
        fail_body,
    )

    with pytest.raises(recovery_receipt.RecoveryReceiptError) as exc_info:
        recovery_receipt.commit_prepared_recovery(
            prepared_path=prepared_path,
            observed_after_bytes=after,
        )

    assert exc_info.value is marker


def test_pinned_publish_refsyncs_parent_after_retry_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    _before, after = _before_after()
    prepared_path = _prepare(receipt_dir)
    original_unlink = recovery_receipt.os.unlink
    original_fsync = recovery_receipt.os.fsync
    cleanup_calls = 0
    parent_fsyncs = 0

    def flaky_sidecar_unlink(
        path: object,
        *args: object,
        **kwargs: object,
    ) -> None:
        nonlocal cleanup_calls
        if isinstance(path, str) and ".tmp-" in path:
            cleanup_calls += 1
            if cleanup_calls == 1:
                raise OSError(errno.EIO, "first sidecar cleanup failed")
        original_unlink(path, *args, **kwargs)

    def count_parent_fsync(descriptor: int) -> None:
        nonlocal parent_fsyncs
        metadata = recovery_receipt.os.fstat(descriptor)
        if recovery_receipt.stat.S_ISDIR(metadata.st_mode):
            parent_fsyncs += 1
        original_fsync(descriptor)

    monkeypatch.setattr(recovery_receipt.os, "unlink", flaky_sidecar_unlink)
    monkeypatch.setattr(recovery_receipt.os, "fsync", count_parent_fsync)

    outcome = recovery_receipt.commit_prepared_recovery(
        prepared_path=prepared_path,
        observed_after_bytes=after,
    )

    assert outcome["status"] == "committed"
    assert cleanup_calls >= 2
    assert parent_fsyncs >= 2
    assert not any(".tmp-" in path.name for path in receipt_dir.iterdir())


def test_verified_parent_closes_fd_when_initial_fstat_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    path = parent / "receipt.json"
    flags = recovery_receipt.os.O_RDONLY | getattr(
        recovery_receipt.os,
        "O_DIRECTORY",
        0,
    )
    descriptor = recovery_receipt.os.open(parent, flags)
    original_fstat = recovery_receipt.os.fstat
    failed = False

    def fixed_parent(_directory: Path) -> tuple[Path, int]:
        return parent, descriptor

    def fail_first_fstat(candidate: int):
        nonlocal failed
        if candidate == descriptor and not failed:
            failed = True
            raise OSError(errno.EIO, "parent identity unavailable")
        return original_fstat(candidate)

    monkeypatch.setattr(recovery_receipt, "_open_posix_directory", fixed_parent)
    monkeypatch.setattr(recovery_receipt.os, "fstat", fail_first_fstat)

    with pytest.raises(OSError, match="parent identity unavailable"):
        with recovery_receipt._verified_parent(path):
            raise AssertionError("verified parent yielded after fstat failure")

    with pytest.raises(OSError) as closed:
        original_fstat(descriptor)
    assert closed.value.errno == errno.EBADF


def test_verify_store_closes_fd_when_initial_fstat_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_dir = tmp_path / "recovery_receipts"
    receipt_dir.mkdir()
    flags = recovery_receipt.os.O_RDONLY | getattr(
        recovery_receipt.os,
        "O_DIRECTORY",
        0,
    )
    descriptor = recovery_receipt.os.open(receipt_dir, flags)
    original_fstat = recovery_receipt.os.fstat
    failed = False

    def fixed_store(_directory: Path) -> tuple[Path, int]:
        return receipt_dir, descriptor

    def fail_first_fstat(candidate: int):
        nonlocal failed
        if candidate == descriptor and not failed:
            failed = True
            raise OSError(errno.EIO, "store identity unavailable")
        return original_fstat(candidate)

    monkeypatch.setattr(recovery_receipt, "_open_posix_directory", fixed_store)
    monkeypatch.setattr(recovery_receipt.os, "fstat", fail_first_fstat)

    findings = recovery_receipt.verify_receipt_store(receipt_dir)

    assert findings
    assert "identity" in " ".join(findings).lower()
    with pytest.raises(OSError) as closed:
        original_fstat(descriptor)
    assert closed.value.errno == errno.EBADF
