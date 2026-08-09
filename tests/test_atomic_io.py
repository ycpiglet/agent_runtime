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


class _NamedOSProxy:
    """Delegate to the host os module while selecting an atomic_io branch."""

    def __init__(self, name: str, **overrides: object) -> None:
        self.name = name
        self._overrides = overrides

    def __getattr__(self, attribute: str) -> object:
        if attribute in self._overrides:
            return self._overrides[attribute]
        return getattr(os, attribute)


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


def test_fsync_disabled_keeps_strict_policy_from_syncing_parent_walk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "new-parent" / "nofsync.json"

    def reject_fsync(_descriptor: int) -> None:
        raise AssertionError("fsync must remain disabled")

    monkeypatch.setattr(atomic_io.os, "fsync", reject_fsync)

    atomic_io.write_json_atomic(
        target,
        {"ok": True},
        fsync=False,
        fsync_policy="strict",
    )

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


def test_exclusive_precommit_is_the_final_fallback_publication_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fallback validation and durable sidecar preparation precede authority."""

    target = tmp_path / "created" / "receipt.json"
    events: list[str] = []
    real_prepare_parent = atomic_io._fallback_prepare_parent

    def observe_parent_validation(
        parent: Path,
        *,
        created_parents: list[atomic_io.CreatedDirectoryIdentity] | None = None,
    ) -> None:
        events.append("parent-validation")
        real_prepare_parent(parent, created_parents=created_parents)

    def observe_destination(source: object, destination: object) -> None:
        events.append("destination")
        os.rename(source, destination)

    def prove_authority() -> None:
        events.append("precommit")
        assert target.parent.is_dir()
        assert not target.exists()
        assert len(_tmp_siblings(target)) == 1

    monkeypatch.setattr(atomic_io, "_fallback_prepare_parent", observe_parent_validation)
    monkeypatch.setattr(
        atomic_io,
        "os",
        _NamedOSProxy("nt", rename=observe_destination),
    )

    atomic_io.publish_json_atomic(
        target,
        {"prepared": True},
        fsync_policy="strict",
        precommit=prove_authority,
    )

    assert events[-3:] == ["parent-validation", "precommit", "destination"]
    assert json.loads(target.read_text(encoding="utf-8")) == {"prepared": True}
    assert _tmp_siblings(target) == []


def test_rejected_exclusive_precommit_restores_owned_fallback_parent_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A callback rejection removes only directories this operation created."""

    target = tmp_path / "agents" / "runtime" / "recovery_receipts" / "receipt.json"
    callback_calls = 0
    rejection = ValueError("stale recovery actor")

    def reject_authority() -> None:
        nonlocal callback_calls
        callback_calls += 1
        assert target.parent.is_dir()
        assert len(_tmp_siblings(target)) == 1
        raise rejection

    monkeypatch.setattr(atomic_io, "os", _NamedOSProxy("nt"))

    with pytest.raises(ValueError, match="stale recovery actor") as rejected:
        atomic_io.publish_json_atomic(
            target,
            {"prepared": True},
            fsync_policy="strict",
            precommit=reject_authority,
        )

    assert rejected.value is rejection
    assert callback_calls == 1
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("parent_case", ("pre-existing", "concurrently-populated"))
def test_rejected_exclusive_precommit_never_removes_unowned_parent_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    parent_case: str,
) -> None:
    target = tmp_path / "receipt-store" / "receipt.json"
    if parent_case == "pre-existing":
        target.parent.mkdir()

    def reject_authority() -> None:
        if parent_case == "concurrently-populated":
            (target.parent / "concurrent.txt").write_text(
                "belongs to another writer\n",
                encoding="utf-8",
            )
        raise ValueError("stale recovery actor")

    monkeypatch.setattr(atomic_io, "os", _NamedOSProxy("nt"))

    with pytest.raises(ValueError, match="stale recovery actor"):
        atomic_io.publish_text_atomic(
            target,
            "prepared\n",
            fsync_policy="strict",
            precommit=reject_authority,
        )

    assert target.parent.is_dir()
    assert not target.exists()
    if parent_case == "concurrently-populated":
        sidecars = _tmp_siblings(target)
        assert len(sidecars) == 1
        assert sidecars[0].read_bytes() == b"prepared\n"
        assert (target.parent / "concurrent.txt").read_text(encoding="utf-8") == (
            "belongs to another writer\n"
        )
    else:
        assert _tmp_siblings(target) == []


