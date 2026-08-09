"""Immutable, receipt-first write-ahead log for Owner recovery mutations.

Recovery receipts are machine authority.  A transaction first publishes an
immutable ``*.prepared.json`` record containing the exact before and predicted
after identities.  Only then may the subject callback run.  A second immutable
``*.committed.json`` or ``*.indeterminate.json`` record witnesses the outcome;
the prepared record is never rewritten into a mutable status document.

The helper deliberately distinguishes three identities:

* ``raw_sha256`` binds the exact bytes that a compare-and-swap transition saw;
* ``semantic_sha256`` binds the canonical JSON value independent of layout;
* ``receipt_digest`` binds the canonical receipt record excluding that field.

All receipt publications use :mod:`atomic_io`'s strict, exclusive publisher.
In particular, a subject-side ``AtomicWriteError`` whose commit point already
passed is recorded as indeterminate and non-retry-safe instead of being
misreported as an ordinary pre-commit failure.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import hmac
import json
import os
import re
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping

from atomic_io import AtomicWriteError, publish_json_atomic


SCHEMA = "agent-runtime-recovery-receipt/v1"
DEFAULT_RECEIPT_DIR = Path("agents/runtime/recovery_receipts")
VALID_STATES = frozenset({"prepared", "committed", "indeterminate"})
VALID_OPERATIONS = frozenset({"adopt", "terminalize", "activate-store", "rotate"})
_RECEIPT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,191}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class RecoveryReceiptError(RuntimeError):
    """A recovery outcome exists but could not be durably witnessed.

    ``committed`` describes the subject transaction, not a failed receipt
    sidecar.  Once this error is raised with ``committed=True``, retrying the
    subject callback is unsafe even if the underlying receipt publication
    error happened before its own commit point.
    """

    def __init__(
        self,
        message: str,
        *,
        stage: str,
        committed: bool,
        retry_safe: bool,
        receipt_committed: bool | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.committed = committed
        self.retry_safe = retry_safe
        self.receipt_committed = receipt_committed


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member is not allowed: {key!r}")
        result[key] = value
    return result


def _load_json_bytes(data: bytes) -> Any:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("receipt subject must be UTF-8 JSON") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc


def canonical_json_bytes(payload: Any) -> bytes:
    """Return the one UTF-8 canonical encoding used by every receipt digest."""

    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"value is not canonical JSON: {exc}") from exc


def raw_digest(data: bytes) -> str:
    """Hash exact bytes without parsing or normalizing them."""

    if not isinstance(data, bytes):
        raise TypeError("raw_digest requires bytes")
    return hashlib.sha256(data).hexdigest()


def semantic_digest(data: bytes) -> str:
    """Hash the canonical JSON value represented by ``data``."""

    return raw_digest(canonical_json_bytes(_load_json_bytes(data)))


def _digest_envelope(data: bytes) -> dict[str, Any]:
    if not isinstance(data, bytes):
        raise TypeError("recovery transition images must be bytes")
    return {
        "raw_sha256": raw_digest(data),
        "semantic_sha256": semantic_digest(data),
        "byte_length": len(data),
    }


def _json_copy(payload: Any) -> Any:
    """Detach caller-owned containers while proving JSON serializability."""

    return _load_json_bytes(canonical_json_bytes(payload))


def _receipt_digest(payload: Mapping[str, Any]) -> str:
    core = {key: value for key, value in payload.items() if key != "receipt_digest"}
    return raw_digest(canonical_json_bytes(core))


def _with_self_digest(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result["receipt_digest"] = _receipt_digest(result)
    return result


def _require_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    if "\x00" in value:
        raise ValueError(f"{key} must not contain NUL")
    return value


def _validate_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("recorded_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("recorded_at must include a timezone")


def _validate_sha(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")


def _validate_digest_envelope(value: Any, field: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    expected = {"raw_sha256", "semantic_sha256", "byte_length"}
    if set(value) != expected:
        raise ValueError(f"{field} must contain exactly {sorted(expected)}")
    _validate_sha(value["raw_sha256"], f"{field}.raw_sha256")
    _validate_sha(value["semantic_sha256"], f"{field}.semantic_sha256")
    length = value["byte_length"]
    if isinstance(length, bool) or not isinstance(length, int) or length < 0:
        raise ValueError(f"{field}.byte_length must be a non-negative integer")


_COMMON_KEYS = {
    "schema",
    "receipt_id",
    "state",
    "operation",
    "subject_ref",
    "owner_id",
    "reason",
    "recorded_at",
    "commit_witness",
    "receipt_digest",
}
_PREPARED_KEYS = _COMMON_KEYS | {"before", "after"}
_COMMITTED_KEYS = _COMMON_KEYS | {
    "prepared_receipt_digest",
    "observed_after_raw_sha256",
    "observed_after_semantic_sha256",
    "observed_after_byte_length",
    "retry_safe",
}
_INDETERMINATE_KEYS = _COMMON_KEYS | {
    "prepared_receipt_digest",
    "finding",
    "retry_safe",
    "uncertainty",
    "observed_after_raw_sha256",
    "observed_after_semantic_sha256",
    "observed_after_byte_length",
}


def _validate_record(payload: Any, *, path: Path | None = None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("recovery receipt must be a JSON object")
    if payload.get("schema") != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA}")

    receipt_id = _require_text(payload, "receipt_id")
    if not _RECEIPT_ID.fullmatch(receipt_id):
        raise ValueError("receipt_id contains unsafe path characters")
    state = payload.get("state")
    if state not in VALID_STATES:
        raise ValueError(f"state must be one of {sorted(VALID_STATES)}")
    operation = payload.get("operation")
    if operation not in VALID_OPERATIONS:
        raise ValueError(f"operation must be one of {sorted(VALID_OPERATIONS)}")
    _require_text(payload, "subject_ref")
    _require_text(payload, "owner_id")
    _require_text(payload, "reason")
    recorded_at = _require_text(payload, "recorded_at")
    _validate_timestamp(recorded_at)

    witness = payload.get("commit_witness")
    if not isinstance(witness, dict) or not witness:
        raise ValueError("commit_witness must be a non-empty JSON object")
    _json_copy(witness)

    expected_keys = {
        "prepared": _PREPARED_KEYS,
        "committed": _COMMITTED_KEYS,
        "indeterminate": _INDETERMINATE_KEYS,
    }[state]
    actual_keys = set(payload)
    if state == "indeterminate":
        observed = {
            "observed_after_raw_sha256",
            "observed_after_semantic_sha256",
            "observed_after_byte_length",
        }
        present = actual_keys & observed
        if present and present != observed:
            raise ValueError("indeterminate observed-after identity must be complete")
        allowed = expected_keys
        required = expected_keys - observed - {"uncertainty"}
        if not required <= actual_keys or not actual_keys <= allowed:
            raise ValueError(
                "indeterminate receipt has missing or additional fields: "
                f"required={sorted(required)} actual={sorted(actual_keys)}"
            )
    elif actual_keys != expected_keys:
        raise ValueError(
            f"{state} receipt must contain exactly {sorted(expected_keys)}; "
            f"got {sorted(actual_keys)}"
        )

    if state == "prepared":
        _validate_digest_envelope(payload.get("before"), "before")
        _validate_digest_envelope(payload.get("after"), "after")
    else:
        _validate_sha(payload.get("prepared_receipt_digest"), "prepared_receipt_digest")
        # Every terminal witness says that the subject callback either crossed
        # its commit point or returned success.  Replaying that callback is
        # therefore never a safe way to resolve the record.
        expected_retry = False
        if payload.get("retry_safe") is not expected_retry:
            raise ValueError(f"{state}.retry_safe must be {expected_retry}")
        if state == "indeterminate":
            _require_text(payload, "finding")
            uncertainty = payload.get("uncertainty")
            if uncertainty is not None:
                if not isinstance(uncertainty, dict):
                    raise ValueError("uncertainty must be a JSON object")
                _json_copy(uncertainty)
        if "observed_after_raw_sha256" in payload:
            _validate_sha(
                payload["observed_after_raw_sha256"],
                "observed_after_raw_sha256",
            )
            _validate_sha(
                payload["observed_after_semantic_sha256"],
                "observed_after_semantic_sha256",
            )
            length = payload["observed_after_byte_length"]
            if isinstance(length, bool) or not isinstance(length, int) or length < 0:
                raise ValueError(
                    "observed_after_byte_length must be a non-negative integer"
                )

    digest = payload.get("receipt_digest")
    _validate_sha(digest, "receipt_digest")
    expected_digest = _receipt_digest(payload)
    if not hmac.compare_digest(digest, expected_digest):
        raise ValueError("receipt digest integrity failure (tampered record)")

    if path is not None:
        expected_name = f"{receipt_id}.{state}.json"
        if path.name != expected_name:
            raise ValueError(
                f"receipt filename must bind id/state as {expected_name!r}"
            )
    return payload


def validate_receipt(path: Path) -> dict[str, Any]:
    """Load and validate one receipt, including its filename and self digest."""

    path = Path(path)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or bool(
        getattr(before, "st_file_attributes", 0) & 0x0400
    ):
        raise ValueError("recovery receipt must not be a symlink or reparse point")
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("recovery receipt must be a regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("opened recovery receipt is not a regular file")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError("recovery receipt identity changed during open")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        data = b"".join(chunks)
    finally:
        os.close(descriptor)
    after = path.lstat()
    if (opened.st_dev, opened.st_ino) != (after.st_dev, after.st_ino):
        raise ValueError("recovery receipt identity changed during read")
    return _validate_record(_load_json_bytes(data), path=path)


def _record_path(receipt_dir: Path, receipt_id: str, state: str) -> Path:
    if not _RECEIPT_ID.fullmatch(receipt_id):
        raise ValueError("receipt_id contains unsafe path characters")
    return Path(receipt_dir) / f"{receipt_id}.{state}.json"


def _require_unused_transaction_id(receipt_dir: Path, receipt_id: str) -> None:
    """Refuse an id if either immutable terminal namespace is occupied."""

    for state in ("committed", "indeterminate"):
        path = _record_path(receipt_dir, receipt_id, state)
        if os.path.lexists(path):
            raise FileExistsError(
                errno.EEXIST,
                "recovery receipt id already has a terminal witness",
                str(path),
            )


def _publish_record(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    record = _validate_record(_json_copy(payload))
    publish_json_atomic(
        path,
        record,
        indent=2,
        sort_keys=True,
        fsync_policy="strict",
    )
    # The publisher is exclusive, but immediate replay still proves that the
    # visible bytes are the exact valid record we intended to make authority.
    observed = validate_receipt(path)
    if not hmac.compare_digest(
        str(observed["receipt_digest"]), str(record["receipt_digest"])
    ):
        raise RecoveryReceiptError(
            "published recovery receipt does not match the intended record",
            stage="receipt-readback",
            committed=False,
            retry_safe=False,
            receipt_committed=True,
        )
    return observed


def prepare_recovery_receipt(
    *,
    receipt_dir: Path,
    receipt_id: str,
    operation: str,
    subject_ref: str,
    before_bytes: bytes,
    predicted_after_bytes: bytes,
    owner_id: str,
    reason: str,
    recorded_at: str,
    commit_witness: Mapping[str, Any],
) -> Path:
    """Publish the immutable WAL intent before any subject mutation."""

    prepared = _with_self_digest(
        {
            "schema": SCHEMA,
            "receipt_id": receipt_id,
            "state": "prepared",
            "operation": operation,
            "subject_ref": subject_ref,
            "owner_id": owner_id,
            "reason": reason,
            "recorded_at": recorded_at,
            "before": _digest_envelope(before_bytes),
            "after": _digest_envelope(predicted_after_bytes),
            "commit_witness": _json_copy(dict(commit_witness)),
        }
    )
    _require_unused_transaction_id(Path(receipt_dir), receipt_id)
    path = _record_path(Path(receipt_dir), receipt_id, "prepared")
    _publish_record(path, prepared)
    return path


def _terminal_base(prepared: Mapping[str, Any], state: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "receipt_id": prepared["receipt_id"],
        "state": state,
        "operation": prepared["operation"],
        "subject_ref": prepared["subject_ref"],
        "owner_id": prepared["owner_id"],
        "reason": prepared["reason"],
        "recorded_at": prepared["recorded_at"],
        "prepared_receipt_digest": prepared["receipt_digest"],
        "commit_witness": _json_copy(prepared["commit_witness"]),
    }


def _observed_fields(data: bytes) -> dict[str, Any]:
    envelope = _digest_envelope(data)
    return {
        "observed_after_raw_sha256": envelope["raw_sha256"],
        "observed_after_semantic_sha256": envelope["semantic_sha256"],
        "observed_after_byte_length": envelope["byte_length"],
    }


def _exception_finding(prefix: str, exc: BaseException) -> str:
    detail = str(exc).strip() or exc.__class__.__name__
    return f"{prefix}: {exc.__class__.__name__}: {detail}"


def _uncertainty_payload(exc: BaseException) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error_type": exc.__class__.__name__,
        "message": str(exc),
    }
    for key in ("stage", "committed", "retry_safe"):
        if hasattr(exc, key):
            payload[key] = getattr(exc, key)
    return payload


def _publish_indeterminate(
    *,
    receipt_dir: Path,
    prepared: Mapping[str, Any],
    finding: str,
    observed: bytes | None = None,
    uncertainty: Mapping[str, Any] | None = None,
) -> tuple[Path, dict[str, Any]]:
    payload = _terminal_base(prepared, "indeterminate")
    payload.update({"finding": finding, "retry_safe": False})
    if observed is not None:
        try:
            payload.update(_observed_fields(observed))
        except (TypeError, ValueError) as exc:
            # A corrupted/non-JSON subject is itself a valid indeterminate
            # outcome.  Preserve its exact raw identity in the uncertainty
            # envelope even though no semantic JSON digest can exist.
            extra = dict(uncertainty or {})
            extra.update(
                {
                    "observed_after_raw_sha256": raw_digest(observed),
                    "observed_after_byte_length": len(observed),
                    "observed_after_semantic_error": str(exc),
                }
            )
            uncertainty = extra
    if uncertainty is not None:
        payload["uncertainty"] = _json_copy(dict(uncertainty))
    record = _with_self_digest(payload)
    path = _record_path(
        Path(receipt_dir), str(prepared["receipt_id"]), "indeterminate"
    )
    try:
        published = _publish_record(path, record)
    except Exception as exc:
        receipt_committed = getattr(exc, "committed", None)
        raise RecoveryReceiptError(
            "subject outcome is non-retry-safe and its indeterminate receipt "
            "could not be durably confirmed",
            stage="indeterminate-receipt-publication",
            committed=True,
            retry_safe=False,
            receipt_committed=(
                bool(receipt_committed) if receipt_committed is not None else None
            ),
        ) from exc
    return path, published


def _indeterminate_outcome(
    *,
    receipt_dir: Path,
    prepared_path: Path,
    prepared: Mapping[str, Any],
    finding: str,
    observed: bytes | None = None,
    uncertainty: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    terminal_path, terminal = _publish_indeterminate(
        receipt_dir=receipt_dir,
        prepared=prepared,
        finding=finding,
        observed=observed,
        uncertainty=uncertainty,
    )
    return {
        "status": "indeterminate",
        "retry_safe": False,
        "receipt_id": prepared["receipt_id"],
        "prepared_path": str(prepared_path),
        "terminal_path": str(terminal_path),
        "receipt_digest": terminal["receipt_digest"],
        "finding": finding,
    }


def _prepared_for_finalize(
    prepared_path: Path,
) -> tuple[Path, dict[str, Any], Path, Path]:
    """Resolve one prepared authority and refuse every terminal replay shape."""

    prepared_path = Path(prepared_path)
    prepared = validate_receipt(prepared_path)
    if prepared.get("state") != "prepared":
        raise ValueError("prepared_path must reference a prepared recovery receipt")
    receipt_dir = prepared_path.parent
    receipt_id = str(prepared["receipt_id"])
    committed_path = _record_path(receipt_dir, receipt_id, "committed")
    indeterminate_path = _record_path(receipt_dir, receipt_id, "indeterminate")
    existing = [
        path
        for path in (committed_path, indeterminate_path)
        if os.path.lexists(path)
    ]
    if len(existing) > 1:
        raise ValueError(
            f"{receipt_id} has conflicting committed and indeterminate witnesses"
        )
    if existing:
        raise FileExistsError(
            errno.EEXIST,
            "recovery receipt already has an immutable terminal witness",
            str(existing[0]),
        )
    return receipt_dir, prepared, committed_path, indeterminate_path


def indeterminate_prepared_recovery(
    *,
    prepared_path: Path,
    finding: str,
    observed_after_bytes: bytes | None = None,
    uncertainty: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Finalize a prepared recovery as indeterminate and non-retry-safe.

    This public split-phase API is used by claim-store transactions whose
    prepared record must be published from an under-lock precommit callback.
    Any existing terminal witness is an immutable replay/collision and is
    refused before publication.
    """

    receipt_dir, prepared, _committed_path, _indeterminate_path = (
        _prepared_for_finalize(prepared_path)
    )
    finding_text = str(finding or "").strip()
    if not finding_text:
        raise ValueError("finding must be a non-empty string")
    return _indeterminate_outcome(
        receipt_dir=receipt_dir,
        prepared_path=Path(prepared_path),
        prepared=prepared,
        finding=finding_text,
        observed=observed_after_bytes,
        uncertainty=uncertainty,
    )


