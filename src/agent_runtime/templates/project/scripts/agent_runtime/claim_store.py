"""Durable, fail-closed authority for the Runtime task-claim store."""

from __future__ import annotations

import contextlib
import json
import math
import os
import re
import stat
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator, Mapping


MARKER_SCHEMA = "agent-runtime-task-claim-store/v1"
WITNESS_SCHEMA = "agent-runtime-task-claim/v1"
MARKER_MAX_BYTES = 4096
CLAIM_MAX_BYTES = 256 * 1024
JSON_MAX_INTEGER_DIGITS = 256
CLAIM_IDENTITY_MAX_CHARS = 160
MAX_STORE_ENTRIES = 4096
LOCK_TIMEOUT_SECONDS = 5.0
DEFAULT_CLAIM_LEASE_MINUTES = 30
DEFAULT_CLAIM_GRACE_SECONDS = 600
CLAIM_GRACE_ENV = "AGENT_RUNTIME_REAPER_GRACE_SECONDS"
_WINDOWS_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400)
_CLAIM_ID = re.compile(r"^CLAIM-[A-Za-z0-9][A-Za-z0-9._-]*$")
ACTIVE_CLAIM_STATUSES = frozenset(
    {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}
)
INACTIVE_CLAIM_STATUSES = frozenset(
    {"blocked", "closed", "completed", "done", "expired", "released"}
)


class ClaimStoreError(RuntimeError):
    """The claim-store authority could not be established safely."""


class ClaimStoreLockTimeout(ClaimStoreError, TimeoutError):
    """The checkout-local claim-store transaction lock timed out."""


def _duration_error(field: str, detail: str) -> ValueError:
    label = re.sub(r"\s+", " ", str(field)).strip()[:96] or "duration"
    return ValueError(f"{label} {detail}"[:256])


def require_duration(value: object, *, field: str, minimum: int) -> int:
    """Return a plain integer duration that satisfies the caller's minimum."""

    if type(minimum) is not int:
        raise _duration_error(field, "minimum is invalid")
    if type(value) is not int or value < minimum:
        raise _duration_error(
            field,
            f"must be a plain integer greater than or equal to {minimum}",
        )
    return value


def expiration_after(
    now: datetime,
    value: object,
    *,
    unit: str,
    field: str,
    minimum: int,
) -> datetime:
    """Return an exact expiration while converting time overflow to ValueError."""

    duration = require_duration(value, field=field, minimum=minimum)
    if unit not in ("seconds", "minutes"):
        raise _duration_error(field, "unit must be seconds or minutes")
    try:
        delta = (
            timedelta(seconds=duration)
            if unit == "seconds"
            else timedelta(minutes=duration)
        )
        return now + delta
    except (OverflowError, TypeError):
        raise _duration_error(field, "is outside the supported datetime range") from None


def deadline_within_grace(
    deadline: datetime,
    now: datetime,
    grace_seconds: object,
) -> bool:
    """Return whether a deadline is live, using overflow-safe grace arithmetic."""

    grace = require_duration(
        grace_seconds,
        field="grace_seconds",
        minimum=0,
    )
    if deadline >= now:
        return True
    elapsed = now - deadline
    grace_days, grace_remainder = divmod(grace, 86_400)
    return elapsed.days < grace_days or (
        elapsed.days == grace_days
        and (elapsed.seconds, elapsed.microseconds) <= (grace_remainder, 0)
    )


@dataclass(frozen=True)
class ClaimLiveness:
    """Pure, bounded interpretation of one task claim's lease authority."""

    state: str
    status: str
    reason: str
    effective_deadline: datetime | None
    deadline_sources: tuple[str, ...]
    findings: tuple[str, ...]


def resolve_claim_grace(
    explicit: object | None = None,
    environ: Mapping[str, str] | None = None,
) -> int:
    """Resolve shared claim grace while preserving the legacy env contract."""

    if explicit is not None:
        return require_duration(
            explicit,
            field="grace_seconds",
            minimum=0,
        )
    source = os.environ if environ is None else environ
    raw = source.get(CLAIM_GRACE_ENV)
    if not raw:
        return DEFAULT_CLAIM_GRACE_SECONDS
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return DEFAULT_CLAIM_GRACE_SECONDS


def _claim_status(value: object) -> str:
    return " ".join(str(value or "").split()).strip().lower()[:96]


def _claim_deadline(
    value: object,
    *,
    source: str,
) -> tuple[datetime | None, str, str]:
    if value is None or value == "":
        return None, "missing", f"{source} is missing"
    if not isinstance(value, str):
        return None, "invalid", f"{source} is invalid: expected an ISO-8601 string"
    text = value.strip()
    if not text:
        return None, "missing", f"{source} is missing"
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None, "invalid", f"{source} is invalid: expected an ISO-8601 timestamp"
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None, "invalid", f"{source} timezone is missing: expected an aware timestamp"
    return parsed, "valid", ""