def test_rejected_exclusive_precommit_preserves_generation_changed_parent_with_aba_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "created-store" / "receipt.json"
    real_lstat = Path.lstat
    callback_calls = 0
    replacement_live = False
    owned_parent_metadata: object | None = None
    owned_sidecar_metadata: object | None = None
    owned_generation: int | None = None
    replacement_generation: int | None = None
    replacement_sidecar: Path | None = None
    replacement_sidecar_bytes: bytes | None = None
    rejection = ValueError("stale recovery actor")

    class GenerationChangedMetadata:
        def __init__(self, metadata: object, overrides: dict[str, int | float]) -> None:
            self._metadata = metadata
            self._overrides = overrides

        def __getattr__(self, attribute: str) -> object:
            if attribute in self._overrides:
                return self._overrides[attribute]
            return getattr(self._metadata, attribute)

    def report_aba_identity(path: Path) -> object:
        metadata = real_lstat(path)
        if not replacement_live:
            return metadata
        if path == replacement_sidecar:
            assert owned_sidecar_metadata is not None
            # The replacement tree contains the exact original sidecar inode;
            # hide only link-count timestamp noise from parking that inode
            # outside the parent while the directory generation is replaced.
            return owned_sidecar_metadata
        if path != target.parent:
            return metadata
        assert owned_parent_metadata is not None
        assert replacement_generation is not None
        return GenerationChangedMetadata(
            owned_parent_metadata,
            {
                "st_ctime_ns": replacement_generation,
                "st_ctime": replacement_generation / 1_000_000_000,
            },
        )

    def replace_parent_then_reject() -> None:
        nonlocal callback_calls
        nonlocal owned_parent_metadata
        nonlocal owned_sidecar_metadata
        nonlocal owned_generation
        nonlocal replacement_generation
        nonlocal replacement_live
        nonlocal replacement_sidecar
        nonlocal replacement_sidecar_bytes
        callback_calls += 1
        sidecars = _tmp_siblings(target)
        assert len(sidecars) == 1
        owned_parent_metadata = real_lstat(target.parent)
        owned_sidecar_metadata = real_lstat(sidecars[0])
        owned_generation = int(owned_parent_metadata.st_ctime_ns)
        replacement_sidecar_bytes = sidecars[0].read_bytes()

        parked_sidecar = tmp_path / "parked-sidecar"
        os.link(sidecars[0], parked_sidecar)
        sidecars[0].unlink()
        target.parent.rmdir()
        target.parent.mkdir()
        replacement_sidecar = target.parent / sidecars[0].name
        os.link(parked_sidecar, replacement_sidecar)
        parked_sidecar.unlink()
        replacement_generation = owned_generation + 1_000_000_000
        replacement_live = True

        reported = target.parent.lstat()
        assert (int(reported.st_dev), int(reported.st_ino)) == (
            int(owned_parent_metadata.st_dev),
            int(owned_parent_metadata.st_ino),
        )
        assert int(reported.st_ctime_ns) == replacement_generation
        assert int(reported.st_ctime_ns) != owned_generation
        assert replacement_sidecar.lstat() is owned_sidecar_metadata
        raise rejection

    monkeypatch.setattr(Path, "lstat", report_aba_identity)
    monkeypatch.setattr(atomic_io, "os", _NamedOSProxy("nt"))

    with pytest.raises(ValueError, match="stale recovery actor") as rejected:
        atomic_io.publish_text_atomic(
            target,
            "prepared\n",
            fsync_policy="strict",
            precommit=replace_parent_then_reject,
        )

    assert rejected.value is rejection
    assert callback_calls == 1
    assert owned_parent_metadata is not None
    assert owned_sidecar_metadata is not None
    assert owned_generation is not None
    assert replacement_generation is not None
    assert replacement_sidecar is not None
    assert replacement_sidecar_bytes == b"prepared\n"
    assert target.parent.is_dir()
    assert replacement_sidecar.read_bytes() == replacement_sidecar_bytes