def commit_prepared_recovery(
    *,
    prepared_path: Path,
    observed_after_bytes: bytes,
) -> dict[str, Any]:
    """Finalize a prepared recovery from exact observed subject bytes.

    Exact mismatch never becomes a false commit: it publishes an indeterminate
    witness instead.  A strict terminal-receipt failure before its own commit
    point is handled the same way because the subject transition has already
    happened; a post-publication durability uncertainty retains the typed
    :class:`AtomicWriteError` and never creates a conflicting second terminal.
    """

    receipt_dir, prepared, committed_path, _indeterminate_path = (
        _prepared_for_finalize(prepared_path)
    )
    if not isinstance(observed_after_bytes, bytes):
        return indeterminate_prepared_recovery(
            prepared_path=prepared_path,
            finding="post-commit readback has an invalid type",
            uncertainty={
                "error_type": "TypeError",
                "message": "observed_after_bytes must be bytes",
            },
        )

    try:
        observed_identity = _digest_envelope(observed_after_bytes)
    except (TypeError, ValueError) as exc:
        return indeterminate_prepared_recovery(
            prepared_path=prepared_path,
            finding=_exception_finding(
                "post-commit subject is not valid JSON", exc
            ),
            observed_after_bytes=observed_after_bytes,
            uncertainty=_uncertainty_payload(exc),
        )
    if observed_identity != prepared["after"]:
        return indeterminate_prepared_recovery(
            prepared_path=prepared_path,
            finding=(
                "post-commit readback does not match the exact predicted after bytes"
            ),
            observed_after_bytes=observed_after_bytes,
        )

    committed = _terminal_base(prepared, "committed")
    committed.update(_observed_fields(observed_after_bytes))
    committed["retry_safe"] = False
    committed_record = _with_self_digest(committed)
    try:
        published = _publish_record(committed_path, committed_record)
    except AtomicWriteError as exc:
        if exc.committed:
            # The immutable terminal entry is visible but its directory fsync
            # failed.  Preserve the typed, non-retry-safe strict outcome; a
            # competing terminal record must never be created beside it.
            raise
        return indeterminate_prepared_recovery(
            prepared_path=prepared_path,
            finding=_exception_finding(
                "committed witness publication failed before its commit point",
                exc,
            ),
            observed_after_bytes=observed_after_bytes,
            uncertainty=_uncertainty_payload(exc),
        )
    return {
        "status": "committed",
        "retry_safe": False,
        "receipt_id": prepared["receipt_id"],
        "prepared_path": str(prepared_path),
        "terminal_path": str(committed_path),
        "receipt_digest": published["receipt_digest"],
    }