def classify_claim_liveness(
    claim: Mapping[str, object],
    *,
    now: datetime,
    grace_seconds: object | None = None,
) -> ClaimLiveness:
    """Classify claim authority consistently across all Runtime consumers."""

    grace = resolve_claim_grace(grace_seconds)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise _duration_error("now", "must be a timezone-aware datetime")

    status = _claim_status(claim.get("status"))
    if status in INACTIVE_CLAIM_STATUSES:
        return ClaimLiveness(
            state="inactive",
            status=status,
            reason="status-inactive",
            effective_deadline=None,
            deadline_sources=(),
            findings=(),
        )
    if status not in ACTIVE_CLAIM_STATUSES:
        return ClaimLiveness(
            state="indeterminate",
            status=status,
            reason="status-unknown",
            effective_deadline=None,
            deadline_sources=(),
            findings=("status-unknown: claim status is not canonical",),
        )

    top, top_state, top_finding = _claim_deadline(
        claim.get("expires_at"),
        source="expires_at",
    )
    lease = claim.get("lease")
    if "lease" in claim and not isinstance(lease, Mapping):
        nested = None
        nested_state = "invalid"
        nested_finding = "lease is invalid: expected a mapping with expires_at"
    else:
        nested, nested_state, nested_finding = _claim_deadline(
            lease.get("expires_at") if isinstance(lease, Mapping) else None,
            source="lease.expires_at",
        )

    parts = (
        ("expires_at", top, top_state, top_finding),
        ("lease.expires_at", nested, nested_state, nested_finding),
    )
    valid = tuple((source, deadline) for source, deadline, state, _ in parts if state == "valid")
    findings = tuple(finding for _, _, _, finding in parts if finding)
    effective_deadline = max((deadline for _, deadline in valid), default=None)
    deadline_sources = tuple(source for source, _ in valid)

    states = {state for _, _, state, _ in parts}
    if "invalid" in states:
        return ClaimLiveness(
            state="indeterminate",
            status=status,
            reason="deadline-invalid",
            effective_deadline=effective_deadline,
            deadline_sources=deadline_sources,
            findings=findings,
        )
    if len(valid) != 2:
        reason = "deadline-missing" if not valid else "deadline-partial"
        return ClaimLiveness(
            state="indeterminate",
            status=status,
            reason=reason,
            effective_deadline=effective_deadline,
            deadline_sources=deadline_sources,
            findings=findings,
        )

    assert top is not None and nested is not None and effective_deadline is not None
    if top != nested:
        findings = (
            *findings,
            "deadline-mismatch: expires_at and lease.expires_at differ",
        )
    if deadline_within_grace(effective_deadline, now, grace):
        state, reason = "live", "lease-valid"
    else:
        state, reason = "expired", "lease-expired"
    return ClaimLiveness(
        state=state,
        status=status,
        reason=reason,
        effective_deadline=effective_deadline,
        deadline_sources=deadline_sources,
        findings=findings,
    )


@dataclass(frozen=True)
class PathIdentity:
    exists: bool
    device: int | None = None
    inode: int | None = None
    mode: int | None = None
    size: int | None = None
    mtime_ns: int | None = None
    ctime_ns: int | None = None
    file_attributes: int | None = None
    reparse_tag: int | None = None


@dataclass(frozen=True)
class ClaimStoreSnapshot:
    root: Path
    agents_directory: PathIdentity
    runtime_directory: PathIdentity
    store: PathIdentity
    outer_anchor_directory: PathIdentity
    outer_marker: PathIdentity
    inner_marker: PathIdentity
    entries: tuple[tuple[str, PathIdentity], ...] = ()
    witness_claim_id: str | None = None
    witness: PathIdentity | None = None


@dataclass(frozen=True)
class ClaimStoreInspection:
    state: str
    finding: str | None
    generation_id: str | None
    witness_claim_id: str | None
    snapshot: ClaimStoreSnapshot | None


def _root_path(root: Path | str) -> Path:
    return Path(root).resolve()


def _git_admin(root: Path) -> tuple[Path, bool]:
    marker = root / ".git"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--absolute-git-dir"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        try:
            marker.lstat()
        except FileNotFoundError:
            return root / ".agent-runtime", False
        except OSError as marker_exc:
            raise ClaimStoreError("git administration marker is unavailable") from marker_exc
        raise ClaimStoreError("git administration directory is unavailable") from exc
    if result.returncode != 0:
        try:
            marker.lstat()
        except FileNotFoundError:
            return root / ".agent-runtime", False
        except OSError as exc:
            raise ClaimStoreError("git administration marker is unavailable") from exc
        raise ClaimStoreError("git administration directory is invalid")
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise ClaimStoreError("git administration directory response is invalid")
    admin = Path(lines[0])
    if not admin.is_absolute():
        raise ClaimStoreError("git administration directory is not absolute")
    return admin.resolve(), True


def checkout_git_admin_dir(root: Path | str) -> Path:
    """Return this checkout's absolute Git admin dir or its non-Git fallback."""

    return _git_admin(_root_path(root))[0]


def outer_marker_path(root: Path | str) -> Path:
    base, is_git = _git_admin(_root_path(root))
    if is_git:
        return base / "agent-runtime" / "task-claim-store"
    return base / "task-claim-store"


def _lock_path(root: Path) -> Path:
    marker = outer_marker_path(root)
    return marker.with_name(marker.name + ".lock")


def _is_alias(metadata: os.stat_result) -> bool:
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = int(getattr(metadata, "st_file_attributes", 0) or 0)
    tag = int(getattr(metadata, "st_reparse_tag", 0) or 0)
    return bool(attributes & _WINDOWS_REPARSE_POINT) or bool(tag)


def _metadata_int(metadata: object, name: str, default: int = 0) -> int:
    try:
        return int(getattr(metadata, name, default) or 0)
    except (TypeError, ValueError):
        return default


def _metadata_time_ns(metadata: object, ns_name: str, seconds_name: str) -> int:
    nanoseconds = getattr(metadata, ns_name, None)
    if nanoseconds is not None:
        return _metadata_int(metadata, ns_name)
    try:
        return int(float(getattr(metadata, seconds_name, 0.0) or 0.0) * 1e9)
    except (TypeError, ValueError):
        return 0


