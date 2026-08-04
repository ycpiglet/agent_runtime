"""Tests for atomic_io — power-loss-safe atomic file writes.

Invariants under test:
  - writes are atomic (temp file + os.replace), never leaving a half-written target;
  - no stray ``.tmp`` sidecar is left behind on success;
  - parent directories are created on demand;
  - JSON serialization honors the caller's ``indent`` / ``sort_keys`` preference so
    existing call-sites keep their on-disk format.
"""

from __future__ import annotations

import errno
import json
import os
import stat
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import atomic_io  # noqa: E402


def _tmp_siblings(path: Path) -> list[Path]:
    return list(path.parent.glob(f"{path.name}.*.tmp"))


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


def test_write_json_atomic_creates_parents_and_valid_json(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "dir" / "state.json"
    atomic_io.write_json_atomic(target, {"b": 2, "a": 1})

    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1, "b": 2}
    # trailing newline preserved (matches prior write_text behavior)
    assert target.read_text(encoding="utf-8").endswith("\n")


def test_write_json_atomic_leaves_no_tmp_sidecar(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    atomic_io.write_json_atomic(target, {"x": 1})
    assert _tmp_siblings(target) == []


def test_write_json_atomic_overwrites_existing(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    atomic_io.write_json_atomic(target, {"v": 1})
    atomic_io.write_json_atomic(target, {"v": 2})
    assert json.loads(target.read_text(encoding="utf-8")) == {"v": 2}
    assert _tmp_siblings(target) == []


def test_sort_keys_default_preserves_insertion_order(tmp_path: Path) -> None:
    target = tmp_path / "ordered.json"
    atomic_io.write_json_atomic(target, {"z": 1, "a": 2}, sort_keys=False)
    text = target.read_text(encoding="utf-8")
    assert text.index('"z"') < text.index('"a"')


def test_sort_keys_true_sorts(tmp_path: Path) -> None:
    target = tmp_path / "sorted.json"
    atomic_io.write_json_atomic(target, {"z": 1, "a": 2}, sort_keys=True)
    text = target.read_text(encoding="utf-8")
    assert text.index('"a"') < text.index('"z"')


def test_write_text_atomic_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    atomic_io.write_text_atomic(target, "hello\nworld\n")
    assert target.read_text(encoding="utf-8") == "hello\nworld\n"
    assert _tmp_siblings(target) == []


def test_fsync_disabled_still_writes(tmp_path: Path) -> None:
    target = tmp_path / "nofsync.json"
    atomic_io.write_json_atomic(target, {"ok": True}, fsync=False)
    assert json.loads(target.read_text(encoding="utf-8")) == {"ok": True}


def test_precreated_predictable_tmp_symlink_cannot_overwrite_external_file(
    tmp_path: Path,
) -> None:
    """A hostile legacy sidecar must never be opened as the write target."""
    target = tmp_path / "state.json"
    external = tmp_path / "external.txt"
    external.write_text("keep me\n", encoding="utf-8")
    predictable_tmp = target.with_name(
        f"{target.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    try:
        predictable_tmp.symlink_to(external)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks are unavailable in this environment: {exc}")

    try:
        atomic_io.write_json_atomic(target, {"safe": True})

        assert external.read_text(encoding="utf-8") == "keep me\n"
        assert json.loads(target.read_text(encoding="utf-8")) == {"safe": True}
    finally:
        predictable_tmp.unlink(missing_ok=True)


def test_write_refuses_symlinked_parent_without_writing_outside(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks are unavailable in this environment: {exc}")

    with pytest.raises(OSError, match="alias|reparse|direct"):
        atomic_io.write_text_atomic(alias / "escaped.txt", "must not escape\n")

    assert not (outside / "escaped.txt").exists()


def test_write_refuses_symlinked_existing_ancestor_of_missing_parent(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks are unavailable in this environment: {exc}")

    with pytest.raises(OSError, match="alias|reparse|direct"):
        atomic_io.write_text_atomic(alias / "new" / "escaped.txt", "must not escape\n")

    assert not (outside / "new").exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX no-follow ancestry validation required")
@pytest.mark.parametrize(
    ("writer_name", "payload"),
    (
        ("write_text_atomic", "must not escape\n"),
        ("write_json_atomic", {"must_not_escape": True}),
        ("publish_text_atomic", "must not escape\n"),
        ("publish_text_owned_atomic", "must not escape\n"),
        ("publish_json_atomic", {"must_not_escape": True}),
        ("publish_json_owned_atomic", {"must_not_escape": True}),
    ),
)
def test_atomic_writers_refuse_existing_parent_below_symlinked_ancestor(
    tmp_path: Path,
    writer_name: str,
    payload: object,
) -> None:
    outside = tmp_path / "outside"
    direct_parent = outside / "direct-parent"
    direct_parent.mkdir(parents=True)
    sentinel = outside / "sentinel.txt"
    sentinel.write_bytes(b"external owner\n")
    authority_root = tmp_path / "authority-root"
    authority_root.mkdir()
    alias = authority_root / "alias"
    try:
        alias.symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks are unavailable in this environment: {exc}")

    outside_target = direct_parent / "escaped-state"
    lexical_target = alias / direct_parent.name / outside_target.name

    refusal: Exception | None = None
    try:
        getattr(atomic_io, writer_name)(lexical_target, payload)
    except Exception as exc:
        refusal = exc

    residue = _tmp_siblings(outside_target)
    assert isinstance(refusal, atomic_io.UnsafePathError), (
        f"{writer_name} followed the symlinked ancestor: "
        f"outcome={'published' if refusal is None else type(refusal).__name__}, "
        f"outside_target_exists={outside_target.exists()}, residue={residue}"
    )
    assert "alias" in str(refusal) or "symlink" in str(refusal) or "reparse" in str(refusal)

    assert sentinel.read_bytes() == b"external owner\n"
    assert not outside_target.exists()
    assert residue == []


def test_write_refuses_non_directory_parent(tmp_path: Path) -> None:
    parent = tmp_path / "not-a-directory"
    parent.write_text("ordinary file\n", encoding="utf-8")

    with pytest.raises(OSError):
        atomic_io.write_text_atomic(parent / "state.txt", "must not appear\n")

    assert parent.read_text(encoding="utf-8") == "ordinary file\n"


def test_windows_reparse_attribute_is_classified_as_alias() -> None:
    fake_stat = SimpleNamespace(
        st_mode=stat.S_IFDIR,
        st_file_attributes=0x0400,
    )

    assert atomic_io._stat_is_path_alias(fake_stat) is True


def test_fallback_parent_validation_rejects_existing_alias_ancestor(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    direct_parent = outside / "direct-parent"
    direct_parent.mkdir(parents=True)
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks are unavailable in this environment: {exc}")

    with pytest.raises(OSError, match="alias|reparse|direct"):
        atomic_io._fallback_prepare_parent(alias / "direct-parent")


@pytest.mark.skipif(os.name != "nt", reason="native Windows junction required")
@pytest.mark.parametrize(
    ("writer_name", "payload"),
    (
        ("write_text_atomic", "must not escape\n"),
        ("write_json_atomic", {"must_not_escape": True}),
        ("publish_text_atomic", "must not escape\n"),
        ("publish_json_atomic", {"must_not_escape": True}),
    ),
)
def test_native_windows_junction_parent_is_rejected_without_external_mutation(
    tmp_path: Path,
    writer_name: str,
    payload: object,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    external_target = outside / "state"
    external_target.write_bytes(b"external owner\n")
    before = {
        path.name: path.read_bytes()
        for path in outside.iterdir()
        if path.is_file()
    }
    junction = tmp_path / "junction-parent"

    try:
        _create_windows_junction(junction, outside)

        with pytest.raises(atomic_io.UnsafePathError, match="alias|reparse|direct"):
            getattr(atomic_io, writer_name)(junction / external_target.name, payload)

        after = {
            path.name: path.read_bytes()
            for path in outside.iterdir()
            if path.is_file()
        }
        assert after == before
    finally:
        try:
            os.lstat(junction)
        except FileNotFoundError:
            pass
        else:
            _remove_windows_junction(junction)


def test_publish_text_atomic_creates_new_file_without_sidecar(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "note.txt"

    result = atomic_io.publish_text_atomic(target, "published once\n")

    assert result is None
    assert target.read_text(encoding="utf-8") == "published once\n"
    assert _tmp_siblings(target) == []


def test_owned_publish_returns_identity_captured_from_opened_file(
    tmp_path: Path,
) -> None:
    target = tmp_path / "owned.txt"

    identity = atomic_io.publish_text_owned_atomic(target, "owned bytes\n")

    metadata = target.lstat()
    assert identity.device == int(metadata.st_dev)
    assert identity.inode == int(metadata.st_ino)
    assert identity.mode == int(metadata.st_mode)
    assert identity.size == len(b"owned bytes\n")
    assert target.read_bytes() == b"owned bytes\n"


@pytest.mark.skipif(os.name != "posix", reason="directory fd cleanup is POSIX-only")
def test_post_commit_parent_fd_close_error_does_not_reverse_publish_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "committed-before-parent-close.txt"
    real_close = atomic_io.os.close
    injected: list[int] = []

    def close_then_raise(descriptor: int) -> None:
        mode = os.fstat(descriptor).st_mode
        real_close(descriptor)
        if stat.S_ISDIR(mode) and not injected:
            injected.append(descriptor)
            raise OSError("injected post-commit parent fd close failure")

    monkeypatch.setattr(atomic_io.os, "close", close_then_raise)

    identity = atomic_io.publish_text_owned_atomic(target, "committed\n")

    assert injected
    assert target.read_bytes() == b"committed\n"
    metadata = target.lstat()
    assert (identity.device, identity.inode) == (
        int(metadata.st_dev),
        int(metadata.st_ino),
    )


def test_publish_json_atomic_preserves_json_options(tmp_path: Path) -> None:
    target = tmp_path / "claim.json"

    atomic_io.publish_json_atomic(
        target,
        {"z": 1, "a": 2},
        indent=4,
        sort_keys=True,
    )

    text = target.read_text(encoding="utf-8")
    assert text.index('"a"') < text.index('"z"')
    assert text.startswith("{\n    ")
    assert text.endswith("\n")


def test_publish_refuses_existing_destination_without_mutation(tmp_path: Path) -> None:
    target = tmp_path / "claim.json"
    target.write_text("owner-one\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        atomic_io.publish_text_atomic(target, "owner-two\n")

    assert target.read_text(encoding="utf-8") == "owner-one\n"
    assert _tmp_siblings(target) == []


def test_publish_refuses_destination_symlink_without_following_it(tmp_path: Path) -> None:
    external = tmp_path / "external.txt"
    external.write_text("keep me\n", encoding="utf-8")
    target = tmp_path / "claim.json"
    try:
        target.symlink_to(external)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks are unavailable in this environment: {exc}")

    with pytest.raises(FileExistsError):
        atomic_io.publish_text_atomic(target, "must not replace\n")

    assert target.is_symlink()
    assert external.read_text(encoding="utf-8") == "keep me\n"
    assert _tmp_siblings(target) == []


def test_publish_cleans_sidecar_when_text_encoding_fails(tmp_path: Path) -> None:
    target = tmp_path / "claim.txt"

    with pytest.raises(UnicodeEncodeError):
        atomic_io.publish_text_atomic(target, "\ud800")

    assert not target.exists()
    assert _tmp_siblings(target) == []


def test_exclusive_sidecar_collision_never_follows_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "state.json"
    external = tmp_path / "external.txt"
    external.write_text("keep me\n", encoding="utf-8")
    hostile = target.with_name(f"{target.name}.hostile.tmp")
    try:
        hostile.symlink_to(external)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks are unavailable in this environment: {exc}")

    tokens = iter(["hostile", "safe"])
    monkeypatch.setattr(atomic_io.secrets, "token_hex", lambda _size: next(tokens))

    atomic_io.write_json_atomic(target, {"safe": True})

    assert external.read_text(encoding="utf-8") == "keep me\n"
    assert json.loads(target.read_text(encoding="utf-8")) == {"safe": True}
    hostile.unlink()
    assert _tmp_siblings(target) == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX exclusive publication uses linkat")
def test_publish_collision_at_publication_point_does_not_clobber(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "claim.json"
    real_link = atomic_io.os.link
    raced = False

    def competing_link(
        source: object,
        destination: object,
        *args: object,
        **kwargs: object,
    ) -> None:
        nonlocal raced
        if not raced:
            raced = True
            target.write_text("competitor\n", encoding="utf-8")
        real_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(atomic_io.os, "link", competing_link)

    with pytest.raises(FileExistsError):
        atomic_io.publish_text_atomic(target, "late writer\n")

    assert target.read_text(encoding="utf-8") == "competitor\n"
    assert _tmp_siblings(target) == []


@pytest.mark.skipif(os.name != "posix", reason="POSIX publication uses link + unlink")
@pytest.mark.parametrize(
    ("publisher_name", "payload", "expected"),
    (
        ("publish_text_atomic", "committed\n", b"committed\n"),
        (
            "publish_json_atomic",
            {"committed": True},
            b'{\n  "committed": true\n}\n',
        ),
    ),
)
def test_publish_reports_committed_success_when_sidecar_cleanup_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    publisher_name: str,
    payload: object,
    expected: bytes,
) -> None:
    target = tmp_path / "committed-state"
    real_unlink = atomic_io._unlink_sidecar

    def unlink_then_raise(path: Path, name: str, parent_fd: int | None) -> None:
        real_unlink(path, name, parent_fd)
        raise OSError("injected post-publication cleanup failure")

    monkeypatch.setattr(atomic_io, "_unlink_sidecar", unlink_then_raise)

    result = getattr(atomic_io, publisher_name)(target, payload)

    assert result is None
    assert target.read_bytes() == expected
    assert _tmp_siblings(target) == []


@pytest.mark.skipif(os.name == "nt", reason="directory fsync is a POSIX durability boundary")
@pytest.mark.parametrize("exclusive", [False, True])
def test_successful_write_fsyncs_file_and_parent_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exclusive: bool,
) -> None:
    target = tmp_path / "durable.txt"
    fsync_kinds: list[str] = []

    def observing_fsync(descriptor: int) -> None:
        mode = os.fstat(descriptor).st_mode
        fsync_kinds.append("directory" if stat.S_ISDIR(mode) else "file")

    monkeypatch.setattr(atomic_io.os, "fsync", observing_fsync)

    writer = atomic_io.publish_text_atomic if exclusive else atomic_io.write_text_atomic
    writer(target, "durable\n")

    assert fsync_kinds == ["file", "directory"]


def test_concurrent_overwrite_writers_publish_only_complete_payloads(tmp_path: Path) -> None:
    target = tmp_path / "shared.txt"
    payloads = {f"writer-{index}:" + (str(index) * 2048) for index in range(12)}
    barrier = threading.Barrier(len(payloads))
    failures: list[BaseException] = []

    def writer(payload: str) -> None:
        try:
            barrier.wait()
            atomic_io.write_text_atomic(target, payload)
        except BaseException as exc:  # pragma: no cover - asserted below
            failures.append(exc)

    threads = [threading.Thread(target=writer, args=(payload,)) for payload in payloads]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert failures == []
    assert target.read_text(encoding="utf-8") in payloads
    assert _tmp_siblings(target) == []


def _transient(winerror: int | None) -> OSError:
    """The shape Windows raises while another handle holds the destination."""

    exc = OSError(errno.EACCES, "Access is denied")
    if winerror is not None:
        exc.winerror = winerror
    return exc


# ERROR_ACCESS_DENIED, ERROR_SHARING_VIOLATION, ERROR_LOCK_VIOLATION, and the
# errno-only shape seen when winerror is unavailable.
@pytest.mark.parametrize("winerror", [5, 32, 33, None])
def test_windows_replace_waits_out_a_transient_destination_handle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    winerror: int | None,
) -> None:
    """Runs on every platform: the Windows branch is otherwise never exercised."""

    source = tmp_path / "sidecar"
    target = tmp_path / "published"
    source.write_text("payload\n", encoding="utf-8")
    attempts: list[int] = []

    real_replace = os.replace

    def flaky_replace(src: object, dst: object) -> None:
        attempts.append(1)
        if len(attempts) < 3:
            raise _transient(winerror)
        real_replace(src, dst)

    monkeypatch.setattr(atomic_io.os, "replace", flaky_replace)
    monkeypatch.setattr(atomic_io.time, "sleep", lambda _seconds: None)

    atomic_io._replace_over_open_destination(source, target)

    assert len(attempts) == 3
    assert target.read_text(encoding="utf-8") == "payload\n"
    assert not source.exists()


# ERROR_PRIVILEGE_NOT_HELD and a plain EPERM: neither clears by waiting.
@pytest.mark.parametrize(
    ("winerror", "err"),
    [(1314, errno.EACCES), (None, errno.EPERM)],
)
def test_windows_replace_never_retries_a_genuine_denial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    winerror: int | None,
    err: int,
) -> None:
    """A retry that swallows a real ACL failure would hide a broken deployment."""

    source = tmp_path / "sidecar"
    source.write_text("payload\n", encoding="utf-8")
    attempts: list[int] = []

    def denying_replace(src: object, dst: object) -> None:
        attempts.append(1)
        exc = OSError(err, "denied")
        if winerror is not None:
            exc.winerror = winerror
        raise exc

    monkeypatch.setattr(atomic_io.os, "replace", denying_replace)
    monkeypatch.setattr(atomic_io.time, "sleep", lambda _seconds: None)

    with pytest.raises(OSError) as caught:
        atomic_io._replace_over_open_destination(source, tmp_path / "published")

    assert caught.value.errno == err
    assert attempts == [1]


def test_windows_replace_retry_is_deadline_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A destination handle that never closes must surface, not spin forever."""

    source = tmp_path / "sidecar"
    source.write_text("payload\n", encoding="utf-8")
    attempts: list[int] = []
    clock = {"now": 0.0}

    def stuck_replace(src: object, dst: object) -> None:
        attempts.append(1)
        raise _transient(32)

    monkeypatch.setattr(atomic_io.os, "replace", stuck_replace)
    monkeypatch.setattr(atomic_io.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(
        atomic_io.time,
        "sleep",
        lambda seconds: clock.__setitem__("now", clock["now"] + max(seconds, 1e-3)),
    )

    with pytest.raises(OSError) as caught:
        atomic_io._replace_over_open_destination(source, tmp_path / "published")

    assert getattr(caught.value, "winerror", None) == 32
    assert clock["now"] >= atomic_io._WINDOWS_REPLACE_DEADLINE_SECONDS
    # Backoff caps out, so the deadline is reached in a bounded number of tries.
    assert len(attempts) < 1000
    assert source.exists(), "a failed replace must leave the sidecar recoverable"


def test_replace_sidecar_routes_windows_through_the_bounded_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pins the dispatch itself: the helper is useless if nothing calls it."""

    target = tmp_path / "published"
    name = "sidecar.tmp"
    (tmp_path / name).write_text("payload\n", encoding="utf-8")
    attempts: list[int] = []
    real_replace = os.replace

    def flaky_replace(src: object, dst: object) -> None:
        attempts.append(1)
        if len(attempts) < 2:
            raise _transient(32)
        real_replace(src, dst)

    monkeypatch.setattr(atomic_io.os, "name", "nt")
    monkeypatch.setattr(atomic_io.os, "replace", flaky_replace)
    monkeypatch.setattr(atomic_io.time, "sleep", lambda _seconds: None)

    atomic_io._replace_sidecar(target, name, None)

    assert attempts == [1, 1], "the sharing violation was surfaced, not waited out"
    assert target.read_text(encoding="utf-8") == "payload\n"


def test_concurrent_exclusive_publish_has_exactly_one_winner(tmp_path: Path) -> None:
    target = tmp_path / "claim.txt"
    payloads = {f"claimant-{index}\n" for index in range(12)}
    barrier = threading.Barrier(len(payloads))
    winners: list[str] = []
    collisions: list[FileExistsError] = []
    failures: list[BaseException] = []

    def publisher(payload: str) -> None:
        try:
            barrier.wait()
            atomic_io.publish_text_atomic(target, payload)
            winners.append(payload)
        except FileExistsError as exc:
            collisions.append(exc)
        except BaseException as exc:  # pragma: no cover - asserted below
            failures.append(exc)

    threads = [threading.Thread(target=publisher, args=(payload,)) for payload in payloads]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert failures == []
    assert len(winners) == 1
    assert len(collisions) == len(payloads) - 1
    assert target.read_text(encoding="utf-8") == winners[0]
    assert _tmp_siblings(target) == []


def test_source_and_project_template_are_byte_identical() -> None:
    assert (ROOT / "scripts" / "atomic_io.py").read_bytes() == (
        ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "atomic_io.py"
    ).read_bytes()