def test_rejected_exclusive_precommit_does_not_follow_replaced_ancestor_alias(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = tmp_path / "symlink-probe"
    try:
        probe.symlink_to(tmp_path, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks are unavailable in this environment: {exc}")
    else:
        probe.unlink()

    created_root = tmp_path / "created-root"
    target = created_root / "nested" / "receipt.json"
    displaced_root = tmp_path / "displaced-root"
    callback_calls = 0
    prepared_sidecar_name: str | None = None
    prepared_sidecar_bytes: bytes | None = None
    rejection = ValueError("stale recovery actor")

    def replace_ancestor_with_alias_then_reject() -> None:
        nonlocal callback_calls
        nonlocal prepared_sidecar_name
        nonlocal prepared_sidecar_bytes
        callback_calls += 1
        sidecars = _tmp_siblings(target)
        assert len(sidecars) == 1
        prepared_sidecar_name = sidecars[0].name
        prepared_sidecar_bytes = sidecars[0].read_bytes()
        created_root.rename(displaced_root)
        created_root.symlink_to(displaced_root, target_is_directory=True)
        raise rejection

    monkeypatch.setattr(atomic_io, "os", _NamedOSProxy("nt"))

    with pytest.raises(ValueError, match="stale recovery actor") as rejected:
        atomic_io.publish_text_atomic(
            target,
            "prepared\n",
            fsync_policy="strict",
            precommit=replace_ancestor_with_alias_then_reject,
        )

    assert rejected.value is rejection
    assert callback_calls == 1
    assert prepared_sidecar_name is not None
    assert prepared_sidecar_bytes == b"prepared\n"
    assert created_root.is_symlink()
    assert displaced_root.is_dir()
    displaced_parent = displaced_root / "nested"
    assert displaced_parent.is_dir()
    assert (displaced_parent / prepared_sidecar_name).read_bytes() == prepared_sidecar_bytes


def test_rejected_exclusive_precommit_missing_sidecar_never_authorizes_parent_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "created-store" / "receipt.json"
    rejection = ValueError("stale recovery actor")

    def remove_capability_then_reject() -> None:
        sidecars = _tmp_siblings(target)
        assert len(sidecars) == 1
        sidecars[0].unlink()
        raise rejection

    monkeypatch.setattr(atomic_io, "os", _NamedOSProxy("nt"))

    with pytest.raises(ValueError) as rejected:
        atomic_io.publish_text_atomic(
            target,
            "prepared\n",
            fsync_policy="strict",
            precommit=remove_capability_then_reject,
        )

    assert rejected.value is rejection
    assert target.parent.is_dir()
    assert list(target.parent.iterdir()) == []


def test_rejected_exclusive_precommit_preserves_sidecar_generation_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "created-store" / "receipt.json"
    real_lstat = Path.lstat
    rejected_callback = False
    owned_sidecar: Path | None = None
    rejection = ValueError("stale recovery actor")

    class ChangedGenerationMetadata:
        def __init__(self, metadata: object) -> None:
            self._metadata = metadata

        def __getattr__(self, attribute: str) -> object:
            if attribute == "st_ctime_ns":
                return int(getattr(self._metadata, attribute)) + 1_000_000_000
            if attribute == "st_ctime":
                return float(getattr(self._metadata, attribute)) + 1.0
            return getattr(self._metadata, attribute)

    def report_generation_change(path: Path) -> object:
        metadata = real_lstat(path)
        if rejected_callback and path == owned_sidecar:
            return ChangedGenerationMetadata(metadata)
        return metadata

    def change_sidecar_generation_then_reject() -> None:
        nonlocal owned_sidecar
        nonlocal rejected_callback
        sidecars = _tmp_siblings(target)
        assert len(sidecars) == 1
        owned_sidecar = sidecars[0]
        rejected_callback = True
        raise rejection

    monkeypatch.setattr(Path, "lstat", report_generation_change)
    monkeypatch.setattr(atomic_io, "os", _NamedOSProxy("nt"))

    with pytest.raises(ValueError) as rejected:
        atomic_io.publish_text_atomic(
            target,
            "prepared\n",
            fsync_policy="strict",
            precommit=change_sidecar_generation_then_reject,
        )

    assert rejected.value is rejection
    assert owned_sidecar is not None
    assert owned_sidecar.read_bytes() == b"prepared\n"
    assert target.parent.is_dir()


def test_precommit_refuses_real_immediate_sidecar_inode_reuse_and_preserves_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full generation, not legacy dev/inode metadata, binds the opened file."""

    target = tmp_path / "created-store" / "receipt.json"
    prepared = b"prepared\n"
    foreign = b"FOREIGN!\n"
    assert len(prepared) == len(foreign)
    callback_calls = 0
    replacement: Path | None = None
    real_run = atomic_io._run_exclusive_precommit

    def callback() -> None:
        nonlocal callback_calls
        callback_calls += 1

    def reuse_at_boundary(
        state: atomic_io._ExclusivePrecommitState,
        path: Path,
        name: str,
        parent_fd: int | None,
        opened_identity: atomic_io.PublishedFileIdentity,
        opened_cleanup_identity: atomic_io._CleanupPathIdentity,
    ) -> None:
        nonlocal replacement
        sidecar = path.parent / name
        opened_legacy = (
            opened_identity.device,
            opened_identity.inode,
            opened_identity.mode,
            opened_identity.size,
            opened_identity.file_attributes,
            opened_identity.reparse_tag,
        )
        for _attempt in range(512):
            sidecar.unlink()
            sidecar.write_bytes(foreign)
            sidecar.chmod(stat.S_IMODE(opened_identity.mode))
            observed = atomic_io._cleanup_path_identity(sidecar, sidecar.lstat())
            observed_legacy = (
                observed.device,
                observed.inode,
                observed.mode,
                observed.size,
                observed.file_attributes,
                observed.reparse_tag,
            )
            if opened_legacy == observed_legacy and not atomic_io._same_cleanup_identity(
                opened_cleanup_identity,
                observed,
            ):
                replacement = sidecar
                return real_run(
                    state,
                    path,
                    name,
                    parent_fd,
                    opened_identity,
                    opened_cleanup_identity,
                )
        pytest.skip(
            "test filesystem did not reuse the sidecar inode with a distinct "
            "generation in 512 immediate recreations"
        )

    monkeypatch.setattr(atomic_io, "_run_exclusive_precommit", reuse_at_boundary)

    with pytest.raises(OSError, match="sidecar identity changed"):
        atomic_io.publish_text_atomic(
            target,
            prepared.decode("utf-8"),
            fsync_policy="strict",
            precommit=callback,
        )

    assert callback_calls == 0
    assert not target.exists()
    assert replacement is not None
    assert replacement.read_bytes() == foreign
    assert target.parent.is_dir()


@pytest.mark.skipif(os.name != "posix", reason="pinned directory fd is POSIX-only")
def test_precommit_refuses_pinned_parent_lexical_replacement_before_callback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lexical authority cannot be combined with a displaced pinned parent."""

    target = tmp_path / "created-store" / "receipt.json"
    displaced = tmp_path / "displaced-store"
    callback_calls = 0
    injected = False
    real_run = atomic_io._run_exclusive_precommit

    def callback() -> None:
        nonlocal callback_calls
        callback_calls += 1

    def move_parent_at_boundary(
        state: atomic_io._ExclusivePrecommitState,
        path: Path,
        name: str,
        parent_fd: int | None,
        opened_identity: atomic_io.PublishedFileIdentity,
        opened_cleanup_identity: atomic_io._CleanupPathIdentity,
    ) -> None:
        nonlocal injected
        assert parent_fd is not None
        assert not injected
        injected = True
        path.parent.rename(displaced)
        path.parent.mkdir()
        (path.parent / "foreign.txt").write_bytes(b"foreign owner\n")
        return real_run(
            state,
            path,
            name,
            parent_fd,
            opened_identity,
            opened_cleanup_identity,
        )

    monkeypatch.setattr(atomic_io, "_run_exclusive_precommit", move_parent_at_boundary)

    with pytest.raises(OSError, match="lexical and pinned atomic parent identities"):
        atomic_io.publish_text_atomic(
            target,
            "prepared\n",
            fsync_policy="strict",
            precommit=callback,
        )

    assert injected
    assert callback_calls == 0
    assert not target.exists()
    assert not (displaced / target.name).exists()
    assert (target.parent / "foreign.txt").read_bytes() == b"foreign owner\n"
    assert displaced.is_dir()


def test_cleanup_identity_uses_real_windows_legacy_ctime_as_birth_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = SimpleNamespace(
        st_dev=1,
        st_ino=2,
        st_mode=stat.S_IFDIR | 0o700,
        st_size=0,
        st_ctime_ns=3,
        st_mtime_ns=4,
        st_nlink=1,
    )
    monkeypatch.setattr(atomic_io.sys, "platform", "win32")

    identity = atomic_io._cleanup_path_identity(tmp_path, metadata)
    changed = identity._replace(change_time_ns=identity.change_time_ns + 1)

    assert identity.birth_time_ns == metadata.st_ctime_ns
    assert atomic_io._same_cleanup_object(identity, changed)
    assert not atomic_io._same_cleanup_identity(identity, changed)


def test_rejected_precommit_cleanup_failure_never_masks_callback_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "created-store" / "receipt.json"
    rejection = ValueError("stale recovery actor")

    def reject_authority() -> None:
        raise rejection

    def fail_cleanup(_path: Path) -> None:
        raise RuntimeError("injected rmdir failure")

    monkeypatch.setattr(Path, "rmdir", fail_cleanup)
    monkeypatch.setattr(atomic_io, "os", _NamedOSProxy("nt"))

    with pytest.raises(ValueError) as rejected:
        atomic_io.publish_text_atomic(
            target,
            "prepared\n",
            fsync_policy="strict",
            precommit=reject_authority,
        )

    assert rejected.value is rejection
    assert target.parent.is_dir()
    assert _tmp_siblings(target) == []


def test_windows_precommit_oserror_is_not_translated_as_destination_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "existing-receipt.json"
    target.write_text("existing\n", encoding="utf-8")
    rejection = OSError(errno.EACCES, "actor authority disappeared")
    callback_calls = 0

    def reject_with_oserror() -> None:
        nonlocal callback_calls
        callback_calls += 1
        raise rejection

    monkeypatch.setattr(atomic_io, "os", _NamedOSProxy("nt"))

    with pytest.raises(OSError) as rejected:
        atomic_io.publish_text_atomic(
            target,
            "prepared\n",
            fsync_policy="strict",
            precommit=reject_with_oserror,
        )

    assert rejected.value is rejection
    assert callback_calls == 1
    assert target.read_bytes() == b"existing\n"
    assert _tmp_siblings(target) == []


def test_successful_precommit_is_not_retried_or_rolled_back_after_publish_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "created-store" / "receipt.json"
    callback_calls = 0

    def prove_authority() -> None:
        nonlocal callback_calls
        callback_calls += 1

    def fail_destination(_source: object, _destination: object) -> None:
        raise OSError(errno.EACCES, "injected destination failure")

    monkeypatch.setattr(
        atomic_io,
        "os",
        _NamedOSProxy("nt", rename=fail_destination),
    )

    with pytest.raises(OSError, match="injected destination failure"):
        atomic_io.publish_text_atomic(
            target,
            "prepared\n",
            fsync_policy="strict",
            precommit=prove_authority,
        )

    assert callback_calls == 1
    assert target.parent.is_dir()
    assert not target.exists()
    assert _tmp_siblings(target) == []


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


@pytest.mark.skipif(os.name != "posix", reason="POSIX exposes the directory fsync boundary")
@pytest.mark.parametrize(
    ("writer_name", "payload", "existing", "expected"),
    (
        ("write_text_atomic", "replacement\n", b"original\n", b"original\n"),
        ("publish_text_atomic", "published\n", None, None),
        ("publish_text_owned_atomic", "published\n", None, None),
        (
            "write_json_atomic",
            {"replacement": True},
            b'{"original":true}\n',
            b'{"original":true}\n',
        ),
        ("publish_json_atomic", {"published": True}, None, None),
        ("publish_json_owned_atomic", {"published": True}, None, None),
    ),
)
def test_strict_file_fsync_failure_is_retry_safe_and_never_commits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    writer_name: str,
    payload: object,
    existing: bytes | None,
    expected: bytes | None,
) -> None:
    target = tmp_path / "strict-file-fsync-state"
    if existing is not None:
        target.write_bytes(existing)

    def fail_regular_file_fsync(descriptor: int) -> None:
        metadata = os.fstat(descriptor)
        if stat.S_ISREG(metadata.st_mode):
            raise OSError(errno.EIO, "injected file fsync failure")

    monkeypatch.setattr(atomic_io.os, "fsync", fail_regular_file_fsync)

    with pytest.raises(atomic_io.AtomicWriteError) as caught:
        getattr(atomic_io, writer_name)(
            target,
            payload,
            fsync_policy="strict",
        )

    assert caught.value.stage == "file-fsync"
    assert caught.value.committed is False
    assert caught.value.retry_safe is True
    assert isinstance(caught.value.__cause__, OSError)
    if expected is None:
        assert not target.exists()
    else:
        assert target.read_bytes() == expected
    assert _tmp_siblings(target) == []


@pytest.mark.skipif(os.name != "posix", reason="POSIX exposes the directory fsync boundary")
@pytest.mark.parametrize(
    ("writer_name", "payload", "expected"),
    (
        ("write_text_atomic", "replacement\n", b"replacement\n"),
        ("publish_text_atomic", "published\n", b"published\n"),
        ("publish_text_owned_atomic", "published\n", b"published\n"),
        (
            "write_json_atomic",
            {"replacement": True},
            b'{\n  "replacement": true\n}\n',
        ),
        (
            "publish_json_atomic",
            {"published": True},
            b'{\n  "published": true\n}\n',
        ),
        (
            "publish_json_owned_atomic",
            {"published": True},
            b'{\n  "published": true\n}\n',
        ),
    ),
)
def test_strict_parent_fsync_failure_reports_committed_non_retry_safe_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    writer_name: str,
    payload: object,
    expected: bytes,
) -> None:
    target = tmp_path / "strict-parent-fsync-state"
    target_parent_identity = (tmp_path.stat().st_dev, tmp_path.stat().st_ino)

    def fail_directory_fsync(descriptor: int) -> None:
        metadata = os.fstat(descriptor)
        if (
            stat.S_ISDIR(metadata.st_mode)
            and (metadata.st_dev, metadata.st_ino) == target_parent_identity
        ):
            raise OSError(errno.EIO, "injected parent fsync failure")

    monkeypatch.setattr(atomic_io.os, "fsync", fail_directory_fsync)

    with pytest.raises(atomic_io.AtomicWriteError) as caught:
        getattr(atomic_io, writer_name)(
            target,
            payload,
            fsync_policy="strict",
        )

    assert caught.value.stage == "parent-fsync"
    assert caught.value.committed is True
    assert caught.value.retry_safe is False
    assert isinstance(caught.value.__cause__, OSError)
    assert target.read_bytes() == expected
    assert _tmp_siblings(target) == []


