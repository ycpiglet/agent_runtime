"""Tests for atomic_io — power-loss-safe atomic file writes.

Invariants under test:
  - writes are atomic (temp file + os.replace), never leaving a half-written target;
  - no stray ``.tmp`` sidecar is left behind on success;
  - parent directories are created on demand;
  - JSON serialization honors the caller's ``indent`` / ``sort_keys`` preference so
    existing call-sites keep their on-disk format.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import atomic_io  # noqa: E402


def _tmp_siblings(path: Path) -> list[Path]:
    return list(path.parent.glob(f"{path.name}.*.tmp"))


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