def execute_recovery(
    *,
    receipt_dir: Path,
    receipt_id: str,
    operation: str,
    subject_ref: str,
    before_bytes: bytes,
    predicted_after_bytes: bytes,
    owner_id: str,
    reason: str,
    recorded_at: str,
    commit_witness: Mapping[str, Any],
    mutate_subject: Callable[[], None],
    read_subject: Callable[[], bytes],
    transition_required: bool = True,
) -> dict[str, Any]:
    """Execute one receipt-first recovery transition.

    A normal exception from ``mutate_subject`` means the callback did not
    commit and is re-raised with only the prepared WAL record remaining.  A
    strict :class:`AtomicWriteError` with ``committed=True`` is different: its
    commit point passed, so this function publishes an indeterminate witness
    and returns ``retry_safe=False``.
    """

    if not transition_required:
        return {
            "status": "not_required",
            "retry_safe": True,
            "receipt_id": receipt_id,
        }

    receipt_dir = Path(receipt_dir)
    prepared_path = prepare_recovery_receipt(
        receipt_dir=receipt_dir,
        receipt_id=receipt_id,
        operation=operation,
        subject_ref=subject_ref,
        before_bytes=before_bytes,
        predicted_after_bytes=predicted_after_bytes,
        owner_id=owner_id,
        reason=reason,
        recorded_at=recorded_at,
        commit_witness=commit_witness,
    )
    validate_receipt(prepared_path)

    try:
        mutate_subject()
    except AtomicWriteError as exc:
        if not exc.committed:
            raise
        observed: bytes | None = None
        try:
            observed = read_subject()
        except Exception:
            pass
        return indeterminate_prepared_recovery(
            prepared_path=prepared_path,
            finding=_exception_finding(
                "subject publication crossed its commit point but durability "
                "could not be confirmed",
                exc,
            ),
            observed_after_bytes=observed,
            uncertainty=_uncertainty_payload(exc),
        )

    try:
        observed_after = read_subject()
    except Exception as exc:
        return indeterminate_prepared_recovery(
            prepared_path=prepared_path,
            finding=_exception_finding(
                "post-commit readback unavailable after subject callback returned",
                exc,
            ),
            uncertainty=_uncertainty_payload(exc),
        )

    if not isinstance(observed_after, bytes):
        exc = TypeError("read_subject must return bytes")
        return indeterminate_prepared_recovery(
            prepared_path=prepared_path,
            finding=_exception_finding("post-commit readback has an invalid type", exc),
            uncertainty=_uncertainty_payload(exc),
        )

    return commit_prepared_recovery(
        prepared_path=prepared_path,
        observed_after_bytes=observed_after,
    )