def _identity_from_metadata(metadata: object) -> PathIdentity:
    return PathIdentity(
        True,
        _metadata_int(metadata, "st_dev"),
        _metadata_int(metadata, "st_ino"),
        _metadata_int(metadata, "st_mode"),
        _metadata_int(metadata, "st_size"),
        _metadata_time_ns(metadata, "st_mtime_ns", "st_mtime"),
        _metadata_time_ns(metadata, "st_ctime_ns", "st_ctime"),
        _metadata_int(metadata, "st_file_attributes"),
        _metadata_int(metadata, "st_reparse_tag"),
    )


def _path_identity(path: Path) -> PathIdentity:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return PathIdentity(False)
    except (OSError, RuntimeError) as exc:
        raise ClaimStoreError("claim-store path metadata is unavailable") from exc
    return _identity_from_metadata(metadata)


def _identity_is_alias(identity: PathIdentity) -> bool:
    return bool(
        identity.exists
        and (
            identity.mode is not None
            and stat.S_ISLNK(identity.mode)
            or int(identity.file_attributes or 0) & _WINDOWS_REPARSE_POINT
            or int(identity.reparse_tag or 0)
        )
    )


def _require_direct(path: Path, kind: str, *, missing_ok: bool = False) -> PathIdentity:
    identity = _path_identity(path)
    if not identity.exists:
        if missing_ok:
            return identity
        raise ClaimStoreError(f"claim-store {kind} is missing")
    assert identity.mode is not None
    metadata = path.lstat()
    if _is_alias(metadata):
        raise ClaimStoreError(f"claim-store {kind} alias is invalid")
    if kind.endswith("directory") and not stat.S_ISDIR(identity.mode):
        raise ClaimStoreError(f"claim-store {kind} is not a directory")
    if kind.endswith("marker") or kind.endswith("witness"):
        if not stat.S_ISREG(identity.mode):
            raise ClaimStoreError(f"claim-store {kind} is not a regular file")
    return identity


def _bounded_bytes(path: Path, limit: int, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ClaimStoreError(f"claim-store {label} is unreadable") from exc
    try:
        opened = os.fstat(descriptor)
        lexical = path.lstat()
        if _is_alias(lexical) or not stat.S_ISREG(opened.st_mode):
            raise ClaimStoreError(f"claim-store {label} alias is invalid")
        if (opened.st_dev, opened.st_ino) != (lexical.st_dev, lexical.st_ino):
            raise ClaimStoreError(f"claim-store {label} changed while opening")
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > limit:
            raise ClaimStoreError(f"claim-store {label} size is too large")
        after = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ClaimStoreError(f"claim-store {label} changed while reading")
        return payload
    except OSError as exc:
        raise ClaimStoreError(f"claim-store {label} read failed") from exc
    finally:
        os.close(descriptor)


def _bounded_json_int(value: str) -> int:
    digits = value[1:] if value.startswith("-") else value
    if len(digits) > JSON_MAX_INTEGER_DIGITS:
        raise ValueError("claim-store JSON integer exceeds the bounded digit limit")
    return int(value)


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"non-standard JSON constant is invalid: {value}")


def _bounded_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("claim-store JSON float is non-finite")
    return parsed


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field is invalid: {key}")
        result[key] = value
    return result


