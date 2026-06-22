"""Tests for regen_host_lock_if_needed.py — template→lock drift catcher.

--check exits 1 when the committed host lock is stale (template tree has diverged).
--write regenerates the lock so that a subsequent --check exits 0.

Guard purpose: editing a template file without regenerating the host lock would red
test_lock_merge_driver.test_regenerate_noop_when_current.  This script catches it
pre-CI so the developer gets a clear message rather than a cryptic test failure.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "regen_host_lock_if_needed.py"
FIXTURE_HOST = ROOT / "tests" / "fixtures" / "host"
FIXTURE_LOCK = FIXTURE_HOST / "agent_runtime.lock.json"


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
    )


def test_check_exits_0_when_lock_is_current():
    """The committed fixture lock must already be up to date."""
    result = _run(["--check"])
    assert result.returncode == 0, result.stdout + result.stderr


def test_check_exits_1_when_lock_is_stale(tmp_path):
    """If the lock is stale (wrong content) --check must exit 1."""
    # Copy the fixture host to a tmp dir and corrupt the lock.
    host = tmp_path / "host"
    shutil.copytree(FIXTURE_HOST, host)
    (host / "agent_runtime.lock.json").write_text('{"stale": true}\n', encoding="utf-8")

    result = _run(["--check", "--host-root", str(host)])
    assert result.returncode == 1, result.stdout + result.stderr
    # The message should tell the developer what to do.
    combined = result.stdout + result.stderr
    assert "--write" in combined


def test_write_then_check_exits_0(tmp_path):
    """After --write the lock is current so --check must exit 0."""
    host = tmp_path / "host"
    shutil.copytree(FIXTURE_HOST, host)
    (host / "agent_runtime.lock.json").write_text('{"stale": true}\n', encoding="utf-8")

    write_result = _run(["--write", "--host-root", str(host)])
    assert write_result.returncode == 0, write_result.stdout + write_result.stderr

    check_result = _run(["--check", "--host-root", str(host)])
    assert check_result.returncode == 0, check_result.stdout + check_result.stderr


def test_write_regenerates_to_canonical_content(tmp_path):
    """--write must produce exactly the same bytes as the canonical committed lock."""
    host = tmp_path / "host"
    shutil.copytree(FIXTURE_HOST, host)
    (host / "agent_runtime.lock.json").write_text('{"stale": true}\n', encoding="utf-8")

    _run(["--write", "--host-root", str(host)])

    regenerated = json.loads((host / "agent_runtime.lock.json").read_text(encoding="utf-8"))
    canonical = json.loads(FIXTURE_LOCK.read_text(encoding="utf-8"))
    assert regenerated == canonical
