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
import secrets
import stat
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from atomic_io import (
    AtomicWriteError,
    CreatedDirectoryIdentity,
    _ExclusivePrecommitState,
    _cleanup_path_identity,
    _cleanup_rejected_sidecar,
    _direct_parent as _atomic_direct_parent,
    _published_file_identity,
    _rollback_created_parents,
    _run_exclusive_precommit,
    publish_json_atomic,
)


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


_WINDOWS_REPARSE_POINT = 0x0400
_DIRECTORY_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
)
_SECURE_POSIX_DIRFD = (
    os.name == "posix"
    and bool(getattr(os, "O_DIRECTORY", 0))
    and bool(getattr(os, "O_NOFOLLOW", 0))
    and all(
        function in os.supports_dir_fd
        for function in (os.open, os.stat, os.link, os.unlink)
    )
    and os.stat in os.supports_follow_symlinks
    and os.link in os.supports_follow_symlinks
    and os.listdir in os.supports_fd
)


def _is_alias(metadata: Any) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _WINDOWS_REPARSE_POINT
    )


def _same_inode(left: Any, right: Any) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _directory_metadata(path: Path, metadata: Any) -> None:
    if _is_alias(metadata):
        raise ValueError(f"unsafe directory alias in recovery receipt path: {path}")
    if not stat.S_ISDIR(metadata.st_mode):
        raise NotADirectoryError(
            errno.ENOTDIR,
            f"recovery receipt path component is not a directory: {path}",
            str(path),
        )


def _open_posix_directory(directory: Path) -> tuple[Path, int]:
    """Open one lexical directory via a root-anchored no-follow fd walk."""

    if not _SECURE_POSIX_DIRFD:
        raise OSError(
            errno.ENOTSUP,
            "platform lacks secure directory-relative recovery receipt operations",
            str(directory),
        )
    absolute = _absolute_lexical(directory)
    root = Path(absolute.anchor)
    root_before = root.lstat()
    _directory_metadata(root, root_before)
    descriptor = os.open(root, _DIRECTORY_FLAGS)
    try:
        root_opened = os.fstat(descriptor)
        _directory_metadata(root, root_opened)
        if not _same_inode(root_before, root_opened):
            raise ValueError("recovery receipt filesystem root changed during open")

        current = root
        for component in absolute.relative_to(root).parts:
            current = current / component
            try:
                metadata = os.stat(
                    component,
                    dir_fd=descriptor,
                    follow_symlinks=False,
                )
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise ValueError(
                        f"unsafe directory alias in recovery receipt path: {current}"
                    ) from exc
                raise
            _directory_metadata(current, metadata)
            try:
                child = os.open(component, _DIRECTORY_FLAGS, dir_fd=descriptor)
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise ValueError(
                        f"unsafe directory alias in recovery receipt path: {current}"
                    ) from exc
                raise
            try:
                opened = os.fstat(child)
                _directory_metadata(current, opened)
                if not _same_inode(metadata, opened):
                    raise ValueError(
                        f"recovery receipt directory identity changed during open: {current}"
                    )
            except BaseException:
                os.close(child)
                raise
            os.close(descriptor)
            descriptor = child
        return absolute, descriptor
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def _fallback_directory_snapshot(directory: Path) -> tuple[tuple[str, int, int], ...]:
    """Capture an alias-free lexical ancestor chain for non-dirfd platforms."""

    absolute = _absolute_lexical(directory)
    root = Path(absolute.anchor)
    paths = [root]
    cursor = root
    for component in absolute.relative_to(root).parts:
        cursor = cursor / component
        paths.append(cursor)
    snapshot: list[tuple[str, int, int]] = []
    for candidate in paths:
        metadata = candidate.lstat()
        _directory_metadata(candidate, metadata)
        snapshot.append((os.fspath(candidate), metadata.st_dev, metadata.st_ino))
    return tuple(snapshot)


@contextmanager
def _verified_parent(path: Path) -> Iterator[tuple[Path, int | None]]:
    """Pin a receipt's alias-free parent and verify its lexical identity after use."""

    absolute = _absolute_lexical(Path(path))
    if os.name == "posix":
        parent_path, parent_fd = _open_posix_directory(absolute.parent)
        owned_parent_fd: int | None = parent_fd
        operation_failed = False
        try:
            parent_identity = os.fstat(parent_fd)
            yield absolute, parent_fd
            reopened_fd: int | None = None
            reopen_failed = False
            try:
                reopened_path, reopened_fd = _open_posix_directory(parent_path)
                if reopened_path != parent_path or not _same_inode(
                    parent_identity, os.fstat(reopened_fd)
                ):
                    raise ValueError(
                        "recovery receipt parent identity changed during access"
                    )
            except BaseException:
                reopen_failed = True
                raise
            finally:
                if reopened_fd is not None:
                    descriptor = reopened_fd
                    reopened_fd = None
                    try:
                        os.close(descriptor)
                    except OSError:
                        if not reopen_failed:
                            raise
        except BaseException:
            operation_failed = True
            raise
        finally:
            if owned_parent_fd is not None:
                descriptor = owned_parent_fd
                owned_parent_fd = None
                try:
                    os.close(descriptor)
                except OSError:
                    if not operation_failed:
                        raise
        return

    before = _fallback_directory_snapshot(absolute.parent)
    yield absolute, None
    after = _fallback_directory_snapshot(absolute.parent)
    if before != after:
        raise ValueError("recovery receipt parent identity changed during access")


