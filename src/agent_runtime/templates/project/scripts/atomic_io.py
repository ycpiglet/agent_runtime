"""Fail-closed, power-loss-safe atomic file writes shared across runtime scripts.

Why this exists: several scripts independently re-implemented a "write a temp file
then ``os.replace`` it" helper, but (a) the logic was duplicated and (b) none of
them called ``fsync`` — so a hard power loss between the buffered write and the
rename could leave a *stale* or *zero-length* target even though ``os.replace`` is
atomic w.r.t. the directory entry. Centralizing here gives every call-site the same
durable primitive: temp file -> flush -> fsync -> atomic rename.

Temporary files are created relative to a verified direct parent directory with
the operating system's exclusive-create primitive and an unpredictable suffix.
Concurrent writers therefore never share a sidecar, and a pre-created symlink
cannot redirect a write outside the target directory.

On POSIX, the default authority boundary is the filesystem root: every lexical
parent component must be alias-free and openable as a directory handle.

``write_*_atomic`` deliberately retains its historical overwrite/last-writer-wins
contract. ``publish_*_atomic`` is the no-clobber counterpart: it atomically
publishes a new file and raises ``FileExistsError`` if any destination entry wins
the race first.
"""

from __future__ import annotations

import errno
import json
import os
import secrets
import stat
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, NamedTuple


_WINDOWS_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400)
_TEMP_ATTEMPTS = 128
# Windows has no overwrite-atomic rename. MoveFileEx fails with
# ERROR_ACCESS_DENIED / ERROR_SHARING_VIOLATION / ERROR_LOCK_VIOLATION while any
# other handle to the destination is open - which every concurrent publisher
# holds for the microseconds between open and close. POSIX rename simply cannot
# fail that way, so the overwrite guarantee this module sells is only real on
# Windows if the transient collision is waited out instead of surfaced. Bounded,
# so a genuine ACL denial still propagates rather than spinning.
_WINDOWS_REPLACE_TRANSIENT_WINERRORS = frozenset({5, 32, 33})
_WINDOWS_REPLACE_DEADLINE_SECONDS = 10.0
_WINDOWS_REPLACE_BACKOFF_SECONDS = 0.001
_WINDOWS_REPLACE_BACKOFF_CEILING_SECONDS = 0.05


class UnsafePathError(OSError):
    """Raised when a target parent is an alias or is not a directory."""


class AtomicWriteError(RuntimeError):
    """Report the exact durability boundary at which an atomic write failed.

    ``committed`` says whether the destination mutation already happened;
    ``retry_safe`` says whether repeating the complete operation is safe.  The
    originating ``OSError`` is retained as ``__cause__`` by the raising site.
    """

    def __init__(
        self,
        message: str,
        *,
        stage: str,
        committed: bool,
        retry_safe: bool,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.committed = committed
        self.retry_safe = retry_safe


class PublishedFileIdentity(NamedTuple):
    """Identity of the opened regular file used for exclusive publication.

    The token is captured with ``fstat`` while the sidecar is still open and
    before its link/rename commit point. Transaction callers can therefore
    register rollback ownership without a fallible post-commit path read.
    """

    device: int
    inode: int
    mode: int
    size: int
    file_attributes: int
    reparse_tag: int


class CreatedDirectoryIdentity(NamedTuple):
    """Identity of a parent directory created by the active atomic operation."""

    path: Path
    device: int
    inode: int


class _CleanupPathIdentity(NamedTuple):
    """Callback-bound identity for one direct lexical path component."""

    path: Path
    device: int
    inode: int
    stat_generation: int
    mode: int
    size: int
    change_time_ns: int
    modification_time_ns: int
    birth_time_ns: int
    link_count: int
    file_attributes: int
    reparse_tag: int


class _RejectedCleanupProof(NamedTuple):
    """Exact sidecar and parent chain observed immediately before authority."""

    path: Path
    sidecar_name: str
    parent_chain: tuple[_CleanupPathIdentity, ...]
    sidecar: _CleanupPathIdentity


class _RollbackAuthority(NamedTuple):
    """Fresh chain identity granting one best-effort created-parent rollback."""

    parent_chain: tuple[_CleanupPathIdentity, ...]


class _ExclusivePrecommitState:
    """Track pending, capture-failed, armed, rejected, or accepted cleanup."""

    __slots__ = ("callback", "phase", "proof")

    def __init__(self, callback: Callable[[], None]) -> None:
        self.callback = callback
        self.phase = "pending"
        self.proof: _RejectedCleanupProof | None = None


def _stat_is_path_alias(metadata: Any) -> bool:
    """Return whether an lstat result is a symlink or Windows reparse point."""
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _WINDOWS_REPARSE_POINT
    )


