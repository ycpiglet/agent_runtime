"""Tests for scripts/release_version_cascade.py.

The "current public tag" is duplicated across many files (pyproject, __init__,
CLI --tag defaults, the CI workflow, the release-gate template, the host fixture
ref, and two test constants). A partial bump reds CI in three separate places
(observed during the v0.3.0 cut). This tool checks consistency in one pass and
bumps the whole set atomically.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import release_version_cascade as rvc  # noqa: E402


def _seed(tmp_path: Path) -> Path:
    """Copy every cascade file from the real repo into a throwaway tree."""
    root = tmp_path / "repo"
    for spec in rvc.CASCADE:
        src = REPO_ROOT / spec.path
        dst = root / spec.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    return root


def test_real_repo_is_consistent() -> None:
    # main ships a consistent cascade; the checker must agree.
    assert rvc.check(REPO_ROOT) == []


def test_every_cascade_file_has_at_least_one_match() -> None:
    # guards against a regex silently matching nothing (a ref that drifted format).
    root = REPO_ROOT
    for spec in rvc.CASCADE:
        found = spec.versions(root)
        assert found, f"no version match in {spec.path} (pattern drifted?)"


def test_check_detects_a_single_drifted_ref(tmp_path: Path) -> None:
    root = _seed(tmp_path)
    assert rvc.check(root) == []
    cur = rvc.current_version(root)
    cli = root / "src/agent_runtime/cli.py"
    cli.write_text(cli.read_text(encoding="utf-8").replace(f"v{cur}", "v0.0.1", 1), encoding="utf-8")

    mismatches = rvc.check(root)

    assert any("cli.py" in m for m in mismatches), mismatches


def test_write_bumps_the_whole_set_atomically(tmp_path: Path) -> None:
    root = _seed(tmp_path)
    cur = rvc.current_version(root)
    assert cur != "9.9.9"

    changed = rvc.write(root, "9.9.9")

    assert rvc.current_version(root) == "9.9.9"
    assert rvc.check(root) == []  # everything now agrees at 9.9.9
    # every cascade file was rewritten
    assert {c for c in changed} == {spec.path for spec in rvc.CASCADE}