@contextmanager
def _verified_regular_file(
    path: Path,
    *,
    access: int = os.O_RDONLY,
) -> Iterator[tuple[Path, int, int | None]]:
    """Open one regular receipt without following its file or parent aliases."""

    with _verified_parent(path) as (absolute, parent_fd):
        if parent_fd is not None:
            metadata = os.stat(
                absolute.name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        else:
            metadata = absolute.lstat()
        if _is_alias(metadata):
            raise ValueError("recovery receipt must not be a symlink or reparse point")
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("recovery receipt must be a regular file")

        flags = (
            access
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        if parent_fd is not None:
            descriptor = os.open(absolute.name, flags, dir_fd=parent_fd)
        else:
            descriptor = os.open(absolute, flags)
        owned_descriptor: int | None = descriptor
        operation_failed = False
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise ValueError("opened recovery receipt is not a regular file")
            if not _same_inode(metadata, opened):
                raise ValueError("recovery receipt identity changed during open")
            yield absolute, descriptor, parent_fd
            if parent_fd is not None:
                after = os.stat(
                    absolute.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            else:
                after = absolute.lstat()
            if _is_alias(after) or not _same_inode(opened, after):
                raise ValueError("recovery receipt identity changed during access")
        except BaseException:
            operation_failed = True
            raise
        finally:
            if owned_descriptor is not None:
                descriptor_to_close = owned_descriptor
                owned_descriptor = None
                try:
                    os.close(descriptor_to_close)
                except OSError:
                    if not operation_failed:
                        raise


def _read_descriptor(descriptor: int) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _validate_receipt_descriptor(path: Path, descriptor: int) -> dict[str, Any]:
    return _validate_record(
        _load_json_bytes(_read_descriptor(descriptor)),
        path=Path(path),
    )


def validate_receipt(path: Path) -> dict[str, Any]:
    """Load one receipt through an alias-free path and verify its self digest."""

    with _verified_regular_file(path) as (absolute, descriptor, _parent_fd):
        return _validate_receipt_descriptor(absolute, descriptor)


def _validate_receipt_at(
    directory_fd: int,
    name: str,
    display_path: Path,
) -> dict[str, Any]:
    """Validate one store entry relative to its already verified directory fd."""

    if not name or Path(name).name != name:
        raise ValueError("recovery receipt store entry has an unsafe name")
    metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if _is_alias(metadata):
        raise ValueError("recovery receipt must not be a symlink or reparse point")
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("recovery receipt must be a regular file")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(name, flags, dir_fd=directory_fd)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or not _same_inode(metadata, opened):
            raise ValueError("recovery receipt identity changed during store open")
        record = _validate_receipt_descriptor(display_path, descriptor)
        after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if _is_alias(after) or not _same_inode(opened, after):
            raise ValueError("recovery receipt identity changed during store read")
        return record
    finally:
        os.close(descriptor)


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


def _write_all(descriptor: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(descriptor, data[offset:])
        if written <= 0:
            raise OSError(errno.EIO, "short write while publishing recovery receipt")
        offset += written


def _publish_record_at(
    parent_fd: int,
    path: Path,
    record: Mapping[str, Any],
    *,
    precommit: Callable[[], None] | None = None,
    created_parents: list[CreatedDirectoryIdentity] | None = None,
) -> None:
    """Strictly publish one immutable record into a pinned POSIX directory."""

    if os.name != "posix":
        raise OSError(
            errno.ENOTSUP,
            "directory-relative recovery receipt publication requires POSIX",
            str(path),
        )
    if not path.name or Path(path.name).name != path.name:
        raise ValueError("recovery receipt publication has an unsafe filename")
    data = (
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor: int | None = None
    sidecar: str | None = None
    published = False
    precommit_state = (
        _ExclusivePrecommitState(precommit) if precommit is not None else None
    )
    owned_parents = created_parents if created_parents is not None else []
    for _attempt in range(128):
        candidate = f".{path.name}.tmp-{secrets.token_hex(12)}"
        try:
            descriptor = os.open(candidate, flags, 0o600, dir_fd=parent_fd)
        except FileExistsError:
            continue
        sidecar = candidate
        break
    if descriptor is None or sidecar is None:
        raise FileExistsError(
            errno.EEXIST,
            "could not reserve an exclusive recovery receipt sidecar",
            str(path),
        )

    try:
        opened: Any | None = None
        opened_cleanup_identity: Any | None = None
        write_failed = False
        try:
            _write_all(descriptor, data)
            try:
                os.fsync(descriptor)
            except OSError as exc:
                raise AtomicWriteError(
                    "recovery receipt file fsync failed before publication",
                    stage="file-fsync",
                    committed=False,
                    retry_safe=True,
                ) from exc
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or opened.st_size != len(data):
                raise OSError(
                    errno.EIO,
                    "recovery receipt sidecar identity changed before publication",
                    sidecar,
                )
            opened_cleanup_identity = _cleanup_path_identity(
                path.parent / sidecar,
                opened,
            )
        except BaseException:
            write_failed = True
            raise
        finally:
            descriptor_to_close = descriptor
            descriptor = None
            try:
                os.close(descriptor_to_close)
            except OSError as exc:
                if not write_failed:
                    raise AtomicWriteError(
                        "recovery receipt file close failed before publication",
                        stage="file-close",
                        committed=False,
                        retry_safe=True,
                    ) from exc

        sidecar_metadata = os.stat(
            sidecar,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        if (
            opened is None
            or _is_alias(sidecar_metadata)
            or not stat.S_ISREG(sidecar_metadata.st_mode)
            or not _same_inode(opened, sidecar_metadata)
            or sidecar_metadata.st_size != len(data)
        ):
            raise OSError(
                errno.EIO,
                "recovery receipt sidecar changed before publication",
                sidecar,
            )
        if precommit_state is not None:
            # External authority must be proved inside the publisher, after
            # all fallible sidecar preparation and immediately before the
            # immutable destination link becomes visible.  A rejected proof
            # can reclaim only the exact callback-bound sidecar and parents.
            assert opened is not None
            assert opened_cleanup_identity is not None
            _run_exclusive_precommit(
                precommit_state,
                path,
                sidecar,
                parent_fd,
                _published_file_identity(opened),
                opened_cleanup_identity,
            )
        os.link(
            sidecar,
            path.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
            follow_symlinks=False,
        )
        published = True
        try:
            os.unlink(sidecar, dir_fd=parent_fd)
        except OSError:
            # The link already crossed the commit point.  Persist that fact
            # before retrying cleanup, then persist a successful retry too.
            pass
        else:
            sidecar = None
        try:
            os.fsync(parent_fd)
        except OSError as exc:
            raise AtomicWriteError(
                "recovery receipt committed but parent directory fsync failed",
                stage="parent-fsync",
                committed=True,
                retry_safe=False,
            ) from exc
        if sidecar is not None:
            try:
                os.unlink(sidecar, dir_fd=parent_fd)
            except OSError as exc:
                raise AtomicWriteError(
                    "recovery receipt committed but sidecar cleanup failed",
                    stage="sidecar-cleanup",
                    committed=True,
                    retry_safe=False,
                ) from exc
            sidecar = None
            try:
                os.fsync(parent_fd)
            except OSError as exc:
                raise AtomicWriteError(
                    "recovery receipt committed but sidecar cleanup fsync failed",
                    stage="sidecar-cleanup-fsync",
                    committed=True,
                    retry_safe=False,
                ) from exc
    finally:
        if descriptor is not None:
            descriptor_to_close = descriptor
            descriptor = None
            try:
                os.close(descriptor_to_close)
            except OSError:
                pass
        if sidecar is not None and not published:
            if precommit_state is not None and precommit_state.phase == "rejected":
                try:
                    authority = _cleanup_rejected_sidecar(
                        precommit_state,
                        path,
                        sidecar,
                        parent_fd,
                        owned_parents,
                    )
                    if authority is not None:
                        _rollback_created_parents(owned_parents, authority)
                except BaseException:
                    pass
            elif (
                precommit_state is not None
                and precommit_state.phase
                in {"pending", "armed", "capture_failed"}
            ):
                pass
            else:
                try:
                    os.unlink(sidecar, dir_fd=parent_fd)
                except OSError:
                    pass


def _readback_published_record(
    path: Path,
    record: Mapping[str, Any],
    *,
    parent_fd: int | None,
) -> dict[str, Any]:
    """Validate the just-published authority through its pinned parent."""

    # The publisher is exclusive, but immediate replay still proves that the
    # visible bytes are the exact valid record we intended to make authority.
    try:
        if parent_fd is not None:
            observed = _validate_receipt_at(parent_fd, path.name, path)
        else:
            observed = validate_receipt(path)
    except (OSError, TypeError, ValueError) as exc:
        terminal = record["state"] != "prepared"
        raise RecoveryReceiptError(
            "published recovery receipt could not be read back and validated",
            stage="receipt-readback",
            committed=terminal,
            retry_safe=False,
            # Exclusive publication returned successfully.  The receipt path
            # is therefore visible even though its readback is uncertain.
            receipt_committed=True,
        ) from exc
    if not hmac.compare_digest(
        str(observed["receipt_digest"]), str(record["receipt_digest"])
    ):
        terminal = record["state"] != "prepared"
        raise RecoveryReceiptError(
            "published recovery receipt does not match the intended record",
            stage="receipt-readback",
            committed=terminal,
            retry_safe=False,
            receipt_committed=True,
        )
    return observed


def _publish_record(
    path: Path,
    payload: Mapping[str, Any],
    *,
    parent_fd: int | None = None,
    precommit: Callable[[], None] | None = None,
) -> dict[str, Any]:
    record = _validate_record(_json_copy(payload))
    if parent_fd is not None:
        _publish_record_at(
            parent_fd,
            path,
            record,
            precommit=precommit,
        )
        return _readback_published_record(
            path,
            record,
            parent_fd=parent_fd,
        )

    if os.name == "posix":
        # Reuse atomic_io's secure create/no-alias parent walk, then keep that
        # directory descriptor pinned through sidecar preparation, the actor
        # proof, destination link, durability fsync, and exact readback.
        created_parents: list[CreatedDirectoryIdentity] = []
        with _atomic_direct_parent(
            path,
            strict_creation_fsync=True,
            created_parents=created_parents,
        ) as (absolute, pinned_parent_fd):
            if pinned_parent_fd is None:
                raise OSError(
                    errno.ENOTSUP,
                    "POSIX receipt publication requires a pinned parent",
                    str(path),
                )
            _publish_record_at(
                pinned_parent_fd,
                absolute,
                record,
                precommit=precommit,
                created_parents=created_parents,
            )
            return _readback_published_record(
                absolute,
                record,
                parent_fd=pinned_parent_fd,
            )

    # Non-POSIX atomic_io performs the platform's direct-parent checks, durable
    # sidecar preparation, and final callback immediately before destination
    # publication. A rejected callback also rolls back only parents that this
    # exclusive publication provably created.
    publish_json_atomic(
        path,
        record,
        indent=2,
        sort_keys=True,
        fsync_policy="strict",
        precommit=precommit,
    )
    return _readback_published_record(
        path,
        record,
        parent_fd=None,
    )


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
    precommit: Callable[[], None] | None = None,
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
    _publish_record(path, prepared, precommit=precommit)
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
    parent_fd: int | None = None,
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
        published = _publish_record(path, record, parent_fd=parent_fd)
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
    parent_fd: int | None = None,
) -> dict[str, Any]:
    terminal_path, terminal = _publish_indeterminate(
        receipt_dir=receipt_dir,
        prepared=prepared,
        finding=finding,
        observed=observed,
        uncertainty=uncertainty,
        parent_fd=parent_fd,
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
    return _prepared_for_finalize_record(prepared_path, prepared)


def _entry_exists(path: Path, parent_fd: int | None) -> bool:
    if parent_fd is None:
        return os.path.lexists(path)
    try:
        os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _prepared_for_finalize_record(
    prepared_path: Path,
    prepared: Mapping[str, Any],
    *,
    parent_fd: int | None = None,
    subject_committed: bool = True,
) -> tuple[Path, dict[str, Any], Path, Path]:
    """Resolve terminal paths from prepared bytes already verified under lock."""

    prepared_path = Path(prepared_path)
    if prepared.get("state") != "prepared":
        raise ValueError("prepared_path must reference a prepared recovery receipt")
    prepared_record = dict(prepared)
    receipt_dir = prepared_path.parent
    receipt_id = str(prepared_record["receipt_id"])
    committed_path = _record_path(receipt_dir, receipt_id, "committed")
    indeterminate_path = _record_path(receipt_dir, receipt_id, "indeterminate")
    try:
        existing = [
            path
            for path in (committed_path, indeterminate_path)
            if _entry_exists(path, parent_fd)
        ]
    except OSError as exc:
        raise RecoveryReceiptError(
            "recovery receipt terminal authority could not be inspected",
            stage="terminal-authority-stat",
            committed=subject_committed,
            retry_safe=not subject_committed,
            receipt_committed=None,
        ) from exc
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
    return receipt_dir, prepared_record, committed_path, indeterminate_path


def _lock_prepared_descriptor(descriptor: int) -> Callable[[], None]:
    """Acquire the platform process-shared lock and return its unlock action."""

    if os.name == "posix":
        import fcntl

        fcntl.flock(descriptor, fcntl.LOCK_EX)

        def unlock_posix() -> None:
            fcntl.flock(descriptor, fcntl.LOCK_UN)

        return unlock_posix
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)

        def unlock_windows() -> None:
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)

        return unlock_windows
    raise OSError(
        errno.ENOTSUP,
        "platform has no supported process-shared recovery transaction lock",
    )


@contextmanager
def _terminal_transaction_lock(
    prepared_path: Path,
) -> Iterator[tuple[dict[str, Any], int | None]]:
    """Serialize both terminal namespaces using the immutable WAL inode.

    A persistent ``*.lock`` sentinel can become stale after a crash and would
    itself pollute the immutable receipt namespace.  The prepared record is
    already mandatory and immutable, so an advisory exclusive lock on its
    verified inode is the transaction-scoped arbiter.  POSIX ``flock`` and the
    Windows CRT byte-range lock both arbitrate separate opens in this process
    and other processes; the operating system releases either lock if a
    finalizer exits unexpectedly.

    The same locked descriptor supplies the prepared bytes.  This matters on
    Windows, where opening a second handle and reading its locked byte can fail
    even in the locking process.  The shared verified-parent primitive rejects
    ancestor aliases and stale file identities on every platform.
    """

    access = os.O_RDWR if os.name == "nt" else os.O_RDONLY
    with _verified_regular_file(prepared_path, access=access) as (
        absolute,
        descriptor,
        parent_fd,
    ):
        unlock: Callable[[], None] | None = None
        try:
            # On Windows this is an exclusive byte-0 msvcrt lock; the prepared
            # bytes below are deliberately read from this same descriptor.
            unlock = _lock_prepared_descriptor(descriptor)

            prepared = _validate_receipt_descriptor(absolute, descriptor)
            if prepared.get("state") != "prepared":
                raise ValueError(
                    "prepared_path must reference a prepared recovery receipt"
                )
            yield prepared, parent_fd
        finally:
            if unlock is not None:
                try:
                    unlock()
                except OSError:
                    pass


def _terminal_receipt_visibility(prepared_path: Path) -> bool | None:
    """Best-effort truth about whether either terminal namespace is occupied."""

    path = Path(prepared_path)
    suffix = ".prepared.json"
    if not path.name.endswith(suffix):
        return None
    receipt_id = path.name[: -len(suffix)]
    if not _RECEIPT_ID.fullmatch(receipt_id):
        return None

    visible = False
    try:
        with _verified_parent(path) as (absolute, parent_fd):
            for state in ("committed", "indeterminate"):
                terminal_path = _record_path(absolute.parent, receipt_id, state)
                try:
                    if parent_fd is not None:
                        os.stat(
                            terminal_path.name,
                            dir_fd=parent_fd,
                            follow_symlinks=False,
                        )
                    else:
                        terminal_path.lstat()
                except FileNotFoundError:
                    continue
                else:
                    visible = True
    except (OSError, ValueError):
        return None
    return visible


@contextmanager
def _subject_committed_transaction_lock(
    prepared_path: Path,
) -> Iterator[tuple[dict[str, Any], int | None]]:
    """Type lock-acquisition failures at the split-phase commit boundary.

    Public split-phase finalizers are only called after their subject mutation
    crossed its commit point.  A missing/unsafe prepared inode or a failed
    process-shared lock must therefore never look like a retry-safe filesystem
    error.  Exceptions raised *after* the lock is acquired retain their normal
    API meaning (for example immutable replay remains ``FileExistsError``).
    """

    entered = False
    body_failed = False
    try:
        with _terminal_transaction_lock(prepared_path) as authority:
            entered = True
            try:
                yield authority
            except BaseException:
                body_failed = True
                raise
    except (ImportError, OSError, ValueError) as exc:
        if entered and body_failed:
            raise
        if entered:
            raise RecoveryReceiptError(
                "subject committed and its terminal receipt was published, but "
                "the recovery receipt parent identity changed",
                stage="terminal-transaction-path",
                committed=True,
                retry_safe=False,
                receipt_committed=True,
            ) from exc
        raise RecoveryReceiptError(
            "subject committed but its recovery transaction lock could not be acquired",
            stage="terminal-transaction-lock",
            committed=True,
            retry_safe=False,
            receipt_committed=_terminal_receipt_visibility(prepared_path),
        ) from exc


@contextmanager
def _subject_precommit_transaction_lock(
    prepared_path: Path,
) -> Iterator[tuple[dict[str, Any], int | None]]:
    """Type execute-time lock failures before the subject callback may run."""

    entered = False
    body_failed = False
    try:
        with _terminal_transaction_lock(prepared_path) as authority:
            entered = True
            try:
                yield authority
            except BaseException:
                body_failed = True
                raise
    except (ImportError, OSError, ValueError) as exc:
        if entered and body_failed:
            raise
        if entered:
            # The locked execute helper only returns after the subject callback
            # and a terminal witness both commit.  Pre-callback failures escape
            # through the body_failed branch with their original truth state.
            raise RecoveryReceiptError(
                "subject committed and its terminal receipt was published, but "
                "the recovery receipt parent identity changed",
                stage="terminal-transaction-path",
                committed=True,
                retry_safe=False,
                receipt_committed=True,
            ) from exc
        raise RecoveryReceiptError(
            "prepared recovery transaction lock could not be acquired before subject CAS",
            stage="terminal-transaction-lock",
            committed=False,
            retry_safe=True,
            # prepare_recovery_receipt completed its exclusive publication and
            # readback before this acquisition was attempted.
            receipt_committed=True,
        ) from exc


def _indeterminate_prepared_recovery_locked(
    *,
    prepared_path: Path,
    prepared: Mapping[str, Any],
    parent_fd: int | None,
    finding: str,
    observed_after_bytes: bytes | None = None,
    uncertainty: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    receipt_dir, prepared, _committed_path, _indeterminate_path = (
        _prepared_for_finalize_record(
            prepared_path,
            prepared,
            parent_fd=parent_fd,
        )
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
        parent_fd=parent_fd,
    )


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

    with _subject_committed_transaction_lock(prepared_path) as authority:
        prepared, parent_fd = authority
        return _indeterminate_prepared_recovery_locked(
            prepared_path=prepared_path,
            prepared=prepared,
            parent_fd=parent_fd,
            finding=finding,
            observed_after_bytes=observed_after_bytes,
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

    with _subject_committed_transaction_lock(prepared_path) as authority:
        prepared, parent_fd = authority
        return _commit_prepared_recovery_locked(
            prepared_path=prepared_path,
            prepared=prepared,
            parent_fd=parent_fd,
            observed_after_bytes=observed_after_bytes,
        )


def _commit_prepared_recovery_locked(
    *,
    prepared_path: Path,
    prepared: Mapping[str, Any],
    parent_fd: int | None,
    observed_after_bytes: bytes,
) -> dict[str, Any]:
    """Finalize while the prepared transaction inode is exclusively locked."""

    receipt_dir, prepared, committed_path, _indeterminate_path = (
        _prepared_for_finalize_record(
            prepared_path,
            prepared,
            parent_fd=parent_fd,
        )
    )
    if not isinstance(observed_after_bytes, bytes):
        return _indeterminate_outcome(
            receipt_dir=receipt_dir,
            prepared_path=Path(prepared_path),
            prepared=prepared,
            finding="post-commit readback has an invalid type",
            uncertainty={
                "error_type": "TypeError",
                "message": "observed_after_bytes must be bytes",
            },
            parent_fd=parent_fd,
        )

    try:
        observed_identity = _digest_envelope(observed_after_bytes)
    except (TypeError, ValueError) as exc:
        return _indeterminate_outcome(
            receipt_dir=receipt_dir,
            prepared_path=Path(prepared_path),
            prepared=prepared,
            finding=_exception_finding(
                "post-commit subject is not valid JSON", exc
            ),
            observed=observed_after_bytes,
            uncertainty=_uncertainty_payload(exc),
            parent_fd=parent_fd,
        )
    if observed_identity != prepared["after"]:
        return _indeterminate_outcome(
            receipt_dir=receipt_dir,
            prepared_path=Path(prepared_path),
            prepared=prepared,
            finding=(
                "post-commit readback does not match the exact predicted after bytes"
            ),
            observed=observed_after_bytes,
            parent_fd=parent_fd,
        )

    committed = _terminal_base(prepared, "committed")
    committed.update(_observed_fields(observed_after_bytes))
    committed["retry_safe"] = False
    committed_record = _with_self_digest(committed)
    try:
        published = _publish_record(
            committed_path,
            committed_record,
            parent_fd=parent_fd,
        )
    except AtomicWriteError as exc:
        if exc.committed:
            raise RecoveryReceiptError(
                "subject committed and its committed witness crossed the "
                "publication point, but durability could not be confirmed",
                stage="committed-receipt-publication",
                committed=True,
                retry_safe=False,
                receipt_committed=True,
            ) from exc
        return _indeterminate_outcome(
            receipt_dir=receipt_dir,
            prepared_path=Path(prepared_path),
            prepared=prepared,
            finding=_exception_finding(
                "committed witness publication failed before its commit point",
                exc,
            ),
            observed=observed_after_bytes,
            uncertainty=_uncertainty_payload(exc),
            parent_fd=parent_fd,
        )
    except RecoveryReceiptError:
        # A successful exclusive publication followed by uncertain readback
        # already owns the committed terminal namespace.  Never attempt the
        # opposing terminal name.
        raise
    except OSError as exc:
        try:
            committed_visible = _entry_exists(committed_path, parent_fd)
        except OSError as visibility_exc:
            raise RecoveryReceiptError(
                "subject committed; committed witness publication failed and "
                "terminal visibility could not be determined "
                f"({exc}; visibility probe: {visibility_exc})",
                stage="committed-receipt-publication",
                committed=True,
                retry_safe=False,
                receipt_committed=None,
            ) from visibility_exc
        if committed_visible:
            raise RecoveryReceiptError(
                "subject committed and a committed witness may be visible, "
                "but publication could not be confirmed",
                stage="committed-receipt-publication",
                committed=True,
                retry_safe=False,
                receipt_committed=None,
            ) from exc
        return _indeterminate_outcome(
            receipt_dir=receipt_dir,
            prepared_path=Path(prepared_path),
            prepared=prepared,
            finding=_exception_finding(
                "committed witness publication failed", exc
            ),
            observed=observed_after_bytes,
            uncertainty=_uncertainty_payload(exc),
            parent_fd=parent_fd,
        )
    return {
        "status": "committed",
        "retry_safe": False,
        "receipt_id": prepared["receipt_id"],
        "prepared_path": str(prepared_path),
        "terminal_path": str(committed_path),
        "receipt_digest": published["receipt_digest"],
    }


def _execute_prepared_recovery_locked(
    *,
    prepared_path: Path,
    prepared: Mapping[str, Any],
    parent_fd: int | None,
    before_bytes: bytes,
    mutate_subject: Callable[[], None],
    read_subject: Callable[[], bytes],
) -> dict[str, Any]:
    """Run CAS, subject callback, observation, and terminal under one lock."""

    # Reject a terminal that raced preparation but won before this executor
    # acquired the transaction lock.  Once this check passes, the same lock is
    # retained through the subject commit and terminal receipt publication.
    _prepared_for_finalize_record(
        prepared_path,
        prepared,
        parent_fd=parent_fd,
        subject_committed=False,
    )

    # This is the compare-and-swap boundary for the subject's exact byte
    # identity.  Recovery callers also hold their subject/store lock around the
    # executor; do not insert fallible work between this read/compare and the
    # callback.  Semantic equivalence is deliberately insufficient because the
    # prepared WAL binds raw bytes as the mutation precondition.
    try:
        observed_before = read_subject()
    except Exception as exc:
        raise RecoveryReceiptError(
            "prepared recovery could not read the subject before its raw CAS",
            stage="subject-before-cas",
            committed=False,
            retry_safe=True,
            receipt_committed=True,
        ) from exc
    if not isinstance(observed_before, bytes):
        raise RecoveryReceiptError(
            "prepared recovery subject raw CAS requires bytes",
            stage="subject-before-cas",
            committed=False,
            retry_safe=True,
            receipt_committed=True,
        )
    if not hmac.compare_digest(observed_before, before_bytes):
        raise RecoveryReceiptError(
            "prepared recovery subject drifted from the exact before bytes",
            stage="subject-before-cas",
            committed=False,
            retry_safe=True,
            receipt_committed=True,
        )

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
        return _indeterminate_prepared_recovery_locked(
            prepared_path=prepared_path,
            prepared=prepared,
            parent_fd=parent_fd,
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
        return _indeterminate_prepared_recovery_locked(
            prepared_path=prepared_path,
            prepared=prepared,
            parent_fd=parent_fd,
            finding=_exception_finding(
                "post-commit readback unavailable after subject callback returned",
                exc,
            ),
            uncertainty=_uncertainty_payload(exc),
        )

    if not isinstance(observed_after, bytes):
        exc = TypeError("read_subject must return bytes")
        return _indeterminate_prepared_recovery_locked(
            prepared_path=prepared_path,
            prepared=prepared,
            parent_fd=parent_fd,
            finding=_exception_finding("post-commit readback has an invalid type", exc),
            uncertainty=_uncertainty_payload(exc),
        )

    return _commit_prepared_recovery_locked(
        prepared_path=prepared_path,
        prepared=prepared,
        parent_fd=parent_fd,
        observed_after_bytes=observed_after,
    )


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
    precommit: Callable[[], None] | None = None,
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
        precommit=precommit,
    )
    with _subject_precommit_transaction_lock(prepared_path) as authority:
        prepared, parent_fd = authority
        return _execute_prepared_recovery_locked(
            prepared_path=prepared_path,
            prepared=prepared,
            parent_fd=parent_fd,
            before_bytes=before_bytes,
            mutate_subject=mutate_subject,
            read_subject=read_subject,
        )


def verify_receipt_store(receipt_dir: Path) -> list[str]:
    """Return integrity findings for an immutable recovery receipt directory."""

    receipt_dir = Path(receipt_dir)
    findings: list[str] = []
    records: dict[str, dict[str, tuple[Path, dict[str, Any]]]] = {}
    absolute_store = _absolute_lexical(receipt_dir)

    def add_record(path: Path, record: dict[str, Any]) -> None:
        receipt_id = str(record["receipt_id"])
        state = str(record["state"])
        group = records.setdefault(receipt_id, {})
        if state in group:
            findings.append(f"{path}: duplicate {state} record for {receipt_id}")
            return
        group[state] = (path, record)

    if os.name == "posix":
        store_fd: int | None = None
        try:
            absolute_store, store_fd = _open_posix_directory(absolute_store)
        except FileNotFoundError:
            return []
        except (OSError, ValueError) as exc:
            return [f"{receipt_dir}: unsafe recovery receipt store path: {exc}"]
        try:
            store_identity = os.fstat(store_fd)
        except OSError as exc:
            findings.append(
                f"{receipt_dir}: recovery receipt store identity unavailable: {exc}"
            )
            descriptor = store_fd
            store_fd = None
            try:
                os.close(descriptor)
            except OSError as close_exc:
                findings.append(
                    f"{receipt_dir}: cannot close recovery receipt store: "
                    f"{close_exc}"
                )
            return findings
        try:
            try:
                names = sorted(os.listdir(store_fd))
            except OSError as exc:
                findings.append(f"{receipt_dir}: cannot enumerate receipt store: {exc}")
                names = []
            for name in names:
                path = absolute_store / name
                if not name.endswith(".json"):
                    findings.append(
                        f"{path}: unexpected entry in recovery receipt store"
                    )
                    continue
                try:
                    record = _validate_receipt_at(store_fd, name, path)
                except (OSError, ValueError, TypeError) as exc:
                    findings.append(f"{path}: invalid recovery receipt: {exc}")
                    continue
                add_record(path, record)

            try:
                names_after = sorted(os.listdir(store_fd))
            except OSError as exc:
                findings.append(
                    f"{receipt_dir}: cannot re-enumerate receipt store: {exc}"
                )
            else:
                if names_after != names:
                    findings.append(
                        f"{receipt_dir}: recovery receipt store contents changed "
                        "during verification"
                    )

            reopened_fd: int | None = None
            try:
                reopened_path, reopened_fd = _open_posix_directory(absolute_store)
                if reopened_path != absolute_store or not _same_inode(
                    store_identity, os.fstat(reopened_fd)
                ):
                    findings.append(
                        f"{receipt_dir}: recovery receipt store identity changed "
                        "during verification"
                    )
            except (OSError, ValueError) as exc:
                findings.append(
                    f"{receipt_dir}: recovery receipt store path changed or became an alias: {exc}"
                )
            finally:
                if reopened_fd is not None:
                    os.close(reopened_fd)
        finally:
            descriptor = store_fd
            store_fd = None
            try:
                os.close(descriptor)
            except OSError as exc:
                findings.append(
                    f"{receipt_dir}: cannot close recovery receipt store: {exc}"
                )
    else:
        try:
            before_snapshot = _fallback_directory_snapshot(absolute_store)
        except FileNotFoundError:
            return []
        except (OSError, ValueError) as exc:
            return [f"{receipt_dir}: unsafe recovery receipt store path: {exc}"]
        try:
            entries = sorted(absolute_store.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            findings.append(f"{receipt_dir}: cannot enumerate receipt store: {exc}")
            entries = []
        for path in entries:
            if not path.name.endswith(".json"):
                findings.append(f"{path}: unexpected entry in recovery receipt store")
                continue
            try:
                record = validate_receipt(path)
            except (OSError, ValueError, TypeError) as exc:
                findings.append(f"{path}: invalid recovery receipt: {exc}")
                continue
            add_record(path, record)
        try:
            entries_after = sorted(
                absolute_store.iterdir(),
                key=lambda item: item.name,
            )
        except OSError as exc:
            findings.append(
                f"{receipt_dir}: cannot re-enumerate receipt store: {exc}"
            )
        else:
            if [entry.name for entry in entries_after] != [
                entry.name for entry in entries
            ]:
                findings.append(
                    f"{receipt_dir}: recovery receipt store contents changed "
                    "during verification"
                )
        try:
            after_snapshot = _fallback_directory_snapshot(absolute_store)
        except (OSError, ValueError) as exc:
            findings.append(
                f"{receipt_dir}: recovery receipt store path changed or became an alias: {exc}"
            )
        else:
            if before_snapshot != after_snapshot:
                findings.append(
                    f"{receipt_dir}: recovery receipt store identity changed during verification"
                )

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
        if not terminals:
            findings.append(
                f"{receipt_id}: unresolved prepared recovery has no terminal witness"
            )
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