def _decode_json(payload: bytes, label: str) -> object:
    try:
        return json.loads(
            payload.decode("utf-8"),
            parse_int=_bounded_json_int,
            parse_float=_bounded_json_float,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ClaimStoreError(f"claim-store {label} JSON is malformed") from exc


def _validate_claim_core_identities(
    payload: dict[str, object],
    *,
    status: str,
) -> None:
    if status in ACTIVE_CLAIM_STATUSES and "task_id" not in payload:
        raise ClaimStoreError("claim-store claim task_id is missing")
    for field in ("task_id", "task_set_id", "agent_instance_id"):
        if field not in payload:
            continue
        value = payload[field]
        # The dispatcher historically writes an exact empty task_set_id for
        # identity-only claims. Keep that one explicit absent-value encoding;
        # every other present core identity must be a bounded canonical string.
        if field == "task_set_id" and value == "":
            continue
        if (
            not isinstance(value, str)
            or not value
            or value != value.strip()
            or len(value) > CLAIM_IDENTITY_MAX_CHARS
        ):
            raise ClaimStoreError(f"claim-store claim {field} is invalid")


def read_claim_payload(path: Path | str) -> dict[str, object]:
    """Read one direct claim with the Runtime's bounded JSON contract."""

    claim_path = Path(path)
    parsed = _decode_json(
        _bounded_bytes(claim_path, CLAIM_MAX_BYTES, "claim"),
        "claim",
    )
    if not isinstance(parsed, dict):
        raise ClaimStoreError("claim-store claim JSON root is invalid")
    claim_id = parsed.get("claim_id")
    if (
        parsed.get("schema") != WITNESS_SCHEMA
        or not valid_claim_id(claim_id)
        or claim_path.name != f"{claim_id}.json"
    ):
        raise ClaimStoreError("claim-store claim identity is invalid")
    raw_status = parsed.get("status")
    if not isinstance(raw_status, str):
        raise ClaimStoreError("claim-store claim status is invalid")
    status = raw_status.strip().lower()
    if status not in ACTIVE_CLAIM_STATUSES | INACTIVE_CLAIM_STATUSES:
        raise ClaimStoreError("claim-store claim status is unknown")
    _validate_claim_core_identities(parsed, status=status)
    parsed["status"] = status
    return parsed


def valid_claim_id(value: object) -> bool:
    """Return whether *value* is a canonical Runtime claim identifier."""

    return isinstance(value, str) and _CLAIM_ID.fullmatch(value) is not None


def _validate_witness(root: Path, claim_id: str) -> PathIdentity:
    if not valid_claim_id(claim_id):
        raise ClaimStoreError("claim-store witness claim id is invalid")
    path = root / "agents" / "runtime" / "task_claims" / f"{claim_id}.json"
    identity = _require_direct(path, "witness")
    parsed = read_claim_payload(path)
    if parsed.get("claim_id") != claim_id:
        raise ClaimStoreError("claim-store witness identity is invalid")
    return identity


def _parse_marker(payload: bytes) -> tuple[str, str]:
    parsed = _decode_json(payload, "marker")
    if not isinstance(parsed, dict) or set(parsed) != {
        "schema",
        "generation_id",
        "witness_claim_id",
    }:
        raise ClaimStoreError("claim-store marker schema is invalid")
    if parsed.get("schema") != MARKER_SCHEMA:
        raise ClaimStoreError("claim-store marker schema is invalid")
    generation = parsed.get("generation_id")
    witness = parsed.get("witness_claim_id")
    if not isinstance(generation, str) or not valid_claim_id(witness):
        raise ClaimStoreError("claim-store marker fields are invalid")
    try:
        parsed_uuid = uuid.UUID(generation)
    except (ValueError, AttributeError) as exc:
        raise ClaimStoreError("claim-store marker generation is invalid") from exc
    if parsed_uuid.version != 4 or str(parsed_uuid) != generation:
        raise ClaimStoreError("claim-store marker generation is invalid")
    return generation, witness


def _direct_entry_identities(
    store: Path,
    store_identity: PathIdentity,
) -> tuple[tuple[str, PathIdentity], ...]:
    if (
        not store_identity.exists
        or store_identity.mode is None
        or _identity_is_alias(store_identity)
        or not stat.S_ISDIR(store_identity.mode)
    ):
        return ()
    items: list[tuple[str, PathIdentity]] = []
    try:
        with os.scandir(store) as entries:
            for entry in entries:
                if len(items) >= MAX_STORE_ENTRIES:
                    raise ClaimStoreError(
                        "claim-store entry count exceeds the bounded limit"
                    )
                items.append((entry.name, _path_identity(store / entry.name)))
    except ClaimStoreError:
        raise
    except (OSError, RuntimeError) as exc:
        raise ClaimStoreError("claim-store entry snapshot is unavailable") from exc
    return tuple(sorted(items, key=lambda item: item[0]))


def _snapshot(root: Path, witness_claim_id: str | None = None) -> ClaimStoreSnapshot:
    store = root / "agents" / "runtime" / "task_claims"
    inner = store / ".claim-store"
    outer = outer_marker_path(root)
    agents_identity = _path_identity(root / "agents")
    runtime_identity = _path_identity(root / "agents" / "runtime")
    store_identity = _path_identity(store)
    outer_anchor_identity = _path_identity(outer.parent)
    outer_identity = _path_identity(outer)
    inner_identity = _path_identity(inner)
    witness_path = (
        store / f"{witness_claim_id}.json" if witness_claim_id is not None else None
    )
    return ClaimStoreSnapshot(
        root,
        agents_identity,
        runtime_identity,
        store_identity,
        outer_anchor_identity,
        outer_identity,
        inner_identity,
        _direct_entry_identities(store, store_identity),
        witness_claim_id,
        _path_identity(witness_path) if witness_path is not None else None,
    )


def _validate_snapshot_identity(
    path: Path,
    identity: PathIdentity,
    kind: str,
    *,
    directory: bool = False,
    regular: bool = False,
) -> None:
    if identity.exists:
        if identity.mode is None or _identity_is_alias(identity):
            raise ClaimStoreError(f"claim-store {kind} alias is invalid")
        if directory and not stat.S_ISDIR(identity.mode):
            raise ClaimStoreError(f"claim-store {kind} is not a directory")
        if regular and not stat.S_ISREG(identity.mode):
            raise ClaimStoreError(f"claim-store {kind} is not a regular file")
    observed = _require_direct(path, kind, missing_ok=True)
    if observed != identity:
        raise ClaimStoreError(f"claim-store {kind} changed during snapshot validation")


def _validated_snapshot(
    root: Path,
    witness_claim_id: str | None = None,
) -> ClaimStoreSnapshot:
    snapshot = _snapshot(root, witness_claim_id)
    store = root / "agents" / "runtime" / "task_claims"
    inner = store / ".claim-store"
    outer = outer_marker_path(root)
    _validate_snapshot_identity(
        root / "agents",
        snapshot.agents_directory,
        "agents directory",
        directory=True,
    )
    _validate_snapshot_identity(
        root / "agents" / "runtime",
        snapshot.runtime_directory,
        "runtime directory",
        directory=True,
    )
    _validate_snapshot_identity(
        store,
        snapshot.store,
        "store directory",
        directory=True,
    )
    _validate_snapshot_identity(
        outer.parent,
        snapshot.outer_anchor_directory,
        "anchor directory",
        directory=True,
    )
    _validate_snapshot_identity(
        outer,
        snapshot.outer_marker,
        "outer marker",
        regular=True,
    )
    _validate_snapshot_identity(
        inner,
        snapshot.inner_marker,
        "inner marker",
        regular=True,
    )
    if snapshot.runtime_directory.exists and not snapshot.agents_directory.exists:
        raise ClaimStoreError("claim-store runtime directory has no agents directory")
    if snapshot.store.exists and not snapshot.runtime_directory.exists:
        raise ClaimStoreError("claim-store store directory has no runtime directory")
    if snapshot.inner_marker.exists and not snapshot.store.exists:
        raise ClaimStoreError("claim-store inner marker has no store directory")
    if snapshot.outer_marker.exists and not snapshot.outer_anchor_directory.exists:
        raise ClaimStoreError("claim-store outer marker has no anchor directory")
    entries = dict(snapshot.entries)
    if not snapshot.store.exists and entries:
        raise ClaimStoreError("claim-store entries have no store directory")
    if entries.get(".claim-store", PathIdentity(False)) != snapshot.inner_marker:
        raise ClaimStoreError("claim-store inner marker entry snapshot is inconsistent")
    if witness_claim_id is not None:
        witness_path = store / f"{witness_claim_id}.json"
        witness = snapshot.witness or PathIdentity(False)
        _validate_snapshot_identity(
            witness_path,
            witness,
            "witness",
            regular=True,
        )
        if entries.get(witness_path.name, PathIdentity(False)) != witness:
            raise ClaimStoreError("claim-store witness entry snapshot is inconsistent")
    final_snapshot = _snapshot(root, witness_claim_id)
    if final_snapshot != snapshot:
        raise ClaimStoreError("claim-store changed during final snapshot validation")
    return snapshot


def _bounded_finding(detail: str) -> str:
    return " ".join(detail.split())[:256]


def _invalid(detail: str) -> ClaimStoreInspection:
    return ClaimStoreInspection(
        "integrity-invalid",
        _bounded_finding(f"claim-store-integrity-invalid: {detail}"),
        None,
        None,
        None,
    )


def _same_authority_snapshot(
    before: ClaimStoreSnapshot,
    after: ClaimStoreSnapshot,
) -> bool:
    return (
        before.root == after.root
        and before.agents_directory == after.agents_directory
        and before.runtime_directory == after.runtime_directory
        and before.store == after.store
        and before.outer_anchor_directory == after.outer_anchor_directory
        and before.outer_marker == after.outer_marker
        and before.inner_marker == after.inner_marker
        and before.entries == after.entries
    )


def inspect_store(root: Path | str) -> ClaimStoreInspection:
    root_path = _root_path(root)
    store = root_path / "agents" / "runtime" / "task_claims"
    inner = store / ".claim-store"
    try:
        outer = outer_marker_path(root_path)
        before = _validated_snapshot(root_path)
        if before.outer_marker.exists and not before.inner_marker.exists:
            return _invalid("claim-store marker pair is one-sided")
        if before.inner_marker.exists and not before.outer_marker.exists:
            if not before.store.exists:
                return _invalid("claim-store initialized inner marker has no store")
            inner_bytes = _bounded_bytes(inner, MARKER_MAX_BYTES, "inner marker")
            generation, witness_claim_id = _parse_marker(inner_bytes)
            witness_identity = _validate_witness(root_path, witness_claim_id)
            after = _validated_snapshot(root_path, witness_claim_id)
            if (
                not _same_authority_snapshot(before, after)
                or after.witness != witness_identity
            ):
                return _invalid(
                    "claim-store snapshot changed or was replaced during inspection"
                )
            return ClaimStoreInspection(
                "migration-required",
                "claim-store checkout activation is required for an initialized inner marker",
                generation,
                witness_claim_id,
                after,
            )
        if not before.outer_marker.exists:
            if not before.store.exists or not before.entries:
                after = _validated_snapshot(root_path)
                if before != after:
                    return _invalid("claim-store snapshot changed during inspection")
                return ClaimStoreInspection("pristine", None, None, None, after)
            after = _validated_snapshot(root_path)
            if before != after:
                return _invalid("claim-store snapshot changed during inspection")
            return ClaimStoreInspection(
                "migration-required",
                "claim-store migration is required for a markerless populated store",
                None,
                None,
                after,
            )
        if not before.store.exists:
            return _invalid("claim-store initialized marker has no store")
        outer_bytes = _bounded_bytes(outer, MARKER_MAX_BYTES, "outer marker")
        inner_bytes = _bounded_bytes(inner, MARKER_MAX_BYTES, "inner marker")
        if outer_bytes != inner_bytes:
            return _invalid("claim-store marker mismatch")
        generation, witness_claim_id = _parse_marker(outer_bytes)
        witness_identity = _validate_witness(root_path, witness_claim_id)
        after = _validated_snapshot(root_path, witness_claim_id)
        if (
            not _same_authority_snapshot(before, after)
            or after.witness != witness_identity
        ):
            return _invalid("claim-store snapshot changed or was replaced during inspection")
        return ClaimStoreInspection(
            "initialized",
            None,
            generation,
            witness_claim_id,
            after,
        )
    except ClaimStoreError as exc:
        return _invalid(str(exc))
    except (OSError, RuntimeError, ValueError) as exc:
        return _invalid(f"claim-store inspection failed: {type(exc).__name__}")


def verify_snapshot(root: Path | str, snapshot: ClaimStoreSnapshot | None) -> bool:
    if not isinstance(snapshot, ClaimStoreSnapshot):
        return False
    root_path = _root_path(root)
    if root_path != snapshot.root:
        return False
    try:
        return _validated_snapshot(root_path, snapshot.witness_claim_id) == snapshot
    except (ClaimStoreError, OSError, RuntimeError, ValueError):
        return False


def read_claims_snapshot(root: Path | str) -> tuple[dict[str, object], ...]:
    """Read every canonical claim from one locked, verified store snapshot."""

    root_path = _root_path(root)
    with store_lock(root_path):
        inspection = inspect_store(root_path)
        if inspection.state not in {"initialized", "pristine"}:
            raise ClaimStoreError(
                inspection.finding or "claim-store authority is unavailable"
            )
        snapshot = inspection.snapshot
        if snapshot is None:
            raise ClaimStoreError("claim-store snapshot is unavailable")
        claims: list[dict[str, object]] = []
        store = root_path / "agents" / "runtime" / "task_claims"
        for name, identity in snapshot.entries:
            if not (name.startswith("CLAIM-") and name.endswith(".json")):
                continue
            if (
                not identity.exists
                or identity.mode is None
                or _identity_is_alias(identity)
                or not stat.S_ISREG(identity.mode)
            ):
                raise ClaimStoreError("claim-store claim entry is invalid")
            claims.append(read_claim_payload(store / name))
        if not verify_snapshot(root_path, snapshot):
            raise ClaimStoreError("claim-store changed while reading claims")
        return tuple(claims)


def _canonical_marker(witness_claim_id: str) -> bytes:
    payload = {
        "schema": MARKER_SCHEMA,
        "generation_id": str(uuid.uuid4()),
        "witness_claim_id": witness_claim_id,
    }
    encoded = (
        json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")
    if len(encoded) > MARKER_MAX_BYTES:
        raise ClaimStoreError("claim-store marker size is too large")
    return encoded


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _remove_created_marker(
    path: Path,
    identity: PathIdentity,
    payload: bytes,
) -> bool:
    try:
        current = _path_identity(path)
        if not current.exists:
            return True
        if current != identity or _bounded_bytes(path, MARKER_MAX_BYTES, "marker") != payload:
            return False
        path.unlink()
        _fsync_directory(path.parent)
        return True
    except (ClaimStoreError, OSError, RuntimeError):
        return False


def _rollback_created_markers(
    created: list[tuple[Path, PathIdentity, bytes]],
) -> bool:
    complete = True
    for path, identity, payload in reversed(created):
        complete = _remove_created_marker(path, identity, payload) and complete
    return complete


def _remove_created_file_object(path: Path, opened: PathIdentity) -> bool:
    try:
        current = _path_identity(path)
        if not current.exists:
            return True
        if (
            _identity_is_alias(current)
            or current.mode is None
            or not stat.S_ISREG(current.mode)
            or current.device != opened.device
            or current.inode != opened.inode
            or current.mode != opened.mode
            or current.file_attributes != opened.file_attributes
            or current.reparse_tag != opened.reparse_tag
        ):
            return False
        path.unlink()
        try:
            _fsync_directory(path.parent)
        except OSError:
            pass
        return True
    except (ClaimStoreError, OSError, RuntimeError):
        return False


def _write_immutable(path: Path, payload: bytes) -> PathIdentity:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise ClaimStoreError("claim-store marker already exists or is unavailable") from exc
    try:
        opened_identity = _identity_from_metadata(os.fstat(descriptor))
    except OSError as exc:
        os.close(descriptor)
        raise ClaimStoreError(
            "claim-store marker identity is unavailable after creation"
        ) from exc
    write_error: BaseException | None = None
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short marker write")
            view = view[written:]
        os.fsync(descriptor)
    except BaseException as exc:
        write_error = exc
    try:
        os.close(descriptor)
    except OSError as exc:
        if write_error is None:
            write_error = exc
    if write_error is not None:
        if not _remove_created_file_object(path, opened_identity):
            raise ClaimStoreError(
                "claim-store marker write failed and rollback was incomplete"
            ) from write_error
        if isinstance(write_error, ClaimStoreError):
            raise write_error
        if isinstance(write_error, OSError):
            raise ClaimStoreError("claim-store marker write failed") from write_error
        raise write_error
    try:
        _fsync_directory(path.parent)
        identity = _require_direct(path, "marker")
        matches = _bounded_bytes(path, MARKER_MAX_BYTES, "marker") == payload
    except BaseException as exc:
        if not _remove_created_file_object(path, opened_identity):
            raise ClaimStoreError(
                "claim-store marker validation failed and rollback was incomplete"
            ) from exc
        if isinstance(exc, ClaimStoreError):
            raise
        if isinstance(exc, OSError):
            raise ClaimStoreError("claim-store marker validation failed") from exc
        raise
    if not matches:
        if not _remove_created_file_object(path, opened_identity):
            raise ClaimStoreError(
                "claim-store marker changed after writing and rollback was incomplete"
            )
        raise ClaimStoreError("claim-store marker changed after writing")
    return identity


def _ensure_direct_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ClaimStoreError("claim-store marker directory is unavailable") from exc
    _require_direct(path, "marker directory")


def _authority_entries(
    snapshot: ClaimStoreSnapshot,
) -> tuple[tuple[str, PathIdentity], ...]:
    return tuple(item for item in snapshot.entries if item[0] != ".claim-store")


def _same_path_object(before: PathIdentity, after: PathIdentity) -> bool:
    return (
        before.exists == after.exists
        and before.device == after.device
        and before.inode == after.inode
        and before.mode == after.mode
        and before.file_attributes == after.file_attributes
        and before.reparse_tag == after.reparse_tag
        and (os.name != "nt" or before.ctime_ns == after.ctime_ns)
    )


def _same_store_continuity(
    before: ClaimStoreSnapshot,
    after: ClaimStoreSnapshot,
    *,
    compare_outer_anchor: bool = True,
) -> bool:
    return (
        before.root == after.root
        and _same_path_object(before.agents_directory, after.agents_directory)
        and _same_path_object(before.runtime_directory, after.runtime_directory)
        and _same_path_object(before.store, after.store)
        and (
            not compare_outer_anchor
            or _same_path_object(
                before.outer_anchor_directory,
                after.outer_anchor_directory,
            )
        )
        and _authority_entries(before) == _authority_entries(after)
    )


def _transaction_snapshot(root: Path, witness_claim_id: str) -> ClaimStoreSnapshot:
    before = _validated_snapshot(root, witness_claim_id)
    witness_identity = _validate_witness(root, witness_claim_id)
    after = _validated_snapshot(root, witness_claim_id)
    if before != after or after.witness != witness_identity:
        raise ClaimStoreError("claim-store changed during transaction snapshot")
    return after


def _require_transaction_continuity(
    baseline: ClaimStoreSnapshot,
    current: ClaimStoreSnapshot,
    *,
    inner_marker: PathIdentity,
    outer_marker: PathIdentity,
) -> None:
    if (
        not _same_store_continuity(baseline, current)
        or baseline.witness_claim_id != current.witness_claim_id
        or baseline.witness != current.witness
        or current.inner_marker != inner_marker
        or current.outer_marker != outer_marker
    ):
        raise ClaimStoreError("claim-store authority continuity changed during marker transaction")


def _establish(root: Path, witness_claim_id: str) -> ClaimStoreInspection:
    inspection = inspect_store(root)
    if inspection.state == "initialized":
        if inspection.witness_claim_id == witness_claim_id:
            return inspection
        raise ClaimStoreError("claim-store marker cannot be rebound")
    if inspection.state == "migration-required" and inspection.generation_id:
        raise ClaimStoreError(
            "claim-store checkout activation requires explicit legacy adoption"
        )
    if inspection.state != "migration-required":
        raise ClaimStoreError(
            inspection.finding or "claim-store is not safe to initialize"
        )
    outer = outer_marker_path(root)
    inner = root / "agents" / "runtime" / "task_claims" / ".claim-store"
    _ensure_direct_directory(inner.parent)
    _ensure_direct_directory(outer.parent)
    baseline = _transaction_snapshot(root, witness_claim_id)
    if (
        inspection.snapshot is None
        or not _same_store_continuity(
            inspection.snapshot,
            baseline,
            compare_outer_anchor=False,
        )
        or baseline.inner_marker.exists
        or baseline.outer_marker.exists
    ):
        raise ClaimStoreError("claim-store changed before marker transaction")
    payload = _canonical_marker(witness_claim_id)
    missing = PathIdentity(False)
    created: list[tuple[Path, PathIdentity, bytes]] = []
    try:
        before_inner = _transaction_snapshot(root, witness_claim_id)
        _require_transaction_continuity(
            baseline,
            before_inner,
            inner_marker=missing,
            outer_marker=missing,
        )
        inner_identity = _write_immutable(inner, payload)
        created.append((inner, inner_identity, payload))
        after_inner = _transaction_snapshot(root, witness_claim_id)
        _require_transaction_continuity(
            baseline,
            after_inner,
            inner_marker=inner_identity,
            outer_marker=missing,
        )
        before_outer = _transaction_snapshot(root, witness_claim_id)
        _require_transaction_continuity(
            baseline,
            before_outer,
            inner_marker=inner_identity,
            outer_marker=missing,
        )
        outer_identity = _write_immutable(outer, payload)
        created.append((outer, outer_identity, payload))
        after_outer = _transaction_snapshot(root, witness_claim_id)
        _require_transaction_continuity(
            baseline,
            after_outer,
            inner_marker=inner_identity,
            outer_marker=outer_identity,
        )
        result = inspect_store(root)
        if (
            result.state != "initialized"
            or result.snapshot is None
            or not _same_store_continuity(baseline, result.snapshot)
            or result.snapshot.witness != baseline.witness
            or result.snapshot.inner_marker != inner_identity
            or result.snapshot.outer_marker != outer_identity
        ):
            raise ClaimStoreError(result.finding or "claim-store initialization failed")
        return result
    except BaseException as exc:
        if not _rollback_created_markers(created):
            raise ClaimStoreError("claim-store marker rollback was incomplete") from exc
        raise


def initialize_store(
    root: Path | str,
    *,
    witness_claim_id: str,
) -> ClaimStoreInspection:
    root_path = _root_path(root)
    with store_lock(root_path):
        return _establish(root_path, witness_claim_id)


def _adoption_candidates(root: Path) -> list[str]:
    store = root / "agents" / "runtime" / "task_claims"
    names: list[str] = []
    try:
        with os.scandir(store) as entries:
            for entry in entries:
                if len(names) >= MAX_STORE_ENTRIES:
                    raise ClaimStoreError(
                        "claim-store adoption entry count exceeds the bounded limit"
                    )
                names.append(entry.name)
    except ClaimStoreError:
        raise
    except (OSError, RuntimeError) as exc:
        raise ClaimStoreError("claim-store adoption enumeration is unavailable") from exc
    return sorted(
        name[:-5]
        for name in names
        if name.endswith(".json") and valid_claim_id(name[:-5])
    )


def _activate_checkout(
    root: Path,
    inspection: ClaimStoreInspection,
    witness_claim_id: str | None,
) -> ClaimStoreInspection:
    expected_witness = inspection.witness_claim_id
    expected_generation = inspection.generation_id
    if expected_witness is None or expected_generation is None:
        raise ClaimStoreError("claim-store checkout activation metadata is unavailable")
    if witness_claim_id is not None and witness_claim_id != expected_witness:
        raise ClaimStoreError("claim-store marker cannot be rebound")
    if not verify_snapshot(root, inspection.snapshot):
        raise ClaimStoreError("claim-store changed before checkout activation")

    inner = root / "agents" / "runtime" / "task_claims" / ".claim-store"
    outer = outer_marker_path(root)
    payload = _bounded_bytes(inner, MARKER_MAX_BYTES, "inner marker")
    generation, retained_witness = _parse_marker(payload)
    if generation != expected_generation or retained_witness != expected_witness:
        raise ClaimStoreError("claim-store inner marker changed before activation")
    _validate_witness(root, retained_witness)
    if not verify_snapshot(root, inspection.snapshot):
        raise ClaimStoreError("claim-store changed before checkout activation")

    _ensure_direct_directory(outer.parent)
    baseline = _transaction_snapshot(root, retained_witness)
    if (
        inspection.snapshot is None
        or not _same_store_continuity(
            inspection.snapshot,
            baseline,
            compare_outer_anchor=False,
        )
        or baseline.inner_marker != inspection.snapshot.inner_marker
        or baseline.outer_marker.exists
    ):
        raise ClaimStoreError("claim-store changed before checkout activation")
    created: list[tuple[Path, PathIdentity, bytes]] = []
    try:
        before_outer = _transaction_snapshot(root, retained_witness)
        _require_transaction_continuity(
            baseline,
            before_outer,
            inner_marker=baseline.inner_marker,
            outer_marker=PathIdentity(False),
        )
        outer_identity = _write_immutable(outer, payload)
        created.append((outer, outer_identity, payload))
        after_outer = _transaction_snapshot(root, retained_witness)
        _require_transaction_continuity(
            baseline,
            after_outer,
            inner_marker=baseline.inner_marker,
            outer_marker=outer_identity,
        )
        result = inspect_store(root)
        if (
            result.state != "initialized"
            or result.snapshot is None
            or not _same_store_continuity(baseline, result.snapshot)
            or result.snapshot.witness != baseline.witness
            or result.snapshot.inner_marker != baseline.inner_marker
            or result.snapshot.outer_marker != outer_identity
        ):
            raise ClaimStoreError(
                result.finding or "claim-store checkout activation failed"
            )
        return result
    except BaseException as exc:
        if not _rollback_created_markers(created):
            raise ClaimStoreError("claim-store marker rollback was incomplete") from exc
        raise


def adopt_legacy_store(
    root: Path | str,
    witness_claim_id: str | None = None,
) -> ClaimStoreInspection:
    root_path = _root_path(root)
    with store_lock(root_path):
        current = inspect_store(root_path)
        if current.state == "initialized":
            if witness_claim_id is None or current.witness_claim_id == witness_claim_id:
                return current
            raise ClaimStoreError("claim-store marker cannot be rebound")
        if current.state != "migration-required":
            raise ClaimStoreError(current.finding or "claim-store adoption is unsafe")
        if current.generation_id is not None:
            return _activate_checkout(root_path, current, witness_claim_id)
        selected = witness_claim_id
        if selected is None:
            for candidate in _adoption_candidates(root_path):
                try:
                    _validate_witness(root_path, candidate)
                except ClaimStoreError:
                    continue
                selected = candidate
                break
        if selected is None:
            raise ClaimStoreError("claim-store adoption has no safe witness")
        return _establish(root_path, selected)


_THREAD_LOCKS: dict[str, threading.RLock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()
_LOCAL = threading.local()


def _thread_lock(key: str) -> threading.RLock:
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, threading.RLock())


def _try_kernel_lock(descriptor: int) -> bool:
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True
    import fcntl

    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock_kernel(descriptor: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_UN)


def _validate_lock_file_identity(path: Path, descriptor: int) -> os.stat_result:
    opened = os.fstat(descriptor)
    lexical = path.lstat()
    if (
        _is_alias(lexical)
        or not stat.S_ISREG(lexical.st_mode)
        or not stat.S_ISREG(opened.st_mode)
    ):
        raise ClaimStoreError("claim-store lock file alias is invalid")
    if (opened.st_dev, opened.st_ino) != (lexical.st_dev, lexical.st_ino):
        raise ClaimStoreError("claim-store lock file changed while opening")
    return opened


@contextlib.contextmanager
def store_lock(
    root: Path | str,
    *,
    timeout_seconds: float = LOCK_TIMEOUT_SECONDS,
) -> Iterator[None]:
    root_path = _root_path(root)
    if timeout_seconds < 0:
        raise ClaimStoreError("claim-store lock timeout is invalid")
    path = _lock_path(root_path)
    key = os.path.normcase(str(path.resolve(strict=False)))
    held = getattr(_LOCAL, "held", None)
    if held is None:
        held = {}
        _LOCAL.held = held
    if key in held:
        held[key] += 1
        try:
            yield
        finally:
            held[key] -= 1
        return
    deadline = time.monotonic() + timeout_seconds
    process_lock = _thread_lock(key)
    if not process_lock.acquire(timeout=max(0.0, timeout_seconds)):
        raise ClaimStoreLockTimeout("claim-store lock timeout")
    descriptor: int | None = None
    acquired = False
    try:
        _ensure_direct_directory(path.parent)
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(path, flags, 0o600)
            opened = _validate_lock_file_identity(path, descriptor)
            if opened.st_size == 0:
                os.write(descriptor, b"\0")
                os.fsync(descriptor)
        except ClaimStoreError:
            raise
        except OSError as exc:
            raise ClaimStoreError("claim-store lock file is unavailable") from exc
        while True:
            if _try_kernel_lock(descriptor):
                acquired = True
                _validate_lock_file_identity(path, descriptor)
                break
            if time.monotonic() >= deadline:
                raise ClaimStoreLockTimeout("claim-store lock timeout")
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
        held[key] = 1
        try:
            yield
        finally:
            held.pop(key, None)
    finally:
        if acquired and descriptor is not None:
            try:
                _unlock_kernel(descriptor)
            except OSError:
                pass
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                # The descriptor has already protected the complete caller
                # transaction. A close error cannot reverse durable truth.
                pass
        process_lock.release()
