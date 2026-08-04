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
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, NamedTuple


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


def _posix_parent_fd(parent: Path) -> int:
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
            try:
                metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                try:
                    os.mkdir(component, mode=0o777, dir_fd=descriptor)
                except FileExistsError:
                    pass
                metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)

            _validate_parent_metadata(current, metadata)
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


def _fallback_prepare_parent(parent: Path) -> None:
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
        try:
            current.mkdir()
        except FileExistsError:
            pass
        _validate_parent_metadata(current, current.lstat())

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
def _direct_parent(path: Path) -> Iterator[tuple[Path, int | None]]:
    absolute = _absolute_lexical(Path(path))
    parent = absolute.parent
    if os.name == "posix":
        if not _SECURE_POSIX_PARENT:
            raise _unsafe_parent(parent, "platform lacks secure directory-relative operations")
        descriptor = _posix_parent_fd(parent)
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

    _fallback_prepare_parent(parent)
    yield absolute, None


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


def _publish_sidecar(path: Path, name: str, parent_fd: int | None) -> bool:
    """Publish without replacement and report whether cleanup completed.

    Once the destination link/rename succeeds, publication is committed. A
    later sidecar cleanup failure must not be reported as publication failure:
    callers could otherwise roll back earlier state while the destination they
    believe absent is already visible. ``False`` therefore means only that the
    caller should make one best-effort cleanup retry.
    """
    if parent_fd is not None:
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

    _fallback_prepare_parent(path.parent)
    source = path.parent / name
    if os.name == "nt":
        # Windows rename fails with FileExistsError when destination exists.
        try:
            os.rename(source, path)
        except OSError as exc:
            try:
                path.lstat()
            except FileNotFoundError:
                raise
            raise FileExistsError(
                errno.EEXIST,
                "atomic publication destination already exists",
                str(path),
            ) from exc
        return True
    else:
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
    except OSError:
        # Some filesystems reject directory fsync. The publication remains
        # atomic, while durability is best-effort as with the file fsync below.
        pass
    finally:
        if close_after and descriptor is not None:
            os.close(descriptor)


def _write_text(
    path: Path,
    text: str,
    *,
    encoding: str,
    fsync: bool,
    exclusive: bool,
) -> PublishedFileIdentity | None:
    with _direct_parent(path) as (absolute, parent_fd):
        descriptor: int | None = None
        sidecar: str | None = None
        published_identity: PublishedFileIdentity | None = None
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
                    except OSError:
                        # Atomicity does not depend on filesystem durability.
                        pass
                opened = os.fstat(handle.fileno())
                if not stat.S_ISREG(opened.st_mode):
                    raise OSError(
                        errno.EINVAL,
                        "atomic sidecar changed from a regular file",
                        sidecar,
                    )
                published_identity = PublishedFileIdentity(
                    int(opened.st_dev),
                    int(opened.st_ino),
                    int(opened.st_mode),
                    int(opened.st_size),
                    int(getattr(opened, "st_file_attributes", 0) or 0),
                    int(getattr(opened, "st_reparse_tag", 0) or 0),
                )

            if exclusive:
                if _publish_sidecar(absolute, sidecar, parent_fd):
                    sidecar = None
            else:
                _replace_sidecar(absolute, sidecar, parent_fd)
                sidecar = None
            if fsync:
                _fsync_parent(absolute, parent_fd)
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if sidecar is not None:
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
) -> None:
    """Atomically write ``text`` to ``path``.

    Creates parent dirs as needed. On success no ``.tmp`` sidecar remains; on any
    failure the partial temp file is cleaned up and the original target is left
    untouched (the write never corrupts an existing file).
    """
    _write_text(Path(path), text, encoding=encoding, fsync=fsync, exclusive=False)


def publish_text_atomic(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
    fsync: bool = True,
) -> None:
    """Atomically publish a new text file without clobbering any destination.

    Raises ``FileExistsError`` if a file, directory, symlink, or reparse point is
    present at the destination when publication occurs.
    """
    publish_text_owned_atomic(Path(path), text, encoding=encoding, fsync=fsync)


def publish_text_owned_atomic(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
    fsync: bool = True,
) -> PublishedFileIdentity:
    """Publish new text and return its pre-commit opened-file identity."""

    identity = _write_text(
        Path(path),
        text,
        encoding=encoding,
        fsync=fsync,
        exclusive=True,
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
) -> None:
    """Atomically write ``payload`` as JSON (trailing newline included)."""
    text = json.dumps(payload, ensure_ascii=False, indent=indent, sort_keys=sort_keys) + "\n"
    write_text_atomic(Path(path), text, fsync=fsync)


def publish_json_atomic(
    path: Path,
    payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    fsync: bool = True,
) -> None:
    """Atomically publish new JSON without replacing an existing destination."""
    publish_json_owned_atomic(
        Path(path),
        payload,
        indent=indent,
        sort_keys=sort_keys,
        fsync=fsync,
    )


def publish_json_owned_atomic(
    path: Path,
    payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    fsync: bool = True,
) -> PublishedFileIdentity:
    """Publish new JSON and return its pre-commit opened-file identity."""

    text = json.dumps(payload, ensure_ascii=False, indent=indent, sort_keys=sort_keys) + "\n"
    return publish_text_owned_atomic(Path(path), text, fsync=fsync)