def _unsafe_parent(path: Path, detail: str) -> UnsafePathError:
    return UnsafePathError(errno.ELOOP, f"unsafe target parent {path}: {detail}", str(path))


def _validate_parent_metadata(path: Path, metadata: Any) -> None:
    if _stat_is_path_alias(metadata):
        raise _unsafe_parent(path, "symlink/reparse alias is not a direct directory")
    if not stat.S_ISDIR(metadata.st_mode):
        raise NotADirectoryError(
            errno.ENOTDIR,
            f"target parent component is not a directory: {path}",
            str(path),
        )


def _absolute_lexical(path: Path) -> Path:
    """Make a path absolute without resolving filesystem aliases."""
    return Path(os.path.abspath(os.fspath(path)))


def _nearest_existing_parent(parent: Path) -> tuple[Path, list[str]]:
    """Find an existing anchor plus missing descendants for fallback creation."""
    missing: list[str] = []
    cursor = parent
    while True:
        try:
            metadata = cursor.lstat()
        except FileNotFoundError:
            if cursor == cursor.parent:
                raise
            missing.append(cursor.name)
            cursor = cursor.parent
            continue
        _validate_parent_metadata(cursor, metadata)
        return cursor, missing


def _same_file(left: Any, right: Any) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _stat_time_ns(metadata: Any, nanoseconds: str) -> int:
    value = getattr(metadata, nanoseconds, None)
    return -1 if value is None else int(value)


def _cleanup_path_identity(path: Path, metadata: Any) -> _CleanupPathIdentity:
    change_time_ns = _stat_time_ns(metadata, "st_ctime_ns")
    birth_time_ns = _stat_time_ns(
        metadata,
        "st_birthtime_ns",
    )
    if birth_time_ns < 0 and sys.platform == "win32":
        # Before Python 3.12 Windows exposed creation time through st_ctime.
        birth_time_ns = change_time_ns
    return _CleanupPathIdentity(
        path=path,
        device=int(metadata.st_dev),
        inode=int(metadata.st_ino),
        stat_generation=int(getattr(metadata, "st_gen", -1)),
        mode=int(metadata.st_mode),
        size=int(metadata.st_size),
        change_time_ns=change_time_ns,
        modification_time_ns=_stat_time_ns(metadata, "st_mtime_ns"),
        birth_time_ns=birth_time_ns,
        link_count=int(getattr(metadata, "st_nlink", 0) or 0),
        file_attributes=int(getattr(metadata, "st_file_attributes", 0) or 0),
        reparse_tag=int(getattr(metadata, "st_reparse_tag", 0) or 0),
    )


def _same_cleanup_object(
    expected: _CleanupPathIdentity,
    observed: _CleanupPathIdentity,
) -> bool:
    """Compare stable object keys while allowing directory entry mutations."""

    return (
        expected.path == observed.path
        and expected.device == observed.device
        and expected.inode == observed.inode
        and expected.stat_generation == observed.stat_generation
        and expected.mode == observed.mode
        and expected.birth_time_ns == observed.birth_time_ns
        and expected.file_attributes == observed.file_attributes
        and expected.reparse_tag == observed.reparse_tag
    )


def _same_cleanup_identity(
    expected: _CleanupPathIdentity,
    observed: _CleanupPathIdentity,
) -> bool:
    """Compare both stable keys and the callback-bound generation."""

    return _same_cleanup_object(expected, observed) and (
        expected.size == observed.size
        and expected.change_time_ns == observed.change_time_ns
        and expected.modification_time_ns == observed.modification_time_ns
        and expected.link_count == observed.link_count
    )