@pytest.mark.skipif(os.name != "posix", reason="POSIX exposes directory entry durability")
def test_strict_first_use_publication_fsyncs_created_directory_entry_and_final_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = tmp_path / "agents" / "runtime"
    runtime.mkdir(parents=True)
    target = runtime / "recovery_receipts" / "RECOVERY-first.prepared.json"
    runtime_identity = (runtime.stat().st_dev, runtime.stat().st_ino)
    synced_directories: list[tuple[int, int]] = []

    def observe_fsync(descriptor: int) -> None:
        metadata = os.fstat(descriptor)
        if stat.S_ISDIR(metadata.st_mode):
            synced_directories.append((metadata.st_dev, metadata.st_ino))

    monkeypatch.setattr(atomic_io.os, "fsync", observe_fsync)

    atomic_io.publish_json_atomic(
        target,
        {"receipt_id": "RECOVERY-first"},
        fsync_policy="strict",
    )

    receipt_store = target.parent
    receipt_store_identity = (receipt_store.stat().st_dev, receipt_store.stat().st_ino)
    # Strict traversal may also sync older ancestors. The newly-created store
    # entry must be persisted through its existing runtime parent before the
    # final destination publication syncs the store directory itself.
    assert synced_directories[-2:] == [runtime_identity, receipt_store_identity]
    assert json.loads(target.read_text(encoding="utf-8")) == {
        "receipt_id": "RECOVERY-first"
    }
    assert _tmp_siblings(target) == []