def verify_receipt_store(receipt_dir: Path) -> list[str]:
    """Return integrity findings for an immutable recovery receipt directory."""

    receipt_dir = Path(receipt_dir)
    if not receipt_dir.exists():
        return []
    if not receipt_dir.is_dir():
        return [f"{receipt_dir}: recovery receipt store is not a directory"]

    findings: list[str] = []
    records: dict[str, dict[str, tuple[Path, dict[str, Any]]]] = {}
    entries = sorted(receipt_dir.iterdir(), key=lambda item: item.name)
    for path in entries:
        if not path.name.endswith(".json"):
            findings.append(f"{path}: unexpected entry in recovery receipt store")
            continue
        try:
            record = validate_receipt(path)
        except (OSError, ValueError, TypeError) as exc:
            findings.append(f"{path}: invalid recovery receipt: {exc}")
            continue
        receipt_id = str(record["receipt_id"])
        state = str(record["state"])
        group = records.setdefault(receipt_id, {})
        if state in group:
            findings.append(f"{path}: duplicate {state} record for {receipt_id}")
            continue
        group[state] = (path, record)

    common = (
        "operation",
        "subject_ref",
        "owner_id",
        "reason",
        "recorded_at",
        "commit_witness",
    )
    for receipt_id, group in sorted(records.items()):
        prepared_pair = group.get("prepared")
        terminals = [state for state in ("committed", "indeterminate") if state in group]
        if terminals and prepared_pair is None:
            findings.append(
                f"{receipt_id}: terminal recovery witness is missing its prepared record"
            )
            continue
        if len(terminals) > 1:
            findings.append(
                f"{receipt_id}: conflicting committed and indeterminate terminal witnesses"
            )
        if prepared_pair is None:
            continue
        _prepared_path, prepared = prepared_pair
        for state in terminals:
            terminal_path, terminal = group[state]
            for key in common:
                if terminal.get(key) != prepared.get(key):
                    findings.append(
                        f"{terminal_path}: {key} does not match prepared authority"
                    )
            if terminal.get("prepared_receipt_digest") != prepared.get("receipt_digest"):
                findings.append(
                    f"{terminal_path}: prepared_receipt_digest does not match prepared record"
                )
            if state == "committed":
                expected = prepared["after"]
                observed = {
                    "raw_sha256": terminal["observed_after_raw_sha256"],
                    "semantic_sha256": terminal["observed_after_semantic_sha256"],
                    "byte_length": terminal["observed_after_byte_length"],
                }
                if observed != expected:
                    findings.append(
                        f"{terminal_path}: committed observation does not match predicted after identity"
                    )
    return findings


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate immutable Agent Runtime recovery receipts"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--receipt-dir",
        type=Path,
        default=DEFAULT_RECEIPT_DIR,
        help="receipt directory, relative to --root unless absolute",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the complete receipt store (the default action)",
    )
    parser.add_argument(
        "--verify",
        action="append",
        type=Path,
        default=[],
        metavar="PATH",
        help="validate one receipt file; may be repeated",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    findings: list[str] = []
    verified: list[str] = []

    for raw_path in args.verify:
        path = raw_path if raw_path.is_absolute() else root / raw_path
        try:
            validate_receipt(path)
        except (OSError, ValueError, TypeError) as exc:
            findings.append(f"{_display_path(path, root)}: {exc}")
        else:
            verified.append(_display_path(path, root))

    # ``--check`` is intentionally also the no-argument default, matching the
    # repository's other gate scripts while retaining a focused --verify mode.
    run_store_check = args.check or not args.verify
    receipt_dir = args.receipt_dir
    if not receipt_dir.is_absolute():
        receipt_dir = root / receipt_dir
    if run_store_check:
        findings.extend(verify_receipt_store(receipt_dir))

    payload = {
        "status": "pass" if not findings else "block",
        "receipt_dir": _display_path(receipt_dir, root),
        "verified": verified,
        "finding_count": len(findings),
        "findings": findings,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif findings:
        print(f"recovery-receipt: block ({len(findings)} finding(s))")
        for finding in findings:
            print(f"- {finding}")
    else:
        print("recovery-receipt: pass")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