def _opened_cleanup_identity_matches(
    expected: _CleanupPathIdentity,
    observed: _CleanupPathIdentity,
) -> bool:
    """Bind the opened sidecar to its first post-close path generation.

    Windows may finalize last-write metadata only when the final writing handle
    closes. Its stable creation/object fields and exact size must still match,
    but the first post-close observation becomes the full callback-bound
    generation used thereafter. POSIX has no such normalization boundary and
    retains exact full-generation equality.
    """

    if sys.platform != "win32":
        return _same_cleanup_identity(expected, observed)
    return _same_cleanup_object(expected, observed) and expected.size == observed.size


def _published_file_identity(metadata: Any) -> PublishedFileIdentity:
    return PublishedFileIdentity(
        int(metadata.st_dev),
        int(metadata.st_ino),
        int(metadata.st_mode),
        int(metadata.st_size),
        int(getattr(metadata, "st_file_attributes", 0) or 0),
        int(getattr(metadata, "st_reparse_tag", 0) or 0),
    )


def _published_identity_matches(
    expected: PublishedFileIdentity,
    observed: _CleanupPathIdentity,
) -> bool:
    return (
        expected.device == observed.device
        and expected.inode == observed.inode
        and expected.mode == observed.mode
        and expected.size == observed.size
        and expected.file_attributes == observed.file_attributes
        and expected.reparse_tag == observed.reparse_tag
    )


def _snapshot_directory_chain(parent: Path) -> tuple[_CleanupPathIdentity, ...]:
    """Capture every direct lexical component from the anchor to ``parent``."""

    absolute = _absolute_lexical(parent)
    entries: list[_CleanupPathIdentity] = []
    for candidate in reversed((absolute, *absolute.parents)):
        metadata = candidate.lstat()
        _validate_parent_metadata(candidate, metadata)
        entries.append(_cleanup_path_identity(candidate, metadata))
    return tuple(entries)


def _sidecar_metadata(path: Path, name: str, parent_fd: int | None) -> Any:
    if parent_fd is not None:
        return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    return (path.parent / name).lstat()


def _capture_precommit_cleanup(
    path: Path,
    name: str,
    parent_fd: int | None,
    opened_identity: PublishedFileIdentity,
    opened_cleanup_identity: _CleanupPathIdentity,
) -> _RejectedCleanupProof:
    """Arm rejected-callback cleanup at the final pre-publication boundary."""

    parent_chain = _snapshot_directory_chain(path.parent)
    if parent_fd is not None:
        pinned_parent_metadata = os.fstat(parent_fd)
        _validate_parent_metadata(path.parent, pinned_parent_metadata)
        pinned_parent = _cleanup_path_identity(path.parent, pinned_parent_metadata)
        if not _same_cleanup_identity(parent_chain[-1], pinned_parent):
            raise OSError(
                errno.EIO,
                "lexical and pinned atomic parent identities differ before precommit authority",
                str(path.parent),
            )

    sidecar_path = path.parent / name
    metadata = _sidecar_metadata(path, name, parent_fd)
    if _stat_is_path_alias(metadata) or not stat.S_ISREG(metadata.st_mode):
        raise OSError(
            errno.EIO,
            "atomic sidecar changed before precommit authority",
            str(sidecar_path),
        )
    sidecar = _cleanup_path_identity(sidecar_path, metadata)
    if not _published_identity_matches(
        opened_identity,
        sidecar,
    ) or not _opened_cleanup_identity_matches(opened_cleanup_identity, sidecar):
        raise OSError(
            errno.EIO,
            "atomic sidecar identity changed before precommit authority",
            str(sidecar_path),
        )

    final_parent_chain = _snapshot_directory_chain(path.parent)
    if len(parent_chain) != len(final_parent_chain) or any(
        not _same_cleanup_identity(before, after)
        for before, after in zip(parent_chain, final_parent_chain)
    ):
        raise OSError(
            errno.EIO,
            "atomic parent chain changed before precommit authority",
            str(path.parent),
        )
    if parent_fd is not None and not _same_cleanup_identity(
        pinned_parent,
        final_parent_chain[-1],
    ):
        raise OSError(
            errno.EIO,
            "lexical and pinned atomic parent identities changed before precommit authority",
            str(path.parent),
        )
    return _RejectedCleanupProof(path, name, final_parent_chain, sidecar)