@pytest.mark.skipif(os.name != "posix", reason="POSIX exposes directory entry durability")
def test_strict_created_parent_fsync_failure_reports_precommit_retry_safe_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = tmp_path / "agents" / "runtime"
    runtime.mkdir(parents=True)
    runtime_identity = (runtime.stat().st_dev, runtime.stat().st_ino)
    target = runtime / "recovery_receipts" / "RECOVERY-first.prepared.json"

    def fail_created_entry_parent_fsync(descriptor: int) -> None:
        metadata = os.fstat(descriptor)
        if (metadata.st_dev, metadata.st_ino) == runtime_identity:
            raise OSError(errno.EIO, "injected created-parent fsync failure")

    monkeypatch.setattr(atomic_io.os, "fsync", fail_created_entry_parent_fsync)

    for _attempt in range(2):
        with pytest.raises(atomic_io.AtomicWriteError) as caught:
            atomic_io.publish_json_atomic(
                target,
                {"receipt_id": "RECOVERY-first"},
                fsync_policy="strict",
            )

        # A supporting directory entry exists, but the requested destination
        # has not crossed its commit point. A retry must re-check the same
        # ancestor boundary even though that directory now exists.
        assert caught.value.stage == "parent-create-fsync"
        assert caught.value.committed is False
        assert caught.value.retry_safe is True
        assert isinstance(caught.value.__cause__, OSError)
        assert caught.value.__cause__.errno == errno.EIO
        assert target.parent.is_dir()
        assert not target.exists()
        assert _tmp_siblings(target) == []


@pytest.mark.skipif(os.name != "posix", reason="POSIX exposes both fsync boundaries")
@pytest.mark.parametrize("failure_kind", ("file", "directory"))
def test_explicit_best_effort_fsync_policy_preserves_legacy_success_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_kind: str,
) -> None:
    target = tmp_path / f"best-effort-{failure_kind}.txt"

    def fail_selected_fsync(descriptor: int) -> None:
        metadata = os.fstat(descriptor)
        kind = "directory" if stat.S_ISDIR(metadata.st_mode) else "file"
        if kind == failure_kind:
            raise OSError(errno.EIO, f"injected {kind} fsync failure")

    monkeypatch.setattr(atomic_io.os, "fsync", fail_selected_fsync)

    result = atomic_io.write_text_atomic(
        target,
        "legacy success\n",
        fsync_policy="best_effort",
    )

    assert result is None
    assert target.read_bytes() == b"legacy success\n"
    assert _tmp_siblings(target) == []


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