def _run_exclusive_precommit(
    state: _ExclusivePrecommitState,
    path: Path,
    name: str,
    parent_fd: int | None,
    opened_identity: PublishedFileIdentity,
    opened_cleanup_identity: _CleanupPathIdentity,
) -> None:
    try:
        state.proof = _capture_precommit_cleanup(
            path,
            name,
            parent_fd,
            opened_identity,
            opened_cleanup_identity,
        )
    except BaseException:
        state.phase = "capture_failed"
        raise
    state.phase = "armed"
    try:
        state.callback()
    except BaseException:
        state.phase = "rejected"
        raise
    state.phase = "accepted"


def _observe_cleanup_chain(
    expected: tuple[_CleanupPathIdentity, ...],
) -> tuple[_CleanupPathIdentity, ...] | None:
    try:
        observed = _snapshot_directory_chain(expected[-1].path)
    except BaseException:
        return None
    if len(expected) != len(observed) or not all(
        _same_cleanup_object(before, after)
        for before, after in zip(expected, observed)
    ):
        return None
    return observed


def _posix_parent_fd(
    parent: Path,
    *,
    strict_creation_fsync: bool,
    created_parents: list[CreatedDirectoryIdentity] | None = None,
) -> int:
    """Open/create ``parent`` through a no-follow walk from the filesystem root."""
    root = Path(parent.anchor)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow:
        raise _unsafe_parent(parent, "platform lacks O_NOFOLLOW parent verification")

    root_before = root.lstat()
    _validate_parent_metadata(root, root_before)
    try:
        descriptor = os.open(root, flags | nofollow)
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise _unsafe_parent(root, "directory changed into an alias during open") from exc
        raise

    try:
        root_opened = os.fstat(descriptor)
        _validate_parent_metadata(root, root_opened)
        if not _same_file(root_before, root_opened):
            raise _unsafe_parent(root, "directory identity changed during open")

        current = root
        for component in parent.relative_to(root).parts:
            current = current / component
            created = False
            try:
                metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                try:
                    os.mkdir(component, mode=0o777, dir_fd=descriptor)
                except FileExistsError:
                    pass
                else:
                    created = True
                metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)

            _validate_parent_metadata(current, metadata)
            if strict_creation_fsync:
                try:
                    os.fsync(descriptor)
                except OSError as exc:
                    raise AtomicWriteError(
                        "atomic write failed before destination commit while "
                        "verifying parent directory-entry durability",
                        stage="parent-create-fsync",
                        committed=False,
                        retry_safe=True,
                    ) from exc
            try:
                child = os.open(component, flags | nofollow, dir_fd=descriptor)
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise _unsafe_parent(
                        current,
                        "directory changed into an alias during open",
                    ) from exc
                raise
            try:
                opened = os.fstat(child)
                _validate_parent_metadata(current, opened)
                if not _same_file(metadata, opened):
                    raise _unsafe_parent(current, "directory identity changed during open")
                if created and created_parents is not None:
                    created_parents.append(
                        CreatedDirectoryIdentity(
                            current,
                            int(opened.st_dev),
                            int(opened.st_ino),
                        )
                    )
            except BaseException:
                os.close(child)
                raise
            try:
                os.close(descriptor)
            except OSError:
                # The verified child handle is already independent of its
                # ancestor. As with the final close, retrying after EINTR risks
                # closing a descriptor that the process has already reused.
                pass
            descriptor = child
        return descriptor
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def _fallback_prepare_parent(
    parent: Path,
    *,
    created_parents: list[CreatedDirectoryIdentity] | None = None,
) -> None:
    """Best available direct-parent validation where dir_fd is unavailable."""
    for candidate in (parent, *parent.parents):
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        _validate_parent_metadata(candidate, metadata)

    anchor, missing = _nearest_existing_parent(parent)
    current = anchor
    for component in reversed(missing):
        current = current / component
        created = False
        try:
            current.mkdir()
        except FileExistsError:
            pass
        else:
            created = True
        metadata = current.lstat()
        _validate_parent_metadata(current, metadata)
        if created and created_parents is not None:
            created_parents.append(
                CreatedDirectoryIdentity(
                    current,
                    int(metadata.st_dev),
                    int(metadata.st_ino),
                )
            )

    # Repeat immediately before use so a stable alias is never accepted merely
    # because it appeared after the create walk. Windows reparse points are
    # detected via st_file_attributes in _stat_is_path_alias.
    _validate_parent_metadata(parent, parent.lstat())


def _supports_secure_posix_parent() -> bool:
    required_dir_fd = (os.open, os.mkdir, os.stat, os.unlink, os.rename, os.link)
    return (
        all(function in os.supports_dir_fd for function in required_dir_fd)
        and os.stat in os.supports_follow_symlinks
        and os.link in os.supports_follow_symlinks
        and bool(getattr(os, "O_DIRECTORY", 0))
        and bool(getattr(os, "O_NOFOLLOW", 0))
    )


_SECURE_POSIX_PARENT = _supports_secure_posix_parent()


@contextmanager
def _direct_parent(
    path: Path,
    *,
    strict_creation_fsync: bool,
    created_parents: list[CreatedDirectoryIdentity] | None = None,
) -> Iterator[tuple[Path, int | None]]:
    absolute = _absolute_lexical(Path(path))
    parent = absolute.parent
    if os.name == "posix":
        if not _SECURE_POSIX_PARENT:
            raise _unsafe_parent(parent, "platform lacks secure directory-relative operations")
        descriptor = _posix_parent_fd(
            parent,
            strict_creation_fsync=strict_creation_fsync,
            created_parents=created_parents,
        )
        try:
            yield absolute, descriptor
        finally:
            try:
                os.close(descriptor)
            except OSError:
                # The yielded operation has already either failed on its own
                # or committed its rename/link. Descriptor cleanup cannot
                # truthfully reverse that result, and retrying close after
                # EINTR risks closing a reused descriptor.
                pass
        return

    _fallback_prepare_parent(parent, created_parents=created_parents)
    yield absolute, None


def _rollback_created_parents(
    created_parents: list[CreatedDirectoryIdentity],
    authority: _RollbackAuthority,
) -> None:
    """Consume callback-bound authority to remove owned empty parents.

    The full root-to-leaf object chain is checked before every ``rmdir``. Full
    generations were already proved intact before sidecar removal minted this
    token; cleanup never refreshes a post-callback generation and calls it
    owned. Any alias, replacement, foreign data, or uncertain metadata stops
    cleanup and preserves the original callback exception.
    """

    expected = list(authority.parent_chain)
    positions = {entry.path: index for index, entry in enumerate(expected)}
    for created in reversed(created_parents):
        position = positions.get(created.path)
        if position is None or position != len(expected) - 1:
            return
        observed = _observe_cleanup_chain(tuple(expected))
        if observed is None:
            return
        leaf = observed[-1]
        if (leaf.device, leaf.inode) != (created.device, created.inode):
            return
        try:
            created.path.rmdir()
        except BaseException:
            return

        expected = expected[:-1]


def _cleanup_rejected_sidecar(
    state: _ExclusivePrecommitState,
    path: Path,
    name: str,
    parent_fd: int | None,
    created_parents: list[CreatedDirectoryIdentity],
) -> _RollbackAuthority | None:
    """Reclaim the exact sidecar and mint directory rollback authority.

    Every lexical parent and the sidecar must retain its complete callback-bound
    generation before any pathname is unlinked. Uncertainty deliberately leaks
    the owned sidecar instead of traversing or deleting another namespace.
    """

    proof = state.proof
    if state.phase != "rejected" or proof is None:
        return None

    first_chain = _observe_cleanup_chain(proof.parent_chain)
    if first_chain is None or any(
        not _same_cleanup_identity(before, after)
        for before, after in zip(proof.parent_chain, first_chain)
    ):
        return None
    try:
        first_sidecar = _cleanup_path_identity(
            proof.sidecar.path,
            _sidecar_metadata(path, name, parent_fd),
        )
    except BaseException:
        return None
    if not _same_cleanup_identity(proof.sidecar, first_sidecar):
        return None

    second_chain = _observe_cleanup_chain(proof.parent_chain)
    if second_chain is None or any(
        not _same_cleanup_identity(before, after)
        for before, after in zip(proof.parent_chain, second_chain)
    ) or any(
        not _same_cleanup_identity(first, second)
        for first, second in zip(first_chain, second_chain)
    ):
        return None
    try:
        second_sidecar = _cleanup_path_identity(
            proof.sidecar.path,
            _sidecar_metadata(path, name, parent_fd),
        )
    except BaseException:
        return None
    if not _same_cleanup_identity(proof.sidecar, second_sidecar):
        return None

    try:
        _unlink_sidecar(path, name, parent_fd)
    except BaseException:
        return None
    if not created_parents:
        return None
    return _RollbackAuthority(second_chain)


def _open_exclusive_tmp(path: Path, parent_fd: int | None) -> tuple[int, str]:
    """Create a unique regular-file sidecar without following existing links."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    for _ in range(_TEMP_ATTEMPTS):
        name = f"{path.name}.{secrets.token_hex(16)}.tmp"
        try:
            if parent_fd is not None:
                descriptor = os.open(name, flags, 0o600, dir_fd=parent_fd)
            else:
                descriptor = os.open(path.parent / name, flags, 0o600)
        except FileExistsError:
            continue
        try:
            metadata = os.fstat(descriptor)
        except BaseException:
            os.close(descriptor)
            try:
                _unlink_sidecar(path, name, parent_fd)
            except OSError:
                pass
            raise
        if not stat.S_ISREG(metadata.st_mode):
            os.close(descriptor)
            try:
                _unlink_sidecar(path, name, parent_fd)
            except OSError:
                pass
            raise OSError(errno.EINVAL, "atomic sidecar is not a regular file", name)
        return descriptor, name
    raise FileExistsError(
        errno.EEXIST,
        f"could not reserve an exclusive atomic sidecar after {_TEMP_ATTEMPTS} attempts",
        str(path),
    )


def _unlink_sidecar(path: Path, name: str, parent_fd: int | None) -> None:
    if parent_fd is not None:
        os.unlink(name, dir_fd=parent_fd)
    else:
        (path.parent / name).unlink()


def _windows_replace_is_transient(exc: OSError) -> bool:
    winerror = getattr(exc, "winerror", None)
    if winerror is not None:
        return winerror in _WINDOWS_REPLACE_TRANSIENT_WINERRORS
    return exc.errno == errno.EACCES


def _replace_over_open_destination(source: Path, path: Path) -> None:
    """Give Windows the overwrite atomicity POSIX rename provides for free.

    A failed MoveFileEx leaves the sidecar intact, so retrying is safe: either
    the destination handle closes and we publish, or the deadline expires and
    the original error propagates untouched.
    """

    deadline = time.monotonic() + _WINDOWS_REPLACE_DEADLINE_SECONDS
    delay = _WINDOWS_REPLACE_BACKOFF_SECONDS
    while True:
        try:
            os.replace(source, path)
            return
        except OSError as exc:
            if not _windows_replace_is_transient(exc):
                raise
            if time.monotonic() >= deadline:
                raise
            time.sleep(delay)
            delay = min(delay * 2, _WINDOWS_REPLACE_BACKOFF_CEILING_SECONDS)


def _replace_sidecar(path: Path, name: str, parent_fd: int | None) -> None:
    if parent_fd is not None:
        # POSIX rename is overwrite-atomic and supports directory-relative
        # operation on every platform where this secure branch is selected.
        os.rename(name, path.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
    else:
        _fallback_prepare_parent(path.parent)
        source = path.parent / name
        if os.name == "nt":
            _replace_over_open_destination(source, path)
        else:
            os.replace(source, path)


def _publish_sidecar(
    path: Path,
    name: str,
    parent_fd: int | None,
    *,
    precommit_state: _ExclusivePrecommitState | None = None,
    opened_identity: PublishedFileIdentity,
    opened_cleanup_identity: _CleanupPathIdentity,
    created_parents: list[CreatedDirectoryIdentity] | None = None,
) -> bool:
    """Publish without replacement and report whether cleanup completed.

    Once the destination link/rename succeeds, publication is committed. A
    later sidecar cleanup failure must not be reported as publication failure:
    callers could otherwise roll back earlier state while the destination they
    believe absent is already visible. ``False`` therefore means only that the
    caller should make one best-effort cleanup retry.
    """
    if parent_fd is not None:
        if precommit_state is not None:
            _run_exclusive_precommit(
                precommit_state,
                path,
                name,
                parent_fd,
                opened_identity,
                opened_cleanup_identity,
            )
        os.link(
            name,
            path.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
            follow_symlinks=False,
        )
        try:
            _unlink_sidecar(path, name, parent_fd)
        except OSError:
            return False
        return True

    _fallback_prepare_parent(path.parent, created_parents=created_parents)
    source = path.parent / name
    if os.name == "nt":
        # Windows rename fails with FileExistsError when destination exists.
        if precommit_state is not None:
            # Callback exceptions are authority results, not rename errors;
            # preserve their exact object instead of collision-translating them.
            _run_exclusive_precommit(
                precommit_state,
                path,
                name,
                parent_fd,
                opened_identity,
                opened_cleanup_identity,
            )
        try:
            os.rename(source, path)
        except OSError as exc:
            try:
                path.lstat()
            except FileNotFoundError:
                raise exc
            raise FileExistsError(
                errno.EEXIST,
                "atomic publication destination already exists",
                str(path),
            ) from exc
        return True
    else:
        if precommit_state is not None:
            _run_exclusive_precommit(
                precommit_state,
                path,
                name,
                parent_fd,
                opened_identity,
                opened_cleanup_identity,
            )
        os.link(source, path, follow_symlinks=False)
        try:
            source.unlink()
        except OSError:
            return False
        return True


def _fsync_parent(path: Path, parent_fd: int | None) -> None:
    if os.name != "posix":
        return
    descriptor = parent_fd
    close_after = False
    try:
        if descriptor is None:
            descriptor = os.open(
                path.parent,
                os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0),
            )
            close_after = True
        os.fsync(descriptor)
    finally:
        if close_after and descriptor is not None:
            os.close(descriptor)


def _require_fsync_policy(value: str) -> str:
    if value not in {"best_effort", "strict"}:
        raise ValueError("fsync_policy must be 'best_effort' or 'strict'")
    return value


def _write_text(
    path: Path,
    text: str,
    *,
    encoding: str,
    fsync: bool,
    fsync_policy: str,
    exclusive: bool,
    precommit: Callable[[], None] | None = None,
) -> PublishedFileIdentity | None:
    policy = _require_fsync_policy(fsync_policy)
    created_parents: list[CreatedDirectoryIdentity] = []
    precommit_state = (
        _ExclusivePrecommitState(precommit) if precommit is not None else None
    )

    with _direct_parent(
        path,
        strict_creation_fsync=fsync and policy == "strict",
        created_parents=created_parents,
    ) as (absolute, parent_fd):
        descriptor: int | None = None
        sidecar: str | None = None
        published_identity: PublishedFileIdentity | None = None
        opened_cleanup_identity: _CleanupPathIdentity | None = None
        try:
            descriptor, sidecar = _open_exclusive_tmp(absolute, parent_fd)
            # newline="" keeps the exact caller bytes on Windows as well as
            # POSIX, which makes byte-bound rollback portable.
            handle = os.fdopen(descriptor, "w", encoding=encoding, newline="")
            descriptor = None
            with handle:
                handle.write(text)
                handle.flush()
                if fsync:
                    try:
                        os.fsync(handle.fileno())
                    except OSError as exc:
                        if policy == "strict":
                            raise AtomicWriteError(
                                "atomic write failed before destination commit during file fsync",
                                stage="file-fsync",
                                committed=False,
                                retry_safe=True,
                            ) from exc
                opened = os.fstat(handle.fileno())
                if not stat.S_ISREG(opened.st_mode):
                    raise OSError(
                        errno.EINVAL,
                        "atomic sidecar changed from a regular file",
                        sidecar,
                    )
                published_identity = _published_file_identity(opened)
                opened_cleanup_identity = _cleanup_path_identity(
                    absolute.parent / sidecar,
                    opened,
                )

            if exclusive:
                assert published_identity is not None
                assert opened_cleanup_identity is not None
                if _publish_sidecar(
                    absolute,
                    sidecar,
                    parent_fd,
                    precommit_state=precommit_state,
                    opened_identity=published_identity,
                    opened_cleanup_identity=opened_cleanup_identity,
                    created_parents=created_parents,
                ):
                    sidecar = None
            else:
                _replace_sidecar(absolute, sidecar, parent_fd)
                sidecar = None
            if fsync:
                try:
                    _fsync_parent(absolute, parent_fd)
                except OSError as exc:
                    if policy == "strict":
                        raise AtomicWriteError(
                            "atomic write committed but parent directory fsync failed",
                            stage="parent-fsync",
                            committed=True,
                            retry_safe=False,
                        ) from exc
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if sidecar is not None:
                if precommit_state is not None and precommit_state.phase == "rejected":
                    try:
                        authority = _cleanup_rejected_sidecar(
                            precommit_state,
                            absolute,
                            sidecar,
                            parent_fd,
                            created_parents,
                        )
                        if authority is not None:
                            _rollback_created_parents(created_parents, authority)
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
                        _unlink_sidecar(absolute, sidecar, parent_fd)
                    except OSError:
                        pass
        if exclusive:
            assert published_identity is not None
            return published_identity
        return None


def write_text_atomic(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
    fsync: bool = True,
    fsync_policy: str = "best_effort",
) -> None:
    """Atomically write ``text`` to ``path``.

    Creates parent dirs as needed. On success no ``.tmp`` sidecar remains. A
    strict file-fsync failure occurs before publication and leaves the original
    target untouched; a strict parent-fsync failure is reported as already
    committed and non-retry-safe.
    """
    _write_text(
        Path(path),
        text,
        encoding=encoding,
        fsync=fsync,
        fsync_policy=fsync_policy,
        exclusive=False,
    )


def publish_text_atomic(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
    fsync: bool = True,
    fsync_policy: str = "best_effort",
    precommit: Callable[[], None] | None = None,
) -> None:
    """Atomically publish a new text file without clobbering any destination.

    Raises ``FileExistsError`` if a file, directory, symlink, or reparse point is
    present at the destination when publication occurs.
    """
    publish_text_owned_atomic(
        Path(path),
        text,
        encoding=encoding,
        fsync=fsync,
        fsync_policy=fsync_policy,
        precommit=precommit,
    )


def publish_text_owned_atomic(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
    fsync: bool = True,
    fsync_policy: str = "best_effort",
    precommit: Callable[[], None] | None = None,
) -> PublishedFileIdentity:
    """Publish new text and return its pre-commit opened-file identity."""

    identity = _write_text(
        Path(path),
        text,
        encoding=encoding,
        fsync=fsync,
        fsync_policy=fsync_policy,
        exclusive=True,
        precommit=precommit,
    )
    assert identity is not None
    return identity


def write_json_atomic(
    path: Path,
    payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    fsync: bool = True,
    fsync_policy: str = "best_effort",
) -> None:
    """Atomically write ``payload`` as JSON (trailing newline included)."""
    text = json.dumps(payload, ensure_ascii=False, indent=indent, sort_keys=sort_keys) + "\n"
    write_text_atomic(
        Path(path),
        text,
        fsync=fsync,
        fsync_policy=fsync_policy,
    )


def publish_json_atomic(
    path: Path,
    payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    fsync: bool = True,
    fsync_policy: str = "best_effort",
    precommit: Callable[[], None] | None = None,
) -> None:
    """Atomically publish new JSON without replacing an existing destination."""
    publish_json_owned_atomic(
        Path(path),
        payload,
        indent=indent,
        sort_keys=sort_keys,
        fsync=fsync,
        fsync_policy=fsync_policy,
        precommit=precommit,
    )


def publish_json_owned_atomic(
    path: Path,
    payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    fsync: bool = True,
    fsync_policy: str = "best_effort",
    precommit: Callable[[], None] | None = None,
) -> PublishedFileIdentity:
    """Publish new JSON and return its pre-commit opened-file identity."""

    text = json.dumps(payload, ensure_ascii=False, indent=indent, sort_keys=sort_keys) + "\n"
    return publish_text_owned_atomic(
        Path(path),
        text,
        fsync=fsync,
        fsync_policy=fsync_policy,
        precommit=precommit,
    )
